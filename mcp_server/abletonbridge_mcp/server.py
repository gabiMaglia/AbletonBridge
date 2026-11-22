"""
Tools MCP base (T-002): handshake (`live_ping`) y snapshot de estado
(`live_get_state`), end-to-end contra el Remote Script via BridgeClient.

Convencion (engram/04_api_contracts.md SS B): la tool MCP valida params,
traduce a un `cmd` del socket, espera la response correlacionada y
devuelve `result` (o levanta el error correspondiente).

Las funciones aca son deliberadamente simples (reciben el `BridgeClient`
ya conectado) para que sean testeables sin levantar el framework MCP real.
El registro como tools del MCP SDK (decoradores @mcp.tool, etc.) se
conecta en un ticket posterior si el ticket lo requiere explicitamente;
T-002 solo exige UNA tool de prueba end-to-end funcionando contra el
bridge, que es lo que cubren estas funciones + sus tests.
"""
from typing import Any, Dict

from .client import BridgeClient


def live_ping(client: BridgeClient) -> Dict[str, Any]:
    """Tool de prueba E2E: handshake con el Remote Script."""
    return client.ping()


def live_get_state(client: BridgeClient, include_clips: bool = True) -> Dict[str, Any]:
    """
    F-005 (version minima de T-002): snapshot del set.
    Params: { include_clips: bool } -- ver engram/04_api_contracts.md SS B F-005.
    """
    return client.send_request("state.get", {"include_clips": include_clips})


def live_probe_api(client: BridgeClient) -> Dict[str, Any]:
    """Diagnostico: que miembros del LOM existen en la version de Live conectada."""
    return client.send_request("probe.api", {})


# --- Spikes temporales T-002c (automatizacion en Arrangement) ---


def live_spike_automation_session(client: BridgeClient, bars: int = 4) -> Dict[str, Any]:
    return client.send_request("spike.automation_session", {"bars": bars})


def live_spike_automation_record_start(
    client: BridgeClient, start_beat: float = 32.0, bars: int = 2
) -> Dict[str, Any]:
    return client.send_request(
        "spike.automation_record_start", {"start_beat": start_beat, "bars": bars}
    )


def live_spike_automation_record_status(client: BridgeClient) -> Dict[str, Any]:
    return client.send_request("spike.automation_record_status", {})


def live_spike_cleanup(client: BridgeClient) -> Dict[str, Any]:
    return client.send_request("spike.cleanup", {})
