"""T-011: tools MCP live_bridge_version / live_bridge_reload (cliente falso, sin sockets)."""
import pytest

from mcp_server.abletonbridge_mcp.client import BridgeDisconnectedError, BridgeTimeoutError
from mcp_server.abletonbridge_mcp.server import live_bridge_reload, live_bridge_version


class FakeClient:
    """Responde bridge.version/bridge.reload; tras el reload cae la conexion y vuelve con otra marca."""

    def __init__(self, before=100.0, after=200.0, down_attempts=2, reloads=True, reload_error=None):
        self.loaded_at, self.after, self.reloads = before, after, reloads
        self.down_attempts, self.pending_down = down_attempts, 0
        self.connected, self.sent, self.connects = True, [], 0
        self.reload_error = reload_error

    def send_request(self, cmd, params):
        self.sent.append(cmd)
        if not self.connected:
            raise BridgeDisconnectedError("not connected")
        if cmd == "bridge.version":
            return {"version": "0.1.0", "loaded_at": self.loaded_at, "reload_count": 0, "port": 1}
        if cmd == "bridge.reload":
            if self.reload_error:
                raise self.reload_error
            if self.reloads:
                self.loaded_at, self.pending_down, self.connected = self.after, self.down_attempts, False
            return {"reloading": True}
        raise AssertionError(cmd)

    def close(self):
        self.connected = False

    def connect(self):
        self.connects += 1
        if self.pending_down > 0:
            self.pending_down -= 1
            raise ConnectionRefusedError("down")
        self.connected = True


class Clock:
    def __init__(self):
        self.t = 0.0

    def now(self):
        return self.t

    def sleep(self, s):
        self.t += s


def test_bridge_version_sends_command() -> None:
    c = FakeClient()
    assert live_bridge_version(c)["loaded_at"] == 100.0
    assert c.sent == ["bridge.version"]


def test_reload_polls_version_with_reconnect_until_timestamp_changes() -> None:
    c, clk = FakeClient(), Clock()
    out = live_bridge_reload(c, sleep=clk.sleep, clock=clk.now)
    assert out["reloaded"] is True and out["before"]["loaded_at"] == 100.0 and out["after"]["loaded_at"] == 200.0
    assert c.sent[:2] == ["bridge.version", "bridge.reload"]
    assert c.connects == 3  # 2 intentos con el puerto cerrado + 1 exitoso


def test_reload_times_out_when_timestamp_never_changes() -> None:
    c, clk = FakeClient(reloads=False), Clock()
    with pytest.raises(BridgeTimeoutError) as e:
        live_bridge_reload(c, timeout=15.0, sleep=clk.sleep, clock=clk.now)
    assert "15" in str(e.value) and "Live" in str(e.value)  # apunta al log de Live
    assert clk.t >= 15.0


def test_reload_tolerates_connection_dropping_right_after_the_reload_response() -> None:
    c, clk = FakeClient(down_attempts=0), Clock()
    assert live_bridge_reload(c, sleep=clk.sleep, clock=clk.now)["reloaded"] is True


def test_reload_command_error_is_propagated() -> None:
    c, clk = FakeClient(reload_error=BridgeTimeoutError("x")), Clock()
    with pytest.raises(BridgeTimeoutError):
        live_bridge_reload(c, sleep=clk.sleep, clock=clk.now)
