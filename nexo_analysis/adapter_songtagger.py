"""Unico punto de contacto con songTagger (D-14).

songTagger corre en WSL (essentia no tiene wheels de Windows). Este modulo lanza
`_songtagger_worker.py` dentro de su venv via `wsl.exe` y post-procesa el JSON
segun la auditoria de F2:

- BPM: se usa el de essentia (el de songTagger sale cuantizado a 10 ms, C-1) y se
  contrasta con una grilla recta ajustada sobre los beats de madmom.
- sections / drops / kick_events: se ignoran (C-2, I-1).
- tonalidad: se marca el sesgo a modo menor del perfil edmm (C-3).

`runner` es inyectable para testear sin WSL.
"""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np

# git rev-parse HEAD de songTagger al momento de escribir este adaptador (2026-11-22).
# Ojo: ese repo tiene cambios sin commitear (auditoria I-6): el hash no garantiza el codigo exacto.
PINNED_COMMIT = "71a97430f646c20cfb007f615fc0e3bd49877287"
DEFAULT_ROOT = Path(r"C:\Users\Gabriel Maglia\Documents\PersonalProjects\songTagger")
MARKER = "NEXO_JSON:"
IGNORED_FIELDS = ("sections", "drops", "kick_events")
REQUIRED_FIELDS = ("beats", "key", "scale")


class SongTaggerError(RuntimeError):
    pass


class ContractError(SongTaggerError):
    """La salida de songTagger no tiene la forma que este adaptador espera."""


@dataclass
class RunResult:
    returncode: int
    stdout: str
    stderr: str


Runner = Callable[..., RunResult]


def default_runner(cmd, timeout=None) -> RunResult:
    p = subprocess.run(list(cmd), capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout)
    return RunResult(p.returncode, p.stdout, p.stderr)


@dataclass
class SongTaggerConfig:
    root: Path = DEFAULT_ROOT
    python_rel: str = ".venv-wsl/bin/python"
    distro: str | None = None
    check_pin: bool = True
    timeout_s: int = 900


@dataclass
class PinStatus:
    ok: bool
    actual: str | None
    expected: str = PINNED_COMMIT


def to_wsl_path(p: str | Path) -> str:
    s = str(p)
    m = re.match(r"^([A-Za-z]):[\\/](.*)$", s)
    if not m:
        return s.replace("\\", "/")
    return f"/mnt/{m.group(1).lower()}/" + m.group(2).replace("\\", "/")


def check_pin(root: Path, runner: Runner = default_runner) -> PinStatus:
    try:
        r = runner(["git", "-C", str(root), "rev-parse", "HEAD"], timeout=30)
    except (OSError, subprocess.SubprocessError):
        return PinStatus(False, None)
    actual = r.stdout.strip() if r.returncode == 0 else None
    return PinStatus(actual == PINNED_COMMIT, actual)


# ----- grilla recta ----------------------------------------------------------------------

@dataclass
class GridFit:
    bpm: float
    first_beat_s: float
    residual_ms: float


def fit_grid(beats: list[float] | np.ndarray) -> GridFit:
    """Recta t = t0 + k*P por minimos cuadrados; tolera beats perdidos (C-1: BPM cuantizado)."""
    t = np.asarray(beats, dtype=float)
    if t.size < 8:
        raise ValueError("hacen falta >= 8 beats para ajustar la grilla")
    d = np.diff(t)
    p0 = float(np.median(d))
    k = np.concatenate([[0], np.cumsum(np.round(d / p0))])   # acumulado: no arrastra el error de p0
    period, t0 = np.polyfit(k, t, 1)
    resid = t - (t0 + period * k)
    return GridFit(60.0 / period, float(t0), float(np.std(resid) * 1000))


# ----- post-proceso ----------------------------------------------------------------------

def normalize(raw: dict) -> dict:
    missing = [k for k in REQUIRED_FIELDS if k not in raw]
    if "bpm" not in raw and "essentia_bpm" not in raw:
        missing.append("bpm|essentia_bpm")
    if missing:
        raise ContractError(f"salida de songTagger sin campos requeridos: {missing}")

    warnings: list[str] = []
    beats = raw["beats"]
    grid = fit_grid(beats) if len(beats) >= 8 else None
    ess = raw.get("essentia_bpm")
    quantized = raw.get("bpm")

    if ess:
        conf = "medium"
        if grid and abs(grid.bpm - ess) <= 0.5:
            conf = "high"
        elif grid:
            warnings.append(f"BPM de essentia ({ess:.2f}) y grilla de beats ({grid.bpm:.2f}) difieren")
        bpm = {"value": round(float(ess), 2), "confidence": conf, "method": "essentia_RhythmExtractor2013"}
    elif grid:
        warnings.append("sin BPM de essentia: se usa la grilla ajustada sobre los beats de madmom")
        bpm = {"value": round(grid.bpm, 2), "confidence": "medium", "method": "grid_fit_madmom_beats"}
    else:
        warnings.append("sin BPM de essentia ni beats suficientes: BPM de songTagger (cuantizado)")
        bpm = {"value": quantized, "confidence": "low", "method": "songTagger_quantized"}
    bpm["songtagger_quantized"] = quantized
    if quantized and grid and abs(quantized - grid.bpm) > 0.2:
        warnings.append(f"BPM de songTagger ({quantized:.2f}) esta cuantizado (audit C-1); no usar")

    strength = float(raw.get("key_strength") or 0.0)
    key = {
        "value": f"{raw['key']} {raw['scale']}",
        "tonic": raw["key"], "mode": raw["scale"], "camelot": raw.get("camelot"),
        "strength": strength, "mode_reliable": False,
        "confidence": "medium" if strength >= 0.8 else "low",
    }
    warnings.append("tonalidad: el perfil edmm de essentia devuelve siempre modo menor; "
                    "la tonica es indicativa, el modo no es confiable (audit C-3)")

    out = {
        "bpm": bpm,
        "key": key,
        "beats_count": len(beats),
        "downbeats_count": len(raw.get("downbeats", [])),
        "first_downbeat_s": raw["downbeats"][0] if raw.get("downbeats") else None,
        "ignored": [k for k in IGNORED_FIELDS if k in raw],
        "warnings": warnings,
    }
    if grid:
        out["grid"] = {"bpm": round(grid.bpm, 3), "first_beat_s": round(grid.first_beat_s, 3),
                       "residual_ms": round(grid.residual_ms, 2)}
    if raw.get("madmom_error"):
        warnings.append(f"madmom fallo: {raw['madmom_error']}")
    return out


# ----- ejecucion -------------------------------------------------------------------------

def analyze(audio_path: str | Path, config: SongTaggerConfig | None = None,
            runner: Runner = default_runner) -> dict:
    cfg = config or SongTaggerConfig()
    root_w = to_wsl_path(cfg.root)
    worker = to_wsl_path(Path(__file__).with_name("_songtagger_worker.py"))
    cmd = ["wsl.exe"] + (["-d", cfg.distro] if cfg.distro else []) + [
        "-e", f"{root_w}/{cfg.python_rel}", worker, root_w, to_wsl_path(audio_path)]

    r = runner(cmd, timeout=cfg.timeout_s)
    if r.returncode != 0:
        raise SongTaggerError(f"songTagger fallo (rc={r.returncode}): {r.stderr.strip()[-600:]}")
    line = next((l for l in reversed(r.stdout.splitlines()) if l.startswith(MARKER)), None)
    if line is None:
        raise SongTaggerError("songTagger no devolvio la linea NEXO_JSON")
    out = normalize(json.loads(line[len(MARKER):]))

    out["songtagger"] = {"pinned": PINNED_COMMIT, "commit": None, "pin_ok": None}
    if cfg.check_pin:
        st = check_pin(cfg.root, runner)
        out["songtagger"].update(commit=st.actual, pin_ok=st.ok)
        if not st.ok:
            out["warnings"].append(
                f"pin de songTagger distinto: esperado {PINNED_COMMIT[:8]}, actual {(st.actual or 'desconocido')[:8]}")
    return out
