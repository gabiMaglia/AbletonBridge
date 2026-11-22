"""Comandos de produccion v1 (T-003) contra un LOM falso."""
import math
import types

import pytest

from remote_script.AbletonBridge import errors, production


# --- fakes ---------------------------------------------------------------


def _db(raw: float) -> str:
    return "-inf dB" if raw <= 0 else f"{20 * math.log10(raw / 0.85):.1f} dB"


def _hz(raw: float) -> str:
    f = 20.0 * 1000.0 ** raw  # 20 Hz .. 20 kHz, exponencial como Auto Filter
    return f"{f / 1000:.2f} kHz" if f >= 1000 else f"{f:.1f} Hz"


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
                           Param("Mode", 0, 2, 0, quantized=True),
                           Param("Frequency", 0.0, 1.0, 0.5, _hz)]


class Utility(Device):
    """Utility real (class StereoGain): el nivel es el parametro "Output" (-1..1, display en dB)."""

    def __init__(self):
        super().__init__("Utility")
        self.class_name = "StereoGain"
        self.parameters = [Param("Device On", 0, 1, 1), Param("Output", -1.0, 1.0, 0.0, lambda v: f"{v * 35:.2f} dB")]


class RT:
    def __init__(self, display_name):
        self.display_name = display_name


class Comp(Device):
    """Compressor con ruteo de entrada (sidechain) como en Live 11+."""

    def __init__(self, song):
        super().__init__("Compressor")
        self.class_name = "Compressor2"
        names = ["Ext. In", "No Input"] + [t.name for t in song.tracks]
        self.available_input_routing_types = [RT(n) for n in names]
        self.input_routing_type = self.available_input_routing_types[1]
        self.available_input_routing_channels = [RT("Post FX"), RT("Pre FX")]
        self.input_routing_channel = self.available_input_routing_channels[0]
        self.parameters += [Param("S/C On", 0, 1, 0, quantized=True), Param("S/C Gain", 0, 1, 0.4),
                            Param("S/C Mix", 0, 1, 1.0)]

    def __setattr__(self, k, v):
        if k == "input_routing_type" and v not in self.__dict__.get("available_input_routing_types", [v]):
            raise ValueError("not an available routing type")
        object.__setattr__(self, k, v)


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


class Env:
    """Envelope de clip estricto: Live rechaza pasos fuera del clip o del rango del parametro."""

    def __init__(self, clip, param):
        self._clip, self._param, self.steps = clip, param, []

    def insert_step(self, time, duration, value):
        if time < 0 or duration <= 0 or time + duration > self._clip.length + 1e-6:
            raise ValueError(f"step {time}+{duration} outside clip of {self._clip.length}")
        if not self._param.min - 1e-9 <= value <= self._param.max + 1e-9:
            raise ValueError(f"value {value} outside [{self._param.min}, {self._param.max}]")
        self.steps.append((time, duration, value))


class EnvMixin:
    """Envelopes de clip: se crean SOLO en clips de Session; en Arrangement no se pueden leer."""

    def _init_env(self):
        self._envs, self.in_arrangement, self._fail_env = {}, False, False

    def create_automation_envelope(self, param):
        if self.in_arrangement:
            raise RuntimeError("clip envelopes can only be created on Session clips")
        if self._fail_env:
            raise RuntimeError("param is not automatable")
        if id(param) in self._envs:
            raise RuntimeError("envelope already exists")
        env = self._envs[id(param)] = Env(self, param)
        return env

    def automation_envelope(self, param):
        if self.in_arrangement:
            return None
        return self._envs.get(id(param))

    def env_steps(self, param):
        env = self._envs.get(id(param))
        return env.steps if env else None


class AClip(EnvMixin):
    """
    Clip de audio como en Live 12.4: el span en Arrangement (end_time) NO sigue a los
    markers; solo lo fija el loop del clip de Session al duplicarlo. Sin crop().
    """

    def __init__(self, path, start, natural, honor_trim=True, gain_display=True, sample_secs=None,
                 fail_warp=False):
        self._init_env()
        self.file_path, self.start_time = path, start
        self.end_time = start + natural
        self.start_marker, self.end_marker = 0.0, natural
        self.loop_start, self.loop_end, self.looping = 0.0, natural, False
        self.warping, self.warp_mode, self.pitch_coarse, self.gain = True, 0, 0, 0.4
        self._honor, self._gain_display = honor_trim, gain_display
        self.sample_rate = 44100.0
        self.sample_length = int((sample_secs if sample_secs is not None else 4.0) * 44100)
        self._fail_warp = fail_warp
        self._natural, self._refuse_extend, self._tempo = natural, False, 120.0
        # Live 12.4: el auto-warp deja un marker de ancla pegado al inicio (visto en real)
        self.warp_markers = [types.SimpleNamespace(beat_time=0.0, sample_time=0.0),
                             types.SimpleNamespace(beat_time=0.03125, sample_time=0.0146)]

    def add_warp_marker(self, warp_marker):
        # Live 12.4 real: un solo argumento (objeto warp marker); (float, float) da ArgumentError
        if self._fail_warp:
            raise RuntimeError("add_warp_marker refused")
        if isinstance(warp_marker, dict):
            beat_time, sample_time = warp_marker["beat_time"], warp_marker["sample_time"]
        else:
            beat_time, sample_time = warp_marker.beat_time, warp_marker.sample_time
        if beat_time > self.end_marker + 1e-6:  # visto en real: marker mas alla del end_marker
            raise RuntimeError("Segment length out of range")
        self.warp_markers.append(types.SimpleNamespace(beat_time=beat_time, sample_time=sample_time))
        self.warp_markers.sort(key=lambda m: m.beat_time)

    def remove_warp_marker(self, beat_time):
        self.warp_markers = [m for m in self.warp_markers if abs(m.beat_time - beat_time) > 1e-9]

    def move_warp_marker(self, beat_time, beat_time_distance):
        # Hipotesis a verificar en Live: mover el marker del final arrastra end_marker/loop_end
        marker = next(m for m in self.warp_markers if abs(m.beat_time - beat_time) < 1e-9)
        carries = abs(self.end_marker - beat_time) < 1e-9
        marker.beat_time += beat_time_distance
        if carries:
            object.__setattr__(self, "end_marker", marker.beat_time)
            object.__setattr__(self, "loop_end", marker.beat_time)
        self.warp_markers.sort(key=lambda m: m.beat_time)

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
        if (k in ("end_marker", "loop_end") and self.__dict__.get("_refuse_extend")
                and self.__dict__.get("warping") and v > self._natural + 1e-9):
            raise RuntimeError(f"{k} beyond the clip's natural end refused")
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
        self.clip = AClip(path, 0.0, s.natural, s.honor_trim, s.gain_display, s.sample_secs,
                          s.fail_warp)
        self.clip._fail_env = s.fail_envelopes
        self.clip._refuse_extend = s.refuse_extend

    def create_clip(self, length):
        self.clip = MClip(0.0, length)
        self.clip._fail_env = self._track._song.fail_envelopes

    def delete_clip(self):
        self.clip = None


class Scene:
    pass


class MClip(EnvMixin):
    def __init__(self, start, length):
        self._init_env()
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
        clip.in_arrangement = True
        self.arrangement_clips.append(clip)
        return clip

    def duplicate_clip_to_arrangement(self, clip, time):
        # Como el spike real: el span = largo de loop del clip de Session
        if isinstance(clip, MClip):
            new = MClip(time, clip.length)
            new.notes = list(clip.notes)
        else:
            span = clip.loop_end - clip.loop_start
            if not clip.warping:
                # Sin warp loop/markers van en SEGUNDOS; T-003b: el span puede quedar en el natural
                span = (self._song.natural if self._song.unwarped_span == "natural"
                        else span * self._song.tempo / 60.0)
            if not clip.looping and self._song.dup_ignores_loop_off:
                span = self._song.natural  # Live ignora el loop si looping=False
            new = AClip(clip.file_path, time, span)
            new.warp_markers = list(clip.warp_markers)
            for k in ("start_marker", "end_marker", "loop_start", "loop_end", "looping",
                      "warping", "warp_mode", "pitch_coarse", "gain"):
                object.__setattr__(new, k, getattr(clip, k))
        new._envs, new.in_arrangement = dict(clip._envs), True  # los envelopes sobreviven
        self.arrangement_clips.append(new)
        return None  # la referencia no es confiable: se re-busca por start_time

    def delete_clip(self, clip):
        self.arrangement_clips.remove(clip)

    def create_midi_clip(self, start, length):
        clip = MClip(start, length)
        clip.in_arrangement = True
        self.arrangement_clips.append(clip)
        return clip

    def insert_device(self, name, index):
        if name == "Nope":
            raise RuntimeError("device not found")
        dev = (Simpler() if name == "Simpler" else Comp(self._song) if name == "Compressor"
               else Utility() if name == "Utility" else Device(name))
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
        self.fail_envelopes = False
        self.sample_secs, self.fail_warp, self.dup_ignores_loop_off = None, False, False
        # "natural": un clip sin warp conserva el span de creacion (T-003b); "honor": respeta el loop
        self.unwarped_span, self.refuse_extend = "natural", False
        self.master_track = Track(self, False, "Master")

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
def utility_chain(song):
    """Utility como ULTIMO device de las pistas 0 y 1 (D-15: la automatizacion de nivel va ahi)."""
    for t in song.tracks[:2]:
        t.devices.append(Utility())


UTIL_GAIN = {"device": "Utility", "param": "Output"}


def util_param(track):
    return next(p for p in track.devices[-1].parameters if p.name == "Output")


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


def one_shot(song, wav, **kw):
    params = {"track": 0, "path": wav, "start_beat": 0.0, "one_shot": True}
    params.update(kw)
    return production.clip_place_audio(song, params)


def test_one_shot_span_equals_sample_beats_not_live_guess(song, wav) -> None:
    song.tempo, song.sample_secs, song.natural = 134.0, 21.30, 32.0  # riser 'excite'
    out = one_shot(song, wav, start_beat=64.0)
    c = out["clips"][0]
    assert out["ok"] is True and out["warnings"] == []
    assert abs(out["sample_beats"] - 47.57) < 0.01
    assert c["start_time"] == 64.0 and abs(c["span"] - out["sample_beats"]) < 1e-6
    assert c["method"] == out["method"] == "session_duplicate_oneshot"
    assert abs(out["covered_beats"] - out["sample_beats"]) < 1e-6


def test_one_shot_forces_warp_markers_to_whole_sample(song, wav) -> None:
    song.tempo, song.sample_secs = 134.0, 21.30
    out = one_shot(song, wav)
    wm = out["warp_markers"]
    assert wm[0] == {"beat_time": 0.0, "sample_time": 0.0}
    assert len(wm) == 2  # el marker de ancla automatico se elimina
    assert abs(wm[-1]["beat_time"] - out["sample_beats"]) < 1e-9
    assert abs(wm[-1]["sample_time"] - 21.30) < 1e-9


def test_one_shot_warps_with_complex_by_default_and_honors_warp_mode(song, wav) -> None:
    song.natural = 32.0  # con natural == sample, A (sin warp) acertaria de casualidad
    assert one_shot(song, wav)["clips"][0]["warp_mode"] == 4
    assert one_shot(song, wav, start_beat=32.0, warp_mode=6)["clips"][0]["warp_mode"] == 6
    assert all(c.warping is True for c in song.tracks[0].arrangement_clips)


def test_one_shot_loop_and_markers_match_sample_beats_and_scratch_is_clean(song, wav) -> None:
    song.sample_secs = 2.0  # 4 beats a 120
    one_shot(song, wav)
    placed = song.tracks[0].arrangement_clips[0]
    assert (placed.loop_start, placed.loop_end, placed.end_marker, placed.looping) == (0.0, 4.0, 4.0, False)
    assert not any(sl.has_clip for sl in song.tracks[0].clip_slots) and len(song.scenes) == 1


def test_one_shot_end_beat_places_start_before_it(song, wav) -> None:
    song.sample_secs = 4.0  # 8 beats
    out = production.clip_place_audio(song, {"track": 0, "path": wav, "end_beat": 64.0, "one_shot": True})
    c = out["clips"][0]
    assert c["start_time"] == 56.0 and c["end_time"] == 64.0 and out["ok"] is True


def test_one_shot_end_beat_before_zero_is_rejected_and_cleans_up(song, wav) -> None:
    song.sample_secs = 4.0
    assert code_of(production.clip_place_audio, song,
                   {"track": 0, "path": wav, "end_beat": 4.0, "one_shot": True}) == errors.INVALID_PARAMS
    assert song.tracks[0].arrangement_clips == []
    assert not any(sl.has_clip for sl in song.tracks[0].clip_slots)


def test_one_shot_start_and_end_beat_validation(song, wav) -> None:
    base = {"track": 0, "path": wav, "one_shot": True}
    for bad in ({}, {"start_beat": 0, "end_beat": 8}):
        assert code_of(production.clip_place_audio, song, dict(base, **bad)) == errors.INVALID_PARAMS
    assert code_of(production.clip_place_audio, song,
                   {"track": 0, "path": wav, "end_beat": 8, "length_beats": 4}) == errors.INVALID_PARAMS


def test_one_shot_falls_back_to_looping_true_when_live_ignores_loop_off(song, wav) -> None:
    song.dup_ignores_loop_off, song.natural, song.sample_secs = True, 32.0, 4.0
    out = one_shot(song, wav)
    assert out["ok"] is True and out["clips"][0]["span"] == 8.0
    assert out["strategy"] == "forced_markers"
    assert len(song.tracks[0].arrangement_clips) == 1  # la copia mala se borro
    assert song.tracks[0].arrangement_clips[0].looping is True


def test_one_shot_warp_marker_failure_reports_step_and_places_nothing(song, wav) -> None:
    song.fail_warp, song.natural, song.refuse_extend = True, 32.0, True
    out = one_shot(song, wav)
    assert out["ok"] is False and out["clips"] == []
    assert out["steps"]["forced_markers_warp_markers"]["ok"] is False
    assert any("warp" in w for w in out["warnings"])
    assert song.tracks[0].arrangement_clips == []
    assert not any(sl.has_clip for sl in song.tracks[0].clip_slots)


def test_one_shot_without_sample_length_fails_clearly(song, wav) -> None:
    orig = AClip.__init__

    def init(self, *a, **k):
        orig(self, *a, **k)
        del self.sample_length

    AClip.__init__ = init
    try:
        out = one_shot(song, wav)
    finally:
        AClip.__init__ = orig
    assert out["ok"] is False and out["clips"] == []
    assert any("sample_length" in w for w in out["warnings"])


def test_one_shot_wrong_span_reports_not_ok(song, wav) -> None:
    song.dup_ignores_loop_off = True  # Live ignora looping=False ...
    song.natural = 32.0
    song.sample_secs = 2.0
    orig = Track.delete_clip
    Track.delete_clip = lambda self, clip: None  # ... y ademas no se puede reintentar
    try:
        out = one_shot(song, wav)
    finally:
        Track.delete_clip = orig
    assert out["ok"] is False and any("span" in w for w in out["warnings"])


# --- T-003d: cadena de estrategias para one_shot ---------------------------------


def riser(song):
    song.tempo, song.sample_secs, song.natural = 134.0, 21.30, 32.0  # auto-warp a 32 beats (real)


def test_one_shot_strategy_a_unwarped_session_uses_seconds_and_wins_first(song, wav) -> None:
    riser(song)
    song.unwarped_span = "honor"
    out = one_shot(song, wav, start_beat=8.0)
    placed = song.tracks[0].arrangement_clips[0]
    assert out["ok"] is True and out["strategy"] == "unwarped_session" and out["strategy_errors"] == {}
    assert placed.warping is False and len(song.tracks[0].arrangement_clips) == 1
    # sin warp loop/markers van en segundos
    assert (placed.loop_start, placed.start_marker) == (0.0, 0.0)
    assert abs(placed.loop_end - 21.30) < 1e-9 and abs(placed.end_marker - 21.30) < 1e-9
    assert abs(out["clips"][0]["span"] - out["sample_beats"]) < 0.05
    assert "forced_markers_warp_markers" not in out["steps"]


def test_one_shot_strategy_a_retries_with_looping_true(song, wav) -> None:
    riser(song)
    song.unwarped_span, song.dup_ignores_loop_off = "honor", True
    out = one_shot(song, wav)
    assert out["strategy"] == "unwarped_session"
    assert out["steps"]["unwarped_session_duplicate_retry"]["ok"] is True
    assert song.tracks[0].arrangement_clips[0].looping is True


def test_one_shot_falls_to_strategy_b_when_unwarped_keeps_creation_span(song, wav) -> None:
    riser(song)  # unwarped_span="natural": A deja span 32 -> se descarta
    out = one_shot(song, wav, start_beat=64.0)
    assert out["ok"] is True and out["strategy"] == "forced_markers"
    assert "span" in out["strategy_errors"]["unwarped_session"]
    assert len(song.tracks[0].arrangement_clips) == 1  # la copia de A se borro
    assert abs(out["covered_beats"] - out["sample_beats"]) < 0.05
    wm = out["warp_markers"]
    assert wm[0] == {"beat_time": 0.0, "sample_time": 0.0} and len(wm) == 2
    assert abs(wm[-1]["sample_time"] - 21.30) < 1e-9
    assert out["warnings"] == [] or all("unwarped_session" in w for w in out["warnings"])


def test_one_shot_strategy_b_extends_end_marker_before_loop_and_marker(song, wav) -> None:
    riser(song)
    out = one_shot(song, wav)
    steps = list(out["steps"])
    assert steps.index("forced_markers_extend_end") < steps.index("forced_markers_extend_loop")         < steps.index("forced_markers_warp_markers")


def test_one_shot_falls_to_strategy_c_when_live_refuses_to_extend(song, wav) -> None:
    riser(song)
    song.refuse_extend = True
    out = one_shot(song, wav)
    assert out["ok"] is True and out["strategy"] == "move_end_marker"
    assert set(out["strategy_errors"]) == {"unwarped_session", "forced_markers"}
    assert "Segment length out of range" in out["strategy_errors"]["forced_markers"]
    assert out["steps"]["forced_markers_extend_end"]["ok"] is False  # se registra el rechazo
    wm = out["warp_markers"]
    assert wm[0] == {"beat_time": 0.0, "sample_time": 0.0} and len(wm) == 2
    assert abs(wm[-1]["beat_time"] - out["sample_beats"]) < 1e-9
    assert len(song.tracks[0].arrangement_clips) == 1
    assert not any(sl.has_clip for sl in song.tracks[0].clip_slots) and len(song.scenes) == 1


def test_one_shot_all_strategies_fail_places_nothing_and_reports_each(song, wav) -> None:
    riser(song)
    song.refuse_extend = True
    song.fail_warp = True  # add_warp_marker rechazado en B y en C
    out = one_shot(song, wav)
    assert out["ok"] is False and out["clips"] == [] and out["strategy"] is None
    assert set(out["strategy_errors"]) == {"unwarped_session", "forced_markers", "move_end_marker"}
    for name in out["strategy_errors"]:
        assert any(name in w for w in out["warnings"])
    assert song.tracks[0].arrangement_clips == []
    assert not any(sl.has_clip for sl in song.tracks[0].clip_slots) and len(song.scenes) == 1


def test_one_shot_reports_diagnostics_of_the_first_session_clip(song, wav) -> None:
    riser(song)
    d = one_shot(song, wav)["diagnostics"]
    assert d["warping"] is True and d["length"] == 32.0
    assert (d["start_marker"], d["end_marker"], d["loop_start"], d["loop_end"]) == (0.0, 32.0, 0.0, 32.0)
    assert d["warp_markers"][0] == {"beat_time": 0.0, "sample_time": 0.0}
    assert len(d["warp_markers"]) == 2  # el auto-warp, antes de que cualquier estrategia lo toque
    assert d["sample_rate"] == 44100.0 and d["sample_length"] == int(21.30 * 44100)


def test_one_shot_diagnostics_degrade_to_unavailable_instead_of_failing(song, wav) -> None:
    orig = AClip.__init__

    def init(self, *a, **k):
        orig(self, *a, **k)
        del self.sample_rate

    AClip.__init__ = init
    try:
        out = one_shot(song, wav)
    finally:
        AClip.__init__ = orig
    assert out["diagnostics"]["sample_rate"].startswith("unavailable")


def test_one_shot_longer_than_requested_length_warns(song, wav) -> None:
    out = one_shot(song, wav, length_beats=4.0)
    assert out["clips"][0]["span"] == 8.0
    assert any("one_shot" in w and "8" in w for w in out["warnings"])


def test_one_shot_applies_pitch_and_gain(song, wav) -> None:
    out = one_shot(song, wav, pitch_coarse=-3, gain_db=-6)
    assert out["clips"][0]["pitch_coarse"] == -3
    assert out["gain"]["applied"] is True


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


# --- T-010: unidades por display, envelopes, master, sidechain -----------------


def test_parse_display_units() -> None:
    assert production.parse_display("1.20 kHz") == 1200.0
    assert production.parse_display("200 ms") == 200.0
    assert production.parse_display("1.5 s") == 1500.0
    assert production.parse_display("-6.0 dB") == -6.0
    assert production.parse_display("50 %") == 50.0
    assert production.parse_display("abc") is None


def test_raw_for_display_hits_hz_target_across_khz_boundary() -> None:
    freq = Device("X").parameters[3]
    for target in (200.0, 1000.0, 8000.0):
        raw, within = production._raw_for_display(freq, target)
        assert within is True
        assert abs(production.parse_display(freq.str_for_value(raw)) - target) <= target * 0.02


def test_raw_for_display_handles_decreasing_display() -> None:
    p = Param("Rev", 0.0, 1.0, 0.5, lambda v: f"{100 - 50 * v:.1f} %")
    raw, within = production._raw_for_display(p, 75.0)
    assert within and abs(raw - 0.5) < 0.01


def test_raw_for_display_unreachable_is_flagged() -> None:
    freq = Device("X").parameters[3]
    raw, within = production._raw_for_display(freq, 90000.0)
    assert within is False and raw == 1.0


def test_raw_for_display_unparseable_raises_invalid() -> None:
    p = Param("Div", 0, 1, 0, lambda v: "1/4 note")
    assert code_of(production._raw_for_display, p, 3.0) == errors.INVALID_PARAMS


def env_of(song, track_idx, clip_idx, param):
    return song.tracks[track_idx].arrangement_clips[clip_idx].env_steps(param)


VOL_RAMP = [{"target": UTIL_GAIN, "points": [[0, 0.2], [8, 0.8]]}]


@pytest.mark.usefixtures("utility_chain")
def test_place_audio_envelope_forces_session_duplicate_and_writes_ramp(song, wav) -> None:
    out = place(song, wav, envelopes=VOL_RAMP)
    assert out["ok"] is True and methods(out) == ["session_duplicate"]
    steps = env_of(song, 0, 0, util_param(song.tracks[0]))
    assert len(steps) == 32
    assert steps[0] == (0.0, 0.25, pytest.approx(0.2))
    assert steps[16][2] == pytest.approx(0.5)  # beat 4 de 8: mitad de la rampa
    assert all(d == 0.25 for _, d, _ in steps)
    assert out["clips"][0]["envelopes"] == [
        {"target": UTIL_GAIN, "param": "Output", "ok": True, "steps": 32}]
    assert not any(s.has_clip for s in song.tracks[0].clip_slots) and len(song.scenes) == 1


@pytest.mark.usefixtures("utility_chain")
def test_place_audio_envelope_tiles_restart_when_span_is_tile(song, wav) -> None:
    out = place(song, wav, length_beats=20.0, envelopes=[
        {"target": UTIL_GAIN, "points": [[0, 0.1], [8, 0.9]]}])
    assert methods(out) == ["session_duplicate"] * 3 and out["ok"] is True
    vol = util_param(song.tracks[0])
    firsts = [env_of(song, 0, i, vol)[0][2] for i in range(3)]
    assert firsts == [pytest.approx(0.1)] * 3
    assert [len(env_of(song, 0, i, vol)) for i in range(3)] == [32, 32, 16]  # ultimo tile parcial


@pytest.mark.usefixtures("utility_chain")
def test_place_audio_envelope_range_span_slices_one_sweep_across_tiles(song, wav) -> None:
    out = place(song, wav, start_beat=16.0, length_beats=20.0, points_span="range", envelopes=[
        {"target": UTIL_GAIN, "points": [[0, 0.0], [20, 1.0]]}])
    assert out["ok"] is True
    vol = util_param(song.tracks[0])
    by_start = {c.start_time: c.env_steps(vol) for c in song.tracks[0].arrangement_clips}
    assert by_start[16.0][0][2] == pytest.approx(0.0)
    assert by_start[24.0][0][2] == pytest.approx(0.4)
    assert by_start[32.0][0][2] == pytest.approx(0.8)
    assert by_start[32.0][-1][0] == 3.75 and by_start[32.0][-1][1] == 0.25  # tile corto, tiempos relativos


@pytest.mark.usefixtures("utility_chain")
def test_place_audio_envelope_holds_first_and_last_value_outside_points(song, wav) -> None:
    place(song, wav, envelopes=[{"target": UTIL_GAIN, "points": [[2, 0.3], [4, 0.6]]}])
    steps = env_of(song, 0, 0, util_param(song.tracks[0]))
    assert steps[0][2] == pytest.approx(0.3) and steps[-1][2] == pytest.approx(0.6)


def test_place_audio_envelope_display_points_resolved_by_unit(song, wav) -> None:
    song.tracks[0].devices.append(Device("Auto Filter"))
    freq = song.tracks[0].devices[0].parameters[3]
    out = place(song, wav, envelopes=[{
        "target": {"device": "Auto Filter", "param": "Frequency"},
        "points": [[0, {"display": 200}], [8, {"display": 4000}]]}])
    assert out["ok"] is True
    steps = env_of(song, 0, 0, freq)
    first = production.parse_display(freq.str_for_value(steps[0][2]))
    assert abs(first - 200) <= 200 * 0.02
    info = out["clips"][0]["envelopes"][0]
    assert info["target"] == {"device": "Auto Filter", "param": "Frequency"} and info["param"] == "Frequency"


def test_place_audio_envelope_pan_and_send_targets(song, wav) -> None:
    out = place(song, wav, envelopes=[
        {"target": "pan", "points": [[0, -1.0], [8, 1.0]]},
        {"target": {"send": 1}, "points": [[0, 0.0], [8, 0.5]]}])
    assert out["ok"] is True
    m = song.tracks[0].mixer_device
    assert env_of(song, 0, 0, m.panning)[0][2] == pytest.approx(-1.0)
    assert env_of(song, 0, 0, m.sends[1])[-1][2] > 0.45
    assert env_of(song, 0, 0, m.sends[0]) is None
    assert [e["ok"] for e in out["clips"][0]["envelopes"]] == [True, True]


@pytest.mark.usefixtures("utility_chain")
def test_place_audio_envelope_section_loop_uses_hook_too(song, wav) -> None:
    out = place(song, wav, length_beats=4.0, loop_start=0.0, loop_end=4.0, envelopes=VOL_RAMP)
    assert out["ok"] is True
    assert len(env_of(song, 0, 0, util_param(song.tracks[0]))) == 16


@pytest.mark.usefixtures("utility_chain")
def test_place_audio_envelope_failure_is_reported_per_tile_not_fatal(song, wav) -> None:
    song.fail_envelopes = True
    out = place(song, wav, envelopes=VOL_RAMP)
    e = out["clips"][0]["envelopes"][0]
    assert e["ok"] is False and "not automatable" in e["error"]
    assert out["ok"] is False and any("envelope" in w for w in out["warnings"])
    assert len(song.tracks[0].arrangement_clips) == 1  # el clip igual quedo colocado


@pytest.mark.parametrize("bad", [
    "volume",                                                       # no es lista
    [{"points": [[0, 0.1]]}],                                       # falta target
    [{"target": "tone", "points": [[0, 0.1]]}],
    [{"target": {"send": 9}, "points": [[0, 0.1]]}],
    [{"target": {"send": True}, "points": [[0, 0.1]]}],
    [{"target": {"device": "Nope", "param": "Drive"}, "points": [[0, 0.1]]}],
    [{"target": {"device": 0, "param": "Nope"}, "points": [[0, 0.1]]}],
    [{"target": UTIL_GAIN, "points": []}],
    [{"target": UTIL_GAIN, "points": [[0]]}],
    [{"target": UTIL_GAIN, "points": [[-1, 0.1]]}],
    [{"target": UTIL_GAIN, "points": [[0, "x"]]}],
    [{"target": UTIL_GAIN, "points": [[0, {"display": "x"}]]}],
    [{"target": UTIL_GAIN, "points": [[0, 7.0]]}],                   # raw fuera de rango
    [{"target": UTIL_GAIN, "points": [[0, 0.1], [0, 0.2]]}],         # tiempos no crecientes
    [{"target": UTIL_GAIN, "points": [[0, 0.1]]}] * 17,
])
@pytest.mark.usefixtures("utility_chain")
def test_place_audio_envelope_validation(song, wav, bad) -> None:
    song.tracks[0].devices.append(Device("Auto Filter"))
    params = {"track": 0, "path": wav, "start_beat": 0, "length_beats": 8, "envelopes": bad}
    assert code_of(production.clip_place_audio, song, params) == errors.INVALID_PARAMS
    assert song.tracks[0].arrangement_clips == []  # valida todo antes de tocar el set


@pytest.mark.usefixtures("utility_chain")
def test_place_audio_envelope_other_param_validation(song, wav) -> None:
    kw = {"track": 0, "path": wav, "start_beat": 0, "length_beats": 8}
    assert code_of(production.clip_place_audio, song, dict(kw, envelopes=VOL_RAMP, points_span="x")) == errors.INVALID_PARAMS
    assert code_of(production.clip_place_audio, song, dict(kw, envelopes=VOL_RAMP, one_shot=True)) == errors.INVALID_PARAMS


def test_place_audio_no_envelopes_keeps_old_path_and_has_no_envelope_key(song, wav) -> None:
    out = place(song, wav)
    assert methods(out) == ["create_audio_clip"] and "envelopes" not in out["clips"][0]


@pytest.mark.usefixtures("utility_chain")
def test_create_midi_envelope_goes_through_session_slot(song) -> None:
    out = production.clip_create_midi(song, LIVE, {
        "track": 1, "start_beat": 32.0, "length_beats": 4.0, "notes": NOTES, "envelopes": VOL_RAMP})
    assert (out["start_time"], out["end_time"], out["note_count"]) == (32.0, 36.0, 2)
    assert out["method"] == "session_duplicate" and out["ok"] is True
    clip = song.tracks[1].arrangement_clips[0]
    assert len(clip.env_steps(util_param(song.tracks[1]))) == 16
    assert out["envelopes"] == [{"target": UTIL_GAIN, "param": "Output", "ok": True, "steps": 16}]
    assert not any(s.has_clip for s in song.tracks[1].clip_slots) and len(song.scenes) == 1
    assert len(song.tracks[1].arrangement_clips) == 1


def test_create_midi_envelope_validates_before_touching_the_set(song) -> None:
    bad = {"track": 1, "start_beat": 0, "length_beats": 4, "notes": [],
           "envelopes": [{"target": "tone", "points": [[0, 0]]}]}
    assert code_of(production.clip_create_midi, song, LIVE, bad) == errors.INVALID_PARAMS
    assert song.tracks[1].arrangement_clips == []


@pytest.mark.usefixtures("utility_chain")
def test_create_midi_envelope_failure_reported(song) -> None:
    song.fail_envelopes = True
    out = production.clip_create_midi(song, LIVE, {
        "track": 1, "start_beat": 0.0, "length_beats": 4.0, "notes": NOTES, "envelopes": VOL_RAMP})
    assert out["ok"] is False and out["envelopes"][0]["ok"] is False
    assert out["note_count"] == 2


# --- master ----------------------------------------------------------------


def test_master_device_insert_and_set_param(song) -> None:
    ins = production.master_device_insert(song, {"name": "Limiter"})
    assert ins["index"] == 0 and song.master_track.devices[0].name == "Limiter"
    out = production.master_device_set_param(song, {"device": "Limiter", "name": "Drive", "value": 0.7})
    assert out["value"] == 0.7
    byd = production.master_device_set_param(song, {"device": 0, "name": "Frequency", "display": 1000})
    assert byd["within_tolerance"] is True and "kHz" in byd["display"]


def test_master_set_mixer_volume_db(song) -> None:
    out = production.master_set_mixer(song, {"volume_db": -3})
    assert abs(float(out["volume"]["display"].split()[0]) + 3) <= 0.1 + 1e-9
    assert out["volume"]["within_tolerance"] is True
    assert code_of(production.master_set_mixer, song, {}) == errors.INVALID_PARAMS
    assert code_of(production.master_set_mixer, song, {"volume_db": "loud"}) == errors.INVALID_PARAMS


def test_master_device_errors(song) -> None:
    assert code_of(production.master_device_set_param, song,
                   {"device": 3, "name": "x", "value": 1}) == errors.INVALID_PARAMS


# --- device.set_param por unidad -------------------------------------------


def test_device_set_param_display(song) -> None:
    production.device_insert(song, {"track": 0, "name": "Auto Filter"})
    out = production.device_set_param(song, {"track": 0, "device": 0, "name": "Frequency", "display": 440})
    assert out["within_tolerance"] is True and out["display"].endswith("Hz")
    assert abs(production.parse_display(out["display"]) - 440) <= 440 * 0.02
    assert song.tracks[0].devices[0].parameters[3].value == out["value"]


def test_device_set_param_value_xor_display(song) -> None:
    production.device_insert(song, {"track": 0, "name": "Auto Filter"})
    base = {"track": 0, "device": 0, "name": "Frequency"}
    assert code_of(production.device_set_param, song, dict(base)) == errors.INVALID_PARAMS
    assert code_of(production.device_set_param, song, dict(base, value=0.5, display=440)) == errors.INVALID_PARAMS
    assert code_of(production.device_set_param, song, dict(base, display="x")) == errors.INVALID_PARAMS


def test_return_device_set_param_display(rsong) -> None:
    rsong.return_tracks[0].devices.append(Device("Auto Filter"))
    out = production.return_device_set_param(rsong, {"return": 0, "device": "Auto Filter",
                                                     "name": "Frequency", "display": 2000})
    assert out["within_tolerance"] is True


def test_device_set_param_plain_value_has_no_within_tolerance(song) -> None:
    production.device_insert(song, {"track": 0, "name": "Saturator"})
    out = production.device_set_param(song, {"track": 0, "device": 0, "name": "Drive", "value": 0.3})
    assert "within_tolerance" not in out


# --- sidechain -------------------------------------------------------------


@pytest.fixture
def csong(song):
    song.tracks[0].name, song.tracks[1].name = "Kick", "Bass"
    production.device_insert(song, {"track": 1, "name": "Compressor"})
    return song


def test_sidechain_routes_by_track_name_and_enables_sc(csong) -> None:
    out = production.compressor_set_sidechain(
        csong, {"track": 1, "device": "Compressor", "source_track_name": "Kick"})
    comp = csong.tracks[1].devices[0]
    assert comp.input_routing_type.display_name == "Kick"
    assert next(p for p in comp.parameters if p.name == "S/C On").value == 1.0
    assert out["ok"] is True and out["input_routing_type"] == "Kick"
    assert out["available_input_routing_types"] == ["Ext. In", "No Input", "Kick", "Bass"]
    assert out["available_input_routing_channels"] == ["Post FX", "Pre FX"]
    assert out["input_routing_channel"] == "Post FX" and out["sidechain_on"] is True
    assert [p["name"] for p in out["sc_params"]] == ["S/C On", "S/C Gain", "S/C Mix"]
    assert out["sc_params"][0]["value"] == 1.0


def test_sidechain_unknown_source_lists_options(csong) -> None:
    with pytest.raises(errors.CommandError) as e:
        production.compressor_set_sidechain(csong, {"track": 1, "device": 0, "source_track_name": "Nope"})
    assert e.value.code == errors.INVALID_PARAMS and "Kick" in e.value.message
    assert csong.tracks[1].devices[0].input_routing_type.display_name == "No Input"


def test_sidechain_device_without_routing_api_is_clear_error(csong) -> None:
    production.device_insert(csong, {"track": 1, "name": "Saturator"})
    with pytest.raises(errors.CommandError) as e:
        production.compressor_set_sidechain(
            csong, {"track": 1, "device": "Saturator", "source_track_name": "Kick"})
    assert e.value.code == errors.INVALID_PARAMS and "input_routing" in e.value.message


def test_sidechain_without_sc_on_param_reports_and_not_ok(csong) -> None:
    comp = csong.tracks[1].devices[0]
    comp.parameters = [p for p in comp.parameters if p.name != "S/C On"]
    out = production.compressor_set_sidechain(csong, {"track": 1, "device": 0, "source_track_name": "Kick"})
    assert out["ok"] is False and out["sidechain_on"] is None
    assert comp.input_routing_type.display_name == "Kick"
    assert any("S/C On" in w for w in out["warnings"])


def test_sidechain_routing_failure_is_a_step_error(csong) -> None:
    comp = csong.tracks[1].devices[0]

    class Frozen(type(comp)):
        def __setattr__(self, k, v):
            if k == "input_routing_type":
                raise RuntimeError("routing locked")
            object.__setattr__(self, k, v)

    comp.__class__ = Frozen
    out = production.compressor_set_sidechain(csong, {"track": 1, "device": 0, "source_track_name": "Kick"})
    assert out["ok"] is False and out["steps"]["set_input_routing_type"]["ok"] is False


def test_sidechain_validation(csong) -> None:
    base = {"track": 1, "device": 0, "source_track_name": "Kick"}
    assert code_of(production.compressor_set_sidechain, csong, dict(base, track=9)) == errors.TRACK_NOT_FOUND
    assert code_of(production.compressor_set_sidechain, csong, dict(base, source_track_name="")) == errors.INVALID_PARAMS
    assert code_of(production.compressor_set_sidechain, csong, dict(base, device=5)) == errors.INVALID_PARAMS


def test_sidechain_matches_routing_name_with_track_number_prefix(csong) -> None:
    comp = csong.tracks[1].devices[0]
    comp.available_input_routing_types = [RT("Ext. In"), RT("No Input"), RT("1-Kick"), RT("2-Bass")]
    out = production.compressor_set_sidechain(csong, {"track": 1, "device": 0, "source_track_name": "kick"})
    assert out["input_routing_type"] == "1-Kick" and out["ok"] is True


def test_volume_target_is_forbidden_by_golden_rule_d15():
    # D-15 (regla inquebrantable de Gabriel): nunca automatizar el fader; usar Utility al final.
    track = types.SimpleNamespace(mixer_device=types.SimpleNamespace(volume=object(), panning=object(), sends=[]))
    with pytest.raises(Exception) as exc:
        production._env_param(track, "volume")
    assert "D-15" in str(exc.value) and "Utility" in str(exc.value)


def test_d15_error_names_the_real_level_param_and_the_helper_command():
    track = types.SimpleNamespace(mixer_device=types.SimpleNamespace(volume=object(), panning=object(), sends=[]))
    with pytest.raises(errors.CommandError) as exc:
        production._env_param(track, "volume")
    assert exc.value.code == errors.INVALID_PARAMS
    assert "Output" in str(exc.value) and "utility.ensure_last" in str(exc.value)


@pytest.mark.usefixtures("utility_chain")
def test_place_audio_with_volume_envelope_is_rejected_before_touching_the_set(song, wav) -> None:
    params = {"track": 0, "path": wav, "start_beat": 0, "length_beats": 8,
              "envelopes": [{"target": "volume", "points": [[0, 0.1]]}]}
    assert code_of(production.clip_place_audio, song, params) == errors.INVALID_PARAMS
    assert song.tracks[0].arrangement_clips == []


# --- utility.ensure_last (D-15) ------------------------------------------------


def test_ensure_last_inserts_utility_on_an_empty_chain(song) -> None:
    out = production.utility_ensure_last(song, {"track": 0})
    assert out["inserted"] is True and out["device"] == 0 and out["track"] == 0
    assert [d.name for d in song.tracks[0].devices] == ["Utility"]
    assert out["param"] == {"name": "Output", "min": -1.0, "max": 1.0, "value": 0.0, "display": "0.00 dB"}
    assert out["target"] == {"device": 0, "param": "Output"} and out["warnings"] == []


def test_ensure_last_appends_after_the_existing_chain(song) -> None:
    song.tracks[0].devices += [Device("Saturator"), Device("Reverb")]
    out = production.utility_ensure_last(song, {"track": 0})
    assert out["inserted"] is True and out["device"] == 2
    assert [d.name for d in song.tracks[0].devices] == ["Saturator", "Reverb", "Utility"]


def test_ensure_last_is_idempotent_when_utility_is_already_last(song) -> None:
    song.tracks[0].devices += [Device("Saturator"), Utility()]
    out = production.utility_ensure_last(song, {"track": 0})
    assert out["inserted"] is False and out["device"] == 1 and len(song.tracks[0].devices) == 2
    again = production.utility_ensure_last(song, {"track": 0})
    assert again["device"] == 1 and len(song.tracks[0].devices) == 2


def test_ensure_last_with_a_utility_that_is_not_last_adds_a_new_one_and_reports_it(song) -> None:
    song.tracks[0].devices += [Utility(), Device("Saturator")]
    out = production.utility_ensure_last(song, {"track": 0})
    assert out["inserted"] is True and out["device"] == 2
    assert out["other_utilities"] == [0]
    assert any("not last" in w for w in out["warnings"])
    assert out["target"] == {"device": 2, "param": "Output"}  # por indice: hay dos Utility
    assert len(song.tracks[0].devices) == 3


def test_ensure_last_recognises_utility_by_class_even_if_renamed(song) -> None:
    u = Utility()
    u.name = "Gain Stage"
    song.tracks[0].devices.append(u)
    out = production.utility_ensure_last(song, {"track": 0})
    assert out["inserted"] is False and out["device"] == 0


def test_ensure_last_on_return_and_master(rsong) -> None:
    r = production.utility_ensure_last(rsong, {"return": 1})
    assert r["track"] == {"return": 1} and r["device"] == 0
    assert [d.name for d in rsong.return_tracks[1].devices] == ["Utility"]
    r0 = production.utility_ensure_last(rsong, {"track": {"return": 0}})
    assert r0["device"] == 1 and r0["track"] == {"return": 0}  # Reverb + Utility
    m = production.utility_ensure_last(rsong, {"track": "master"})
    assert m["track"] == "master" and m["device"] == 0
    assert [d.name for d in rsong.master_track.devices] == ["Utility"]


@pytest.mark.parametrize("bad", [{}, {"track": 9}, {"track": "x"}, {"return": 9}, {"track": True}])
def test_ensure_last_rejects_unknown_tracks(song, bad) -> None:
    assert code_of(production.utility_ensure_last, song, bad) in (errors.TRACK_NOT_FOUND, errors.INVALID_PARAMS)
    assert song.tracks[0].devices == [] and song.master_track.devices == []


def test_ensure_last_target_feeds_a_clip_envelope(song, wav) -> None:
    t = production.utility_ensure_last(song, {"track": 0})["target"]
    out = place(song, wav, envelopes=[{"target": t, "points": [[0, 0.2], [8, 0.8]]}])
    assert out["ok"] is True and len(env_of(song, 0, 0, util_param(song.tracks[0]))) == 32


def test_ensure_last_fails_clearly_if_utility_has_no_level_param(song) -> None:
    u = Utility()
    u.parameters = [p for p in u.parameters if p.name != "Output"]
    song.tracks[0].devices.append(u)
    assert code_of(production.utility_ensure_last, song, {"track": 0}) == errors.LOM_ERROR
