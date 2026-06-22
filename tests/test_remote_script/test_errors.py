"""Catalogo de codigos de error (engram/04_api_contracts.md SS A)."""
from remote_script.AbletonBridge import errors


def test_catalog_contains_all_contract_codes() -> None:
    expected = {
        "BRIDGE_TIMEOUT",
        "BRIDGE_DISCONNECTED",
        "BAD_REQUEST",
        "UNKNOWN_CMD",
        "INVALID_PARAMS",
        "TRACK_NOT_FOUND",
        "CLIP_SLOT_NOT_FOUND",
        "CLIP_NOT_FOUND",
        "SLOT_OCCUPIED",
        "NOT_MIDI_TRACK",
        "LOM_ERROR",
    }
    assert expected.issubset(errors.ALL_CODES)


def test_constants_match_their_string_value() -> None:
    assert errors.BAD_REQUEST == "BAD_REQUEST"
    assert errors.UNKNOWN_CMD == "UNKNOWN_CMD"
    assert errors.LOM_ERROR == "LOM_ERROR"
