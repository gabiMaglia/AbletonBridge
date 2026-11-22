"""Entry point de Live: create_instance, pump del dispatcher, disconnect."""
import importlib
import socket
import sys
import threading
import types

import pytest

import remote_script.AbletonBridge as pkg
from remote_script.AbletonBridge import surface


def _c_instance(song):
    return types.SimpleNamespace(song=lambda: song)


def _song():
    return types.SimpleNamespace(tempo=120.0, is_playing=False, tracks=[])


@pytest.fixture
def instance(fake_live, monkeypatch):
    monkeypatch.setattr(surface, "PORT_RANGE", range(0, 1))
    monkeypatch.setattr(surface, "PREFERRED_PORT", 0)
    inst = pkg.create_instance(_c_instance(_song()))
    yield inst
    inst.disconnect()


def _call_while_pumping(instance, client, cmd):
    out = {}
    t = threading.Thread(target=lambda: out.update(client.send_request(cmd, {})))
    t.start()
    while t.is_alive():
        instance._tick()
        t.join(0.02)
    return out


def test_create_instance_returns_surface_and_binds_port(instance) -> None:
    assert isinstance(instance, surface.AbletonBridge)
    assert instance.server.port
    assert any("port" in m.lower() for m in instance.logs)


def test_tick_drains_dispatcher_and_reschedules(instance) -> None:
    ran = []
    instance.dispatcher.submit(lambda: ran.append(1))
    before = len(instance.scheduled)
    instance._tick()
    assert ran == [1]
    assert len(instance.scheduled) == before + 1


def test_tick_swallows_job_exceptions(instance) -> None:
    def boom():
        raise RuntimeError("x")

    instance.dispatcher.submit(boom)
    instance._tick()  # no debe propagar a Live
    assert any("error" in m.lower() for m in instance.logs)


def test_tick_does_not_reschedule_after_disconnect(instance) -> None:
    instance.disconnect()
    before = len(instance.scheduled)
    instance._tick()
    assert len(instance.scheduled) == before


def test_disconnect_releases_port(instance) -> None:
    port = instance.server.port
    instance.disconnect()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
    finally:
        s.close()


def test_handlers_end_to_end_through_pump(instance) -> None:
    from mcp_server.abletonbridge_mcp.client import BridgeClient

    client = BridgeClient(host="127.0.0.1", port=instance.server.port, timeout=2.0)
    client.connect()
    try:
        assert client.ping() == {"pong": True, "live_version": "12.4.16", "api_level": 12}
        assert _call_while_pumping(instance, client, "state.get")["tempo"] == 120.0
        probe = _call_while_pumping(instance, client, "probe.api")
        assert probe["members"]["Track.create_audio_clip"] is True
    finally:
        client.close()


def test_uses_framework_base_when_available(monkeypatch) -> None:
    fw = types.ModuleType("_Framework")
    cs_mod = types.ModuleType("_Framework.ControlSurface")

    class FakeCS:
        def __init__(self, c_instance):
            self.c_instance = c_instance

    cs_mod.ControlSurface = FakeCS
    monkeypatch.setitem(sys.modules, "_Framework", fw)
    monkeypatch.setitem(sys.modules, "_Framework.ControlSurface", cs_mod)
    reloaded = importlib.reload(surface)
    try:
        assert issubclass(reloaded.AbletonBridge, FakeCS)
    finally:
        monkeypatch.undo()
        importlib.reload(surface)


def test_tick_survives_spike_tick_exception(instance) -> None:
    def boom():
        raise RuntimeError("spike")

    instance.spikes.tick = boom
    ran = []
    instance.dispatcher.submit(lambda: ran.append(1))
    instance._tick()
    assert ran == [1] and any("spike" in m for m in instance.logs)


def test_spike_handlers_registered(instance) -> None:
    for cmd in ("spike.automation_session", "spike.automation_record_start",
                "spike.automation_record_status", "spike.cleanup",
                "spike.automation_arm", "spike.audio_clip", "spike.devices",
                "spike.simpler_slice"):
        assert cmd in instance.server._handlers


def test_state_detail_handler_registered(instance) -> None:
    assert "state.detail" in instance.server._handlers


def test_production_handlers_registered(instance) -> None:
    for cmd in ("song.set", "track.create", "track.set_mixer", "clip.place_audio",
                "clip.create_midi", "device.insert", "device.set_param", "simpler.load",
                "locator.set", "locator.clear_all", "track.delete"):
        assert cmd in instance.server._handlers
