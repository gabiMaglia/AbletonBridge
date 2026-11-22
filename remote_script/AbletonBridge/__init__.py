"""
AbletonBridge — Remote Script.

IMPORTANTE: este paquete corre dentro del interprete embebido de Ableton
Live. SOLO puede usar la stdlib de Python (socket, json, threading, etc.)
segun ADR-001 / engram/02_architecture.md.

Live carga el script llamando a `create_instance(c_instance)`, que debe
devolver una ControlSurface (ver surface.py).

- protocol / errors: framing newline-JSON y catalogo de errores.
- dispatcher: cola thread-safe hacia el hilo principal de Live.
- server: TCP server (thread aparte).
- handlers: comandos que tocan el LOM (ping/state.get/probe.api).
- surface: ControlSurface + pump del dispatcher.

Ver engram/04_api_contracts.md SS A para el contrato completo.
"""

from . import dispatcher, errors, handlers, protocol, server  # noqa: F401
from .surface import AbletonBridge


def create_instance(c_instance):
    """Entry point que Live invoca al seleccionar el Control Surface."""
    return AbletonBridge(c_instance)
