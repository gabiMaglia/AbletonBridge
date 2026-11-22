import numpy as np
import pytest

from nexo_analysis import loudness as L
from tests.test_nexo_analysis.synth import SR, sine, stereo

FFMPEG_SAMPLE = """
[Parsed_ebur128_0 @ 000001] Summary:

  Integrated loudness:
    I:         -23.0 LUFS
    Threshold: -33.0 LUFS

  Loudness range:
    LRA:         4.2 LU
    Threshold: -43.0 LUFS
    LRA low:   -26.0 LUFS
    LRA high:  -21.8 LUFS

  True peak:
    Peak:       -1.2 dBFS
"""


def test_integrated_matches_ebu_reference_sine():
    # EBU: seno estereo de -20 dBFS pico a 997 Hz mide -20 LUFS.
    x = stereo(sine(997, 20, amp=10 ** (-20 / 20)))
    r = L.measure(x, SR, use_ffmpeg=False)
    assert r.integrated_lufs == pytest.approx(-20.0, abs=0.1)
    assert r.method["integrated"] == "numeric_bs1770"


def test_integrated_scales_with_gain():
    x = stereo(sine(997, 15, amp=0.1))
    a = L.measure(x, SR, use_ffmpeg=False).integrated_lufs
    b = L.measure(x * 2, SR, use_ffmpeg=False).integrated_lufs
    assert b - a == pytest.approx(6.02, abs=0.05)


def test_integrated_agrees_with_pyloudnorm():
    import pyloudnorm as pyln

    x = stereo(sine(220, 12, amp=0.3) + sine(3000, 12, amp=0.05))
    ours = L.measure(x, SR, use_ffmpeg=False).integrated_lufs
    ref = pyln.Meter(SR).integrated_loudness(x)
    assert ours == pytest.approx(ref, abs=0.05)


def test_short_term_curve_window_and_hop():
    x = stereo(sine(997, 10, amp=0.1))
    r = L.measure(x, SR, use_ffmpeg=False)
    # ventana 3 s, hop 1 s sobre 10 s => ventanas completas en t=3..10
    assert r.short_term_hop_s == 1.0
    assert len(r.short_term_lufs) == 8
    assert all(v == pytest.approx(r.short_term_lufs[0], abs=0.05) for v in r.short_term_lufs)


def test_short_term_follows_level_step():
    x = stereo(np.concatenate([sine(997, 6, amp=0.01), sine(997, 6, amp=0.1)]))
    r = L.measure(x, SR, use_ffmpeg=False)
    assert r.short_term_lufs[0] == pytest.approx(r.short_term_lufs[-1] - 20.0, abs=0.3)


def test_lra_of_two_levels_ten_lu_apart():
    x = stereo(np.concatenate([sine(997, 30, amp=0.01), sine(997, 30, amp=10 ** (-30 / 20))]))
    r = L.measure(x, SR, use_ffmpeg=False)
    assert r.lra_lu == pytest.approx(10.0, abs=1.0)


def test_lra_steady_signal_is_zero():
    r = L.measure(stereo(sine(997, 20, amp=0.1)), SR, use_ffmpeg=False)
    assert r.lra_lu == pytest.approx(0.0, abs=0.1)


def test_true_peak_catches_intersample_peak():
    # seno a fs/4 con fase 45 grados: todas las muestras en +-0.707 pero el pico real es 1.0
    x = sine(SR / 4, 2, amp=1.0, phase=np.pi / 4)
    r = L.measure(stereo(x), SR, use_ffmpeg=False)
    assert r.sample_peak_dbfs == pytest.approx(-3.0, abs=0.1)
    assert r.true_peak_dbtp == pytest.approx(0.0, abs=0.15)
    assert r.method["true_peak"] == "numeric_4x_polyphase"


def test_mono_input_is_accepted():
    r = L.measure(sine(997, 5, amp=0.1), SR, use_ffmpeg=False)
    assert r.integrated_lufs == pytest.approx(-20.0 - 3.01, abs=0.15)


def test_parse_ffmpeg_summary():
    p = L.parse_ebur128_summary(FFMPEG_SAMPLE)
    assert p == {"integrated_lufs": -23.0, "lra_lu": 4.2, "true_peak_dbtp": -1.2}


def test_parse_ffmpeg_summary_rejects_garbage():
    with pytest.raises(ValueError):
        L.parse_ebur128_summary("nothing useful")


def test_ffmpeg_is_preferred_when_available(tmp_path, monkeypatch):
    calls = []

    def fake_run(path):
        calls.append(path)
        return L.parse_ebur128_summary(FFMPEG_SAMPLE)

    monkeypatch.setattr(L, "ffmpeg_available", lambda: True)
    monkeypatch.setattr(L, "_run_ffmpeg_ebur128", fake_run)
    r = L.measure(stereo(sine(997, 5, amp=0.1)), SR, path=tmp_path / "x.wav")
    assert calls and r.method["integrated"] == "ffmpeg_ebur128"
    assert r.integrated_lufs == -23.0 and r.true_peak_dbtp == -1.2 and r.lra_lu == 4.2
    # la curva short-term siempre es numerica
    assert r.method["short_term"] == "numeric_bs1770"


def test_falls_back_to_numeric_without_ffmpeg(monkeypatch):
    monkeypatch.setattr(L, "ffmpeg_available", lambda: False)
    r = L.measure(stereo(sine(997, 5, amp=0.1)), SR)
    assert r.method["integrated"] == "numeric_bs1770"
