"""state.detail: lectura completa y de solo lectura del set, contra fakes del LOM."""
import types

import pytest

from remote_script.AbletonBridge import state_detail

_FROZEN = {"on": False}


class LomWrite(BaseException):
    """BaseException: los safe() del codigo bajo test no pueden tragarsela."""


class NS(types.SimpleNamespace):
    def __setattr__(self, k, v):
        if _FROZEN["on"]:
            raise LomWrite(k)
        super().__setattr__(k, v)


class Param:
    def __init__(self, name, value, default, lo=0.0, hi=1.0, quantized=False):
        self.name, self.value, self.default_value = name, value, default
        self.min, self.max, self.is_quantized = lo, hi, quantized

    def str_for_value(self, v):
        return f"{v:.2f}u"


def _device(name="Comp", cls="Compressor2", params=None, **extra):
    return NS(
        name=name, class_name=cls, type=1, is_active=True,
        parameters=params if params is not None else [
            Param("Device On", 1.0, 1.0, quantized=True),
            Param("Threshold", 0.5, 0.5),
            Param("Ratio", 0.8, 0.3),
        ],
        can_have_chains=False, **extra,
    )


def _mixer(vol=0.85, pan=0.0, sends=(0.0,)):
    return NS(
        volume=Param("Volume", vol, 0.85),
        panning=Param("Pan", pan, 0.0),
        sends=[Param("Send A", s, 0.0) for s in sends],
    )


def _audio_clip(**kw):
    base = dict(
        name="loop", length=4.0, is_audio_clip=True, is_midi_clip=False,
        file_path="C:/x/loop.wav", warping=True, warp_mode=6, pitch_coarse=-2,
        pitch_fine=0, gain=0.5, gain_display_string="-6 dB", looping=True,
        loop_start=0.0, loop_end=4.0, start_marker=0.0, end_marker=4.0,
        start_time=8.0, end_time=12.0,
    )
    base.update(kw)
    return NS(**base)


def _midi_clip():
    return NS(
        name="notes", length=4.0, is_audio_clip=False, is_midi_clip=True,
        looping=True, loop_start=0.0, loop_end=4.0, start_marker=0.0, end_marker=4.0,
        start_time=0.0, end_time=4.0,
        get_all_notes_extended=lambda: [1, 2, 3],
    )


def _slot(clip=None):
    return NS(has_clip=clip is not None, clip=clip)


def _track(name="Audio", audio=True, devices=None, session=None, arrangement=None, **kw):
    base = dict(
        name=name, has_audio_input=audio, has_midi_input=not audio,
        is_foldable=False, is_grouped=False, group_track=None, color_index=3,
        mute=False, solo=False, arm=False,
        output_routing_type=NS(display_name="Master"),
        mixer_device=_mixer(), devices=devices or [],
        clip_slots=session or [], arrangement_clips=arrangement or [],
    )
    base.update(kw)
    return NS(**base)


def _song(tracks=None, returns=None):
    return NS(
        tempo=120.0, signature_numerator=4, signature_denominator=4,
        song_length=64.0, current_song_time=0.0, is_playing=False,
        loop=True, loop_start=0.0, loop_length=16.0,
        cue_points=[NS(name="Drop", time=32.0)],
        root_note=0, scale_name="Minor",
        tracks=tracks or [], return_tracks=returns or [],
        master_track=_track("Master", devices=[_device("Limiter", "Limiter")]),
    )


def test_song_block() -> None:
    out = state_detail.get_state_detail(_song(), {})
    s = out["song"]
    assert s["tempo"] == 120.0 and s["signature_numerator"] == 4
    assert s["loop"] == {"on": True, "start": 0.0, "length": 16.0}
    assert s["cue_points"] == [{"name": "Drop", "time": 32.0}]
    assert s["scale_name"] == "Minor"


def test_track_basics_and_mixer_display() -> None:
    out = state_detail.get_state_detail(_song([_track("Kick")]), {})
    t = out["tracks"][0]
    assert t["index"] == 0 and t["kind"] == "audio" and t["name"] == "Kick"
    assert t["output_routing"] == "Master"
    assert t["mixer"]["volume"] == {"value": 0.85, "display": "0.85u"}
    assert t["mixer"]["sends"][0]["display"] == "0.00u"


def test_kind_midi_and_group() -> None:
    grp = _track("Grp", audio=False, is_foldable=True, has_midi_input=False, arm=None)
    mid = _track("Mel", audio=False, is_grouped=True, group_track=NS(name="Grp"))
    out = state_detail.get_state_detail(_song([grp, mid]), {})
    assert out["tracks"][0]["kind"] == "group"
    assert out["tracks"][1]["kind"] == "midi"
    assert out["tracks"][1]["group_name"] == "Grp"


def test_group_arm_unreadable_does_not_abort() -> None:
    class Grp:
        name = "G"
        has_audio_input = False
        has_midi_input = False
        is_foldable = True
        is_grouped = False
        group_track = None
        mute = False
        solo = False
        output_routing_type = NS(display_name="Master")
        mixer_device = _mixer()
        devices = []
        clip_slots = []
        arrangement_clips = []

        @property
        def arm(self):
            raise RuntimeError("group tracks cannot be armed")

    out = state_detail.get_state_detail(_song([Grp()]), {})
    assert out["tracks"][0]["arm"] == "unavailable: RuntimeError"
    assert out["tracks"][0]["name"] == "G"


def test_params_changed_omits_defaults() -> None:
    out = state_detail.get_state_detail(_song([_track(devices=[_device()])]), {})
    names = [p["name"] for p in out["tracks"][0]["devices"][0]["parameters"]]
    assert names == ["Ratio"]


def test_params_changed_keeps_device_on_when_off() -> None:
    dev = _device(params=[Param("Device On", 0.0, 1.0, quantized=True)])
    out = state_detail.get_state_detail(_song([_track(devices=[dev])]), {})
    assert [p["name"] for p in out["tracks"][0]["devices"][0]["parameters"]] == ["Device On"]


def test_params_all_and_none() -> None:
    song = _song([_track(devices=[_device()])])
    allp = state_detail.get_state_detail(song, {"params": "all"})["tracks"][0]["devices"][0]
    assert len(allp["parameters"]) == 3
    p = allp["parameters"][1]
    assert p == {
        "name": "Threshold", "value": 0.5, "display": "0.50u",
        "min": 0.0, "max": 1.0, "is_quantized": False,
    }
    nonep = state_detail.get_state_detail(song, {"params": "none"})["tracks"][0]["devices"][0]
    assert "parameters" not in nonep
    assert nonep["class_name"] == "Compressor2" and nonep["is_active"] is True


def test_invalid_params_mode_raises() -> None:
    with pytest.raises(ValueError):
        state_detail.get_state_detail(_song(), {"params": "bogus"})


def test_track_filter() -> None:
    song = _song([_track("A"), _track("B"), _track("C")])
    out = state_detail.get_state_detail(song, {"tracks": [2, 0, 99]})
    assert [t["index"] for t in out["tracks"]] == [0, 2]
    assert [t["name"] for t in out["tracks"]] == ["A", "C"]


def test_clips_session_and_arrangement() -> None:
    tr = _track(
        session=[_slot(), _slot(_audio_clip())],
        arrangement=[_audio_clip(), _midi_clip()],
    )
    t = state_detail.get_state_detail(_song([tr]), {})["tracks"][0]
    sc = t["session_clips"][0]
    assert sc["slot"] == 1 and sc["is_audio"] is True
    assert sc["file_path"] == "C:/x/loop.wav" and sc["warp_mode"] == 6
    assert sc["pitch_coarse"] == -2 and sc["gain"] == 0.5
    assert sc["gain_display"] == "-6 dB"
    arr = t["arrangement_clips"]
    assert arr[0]["start_time"] == 8.0 and arr[0]["end_time"] == 12.0
    assert arr[1]["is_audio"] is False and arr[1]["note_count"] == 3
    assert "file_path" not in arr[1]


def test_include_flags() -> None:
    tr = _track(session=[_slot(_audio_clip())], arrangement=[_audio_clip()])
    t = state_detail.get_state_detail(
        _song([tr]), {"include_session": False, "include_arrangement": False}
    )["tracks"][0]
    assert "session_clips" not in t and "arrangement_clips" not in t


def test_missing_optional_clip_fields_are_unavailable() -> None:
    clip = _audio_clip()
    del clip.gain_display_string
    tr = _track(arrangement=[clip])
    c = state_detail.get_state_detail(_song([tr]), {})["tracks"][0]["arrangement_clips"][0]
    assert c["gain_display"] == "unavailable: AttributeError"
    assert c["name"] == "loop"


def test_rack_chains_recursive_with_depth_cap_and_in_note() -> None:
    def rack(depth, inner=None):
        chain = NS(
            name=f"chain{depth}", mute=False, solo=False, in_note=36,
            devices=[inner] if inner else [_device("Leaf")],
        )
        d = _device(f"Rack{depth}", "DrumGroupDevice", params=[])
        d.can_have_chains = True
        d.chains = [chain]
        return d

    # 5 racks anidados: el limite es profundidad 3
    deep = rack(5)
    for lvl in (4, 3, 2, 1):
        deep = rack(lvl, deep)
    out = state_detail.get_state_detail(_song([_track(devices=[deep])]), {})
    d0 = out["tracks"][0]["devices"][0]
    assert d0["chains"][0]["in_note"] == 36
    d1 = d0["chains"][0]["devices"][0]
    d2 = d1["chains"][0]["devices"][0]
    assert "chains" in d2
    d3 = d2["chains"][0]["devices"][0]
    assert d3.get("chains_truncated") is True and "chains" not in d3


def test_returns_and_master() -> None:
    ret = _track("A-Reverb", devices=[_device("Reverb", "Reverb")])
    out = state_detail.get_state_detail(_song(returns=[ret]), {})
    assert out["returns"][0]["name"] == "A-Reverb"
    assert out["returns"][0]["devices"][0]["class_name"] == "Reverb"
    assert out["master"]["devices"][0]["class_name"] == "Limiter"
    assert "mixer" in out["master"]


def test_unreadable_device_field_does_not_abort() -> None:
    class Bad:
        name = "X"
        can_have_chains = False
        parameters = []

        @property
        def class_name(self):
            raise KeyError("nope")

    out = state_detail.get_state_detail(_song([_track(devices=[Bad()])]), {})
    assert out["tracks"][0]["devices"][0]["class_name"] == "unavailable: KeyError"


def test_read_only_no_setattr() -> None:
    """Con los fakes congelados, cualquier escritura al LOM revienta."""
    song = _song([_track(devices=[_device()], session=[_slot(_audio_clip())])])
    _FROZEN["on"] = True
    try:
        state_detail.get_state_detail(song, {"params": "all"})
    finally:
        _FROZEN["on"] = False
