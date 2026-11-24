"""
Tests del BridgeServer real (Remote Script) contra un BridgeClient real,
ambos en localhost. Sustituye a Ableton: no hay LOM real, pero valida
bind/fallback de puerto, framing end-to-end y el comando `ping`.
"""
from remote_script.AbletonBridge.dispatcher import UIDispatcher
from remote_script.AbletonBridge.server import BridgeServer

from mcp_server.abletonbridge_mcp.client import BridgeClient


def fake_live_info():
    return {"live_version": "12.0.5", "api_level": 12}


def test_bind_uses_preferred_port_when_free() -> None:
    server = BridgeServer(
        dispatcher=UIDispatcher(),
        live_info_provider=fake_live_info,
        preferred_port=0,  # 0 = puerto efimero asignado por el OS, siempre libre
        port_range=range(0, 1),
    )
    port = server.bind()
    assert port != 0  # el OS asigna uno real
    server.stop()


def test_bind_falls_back_to_next_port_if_preferred_busy() -> None:
    import socket as socket_module

    # Ocupa el puerto SIN SO_REUSEADDR para que el bind() de BridgeServer
    # (que si usa SO_REUSEADDR) no pueda compartirlo -- en Windows,
    # SO_REUSEADDR por si solo no fuerza el conflicto que necesitamos probar.
    blocker_sock = socket_module.socket(socket_module.AF_INET, socket_module.SOCK_STREAM)
    blocker_sock.bind(("127.0.0.1", 0))
    blocker_sock.listen(1)
    busy_port = blocker_sock.getsockname()[1]

    contender = BridgeServer(
        dispatcher=UIDispatcher(),
        live_info_provider=fake_live_info,
        preferred_port=busy_port,
        port_range=range(busy_port, busy_port + 3),
    )
    try:
        granted_port = contender.bind()
        assert granted_port != busy_port
        assert granted_port in range(busy_port, busy_port + 3)
    finally:
        blocker_sock.close()
        contender.stop()


def test_ping_end_to_end_real_sockets() -> None:
    server = BridgeServer(
        dispatcher=UIDispatcher(),
        live_info_provider=fake_live_info,
        preferred_port=0,
        port_range=range(0, 1),
    )
    port = server.bind()
    server.start()

    client = BridgeClient(host="127.0.0.1", port=port, timeout=2.0)
    try:
        client.connect()
        result = client.ping()
        assert result == {"pong": True, "live_version": "12.0.5", "api_level": 12}
    finally:
        client.close()
        server.stop()


def test_unknown_cmd_returns_unknown_cmd_error() -> None:
    from mcp_server.abletonbridge_mcp.client import BridgeCommandError

    server = BridgeServer(
        dispatcher=UIDispatcher(),
        live_info_provider=fake_live_info,
        preferred_port=0,
        port_range=range(0, 1),
    )
    port = server.bind()
    server.start()

    client = BridgeClient(host="127.0.0.1", port=port, timeout=2.0)
    try:
        client.connect()
        try:
            client.send_request("track.create_midi", {})
            assert False, "expected BridgeCommandError"
        except BridgeCommandError as exc:
            assert exc.code == "UNKNOWN_CMD"
    finally:
        client.close()
        server.stop()


def test_registered_handler_runs_via_dispatcher_pump() -> None:
    import threading

    dispatcher = UIDispatcher()
    main_thread = threading.get_ident()
    seen = {}

    def handler(params):
        seen["thread"] = threading.get_ident()
        return {"echo": params.get("v")}

    server = BridgeServer(
        dispatcher=dispatcher,
        live_info_provider=fake_live_info,
        preferred_port=0,
        port_range=range(0, 1),
        handlers={"custom.echo": handler},
    )
    port = server.bind()
    server.start()
    client = BridgeClient(host="127.0.0.1", port=port, timeout=2.0)
    out = {}
    try:
        client.connect()
        t = threading.Thread(target=lambda: out.update(client.send_request("custom.echo", {"v": 7})))
        t.start()
        while t.is_alive():
            dispatcher.pump()
            t.join(0.02)
        assert out == {"echo": 7}
        assert seen["thread"] == main_thread
    finally:
        client.close()
        server.stop()


def test_command_error_from_handler_keeps_its_code() -> None:
    import threading

    from mcp_server.abletonbridge_mcp.client import BridgeCommandError
    from remote_script.AbletonBridge import errors

    dispatcher = UIDispatcher()

    def handler(params):
        raise errors.CommandError(errors.TRACK_NOT_FOUND, "no track 9")

    server = BridgeServer(
        dispatcher=dispatcher, live_info_provider=fake_live_info,
        preferred_port=0, port_range=range(0, 1), handlers={"x.fail": handler},
    )
    port = server.bind()
    server.start()
    client = BridgeClient(host="127.0.0.1", port=port, timeout=2.0)
    caught = {}

    def call():
        try:
            client.send_request("x.fail", {})
        except BridgeCommandError as exc:
            caught["code"], caught["msg"] = exc.code, exc.message

    try:
        client.connect()
        t = threading.Thread(target=call)
        t.start()
        while t.is_alive():
            dispatcher.pump()
            t.join(0.02)
        assert caught == {"code": "TRACK_NOT_FOUND", "msg": "no track 9"}
    finally:
        client.close()
        server.stop()


# --- T-022: el loop de accept sobrevive a fallos de una conexion ---------
# Inyeccion de fallos con sockets falsos: determinista, sin carreras de
# timing. Reproduce lo visto en el log real de Live 12.4.16 (WinError 10053).

import threading

PING_LINE = b'{"id":"1","cmd":"ping","params":{}}\n'


class _FakeConn:
    """Conexion falsa: entrega `incoming` y puede fallar en recv/sendall."""

    def __init__(self, incoming=b"", recv_exc=None, send_exc=None) -> None:
        self._incoming = incoming
        self._recv_exc = recv_exc
        self._send_exc = send_exc
        self.sent = b""
        self.closed = threading.Event()

    def settimeout(self, _t) -> None:
        pass

    def recv(self, _n):
        if self._recv_exc is not None:
            raise self._recv_exc
        data, self._incoming = self._incoming, b""
        return data  # b"" = el cliente cerro

    def sendall(self, data) -> None:
        if self._send_exc is not None:
            raise self._send_exc
        self.sent += data

    def close(self) -> None:
        self.closed.set()


class _FakeListener:
    """Socket de escucha falso: entrega las conexiones en orden y luego timeout."""

    def __init__(self, conns) -> None:
        self._conns = list(conns)

    def settimeout(self, _t) -> None:
        pass

    def accept(self):
        import socket as socket_module

        if self._conns:
            return self._conns.pop(0), ("127.0.0.1", 0)
        raise socket_module.timeout()

    def close(self) -> None:
        pass


def _serve_with(conns):
    server = BridgeServer(dispatcher=UIDispatcher(), live_info_provider=fake_live_info)
    server._sock = _FakeListener(conns)
    thread = threading.Thread(target=server._serve_forever, daemon=True)
    thread.start()
    return server, thread


def _assert_second_client_served(bad_conn) -> None:
    good = _FakeConn(incoming=PING_LINE)
    server, thread = _serve_with([bad_conn, good])
    try:
        assert good.closed.wait(timeout=3.0), "el segundo cliente no fue atendido"
        assert b'"pong":true' in good.sent.replace(b" ", b"")
        assert thread.is_alive(), "el loop de accept murio"
    finally:
        server.stop()


def test_sendall_connection_aborted_10053_does_not_kill_accept_loop() -> None:
    """WinError 10053 (ConnectionAbortedError) en sendall: el cliente se fue a mitad de respuesta."""
    bad = _FakeConn(
        incoming=PING_LINE,
        send_exc=ConnectionAbortedError(10053, "software caused connection abort"),
    )
    _assert_second_client_served(bad)
    assert bad.closed.is_set()


def test_recv_connection_reset_10054_does_not_kill_accept_loop() -> None:
    """WinError 10054 (ConnectionResetError) en recv: el peer reseteo la conexion."""
    bad = _FakeConn(recv_exc=ConnectionResetError(10054, "forcibly closed by remote host"))
    _assert_second_client_served(bad)
    assert bad.closed.is_set()


def test_unexpected_exception_in_connection_does_not_kill_accept_loop() -> None:
    """Una excepcion NO-OSError (p.ej. UnicodeDecodeError por bytes basura) no tumba el loop."""
    bad = _FakeConn(incoming=b"\xff\xfe\n")
    _assert_second_client_served(bad)
    assert bad.closed.is_set()


def test_after_response_still_runs_after_each_response() -> None:
    """T-011: `after_response` se sigue corriendo tras la respuesta (bridge.reload)."""
    good = _FakeConn(incoming=PING_LINE)
    server = BridgeServer(dispatcher=UIDispatcher(), live_info_provider=fake_live_info)
    ran = threading.Event()
    server.after_response(ran.set)
    server._sock = _FakeListener([good])
    thread = threading.Thread(target=server._serve_forever, daemon=True)
    thread.start()
    try:
        assert ran.wait(timeout=3.0)
        assert b"pong" in good.sent
    finally:
        server.stop()
