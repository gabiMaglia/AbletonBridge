import numpy as np
import pytest
import soundfile as sf

from nexo_analysis import blueprint as B
from tests.test_nexo_analysis.synth import SR, kick, note_hz, rumble_loop


def fake_adapter(path):
    return {
        "bpm": {"value": 134.0, "confidence": "high", "method": "essentia_RhythmExtractor2013"},
        "key": {"tonic": "F", "mode": "minor", "camelot": "4A", "mode_reliable": False, "confidence": "medium"},
        "downbeats_count": 40,
        "warnings": ["modo siempre menor"],
        "songtagger": {"commit": "abc", "pin_ok": True},
    }


def is_measure(v):
    return isinstance(v, dict) and {"value", "confidence", "method"} <= set(v)


def test_blueprint_for_rumble_sample(tmp_path):
    p = tmp_path / "rumble.wav"
    sf.write(p, np.stack([rumble_loop(note_hz(29), bars=4)] * 2, axis=1).astype(np.float32), SR)
    bp = B.build_blueprint(p, role="rumble", adapter=fake_adapter, use_ffmpeg=False)

    assert bp["schema_version"] == "0.1"
    assert bp["source"]["kind"] == "file" and len(bp["source"]["sha256"]) == 64
    assert bp["source"]["source_quality"] == "lossless"
    assert "pyloudnorm" in bp["source"]["tools"]

    g = bp["global"]
    for k in ("duration_s", "bpm", "lufs_integrated", "true_peak_dbtp", "lra_lu"):
        assert is_measure(g[k]), k
    assert g["bpm"]["value"] == 134.0
    assert g["key"]["value"] == "F minor" and g["key"]["camelot"] == "4A"
    assert g["short_term_lufs_curve"]["hop_s"] == 1.0

    rum = bp["elements"]["rumble"]
    assert rum["note"]["note"] == "F1" and rum["note"]["confidence"] in ("high", "medium")
    assert bp["sections"] == []
    assert any("sections" in w for w in bp["warnings"])
    assert "modo siempre menor" in bp["warnings"]


def test_blueprint_for_kick_has_glide(tmp_path):
    p = tmp_path / "kick.wav"
    sf.write(p, kick(note_hz(31)).astype(np.float32), SR)
    bp = B.build_blueprint(p, role="kick", adapter=None, use_ffmpeg=False)
    k = bp["elements"]["kick"]
    assert k["note"]["note"] == "G1" and k["glide_st"]["value"] > 5
    assert "bpm" not in bp["global"]            # sin adaptador no se inventa tempo
    assert any("songTagger" in w for w in bp["warnings"])


def test_lossy_extension_is_flagged(tmp_path):
    assert B.source_quality(tmp_path / "a.mp3") == "lossy_file"
    assert B.source_quality(tmp_path / "a.flac") == "lossless"


def test_json_serializable(tmp_path):
    import json

    p = tmp_path / "k.wav"
    sf.write(p, kick(note_hz(29)).astype(np.float32), SR)
    json.dumps(B.build_blueprint(p, role="kick", adapter=fake_adapter, use_ffmpeg=False))


def test_one_shot_shorter_than_a_gating_block_skips_loudness(tmp_path):
    p = tmp_path / "k.wav"
    sf.write(p, kick(note_hz(31), secs=0.3).astype(np.float32), SR)
    bp = B.build_blueprint(p, role="kick", adapter=None, use_ffmpeg=False)
    assert "lufs_integrated" not in bp["global"]
    assert any("loudness" in w for w in bp["warnings"])
    assert bp["elements"]["kick"]["note"]["note"] == "G1"
