"""
BridgeServer — servidor TCP local del Remote Script.

Contrato (engram/04_api_contracts.md SS A):
- Bind SOLO a 127.0.0.1 (nunca 0.0.0.0).
- Puerto por defecto 19845, con fallback automatico en el rango 19845-19855
  si esta ocupado.
- Una conexion MCP a la vez.
- Framing newline-delimited JSON.
- `ping` responde { pong: true, live_version, api_level } sin pasar por el
  dispatcher (no toca el LOM).
- Cualquier comando que SI toque el LOM (transport.*, track.*, clip.*,
  state.get) debe ejecutarse via `UIDispatcher.run_blocking` -- nunca
  directamente en el thread del socket. T-002 solo implementa el
  mecanismo + el comando `ping`; T-003+ conectan los comandos reales al LOM.

Stdlib pura (socket, threading, json) -- corre en el interprete embebido
de Live.
"""
import json
import socket
import threading
from typing import Any, Callable, Dict, Optional

from . import errors, protocol
from .dispatcher import UIDispatcher

DEFAULT_PORT = 19845
FALLBACK_PORT_RANGE = range(19845, 19856)  # 19845..19855 inclusive


CommandHandler = Callable[[Dict[str, Any], UIDispatcher], Dict[str, Any]]


def handle_ping(params: Dict[str, Any], live_info: Dict[str, Any]) -> Dict[str, Any]:
    """Handler de `ping`. No toca el LOM: no requiere el dispatcher."""
    return {
        "pong": True,
        "live_version": live_info.get("live_version", "unknown"),
        "api_level": live_info.get("api_level", 0),
    }


class BridgeServer:
    """
    Servidor TCP que escucha en 127.0.0.1, acepta UNA conexion a la vez,
    parsea el envelope newline-JSON y despacha comandos.

    `live_info_provider` es un callable que devuelve {"live_version", "api_level"}
    -- en produccion lo provee la ControlSurface real; en tests, un stub.
    """

    def __init__(
        self,
        dispatcher: UIDispatcher,
        live_info_provider: Callable[[], Dict[str, Any]],
        host: str = "127.0.0.1",
        preferred_port: int = DEFAULT_PORT,
        port_range: range = FALLBACK_PORT_RANGE,
        handlers: Optional[Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]]] = None,
    ) -> None:
        self._handlers = handlers or {}
        self._dispatcher = dispatcher
        self._live_info_provider = live_info_provider
        self._host = host
        self._preferred_port = preferred_port
        self._port_range = port_range
        self._sock: Optional[socket.socket] = None
        self.port: Optional[int] = None
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def bind(self) -> int:
        """Intenta bindear en el puerto preferido, con fallback en el rango. Devuelve el puerto efectivo."""
        candidates = [self._preferred_port] + [
            p for p in self._port_range if p != self._preferred_port
        ]
        last_error: Optional[OSError] = None
        for port in candidates:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((self._host, port))
            except OSError as exc:
                last_error = exc
                sock.close()
                continue
            sock.listen(1)
            self._sock = sock
            self.port = sock.getsockname()[1]
            return self.port
        raise OSError(
            f"no free port available in range {self._port_range} (last error: {last_error})"
        )

    def start(self) -> None:
        """Arranca el thread del socket. Requiere haber llamado bind() antes."""
        if self._sock is None:
            self.bind()
        self._thread = threading.Thread(target=self._serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass

    def _serve_forever(self) -> None:
        assert self._sock is not None
        self._sock.settimeout(0.5)
        while not self._stop_event.is_set():
            try:
                conn, _addr = self._sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            self._handle_connection(conn)

    def _handle_connection(self, conn: socket.socket) -> None:
        conn.settimeout(0.5)
        buf = b""
        try:
            while not self._stop_event.is_set():
                try:
                    chunk = conn.recv(4096)
                except socket.timeout:
                    continue
                if not chunk:
                    break
                buf += chunk
                lines, buf = protocol.split_buffered_lines(buf)
                for raw_line in lines:
                    response = self._handle_line(raw_line.decode("utf-8"))
                    if response is not None:
                        conn.sendall(response.encode("utf-8"))
        finally:
            conn.close()

    def _handle_line(self, line: str) -> Optional[str]:
        try:
            request = protocol.decode_request(line)
        except protocol.ProtocolError as exc:
            # No tenemos un id valido si el parseo fallo antes de leerlo;
            # respondemos con id vacio segun mejor esfuerzo del contrato.
            return protocol.encode_error_response("", exc.code, exc.message)

        try:
            result = self._dispatch(request.cmd, request.params)
        except (_CommandError, errors.CommandError) as exc:
            return protocol.encode_error_response(request.id, exc.code, exc.message)
        except Exception as exc:  # noqa: BLE001
            return protocol.encode_error_response(request.id, errors.LOM_ERROR, str(exc))

        return protocol.encode_response(request.id, result)

    def _dispatch(self, cmd: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if cmd == "ping":
            return handle_ping(params, self._live_info_provider())
        handler = self._handlers.get(cmd)
        if handler is not None:
            # El LOM solo se toca en el hilo principal de Live.
            return self._dispatcher.run_blocking(lambda: handler(params))
        raise _CommandError(errors.UNKNOWN_CMD, f"unknown cmd: {cmd}")


class _CommandError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
