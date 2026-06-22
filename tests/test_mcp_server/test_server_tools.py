"""
Tests E2E (Claude -> MCP -> RemoteScript mockeado) de la(s) tool(s) MCP
base de T-002: `live_ping` (handshake) y `live_get_state` minimo.

El "Remote Script" es el FakeRemoteScript de test_client.py reutilizado
via fixture local equivalente, para no depender de Ableton.
"""
import json
import socket
import threading

import pytest

from mcp_server.abletonbridge_mcp.client import BridgeClient
from mcp_server.abletonbridge_mcp.server import live_get_state, live_ping


class FakeRemoteScript:
    def __init__(self, handler) -> None:
        self._handler = handler
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(("127.0.0.1", 0))
        self._sock.listen(1)
        self.port = self._sock.getsockname()[1]
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._serve, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        try:
            self._sock.close()
        except OSError:
            pass

    def _serve(self) -> None:
        try:
            self._sock.settimeout(0.5)
            conn, _ = self._sock.accept()
        except OSError:
            return
        conn.settimeout(0.5)
        buf = b""
        try:
            while not self._stop.is_set():
                try:
                    chunk = conn.recv(4096)
                except socket.timeout:
                    continue
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    req = json.loads(line.decode("utf-8"))
                    reply = self._handler(req)
                    if reply is not None:
                        conn.sendall((json.dumps(reply) + "\n").encode("utf-8"))
        finally:
            conn.close()


def make_handler():
    def handler(req):
        cmd = req["cmd"]
        if cmd == "ping":
            return {
                "id": req["id"],
                "ok": True,
                "result": {"pong": True, "live_version": "12.0.5", "api_level": 12},
            }
        if cmd == "state.get":
            return {
                "id": req["id"],
                "ok": True,
                "result": {
                    "tempo": 120.0,
                    "is_playing": False,
                    "live_version": "12.0.5",
                    "tracks": [],
                },
            }
        return {
            "id": req["id"],
            "ok": False,
            "error": {"code": "UNKNOWN_CMD", "message": cmd},
        }

    return handler


@pytest.fixture
def connected_client():
    srv = FakeRemoteScript(make_handler())
    srv.start()
    client = BridgeClient(host="127.0.0.1", port=srv.port, timeout=2.0)
    client.connect()
    yield client
    client.close()
    srv.stop()


def test_live_ping_tool_returns_handshake_payload(connected_client) -> None:
    result = live_ping(connected_client)
    assert result == {"pong": True, "live_version": "12.0.5", "api_level": 12}


def test_live_get_state_tool_returns_state_snapshot(connected_client) -> None:
    result = live_get_state(connected_client, include_clips=True)
    assert result["tempo"] == 120.0
    assert result["is_playing"] is False
    assert result["tracks"] == []
