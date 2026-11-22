"""Comandos de produccion v1 (T-003) contra un LOM falso."""
import math
import types

import pytest

from remote_script.AbletonBridge import errors, production


# --- fakes ---------------------------------------------------------------


def _db(raw: float) -> str:
    return "-inf dB" if raw <= 0 else f"{20 * math.log10(raw / 0.85):.1f} dB"


class Param:
    def __init__(self, name, lo=0.0, hi=1.0, value=0.5, display=None, quantized=False):
        self.name, self.min, self.max, self.value = name, lo, hi, value
        self.default_value, self.is_quantized = value, quantized
        self._display = display or (lambda v: f"{v:.2f}")

    def str_for_value(self, v):
        return self._display(v)


class Mixer:
    def __init__(self):
        self.volume = Param("Volume", 0.0, 1.0, 0.85, _db)
        self.panning = Param("Pan", -1.0, 1.0, 0.0, lambda v: f"{v:.2f}")
        self.sends = [Param("A", 0.0, 1.0, 0.0, _db), Param("B", 0.0, 1.0, 0.0, _db)]


class Device:
    def __init__(self, name):
        self.name, self.class_name = name, name.replace(" ", "")
        self.parameters = [Param("Device On", 0, 1, 1), Param("Drive", 0, 1, 0.5),
                           Param("Mode", 0, 2, 0, quantized=True)]


class Sample:
    def __init__(self, path):
        self.file_path = path


class Simpler(Device):
    def __init__(self):
        super().__init__("Simpler")
        self.class_name = "OriginalSimpler"
        self.playback_mode, self.sample = 0, None

    def replace_sample(self, path):
        self.sample = Sample(path)


class AClip:
    """
    Clip de audio como en Live 12.4: el span en Arrangement (end_time) NO sigue a los
    markers; solo lo fija el loop del clip de Session al duplicarlo. Sin crop().
    """

    def __init__(self, path, start, natural, honor_trim=True, gain_display=True):
        self.file_path, self.start_time = path, start
        self.end_time = start + natural
        self.start_marker, self.end_marker = 0.0, natural
        self.loop_start, self.loop_end, self.looping = 0.0, natural, False
        self.warping, self.warp_mode, self.pitch_coarse, self.gain = True, 0, 0, 0.4
        self._honor, self._gain_display = honor_trim, gain_display

    @property
    def length(self):
        return self.end_marker - self.start_marker

    @property
    def gain_display_string(self):
        if not self._gain_display:
            raise AttributeError("no gain_display_string")
        return _db(self.gain)

    def __setattr__(self, k, v):
        if k in ("end_marker", "loop_end") and not self.__dict__.get("_honor", True):
            return
        object.__setattr__(self, k, v)


class Slot:
    def __init__(self, track):
        self._track, self.clip = track, None

    @property
    def has_clip(self):
        return self.clip is not None

    def create_audio_clip(self, path):
        s = self._track._song
        # No devuelve el clip a proposito: el codigo debe leer slot.clip
        self.clip = AClip(path, 0.0, s.natural, s.honor_trim, s.gain_display)

    def delete_clip(self):
        self.clip = None


class Scene:
    pass


class MClip:
    def __init__(self, start, length):
        self.start_time, self.length = start, length
        self.end_time, self.name = start + length, ""
        self.notes = []

    def add_new_notes(self, specs):
        self.notes.extend(specs)

    def get_all_notes_extended(self):
        return list(self.notes)


class Track:
    def __init__(self, song, midi, name="T"):
        self._song = song
        self.has_midi_input, self.name = midi, name
        self.mute, self.solo = False, False
        self.mixer_device, self.devices, self.arrangement_clips = Mixer(), [], []
        self.clip_slots = [Slot(self) for _ in song.scenes]

    def create_audio_clip(self, path, pos):
        clip = AClip(path, pos, self._song.natural, self._song.honor_trim, self._song.gain_display)
        self.arrangement_clips.append(clip)
        return clip

    def duplicate_clip_to_arrangement(self, clip, time):
        # Como el spike real: el span = largo de loop del clip de Session
        new = AClip(clip.file_path, time, clip.loop_end - clip.loop_start)
        for k in ("start_marker", "end_marker", "loop_start", "loop_end", "looping",
                  "warping", "warp_mode", "pitch_coarse", "gain"):
            object.__setattr__(new, k, getattr(clip, k))
        self.arrangement_clips.append(new)
        return None  # la referencia no es confiable: se re-busca por start_time

    def delete_clip(self, clip):
        self.arrangement_clips.remove(clip)

    def create_midi_clip(self, start, length):
        clip = MClip(start, length)
        self.arrangement_clips.append(clip)
        return clip

    def insert_device(self, name, index):
        if name == "Nope":
            raise RuntimeError("device not found")
        dev = Simpler() if name == "Simpler" else Device(name)
        self.devices.insert(index, dev)
        return dev


class Cue:
    def __init__(self, time):
        self.time, self.name = time, ""


class Song:
    def __init__(self):
        self.scenes = [Scene()]
        self.tracks = []
        self.return_tracks = []
        self.tempo, self.signature_numerator, self.signature_denominator = 120.0, 4, 4
        self.loop_start, self.loop_length, self.loop = 0.0, 16.0, False
        self._time, self._pending, self.cue_points = 0.0, None, []
        self.freeze_playhead = False
        self.natural, self.honor_trim, self.gain_display = 8.0, True, True

    def create_scene(self, i):
        self.scenes.append(Scene())
        for t in self.tracks:
            t.clip_slots.append(Slot(t))

    def delete_scene(self, i):
        del self.scenes[i]
        for t in self.tracks:
            del t.clip_slots[i]

    def create_audio_track(self, i):
        self._add(False, i)

    def create_midi_track(self, i):
        self._add(True, i)

    def _add(self, midi, i):
        self.tracks.insert(len(self.tracks) if i == -1 else i, Track(self, midi))

    def delete_track(self, i):
        del self.tracks[i]

    def create_return_track(self, *args):
        if args:
            raise TypeError("create_return_track takes no arguments")
        self.return_tracks.append(Track(self, False, "New Return"))

    @property
    def current_song_time(self):
        return self._time

    @current_song_time.setter
    def current_song_time(self, v):
        # Live aplica el cambio de playhead recien en un tick posterior
        self._pending = v

    def apply_pending(self):
        if self._pending is not None and not self.freeze_playhead:
            self._time, self._pending = self._pending, None

    def set_or_delete_cue(self):
        for c in list(self.cue_points):
            if abs(c.time - self._time) < 1e-6:
                self.cue_points.remove(c)
                return
        self.cue_points.append(Cue(self._time))


LIVE = types.SimpleNamespace(Clip=types.SimpleNamespace(
    MidiNoteSpecification=lambda **kw: types.SimpleNamespace(**kw)))


@pytest.fixture
def song():
    s = Song()
    s.create_audio_track(-1)
    s.create_midi_track(-1)
    return s


@pytest.fixture
def wav(tmp_path):
    p = tmp_path / "loop.wav"
    p.write_bytes(b"RIFF")
    return str(p)


def code_of(fn, *args):
    with pytest.raises(errors.CommandError) as e:
        fn(*args)
    return e.value.code


# --- errors --------------------------------------------------------------


def test_command_error_carries_code() -> None:
    e = errors.CommandError(errors.INVALID_PARAMS, "bad")
    assert (e.code, e.message, str(e)) == ("INVALID_PARAMS", "bad", "bad")


# --- song.set ------------------------------------------------------------


def test_song_set_applies_and_reads_back(song) -> None:
    out = production.song_set(song, {
        "tempo": 128, "signature_numerator": 3, "signature_denominator": 8,
        "loop_start": 32.0, "loop_length": 64.0, "loop_on": True})
    assert out == {"tempo": 128.0, "signature_numerator": 3, "signature_denominator": 8,
                   "loop_start": 32.0, "loop_length": 64.0, "loop_on": True}
    assert song.tempo == 128.0 and song.loop is True


def test_song_set_partial_only_changes_given(song) -> None:
    production.song_set(song, {"tempo": 140})
    assert song.signature_numerator == 4 and song.tempo == 140.0


@pytest.mark.parametrize("bad", [
    {"tempo": 5}, {"tempo": "fast"}, {"tempo": True}, {"signature_denominator": 3},
    {"signature_numerator": 0}, {"loop_length": 0}, {"loop_start": -1}, {"loop_on": "yes"},
])
def test_song_set_rejects_invalid(song, bad) -> None:
    assert code_of(production.song_set, song, bad) == errors.INVALID_PARAMS


# --- track.create --------------------------------------------------------


def test_track_create_audio_and_midi(song) -> None:
    a = production.track_create(song, {"kind": "audio", "name": "Kick"})
    m = production.track_create(song, {"kind": "midi", "name": "Bass", "index": 0})
    assert a == {"index": 2, "name": "Kick"}
    assert m == {"index": 0, "name": "Bass"}
    assert song.tracks[0].has_midi_input is True and song.tracks[0].name == "Bass"


@pytest.mark.parametrize("bad", [
    {"kind": "group", "name": "x"}, {"kind": "audio", "name": ""},
    {"kind": "audio", "name": "x", "index": 99}, {"kind": "audio", "name": "x", "index": -2},
])
def test_track_create_rejects_invalid(song, bad) -> None:
    assert code_of(production.track_create, song, bad) == errors.INVALID_PARAMS


# --- track.set_mixer -----------------------------------------------------


def test_set_mixer_volume_db_within_tolerance(song) -> None:
    out = production.track_set_mixer(song, {"track": 0, "volume_db": -6})
    shown = float(out["volume"]["display"].split()[0])
    assert abs(shown + 6) <= 0.1 + 1e-9
    assert out["volume"]["value"] == song.tracks[0].mixer_device.volume.value


def test_set_mixer_zero_db_is_raw_085(song) -> None:
    out = production.track_set_mixer(song, {"track": 0, "volume_db": 0})
    assert abs(out["volume"]["value"] - 0.85) < 0.01


def test_set_mixer_minus_inf(song) -> None:
    out = production.track_set_mixer(song, {"track": 0, "volume_db": "-inf"})
    assert out["volume"]["value"] == 0.0 and out["volume"]["display"] == "-inf dB"


def test_set_mixer_pan_mute_solo(song) -> None:
    out = production.track_set_mixer(song, {"track": 1, "pan": -0.5, "mute": True, "solo": True})
    assert out["panning"]["value"] == -0.5
    assert out["mute"] is True and out["solo"] is True
    assert "volume" not in out


def test_set_mixer_errors(song) -> None:
    assert code_of(production.track_set_mixer, song, {"track": 9}) == errors.TRACK_NOT_FOUND
    assert code_of(production.track_set_mixer, song, {"track": 0, "pan": 2}) == errors.INVALID_PARAMS
    assert code_of(production.track_set_mixer, song, {"track": 0, "volume_db": "loud"}) == errors.INVALID_PARAMS
    assert code_of(production.track_set_mixer, song, {"track": True}) == errors.TRACK_NOT_FOUND


def test_set_mixer_unreachable_db_reports_closest(song) -> None:
    out = production.track_set_mixer(song, {"track": 0, "volume_db": 30})
    assert out["volume"]["value"] == 1.0
    assert out["volume"]["within_tolerance"] is False


# --- clip.place_audio ----------------------------------------------------


def place(song, wav, **kw):
    params = {"track": 0, "path": wav, "start_beat": 0.0, "length_beats": 8.0}
    params.update(kw)
    return production.clip_place_audio(song, params)


def methods(out):
    return [c["method"] for c in out["clips"]]


def test_place_audio_exact_fit(song, wav) -> None:
    out = place(song, wav)
    assert out["ok"] is True and len(out["clips"]) == 1
    c = out["clips"][0]
    assert (c["start_time"], c["end_time"], c["length"]) == (0.0, 8.0, 8.0)
    assert c["method"] == "create_audio_clip" and c["warping"] is True


def test_place_audio_tiles_and_trims_last_via_session_slot(song, wav) -> None:
    out = place(song, wav, start_beat=16.0, length_beats=20.0)
    assert [(c["start_time"], c["end_time"]) for c in out["clips"]] == [
        (16.0, 24.0), (24.0, 32.0), (32.0, 36.0)]
    assert methods(out) == ["create_audio_clip", "create_audio_clip", "session_duplicate"]
    assert out["warnings"] == [] and out["ok"] is True
    track = song.tracks[0]
    assert len(track.arrangement_clips) == 3  # el tile natural descartado no queda
    assert not any(s.has_clip for s in track.clip_slots)  # scratch limpio
    assert len(song.scenes) == 1


def test_place_audio_trims_long_file(song, wav) -> None:
    out = place(song, wav, length_beats=4.0)
    c = out["clips"][0]
    assert (c["start_time"], c["end_time"], c["span"], c["length"]) == (0.0, 4.0, 4.0, 4.0)
    assert c["method"] == "session_duplicate"
    assert out["ok"] is True and out["warnings"] == []


def test_place_audio_long_natural_in_the_middle(song, wav) -> None:
    song.natural = 32.0
    out = place(song, wav, start_beat=480.0, length_beats=28.0)
    c = out["clips"][0]
    assert (c["start_time"], c["end_time"], c["span"]) == (480.0, 508.0, 28.0)
    assert [x.end_time for x in song.tracks[0].arrangement_clips] == [508.0]


def test_place_audio_never_calls_crop(song, wav) -> None:
    out = place(song, wav, length_beats=4.0)
    assert not any("crop" in k for k in out["steps"])


def test_place_audio_creates_and_removes_scene_when_no_empty_slot(song, wav) -> None:
    song.tracks[0].clip_slots[0].clip = AClip(wav, 0.0, 4.0)
    out = place(song, wav, length_beats=4.0)
    assert out["ok"] is True and out["clips"][0]["span"] == 4.0
    assert len(song.scenes) == 1 and len(song.tracks[0].clip_slots) == 1
    assert song.tracks[0].clip_slots[0].has_clip  # el clip previo del usuario sigue ahi


def test_place_audio_trim_ignored_reports_actual_span(song, wav) -> None:
    song.honor_trim = False
    out = place(song, wav, length_beats=4.0)
    assert out["ok"] is False
    assert out["clips"][0]["span"] == 8.0
    assert any("span" in w and "8" in w for w in out["warnings"])


def test_place_audio_applies_warp_and_pitch_to_every_copy(song, wav) -> None:
    out = place(song, wav, length_beats=12.0, warp_mode=6, pitch_coarse=-2)
    assert methods(out) == ["create_audio_clip", "session_duplicate"]
    assert [(c["warp_mode"], c["pitch_coarse"]) for c in out["clips"]] == [(6, -2), (6, -2)]


def test_place_audio_gain_db(song, wav) -> None:
    out = place(song, wav, length_beats=12.0, gain_db=-6)
    assert abs(float(out["gain"]["display"].split()[0]) + 6) <= 0.1 + 1e-9
    clips = song.tracks[0].arrangement_clips
    assert clips[0].gain == clips[1].gain


def test_place_audio_gain_unavailable_is_reported_not_fatal(song, wav) -> None:
    song.gain_display = False
    out = place(song, wav, gain_db=-6)
    assert out["ok"] is True and len(out["clips"]) == 1
    assert out["gain"]["applied"] is False
    assert any("gain" in w for w in out["warnings"])


def test_place_audio_loop_section(song, wav) -> None:
    out = place(song, wav, length_beats=4.0, loop_start=1.0, loop_end=2.0)
    assert [c["length"] for c in out["clips"]] == [1.0] * 4
    assert [c["span"] for c in out["clips"]] == [1.0] * 4
    assert methods(out) == ["session_duplicate"] * 4
    assert song.tracks[0].arrangement_clips[0].looping is True
    assert out["ok"] is True


def test_place_audio_one_shot_is_placed_once_unwarped(song, wav) -> None:
    out = place(song, wav, length_beats=40.0, one_shot=True, warp_mode=4)
    assert len(out["clips"]) == 1
    c = out["clips"][0]
    assert c["warping"] is False and c["method"] == "create_audio_clip"
    assert c["span"] == 8.0 and out["covered_beats"] == 8.0
    assert out["ok"] is True and out["warnings"] == []


def test_place_audio_one_shot_without_length(song, wav) -> None:
    out = production.clip_place_audio(song, {"track": 0, "path": wav, "start_beat": 4.0, "one_shot": True})
    assert out["ok"] is True and out["clips"][0]["start_time"] == 4.0


def test_place_audio_one_shot_longer_than_requested_warns(song, wav) -> None:
    out = place(song, wav, length_beats=4.0, one_shot=True)
    assert out["clips"][0]["span"] == 8.0
    assert any("one_shot" in w and "8" in w for w in out["warnings"])


def test_place_audio_one_shot_reports_sample_beats(song, wav) -> None:
    AClip.sample_length = 44100 * 4
    AClip.sample_rate = 44100.0
    try:
        out = place(song, wav, one_shot=True)
    finally:
        del AClip.sample_length, AClip.sample_rate
    assert out["sample_beats"] == 8.0  # 4 s a 120 bpm


def test_place_audio_length_required_unless_one_shot(song, wav) -> None:
    assert code_of(production.clip_place_audio, song,
                   {"track": 0, "path": wav, "start_beat": 0}) == errors.INVALID_PARAMS
    assert code_of(production.clip_place_audio, song,
                   {"track": 0, "path": wav, "start_beat": 0, "one_shot": "yes",
                    "length_beats": 4}) == errors.INVALID_PARAMS


def test_place_audio_validation(song, wav, tmp_path) -> None:
    assert code_of(production.clip_place_audio, song,
                   {"track": 0, "path": "rel.wav", "start_beat": 0, "length_beats": 4}) == errors.INVALID_PARAMS
    assert code_of(production.clip_place_audio, song,
                   {"track": 0, "path": str(tmp_path / "no.wav"), "start_beat": 0, "length_beats": 4}) == errors.INVALID_PARAMS
    assert code_of(production.clip_place_audio, song,
                   {"track": 0, "path": wav, "start_beat": -1, "length_beats": 4}) == errors.INVALID_PARAMS
    assert code_of(production.clip_place_audio, song,
                   {"track": 0, "path": wav, "start_beat": 0, "length_beats": 0}) == errors.INVALID_PARAMS
    assert code_of(production.clip_place_audio, song,
                   {"track": 1, "path": wav, "start_beat": 0, "length_beats": 4}) == errors.INVALID_PARAMS
    assert code_of(production.clip_place_audio, song,
                   {"track": 5, "path": wav, "start_beat": 0, "length_beats": 4}) == errors.TRACK_NOT_FOUND
    assert code_of(production.clip_place_audio, song,
                   {"track": 0, "path": wav, "start_beat": 0, "length_beats": 4, "warp_mode": 5}) == errors.INVALID_PARAMS


def test_place_audio_tile_cap(song, wav) -> None:
    song.natural = 0.0
    out = place(song, wav, length_beats=4.0)
    assert out["ok"] is False and out["warnings"]


# --- clip.create_midi ----------------------------------------------------


NOTES = [{"pitch": 36, "start": 0.0, "duration": 0.5, "velocity": 100},
         {"pitch": 38, "start": 1.0, "duration": 0.25, "velocity": 90}]


def test_create_midi_clip_with_notes(song) -> None:
    out = production.clip_create_midi(song, LIVE, {
        "track": 1, "start_beat": 32.0, "length_beats": 4.0, "notes": NOTES})
    assert (out["start_time"], out["end_time"], out["length"], out["note_count"]) == (32.0, 36.0, 4.0, 2)
    spec = song.tracks[1].arrangement_clips[0].notes[1]
    assert (spec.pitch, spec.start_time, spec.duration, spec.velocity) == (38, 1.0, 0.25, 90)


def test_create_midi_errors(song) -> None:
    base = {"start_beat": 0, "length_beats": 4, "notes": []}
    assert code_of(production.clip_create_midi, song, LIVE, dict(base, track=0)) == errors.NOT_MIDI_TRACK
    assert code_of(production.clip_create_midi, song, LIVE, dict(base, track=7)) == errors.TRACK_NOT_FOUND
    bad_note = [{"pitch": 200, "start": 0, "duration": 1, "velocity": 100}]
    assert code_of(production.clip_create_midi, song, LIVE, dict(base, track=1, notes=bad_note)) == errors.INVALID_PARAMS
    assert code_of(production.clip_create_midi, song, LIVE, dict(base, track=1, length_beats=0)) == errors.INVALID_PARAMS
    assert code_of(production.clip_create_midi, song, LIVE, dict(base, track=1, notes="x")) == errors.INVALID_PARAMS


def test_create_midi_empty_notes_ok(song) -> None:
    out = production.clip_create_midi(song, LIVE, {
        "track": 1, "start_beat": 0, "length_beats": 4, "notes": []})
    assert out["note_count"] == 0


# --- device.insert / device.set_param / simpler.load ----------------------


def test_device_insert_append_and_index(song) -> None:
    a = production.device_insert(song, {"track": 0, "name": "Saturator"})
    b = production.device_insert(song, {"track": 0, "name": "Utility", "index": 0})
    assert a == {"index": 0, "class_name": "Saturator", "name": "Saturator"}
    assert b["index"] == 0 and song.tracks[0].devices[0].name == "Utility"


def test_device_insert_failure_is_lom_error_not_crash(song) -> None:
    with pytest.raises(RuntimeError):
        production.device_insert(song, {"track": 0, "name": "Nope"})


def test_device_set_param_by_name(song) -> None:
    production.device_insert(song, {"track": 0, "name": "Saturator"})
    out = production.device_set_param(song, {"track": 0, "device": 0, "name": "Drive", "value": 0.75})
    assert out["name"] == "Drive" and out["value"] == 0.75 and out["display"] == "0.75"


def test_device_set_param_device_by_name(song) -> None:
    production.device_insert(song, {"track": 0, "name": "Saturator"})
    out = production.device_set_param(song, {"track": 0, "device": "Saturator", "name": "Drive", "value": 0.1})
    assert out["value"] == 0.1


def test_device_set_param_errors(song) -> None:
    production.device_insert(song, {"track": 0, "name": "Saturator"})
    p = {"track": 0, "device": 0, "name": "Drive", "value": 0.5}
    assert code_of(production.device_set_param, song, dict(p, name="drive")) == errors.INVALID_PARAMS
    assert code_of(production.device_set_param, song, dict(p, value=5)) == errors.INVALID_PARAMS
    assert code_of(production.device_set_param, song, dict(p, value="x")) == errors.INVALID_PARAMS
    assert code_of(production.device_set_param, song, dict(p, device=4)) == errors.INVALID_PARAMS
    assert code_of(production.device_set_param, song, dict(p, track=9)) == errors.TRACK_NOT_FOUND


def test_simpler_load(song, wav) -> None:
    production.device_insert(song, {"track": 1, "name": "Simpler"})
    out = production.simpler_load(song, {"track": 1, "device": 0, "path": wav, "playback_mode": 2})
    assert out["ok"] is True
    assert out["file_path"] == wav and out["playback_mode"] == 2


def test_simpler_load_without_mode_keeps_it(song, wav) -> None:
    production.device_insert(song, {"track": 1, "name": "Simpler"})
    out = production.simpler_load(song, {"track": 1, "device": 0, "path": wav})
    assert out["playback_mode"] == 0


def test_simpler_load_rejects_non_simpler_and_bad_path(song, wav) -> None:
    production.device_insert(song, {"track": 0, "name": "Saturator"})
    assert code_of(production.simpler_load, song, {"track": 0, "device": 0, "path": wav}) == errors.INVALID_PARAMS
    production.device_insert(song, {"track": 1, "name": "Simpler"})
    assert code_of(production.simpler_load, song, {"track": 1, "device": 0, "path": "x.wav"}) == errors.INVALID_PARAMS
    assert code_of(production.simpler_load, song, {"track": 1, "device": 0, "path": wav, "playback_mode": 7}) == errors.INVALID_PARAMS


# --- locators ------------------------------------------------------------


def run(q, song, max_ticks=50):
    """Simula los ticks del pump: cada tick avanza la maquina y luego Live aplica el playhead."""
    for _ in range(max_ticks):
        q.tick(song)
        song.apply_pending()
        if q.status(song)["pending"] == 0 and not q._restore:
            break
    return q.status(song)


@pytest.fixture
def q():
    return production.LocatorQueue()


def test_locator_set_is_queued_not_applied_in_same_call(song, q) -> None:
    out = q.set_many(song, {"items": [{"time": 64.0, "name": "DROP"}]})
    assert out["queued"] is True and "id" in out and song.cue_points == []
    assert q.status(song)["pending"] == 1


def test_locator_set_creates_cue_at_requested_time_and_restores_playhead(song, q) -> None:
    song.current_song_time = 5.0
    song.apply_pending()
    q.set_many(song, {"items": [{"time": 0.0, "name": "IN"}, {"time": 96.0, "name": "OUT"}]})
    st = run(q, song)
    assert st["errors"] == [] and st["pending"] == 0
    assert [(c["name"], c["time"]) for c in st["cue_points"]] == [("IN", 0.0), ("OUT", 96.0)]
    assert [(d["name"], d["time"]) for d in st["done"]] == [("IN", 0.0), ("OUT", 96.0)]
    song.apply_pending()
    assert song.current_song_time == 5.0


def test_locator_set_renames_existing_without_deleting(song, q) -> None:
    q.set_many(song, {"items": [{"time": 64.0, "name": "A"}]})
    run(q, song)
    q.set_many(song, {"items": [{"time": 64.0, "name": "B"}]})
    st = run(q, song)
    assert st["cue_points"] == [{"name": "B", "time": 64.0}]
    assert st["done"] == [{"name": "B", "time": 64.0}]


def test_locator_validation(song, q) -> None:
    bad = [{"items": []}, {"items": "x"}, {"items": [{"time": -1, "name": "x"}]},
           {"items": [{"time": 1, "name": ""}]}, {"items": [{"time": "1", "name": "x"}]},
           {"items": [{"time": 1, "name": "ok"}, {"time": 2}]}, {}]
    for params in bad:
        assert code_of(q.set_many, song, params) == errors.INVALID_PARAMS
    assert q.status(song)["pending"] == 0


def test_locator_playhead_never_arrives_reports_timeout(song) -> None:
    now = [0.0]
    q = production.LocatorQueue(clock=lambda: now[0])
    song.freeze_playhead = True
    q.set_many(song, {"items": [{"time": 8.0, "name": "X"}]})
    q.tick(song)
    now[0] = 5.0
    song.apply_pending()
    q.tick(song)
    st = q.status(song)
    assert st["pending"] == 0 and len(st["errors"]) == 1
    assert st["errors"][0]["name"] == "X" and "timeout" in st["errors"][0]["error"]
    assert song.cue_points == []


def test_locator_clear_all_goes_through_queue(song, q) -> None:
    for t in (0.0, 32.0, 64.0):
        song._time = t
        song.set_or_delete_cue()
    song._time = 0.0
    out = q.clear_all(song, {})
    assert out["queued"] is True and out["count"] == 3
    assert len(song.cue_points) == 3
    st = run(q, song)
    assert st["cue_points"] == [] and st["errors"] == []
    assert len(st["done"]) == 3


# --- track.delete --------------------------------------------------------


def test_track_delete_requires_matching_name(song) -> None:
    song.tracks[0].name = "Kick"
    assert code_of(production.track_delete, song, {"track": 0, "confirm_name": "kick"}) == errors.INVALID_PARAMS
    assert len(song.tracks) == 2
    out = production.track_delete(song, {"track": 0, "confirm_name": "Kick"})
    assert out == {"deleted": "Kick", "index": 0, "track_count": 1}
    assert code_of(production.track_delete, song, {"track": 5, "confirm_name": "x"}) == errors.TRACK_NOT_FOUND


# --- db search -----------------------------------------------------------


def test_parse_db() -> None:
    assert production.parse_db("-6.2 dB") == -6.2
    assert production.parse_db("-inf dB") == -math.inf
    assert production.parse_db("−6.0 dB") == -6.0
    assert production.parse_db("0.00") == 0.0
    assert production.parse_db("garbage") is None


# --- sends y returns (T-009) -------------------------------------------------


@pytest.fixture
def rsong(song):
    song.create_return_track()
    song.create_return_track()
    song.return_tracks[0].name, song.return_tracks[1].name = "A-Reverb", "B-Delay"
    song.return_tracks[0].devices.append(Device("Reverb"))
    return song


def test_set_send_bisects_db(rsong) -> None:
    out = production.track_set_send(rsong, {"track": 0, "send": 1, "db": -12})
    assert abs(float(out["display"].split()[0]) + 12) <= 0.1 + 1e-9
    assert out["within_tolerance"] is True
    assert out["value"] == rsong.tracks[0].mixer_device.sends[1].value
    assert rsong.tracks[0].mixer_device.sends[0].value == 0.0


def test_set_send_minus_inf_and_unreachable(rsong) -> None:
    rsong.tracks[0].mixer_device.sends[0].value = 0.5
    out = production.track_set_send(rsong, {"track": 0, "send": 0, "db": "-inf"})
    assert out["value"] == 0.0 and out["display"] == "-inf dB"
    out = production.track_set_send(rsong, {"track": 0, "send": 0, "db": 30})
    assert out["within_tolerance"] is False


@pytest.mark.parametrize("bad", [
    {"track": 0, "send": 2, "db": -6}, {"track": 0, "send": -1, "db": -6},
    {"track": 0, "send": True, "db": -6}, {"track": 0, "send": 0},
    {"track": 0, "send": 0, "db": "loud"}, {"track": 0, "db": -6},
])
def test_set_send_invalid(rsong, bad) -> None:
    assert code_of(production.track_set_send, rsong, bad) == errors.INVALID_PARAMS


def test_set_send_track_not_found(rsong) -> None:
    assert code_of(production.track_set_send, rsong, {"track": 9, "send": 0, "db": 0}) == errors.TRACK_NOT_FOUND


def test_return_list(rsong) -> None:
    res = production.return_list(rsong, {})
    out = res["returns"]
    assert res["count"] == 2 and [r["index"] for r in out] == [0, 1]
    assert out[0]["name"] == "A-Reverb" and out[0]["devices"] == ["Reverb"]
    assert out[1]["devices"] == []
    assert set(out[0]["volume"]) == {"value", "display"}


def test_return_list_empty_is_still_a_dict(song) -> None:
    assert production.return_list(song, {}) == {"returns": [], "count": 0}


def test_return_set_mixer(rsong) -> None:
    out = production.return_set_mixer(rsong, {"return": 1, "volume_db": -6, "pan": 0.25, "mute": True})
    assert out["return"] == 1
    assert abs(float(out["volume"]["display"].split()[0]) + 6) <= 0.1 + 1e-9
    assert out["panning"]["value"] == 0.25 and out["mute"] is True
    assert rsong.return_tracks[1].mute is True and "solo" not in out


def test_return_set_mixer_errors(rsong) -> None:
    assert code_of(production.return_set_mixer, rsong, {"return": 5}) == errors.TRACK_NOT_FOUND
    assert code_of(production.return_set_mixer, rsong, {"return": 0, "pan": 3}) == errors.INVALID_PARAMS
    assert code_of(production.return_set_mixer, rsong, {"return": 0, "solo": True}) == errors.INVALID_PARAMS


def test_return_device_insert_and_set_param(rsong) -> None:
    out = production.return_device_insert(rsong, {"return": 1, "name": "Delay"})
    assert out["index"] == 0 and out["name"] == "Delay"
    assert [d.name for d in rsong.return_tracks[1].devices] == ["Delay"]
    p = production.return_device_set_param(rsong, {"return": 1, "device": "Delay", "name": "Drive", "value": 0.2})
    assert p["value"] == 0.2
    assert code_of(production.return_device_insert, rsong, {"return": 7, "name": "Delay"}) == errors.TRACK_NOT_FOUND
    assert code_of(production.return_device_set_param, rsong,
                   {"return": 0, "device": "Nope", "name": "Drive", "value": 0.2}) == errors.INVALID_PARAMS


def test_return_create_renames_and_returns_index(rsong) -> None:
    out = production.return_create(rsong, {"name": "C-Chorus"})
    assert out == {"index": 2, "name": "C-Chorus"}
    out = production.return_create(rsong, {})
    assert out["index"] == 3 and out["name"] == "New Return"
    assert code_of(production.return_create, rsong, {"name": ""}) == errors.INVALID_PARAMS


# --- clip.delete_range ---------------------------------------------------


def _arr(song, spans):
    for st, en in spans:
        song.tracks[0].arrangement_clips.append(AClip("x", st, en - st))


def test_delete_range_deletes_only_clips_fully_inside(song) -> None:
    _arr(song, [(0, 8), (8, 16), (16, 24), (4, 12), (20, 40)])
    out = production.clip_delete_range(song, {"track": 0, "start_beat": 8.0, "end_beat": 24.0})
    assert sorted((d["start_time"], d["end_time"]) for d in out["deleted"]) == [(8.0, 16.0), (16.0, 24.0)]
    assert out["count"] == 2 and out["track"] == 0
    assert sorted(c.start_time for c in song.tracks[0].arrangement_clips) == [0, 4, 20]


def test_delete_range_validation(song) -> None:
    assert code_of(production.clip_delete_range, song,
                   {"track": 0, "start_beat": 8, "end_beat": 8}) == errors.INVALID_PARAMS
    assert code_of(production.clip_delete_range, song,
                   {"track": 0, "start_beat": -1, "end_beat": 8}) == errors.INVALID_PARAMS
    assert code_of(production.clip_delete_range, song,
                   {"track": 9, "start_beat": 0, "end_beat": 8}) == errors.TRACK_NOT_FOUND
