import json

import numpy as np
import pytest
import soundfile as sf

from nexo_analysis import index_pack as IP
from tests.test_nexo_analysis.synth import SR, kick, note_hz, rumble_loop

F1 = note_hz(29)
G1 = note_hz(31)


def test_parse_name_loop_with_bpm_and_key():
    m = IP.parse_name("ZEN_PDT_134_rumble_loop_nuar_F.wav")
    assert (m.bpm, m.key_name, m.key_pc, m.kit) == (134, "F", 5, "nuar")


def test_parse_name_one_shot_sharp_key():
    m = IP.parse_name("ZEN_PDT_kick_one_shot_azure_F#.wav")
    assert (m.bpm, m.key_name, m.key_pc, m.kit) == (None, "F#", 6, "azure")


def test_parse_name_no_key():
    m = IP.parse_name("ZEN_PDT_clap_one_shot_nuar.wav")
    assert m.key_name is None and m.kit == "nuar"


def test_parse_name_fx_trail_variant_keeps_kit():
    m = IP.parse_name("ZEN_PDT_134_bass_synth_loop_crisp_fx_trail_F#.wav")
    assert m.kit == "crisp" and m.key_name == "F#"


def test_parse_name_multiword_kit():
    assert IP.parse_name("ZEN_PDT_synth_one_shot_interval_it_F.wav").kit == "interval_it"


@pytest.mark.parametrize(
    "rel, role",
    [
        ("one_shots/drums/kick/ZEN_PDT_kick_one_shot_nuar_G.wav", "kick"),
        ("loops/rumble_loops/ZEN_PDT_134_rumble_loop_nuar_F.wav", "rumble"),
        ("loops/bass_synth_loops/ZEN_PDT_134_bass_synth_loop_nuar_F.wav", "bass"),
        ("one_shots/bass_synth_one_shots/ZEN_PDT_bass_synth_one_shot_x_F.wav", "bass"),
        ("loops/drum_loops/drum_loops_no_kick/ZEN_PDT_134_drum_loop_no_kick_nuar_F.wav", "other"),
        ("loops/drum_loops/drum_grooves/ZEN_PDT_134_drum_loop_groove_nuar_F.wav", "other"),
        ("loops/music_loops/ZEN_PDT_134_music_loop_nuar_F.wav", "other"),
    ],
)
def test_classify(rel, role):
    assert IP.classify(rel) == role


def test_pitch_class_delta_signed_and_wrapped():
    assert IP.pc_delta(5, 5) == 0
    assert IP.pc_delta(7, 5) == 2        # medido 2 st sobre el nombre
    assert IP.pc_delta(11, 0) == -1
    assert IP.pc_delta(0, 11) == 1


def _write(tmp, rel, data):
    p = tmp / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    sf.write(p, data.astype(np.float32), SR)
    return p


def test_index_measures_only_kick_rumble_bass_and_flags_mismatch(tmp_path):
    _write(tmp_path, "one_shots/drums/kick/ZEN_PDT_kick_one_shot_nuar_G.wav", kick(F1))   # nombre G, audio F
    _write(tmp_path, "loops/rumble_loops/ZEN_PDT_134_rumble_loop_nuar_F.wav", rumble_loop(F1, bpm=134, bars=2))
    _write(tmp_path, "loops/music_loops/ZEN_PDT_134_music_loop_nuar_F.wav", rumble_loop(F1, bpm=134, bars=2))
    (tmp_path / "loops/rumble_loops/ZEN_PDT_134_rumble_loop_nuar_F.wav.asd").write_bytes(b"x")

    out = IP.index_pack(tmp_path)
    by = {e["file"].split("/")[-1]: e for e in out["entries"]}
    assert len(by) == 3                                   # el .asd se ignora

    k = by["ZEN_PDT_kick_one_shot_nuar_G.wav"]
    assert k["role"] == "kick" and k["name_key"] == "G"
    assert k["measured_key"] == "F" and k["measured"]["note"] == "F1"
    assert k["key_mismatch"] is True and k["key_delta_semitones"] == -2

    r = by["ZEN_PDT_134_rumble_loop_nuar_F.wav"]
    assert r["measured_key"] == "F" and r["key_mismatch"] is False
    assert r["duration_s"] == pytest.approx(2 * 4 * 60 / 134, abs=0.01)
    assert r["bars"] == pytest.approx(2.0, abs=0.01)

    o = by["ZEN_PDT_134_music_loop_nuar_F.wav"]
    assert o["role"] == "other" and "measured" not in o and o["key_mismatch"] is None

    assert out["summary"]["measured"] == 2 and out["summary"]["mismatches"] == 1


def test_include_filter(tmp_path):
    _write(tmp_path, "one_shots/drums/kick/ZEN_PDT_kick_one_shot_nuar_G.wav", kick(G1))
    _write(tmp_path, "one_shots/drums/kick/ZEN_PDT_kick_one_shot_acido_F.wav", kick(F1))
    out = IP.index_pack(tmp_path, include=["nuar"])
    assert [e["kit"] for e in out["entries"]] == ["nuar"]


def test_cli_writes_json(tmp_path):
    _write(tmp_path, "one_shots/drums/kick/ZEN_PDT_kick_one_shot_nuar_F.wav", kick(F1))
    dest = tmp_path / "o" / "idx.json"
    assert IP.main([str(tmp_path), "--out", str(dest), "--include", "nuar"]) == 0
    data = json.loads(dest.read_text(encoding="utf-8"))
    assert data["entries"][0]["measured_key"] == "F"


def test_unreadable_file_is_reported_not_fatal(tmp_path):
    p = tmp_path / "one_shots/drums/kick/ZEN_PDT_kick_one_shot_bad_F.wav"
    p.parent.mkdir(parents=True)
    p.write_bytes(b"not audio")
    out = IP.index_pack(tmp_path)
    assert out["entries"][0]["error"]
