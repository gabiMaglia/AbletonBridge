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
