import numpy as np
import pytest

from nexo_analysis import pitch as P
from tests.test_nexo_analysis.synth import SR, kick, note_hz, rumble_loop, sine

F1 = note_hz(29)   # 43.654 Hz
G1 = note_hz(31)   # 48.999 Hz
A1 = 55.0


@pytest.fixture(autouse=True)
def _no_pyin(monkeypatch):
    # librosa/numba tardan en compilar; el cross-check tiene su propio test
    monkeypatch.setattr(P, "librosa_available", lambda: False)


def cents(a: float, b: float) -> float:
    return 1200 * np.log2(a / b)


def test_hz_to_note_names_and_cents():
    n = P.hz_to_note(F1)
    assert (n.name, round(n.cents)) == ("F1", 0)
    n = P.hz_to_note(A1 * 2 ** (20 / 1200))
    assert (n.name, round(n.cents)) == ("A1", 20)
    assert P.hz_to_note(note_hz(30)).name == "F#1"


def test_parabolic_peak_is_sub_bin():
    f = P.spectral_peak(sine(47.3, 1.0), SR, 30, 150)
    assert f == pytest.approx(47.3, abs=0.15)


@pytest.mark.parametrize("midi", [28, 29, 30, 31, 33])
def test_kick_fundamental_within_20_cents(midi):
    hz = note_hz(midi)
    r = P.analyze_kick(kick(hz), SR)
    assert r.note.name == P.hz_to_note(hz).name
    assert abs(cents(r.hz, hz)) < 20
    assert r.confidence in ("high", "medium")


def test_kick_glide_is_reported():
    r = P.analyze_kick(kick(F1, f_start=160), SR)
    assert r.glide_st is not None and r.glide_st > 5


def test_kick_pitch_ignores_the_click_transient():
    r = P.analyze_kick(kick(F1, click=3.0), SR)
    assert r.note.name == "F1"


def test_kick_octave_ambiguity_reports_subharmonic_with_low_confidence():
    # fundamental debil (-10.5 dB) con 2do armonico fuerte
    t = np.arange(int(0.6 * SR)) / SR
    env = np.exp(-t / 0.25)
    x = env * (0.3 * np.sin(2 * np.pi * F1 * t) + 1.0 * np.sin(2 * np.pi * 2 * F1 * t))
    r = P.analyze_kick(x, SR)
    assert r.hz == pytest.approx(F1, abs=1.0)
    assert r.octave_ambiguous is True
    assert r.confidence == "low"


def test_kick_too_short_raises():
    with pytest.raises(ValueError):
        P.analyze_kick(np.zeros(100), SR)


def test_kick_stereo_input():
    k = kick(F1)
    r = P.analyze_kick(np.stack([k, k], axis=1), SR)
    assert r.note.name == "F1"


def test_rumble_median_note_and_stability():
    r = P.analyze_rumble(rumble_loop(A1), SR)
    assert r.note.name == "A1"
    assert abs(cents(r.hz, A1)) < 20
    assert r.stability > 0.8


def test_rumble_with_pink_noise_floor():
    r = P.analyze_rumble(rumble_loop(F1, noise_db=-20, bars=4), SR)
    assert r.note.name == "F1"


def test_rumble_octave_rule():
    r = P.analyze_rumble(rumble_loop(F1, h2=3.0), SR)
    assert r.hz == pytest.approx(F1, abs=1.0)
    assert r.octave_ambiguous


def test_rumble_silence_has_no_pitch():
    r = P.analyze_rumble(np.zeros(SR * 2), SR)
    assert r.hz is None and r.confidence == "none"


def test_rumble_resolves_two_semitones_apart_when_isolated():
    f = P.analyze_rumble(rumble_loop(F1), SR)
    g = P.analyze_rumble(rumble_loop(G1), SR)
    assert (f.note.name, g.note.name) == ("F1", "G1")


def test_interval_rumble_to_kick():
    kk = P.analyze_kick(kick(G1), SR)
    rr = P.analyze_rumble(rumble_loop(F1), SR)
    iv = P.interval(kk, rr)
    assert iv.semitones_exact == pytest.approx(-2.0, abs=0.3)   # el rumble esta 2 st abajo del kick
    assert iv.pitch_coarse_rumble_to_kick == 2                  # subir el rumble +2 lo alinea
    assert abs(iv.residual_cents) < 30


def test_interval_wraps_octaves_to_minimal_shift():
    kk = P.analyze_kick(kick(F1), SR)
    rr = P.analyze_rumble(rumble_loop(note_hz(29 + 12 + 1)), SR)  # F#2
    iv = P.interval(kk, rr)
    assert iv.pitch_coarse_rumble_to_kick == -1


def test_interval_target_key():
    kk = P.analyze_kick(kick(G1), SR)
    rr = P.analyze_rumble(rumble_loop(F1), SR)
    iv = P.interval(kk, rr, target_key="F minor")
    assert iv.target_key == "F minor"
    assert iv.rumble_in_key and iv.kick_in_key
    assert iv.pitch_coarse_kick_to_key_root == -2
    assert iv.pitch_coarse_rumble_to_key_root == 0


def test_pitch_class_in_key():
    assert P.pitch_class_in_key(10, "F minor") is True    # Bb
    assert P.pitch_class_in_key(9, "F minor") is False    # A natural
    assert P.pitch_class_in_key(9, "F major") is True


def test_interval_needs_both_pitches():
    kk = P.analyze_kick(kick(F1), SR)
    silent = P.analyze_rumble(np.zeros(SR * 2), SR)
    with pytest.raises(ValueError):
        P.interval(kk, silent)


def test_pyin_crosscheck_is_skipped_without_librosa():
    r = P.analyze_kick(kick(F1), SR, crosscheck=True)
    assert r.pyin_hz is None and r.pyin_agrees is None


def test_cli_prints_measurements_and_interval(tmp_path, capsys):
    import json

    import soundfile as sf

    sf.write(tmp_path / "k.wav", kick(G1).astype(np.float32), SR)
    sf.write(tmp_path / "r.wav", rumble_loop(F1).astype(np.float32), SR)
    rc = P.main(["--kick", str(tmp_path / "k.wav"), "--rumble", str(tmp_path / "r.wav"), "--key", "F minor"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["kick"]["note"]["name"] == "G1" and out["rumble"]["note"]["name"] == "F1"
    assert out["interval"]["pitch_coarse_rumble_to_kick"] == 2


def test_rumble_with_two_competing_partials_is_low_confidence():
    # F1 y A1 al mismo nivel: no hay fundamental unica (caso real del rumble nuar)
    x = rumble_loop(F1, bars=4) + rumble_loop(A1, bars=4)
    r = P.analyze_rumble(x, SR)
    assert r.confidence == "low"
    assert r.competing_peaks
    assert {round(p) for p in r.peaks_hz[:2]} == {44, 55}


def test_rumble_single_partial_has_no_competition():
    r = P.analyze_rumble(rumble_loop(F1, bars=4), SR)
    assert r.competing_peaks == []
