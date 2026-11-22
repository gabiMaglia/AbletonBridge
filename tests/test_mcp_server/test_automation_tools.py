"""T-012: tools MCP live_automation_* (cliente falso, sin sockets)."""
import pytest

from mcp_server.abletonbridge_mcp.client import BridgeError, BridgeTimeoutError
from mcp_server.abletonbridge_mcp.server import (
    live_automation_cancel,
    live_automation_clear,
    live_automation_record,
    live_automation_status,
)

LANES = [{"track": 0, "target": "volume", "points": [[8.0, 0.0], [16.0, 1.0]]}]


class Clock:
    def __init__(self):
        self.t = 0.0

    def now(self):
        return self.t

    def sleep(self, s):
        self.t += s


class FakeClient:
    """Responde automation.*; el status pasa por `phases` en cada consulta."""

    def __init__(self, phases=("recording", "recording", "done"), tempo=120.0, queue_error=None):
        self.phases, self.tempo, self.sent, self.queue_error = list(phases), tempo, [], queue_error

    def send_request(self, cmd, params):
        self.sent.append((cmd, params))
        if cmd == "automation.record":
            if self.queue_error:
                raise self.queue_error
            return {"queued": True, "tempo": self.tempo, "lanes": 1, "expected_seconds": 6.0}
        if cmd == "automation.status":
            phase = self.phases.pop(0) if len(self.phases) > 1 else self.phases[0]
            return {"phase": phase, "progress": 0.5, "lanes": [], "errors": []}
        if cmd == "automation.cancel":
            return {"cancelled": True, "phase": "cancelled"}
        if cmd == "automation.clear":
            return {"supported": False, "cleared": False}
        raise AssertionError(cmd)


def run(client, clk=None, **kw):
    clk = clk or Clock()
    return live_automation_record(client, 8.0, 16.0, LANES, sleep=clk.sleep, clock=clk.now, **kw), clk


def test_record_queues_then_polls_until_done_and_returns_the_final_status() -> None:
    c = FakeClient()
    out, _ = run(c)
    assert out["phase"] == "done"
    cmds = [x[0] for x in c.sent]
    assert cmds[0] == "automation.record" and cmds.count("automation.status") == 3
    assert c.sent[0][1] == {"start_beat": 8.0, "end_beat": 16.0, "lanes": LANES, "preroll_beats": 4.0}


def test_record_returns_on_error_phase_too() -> None:
    out, _ = run(FakeClient(phases=("error",)))
    assert out["phase"] == "error"


def test_record_times_out_at_beats_at_tempo_plus_20s_and_cancels() -> None:
    c, clk = FakeClient(phases=("recording",)), Clock()
    with pytest.raises(BridgeTimeoutError):
        live_automation_record(c, 8.0, 16.0, LANES, sleep=clk.sleep, clock=clk.now, poll_interval=1.0)
    assert 26.0 <= clk.t <= 28.0  # (8+4) beats a 120 BPM = 6 s, + 20 s
    assert c.sent[-1][0] == "automation.cancel"


def test_timeout_budget_uses_the_tempo_reported_by_the_bridge() -> None:
    c, clk = FakeClient(phases=("recording",), tempo=60.0), Clock()
    with pytest.raises(BridgeTimeoutError):
        live_automation_record(c, 8.0, 16.0, LANES, sleep=clk.sleep, clock=clk.now)
    assert clk.t >= 12.0 + 20.0


@pytest.mark.parametrize("kw", [
    {"start_beat": 8.0, "end_beat": 8.0},
    {"start_beat": -1.0, "end_beat": 8.0},
    {"lanes": []},
    {"lanes": "x"},
    {"preroll_beats": -2.0},
])
def test_record_validates_before_sending(kw) -> None:
    c = FakeClient()
    args = {"start_beat": 8.0, "end_beat": 16.0, "lanes": LANES}
    args.update(kw)
    with pytest.raises(ValueError):
        live_automation_record(c, **args)
    assert c.sent == []


def test_record_propagates_bridge_errors() -> None:
    with pytest.raises(BridgeError):
        run(FakeClient(queue_error=BridgeError("INVALID_PARAMS", "bad")))


def test_status_cancel_and_clear_send_their_commands() -> None:
    c = FakeClient()
    assert live_automation_status(c)["phase"] == "recording"
    assert live_automation_cancel(c)["cancelled"] is True
    out = live_automation_clear(c, 0, "volume", start_beat=8.0, end_beat=16.0)
    assert out["supported"] is False
    assert c.sent[-1] == ("automation.clear", {"track": 0, "target": "volume", "start_beat": 8.0, "end_beat": 16.0})
    live_automation_clear(c, 0, "volume")
    assert c.sent[-1] == ("automation.clear", {"track": 0, "target": "volume"})
