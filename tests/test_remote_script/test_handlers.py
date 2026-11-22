"""Handlers LOM (ping/get_state/probe_api) contra objetos falsos."""
import types

from remote_script.AbletonBridge import handlers


def _clip(name, length, midi=True):
    return types.SimpleNamespace(name=name, length=length, is_midi_clip=midi)


def _slot(clip=None):
    return types.SimpleNamespace(has_clip=clip is not None, clip=clip)


def _song():
    t0 = types.SimpleNamespace(
        name="Bass", has_midi_input=True,
        clip_slots=[_slot(_clip("riff", 4.0)), _slot()],
    )
    t1 = types.SimpleNamespace(name="Audio 1", has_midi_input=False, clip_slots=[_slot()])
    return types.SimpleNamespace(tempo=128.0, is_playing=True, tracks=[t0, t1])


def test_live_info_formats_version_and_api_level(fake_live) -> None:
    info = handlers.read_live_info(fake_live)
    assert info == {"live_version": "12.4.16", "api_level": 12}


def test_get_state_with_clips() -> None:
    state = handlers.get_state(_song(), {"live_version": "12.4.16"}, {"include_clips": True})
    assert state["tempo"] == 128.0
    assert state["is_playing"] is True
    assert state["live_version"] == "12.4.16"
    assert state["tracks"][0] == {
        "index": 0, "name": "Bass", "is_midi": True,
        "clips": [{"slot_index": 0, "name": "riff", "length_beats": 4.0, "is_midi": True}],
    }
    assert state["tracks"][1]["clips"] == []


def test_get_state_without_clips_omits_clips() -> None:
    state = handlers.get_state(_song(), {"live_version": "x"}, {"include_clips": False})
    assert "clips" not in state["tracks"][0]


def test_get_state_default_includes_clips() -> None:
    state = handlers.get_state(_song(), {"live_version": "x"}, {})
    assert "clips" in state["tracks"][0]


def test_probe_api_all_present(fake_live) -> None:
    result = handlers.probe_api(fake_live, {"live_version": "12.4.16"})
    assert result["live_version"] == "12.4.16"
    members = result["members"]
    assert members["Track.create_audio_clip"] is True
    assert members["Application.browser"] is True
    assert members["Browser.load_item"] is True
    assert len(members) == 23  # 4+6+1+8+1+1+1+1 miembros del ticket
    assert all(v is True for v in members.values())


def test_probe_api_reports_missing_member(install_fake_live) -> None:
    live = install_fake_live(missing_members=["Clip.crop"])
    members = handlers.probe_api(live, {"live_version": "12.4.16"})["members"]
    assert members["Clip.crop"] is False
    assert members["Clip.add_new_notes"] is True


def test_probe_api_reports_class_missing_without_crashing(install_fake_live) -> None:
    live = install_fake_live(missing_classes=["SimplerDevice"])
    members = handlers.probe_api(live, {"live_version": "12.4.16"})["members"]
    assert members["SimplerDevice.replace_sample"] == "class_missing"
