"""Tools MCP de produccion v1 (T-003): arman el cmd/params correctos y omiten los None."""
from mcp_server.abletonbridge_mcp import server as s


class C:
    def __init__(self):
        self.sent = []

    def send_request(self, cmd, params):
        self.sent.append((cmd, params))
        return {"ok": True}


def sent(fn, *args, **kw):
    c = C()
    fn(c, *args, **kw)
    return c.sent[0]


def test_song_set_omits_none() -> None:
    assert sent(s.live_song_set, tempo=128.0, loop_on=True) == (
        "song.set", {"tempo": 128.0, "loop_on": True})


def test_track_create_defaults() -> None:
    assert sent(s.live_track_create, "midi", "Bass") == (
        "track.create", {"kind": "midi", "name": "Bass", "index": -1})


def test_track_set_mixer() -> None:
    assert sent(s.live_track_set_mixer, 2, volume_db=-6, mute=False) == (
        "track.set_mixer", {"track": 2, "volume_db": -6, "mute": False})


def test_clip_place_audio() -> None:
    assert sent(s.live_clip_place_audio, 0, "C:/a.wav", 16.0, 32.0, warp_mode=4, gain_db=-3) == (
        "clip.place_audio",
        {"track": 0, "path": "C:/a.wav", "start_beat": 16.0, "length_beats": 32.0,
         "warp_mode": 4, "gain_db": -3})


def test_clip_create_midi() -> None:
    notes = [{"pitch": 36, "start": 0, "duration": 1, "velocity": 100}]
    assert sent(s.live_clip_create_midi, 1, 0.0, 4.0, notes) == (
        "clip.create_midi", {"track": 1, "start_beat": 0.0, "length_beats": 4.0, "notes": notes})


def test_device_tools() -> None:
    assert sent(s.live_device_insert, 0, "Saturator") == (
        "device.insert", {"track": 0, "name": "Saturator", "index": -1})
    assert sent(s.live_device_set_param, 0, "Saturator", "Drive", 0.4) == (
        "device.set_param", {"track": 0, "device": "Saturator", "name": "Drive", "value": 0.4})
    assert sent(s.live_simpler_load, 1, 0, "C:/k.wav", playback_mode=1) == (
        "simpler.load", {"track": 1, "device": 0, "path": "C:/k.wav", "playback_mode": 1})


def test_locator_and_delete_tools() -> None:
    assert sent(s.live_locator_set, 64.0, "DROP") == ("locator.set", {"time": 64.0, "name": "DROP"})
    items = [{"time": 0.0, "name": "IN"}, {"time": 96.0, "name": "OUT"}]
    assert sent(s.live_locator_set_many, items) == ("locator.set_many", {"items": items})
    assert sent(s.live_locator_status) == ("locator.status", {})
    assert sent(s.live_locator_clear_all) == ("locator.clear_all", {})
    assert sent(s.live_track_delete, 3, "Old") == (
        "track.delete", {"track": 3, "confirm_name": "Old"})
