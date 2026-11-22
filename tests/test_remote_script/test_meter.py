"""T-017: meter.capture — medicion de picos/nivel por pista con transporte (LOM falso, solo lectura)."""
import math
import types
from typing import List

import pytest

from remote_script.AbletonBridge import automation
from remote_script.AbletonBridge.errors import CommandError


class Vol:
    def __init__(self, raw=0.85):
        self.value, self.min, self.max = raw, 0.0, 1.0

    def str_for_value(self, raw):
        return f"{raw * 10 - 8.5:.1f} dB"


class Dev:
    def __init__(self, name, **attrs):
        self.name = name
        self.parameters = []
        for k, v in attrs.items():
            setattr(self, k, v)


class Track:
    def __init__(self, name="T", left=0.0, right=0.0, audio=True, level=None):
        self.name, self.has_audio_output = name, audio
        self.output_meter_left, self.output_meter_right = left, right
        if level is not None:
            self.output_meter_level = level
        self.mixer_device = types.SimpleNamespace(volume=Vol())
        self.devices: list = []
        self.arm = False


class Song:
    def __init__(self):
        self.tempo = 120.0
        self.current_song_time = 12.0
        self.is_playing = False
        self.record_mode = False
        self.session_automation_record = False
        self.signature_numerator, self.signature_denominator = 4, 4
        self.tracks = [Track("Kick"), Track("Bass"), Track("Midi", audio=False)]
        self.return_tracks = [Track("A-Reverb")]
        self.master_track = Track("Master")
        self.calls: List[str] = []
        self.insert_marker = 40.0

    def start_playing(self):
        self.calls.append("start")
        self.current_song_time = self.insert_marker
        self.is_playing = True

    def stop_playing(self):
        self.calls.append("stop")
        self.is_playing = False


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def params(**kw):
    base = {"start_beat": 8.0, "end_beat": 16.0, "preroll_beats": 4}
    base.update(kw)
    return base


def to_measuring(m, song):
    m.tick(song)  # queued -> seeking
    m.tick(song)  # pide el salto
    m.tick(song)  # llega al preroll
    assert m.phase == "preroll"


def at(m, song, t):
    song.current_song_time = t
    m.tick(song)


def run_all(m, song, end):
    for _ in range(3):
        m.tick(song)
    for t in range(0, end, 4):
        at(m, song, float(t))
    at(m, song, float(end))


def test_validation_rejects_bad_params() -> None:
    song = Song()
    m = automation.MeterCapture()
    for bad in (params(end_beat=8.0), params(start_beat=-1), {"end_beat": 8.0}, params(tracks=[9]),
                params(tracks=["x"]), params(tracks="some"), params(bin_bars=0), params(bin_bars=2.5),
                params(include_returns="yes"), params(calibration={"points": []}),
                params(calibration={"points": [[0.0, -6.0]]}), params(calibration={"points": [[1, 2, 3]]}),
                params(calibration={"points": [[0.5, -6.0], [0.5, -3.0]]})):
        with pytest.raises(CommandError):
            m.capture(song, bad)
    assert m.phase == "idle" and m.busy() is False


def test_capture_queues_and_reports_targets_skipping_midi_only() -> None:
    song = Song()
    m = automation.MeterCapture(clock=Clock())
    out = m.capture(song, params())
    assert out["queued"] is True and out["phase"] == "queued" and m.busy() is True
    names = [t["name"] for t in m.status(song)["targets"]]
    assert names == ["Kick", "Bass", "A-Reverb", "Master"]
    assert any("Midi" in w for w in out["warnings"])


def test_track_selection_and_flags() -> None:
    song = Song()
    m = automation.MeterCapture(clock=Clock())
    m.capture(song, params(tracks=[1], include_returns=False, include_master=False))
    t = m.status(song)["targets"]
    assert [(x["kind"], x["index"], x["name"]) for x in t] == [("track", 1, "Bass")]


def test_it_never_touches_record_mode_or_automation_arm_or_track_arm() -> None:
    song = Song()
    song.tracks[0].arm = True
    m = automation.MeterCapture(clock=Clock())
    m.capture(song, params())
    to_measuring(m, song)
    at(m, song, 8.0)
    at(m, song, 16.0)
    assert m.phase == "done"
    assert song.record_mode is False and song.session_automation_record is False
    assert song.tracks[0].arm is True


def test_measures_peak_rms_samples_and_restores_transport() -> None:
    song = Song()
    m = automation.MeterCapture(clock=Clock())
    m.capture(song, params(tracks=[0], include_returns=False, include_master=False))
    to_measuring(m, song)
    kick = song.tracks[0]
    at(m, song, 7.0)  # antes de la ventana: no cuenta
    assert m.status(song)["targets"][0]["samples"] == 0
    kick.output_meter_left, kick.output_meter_right = 0.5, 0.25
    at(m, song, 8.0)
    kick.output_meter_left, kick.output_meter_right = 0.25, 0.75
    at(m, song, 9.0)
    at(m, song, 16.0)  # >= end: termina sin contar esta muestra
    st = m.status(song)
    assert st["phase"] == "done"
    t = st["targets"][0]
    assert t["samples"] == 2
    assert t["peak_raw"] == 0.75
    # RMS crudo = sqrt(media de max(L,R)^2) = sqrt((0.25 + 0.5625) / 2)
    assert t["rms_raw"] == pytest.approx(math.sqrt((0.25 + 0.5625) / 2), abs=1e-3)
    assert t["peak_db_est"] == pytest.approx(20 * math.log10(0.75), abs=0.1)
    assert t["fader_display"] == "0.0 dB"
    assert song.is_playing is False and song.current_song_time == 12.0
    assert song.calls[-1] == "stop"


def test_bins_group_by_bars_with_per_bin_peak() -> None:
    song = Song()
    m = automation.MeterCapture(clock=Clock())
    # compas 4/4: bin_bars=1 -> 4 beats; rango 8..16 = 2 bins (compases 3 y 4)
    m.capture(song, params(tracks=[0], include_returns=False, include_master=False, bin_bars=1))
    to_measuring(m, song)
    kick = song.tracks[0]
    for t, v in ((8.0, 0.2), (9.0, 0.4), (12.0, 0.9), (13.0, 0.1)):
        kick.output_meter_left = kick.output_meter_right = v
        at(m, song, t)
    at(m, song, 16.0)
    bins = m.status(song)["targets"][0]["bins"]
    assert [(b["bar_from"], b["bar_to"]) for b in bins] == [(3, 3), (4, 4)]
    assert bins[0]["peak_raw"] == 0.4 and bins[1]["peak_raw"] == 0.9
    assert set(bins[0]) == {"bar_from", "bar_to", "peak_raw", "peak_db_est", "rms_db_est"}


def test_meter_level_is_used_when_left_right_missing_and_guarded() -> None:
    song = Song()
    tr = song.tracks[0]
    del tr.output_meter_left, tr.output_meter_right
    tr.output_meter_level = 0.6
    m = automation.MeterCapture(clock=Clock())
    m.capture(song, params(tracks=[0], include_returns=False, include_master=False))
    to_measuring(m, song)
    at(m, song, 8.0)
    at(m, song, 16.0)
    assert m.status(song)["targets"][0]["peak_raw"] == 0.6


def test_a_target_whose_meter_raises_is_isolated() -> None:
    song = Song()

    class Boom(Track):
        @property
        def output_meter_left(self):
            raise RuntimeError("meter gone")

        @output_meter_left.setter
        def output_meter_left(self, v):
            pass

    song.tracks[0] = Boom("Kick")
    song.tracks[1].output_meter_left = song.tracks[1].output_meter_right = 0.5
    m = automation.MeterCapture(clock=Clock())
    m.capture(song, params(tracks=[0, 1], include_returns=False, include_master=False))
    to_measuring(m, song)
    at(m, song, 8.0)
    at(m, song, 16.0)
    st = m.status(song)
    assert st["phase"] == "done"
    assert st["targets"][1]["peak_raw"] == 0.5
    assert st["targets"][0]["samples"] == 0 and any("Kick" in w for w in st["warnings"])


def test_calibration_interpolates_piecewise_in_log_space() -> None:
    cal = automation.MeterCalibration([[0.1, -20.0], [1.0, 0.0]])
    assert cal.to_db(1.0) == pytest.approx(0.0)
    assert cal.to_db(0.1) == pytest.approx(-20.0)
    assert cal.to_db(math.sqrt(0.1)) == pytest.approx(-10.0, abs=1e-6)  # medio camino en log
    assert cal.to_db(2.0) > 0.0  # extrapola con la pendiente del ultimo tramo
    assert cal.to_db(0.0) is None
    one = automation.MeterCalibration([[0.5, -6.0]])
    assert one.to_db(0.25) == pytest.approx(-12.0, abs=0.03)
    default = automation.MeterCalibration(None)
    assert default.to_db(0.5) == pytest.approx(20 * math.log10(0.5))
    assert default.label == "db_estimate_uncalibrated" and cal.label == "db_calibrated"


def test_capture_with_calibration_labels_the_db_field() -> None:
    song = Song()
    m = automation.MeterCapture(clock=Clock())
    m.capture(song, params(tracks=[0], include_returns=False, include_master=False,
                           calibration={"points": [[0.5, -6.0], [1.0, 0.0]]}))
    to_measuring(m, song)
    song.tracks[0].output_meter_left = song.tracks[0].output_meter_right = 0.5
    at(m, song, 8.0)
    at(m, song, 16.0)
    st = m.status(song)
    assert st["db_mapping"] == "db_calibrated"
    assert st["targets"][0]["peak_db_est"] == pytest.approx(-6.0, abs=0.05)


def test_default_mapping_is_labeled_uncalibrated() -> None:
    song = Song()
    m = automation.MeterCapture(clock=Clock())
    m.capture(song, params())
    assert m.status(song)["db_mapping"] == "db_estimate_uncalibrated"


def test_gain_reduction_unavailable_unless_a_reduction_attribute_exists() -> None:
    song = Song()
    song.tracks[0].devices = [Dev("Compressor")]
    song.tracks[1].devices = [Dev("Glue Compressor", gain_reduction=3.5)]
    m = automation.MeterCapture(clock=Clock())
    m.capture(song, params(tracks=[0, 1], include_returns=False, include_master=False))
    to_measuring(m, song)
    at(m, song, 8.0)
    song.tracks[1].devices[0].gain_reduction = 5.0
    at(m, song, 9.0)
    at(m, song, 16.0)
    t0, t1 = m.status(song)["targets"]
    assert t0["gain_reduction"] == "unavailable"
    gr = t1["gain_reduction"][0]
    assert gr["device"] == "Glue Compressor" and gr["max"] == 5.0 and gr["source"] == "gain_reduction"


def test_timeout_finalizes_with_error_and_restores() -> None:
    song = Song()
    clock = Clock()
    m = automation.MeterCapture(clock=clock)
    m.capture(song, params())
    m.tick(song)
    clock.t = 10_000.0
    m.tick(song)
    assert m.phase == "error" and "timeout" in m.errors[0]
    assert song.is_playing is False and song.current_song_time == 12.0


def test_cancel_restores_and_second_capture_is_refused_while_busy() -> None:
    song = Song()
    m = automation.MeterCapture(clock=Clock())
    m.capture(song, params())
    with pytest.raises(CommandError):
        m.capture(song, params())
    m.tick(song)
    out = m.cancel(song)
    assert out["cancelled"] is True and m.phase == "cancelled" and m.busy() is False
    assert song.is_playing is False and song.current_song_time == 12.0
    assert m.cancel(song)["cancelled"] is False


def test_a_tick_exception_never_propagates() -> None:
    song = Song()
    m = automation.MeterCapture(clock=Clock())
    m.capture(song, params())
    song.start_playing = lambda: (_ for _ in ()).throw(RuntimeError("no transport"))
    m.tick(song)
    assert m.phase == "error" and "no transport" in m.errors[0]


def test_status_payload_stays_small_for_a_big_set() -> None:
    import json

    song = Song()
    song.tracks = [Track(f"Track {i}", 0.5, 0.5) for i in range(40)]
    m = automation.MeterCapture(clock=Clock())
    m.capture(song, params(start_beat=0.0, end_beat=256.0, preroll_beats=0))
    run_all(m, song, 256)
    assert m.phase == "done"
    st = m.status(song)
    assert len(json.dumps(st)) < 60_000 and st["targets"][0]["bins"]


def test_status_drops_bins_with_a_warning_when_they_would_blow_the_budget() -> None:
    import json

    song = Song()
    song.tracks = [Track(f"Track {i}", 0.5, 0.5) for i in range(40)]
    m = automation.MeterCapture(clock=Clock())
    m.capture(song, params(start_beat=0.0, end_beat=512.0, preroll_beats=0, bin_bars=1))
    run_all(m, song, 512)
    st = m.status(song)
    assert len(json.dumps(st)) < 60_000
    assert all("bins" not in t for t in st["targets"]) and any("bins omitted" in w for w in st["warnings"])


# --- cableado en runtime ---------------------------------------------------------------


def _runtime(song):
    from remote_script.AbletonBridge import runtime

    host = types.SimpleNamespace(song=lambda: song, log_message=lambda m: None)
    return runtime.BridgeRuntime(host, None, {}, 0, range(0, 1))


def test_runtime_registers_commands_ticks_and_counts_as_busy() -> None:
    song = Song()
    rt = _runtime(song)
    h = rt._build_handlers()
    for cmd in ("meter.capture", "meter.status", "meter.cancel"):
        assert cmd in h
    assert h["meter.capture"](params())["queued"] is True
    assert rt.busy() is True
    rt.tick()
    assert h["meter.status"]({})["phase"] == "seeking"
    assert h["meter.cancel"]({})["cancelled"] is True
    assert rt.busy() is False


def test_runtime_refuses_meter_while_automation_records_and_vice_versa() -> None:
    song = Song()
    rt = _runtime(song)
    h = rt._build_handlers()
    rt.meter.capture(song, params())
    with pytest.raises(CommandError):
        h["automation.record"]({"start_beat": 8.0, "end_beat": 16.0, "lanes": []})
    rt.meter.cancel(song)
    rt.automation.phase = "recording"
    with pytest.raises(CommandError):
        h["meter.capture"](params())
    rt.automation.phase = "idle"


def test_runtime_tick_survives_a_broken_meter() -> None:
    rt = _runtime(Song())
    logs: List[str] = []
    rt.host.log_message = logs.append
    rt.meter.tick = lambda song: (_ for _ in ()).throw(RuntimeError("boom"))
    rt.tick()
    assert any("meter" in m for m in logs)
