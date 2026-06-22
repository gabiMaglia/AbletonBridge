"""
Catalogo de codigos de error del protocolo del puente.
Ver engram/04_api_contracts.md SS A ("Codigos de error (catalogo base)").

Stdlib pura: este modulo corre en el interprete embebido de Live.
"""

# Errores resueltos por el servidor MCP (cliente).
BRIDGE_TIMEOUT = "BRIDGE_TIMEOUT"
BRIDGE_DISCONNECTED = "BRIDGE_DISCONNECTED"

# Errores resueltos por el Remote Script (servidor).
BAD_REQUEST = "BAD_REQUEST"
UNKNOWN_CMD = "UNKNOWN_CMD"
INVALID_PARAMS = "INVALID_PARAMS"
TRACK_NOT_FOUND = "TRACK_NOT_FOUND"
CLIP_SLOT_NOT_FOUND = "CLIP_SLOT_NOT_FOUND"
CLIP_NOT_FOUND = "CLIP_NOT_FOUND"
SLOT_OCCUPIED = "SLOT_OCCUPIED"
NOT_MIDI_TRACK = "NOT_MIDI_TRACK"
LOM_ERROR = "LOM_ERROR"

ALL_CODES = frozenset(
    {
        BRIDGE_TIMEOUT,
        BRIDGE_DISCONNECTED,
        BAD_REQUEST,
        UNKNOWN_CMD,
        INVALID_PARAMS,
        TRACK_NOT_FOUND,
        CLIP_SLOT_NOT_FOUND,
        CLIP_NOT_FOUND,
        SLOT_OCCUPIED,
        NOT_MIDI_TRACK,
        LOM_ERROR,
    }
)
