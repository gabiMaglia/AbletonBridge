"""Blueprint v0.1 (stub): adaptador songTagger + loudness + pitch en el esquema de F2 §8.

Cada valor medido es {value, confidence, method}. Lo que v1 NO mide (secciones,
patrones, stems, balance espectral) queda vacio y se declara en `warnings`: no se
inventa nada.

    python -m nexo_analysis.blueprint <audio> [--role kick|rumble|bass] --out bp.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Callable

import soundfile as sf

from . import __version__, loudness, pitch

SCHEMA_VERSION = "0.1"
LOSSLESS_EXT = {".wav", ".flac", ".aif", ".aiff"}


def source_quality(path: str | Path) -> str:
    return "lossless" if Path(path).suffix.lower() in LOSSLESS_EXT else "lossy_file"


def _num(v: float | None, nd: int = 2) -> float | None:
    return round(float(v), nd) if v is not None and math.isfinite(float(v)) else None


def _m(value, confidence: str, method: str, **extra) -> dict:
    return {"value": value, "confidence": confidence, "method": method, **extra}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _note_block(res: pitch.PitchResult) -> dict:
    if not res.note:
        return {"hz": None, "note": None, "cents": None, "confidence": "none", "method": res.method}
    return {"hz": res.hz, "note": res.note.name, "cents": res.note.cents,
            "confidence": res.confidence, "method": res.method}


def build_blueprint(
    path: str | Path,
    *,
    role: str | None = None,
    adapter: Callable[[Path], dict] | None = None,
    use_ffmpeg: bool = True,
) -> dict:
    path = Path(path)
    quality = source_quality(path)
    data, sr = sf.read(str(path), always_2d=True)
    duration = len(data) / sr
    warnings: list[str] = []

    g: dict = {"duration_s": _m(round(duration, 3), "high", "decoder")}
    lossless = quality == "lossless"
    if not lossless:
        warnings.append("true peak medido sobre audio con perdida")
    try:
        lo = loudness.measure(data, sr, path=path, use_ffmpeg=use_ffmpeg)
    except ValueError as exc:  # one-shots mas cortos que un bloque de gating (0.4 s)
        warnings.append(f"loudness no medido: {exc}")
    else:
        ff = lo.method["integrated"].startswith("ffmpeg")
        lconf = "high" if lossless else "medium"
        tp_conf = ("high" if ff else "medium") if lossless else "low"
        g.update({
            "lufs_integrated": _m(_num(lo.integrated_lufs), lconf, lo.method["integrated"]),
            "true_peak_dbtp": _m(_num(lo.true_peak_dbtp), tp_conf, lo.method["true_peak"]),
            "sample_peak_dbfs": _m(_num(lo.sample_peak_dbfs), "high", lo.method["sample_peak"]),
            "lra_lu": _m(_num(lo.lra_lu), lconf, lo.method["lra"]),
            "short_term_lufs_curve": {"hop_s": lo.short_term_hop_s, "window_s": lo.short_term_window_s,
                                      "values": [_num(v) for v in lo.short_term_lufs]},
        })

    tools = {"nexo_analysis": __version__, "ffmpeg": bool(shutil.which("ffmpeg"))}
    try:
        tools["pyloudnorm"] = metadata.version("pyloudnorm")
    except metadata.PackageNotFoundError:
        tools["pyloudnorm"] = "desconocida"

    if adapter is None:
        warnings.append("sin songTagger: no hay bpm, tonalidad ni downbeats")
    else:
        st = adapter(path)
        warnings.extend(st.get("warnings", []))
        b, k = st["bpm"], st["key"]
        g["bpm"] = _m(b["value"], b["confidence"], b["method"])
        g["key"] = _m(k["value"] if "value" in k else f"{k['tonic']} {k['mode']}", k["confidence"],
                      "essentia edmm (modo no confiable)", camelot=k.get("camelot"))
        if b["value"]:
            g["bars"] = _m(round(duration / (240.0 / b["value"]), 2), b["confidence"], "duration*bpm")
        tools["songTagger"] = (st.get("songtagger") or {}).get("commit") or "desconocido"

    elements: dict = {}
    if role == "kick":
        r = pitch.analyze_kick(data, sr)
        elements["kick"] = {"note": _note_block(r),
                            "glide_st": _m(r.glide_st, "low", "hilbert_inst_freq_3_10ms")}
    elif role in ("rumble", "bass"):
        r = pitch.analyze_rumble(data, sr)
        elements[role] = {"note": _note_block(r), "stability": r.stability, "peaks_hz": r.peaks_hz}
    elif role is not None:
        raise ValueError(f"role desconocido: {role!r} (kick|rumble|bass)")
    else:
        warnings.append("elements no medidos: pasar role=kick|rumble|bass (v1 no separa stems)")
    warnings.append("sections no implementado en v1 (las de songTagger no son confiables, audit C-2)")

    return {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "kind": "file", "uri": str(path), "sha256": _sha256(path), "source_quality": quality,
            "analyzed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "tools": tools,
        },
        "global": g,
        "sections": [],
        "elements": elements,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="nexo_analysis.blueprint")
    ap.add_argument("audio")
    ap.add_argument("--role", choices=["kick", "rumble", "bass"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-songtagger", action="store_true", help="no llamar a WSL/songTagger")
    ap.add_argument("--no-ffmpeg", action="store_true")
    a = ap.parse_args(argv)
    adapter = None
    if not a.no_songtagger:
        from . import adapter_songtagger
        adapter = adapter_songtagger.analyze
    bp = build_blueprint(a.audio, role=a.role, adapter=adapter, use_ffmpeg=not a.no_ffmpeg)
    dest = Path(a.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(bp, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"blueprint -> {dest}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
