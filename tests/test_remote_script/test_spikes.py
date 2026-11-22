"""Spikes de automatizacion en Arrangement (T-002c) contra un LOM falso."""
import types
from typing import Any, List

import pytest

from remote_script.AbletonBridge import spikes


class P:
    def __init__(self, name, lo=0.0, hi=1.0, default=0.5):
        self.name, self.min, self.max, self.default_value = name, lo, hi, default
        self.value = default
        self.automation_state = 0


class Env:
    def __init__(self):
        self.steps: List[tuple] = []

    def insert_step(self, t, d, v):
        self.steps.append((t, d, v))

    def value_at_time(self, t):
        cur = self.steps[0][2] if self.steps else 0.0
        for st, _d, v in self.steps:
            if st <= t:
                cur = v
        return cur


class Clip:
    def __init__(self, length, start=0.0):
        self.length, self.start_time, self.end_time = length, start, start + length
        self.notes: Any = None
        self.envs = {}

    def create_automation_envelope(self, param):
        self.envs[id(param)] = Env()
        return self.envs[id(param)]

    def automation_envelope(self, param):
        return self.envs.get(id(param))

    def add_new_notes(self, specs):
        self.notes = specs


class Slot:
    has_clip = False
    clip = None

    def create_clip(self, length):
        self.clip, self.has_clip = Clip(length), True


class Device:
    def __init__(self, name, params):
        self.name = name
        self.parameters = [P(n) for n in params]


DEVICE_PARAMS = {
    "Operator": ["Device On", "Transpose", "Osc A Level"],
    "Auto Filter": ["Device On", "Frequency", "Resonance"],
}


class Track:
    def __init__(self, fail_insert=False, arrangement_envs=False):
        self.name = ""
        self.devices: List[Device] = []
        self.clip_slots = [Slot()]
        self.arrangement_clips: List[Clip] = []
        self.mixer_device = types.SimpleNamespace(volume=P("Volume", 0.0, 1.0, 0.85))
        self.fail_insert, self.arr_envs = fail_insert, arrangement_envs

    def insert_device(self, name, idx):
        if self.fail_insert:
            raise RuntimeError("no insert_device")
        self.devices.insert(idx, Device(name, DEVICE_PARAMS[name]))

    def duplicate_clip_to_arrangement(self, clip, t):
        c = Clip(clip.length, t)
        if self.arr_envs:
            c.envs = dict(clip.envs)
        self.arrangement_clips.append(c)
        return c


class Song:
    def __init__(self, **track_kw):
        self.tracks = [types.SimpleNamespace(name="Keep me")]
        self.track_kw = track_kw
        self.tempo = 120.0
        self.current_song_time = 0.0
        self.record_mode = False
        self.is_playing = False
        self.session_automation_record = False
        self.arrangement_overdub = False

    def create_midi_track(self, idx):
        self.tracks.append(Track(**self.track_kw))

    def delete_track(self, i):
        del self.tracks[i]

    def start_playing(self):
        self.is_playing = True

    def stop_playing(self):
        self.is_playing = False


@pytest.fixture
def live(fake_live):
    class Spec:
        def __init__(self, **kw):
            self.__dict__.update(kw)

    fake_live.Clip.MidiNoteSpecification = Spec
    return fake_live


def test_session_builds_track_envelopes_and_reports(live) -> None:
    song = Song()
    out = spikes.automation_session(song, live, {"bars": 2})
    t = song.tracks[1]
    assert t.name == "SPIKE-AUTO-SESSION" and out["track_index"] == 1
    assert [d.name for d in t.devices] == ["Operator", "Auto Filter"]
    assert out["autofilter_param_names"] == ["Device On", "Frequency", "Resonance"]
    clip = t.clip_slots[0].clip
    assert clip.length == 8.0 and len(clip.notes) == 8
    assert out["envelopes_created"] == {"volume": True, "filter_freq": True}
    assert len(clip.envs) == 2
    assert out["arrangement_clips"][0]["start_time"] == 0.0
    assert out["arrangement_envelope"]["volume"]["present"] is False
    assert out["automation_state"]["volume"] == 0
    assert out["steps"]["create_track"] == {"ok": True, "error": None}


def test_session_readback_values_ramp_up(live) -> None:
    out = spikes.automation_session(Song(), live, {"bars": 1})
    samples = out["session_envelope_readback"]["volume"]
    assert samples[0]["value"] < samples[-1]["value"]


def test_session_arrangement_envelope_samples_when_present(live) -> None:
    out = spikes.automation_session(Song(arrangement_envs=True), live, {"bars": 1})
    arr = out["arrangement_envelope"]["volume"]
    assert arr["present"] is True and arr["samples"]


def test_session_survives_insert_device_failure(live) -> None:
    out = spikes.automation_session(Song(fail_insert=True), live, {"bars": 1})
    assert out["steps"]["insert_devices"]["ok"] is False
    assert "no insert_device" in out["steps"]["insert_devices"]["error"]
    assert out["envelopes_created"]["volume"] is True
    assert out["envelopes_created"]["filter_freq"] is False


def test_session_note_api_failure_is_reported(fake_live) -> None:
    out = spikes.automation_session(Song(), fake_live, {"bars": 1})  # sin MidiNoteSpecification
    assert out["steps"]["add_notes"]["ok"] is False
    assert out["steps"]["duplicate_to_arrangement"]["ok"] is True


def test_record_start_sets_transport_and_does_not_block(live) -> None:
    song = Song()
    r = spikes.RecordSpike()
    out = r.start(song, live, {"start_beat": 32.0, "bars": 2})
    assert out["started"] is True
    assert song.current_song_time == 32.0 and song.record_mode and song.is_playing
    assert song.tracks[1].name == "SPIKE-AUTO-RECORD"
    assert [d.name for d in song.tracks[1].devices] == ["Operator"]
    assert out["operator_param"] == "Transpose"
    assert r.status(song)["phase"] == "running"


def test_record_tick_ramps_then_finishes(live) -> None:
    song = Song()
    r = spikes.RecordSpike()
    r.start(song, live, {"start_beat": 32.0, "bars": 1})
    vol = song.tracks[1].mixer_device.volume
    song.current_song_time = 34.0
    r.tick()
    assert vol.value == pytest.approx(0.85 * 0.5)
    song.current_song_time = 36.5
    r.tick()
    st = r.status(song)
    assert st["phase"] == "done" and st["steps_applied"] == 2
    assert song.is_playing is False and song.record_mode is False
    assert st["arrangement_clips"] == [] and "volume" in st["automation_state"]


def test_record_start_stops_running_transport_first(live) -> None:
    song = Song()
    calls = []
    song.stop_playing = lambda: calls.append("stop")
    song.start_playing = lambda: calls.append("start")
    song.is_playing = True
    spikes.RecordSpike().start(song, live, {"bars": 1})
    assert calls[:2] == ["stop", "start"]


def test_record_tick_waits_while_transport_not_playing(live) -> None:
    song = Song()
    r = spikes.RecordSpike()
    r.start(song, live, {"start_beat": 32.0, "bars": 1})
    song.is_playing = False
    song.current_song_time = 100.0  # posicion vieja: no debe contar como fin
    r.tick()
    assert r.status(song)["phase"] == "running" and r.steps_applied == 0


def test_record_ignores_position_before_start(live) -> None:
    song = Song()
    r = spikes.RecordSpike()
    r.start(song, live, {"start_beat": 32.0, "bars": 1})
    song.current_song_time = 10.0
    r.tick()
    assert r.steps_applied == 0 and r.status(song)["phase"] == "running"


def test_record_status_exposes_trace(live) -> None:
    song = Song()
    r = spikes.RecordSpike()
    r.start(song, live, {"start_beat": 32.0, "bars": 1})
    song.current_song_time = 34.0
    r.tick()
    trace = r.status(song)["trace"]
    assert trace[-1]["song_time"] == 34.0 and trace[-1]["progress"] == pytest.approx(0.5)


def test_record_picks_continuous_operator_param(live) -> None:
    song = Song()
    r = spikes.RecordSpike()
    out_holder = {}
    original = Track.insert_device

    def insert(self, name, idx):
        original(self, name, idx)
        self.devices[idx].parameters[1].is_quantized = True  # "Transpose" cuantizado

    Track.insert_device = insert
    try:
        out_holder = r.start(song, live, {"bars": 1})
    finally:
        Track.insert_device = original
    assert out_holder["operator_param"] == "Osc A Level"


def test_record_tick_error_goes_to_error_phase_without_raising(live) -> None:
    song = Song()
    r = spikes.RecordSpike()
    r.start(song, live, {"bars": 1})
    song.tracks[1].mixer_device = None
    r.tick()
    assert r.status(song)["phase"] == "error" and r.status(song)["errors"]
    assert song.record_mode is False


def test_record_timeout_when_transport_never_advances(live) -> None:
    clock = [0.0]
    r = spikes.RecordSpike(clock=lambda: clock[0])
    song = Song()
    r.start(song, live, {"bars": 1})
    clock[0] = 1000.0
    r.tick()
    assert r.status(song)["phase"] == "error"


def test_record_start_twice_rejected(live) -> None:
    r = spikes.RecordSpike()
    song = Song()
    r.start(song, live, {})
    out = r.start(song, live, {})
    assert out["started"] is False


def test_tick_idle_is_noop() -> None:
    spikes.RecordSpike().tick()


def test_cleanup_deletes_only_spike_tracks_and_stops(live) -> None:
    song = Song()
    r = spikes.RecordSpike()
    r.start(song, live, {})
    spikes.automation_session(song, live, {"bars": 1})
    out = spikes.cleanup(song, r)
    assert [t.name for t in song.tracks] == ["Keep me"]
    assert sorted(out["deleted"]) == ["SPIKE-AUTO-RECORD", "SPIKE-AUTO-SESSION"]
    assert song.record_mode is False and song.is_playing is False
    assert r.status(song)["phase"] == "idle"


def test_automation_arm_sets_and_reports_readback(live) -> None:
    song = Song()
    out = spikes.automation_arm(song, {"enable": True})
    assert out == {"ok": True, "error": None, "before": False, "after": True}
    assert song.session_automation_record is True
    assert spikes.automation_arm(song, {"enable": False})["after"] is False


def test_automation_arm_reports_failure_without_raising(live) -> None:
    class Bad:
        @property
        def session_automation_record(self):
            return False

        @session_automation_record.setter
        def session_automation_record(self, v):
            raise RuntimeError("read only")

    out = spikes.automation_arm(Bad(), {"enable": True})
    assert out["ok"] is False and "read only" in out["error"]


def test_record_start_arms_by_default_and_restores_on_done(live) -> None:
    song = Song()
    r = spikes.RecordSpike()
    r.start(song, live, {"start_beat": 32.0, "bars": 1})
    assert song.session_automation_record is True
    song.current_song_time = 36.5
    r.tick()
    assert r.status(song)["phase"] == "done"
    assert song.session_automation_record is False


def test_record_start_arm_false_leaves_flag_alone(live) -> None:
    song = Song()
    r = spikes.RecordSpike()
    r.start(song, live, {"arm": False})
    assert song.session_automation_record is False


def test_record_restores_previous_arm_value_on_error(live) -> None:
    song = Song()
    song.session_automation_record = True
    r = spikes.RecordSpike()
    r.start(song, live, {"bars": 1})
    song.tracks[1].mixer_device = None
    r.tick()
    assert r.status(song)["phase"] == "error"
    assert song.session_automation_record is True


def test_cleanup_restores_arm(live) -> None:
    song = Song()
    r = spikes.RecordSpike()
    r.start(song, live, {})
    spikes.cleanup(song, r)
    assert song.session_automation_record is False
