"""Loudness BS.1770 / EBU R128: integrado, short-term, LRA, sample peak y true peak.

Metodo por valor (queda en `LoudnessResult.method`):
- integrado / LRA / true peak: ffmpeg `ebur128=peak=true` si hay ffmpeg y un path
  (referencia de la industria); si no, calculo numerico propio.
- curva short-term (ventana 3 s, hop 1 s): siempre numerica, con el mismo
  filtro K-weighting que pyloudnorm.
- true peak numerico: sobremuestreo 4x polifasico (scipy `resample_poly`), pico
  del resultado. Es la aproximacion del Anexo 2 de BS.1770 (el estandar pide
  >= 4x a 48 kHz); subestima apenas respecto de un medidor certificado.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
from scipy.signal import lfilter, resample_poly

ABS_GATE_LUFS = -70.0
_CH_GAIN = (1.0, 1.0, 1.0, 1.41, 1.41)
_OFFSET = -0.691


@dataclass
class LoudnessResult:
    integrated_lufs: float
    lra_lu: float
    sample_peak_dbfs: float
    true_peak_dbtp: float
    short_term_lufs: list[float]
    short_term_hop_s: float
    short_term_window_s: float
    method: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def parse_ebur128_summary(text: str) -> dict[str, float]:
    """Extrae I, LRA y true peak del resumen final de `ffmpeg -af ebur128=peak=true`."""
    idx = text.rfind("Summary:")
    block = text[idx:] if idx >= 0 else text
    i = re.findall(r"\bI:\s+(-?[\d.]+)\s+LUFS", block)
    lra = re.findall(r"\bLRA:\s+(-?[\d.]+)\s+LU\b", block)
    tp = re.findall(r"\bPeak:\s+(-?[\d.]+)\s+dBFS", block)
    if not (i and lra and tp):
        raise ValueError("resumen de ebur128 incompleto (falta I, LRA o Peak)")
    return {"integrated_lufs": float(i[-1]), "lra_lu": float(lra[-1]), "true_peak_dbtp": float(tp[-1])}


def _run_ffmpeg_ebur128(path: Path) -> dict[str, float]:
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
         "-filter_complex", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True, timeout=600,
    )
    return parse_ebur128_summary(proc.stderr)


def _k_weight_energy(x: np.ndarray, sr: int) -> np.ndarray:
    """Energia instantanea ponderada K y sumada por canal (G de BS.1770)."""
    import pyloudnorm as pyln

    stages = list(pyln.Meter(sr)._filters.values())
    total = np.zeros(x.shape[0])
    for ch in range(min(x.shape[1], len(_CH_GAIN))):
        y = x[:, ch]
        for st in stages:
            y = lfilter(st.b, st.a, y)
        total += _CH_GAIN[ch] * y * y
    return total


def _windowed_lufs(cs: np.ndarray, win: int, hop: int) -> np.ndarray:
    starts = np.arange(0, len(cs) - win, hop)
    mean = (cs[starts + win] - cs[starts]) / win
    with np.errstate(divide="ignore"):
        return _OFFSET + 10 * np.log10(mean)


def _power_mean_lufs(l: np.ndarray) -> float:
    return _OFFSET + 10 * np.log10(np.mean(10 ** ((l - _OFFSET) / 10)))


def _integrated(blocks: np.ndarray) -> float:
    g = blocks[blocks > ABS_GATE_LUFS]
    if g.size == 0:
        return float("-inf")
    rel = _power_mean_lufs(g) - 10.0
    g = g[g > rel]
    return float(_power_mean_lufs(g)) if g.size else float("-inf")


def _lra(st: np.ndarray) -> float:
    g = st[st > ABS_GATE_LUFS]
    if g.size == 0:
        return 0.0
    g = g[g > _power_mean_lufs(g) - 20.0]
    if g.size < 2:
        return 0.0
    return float(np.percentile(g, 95) - np.percentile(g, 10))


def _peaks(x: np.ndarray) -> tuple[float, float]:
    def db(v: float) -> float:
        return float(20 * np.log10(v)) if v > 0 else float("-inf")

    sample = float(np.max(np.abs(x)))
    over = resample_poly(x, 4, 1, axis=0, window=("kaiser", 8.0))
    # el filtro rebota contra el escalon de inicio/fin de archivo: se descartan 32 muestras por borde
    edge = 128
    if over.shape[0] > 4 * edge:
        over = over[edge:-edge]
    return db(sample), db(float(np.max(np.abs(over))))


def measure(
    samples: np.ndarray,
    sr: int,
    *,
    path: str | Path | None = None,
    use_ffmpeg: bool = True,
) -> LoudnessResult:
    """Mide loudness de `samples` (n,) o (n, canales). Con `path` + ffmpeg usa ffmpeg."""
    x = np.asarray(samples, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    if x.shape[0] < sr * 0.4:
        raise ValueError("audio demasiado corto para medir loudness (< 0.4 s)")

    cs = np.concatenate([[0.0], np.cumsum(_k_weight_energy(x, sr))])
    blocks = _windowed_lufs(cs, int(0.4 * sr), int(0.1 * sr))
    st_win = int(3.0 * sr)
    short_term = _windowed_lufs(cs, st_win, sr) if len(cs) > st_win + 1 else np.array([])
    lra_hop = _windowed_lufs(cs, st_win, int(0.1 * sr)) if len(cs) > st_win + 1 else np.array([])

    sample_peak, true_peak = _peaks(x)
    integrated, lra = _integrated(blocks), _lra(lra_hop)
    method = {
        "integrated": "numeric_bs1770", "lra": "numeric_ebu3342",
        "true_peak": "numeric_4x_polyphase", "short_term": "numeric_bs1770",
        "sample_peak": "numeric",
    }

    if use_ffmpeg and path is not None and ffmpeg_available():
        try:
            ff = _run_ffmpeg_ebur128(Path(path))
        except (ValueError, OSError, subprocess.SubprocessError):
            ff = None  # ffmpeg roto o salida rara: nos quedamos con el calculo numerico
        if ff:
            integrated, lra, true_peak = ff["integrated_lufs"], ff["lra_lu"], ff["true_peak_dbtp"]
            method.update(integrated="ffmpeg_ebur128", lra="ffmpeg_ebur128", true_peak="ffmpeg_ebur128")

    return LoudnessResult(
        integrated_lufs=round(float(integrated), 2),
        lra_lu=round(float(lra), 2),
        sample_peak_dbfs=round(sample_peak, 2),
        true_peak_dbtp=round(true_peak, 2),
        short_term_lufs=[round(float(v), 2) for v in short_term],
        short_term_hop_s=1.0,
        short_term_window_s=3.0,
        method=method,
    )


def measure_file(path: str | Path, *, use_ffmpeg: bool = True) -> LoudnessResult:
    import soundfile as sf

    data, sr = sf.read(str(path), always_2d=True)
    return measure(data, sr, path=path, use_ffmpeg=use_ffmpeg)
