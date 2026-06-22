"""Framing newline-JSON del lado cliente (servidor MCP)."""
import json

import pytest

from mcp_server.abletonbridge_mcp import protocol


def test_encode_request_includes_id_cmd_params() -> None:
    raw = protocol.encode_request(request_id="uuid-1", cmd="ping", params={})
    assert raw.endswith("\n")
    payload = json.loads(raw.strip())
    assert payload == {"id": "uuid-1", "cmd": "ping", "params": {}}


def test_decode_response_ok() -> None:
    line = '{"id": "uuid-1", "ok": true, "result": {"pong": true}}\n'
    resp = protocol.decode_response(line)
    assert resp.id == "uuid-1"
    assert resp.ok is True
    assert resp.result == {"pong": True}
    assert resp.error is None


def test_decode_response_error() -> None:
    line = (
        '{"id": "uuid-1", "ok": false, '
        '"error": {"code": "BRIDGE_TIMEOUT", "message": "no reply"}}\n'
    )
    resp = protocol.decode_response(line)
    assert resp.ok is False
    assert resp.error == {"code": "BRIDGE_TIMEOUT", "message": "no reply"}
    assert resp.result is None


def test_decode_response_invalid_json_raises() -> None:
    with pytest.raises(protocol.ProtocolError):
        protocol.decode_response("garbage\n")


def test_decode_response_missing_id_raises() -> None:
    with pytest.raises(protocol.ProtocolError):
        protocol.decode_response('{"ok": true, "result": {}}\n')
