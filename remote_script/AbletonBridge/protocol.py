"""
Framing newline-delimited JSON del lado Remote Script (servidor).
Ver engram/04_api_contracts.md SS A.

Stdlib pura (json) — corre en el interprete embebido de Live.
"""
import json
from typing import Any, Dict, List, NamedTuple, Tuple

from . import errors


class ProtocolError(Exception):
    """Error de framing/parsing del envelope. Mapea 1:1 a un codigo del catalogo."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class Request(NamedTuple):
    id: str
    cmd: str
    params: Dict[str, Any]


def decode_request(line: str) -> Request:
    """Decodea una linea newline-JSON en un Request. Lanza ProtocolError si es invalida."""
    stripped = line.strip()
    if not stripped:
        raise ProtocolError(errors.BAD_REQUEST, "empty line")

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise ProtocolError(errors.BAD_REQUEST, f"invalid json: {exc}") from exc

    if not isinstance(payload, dict):
        raise ProtocolError(errors.BAD_REQUEST, "envelope must be a JSON object")

    if "id" not in payload or not isinstance(payload["id"], str):
        raise ProtocolError(errors.BAD_REQUEST, "missing or invalid 'id'")

    if "cmd" not in payload or not isinstance(payload["cmd"], str):
        raise ProtocolError(errors.BAD_REQUEST, "missing or invalid 'cmd'")

    if "params" not in payload or not isinstance(payload["params"], dict):
        raise ProtocolError(errors.BAD_REQUEST, "missing or invalid 'params'")

    return Request(id=payload["id"], cmd=payload["cmd"], params=payload["params"])


def encode_response(request_id: str, result: Dict[str, Any]) -> str:
    """Codifica una response exitosa como una linea newline-JSON."""
    envelope = {"id": request_id, "ok": True, "result": result}
    return json.dumps(envelope, separators=(",", ":")) + "\n"


def encode_error_response(request_id: str, code: str, message: str) -> str:
    """Codifica una response de error como una linea newline-JSON."""
    envelope = {"id": request_id, "ok": False, "error": {"code": code, "message": message}}
    return json.dumps(envelope, separators=(",", ":")) + "\n"


def split_buffered_lines(buf: bytes) -> Tuple[List[bytes], bytes]:
    """
    Divide un buffer de bytes recibido del socket en lineas completas
    (terminadas en \\n) y el remanente sin terminar (linea parcial).
    """
    if b"\n" not in buf:
        return [], buf
    *complete, remainder = buf.split(b"\n")
    return complete, remainder
