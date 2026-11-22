"""Indexa un pack de samples: metadata del nombre primero, audio solo donde hace falta (P-05).

    python -m nexo_analysis.index_pack <carpeta> --out pack.json [--include nuar]

Solo kicks, rumbles y bajos se miden (nota real); el resto queda con lo que dice
el nombre y la duracion. `key_mismatch` marca los casos en que la tonalidad del
nombre y la nota medida no coinciden.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import soundfile as sf

from . import pitch as P

AUDIO_EXT = {".wav", ".aif", ".aiff", ".flac", ".mp3"}
_NAMES = P._NAMES
_KEY_RE = re.compile(r"^([A-G])(#|b)?(m)?$")
# palabras genericas del nombre: lo que sobra es el nombre del kit
_VOCAB = {
    "kick", "one", "shot", "shots", "loop", "loops", "rumble", "bass", "synth", "fx", "trail",
    "drum", "perc", "percussion", "clap", "hat", "hi", "closed", "open", "no", "groove", "top",
    "music", "atmo", "acid", "arp", "hoover", "lead", "stab",
}
_FLAT_TO_SHARP = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}


@dataclass
class NameMeta:
    bpm: int | None
    key_name: str | None
    key_pc: int | None
    kit: str | None


def parse_name(filename: str) -> NameMeta:
    stem = Path(filename).stem
    tokens = stem.split("_")
    while tokens and tokens[0].isupper() and tokens[0].isalpha():   # prefijo del pack: ZEN_PDT_
        tokens.pop(0)

    key_name = key_pc = None
    if tokens:
        m = _KEY_RE.match(tokens[-1])
        if m:
            key_name = tokens.pop()
            root = m.group(1) + (m.group(2) or "")
            root = _FLAT_TO_SHARP.get(root, root)
            key_pc = _NAMES.index(root)

    bpm = None
    for i, t in enumerate(tokens):
        if t.isdigit() and 60 <= int(t) <= 200:
            bpm = int(t)
            tokens.pop(i)
            break

    kit_tokens = [t for t in tokens if t.lower() not in _VOCAB]
    return NameMeta(bpm, key_name, key_pc, "_".join(kit_tokens) or None)


def classify(rel_path: str) -> str:
    parts = [p.lower() for p in Path(rel_path).parts]
    name = parts[-1]
    if parts[-2:-1] == ["kick"] or "kick_one_shot" in name:
        return "kick"
    if any("rumble" in p for p in parts):
        return "rumble"
    if any("bass" in p for p in parts):
        return "bass"
    return "other"


def pc_delta(measured_pc: int, name_pc: int) -> int:
    """Semitonos (con signo, camino corto) que la nota medida esta por encima de la del nombre."""
    return ((measured_pc - name_pc + 6) % 12) - 6


def _measure(path: Path, role: str) -> dict:
    data, sr = sf.read(str(path), always_2d=True)
    res = P.analyze_kick(data, sr) if role == "kick" else P.analyze_rumble(data, sr)
    if not res.note:
        return {"note": None, "confidence": "none", "method": res.method}
    out = {
        "hz": res.hz, "note": res.note.name, "cents": res.note.cents,
        "confidence": res.confidence, "method": res.method,
        "octave_ambiguous": res.octave_ambiguous,
    }
    if role == "kick":
        out["glide_st"] = res.glide_st
    else:
        out["stability"] = res.stability
        out["peaks_hz"] = res.peaks_hz
    if res.pyin_hz is not None:
        out["pyin_hz"], out["pyin_agrees"] = res.pyin_hz, res.pyin_agrees
    return out


def _entry(root: Path, path: Path, measure: bool) -> dict:
    rel = path.relative_to(root).as_posix()
    meta = parse_name(path.name)
    role = classify(rel)
    e: dict = {
        "file": rel, "role": role, "kit": meta.kit, "bpm": meta.bpm,
        "name_key": meta.key_name, "measured_key": None, "key_mismatch": None,
        "key_delta_semitones": None,
    }
    try:
        dur = sf.info(str(path)).duration
        e["duration_s"] = round(dur, 3)
        e["bars"] = round(dur / (4 * 60.0 / meta.bpm), 2) if meta.bpm else None
        if measure and role != "other":
            m = _measure(path, role)
            e["measured"] = m
            if m.get("note"):
                e["measured_key"] = m["note"][:-1]
                if meta.key_pc is not None:
                    d = pc_delta(_NAMES.index(e["measured_key"]), meta.key_pc)
                    e["key_delta_semitones"] = d
                    e["key_mismatch"] = d != 0
    except Exception as exc:  # un archivo roto no frena el indice
        e["error"] = f"{type(exc).__name__}: {exc}"
    return e


def index_pack(root: str | Path, include: list[str] | None = None, measure: bool = True) -> dict:
    root = Path(root)
    inc = [s.lower() for s in include or []]
    files = sorted(
        p for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in AUDIO_EXT and (not inc or any(s in p.name.lower() for s in inc))
    )
    entries = []
    for i, p in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {p.name}", file=sys.stderr)
        entries.append(_entry(root, p, measure))
    roles: dict[str, int] = {}
    for e in entries:
        roles[e["role"]] = roles.get(e["role"], 0) + 1
    return {
        "root": str(root),
        "entries": entries,
        "summary": {
            "files": len(entries),
            "by_role": roles,
            "measured": sum(1 for e in entries if e.get("measured")),
            "mismatches": sum(1 for e in entries if e["key_mismatch"]),
            "errors": sum(1 for e in entries if e.get("error")),
        },
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="nexo_analysis.index_pack", description=__doc__.splitlines()[0])
    ap.add_argument("folder")
    ap.add_argument("--out", required=True)
    ap.add_argument("--include", action="append", help="solo archivos cuyo nombre contenga este texto (repetible)")
    ap.add_argument("--no-measure", action="store_true", help="solo nombres y duraciones")
    a = ap.parse_args(argv)
    out = index_pack(a.folder, include=a.include, measure=not a.no_measure)
    dest = Path(a.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out["summary"]), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
