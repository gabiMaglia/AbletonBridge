"""T-024: timeout del dispatcher por comando, cancelacion de jobs no iniciados y estadisticas."""
import threading
import types

import pytest

import remote_script.AbletonBridge as pkg
from mcp_server.abletonbridge_mcp import client as mcp_client
from remote_script.AbletonBridge import dispatcher as disp
from remote_script.AbletonBridge import errors, surface
from remote_script.AbletonBridge.dispatcher import UIDispatcher


class FakeClock:
    def __init__(self) -> None:
        self.t = 100.0

    def __call__(self) -> float:
        return self.t


def _in_thread(fn):
    out: dict = {}

    def run() -> None:
        try:
            out["result"] = fn()
        except Exception as exc:  # noqa: BLE001
            out["error"] = exc

    t = threading.Thread(target=run)
    t.start()
    return t, out


# --- cancelacion de jobs que vencen sin haber empezado ---


def test_job_expired_before_start_is_cancelled_and_never_runs() -> None:
    d = UIDispatcher()
    ran = []
    with pytest.raises(errors.CommandError) as info:
        d.run_blocking(lambda: ran.append(1), timeout=0.05, cmd="song.set")
    d.pump()  # Live atiende la cola tarde: el job cancelado no debe correr
    assert ran == []
    assert info.value.code == errors.DISPATCH_TIMEOUT
    assert "no se ejecuto" in info.value.message and "song.set" in info.value.message


def test_cancelled_job_does_not_block_following_jobs() -> None:
    d = UIDispatcher()
    with pytest.raises(errors.CommandError):
        d.run_blocking(lambda: 1, timeout=0.01)
    seen = []
    d.submit(lambda: seen.append("next"))
    d.pump()
    assert seen == ["next"]


# --- jobs que ya empezaron: se espera su resultado real ---


def test_job_started_before_timeout_is_awaited_and_returns_real_result() -> None:
    d = UIDispatcher()
    started, release = threading.Event(), threading.Event()

    def slow() -> str:
        started.set()
        release.wait(2)
        return "applied"

    t, out = _in_thread(lambda: d.run_blocking(slow, timeout=0.05, cmd="song.set"))
    pump = threading.Thread(target=d.pump)
    pump.start()
    assert started.wait(2)
    t.join(0.2)  # el timeout (0.05) ya vencio: no debe haber devuelto error
    assert t.is_alive() and "error" not in out
    release.set()
    t.join(2)
    pump.join(2)
    assert out == {"result": "applied"}


def test_job_started_propagates_its_own_exception_after_timeout() -> None:
    d = UIDispatcher()
    started, release = threading.Event(), threading.Event()

    def slow() -> None:
        started.set()
        release.wait(2)
        raise ValueError("boom")

    t, out = _in_thread(lambda: d.run_blocking(slow, timeout=0.05))
    pump = threading.Thread(target=d.pump)
    pump.start()
    assert started.wait(2)
    t.join(0.2)
    release.set()
    t.join(2)
    pump.join(2)
    assert isinstance(out["error"], ValueError)


def test_started_job_has_a_hard_cap_with_an_explicit_message() -> None:
    d = UIDispatcher()
    started, release = threading.Event(), threading.Event()

    def stuck() -> None:
        started.set()
        release.wait(2)

    t, out = _in_thread(lambda: d.run_blocking(stuck, timeout=0.05, started_cap=0.1, cmd="clip.place_audio"))
    pump = threading.Thread(target=d.pump)
    pump.start()
    assert started.wait(2)
    t.join(2)
    release.set()
    pump.join(2)
    err = out["error"]
    assert isinstance(err, errors.CommandError) and err.code == errors.DISPATCH_TIMEOUT
    assert "sigue ejecutandose" in err.message and "relee" in err.message


def test_hard_cap_default_is_documented_and_generous() -> None:
    assert disp.STARTED_CAP >= 60.0


# --- timeouts por comando ---


def test_timeout_for_heavy_vs_reads() -> None:
    assert disp.timeout_for("song.set") == disp.HEAVY_TIMEOUT
    assert disp.timeout_for("state.get") == disp.READ_TIMEOUT
    assert disp.timeout_for("whatever") == disp.READ_TIMEOUT


def test_server_timeouts_are_strictly_below_client_timeouts() -> None:
    """Invariante: el servidor siempre contesta antes de que el cliente se rinda."""
    assert disp.HEAVY_COMMANDS == mcp_client.HEAVY_COMMANDS
    assert disp.HEAVY_TIMEOUT < mcp_client.HEAVY_TIMEOUT
    assert disp.READ_TIMEOUT < mcp_client.DEFAULT_TIMEOUT
    for cmd in mcp_client.HEAVY_COMMANDS | {"state.get", "ping", "bridge.version"}:
        assert disp.timeout_for(cmd) < (
            mcp_client.HEAVY_TIMEOUT if cmd in mcp_client.HEAVY_COMMANDS else mcp_client.DEFAULT_TIMEOUT
        )


def test_server_dispatch_uses_per_command_timeout() -> None:
    from remote_script.AbletonBridge.server import BridgeServer

    calls = []

    class Spy:
        def run_blocking(self, job, timeout=None, cmd=None):
            calls.append((cmd, timeout))
            return {}

    srv = BridgeServer(Spy(), lambda: {}, handlers={"song.set": lambda p: {}, "state.get": lambda p: {}})
    srv._dispatch("song.set", {})
    srv._dispatch("state.get", {})
    assert calls == [("song.set", disp.HEAVY_TIMEOUT), ("state.get", disp.READ_TIMEOUT)]


# --- instrumentacion (DT-09) ---


def test_stats_record_queue_wait_and_run_time_per_cmd() -> None:
    clock = FakeClock()
    d = UIDispatcher(clock=clock)

    def job() -> int:
        clock.t += 2.5  # tiempo de ejecucion
        return 7

    t, out = _in_thread(lambda: d.run_blocking(job, timeout=5.0, cmd="song.set"))
    while d._queue.empty():  # espera a que el thread encole
        pass
    clock.t += 1.0  # tiempo en cola
    d.pump()
    t.join(2)
    assert out == {"result": 7}
    s = d.stats()["song.set"]
    assert s["count"] == 1 and s["cancelled"] == 0
    assert s["last"] == [{"wait_ms": 1000.0, "run_ms": 2500.0}]


def test_stats_keep_only_last_n_and_count_cancelled() -> None:
    d = UIDispatcher()
    for _ in range(disp.STATS_KEEP + 3):
        d.submit(lambda: None)  # no importa; probamos run_blocking con pump desde otro thread
    d.pump()
    for i in range(disp.STATS_KEEP + 3):
        t, _out = _in_thread(lambda: d.run_blocking(lambda: 1, timeout=2.0, cmd="x"))
        while d._queue.empty():
            pass
        d.pump()
        t.join(2)
    with pytest.raises(errors.CommandError):
        d.run_blocking(lambda: 1, timeout=0.01, cmd="x")
    s = d.stats()["x"]
    assert len(s["last"]) == disp.STATS_KEEP
    assert s["count"] == disp.STATS_KEEP + 3 and s["cancelled"] == 1


def test_stats_without_cmd_are_not_recorded() -> None:
    d = UIDispatcher()
    t, _ = _in_thread(lambda: d.run_blocking(lambda: 1, timeout=2.0))
    while d._queue.empty():
        pass
    d.pump()
    t.join(2)
    assert d.stats() == {}


def test_bridge_stats_handler_registered_and_returns_dispatcher_stats(fake_live, monkeypatch) -> None:
    monkeypatch.setattr(surface, "PORT_RANGE", range(0, 1))
    monkeypatch.setattr(surface, "PREFERRED_PORT", 0)
    song = types.SimpleNamespace(tempo=120.0, is_playing=False, tracks=[])
    inst = pkg.create_instance(types.SimpleNamespace(song=lambda: song))
    try:
        assert "bridge.stats" in inst.server._handlers
        inst.runtime.dispatcher._record("song.set", 0.1, 0.2)
        out = inst.server._handlers["bridge.stats"]({})
        assert out["stats"]["song.set"]["last"] == [{"wait_ms": 100.0, "run_ms": 200.0}]
        assert out["timeouts"]["heavy_s"] == disp.HEAVY_TIMEOUT
        assert out["timeouts"]["read_s"] == disp.READ_TIMEOUT
    finally:
        inst.disconnect()
