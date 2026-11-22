"""T-012: automation.record — lane real de automatizacion grabada (maquina de estados) con LOM falso."""
import types
from typing import Any, List, Optional

import pytest

from remote_script.AbletonBridge import automation, errors
from remote_script.AbletonBridge.errors import CommandError


class P:
    """Parametro con display lineal 'N %' (raw 0..1 -> 0..100) para probar {"display": n}."""

    def __init__(self, name, lo=0.0, hi=1.0, value=0.0, fail_set=False):
        self.name, self.min, self.max = name, lo, hi
        self._value, self.fail_set = value, fail_set
        self.writes: List[float] = []

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        if self.fail_set:
            raise RuntimeError("param rejected")
        self._value = v
        self.writes.append(v)

    def str_for_value(self, raw):
        return f"{(raw - self.min) / (self.max - self.min) * 100:.1f} %"


class Dev:
    def __init__(self, name, params):
        self.name, self.parameters = name, params


class Track:
    def __init__(self, name="T", armed=False, can_arm=True):
        self.name, self.arm, self.can_be_armed = name, armed, can_arm
        self.mixer_device = types.SimpleNamespace(
            volume=P("Volume", 0.0, 1.0, 0.5), panning=P("Pan", -1.0, 1.0, 0.0),
            sends=[P("Send A", 0.0, 1.0, 0.0)])
        self.devices = [Dev("Auto Filter", [P("Frequency", 20.0, 20000.0, 20000.0), P("Resonance", 0.0, 1.0)])]


class Song:
    def __init__(self, tracks=None):
        self.tempo = 120.0
        self.current_song_time = 12.0
        self.is_playing = False
        self.record_mode = False
        self.session_automation_record = False
        self.tracks = tracks if tracks is not None else [Track("Kick"), Track("Bass")]
        self.return_tracks = [Track("A-Reverb")]
        self.master_track = Track("Master")
        self.master_track.mixer_device.sends = []
        self.calls: List[str] = []
        self.insert_marker = 40.0

    def start_playing(self):
        # Live real: start_playing arranca desde el marcador de inicio, no desde current_song_time
        self.calls.append("start")
        self.current_song_time = self.insert_marker
        self.is_playing = True

    def continue_playing(self):
        # Live real: continue_playing arranca desde current_song_time
        self.calls.append("continue")
        self.is_playing = True

    def stop_playing(self):
        self.calls.append("stop")
        self.is_playing = False


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def lane(track=0, target="volume", points=((8.0, 0.0), (16.0, 1.0))):
    return {"track": track, "target": target, "points": [list(p) for p in points]}


def params(**kw):
    base = {"start_beat": 8.0, "end_beat": 16.0, "lanes": [lane()], "preroll_beats": 4}
    base.update(kw)
    return base


def drive(rec, song, t):
    """Mueve el playhead a `t` (transporte andando) y corre un tick."""
    song.current_song_time = t
    rec.tick(song)


def to_recording(rec, song):
    rec.tick(song)  # queued -> seeking
    rec.tick(song)  # seeking -> preroll (start_playing)
    drive(rec, song, 8.0)  # punch-in
    assert rec.phase == "recording"


# --- validacion ----------------------------------------------------------------


@pytest.mark.parametrize("bad", [
    {"lanes": []},
    {"lanes": "x"},
    {"end_beat": 8.0},
    {"start_beat": -1.0},
    {"preroll_beats": -1},
    {"lanes": [lane(points=())]},
    {"lanes": [lane(points=((9.0, 0.1), (8.0, 0.2)))]},
    {"lanes": [lane(points=((8.0, 5.0),))]},
    {"lanes": [lane(target="nope")]},
    {"lanes": [lane(target={"device": "Auto Filter", "param": "Nope"})]},
    {"lanes": [lane(track=99)]},
    {"lanes": [lane(track={"return": 7})]},
    {"lanes": [lane(track="master", target={"send": 0})]},
    {"lanes": [lane(points=((8.0, {"display": "x"}),))]},
])
def test_invalid_params_rejected_without_touching_the_set(bad) -> None:
    song, rec = Song(), automation.AutomationRecorder()
    with pytest.raises(CommandError) as e:
        rec.record(song, params(**bad))
    assert e.value.code == errors.INVALID_PARAMS
    assert rec.phase == "idle" and song.session_automation_record is False and song.calls == []


def test_queue_response_and_nothing_applied_until_the_first_tick() -> None:
    song, rec = Song(), automation.AutomationRecorder()
    out = rec.record(song, params())
    assert out["queued"] is True and out["tempo"] == 120.0 and out["lanes"] == 1
    assert out["expected_seconds"] == pytest.approx((8.0 + 4.0) * 60 / 120)
    assert rec.phase == "queued" and song.session_automation_record is False and song.calls == []


def test_second_record_while_running_is_rejected() -> None:
    song, rec = Song(), automation.AutomationRecorder()
    rec.record(song, params())
    with pytest.raises(CommandError):
        rec.record(song, params())


# --- interpolacion -------------------------------------------------------------


def test_interp_is_linear_and_holds_at_the_ends() -> None:
    pts = [(8.0, 0.0), (12.0, 1.0), (16.0, 0.5)]
    assert automation.interp(pts, 0.0) == 0.0
    assert automation.interp(pts, 10.0) == pytest.approx(0.5)
    assert automation.interp(pts, 14.0) == pytest.approx(0.75)
    assert automation.interp(pts, 99.0) == 0.5
    assert automation.interp([(3.0, 0.7)], 50.0) == 0.7


def test_display_values_are_resolved_to_raw_once_up_front() -> None:
    song, rec = Song(), automation.AutomationRecorder()
    pts = ((8.0, {"display": 25}), (16.0, {"display": 75}))
    rec.record(song, params(lanes=[lane(points=pts)]))
    assert rec._lanes[0].points == [(8.0, pytest.approx(0.25, abs=0.01)), (16.0, pytest.approx(0.75, abs=0.01))]


# --- setup / punch-in ------------------------------------------------------------


def test_first_tick_saves_state_arms_automation_and_seeks_to_preroll() -> None:
    song = Song(tracks=[Track("Kick", armed=True), Track("Bass"), Track("Lead", armed=True)])
    song.record_mode = True
    rec = automation.AutomationRecorder()
    rec.record(song, params())
    rec.tick(song)
    assert song.session_automation_record is True and song.record_mode is False
    assert song.current_song_time == 4.0 and rec.phase == "seeking"
    assert [t.arm for t in song.tracks] == [False, False, False]
    assert [d["name"] for d in rec.status(song)["disarmed_tracks"]] == ["Kick", "Lead"]
    assert song.tracks[0].mixer_device.volume.value == 0.0  # valor en start_beat antes de reproducir
    assert song.calls == []  # aun no arranco el transporte


def test_preroll_is_clamped_at_zero() -> None:
    song, rec = Song(), automation.AutomationRecorder()
    rec.record(song, params(start_beat=2.0, end_beat=6.0, lanes=[lane(points=((2.0, 0.0), (6.0, 1.0)))]))
    rec.tick(song)
    assert song.current_song_time == 0.0


def test_transport_starts_only_after_the_playhead_arrives() -> None:
    song, rec = Song(), automation.AutomationRecorder()
    rec.record(song, params())
    rec.tick(song)
    song.current_song_time = 12.0  # Live todavia no aplico el seek
    rec.tick(song)
    assert rec.phase == "seeking" and song.calls == []
    song.current_song_time = 4.0
    rec.tick(song)
    assert rec.phase == "preroll" and song.calls == ["continue"]


def test_punch_in_exactly_when_song_time_reaches_start_beat() -> None:
    song, rec = Song(), automation.AutomationRecorder()
    rec.record(song, params())
    rec.tick(song)
    rec.tick(song)
    drive(rec, song, 6.0)
    assert song.record_mode is False and rec.phase == "preroll"
    drive(rec, song, 7.99)
    assert song.record_mode is False
    drive(rec, song, 8.0)
    assert song.record_mode is True and rec.phase == "recording"


def test_preroll_waits_while_transport_is_not_playing() -> None:
    song, rec = Song(), automation.AutomationRecorder()
    rec.record(song, params())
    rec.tick(song)
    rec.tick(song)
    song.is_playing = False
    drive(rec, song, 9.0)
    assert song.record_mode is False and rec.phase == "preroll"


# --- escritura --------------------------------------------------------------------


def test_every_tick_writes_the_interpolated_value_only_when_it_changed() -> None:
    song, rec = Song(), automation.AutomationRecorder()
    rec.record(song, params())
    to_recording(rec, song)
    vol = song.tracks[0].mixer_device.volume
    drive(rec, song, 12.0)
    assert vol.value == pytest.approx(0.5)
    n = len(vol.writes)
    drive(rec, song, 12.0)  # mismo tiempo: sin cambio, sin escritura
    drive(rec, song, 12.0 + 1e-9)
    assert len(vol.writes) == n
    drive(rec, song, 14.0)
    assert vol.value == pytest.approx(0.75) and len(vol.writes) == n + 1
    lane_status = rec.status(song)["lanes"][0]
    assert lane_status["writes"] >= 2 and lane_status["last_value"] == pytest.approx(0.75)
    assert lane_status["param_name"] == "Volume" and lane_status["track"] == 0


def test_punch_in_writes_the_start_value_inside_the_record_window() -> None:
    song, rec = Song(), automation.AutomationRecorder()
    rec.record(song, params())
    to_recording(rec, song)
    assert song.tracks[0].mixer_device.volume.writes[-1] == 0.0  # forzado al punchear


def test_all_target_kinds_are_written() -> None:
    song, rec = Song(), automation.AutomationRecorder()
    lanes = [
        lane(0, "pan", ((8.0, -1.0), (16.0, 1.0))),
        lane(0, {"send": 0}),
        lane(1, {"device": "Auto Filter", "param": "Frequency"}, ((8.0, 20.0), (16.0, 20000.0))),
        lane(0, {"device": 0, "param": "Resonance"}),
        lane({"return": 0}, "volume"),
        lane("master", "volume"),
    ]
    rec.record(song, params(lanes=lanes))
    to_recording(rec, song)
    drive(rec, song, 12.0)
    assert song.tracks[0].mixer_device.panning.value == pytest.approx(0.0)
    assert song.tracks[0].mixer_device.sends[0].value == pytest.approx(0.5)
    assert song.tracks[1].devices[0].parameters[0].value == pytest.approx(10010.0)
    assert song.tracks[0].devices[0].parameters[1].value == pytest.approx(0.5)
    assert song.return_tracks[0].mixer_device.volume.value == pytest.approx(0.5)
    assert song.master_track.mixer_device.volume.value == pytest.approx(0.5)


# --- fin / restore ------------------------------------------------------------------


def finish_setup(armed=(True, False)):
    song = Song(tracks=[Track("Kick", armed=armed[0]), Track("Bass", armed=armed[1])])
    song.session_automation_record = False
    rec = automation.AutomationRecorder()
    rec.record(song, params())
    return song, rec


def test_end_beat_stops_transport_and_restores_everything() -> None:
    song, rec = finish_setup()
    to_recording(rec, song)
    drive(rec, song, 12.0)
    drive(rec, song, 16.0)
    assert rec.phase == "done"
    assert song.record_mode is False and song.is_playing is False
    assert song.session_automation_record is False  # estado previo
    assert song.current_song_time == 12.0  # playhead original
    assert [t.arm for t in song.tracks] == [True, False]  # re-armado
    st = rec.status(song)
    assert st["progress"] == 1.0 and st["errors"] == []
    assert song.tracks[0].mixer_device.volume.value == pytest.approx(1.0)  # valor final escrito


def test_previous_automation_arm_true_is_restored_as_true() -> None:
    song, rec = Song(), automation.AutomationRecorder()
    song.session_automation_record = True
    rec.record(song, params())
    to_recording(rec, song)
    drive(rec, song, 16.0)
    assert song.session_automation_record is True


def test_status_progress_and_shape_while_recording() -> None:
    song, rec = finish_setup()
    st = rec.status(song)
    assert st["phase"] == "queued" and st["progress"] == 0.0
    to_recording(rec, song)
    drive(rec, song, 12.0)
    st = rec.status(song)
    assert set(st) >= {"phase", "progress", "current_beat", "lanes", "errors", "disarmed_tracks"}
    assert st["progress"] == pytest.approx(0.5) and st["current_beat"] == 12.0
    assert st["phase"] == "recording"


def test_cancel_mid_recording_restores_and_reports() -> None:
    song, rec = finish_setup()
    to_recording(rec, song)
    drive(rec, song, 10.0)
    out = rec.cancel(song)
    assert out["cancelled"] is True and rec.phase == "cancelled"
    assert song.record_mode is False and song.is_playing is False
    assert song.session_automation_record is False and song.current_song_time == 12.0
    assert song.tracks[0].arm is True


def test_cancel_when_idle_is_a_noop() -> None:
    song, rec = Song(), automation.AutomationRecorder()
    assert rec.cancel(song)["cancelled"] is False and rec.phase == "idle"


def test_cancel_while_queued_never_touches_the_set() -> None:
    song, rec = finish_setup()
    out = rec.cancel(song)
    assert out["cancelled"] is True and song.calls == [] and song.session_automation_record is False


def test_wall_clock_timeout_goes_to_error_and_restores() -> None:
    clock, song = Clock(), finish_setup()[0]
    rec = automation.AutomationRecorder(clock=clock)
    rec.record(song, params())
    rec.tick(song)
    rec.tick(song)  # preroll, el transporte no avanza
    clock.t = 10_000.0
    rec.tick(song)
    assert rec.phase == "error" and "timeout" in rec.status(song)["errors"][0].lower()
    assert song.record_mode is False and song.is_playing is False and song.tracks[0].arm is True


def test_timeout_scales_with_the_length_of_the_recording() -> None:
    clock, song = Clock(), Song()
    rec = automation.AutomationRecorder(clock=clock)
    # 192 compases a 134 BPM (~6 min): a los 7 min de reloj NO debe haber vencido
    song.tempo = 134.0
    rec.record(song, params(start_beat=0.0, end_beat=768.0, lanes=[lane(points=((0.0, 0.0), (768.0, 1.0)))]))
    rec.tick(song)
    rec.tick(song)
    clock.t = 7 * 60.0
    drive(rec, song, 0.0)
    assert rec.phase in ("preroll", "recording")


def test_param_error_during_recording_is_isolated_and_restores() -> None:
    song, rec = finish_setup()
    to_recording(rec, song)
    song.tracks[0].mixer_device.volume.fail_set = True
    drive(rec, song, 12.0)  # no debe propagar
    assert rec.phase == "error" and rec.status(song)["errors"]
    assert song.record_mode is False and song.is_playing is False and song.tracks[0].arm is True


def test_setup_failure_goes_to_error_without_raising() -> None:
    class BoomSong(Song):
        explode = False

        @property
        def session_automation_record(self):
            return False

        @session_automation_record.setter
        def session_automation_record(self, v):
            if self.explode:
                raise RuntimeError("no arm")

    song, rec = BoomSong(), automation.AutomationRecorder()
    song.explode = True
    rec.record(song, params())
    rec.tick(song)
    assert rec.phase == "error" and rec.status(song)["errors"]
    assert song.record_mode is False


def test_a_finished_recorder_accepts_a_new_recording() -> None:
    song, rec = finish_setup()
    to_recording(rec, song)
    drive(rec, song, 16.0)
    assert rec.phase == "done"
    assert rec.record(song, params())["queued"] is True and rec.phase == "queued"


def test_tick_when_idle_is_noop() -> None:
    automation.AutomationRecorder().tick(Song())


def test_busy_only_while_a_recording_is_in_flight() -> None:
    song, rec = Song(), automation.AutomationRecorder()
    assert rec.busy() is False
    rec.record(song, params())
    assert rec.busy() is True
    rec.cancel(song)
    assert rec.busy() is False


# --- automation.clear ----------------------------------------------------------------


def test_clear_reports_unsupported_when_the_lom_has_no_api() -> None:
    song = Song()
    out = automation.clear(song, {"track": 0, "target": "volume"})
    assert out["supported"] is False and out["cleared"] is False and out["param_name"] == "Volume"


def test_clear_calls_the_lom_when_it_exists() -> None:
    song = Song()
    seen: List[Any] = []
    song.tracks[0].mixer_device.volume.clear_automation = lambda *a: seen.append(a)
    out = automation.clear(song, {"track": 0, "target": "volume", "start_beat": 8.0, "end_beat": 16.0})
    assert out["supported"] is True and out["cleared"] is True and seen == [(8.0, 16.0)]


def test_clear_validates_target_and_range() -> None:
    song = Song()
    with pytest.raises(CommandError):
        automation.clear(song, {"track": 0, "target": "nope"})
    with pytest.raises(CommandError):
        automation.clear(song, {"track": 0, "target": "volume", "start_beat": 8.0})
    with pytest.raises(CommandError):
        automation.clear(song, {"track": 0, "target": "volume", "start_beat": 8.0, "end_beat": 4.0})


# --- cableado en runtime ---------------------------------------------------------------


def _runtime(song):
    from remote_script.AbletonBridge import runtime

    host = types.SimpleNamespace(song=lambda: song, log_message=lambda m: None)
    rt = runtime.BridgeRuntime(host, None, {}, 0, range(0, 1))
    return rt


def test_runtime_registers_the_four_commands_and_ticks_the_recorder() -> None:
    song = Song()
    rt = _runtime(song)
    h = rt.server._handlers if hasattr(rt.server, "_handlers") else rt._build_handlers()
    for cmd in ("automation.record", "automation.status", "automation.cancel", "automation.clear"):
        assert cmd in h
    assert h["automation.record"](params())["queued"] is True
    assert rt.busy() is True
    rt.tick()  # queued -> seeking
    assert song.session_automation_record is True
    assert h["automation.status"]({})["phase"] == "seeking"
    assert h["automation.cancel"]({})["cancelled"] is True
    assert rt.busy() is False and song.session_automation_record is False


def test_runtime_tick_survives_a_broken_recorder() -> None:
    rt = _runtime(Song())
    logs: List[str] = []
    rt.host.log_message = logs.append
    rt.automation.tick = lambda song: (_ for _ in ()).throw(RuntimeError("boom"))
    rt.tick()
    assert any("automation" in m for m in logs)


def test_transport_starts_from_seek_position_not_insert_marker():
    # Visto en Live 12.4.16: start_playing() arranca desde el marcador de inicio (ej. 160)
    # aunque current_song_time apunte al preroll; hay que usar continue_playing().
    song = Song()
    rec = automation.AutomationRecorder(clock=Clock())
    rec.record(song, {"start_beat": 100.0, "end_beat": 108.0, "preroll_beats": 4,
                      "lanes": [{"track": 0, "target": "volume", "points": [[100.0, 0.2], [108.0, 0.8]]}]})
    for _ in range(3):
        rec.tick(song)
    assert "continue" in song.calls and "start" not in song.calls
    assert song.current_song_time == 96.0
