"""T-017: tools MCP live_meter_* (cliente falso, sin sockets)."""
import pytest

from mcp_server.abletonbridge_mcp.client import BridgeTimeoutError
from mcp_server.abletonbridge_mcp.server import live_meter_cancel, live_meter_capture, live_meter_status


class Clock:
    def __init__(self):
        self.t = 0.0

    def now(self):
        return self.t

    def sleep(self, s):
        self.t += s


class FakeClient:
    def __init__(self, phases=("measuring", "measuring", "done"), tempo=120.0):
        self.phases, self.tempo, self.sent = list(phases), tempo, []

    def send_request(self, cmd, params):
        self.sent.append((cmd, params))
        if cmd == "meter.capture":
            return {"queued": True, "tempo": self.tempo}
        if cmd == "meter.status":
            phase = self.phases.pop(0) if len(self.phases) > 1 else self.phases[0]
            return {"phase": phase, "targets": []}
        if cmd == "meter.cancel":
            return {"cancelled": True, "phase": "cancelled"}
        raise AssertionError(cmd)


def run(client, clk=None, **kw):
    clk = clk or Clock()
    return live_meter_capture(client, 8.0, 16.0, sleep=clk.sleep, clock=clk.now, **kw)


def test_capture_queues_polls_until_done_and_returns_final_status() -> None:
    c = FakeClient()
    out = run(c)
    assert out["phase"] == "done"
    cmds = [x[0] for x in c.sent]
    assert cmds[0] == "meter.capture" and cmds.count("meter.status") == 3
    assert c.sent[0][1] == {"start_beat": 8.0, "end_beat": 16.0, "tracks": "all", "include_returns": True,
                            "include_master": True, "bin_bars": 8, "preroll_beats": 2.0}


def test_optional_params_are_forwarded_and_none_dropped() -> None:
    c = FakeClient()
    run(c, tracks=[0, 2], include_master=False, bin_bars=4, calibration={"points": [[0.5, -6.0]]})
    p = c.sent[0][1]
    assert p["tracks"] == [0, 2] and p["include_master"] is False and p["bin_bars"] == 4
    assert p["calibration"] == {"points": [[0.5, -6.0]]}


def test_timeout_cancels_and_raises() -> None:
    c = FakeClient(phases=("measuring",))
    with pytest.raises(BridgeTimeoutError):
        run(c)
    assert c.sent[-1][0] == "meter.cancel"


def test_bad_range_is_rejected_before_any_request() -> None:
    c = FakeClient()
    with pytest.raises(ValueError):
        live_meter_capture(c, 16.0, 8.0)
    assert c.sent == []


def test_status_and_cancel_are_passthrough() -> None:
    c = FakeClient()
    assert live_meter_status(c)["phase"] == "measuring"
    assert live_meter_cancel(c)["cancelled"] is True
