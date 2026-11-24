"""
T-016: servidor MCP stdio. Envuelve los `live_*(client, ...)` de server.py como tools reales
sin tocar sus firmas (otro codigo los importa).

- Un unico BridgeClient compartido, conectado de forma perezosa (la primera tool que se llama
  conecta; Live puede abrirse despues de Claude Code) y reconectado en la llamada siguiente
  a una caida. Solo las lecturas de IDEMPOTENT_COMMANDS se reintentan (una vez); una escritura
  ya enviada jamas se repite: podria duplicar un efecto en el set (T-023).
- Todo error llega al modelo como ToolError ("CODE: mensaje"); cualquier otra excepcion del SDK
  se enmascara como "Error executing tool", asi que tampoco se deja pasar un RuntimeError.
- Resultados > MAX_RESULT_CHARS se vuelcan a `.cache/mcp_results/` y se devuelve un resumen
  (Claude Code corta las respuestas MCP en ~25k tokens).
- stdout es del protocolo: todo log va a stderr. EOF en stdin termina el proceso limpio.
"""
import inspect
import json
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from . import server as bridge_tools
from .client import (
    BridgeClient,
    BridgeCommandError,
    BridgeDisconnectedError,
    BridgeError,
    BridgeTimeoutError,
)

try:  # mcp >= 2
    from mcp.server.mcpserver import MCPServer as _ServerClass
    from mcp.server.mcpserver.exceptions import ToolError
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _ServerClass
    from mcp.server.fastmcp.exceptions import ToolError

MAX_RESULT_CHARS = 60_000
RESULT_CACHE = Path(__file__).resolve().parents[2] / ".cache" / "mcp_results"
PREVIEW_CHARS = 1_500
# Parametros de inyeccion/test de las funciones de server.py: no son parte del schema MCP.
HIDDEN_PARAMS = frozenset({"client", "sleep", "clock", "cache_dir"})
SPIKES_ENV = "NEXO_MCP_SPIKES"
# Lecturas sin efecto en el set: unicas que se reintentan solas tras una conexion caida.
IDEMPOTENT_COMMANDS = frozenset({
    "ping", "state.get", "state.detail", "bridge.version", "bridge.stats", "return.list",
    "locator.status", "automation.status", "meter.status",
})

INSTRUCTIONS = (
    "Puente a Ableton Live (Remote Script en 127.0.0.1:19845). Live debe estar abierto con el "
    "Remote Script cargado. Regla D-15: nunca automatizar el volumen de pista; Utility al final, "
    "param Output. Ver la skill nexo-ableton."
)

# Las funciones sin docstring en server.py reciben esta descripcion.
DESCRIPTIONS: Dict[str, str] = {
    "live_song_set": "Cambia tempo, compas y loop del set (solo los params enviados).",
    "live_track_create": "Crea una pista (kind: audio|midi) con nombre, en index (-1 = al final).",
    "live_track_set_mixer": "Setea volumen (dB), pan, mute y solo de una pista. No automatizar volumen (D-15).",
    "live_track_delete": "Borra una pista; exige confirm_name igual al nombre actual.",
    "live_clip_delete_range": "Borra los clips de Arrangement de una pista entre start_beat y end_beat.",
    "live_clip_create_midi": "Crea un clip MIDI en Arrangement con notas y envelopes opcionales.",
    "live_device_insert": "Inserta un device por nombre en una pista (index -1 = al final).",
    "live_simpler_load": "Carga un sample en un Simpler existente (playback_mode opcional).",
    "live_track_set_send": "Setea el nivel de un send de una pista, en dB.",
    "live_return_list": "Lista las pistas return con sus devices.",
    "live_return_set_mixer": "Setea volumen (dB), pan y mute de un return.",
    "live_return_device_insert": "Inserta un device por nombre en un return.",
    "live_return_device_set_param": "Setea un parametro de un device de un return (value crudo o display en su unidad).",
    "live_return_create": "Crea una pista return (nombre opcional).",
    "live_master_device_insert": "Inserta un device por nombre en la pista Master.",
    "live_master_device_set_param": "Setea un parametro de un device del Master (value crudo o display).",
    "live_master_set_mixer": "Setea el volumen del Master en dB.",
    "live_compressor_set_sidechain": "Rutea el sidechain de un Compressor a otra pista (por nombre).",
    "live_locator_status": "Estado de la cola asincrona de locators.",
    "live_locator_clear_all": "Borra todos los locators del set.",
    "live_automation_status": "Fase actual de la grabacion de automatizacion (idle/running/done/error/cancelled).",
    "live_automation_cancel": "Cancela la grabacion de automatizacion en curso y restaura el set.",
    "live_spike_automation_session": "SPIKE temporal T-002c: automatizacion en Session.",
    "live_spike_automation_record_start": "SPIKE temporal T-002c: inicia grabacion de automatizacion.",
    "live_spike_automation_record_status": "SPIKE temporal T-002c: estado de la grabacion.",
    "live_spike_cleanup": "SPIKE temporal T-002c: limpia lo creado por los spikes.",
    "live_spike_automation_arm": "SPIKE temporal T-002d: arma/desarma Automation Arm.",
    "live_spike_audio_clip": "SPIKE temporal T-002d: coloca un clip de audio de prueba.",
    "live_spike_devices": "SPIKE temporal T-002d: vuelca el catalogo de devices.",
    "live_spike_simpler_slice": "SPIKE temporal T-002d: prueba de slicing en Simpler.",
}


_MAY_HAVE_RUN = (
    "El comando {cmd} pudo haberse ejecutado en Live: relee el estado (live_get_state) antes de "
    "reintentar; reintentar a ciegas puede duplicar el efecto."
)


class _CallTracker:
    """Envuelve el cliente por llamada: recuerda que comandos salieron y marca el error con su cmd."""

    def __init__(self, client: Any) -> None:
        self._client = client
        self.commands: list = []

    def send_request(self, cmd: str, params: Dict[str, Any]) -> Any:
        self.commands.append(cmd)
        try:
            return self._client.send_request(cmd, params)
        except BridgeError as exc:
            if getattr(exc, "cmd", None) is None:
                exc.cmd = cmd  # type: ignore[attr-defined]
            raise

    def ping(self) -> Any:
        return self.send_request("ping", {})

    def all_idempotent(self) -> bool:
        return bool(self.commands) and all(c in IDEMPOTENT_COMMANDS for c in self.commands)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)


class BridgeRuntime:
    """Cliente compartido, conexion perezosa, errores normalizados y guard de tamano."""

    def __init__(
        self,
        client_factory: Optional[Callable[[], Any]] = None,
        cache_dir: Optional[Path] = None,
        max_chars: int = MAX_RESULT_CHARS,
    ) -> None:
        self._factory = client_factory or BridgeClient
        self._cache_dir = Path(cache_dir) if cache_dir is not None else RESULT_CACHE
        self._max_chars = max_chars
        self._client: Any = None
        self._ready = False
        self._lock = threading.RLock()

    def _ensure_client(self) -> Any:
        if self._client is None:
            self._client = self._factory()
        if not self._ready:
            self._client.connect_with_retry()
            self._ready = True
        return self._client

    def call(self, fn: Callable[..., Any], arguments: Dict[str, Any]) -> Any:
        with self._lock:
            try:
                result = self._run(fn, arguments)
            except ToolError:
                raise
            except Exception as exc:
                raise ToolError(self._describe(exc)) from exc
            return self._guard(result)

    def _run(self, fn: Callable[..., Any], arguments: Dict[str, Any]) -> Any:
        # Reintento unico: tras recrear Live la superficie, el primer request cae en el socket muerto.
        for attempt in (1, 2):
            tracker = _CallTracker(self._ensure_client())
            try:
                return fn(tracker, **arguments)
            except BridgeDisconnectedError as exc:
                self._drop()
                if attempt == 1 and tracker.all_idempotent():
                    continue
                raise
        raise AssertionError("unreachable")

    def _describe(self, exc: Exception) -> str:
        cmd = getattr(exc, "cmd", None)
        if isinstance(exc, BridgeCommandError):
            return f"{exc.code}: {exc.message}"
        if isinstance(exc, BridgeDisconnectedError):
            base = f"{exc.code}: {exc}."
            if cmd is None:
                return f"{base} Live abierto con el Remote Script cargado?"
            if cmd in IDEMPOTENT_COMMANDS:
                return f"{base} Se reintento una vez y fallo igual: Live abierto con el Remote Script cargado?"
            if not exc.after_send:
                return f"{base} El comando {cmd} no se envio a Live: es seguro reintentarlo."
            return f"{base} {_MAY_HAVE_RUN.format(cmd=cmd)}"
        if isinstance(exc, BridgeTimeoutError):
            base = f"{exc.code}: {exc}."
            if cmd is None or cmd in IDEMPOTENT_COMMANDS:
                return base
            return f"{base} {_MAY_HAVE_RUN.format(cmd=cmd)}"
        if isinstance(exc, BridgeError):
            return f"{exc.code}: {exc}"
        return f"{type(exc).__name__}: {exc}"

    def _drop(self) -> None:
        self._ready = False
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass

    def close(self) -> None:
        with self._lock:
            self._drop()

    def _guard(self, result: Any) -> Any:
        text = json.dumps(result, ensure_ascii=False, default=str)
        if len(text) <= self._max_chars:
            return result
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        path = self._cache_dir / f"result_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns() % 1_000_000:06d}.json"
        path.write_text(text, encoding="utf-8")
        return {
            "truncated": True,
            "file": str(path.resolve()),
            "chars": len(text),
            "top_level_keys": list(result.keys()) if isinstance(result, dict) else None,
            "preview": text[:PREVIEW_CHARS],
            "note": "Resultado demasiado grande para MCP: leer el archivo por partes.",
        }


def public_tool_functions(include_spikes: Optional[bool] = None) -> Dict[str, Callable[..., Any]]:
    if include_spikes is None:
        include_spikes = os.environ.get(SPIKES_ENV) == "1"
    funcs: Dict[str, Callable[..., Any]] = {}
    for name, fn in inspect.getmembers(bridge_tools, inspect.isfunction):
        if not name.startswith("live_") or fn.__module__ != bridge_tools.__name__:
            continue
        if name.startswith("live_spike_") and not include_spikes:
            continue
        funcs[name] = fn
    return funcs


def _wrap(runtime: BridgeRuntime, name: str, fn: Callable[..., Any]) -> Callable[..., Any]:
    original = inspect.signature(fn)
    params = [p for p in original.parameters.values() if p.name not in HIDDEN_PARAMS]
    sig = original.replace(parameters=params)

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        bound = sig.bind(*args, **kwargs)
        return runtime.call(fn, dict(bound.arguments))

    wrapper.__name__ = name
    wrapper.__qualname__ = name
    wrapper.__doc__ = inspect.getdoc(fn) or DESCRIPTIONS.get(name) or f"Comando del bridge ({name})."
    wrapper.__signature__ = sig  # type: ignore[attr-defined]
    wrapper.__annotations__ = {p.name: p.annotation for p in params if p.annotation is not p.empty}
    if sig.return_annotation is not sig.empty:
        wrapper.__annotations__["return"] = sig.return_annotation
    return wrapper


def build_tools(runtime: BridgeRuntime, include_spikes: Optional[bool] = None) -> Dict[str, Callable[..., Any]]:
    return {n: _wrap(runtime, n, f) for n, f in public_tool_functions(include_spikes).items()}


def build_server(
    client_factory: Optional[Callable[[], Any]] = None,
    runtime: Optional[BridgeRuntime] = None,
) -> Any:
    runtime = runtime or BridgeRuntime(client_factory=client_factory)
    srv = _ServerClass("nexo-ableton", instructions=INSTRUCTIONS)
    for name, tool in build_tools(runtime).items():
        srv.add_tool(tool, name=name)
    srv._bridge_runtime = runtime  # para el cierre en main()
    return srv


def main() -> int:
    srv = build_server()
    try:
        srv.run("stdio")
    except KeyboardInterrupt:
        pass
    finally:
        srv._bridge_runtime.close()
        sys.stderr.flush()
    return 0
