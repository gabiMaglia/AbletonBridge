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
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

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


# Tope de caracteres antes de volcar a archivo (los resultados MCP se cortan ~25k tokens).
STATE_DETAIL_MAX_CHARS = 60_000
STATE_DETAIL_CACHE = Path(__file__).resolve().parents[2] / ".cache" / "state_detail"


def _state_detail_summary(result: Dict[str, Any]) -> Dict[str, Any]:
    def names(devices: Any) -> Any:
        if not isinstance(devices, list):
            return devices
        return [d.get("name") if isinstance(d, dict) else d for d in devices]

    def row(t: Any) -> Any:
        if not isinstance(t, dict):
            return t
        return {"index": t.get("index"), "name": t.get("name"),
                "kind": t.get("kind"), "devices": names(t.get("devices"))}

    tracks = result.get("tracks")
    returns = result.get("returns")
    master = result.get("master")
    return {
        "tracks": [row(t) for t in tracks] if isinstance(tracks, list) else tracks,
        "returns": [row(t) for t in returns] if isinstance(returns, list) else returns,
        "master_devices": names(master.get("devices")) if isinstance(master, dict) else master,
    }


def live_get_state_detail(
    client: BridgeClient,
    tracks: Optional[List[int]] = None,
    params: str = "changed",
    include_arrangement: bool = True,
    include_session: bool = True,
    cache_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Lectura completa y de SOLO LECTURA del set (T-008). Ver contrato `state.detail`.
    Si el JSON supera STATE_DETAIL_MAX_CHARS se vuelca a `.cache/state_detail/` y se
    devuelve {truncated, file, summary}.
    """
    request: Dict[str, Any] = {
        "params": params,
        "include_arrangement": include_arrangement,
        "include_session": include_session,
    }
    if tracks is not None:
        request["tracks"] = tracks
    result = client.send_request("state.detail", request)
    text = json.dumps(result, ensure_ascii=False)
    if len(text) <= STATE_DETAIL_MAX_CHARS:
        return result
    target = Path(cache_dir) if cache_dir is not None else STATE_DETAIL_CACHE
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"state_detail_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns() % 1_000_000:06d}.json"
    path.write_text(text, encoding="utf-8")
    return {"truncated": True, "file": str(path.resolve()), "summary": _state_detail_summary(result)}


def live_probe_api(client: BridgeClient) -> Dict[str, Any]:
    """Diagnostico: que miembros del LOM existen en la version de Live conectada."""
    return client.send_request("probe.api", {})


# --- Spikes temporales T-002c (automatizacion en Arrangement) ---


def live_spike_automation_session(client: BridgeClient, bars: int = 4) -> Dict[str, Any]:
    return client.send_request("spike.automation_session", {"bars": bars})


def live_spike_automation_record_start(
    client: BridgeClient, start_beat: float = 32.0, bars: int = 2, arm: bool = True
) -> Dict[str, Any]:
    return client.send_request(
        "spike.automation_record_start", {"start_beat": start_beat, "bars": bars, "arm": arm}
    )


def live_spike_automation_record_status(client: BridgeClient) -> Dict[str, Any]:
    return client.send_request("spike.automation_record_status", {})


def live_spike_cleanup(client: BridgeClient) -> Dict[str, Any]:
    return client.send_request("spike.cleanup", {})


# --- Spikes temporales T-002d (ronda 2) ---


def live_spike_automation_arm(client: BridgeClient, enable: bool = True) -> Dict[str, Any]:
    return client.send_request("spike.automation_arm", {"enable": enable})


def live_spike_audio_clip(
    client: BridgeClient, path: str, position_beats: float = 0.0
) -> Dict[str, Any]:
    return client.send_request(
        "spike.audio_clip", {"path": path, "position_beats": position_beats}
    )


def live_spike_devices(client: BridgeClient) -> Dict[str, Any]:
    return client.send_request("spike.devices", {})


def live_spike_simpler_slice(
    client: BridgeClient, loop_path: str, oneshot_path: str
) -> Dict[str, Any]:
    return client.send_request(
        "spike.simpler_slice", {"loop_path": loop_path, "oneshot_path": oneshot_path}
    )
