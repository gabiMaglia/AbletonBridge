"""T-023: timeout por comando, respuesta tardia y marca after_send del BridgeClient (sockets falsos)."""
import json
import socket

import pytest

from mcp_server.abletonbridge_mcp import client as c
from mcp_server.abletonbridge_mcp.client import (
    BridgeClient,
    BridgeDisconnectedError,
    BridgeTimeoutError,
)


class ScriptedSocket:
    """recv devuelve lo encolado; sin datos simula timeout. Registra settimeout."""

    def __init__(self):
        self.timeouts = []
        self.sent = []
        self.inbox = []
        self.send_error = None

    def settimeout(self, t):
        self.timeouts.append(t)

    def sendall(self, data):
        if self.send_error:
            raise self.send_error
        self.sent.append(json.loads(data))

    def recv(self, n):
        if not self.inbox:
            raise socket.timeout()
        return self.inbox.pop(0)

    def close(self):
        pass


def make_client(sock, **kw):
    cl = BridgeClient(**kw)
    cl._sock = sock
    return cl


def reply(req_id, **result):
    return (json.dumps({"id": req_id, "ok": True, "result": result}) + "\n").encode()


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("NEXO_MCP_TIMEOUT", raising=False)
    monkeypatch.delenv("NEXO_MCP_HEAVY_TIMEOUT", raising=False)


def test_heavy_commands_get_longer_timeout_than_reads() -> None:
    assert c.timeout_for("ping") == 5.0
    assert c.timeout_for("state.get") == 5.0
    for cmd in ("clip.place_audio", "song.set", "clip.create_midi"):
        assert c.timeout_for(cmd) == 30.0, cmd


def test_env_vars_override_defaults(monkeypatch) -> None:
    monkeypatch.setenv("NEXO_MCP_TIMEOUT", "7")
    monkeypatch.setenv("NEXO_MCP_HEAVY_TIMEOUT", "45")
    assert c.timeout_for("ping") == 7.0
    assert c.timeout_for("song.set") == 45.0


def test_bad_env_value_falls_back_to_default(monkeypatch) -> None:
    monkeypatch.setenv("NEXO_MCP_TIMEOUT", "abc")
    assert c.timeout_for("ping") == 5.0


def test_async_polling_commands_keep_short_timeout() -> None:
    for cmd in ("automation.record", "meter.capture", "locator.set_many", "bridge.reload", "automation.status"):
        assert c.timeout_for(cmd) == 5.0, cmd


def test_send_request_waits_with_the_commands_timeout() -> None:
    sock = ScriptedSocket()
    with pytest.raises(BridgeTimeoutError):
        make_client(sock, timeout=0.2).send_request("song.set", {})
    # heavy: ignora el timeout chico del constructor y usa el de la tabla (~30 s)
    assert sock.timeouts[0] > 25
    sock2 = ScriptedSocket()
    with pytest.raises(BridgeTimeoutError):
        make_client(sock2, timeout=0.2).send_request("ping", {})
    assert sock2.timeouts[0] <= 0.2


def test_late_response_does_not_corrupt_next_request() -> None:
    sock = ScriptedSocket()
    cl = make_client(sock, timeout=0.2)
    with pytest.raises(BridgeTimeoutError):
        cl.send_request("ping", {})
    stale_id = sock.sent[0]["id"]
    # la respuesta de la request vencida llega tarde, pegada a la de la siguiente
    sock.inbox.append(reply(stale_id, stale=True))
    orig_sendall = sock.sendall

    def sendall(data):
        orig_sendall(data)
        sock.inbox.append(reply(sock.sent[-1]["id"], fresh=True))

    sock.sendall = sendall
    assert cl.send_request("ping", {}) == {"fresh": True}


def test_not_connected_is_marked_not_sent() -> None:
    with pytest.raises(BridgeDisconnectedError) as ei:
        BridgeClient().send_request("ping", {})
    assert ei.value.after_send is False


def test_send_failure_is_marked_not_sent() -> None:
    sock = ScriptedSocket()
    sock.send_error = BrokenPipeError("broken pipe")
    with pytest.raises(BridgeDisconnectedError) as ei:
        make_client(sock).send_request("ping", {})
    assert ei.value.after_send is False


def test_recv_failure_is_marked_after_send() -> None:
    sock = ScriptedSocket()
    sock.recv = lambda n: b""
    with pytest.raises(BridgeDisconnectedError) as ei:
        make_client(sock).send_request("ping", {})
    assert ei.value.after_send is True
