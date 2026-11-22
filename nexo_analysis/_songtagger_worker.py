"""Se ejecuta DENTRO del venv de songTagger en WSL (essentia + madmom). No importar desde Windows.

    <songTagger>/.venv-wsl/bin/python _songtagger_worker.py <songTagger_root> <audio>

Llama a las funciones de songTagger tal cual (sin modificarlo) y expone lo que su
pipeline descarta: el BPM de essentia. Imprime una linea `NEXO_JSON:{...}`; todo lo
demas que salga por stdout (logs de madmom) se ignora.
"""
import json
import sys


def main(root: str, audio_path: str) -> dict:
    sys.path.insert(0, root)
    from analyzer.audio_loader import load_audio
    from analyzer.key_detector import detect_key
    from analyzer.rhythm import extract_rhythm, refine_beats_madmom

    audio = load_audio(audio_path)
    ess = extract_rhythm(audio)
    try:
        mm = refine_beats_madmom(audio_path)
    except Exception as exc:  # madmom es fragil; seguimos con los ticks de essentia
        mm = None
        madmom_error = f"{type(exc).__name__}: {exc}"
    else:
        madmom_error = None
    key = detect_key(audio)

    beats = mm["beats"] if mm else ess["ticks"]
    downbeats = mm["downbeats"] if mm else []
    return {
        "file": audio_path,
        "essentia_bpm": float(ess["bpm"]),
        "essentia_confidence": float(ess["confidence"]),
        "madmom_bpm": float(mm["bpm"]) if mm else None,
        "madmom_error": madmom_error,
        "bpm": float(mm["bpm"]) if mm else float(ess["bpm"]),
        "bpm_source": "madmom" if mm else "essentia_fallback",
        "beats": [round(float(b), 3) for b in beats],
        "downbeats": [round(float(b), 3) for b in downbeats],
        "key": key["key"],
        "scale": key["scale"],
        "key_strength": float(key["strength"]),
        "camelot": key["camelot"],
    }


if __name__ == "__main__":
    print("NEXO_JSON:" + json.dumps(main(sys.argv[1], sys.argv[2])))
