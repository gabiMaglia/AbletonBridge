"""
Tests del framing newline-delimited JSON usado en el socket TCP local
(MCP <-> Remote Script), según engram/04_api_contracts.md SS A.

Cubre SOLO lo testeable sin Ableton: encode/decode de envelopes,
validacion de campos requeridos y catalogo de errores.
"""
import json

import pytest

from remote_script.AbletonBridge import errors, protocol


class TestEncodeFraming:
    def test_encode_response_ok_ends_with_newline(self) -> None:
        raw = protocol.encode_response(request_id="abc-123", result={"pong": True})
        assert raw.endswith("\n")
        assert raw.count("\n") == 1

    def test_encode_response_ok_is_valid_single_line_json(self) -> None:
        raw = protocol.encode_response(request_id="abc-123", result={"pong": True})
        payload = json.loads(raw.strip())
        assert payload == {"id": "abc-123", "ok": True, "result": {"pong": True}}

    def test_encode_response_error_shape(self) -> None:
        raw = protocol.encode_error_response(
            request_id="abc-123",
            code=errors.BAD_REQUEST,
            message="missing cmd",
        )
        payload = json.loads(raw.strip())
        assert payload == {
            "id": "abc-123",
            "ok": False,
            "error": {"code": "BAD_REQUEST", "message": "missing cmd"},
        }

    def test_encode_response_rejects_internal_newlines_in_result(self) -> None:
        # JSON compacto: json.dumps no inserta \n internos por default,
        # pero validamos explicitamente que el framing nunca se rompe.
        raw = protocol.encode_response(request_id="x", result={"text": "line1\nline2"})
        assert raw.count("\n") == 1
        assert raw.endswith("\n")


class TestDecodeFraming:
    def test_decode_valid_request(self) -> None:
        line = '{"id": "uuid-1", "cmd": "ping", "params": {}}\n'
        req = protocol.decode_request(line)
        assert req.id == "uuid-1"
        assert req.cmd == "ping"
        assert req.params == {}

    def test_decode_request_strips_trailing_newline(self) -> None:
        line = '{"id": "uuid-1", "cmd": "ping", "params": {}}\n'
        req = protocol.decode_request(line)
        assert req.cmd == "ping"

    def test_decode_invalid_json_raises_protocol_error(self) -> None:
        with pytest.raises(protocol.ProtocolError) as exc_info:
            protocol.decode_request("not json at all\n")
        assert exc_info.value.code == errors.BAD_REQUEST

    def test_decode_missing_id_raises_bad_request(self) -> None:
        line = '{"cmd": "ping", "params": {}}\n'
        with pytest.raises(protocol.ProtocolError) as exc_info:
            protocol.decode_request(line)
        assert exc_info.value.code == errors.BAD_REQUEST

    def test_decode_missing_cmd_raises_bad_request(self) -> None:
        line = '{"id": "uuid-1", "params": {}}\n'
        with pytest.raises(protocol.ProtocolError) as exc_info:
            protocol.decode_request(line)
        assert exc_info.value.code == errors.BAD_REQUEST

    def test_decode_missing_params_raises_bad_request(self) -> None:
        line = '{"id": "uuid-1", "cmd": "ping"}\n'
        with pytest.raises(protocol.ProtocolError) as exc_info:
            protocol.decode_request(line)
        assert exc_info.value.code == errors.BAD_REQUEST

    def test_decode_params_must_be_object(self) -> None:
        line = '{"id": "uuid-1", "cmd": "ping", "params": [1, 2]}\n'
        with pytest.raises(protocol.ProtocolError) as exc_info:
            protocol.decode_request(line)
        assert exc_info.value.code == errors.BAD_REQUEST

    def test_decode_blank_line_raises_bad_request(self) -> None:
        with pytest.raises(protocol.ProtocolError) as exc_info:
            protocol.decode_request("\n")
        assert exc_info.value.code == errors.BAD_REQUEST


class TestLineSplitting:
    def test_iter_lines_splits_buffer_on_newline(self) -> None:
        buf = b'{"id":"1","cmd":"ping","params":{}}\n{"id":"2","cmd":"ping","params":{}}\n'
        lines, remainder = protocol.split_buffered_lines(buf)
        assert len(lines) == 2
        assert remainder == b""

    def test_iter_lines_keeps_partial_trailing_line_as_remainder(self) -> None:
        buf = b'{"id":"1","cmd":"ping","params":{}}\n{"id":"2","cmd":"pi'
        lines, remainder = protocol.split_buffered_lines(buf)
        assert len(lines) == 1
        assert remainder == b'{"id":"2","cmd":"pi'
