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
from typing import Any, Callable, Dict, List, Optional

from .client import BridgeClient, BridgeError, BridgeTimeoutError


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
    start_beat: Optional[float],
    length_beats: Optional[float],
    warp_mode: Optional[int] = None,
    pitch_coarse: Optional[int] = None,
    gain_db: Optional[float] = None,
    loop_start: Optional[float] = None,
    loop_end: Optional[float] = None,
    one_shot: Optional[bool] = None,
    envelopes: Optional[List[Dict[str, Any]]] = None,
    points_span: Optional[str] = None,
    end_beat: Optional[float] = None,
) -> Dict[str, Any]:
    """
    envelopes: [{target, points}] se escriben en cada tile (ver contrato T-010).
    one_shot: duracion exacta del sample (warp markers forzados); usar start_beat O end_beat
    (end_beat = donde TERMINA, p.ej. un riser que cae en un downbeat).
    """
    return client.send_request("clip.place_audio", _compact(
        track=track, path=path, start_beat=start_beat, length_beats=length_beats,
        warp_mode=warp_mode, pitch_coarse=pitch_coarse, gain_db=gain_db,
        loop_start=loop_start, loop_end=loop_end, one_shot=one_shot,
        envelopes=envelopes, points_span=points_span, end_beat=end_beat))


def live_clip_delete_range(client: BridgeClient, track: int, start_beat: float, end_beat: float) -> Dict[str, Any]:
    return client.send_request("clip.delete_range", {
        "track": track, "start_beat": start_beat, "end_beat": end_beat})


def live_clip_create_midi(
    client: BridgeClient,
    track: int,
    start_beat: float,
    length_beats: float,
    notes: List[Dict[str, Any]],
    envelopes: Optional[List[Dict[str, Any]]] = None,
    points_span: Optional[str] = None,
) -> Dict[str, Any]:
    return client.send_request("clip.create_midi", _compact(
        track=track, start_beat=start_beat, length_beats=length_beats, notes=notes,
        envelopes=envelopes, points_span=points_span))


def live_device_insert(client: BridgeClient, track: int, name: str, index: int = -1) -> Dict[str, Any]:
    return client.send_request("device.insert", {"track": track, "name": name, "index": index})


def live_utility_ensure_last(
    client: BridgeClient, track: Any = None, return_: Optional[int] = None,
) -> Dict[str, Any]:
    """D-15: deja un Utility como ultimo device (track: indice | "master" | {"return": i}; o return_)."""
    return client.send_request("utility.ensure_last", _compact(track=track, **{"return": return_}))


def live_device_set_param(
    client: BridgeClient, track: int, device: Any, name: str,
    value: Optional[float] = None, display: Optional[float] = None,
) -> Dict[str, Any]:
    """`value` = crudo; `display` = numero en la unidad del parametro (Hz, dB, %). Uno de los dos."""
    return client.send_request("device.set_param", _compact(
        track=track, device=device, name=name, value=value, display=display))


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
    client: BridgeClient, return_: int, device: Any, name: str,
    value: Optional[float] = None, display: Optional[float] = None,
) -> Dict[str, Any]:
    return client.send_request("return.device_set_param", _compact(
        **{"return": return_}, device=device, name=name, value=value, display=display))


def live_return_create(client: BridgeClient, name: Optional[str] = None) -> Dict[str, Any]:
    return client.send_request("return.create", _compact(name=name))


# --- Master y sidechain (T-010) ---


def live_master_device_insert(client: BridgeClient, name: str, index: int = -1) -> Dict[str, Any]:
    return client.send_request("master.device_insert", {"name": name, "index": index})


def live_master_device_set_param(
    client: BridgeClient, device: Any, name: str,
    value: Optional[float] = None, display: Optional[float] = None,
) -> Dict[str, Any]:
    return client.send_request("master.device_set_param", _compact(
        device=device, name=name, value=value, display=display))


def live_master_set_mixer(client: BridgeClient, volume_db: Any) -> Dict[str, Any]:
    return client.send_request("master.set_mixer", {"volume_db": volume_db})


def live_compressor_set_sidechain(
    client: BridgeClient, track: int, device: Any, source_track_name: str
) -> Dict[str, Any]:
    return client.send_request("compressor.set_sidechain", {
        "track": track, "device": device, "source_track_name": source_track_name})


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


def live_bridge_version(client: BridgeClient) -> Dict[str, Any]:
    """T-011: {version, loaded_at (timestamp de carga de los modulos), reload_count, port}."""
    return client.send_request("bridge.version", {})


def live_bridge_stats(client: BridgeClient) -> Dict[str, Any]:
    """T-024: tiempos del dispatcher por comando (ultimos 10: wait_ms en cola, run_ms ejecutando; cancelled = vencidos sin correr) y timeouts vigentes."""
    return client.send_request("bridge.stats", {})


def live_bridge_reload(
    client: BridgeClient,
    timeout: float = 15.0,
    poll_interval: float = 0.5,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> Dict[str, Any]:
    """
    T-011: recarga los modulos del Remote Script sin reiniciar Live. Manda `bridge.reload` (responde
    antes de recargar) y reconecta sondeando `bridge.version` hasta que cambie `loaded_at`
    (o suba `reload_count`). Si no cambia en `timeout` s el reload fallo: ver el log de Live.
    """
    before = client.send_request("bridge.version", {})
    client.send_request("bridge.reload", {})
    started = clock()
    deadline = started + timeout
    after: Optional[Dict[str, Any]] = None
    while clock() < deadline:
        client.close()  # el servidor viejo cae al recargar; siempre se reconecta limpio
        sleep(poll_interval)
        try:
            client.connect()
            current = client.send_request("bridge.version", {})
        except (OSError, BridgeError):
            continue
        if (current.get("loaded_at") != before.get("loaded_at")
                or current.get("reload_count", 0) > before.get("reload_count", 0)):
            after = current
            break
    if after is None:
        try:
            client.close()
            client.connect()  # dejar el cliente usable
        except (OSError, BridgeError):
            pass
        raise BridgeTimeoutError(
            f"bridge did not report a new loaded_at within {timeout:g}s; the reload may have failed "
            "(syntax/import error), check Live's Log.txt"
        )
    return {"reloaded": True, "before": before, "after": after, "elapsed_s": round(clock() - started, 3)}


# --- T-012: automatizacion de pista grabada (lane real) ---

AUTOMATION_FINAL_PHASES = ("done", "error", "cancelled")
AUTOMATION_TIMEOUT_MARGIN_S = 20.0


def live_automation_record(
    client: BridgeClient,
    start_beat: float,
    end_beat: float,
    lanes: List[Dict[str, Any]],
    preroll_beats: float = 4.0,
    poll_interval: float = 1.0,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> Dict[str, Any]:
    """
    Graba `lanes` [{track, target, points:[[beat, valor]]}] como automatizacion REAL de pista
    (Automation Arm + record + transporte). Encola `automation.record` y sondea `automation.status`
    hasta done/error/cancelled; devuelve el status final. Tope: (fin-inicio+preroll) beats al tempo
    de Live + 20 s; si vence, cancela (restaura el set) y lanza BridgeTimeoutError.
    """
    if start_beat < 0 or end_beat <= start_beat:
        raise ValueError("need 0 <= start_beat < end_beat")
    if preroll_beats < 0:
        raise ValueError("preroll_beats must be >= 0")
    if not isinstance(lanes, list) or not lanes:
        raise ValueError("lanes must be a non-empty list")
    queued = client.send_request("automation.record", {
        "start_beat": start_beat, "end_beat": end_beat, "lanes": lanes, "preroll_beats": preroll_beats})
    tempo = float(queued.get("tempo") or 120.0)
    budget = (end_beat - start_beat + preroll_beats) * 60.0 / tempo + AUTOMATION_TIMEOUT_MARGIN_S
    deadline = clock() + budget
    while True:
        status = client.send_request("automation.status", {})
        if status.get("phase") in AUTOMATION_FINAL_PHASES:
            return status
        if clock() >= deadline:
            try:
                client.send_request("automation.cancel", {})
            except BridgeError:
                pass
            raise BridgeTimeoutError(
                f"automation recording did not finish within {budget:g}s (phase {status.get('phase')!r}); "
                "it was cancelled and the set restored"
            )
        sleep(poll_interval)


def live_automation_status(client: BridgeClient) -> Dict[str, Any]:
    return client.send_request("automation.status", {})


def live_automation_cancel(client: BridgeClient) -> Dict[str, Any]:
    return client.send_request("automation.cancel", {})


def live_automation_clear(
    client: BridgeClient, track: Any, target: Any,
    start_beat: Optional[float] = None, end_beat: Optional[float] = None,
) -> Dict[str, Any]:
    """Best-effort: si el LOM no puede borrar un lane responde supported:false."""
    return client.send_request("automation.clear", _compact(
        track=track, target=target, start_beat=start_beat, end_beat=end_beat))


# --- T-017: lectura de medidores (solo lectura, sin record ni Automation Arm) ---

METER_FINAL_PHASES = ("done", "error", "cancelled")


def live_meter_capture(
    client: BridgeClient,
    start_beat: float,
    end_beat: float,
    tracks: Any = "all",
    include_returns: bool = True,
    include_master: bool = True,
    bin_bars: int = 8,
    calibration: Optional[Dict[str, Any]] = None,
    preroll_beats: float = 2.0,
    poll_interval: float = 1.0,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> Dict[str, Any]:
    """
    Mide picos y nivel (medidores de salida del LOM) por pista/return/master mientras Live reproduce
    [start_beat, end_beat). Solo lectura. Devuelve por target: fader_display, peak/rms crudos y en dB
    (estimado: `db_mapping` dice si esta calibrado), bins por `bin_bars` compases y gain_reduction
    ("unavailable" si el LOM no lo expone). `calibration` = {points: [[raw, dbfs], ...]}.
    Encola `meter.capture` y sondea `meter.status`; al vencer el tope cancela y restaura el transporte.
    """
    if start_beat < 0 or end_beat <= start_beat:
        raise ValueError("need 0 <= start_beat < end_beat")
    if preroll_beats < 0:
        raise ValueError("preroll_beats must be >= 0")
    queued = client.send_request("meter.capture", _compact(
        start_beat=start_beat, end_beat=end_beat, tracks=tracks, include_returns=include_returns,
        include_master=include_master, bin_bars=bin_bars, calibration=calibration,
        preroll_beats=preroll_beats))
    tempo = float(queued.get("tempo") or 120.0)
    budget = (end_beat - start_beat + preroll_beats) * 60.0 / tempo + AUTOMATION_TIMEOUT_MARGIN_S
    deadline = clock() + budget
    while True:
        status = client.send_request("meter.status", {})
        if status.get("phase") in METER_FINAL_PHASES:
            return status
        if clock() >= deadline:
            try:
                client.send_request("meter.cancel", {})
            except BridgeError:
                pass
            raise BridgeTimeoutError(
                f"meter capture did not finish within {budget:g}s (phase {status.get('phase')!r}); "
                "it was cancelled and the transport restored"
            )
        sleep(poll_interval)


def live_meter_status(client: BridgeClient) -> Dict[str, Any]:
    """Estado/resultado parcial de la captura de medidores en curso (o la ultima)."""
    return client.send_request("meter.status", {})


def live_meter_cancel(client: BridgeClient) -> Dict[str, Any]:
    """Cancela la captura de medidores y restaura transporte y playhead."""
    return client.send_request("meter.cancel", {})


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
