"""Spikes ronda 2 (T-002d): audio clips, devices y Simpler contra un LOM falso."""
import types
from typing import Any, List

import pytest

from remote_script.AbletonBridge import spikes, spikes_media


class P:
    def __init__(self, name, lo=0.0, hi=1.0, default=0.5, quantized=False, items=None):
        self.name, self.original_name = name, name
        self.min, self.max, self.default_value = lo, hi, default
        self.value = default
        self.is_quantized = quantized
        if items:
            self.value_items = items

    def str_for_value(self, v):
        return f"{v:.2f}"


class AClip:
    def __init__(self, path, start):
        self.file_path, self.start_time = path, start
        self.is_audio_clip = True
        self.length, self.end_time = 8.0, start + 8.0
        self.warping, self.warp_mode = True, 0
        self.warp_markers = [types.SimpleNamespace(beat_time=0.0, sample_time=0.0)]
        self.start_marker, self.end_marker = 0.0, 8.0
        self.loop_start, self.loop_end, self.looping = 0.0, 8.0, False
        self.gain, self.pitch_coarse = 0.4, 0
        self.order: List[str] = []

    def __setattr__(self, k, v):
        if k in ("start_marker", "end_marker", "loop_start", "loop_end"):
            self.__dict__.setdefault("order", []).append(k)
            if k.endswith("start") or k == "start_marker":
                if v >= self.__dict__.get("end_marker" if k == "start_marker" else "loop_end", 1e9):
                    raise RuntimeError("start past end")
        object.__setattr__(self, k, v)


class MClip:
    def __init__(self, length):
        self.length, self.notes = length, None

    def add_new_notes(self, specs):
        self.notes = specs


class Slot:
    has_clip = False
    clip = None

    def create_clip(self, length):
        self.clip, self.has_clip = MClip(length), True


class Sample:
    def __init__(self, path):
        self.file_path, self.length, self.sample_rate = path, 44100 * 4, 44100
        self.slicing_style, self.slicing_sensitivity, self.slicing_beat_division = 0, 1.0, 4
        self.slices = [0, 100, 200]
        self.fail_clear = False

    def clear_slices(self):
        if self.fail_clear:
            raise RuntimeError("no clear")
        self.slices = []

    def insert_slice(self, frame):
        self.slices.append(frame)


class Simpler:
    def __init__(self):
        self.name, self.class_name = "Simpler", "OriginalSimpler"
        self.playback_mode = 0
        self.sample = None
        self.parameters = [P("Device On"), P("Transpose", -48, 48, 0)]

    def replace_sample(self, path):
        self.sample = Sample(path)


class Dev:
    def __init__(self, name):
        self.name, self.class_name = name, name.replace(" ", "")
        self.parameters = [
            P("Device On", quantized=True, items=["Off", "On"]),
            P("Drive", 0.0, 36.0, 0.0),
            P("Gain", -35.0, 35.0, 0.0),
        ]


class Track:
    def __init__(self, kind, fail=()):
        self.kind, self.name, self.fail = kind, "", fail
        self.devices: List[Any] = []
        self.arrangement_clips: List[AClip] = []
        self.clip_slots = [Slot()]

    def insert_device(self, name, idx):
        if name in self.fail:
            raise RuntimeError(f"cannot insert {name}")
        dev = Simpler() if name == "Simpler" else Dev(name)
        self.devices.insert(idx, dev)
        return dev

    def create_audio_clip(self, path, pos):
        clip = AClip(path, pos)
        self.arrangement_clips.append(clip)
        return clip


class Song:
    def __init__(self, **kw):
        self.tracks = [types.SimpleNamespace(name="Keep me")]
        self.kw = kw

    def create_audio_track(self, idx):
        self.tracks.append(Track("audio", **self.kw))

    def create_midi_track(self, idx):
        self.tracks.append(Track("midi", **self.kw))

    def delete_track(self, i):
        del self.tracks[i]


@pytest.fixture
def live(fake_live):
    class Spec:
        def __init__(self, **kw):
            self.__dict__.update(kw)

    fake_live.Clip.MidiNoteSpecification = Spec
    return fake_live


@pytest.fixture
def wav(tmp_path):
    p = tmp_path / "loop.wav"
    p.write_bytes(b"x")
    return str(p)


# --- validacion de path ---


@pytest.mark.parametrize("bad", ["", "relative.wav", "C:/nope/missing.wav", None, 5])
def test_invalid_paths_rejected_without_touching_live(live, bad) -> None:
    song = Song()
    out = spikes_media.audio_clip(song, live, {"path": bad})
    assert out == {"ok": False, "error": "invalid path"}
    assert len(song.tracks) == 1


def test_bad_extension_rejected(live, tmp_path) -> None:
    p = tmp_path / "a.txt"
    p.write_text("x")
    song = Song()
    assert spikes_media.audio_clip(song, live, {"path": str(p)})["error"] == "invalid path"
    assert len(song.tracks) == 1


def test_simpler_rejects_if_either_path_invalid(live, wav) -> None:
    song = Song()
    out = spikes_media.simpler_slice(song, live, {"loop_path": wav, "oneshot_path": "nope.wav"})
    assert out == {"ok": False, "error": "invalid path"} and len(song.tracks) == 1


# --- audio_clip ---


def test_audio_clip_creates_three_clips_and_reads_back(live, wav) -> None:
    song = Song()
    out = spikes_media.audio_clip(song, live, {"path": wav, "position_beats": 4.0})
    t = song.tracks[1]
    assert t.name == "SPIKE-AUDIO" and out["ok"] is True
    assert [c.start_time for c in t.arrangement_clips] == [4.0, 20.0, 24.0]
    base = out["clips"]["base"]
    assert base["is_audio_clip"] is True and base["file_path"] == wav
    assert base["warp_markers"] == [{"beat_time": 0.0, "sample_time": 0.0}]
    assert base["pitch_coarse"] == 0 and base["gain"] == 0.4


def test_audio_clip_chop_sets_one_beat_slice(live, wav) -> None:
    song = Song()
    out = spikes_media.audio_clip(song, live, {"path": wav})
    chop = song.tracks[1].arrangement_clips[1]
    assert (chop.start_marker, chop.end_marker) == (1.0, 2.0)
    assert (chop.loop_start, chop.loop_end) == (1.0, 2.0)
    assert out["clips"]["chop"]["loop_start"] == 1.0


def test_audio_clip_sets_start_before_end_when_shrinking(live, wav) -> None:
    song = Song()
    spikes_media.audio_clip(song, live, {"path": wav})
    chop = song.tracks[1].arrangement_clips[1]
    order = [k for k in chop.order if k in ("start_marker", "end_marker")]
    assert order[-2:] == ["start_marker", "end_marker"]


def test_audio_clip_complex_pro_and_pitch(live, wav) -> None:
    song = Song()
    out = spikes_media.audio_clip(song, live, {"path": wav})
    cp = song.tracks[1].arrangement_clips[2]
    assert cp.warp_mode == 6 and cp.pitch_coarse == -2
    assert out["complex_pro_mode_value"] == 6
    assert out["clips"]["complex"]["pitch_coarse"] == -2


def test_audio_clip_step_failure_is_reported_not_raised(live, wav) -> None:
    class Boom(Song):
        def create_audio_track(self, idx):
            raise RuntimeError("no track")

    out = spikes_media.audio_clip(Boom(), live, {"path": wav})
    assert out["ok"] is False and "no track" in out["steps"]["create_track"]["error"]


# --- devices ---


def test_devices_inserts_chain_in_order_with_param_dump(live) -> None:
    song = Song()
    out = spikes_media.devices(song, live, {})
    t = song.tracks[1]
    assert t.name == "SPIKE-DEVICES"
    assert [d.name for d in t.devices[:5]] == [
        "EQ Eight", "Saturator", "Compressor", "Drum Buss", "Utility"]
    sat = next(d for d in out["devices"] if d["name"] == "Saturator")
    assert sat["class_name"] == "Saturator"
    on, drive = sat["parameters"][0], sat["parameters"][1]
    assert on["is_quantized"] is True and on["value_items"] == ["Off", "On"]
    assert "default_value" not in on
    assert drive["default_value"] == 0.0 and drive["str_for_value"] == "0.00"
    assert drive["original_name"] == "Drive"


def test_devices_sets_drive_half_and_gain_quarter(live) -> None:
    song = Song()
    out = spikes_media.devices(song, live, {})
    assert out["set_params"]["Saturator.Drive"]["value"] == pytest.approx(18.0)
    assert out["set_params"]["Utility.Gain"]["value"] == pytest.approx(-35 + 70 * 0.25)
    assert out["set_params"]["Utility.Gain"]["str_for_value"] == "-17.50"


def test_devices_drum_rack_result_and_failure_isolated(live) -> None:
    out = spikes_media.devices(Song(fail=("Drum Rack", "Compressor")), live, {})
    assert out["drum_rack"]["ok"] is False and "Drum Rack" in out["drum_rack"]["error"]
    assert out["steps"]["insert_Compressor"]["ok"] is False
    assert out["steps"]["insert_Utility"]["ok"] is True
    assert "Utility.Gain" in out["set_params"]


def test_devices_drum_rack_ok(live) -> None:
    out = spikes_media.devices(Song(), live, {})
    assert out["drum_rack"]["ok"] is True


# --- simpler ---


def test_simpler_slice_builds_slicing_track(live, wav) -> None:
    song = Song()
    out = spikes_media.simpler_slice(song, live, {"loop_path": wav, "oneshot_path": wav})
    t = song.tracks[1]
    assert t.name == "SPIKE-SIMPLER-SLICE" and out["ok"] is True
    dev = t.devices[0]
    assert dev.playback_mode == 2 and dev.sample.file_path == wav
    s = out["slice"]
    assert s["sample"]["length"] == 44100 * 4 and s["sample"]["slices_count"] == 3
    assert s["sample"]["first_slices"] == [0, 100, 200]
    assert dev.sample.slices == [0, 44100, 88200, 132300]
    assert s["slices_after"] == [0, 44100, 88200, 132300]
    notes = t.clip_slots[0].clip.notes
    assert [n.pitch for n in notes] == [36, 37, 38, 39]
    assert [n.start_time for n in notes] == [0.0, 1.0, 2.0, 3.0]
    assert t.clip_slots[0].clip.length == 4.0


def test_simpler_oneshot_track(live, wav) -> None:
    song = Song()
    out = spikes_media.simpler_slice(song, live, {"loop_path": wav, "oneshot_path": wav})
    t = song.tracks[2]
    assert t.name == "SPIKE-SIMPLER-ONESHOT"
    assert t.devices[0].playback_mode == 1
    assert [n.pitch for n in t.clip_slots[0].clip.notes] == [60, 60, 60, 60]
    assert out["oneshot"]["playback_mode_readback"] == 1


def test_simpler_clear_slices_failure_is_reported(live, wav, monkeypatch) -> None:
    monkeypatch.setattr(Sample, "clear_slices", lambda self: (_ for _ in ()).throw(RuntimeError("no clear")))
    out = spikes_media.simpler_slice(Song(), live, {"loop_path": wav, "oneshot_path": wav})
    assert out["steps"]["slice_clear_slices"]["ok"] is False
    assert out["steps"]["oneshot_create_clip"]["ok"] is True


def test_cleanup_removes_round2_tracks(live, wav) -> None:
    song = Song()
    song.session_automation_record = False
    song.stop_playing = lambda: None
    spikes_media.audio_clip(song, live, {"path": wav})
    spikes_media.devices(song, live, {})
    spikes_media.simpler_slice(song, live, {"loop_path": wav, "oneshot_path": wav})
    out = spikes.cleanup(song, spikes.RecordSpike())
    assert [t.name for t in song.tracks] == ["Keep me"]
    assert len(out["deleted"]) == 4
