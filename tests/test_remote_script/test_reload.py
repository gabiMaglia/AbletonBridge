"""T-011: bridge.reload / bridge.version — recarga de NUESTROS modulos sin reiniciar Live."""
import ast
import subprocess
import sys
import threading
import time
import types
from pathlib import Path

import pytest

import remote_script.AbletonBridge as pkg
from remote_script.AbletonBridge import errors, reloader, spikes, surface, version
from mcp_server.abletonbridge_mcp.client import BridgeClient

PKG_DIR = Path(pkg.__file__).parent
ROOT = PKG_DIR.parent.parent


def _c_instance(song):
    return types.SimpleNamespace(song=lambda: song)


@pytest.fixture
def instance(fake_live, monkeypatch):
    monkeypatch.setattr(surface, "PORT_RANGE", range(0, 1))
    monkeypatch.setattr(surface, "PREFERRED_PORT", 0)
    song = types.SimpleNamespace(tempo=120.0, is_playing=False, tracks=[])
    inst = pkg.create_instance(_c_instance(song))
    yield inst
    inst.disconnect()


def _call_while_pumping(instance, cmd, port=None):
    client = BridgeClient(host="127.0.0.1", port=port or instance.server.port, timeout=2.0)
    client.connect()
    out = {}
    t = threading.Thread(target=lambda: out.update(client.send_request(cmd, {})))
    t.start()
    while t.is_alive():
        instance._tick()
        t.join(0.02)
    client.close()
    return out


def _tick_until(instance, cond, tries=100):
    for _ in range(tries):
        instance._tick()
        if cond():
            return True
        time.sleep(0.02)
    return False


def _ping(port):
    client = BridgeClient(host="127.0.0.1", port=port, timeout=2.0)
    client.connect()
    try:
        return client.ping()
    finally:
        client.close()


def fake_reload(monkeypatch, effects=None, boom_on=None):
    """Sustituye importlib.reload: simula 'codigo nuevo' tocando atributos del modulo."""
    calls = []

    def reload(module):
        name = module.__name__.rsplit(".", 1)[-1]
        calls.append(name)
        if name == boom_on:
            raise SyntaxError(f"bad code in {name}")
        if effects and name in effects:
            effects[name](module)
        return module

    monkeypatch.setattr(reloader.importlib, "reload", reload)
    return calls


# --- bridge.version ---


def test_version_constants_exist() -> None:
    assert isinstance(version.VERSION, str) and version.VERSION
    assert isinstance(version.LOADED_AT, float)


def test_bridge_version_handler_reports_version_timestamp_and_count(instance) -> None:
    out = _call_while_pumping(instance, "bridge.version")
    assert out["version"] == version.VERSION
    assert out["loaded_at"] == version.LOADED_AT
    assert out["reload_count"] == 0 and out["port"] == instance.server.port


def test_bridge_handlers_registered(instance) -> None:
    for cmd in ("bridge.reload", "bridge.version"):
        assert cmd in instance.server._handlers


# --- server: callback posterior a la respuesta ---


def test_server_runs_after_response_callbacks_once_after_sending(instance) -> None:
    seen = []
    instance.server.after_response(lambda: seen.append(1))
    assert seen == []  # nada hasta que se envie una respuesta
    assert _ping(instance.server.port)["pong"] is True
    assert _tick_until(instance, lambda: seen == [1])
    _ping(instance.server.port)
    time.sleep(0.1)
    assert seen == [1]


# --- reload ---


def test_reload_command_responds_first_then_reloads_on_a_later_tick(instance, monkeypatch) -> None:
    calls = fake_reload(monkeypatch)
    old_runtime, port = instance.runtime, instance.server.port
    out = _call_while_pumping(instance, "bridge.reload")
    assert out == {"reloading": True}
    assert _tick_until(instance, lambda: instance.reload_count == 1)
    assert instance.runtime is not old_runtime
    assert instance.server.port == port  # mismo puerto, liberado y re-bindeado
    assert _ping(port)["pong"] is True
    assert calls == list(reloader.RELOAD_ORDER)


def test_reload_swaps_module_implementations_and_rebuilds_handler_table(instance, monkeypatch) -> None:
    class NewSpike(spikes.RecordSpike):
        marker = "new code"

    def swap(module):
        monkeypatch.setattr(module, "RecordSpike", NewSpike)

    fake_reload(monkeypatch, {"spikes": swap})
    old_handlers = instance.server._handlers
    _call_while_pumping(instance, "bridge.reload")
    assert _tick_until(instance, lambda: instance.reload_count == 1)
    assert isinstance(instance.spikes, NewSpike)
    assert instance.server._handlers is not old_handlers
    assert set(instance.server._handlers) == set(old_handlers)


def test_reload_answers_with_new_loaded_at(instance, monkeypatch) -> None:
    fake_reload(monkeypatch, {"version": lambda m: monkeypatch.setattr(m, "LOADED_AT", 123.0)})
    _call_while_pumping(instance, "bridge.reload")
    assert _tick_until(instance, lambda: instance.reload_count == 1)
    out = _call_while_pumping(instance, "bridge.version")
    assert out["loaded_at"] == 123.0 and out["reload_count"] == 1


def test_reload_keeps_pending_dispatcher_jobs(instance, monkeypatch) -> None:
    fake_reload(monkeypatch)
    ran = []
    instance._reload_pending = True
    instance.dispatcher.submit(lambda: ran.append(1))
    instance._reload()  # sin pump previo: el job pendiente no puede perderse
    instance._tick()
    assert ran == [1] and instance.reload_count == 1


def test_failed_module_reload_rolls_back_and_old_bridge_keeps_serving(instance, monkeypatch) -> None:
    fake_reload(monkeypatch, {"errors": lambda m: setattr(m, "MARK", 1)}, boom_on="production")
    old_runtime, port = instance.runtime, instance.server.port
    _call_while_pumping(instance, "bridge.reload")
    assert _tick_until(instance, lambda: any("reload failed" in m for m in instance.logs))  # no propaga
    assert instance.runtime is old_runtime and instance.reload_count == 0
    assert not hasattr(errors, "MARK")  # el modulo a medio recargar se restauro
    assert _ping(port)["pong"] is True


def test_new_runtime_failure_rebuilds_from_old_modules(instance, monkeypatch) -> None:
    from remote_script.AbletonBridge import runtime as runtime_mod

    class Broken(runtime_mod.BridgeRuntime):
        def start(self):
            raise OSError("cannot bind")

    fake_reload(monkeypatch, {"runtime": lambda m: monkeypatch.setattr(m, "BridgeRuntime", Broken)})
    old_runtime, port = instance.runtime, instance.server.port
    _call_while_pumping(instance, "bridge.reload")
    assert _tick_until(instance, lambda: any("rolled back" in m for m in instance.logs))
    assert instance.runtime is not old_runtime and not isinstance(instance.runtime, Broken)
    assert instance.server.port == port and _ping(port)["pong"] is True
    assert instance.reload_count == 0


def test_reload_is_deferred_while_locator_queue_is_busy(instance, monkeypatch) -> None:
    calls = fake_reload(monkeypatch)
    instance.locators._phase = "moving"
    instance.request_reload()
    instance._tick()
    assert calls == [] and instance.reload_count == 0
    instance.locators._phase = "idle"
    assert _tick_until(instance, lambda: instance.reload_count == 1)


def test_tick_never_raises_when_everything_fails(instance, monkeypatch) -> None:
    fake_reload(monkeypatch, boom_on="errors")
    instance.request_reload()
    instance._tick()  # no debe propagar a Live
    assert instance.runtime is not None


# --- reloader ---


def test_reload_order_covers_every_module_and_respects_imports() -> None:
    mods = {p.stem for p in PKG_DIR.glob("*.py")}
    assert set(reloader.RELOAD_ORDER) == mods - {"__init__", "surface", "reloader"}
    pos = {n: i for i, n in enumerate(reloader.RELOAD_ORDER)}
    for name in reloader.RELOAD_ORDER:
        tree = ast.parse((PKG_DIR / f"{name}.py").read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level == 1:
                deps = [node.module] if node.module else [a.name for a in node.names]
                for dep in deps:
                    assert pos[dep] < pos[name], f"{name} imports {dep} which reloads later"


def test_reload_package_only_touches_our_package(monkeypatch) -> None:
    calls = fake_reload(monkeypatch)
    for bad in ("os", "..errors", "a.b"):
        with pytest.raises(ValueError):
            reloader.reload_package(pkg.__name__, (bad,))
    assert calls == []


def test_reload_package_rollback_restores_state(monkeypatch) -> None:
    fake_reload(monkeypatch, {"errors": lambda m: setattr(m, "MARK", 1)})
    result = reloader.reload_package(pkg.__name__, ("errors",))
    assert hasattr(errors, "MARK")
    result.rollback()
    assert not hasattr(errors, "MARK")


def test_real_reload_end_to_end_in_a_clean_interpreter() -> None:
    """Sin fakes: importlib.reload real en un proceso aparte (no contaminar las clases de otros tests)."""
    code = r"""
import sys, types, threading, time
sys.path.insert(0, %r)
sys.modules["Live"] = __import__("tests.conftest", fromlist=["x"]).build_fake_live()
import remote_script.AbletonBridge as pkg
from remote_script.AbletonBridge import surface, version
from mcp_server.abletonbridge_mcp.client import BridgeClient
surface.PORT_RANGE, surface.PREFERRED_PORT = range(0, 1), 0
song = types.SimpleNamespace(tempo=120.0, is_playing=False, tracks=[])
inst = pkg.create_instance(types.SimpleNamespace(song=lambda: song))
before, port = version.LOADED_AT, inst.server.port
time.sleep(0.05)
inst.request_reload()
inst._tick()
assert inst.reload_count == 1, inst.logs
assert version.LOADED_AT > before
c = BridgeClient(port=inst.server.port, timeout=2.0); c.connect()
out = {}
t = threading.Thread(target=lambda: out.update(c.send_request("bridge.version", {})))
t.start()
while t.is_alive():
    inst._tick(); t.join(0.02)
assert out["loaded_at"] == version.LOADED_AT > before and out["reload_count"] == 1, out
assert inst.server.port == port
inst.disconnect()
print("OK")
""" % str(ROOT)
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                          cwd=str(ROOT), timeout=60)
    assert proc.returncode == 0 and "OK" in proc.stdout, proc.stdout + proc.stderr
