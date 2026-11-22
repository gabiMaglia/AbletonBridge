"""Nota fundamental de kicks y rumbles/bajos, e intervalo rumble-vs-kick.

Metodo principal: FFT con ventana Hann + interpolacion parabolica del pico en
30-150 Hz, sobre el cuerpo del sonido (nunca sobre el transitorio). pYIN de
librosa es solo una segunda opinion opcional.

Limite conocido (auditoria D-d): el zero-padding interpola, no agrega
resolucion. Dos tonos a menos de ~1/T Hz no se separan en una misma ventana;
por eso kick y rumble se miden por separado, nunca en la misma mezcla.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field

import numpy as np
from scipy.signal import butter, hilbert, sosfiltfilt

FMIN, FMAX = 30.0, 150.0
OCTAVE_RATIO = 10 ** (-12 / 20)      # fundamental a menos de 12 dB del pico => ambiguedad
_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


@dataclass(frozen=True)
class Note:
    name: str          # "F1"
    midi: int
    cents: float       # -50..+50 respecto de la nota
    hz: float


def hz_to_midi(hz: float) -> float:
    return 69.0 + 12.0 * math.log2(hz / 440.0)


def hz_to_note(hz: float) -> Note:
    m = hz_to_midi(hz)
    n = int(round(m))
    return Note(f"{_NAMES[n % 12]}{n // 12 - 1}", n, round((m - n) * 100.0, 1), float(hz))


@dataclass
class PitchResult:
    hz: float | None
    note: Note | None
    confidence: str                      # high | medium | low | none
    method: str
    octave_ambiguous: bool = False
    glide_st: float | None = None        # solo kicks
    stability: float | None = None       # solo rumbles: fraccion de frames a +-50 cents
    cents_spread: float | None = None
    peaks_hz: list[float] = field(default_factory=list)
    competing_peaks: list[float] = field(default_factory=list)   # otros picos a <= 3 dB y > 1.5 st
    pyin_hz: float | None = None
    pyin_agrees: bool | None = None

    def to_dict(self) -> dict:
        return asdict(self)


# ----- primitivas -------------------------------------------------------------------------

def _mono(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    return x.mean(axis=1) if x.ndim == 2 else x


def _band(x: np.ndarray, sr: int, lo: float, hi: float) -> np.ndarray:
    sos = butter(4, [lo, hi], btype="band", fs=sr, output="sos")
    return sosfiltfilt(sos, x)


def _spectrum(x: np.ndarray, sr: int) -> tuple[np.ndarray, np.ndarray]:
    nfft = 1 << int(math.ceil(math.log2(max(len(x), 4 * sr))))   # bins <= 0.25 Hz
    mag = np.abs(np.fft.rfft(x * np.hanning(len(x)), nfft))
    return np.fft.rfftfreq(nfft, 1.0 / sr), mag


def _peak_in(freqs: np.ndarray, mag: np.ndarray, lo: float, hi: float) -> tuple[float, float] | None:
    idx = np.where((freqs >= lo) & (freqs <= hi))[0]
    if idx.size < 3:
        return None
    k = idx[int(np.argmax(mag[idx]))]
    if mag[k] <= 0 or k == 0 or k >= len(mag) - 1:
        return None
    a, b, c = np.log(mag[k - 1] + 1e-30), np.log(mag[k] + 1e-30), np.log(mag[k + 1] + 1e-30)
    denom = a - 2 * b + c
    delta = 0.5 * (a - c) / denom if denom != 0 else 0.0
    return float(freqs[k] + delta * (freqs[1] - freqs[0])), float(mag[k])


def spectral_peak(x: np.ndarray, sr: int, lo: float = FMIN, hi: float = FMAX) -> float | None:
    """Frecuencia del pico dominante en [lo, hi] con interpolacion parabolica (log-magnitud)."""
    f, m = _spectrum(_mono(x), sr)
    p = _peak_in(f, m, lo, hi)
    return p[0] if p else None


def _resolve_octave(freqs: np.ndarray, mag: np.ndarray, hz: float, pmag: float) -> tuple[float, bool]:
    """Si hay un pico en hz/2 a menos de 12 dB del principal, la fundamental es hz/2."""
    half = _peak_in(freqs, mag, hz / 2 * 0.93, hz / 2 * 1.07) if hz / 2 >= 22.0 else None
    if half and half[1] >= OCTAVE_RATIO * pmag:
        # debe ser un maximo local real y no la cola de leakage del pico principal
        return half[0], True
    return hz, False


def _pyin(x: np.ndarray, sr: int) -> float | None:
    if not librosa_available():
        return None
    import librosa

    try:
        f0, voiced, _ = librosa.pyin(x.astype(np.float32), fmin=30, fmax=200, sr=sr,
                                     frame_length=8192, hop_length=1024)
    except Exception:
        return None
    f0 = f0[voiced & np.isfinite(f0)] if voiced is not None else f0[np.isfinite(f0)]
    return float(np.median(f0)) if f0.size else None


def librosa_available() -> bool:
    try:
        import librosa  # noqa: F401
    except Exception:
        return False
    return True


def _attach_pyin(res: PitchResult, x: np.ndarray, sr: int, crosscheck: bool) -> None:
    if not (crosscheck and res.hz):
        return
    py = _pyin(x, sr)
    if py:
        res.pyin_hz = round(py, 2)
        # el octavo de tolerancia absorbe el glide residual que pYIN promedia
        res.pyin_agrees = abs(1200 * math.log2(py / res.hz)) < 100


# ----- kick one-shot ----------------------------------------------------------------------

def analyze_kick(
    samples: np.ndarray, sr: int, *, skip_ms: float = 20.0, crosscheck: bool = True
) -> PitchResult:
    """Nota del tramo estable de un kick one-shot (salta ataque y barrido inicial)."""
    x = _mono(samples)
    if len(x) < int(0.15 * sr):
        raise ValueError("kick demasiado corto (< 150 ms) para medir pitch")
    peak = float(np.max(np.abs(x)))
    if peak == 0:
        return PitchResult(None, None, "none", "fft_body")
    onset = int(np.argmax(np.abs(x) > 0.1 * peak))
    y = _band(x, sr, 20.0, 250.0)

    # glide: frecuencia instantanea en los primeros ms, antes de que se estabilice
    a, b = onset + int(0.003 * sr), onset + int(0.010 * sr)
    inst = np.diff(np.unwrap(np.angle(hilbert(y[onset : onset + int(0.05 * sr)])))) * sr / (2 * np.pi)
    start_hz = float(np.median(inst[a - onset : b - onset])) if b - onset < len(inst) else None

    body = y[onset + int(skip_ms * sr / 1000) : onset + int(skip_ms * sr / 1000) + int(0.5 * sr)]
    win, hop = int(0.100 * sr), int(0.025 * sr)
    if len(body) < win:
        win = len(body)
    starts = list(range(0, max(1, len(body) - win + 1), hop))
    rms = np.array([np.sqrt(np.mean(body[s : s + win] ** 2)) for s in starts])
    keep = [s for s, r in zip(starts, rms) if r >= 10 ** (-35 / 20) * rms.max()]
    stable = keep[len(keep) // 2 :] if len(keep) >= 3 else keep
    peaks = []
    for s in stable:
        f, m = _spectrum(body[s : s + win], sr)
        p = _peak_in(f, m, FMIN, FMAX)
        if p:
            peaks.append(p[0])
    if not peaks:
        return PitchResult(None, None, "none", "fft_body")

    hz = float(np.median(peaks))
    seg = body[stable[0] : stable[-1] + win]
    f, m = _spectrum(seg, sr)
    p = _peak_in(f, m, hz * 0.9, hz * 1.1)
    hz, pmag = (p[0], p[1]) if p else (hz, 1.0)
    hz, ambiguous = _resolve_octave(f, m, hz, pmag)
    spread = float(np.std([1200 * math.log2(q / np.median(peaks)) for q in peaks])) if len(peaks) > 1 else 0.0

    if ambiguous:
        conf = "low"
    elif spread < 15 and len(peaks) >= 3:
        conf = "high"
    elif spread < 40:
        conf = "medium"
    else:
        conf = "low"

    res = PitchResult(
        hz=round(hz, 2), note=hz_to_note(hz), confidence=conf, method="fft_body_hann_parabolic",
        octave_ambiguous=ambiguous, cents_spread=round(spread, 1),
        glide_st=round(12 * math.log2(start_hz / hz), 1) if start_hz and start_hz > 0 else None,
    )
    _attach_pyin(res, body, sr, crosscheck)
    return res


# ----- rumble / bajo ----------------------------------------------------------------------

def analyze_rumble(
    samples: np.ndarray, sr: int, *, frame_s: float = 0.5, crosscheck: bool = False
) -> PitchResult:
    """Nota dominante (mediana en el tiempo) de un loop de rumble/bajo en 30-150 Hz."""
    x = _mono(samples)
    if len(x) < int(0.1 * sr):
        raise ValueError("loop demasiado corto (< 100 ms)")
    y = _band(x, sr, 25.0, 200.0)
    win = min(int(frame_s * sr), len(y))
    hop = max(1, win // 2)
    starts = list(range(0, max(1, len(y) - win + 1), hop))
    rms = np.array([np.sqrt(np.mean(y[s : s + win] ** 2)) for s in starts])
    if rms.max() < 1e-6:
        return PitchResult(None, None, "none", "fft_frames_median", stability=0.0)

    peaks, acc = [], None
    for s, r in zip(starts, rms):
        if r < 10 ** (-30 / 20) * rms.max():
            continue
        f, m = _spectrum(y[s : s + win], sr)
        p = _peak_in(f, m, FMIN, FMAX)
        if p:
            peaks.append(p[0])
            acc = m**2 if acc is None else acc + m**2
    if not peaks:
        return PitchResult(None, None, "none", "fft_frames_median", stability=0.0)

    med = float(np.median(peaks))
    avg = np.sqrt(acc / len(peaks))
    p = _peak_in(f, avg, med * 0.9, med * 1.1)
    hz, pmag = (p[0], p[1]) if p else (med, 1.0)
    hz, ambiguous = _resolve_octave(f, avg, hz, pmag)
    in_tol = [abs(1200 * math.log2(q / med)) <= 50 for q in peaks]
    stability = float(np.mean(in_tol))

    # maximos locales del espectro promedio, de mayor a menor
    band = (f >= FMIN) & (f <= FMAX)
    idx = np.where(band)[0]
    mid = idx[1:-1]
    loc = mid[(avg[mid] > avg[mid - 1]) & (avg[mid] >= avg[mid + 1])]
    top, taken = [], []
    for k in loc[np.argsort(avg[loc])[::-1]]:
        if all(abs(f[k] - t) > 3.0 for t in taken):
            taken.append(float(f[k]))
            top.append(k)
        if len(top) == 4:
            break
    # competidores: picos fuertes que no son la fundamental ni su octava (un rumble de
    # kick con reverb suele tener varios parciales y no una nota unica)
    competing = []
    for k in top:
        dist = abs(1200 * math.log2(f[k] / hz))
        octave = min(abs(dist - 1200), abs(dist - 2400)) < 60
        if dist > 150 and not octave and avg[k] >= pmag * 10 ** (-3 / 20):
            competing.append(round(float(f[k]), 1))
    top_hz = [round(float(f[k]), 1) for k in top]

    if ambiguous or competing or stability < 0.5:
        conf = "low"
    elif stability >= 0.8 and len(peaks) >= 4:
        conf = "high"
    else:
        conf = "medium"
    res = PitchResult(
        hz=round(hz, 2), note=hz_to_note(hz), confidence=conf, method="fft_frames_median",
        octave_ambiguous=ambiguous, stability=round(stability, 2), peaks_hz=top_hz,
        competing_peaks=competing,
        cents_spread=round(float(np.std([1200 * math.log2(q / med) for q in peaks])), 1),
    )
    _attach_pyin(res, y, sr, crosscheck)
    return res


# ----- intervalo y tonalidad --------------------------------------------------------------

_MAJOR = (0, 2, 4, 5, 7, 9, 11)
_MINOR = (0, 2, 3, 5, 7, 8, 10)
_FLAT = {"DB": "C#", "EB": "D#", "GB": "F#", "AB": "G#", "BB": "A#"}


def parse_key(key: str) -> tuple[int, str]:
    """'F minor' / 'F#m' / 'Bb major' / 'F' -> (pitch class de la tonica, 'minor'|'major')."""
    s = key.strip().replace("♯", "#").replace("♭", "b")
    minor = s.lower().endswith(("minor", "min")) or (s[1:].lstrip("#b").lower() == "m")
    root = s[0].upper() + (s[1] if len(s) > 1 and s[1] in "#b" else "")
    root = _FLAT.get(root.upper(), root.upper() if len(root) == 1 else root[0].upper() + root[1])
    if root not in _NAMES:
        raise ValueError(f"tonalidad no reconocida: {key!r}")
    return _NAMES.index(root), "minor" if minor else "major"


def pitch_class_in_key(pc: int, key: str) -> bool:
    root, mode = parse_key(key)
    return ((pc - root) % 12) in (_MINOR if mode == "minor" else _MAJOR)


def _wrap(d: float) -> float:
    """Reduce un desplazamiento al camino mas corto dentro de la octava: [-6, 6)."""
    return ((d + 6.0) % 12.0) - 6.0


@dataclass
class IntervalResult:
    semitones_exact: float                   # midi(rumble) - midi(kick); incluye octavas
    pitch_coarse_rumble_to_kick: int         # st a sumar al rumble para igualar la nota del kick
    residual_cents: float                    # lo que queda tras el pitch_coarse
    target_key: str | None = None
    kick_in_key: bool | None = None
    rumble_in_key: bool | None = None
    pitch_coarse_kick_to_key_root: int | None = None
    pitch_coarse_rumble_to_key_root: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def interval(kick: PitchResult, rumble: PitchResult, target_key: str | None = None) -> IntervalResult:
    """Diferencia rumble-kick y el pitch_coarse que alinea el rumble al kick (criterio de Gabriel)."""
    if not (kick.hz and rumble.hz):
        raise ValueError("hace falta una nota medida en el kick y en el rumble")
    mk, mr = hz_to_midi(kick.hz), hz_to_midi(rumble.hz)
    d = _wrap(mk - mr)
    coarse = int(round(d))
    out = IntervalResult(
        semitones_exact=round(mr - mk, 2),
        pitch_coarse_rumble_to_kick=coarse,
        residual_cents=round((d - coarse) * 100, 1),
    )
    if target_key:
        root, _ = parse_key(target_key)
        out.target_key = target_key
        out.kick_in_key = pitch_class_in_key(int(round(mk)) % 12, target_key)
        out.rumble_in_key = pitch_class_in_key(int(round(mr)) % 12, target_key)
        out.pitch_coarse_kick_to_key_root = int(round(_wrap(root - mk)))
        out.pitch_coarse_rumble_to_key_root = int(round(_wrap(root - mr)))
    return out


def main(argv: list[str] | None = None) -> int:
    """python -m nexo_analysis.pitch --kick k.wav --rumble r.wav [--key "F minor"]"""
    import argparse
    import json

    import soundfile as sf

    ap = argparse.ArgumentParser(prog="nexo_analysis.pitch")
    ap.add_argument("--kick")
    ap.add_argument("--rumble")
    ap.add_argument("--bass")
    ap.add_argument("--key", help="tonalidad objetivo, ej. 'F minor'")
    a = ap.parse_args(argv)

    def load(p: str):
        d, sr = sf.read(p, always_2d=True)
        return d, sr

    def dump(r: PitchResult) -> dict:
        d = r.to_dict()
        d["note"] = asdict(r.note) if r.note else None
        return d

    out: dict = {}
    res: dict[str, PitchResult] = {}
    if a.kick:
        res["kick"] = analyze_kick(*load(a.kick))
    if a.rumble:
        res["rumble"] = analyze_rumble(*load(a.rumble))
    if a.bass:
        res["bass"] = analyze_rumble(*load(a.bass))
    out.update({k: dump(v) for k, v in res.items()})
    for other in ("rumble", "bass"):
        if "kick" in res and other in res and res["kick"].hz and res[other].hz:
            out["interval" if other == "rumble" else "interval_bass"] = interval(
                res["kick"], res[other], a.key).to_dict()
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
