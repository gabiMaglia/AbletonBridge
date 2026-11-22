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


# --- Produccion v1 (T-003) ---


def _compact(**kw: Any) -> Dict[str, Any]:
    """Params sin los None (los opcionales no enviados no deben pisar nada)."""
    return {k: v for k, v in kw.items() if v is not None}


def live_song_set(
    client: BridgeClient,
    tempo: Optional[float] = None,
    signature_numerator: Optional[int] = None,
    signature_denominator: Optional[int] = None,
    loop_start: Optional[float] = None,
    loop_length: Optional[float] = None,
    loop_on: Optional[bool] = None,
) -> Dict[str, Any]:
    return client.send_request("song.set", _compact(
        tempo=tempo, signature_numerator=signature_numerator,
        signature_denominator=signature_denominator, loop_start=loop_start,
        loop_length=loop_length, loop_on=loop_on))


def live_track_create(client: BridgeClient, kind: str, name: str, index: int = -1) -> Dict[str, Any]:
    return client.send_request("track.create", {"kind": kind, "name": name, "index": index})


def live_track_set_mixer(
    client: BridgeClient,
    track: int,
    volume_db: Any = None,
    pan: Optional[float] = None,
    mute: Optional[bool] = None,
    solo: Optional[bool] = None,
) -> Dict[str, Any]:
    return client.send_request("track.set_mixer", _compact(
        track=track, volume_db=volume_db, pan=pan, mute=mute, solo=solo))


def live_track_delete(client: BridgeClient, track: int, confirm_name: str) -> Dict[str, Any]:
    return client.send_request("track.delete", {"track": track, "confirm_name": confirm_name})


def live_clip_place_audio(
    client: BridgeClient,
    track: int,
    path: str,
    start_beat: float,
    length_beats: float,
    warp_mode: Optional[int] = None,
    pitch_coarse: Optional[int] = None,
    gain_db: Optional[float] = None,
    loop_start: Optional[float] = None,
    loop_end: Optional[float] = None,
) -> Dict[str, Any]:
    return client.send_request("clip.place_audio", _compact(
        track=track, path=path, start_beat=start_beat, length_beats=length_beats,
        warp_mode=warp_mode, pitch_coarse=pitch_coarse, gain_db=gain_db,
        loop_start=loop_start, loop_end=loop_end))


def live_clip_create_midi(
    client: BridgeClient,
    track: int,
    start_beat: float,
    length_beats: float,
    notes: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return client.send_request("clip.create_midi", {
        "track": track, "start_beat": start_beat, "length_beats": length_beats, "notes": notes})


def live_device_insert(client: BridgeClient, track: int, name: str, index: int = -1) -> Dict[str, Any]:
    return client.send_request("device.insert", {"track": track, "name": name, "index": index})


def live_device_set_param(
    client: BridgeClient, track: int, device: Any, name: str, value: float
) -> Dict[str, Any]:
    return client.send_request("device.set_param", {
        "track": track, "device": device, "name": name, "value": value})


def live_simpler_load(
    client: BridgeClient, track: int, device: Any, path: str, playback_mode: Optional[int] = None
) -> Dict[str, Any]:
    return client.send_request("simpler.load", _compact(
        track=track, device=device, path=path, playback_mode=playback_mode))


# --- Sends y returns (T-009) ---


def live_track_set_send(client: BridgeClient, track: int, send: int, db: Any) -> Dict[str, Any]:
    return client.send_request("track.set_send", {"track": track, "send": send, "db": db})


def live_return_list(client: BridgeClient) -> Dict[str, Any]:
    return client.send_request("return.list", {})


def live_return_set_mixer(
    client: BridgeClient,
    return_: int,
    volume_db: Any = None,
    pan: Optional[float] = None,
    mute: Optional[bool] = None,
) -> Dict[str, Any]:
    return client.send_request("return.set_mixer", _compact(
        **{"return": return_}, volume_db=volume_db, pan=pan, mute=mute))


def live_return_device_insert(client: BridgeClient, return_: int, name: str, index: int = -1) -> Dict[str, Any]:
    return client.send_request("return.device_insert", {"return": return_, "name": name, "index": index})


def live_return_device_set_param(
    client: BridgeClient, return_: int, device: Any, name: str, value: float
) -> Dict[str, Any]:
    return client.send_request("return.device_set_param", {
        "return": return_, "device": device, "name": name, "value": value})


def live_return_create(client: BridgeClient, name: Optional[str] = None) -> Dict[str, Any]:
    return client.send_request("return.create", _compact(name=name))


def live_locator_set(client: BridgeClient, time: float, name: str) -> Dict[str, Any]:
    """Encola UN locator (asincrono); ver live_locator_status."""
    return client.send_request("locator.set", {"time": time, "name": name})


def live_locator_set_many(client: BridgeClient, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Encola locators [{time, name}]; se procesan en orden, uno por tick de Live."""
    return client.send_request("locator.set_many", {"items": items})


def live_locator_status(client: BridgeClient) -> Dict[str, Any]:
    return client.send_request("locator.status", {})


def live_locator_clear_all(client: BridgeClient) -> Dict[str, Any]:
    return client.send_request("locator.clear_all", {})


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
