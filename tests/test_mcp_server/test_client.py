"""
Tests del BridgeClient (servidor MCP actuando de cliente TCP) contra un
Remote Script MOCKEADO: un servidor TCP fake en localhost que responde
segun guiones controlados por el test. No requiere Ableton.

Cubre: handshake (ping), correlacion por id, timeout, reconexion con
backoff segun engram/04_api_contracts.md SS A.
"""
import json
import socket
import threading
import time

import pytest

from mcp_server.abletonbridge_mcp.client import (
    BridgeClient,
    BridgeDisconnectedError,
    BridgeTimeoutError,
)


class FakeRemoteScript:
    """Servidor TCP minimo que simula el Remote Script para tests."""

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


def ping_ok_handler(req):
    return {
        "id": req["id"],
        "ok": True,
        "result": {"pong": True, "live_version": "12.0.5", "api_level": 12},
    }


def silent_handler(req):
    return None  # nunca responde -> fuerza timeout


@pytest.fixture
def fake_rs():
    servers = []

    def _make(handler):
        srv = FakeRemoteScript(handler)
        srv.start()
        servers.append(srv)
        return srv

    yield _make
    for srv in servers:
        srv.stop()


class TestHandshake:
    def test_ping_returns_pong_payload(self, fake_rs) -> None:
        srv = fake_rs(ping_ok_handler)
        client = BridgeClient(host="127.0.0.1", port=srv.port, timeout=2.0)
        client.connect()
        result = client.ping()
        assert result == {"pong": True, "live_version": "12.0.5", "api_level": 12}
        client.close()

    def test_request_correlates_response_by_id(self, fake_rs) -> None:
        seen_ids = []

        def handler(req):
            seen_ids.append(req["id"])
            return {"id": req["id"], "ok": True, "result": {"echo": req["params"]}}

        srv = fake_rs(handler)
        client = BridgeClient(host="127.0.0.1", port=srv.port, timeout=2.0)
        client.connect()
        result = client.send_request("echo.test", {"a": 1})
        assert result == {"echo": {"a": 1}}
        assert len(seen_ids) == 1
        client.close()


class TestTimeout:
    def test_send_request_raises_bridge_timeout_when_no_reply(self, fake_rs) -> None:
        srv = fake_rs(silent_handler)
        client = BridgeClient(host="127.0.0.1", port=srv.port, timeout=0.3)
        client.connect()
        with pytest.raises(BridgeTimeoutError):
            client.send_request("ping", {})
        client.close()


class TestDisconnection:
    def test_send_request_raises_disconnected_if_not_connected(self) -> None:
        client = BridgeClient(host="127.0.0.1", port=1, timeout=1.0)
        with pytest.raises(BridgeDisconnectedError):
            client.send_request("ping", {})

    def test_connect_retries_with_backoff_until_server_available(self) -> None:
        # No hay servidor escuchando en este puerto al inicio.
        free_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        free_sock.bind(("127.0.0.1", 0))
        port = free_sock.getsockname()[1]
        free_sock.close()

        srv_holder = {}

        def start_server_late():
            time.sleep(0.2)
            srv = FakeRemoteScript(ping_ok_handler)
            srv._sock.close()
            srv._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv._sock.bind(("127.0.0.1", port))
            srv._sock.listen(1)
            srv.port = port
            srv.start()
            srv_holder["srv"] = srv

        t = threading.Thread(target=start_server_late)
        t.start()

        client = BridgeClient(
            host="127.0.0.1",
            port=port,
            timeout=1.0,
            backoff_schedule=(0.1, 0.2, 0.4),
        )
        client.connect_with_retry(max_attempts=5)
        result = client.ping()
        assert result["pong"] is True

        t.join(timeout=2)
        client.close()
        srv_holder["srv"].stop()
