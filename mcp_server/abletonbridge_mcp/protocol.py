"""
Framing newline-delimited JSON del lado servidor MCP (cliente del socket).
Ver engram/04_api_contracts.md SS A.

Nota de diseno: este modulo NO se importa desde `remote_script/`, y
viceversa. El Remote Script corre en el interprete embebido de Live
(stdlib pura, sin pip) y el servidor MCP es un proceso normal con su
propio venv -- mantenerlos como paquetes independientes evita cualquier
import cruzado accidental que rompa esa restriccion (ver ADR-001).
"""
import json
from typing import Any, Dict, NamedTuple, Optional


class ProtocolError(Exception):
    pass


def encode_request(request_id: str, cmd: str, params: Dict[str, Any]) -> str:
    envelope = {"id": request_id, "cmd": cmd, "params": params}
    return json.dumps(envelope, separators=(",", ":")) + "\n"


class Response(NamedTuple):
    id: str
    ok: bool
    result: Optional[Dict[str, Any]]
    error: Optional[Dict[str, Any]]


def decode_response(line: str) -> Response:
    stripped = line.strip()
    if not stripped:
        raise ProtocolError("empty line")

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise ProtocolError(f"invalid json: {exc}") from exc

    if not isinstance(payload, dict) or "id" not in payload or "ok" not in payload:
        raise ProtocolError("envelope missing required fields (id, ok)")

    return Response(
        id=payload["id"],
        ok=bool(payload["ok"]),
        result=payload.get("result"),
        error=payload.get("error"),
    )
