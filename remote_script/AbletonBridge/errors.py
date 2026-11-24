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
DISPATCH_TIMEOUT = "DISPATCH_TIMEOUT"

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
        DISPATCH_TIMEOUT,
    }
)


class CommandError(Exception):
    """Error de dominio de un handler: el servidor lo responde con este `code` (no LOM_ERROR)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
