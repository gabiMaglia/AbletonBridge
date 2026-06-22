"""
AbletonBridge — Remote Script base (T-002).

IMPORTANTE: este paquete corre dentro del interprete embebido de Ableton
Live. SOLO puede usar la stdlib de Python (socket, json, threading, etc.)
segun ADR-001 / engram/02_architecture.md. No agregar dependencias de
terceros aca.

Live carga el Remote Script buscando una clase de Control Surface en este
modulo. La integracion real con `Live.Application`/ControlSurface se
completa en T-003+ (no testeable sin Ableton instalado). Por ahora este
paquete expone:

- protocol: framing newline-JSON (envelope request/response).
- errors: catalogo de codigos de error del contrato.
- dispatcher: cola thread-safe hacia el hilo de UI de Live.
- server: TCP server (thread aparte) que parsea envelopes y responde.

Ver engram/04_api_contracts.md SS A para el contrato completo.
"""

from . import dispatcher, errors, protocol, server  # noqa: F401
