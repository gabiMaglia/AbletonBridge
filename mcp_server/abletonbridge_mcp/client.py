"""
BridgeClient — cliente TCP del servidor MCP hacia el Remote Script.

Contrato (engram/04_api_contracts.md SS A):
- El servidor MCP es el CLIENTE; el Remote Script es el servidor.
- Correlacion por `id` (UUID v4) -- usamos un mapa id->resultado simple ya
  que esta implementacion es sincronica (una request en vuelo a la vez es
  suficiente para T-002; T-003+ puede paralelizar si el contrato lo permite).
- Timeout de request: 5s por defecto.
- Reconexion con backoff: 1s, 2s, 4s (max 4s) -- configurable para tests.
"""
import json
import socket
import time
import uuid
from typing import Any, Dict, Optional, Sequence

from . import protocol

DEFAULT_TIMEOUT = 5.0
DEFAULT_BACKOFF_SCHEDULE = (1.0, 2.0, 4.0)


class BridgeError(Exception):
    code = "BRIDGE_ERROR"


class BridgeTimeoutError(BridgeError):
    code = "BRIDGE_TIMEOUT"


class BridgeDisconnectedError(BridgeError):
    code = "BRIDGE_DISCONNECTED"


class BridgeCommandError(BridgeError):
    """Error de dominio devuelto por el Remote Script (ok=false)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class BridgeClient:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 19845,
        timeout: float = DEFAULT_TIMEOUT,
        backoff_schedule: Sequence[float] = DEFAULT_BACKOFF_SCHEDULE,
    ) -> None:
        self._host = host
        self._port = port
        self._timeout = timeout
        self._backoff_schedule = backoff_schedule
        self._sock: Optional[socket.socket] = None
        self._recv_buf = b""

    def connect(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self._timeout)
        sock.connect((self._host, self._port))
        self._sock = sock
        self._recv_buf = b""

    def connect_with_retry(self, max_attempts: int = 3) -> None:
        last_error: Optional[Exception] = None
        for attempt in range(max_attempts):
            try:
                self.connect()
                return
            except OSError as exc:
                last_error = exc
                if attempt < len(self._backoff_schedule):
                    time.sleep(self._backoff_schedule[attempt])
                else:
                    time.sleep(self._backoff_schedule[-1] if self._backoff_schedule else 1.0)
        raise BridgeDisconnectedError(
            f"could not connect to {self._host}:{self._port} after {max_attempts} attempts"
        ) from last_error

    def close(self) -> None:
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def send_request(self, cmd: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envia un comando y espera su response correlacionada por id.
        Lanza BridgeDisconnectedError, BridgeTimeoutError o BridgeCommandError.
        """
        if self._sock is None:
            raise BridgeDisconnectedError("not connected to remote script")

        request_id = str(uuid.uuid4())
        line = protocol.encode_request(request_id, cmd, params)

        try:
            self._sock.sendall(line.encode("utf-8"))
        except OSError as exc:
            raise BridgeDisconnectedError(str(exc)) from exc

        deadline = time.monotonic() + self._timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise BridgeTimeoutError(f"timed out waiting for response to {cmd!r}")

            resp = self._try_read_response(request_id, remaining)
            if resp is not None:
                return resp

    def _try_read_response(self, request_id: str, timeout: float) -> Optional[Dict[str, Any]]:
        assert self._sock is not None
        self._sock.settimeout(timeout)

        while b"\n" not in self._recv_buf:
            try:
                chunk = self._sock.recv(4096)
            except socket.timeout:
                raise BridgeTimeoutError(f"timed out waiting for response to id={request_id}")
            except OSError as exc:
                raise BridgeDisconnectedError(str(exc)) from exc
            if not chunk:
                raise BridgeDisconnectedError("connection closed by remote script")
            self._recv_buf += chunk

        line, self._recv_buf = self._recv_buf.split(b"\n", 1)
        response = protocol.decode_response(line.decode("utf-8") + "\n")

        if response.id != request_id:
            # Fuera de orden: en T-002 no esperamos pipelining real, pero el
            # contrato lo permite. Descartamos y seguimos esperando la nuestra.
            return None

        if not response.ok:
            error = response.error or {}
            raise BridgeCommandError(
                error.get("code", "LOM_ERROR"), error.get("message", "unknown error")
            )

        return response.result or {}

    def ping(self) -> Dict[str, Any]:
        return self.send_request("ping", {})
