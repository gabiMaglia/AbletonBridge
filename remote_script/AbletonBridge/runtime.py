"""
BridgeRuntime — todo el estado intercambiable del bridge (T-011).

La ControlSurface (surface.py) pertenece a Live y no se puede recargar; esto si. Contiene el
servidor, el dispatcher, la tabla de handlers y las maquinas de estado de spikes/locators, de modo
que `bridge.reload` pueda descartar el objeto entero y construir otro con los modulos recargados.
"""
from typing import Any, Callable, Dict

from . import automation, dispatcher as dispatcher_mod, handlers, production, spikes, spikes_media, state_detail, version
from .dispatcher import UIDispatcher
from .server import BridgeServer

Handler = Callable[[Dict[str, Any]], Dict[str, Any]]


class BridgeRuntime:
    def __init__(self, host: Any, live: Any, live_info: Dict[str, Any],
                 preferred_port: int, port_range: range) -> None:
        self.host = host
        self._live = live
        self._live_info = live_info
        self.dispatcher = UIDispatcher()
        self.spikes = spikes.RecordSpike()
        self.locators = production.LocatorQueue()
        self.automation = automation.AutomationRecorder()
        self.meter = automation.MeterCapture()
        self.server = BridgeServer(
            dispatcher=self.dispatcher,
            live_info_provider=lambda: self._live_info,
            preferred_port=preferred_port,
            port_range=port_range,
            handlers=self._build_handlers(),
            log=self._log,
        )

    def _log(self, message: str) -> None:
        # El host es la ControlSurface: su log_message escribe en Log.txt de Live.
        self.host.log_message(message)

    def song(self) -> Any:
        return self.host.song()

    def start(self) -> int:
        port = self.server.bind()
        self.server.start()
        return port

    def stop(self) -> None:
        self.server.stop()

    def adopt(self, old: "BridgeRuntime") -> None:
        """Pasa los jobs que quedaron encolados en el dispatcher viejo (no se pierden en el reload)."""
        queue = getattr(old.dispatcher, "_queue", None)
        while queue is not None:
            try:
                job = queue.get_nowait()
            except Exception:  # noqa: BLE001 - queue.Empty u otra cosa: no hay mas
                break
            self.dispatcher.submit(job)

    def busy(self) -> bool:
        """True si hay una maquina de estados a mitad de camino (un reload la perderia)."""
        return (getattr(self.locators, "_phase", "idle") != "idle"
                or getattr(self.spikes, "phase", "idle") == "running"
                or self.automation.busy()
                or self.meter.busy())

    def tick(self) -> None:
        # Cada pieza aislada: una rota no frena el pump ni a las demas.
        log = self.host.log_message
        try:
            self.dispatcher.pump()
        except Exception as exc:  # noqa: BLE001
            log(f"AbletonBridge: tick error: {exc!r}")
        try:
            self.spikes.tick()
        except Exception as exc:  # noqa: BLE001
            log(f"AbletonBridge: spike tick error: {exc!r}")
        try:
            self.locators.tick(self.song())
        except Exception as exc:  # noqa: BLE001
            log(f"AbletonBridge: locator tick error: {exc!r}")
        try:
            self.automation.tick(self.song())
        except Exception as exc:  # noqa: BLE001
            log(f"AbletonBridge: automation tick error: {exc!r}")
        try:
            self.meter.tick(self.song())
        except Exception as exc:  # noqa: BLE001
            log(f"AbletonBridge: meter tick error: {exc!r}")

    # -- bridge.* --

    def _reload(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # La respuesta tiene que salir ANTES de recargar: el servidor corre el callback tras enviarla
        # y el reload en si ocurre en un tick posterior, en el hilo principal.
        self.server.after_response(self.host.request_reload)
        return {"reloading": True}

    def _version(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "version": version.VERSION,
            "loaded_at": version.LOADED_AT,
            "reload_count": getattr(self.host, "reload_count", 0),
            "port": self.server.port,
        }

    def _stats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "stats": self.dispatcher.stats(),
            "timeouts": {
                "read_s": dispatcher_mod.READ_TIMEOUT,
                "heavy_s": dispatcher_mod.HEAVY_TIMEOUT,
                "started_cap_s": dispatcher_mod.STARTED_CAP,
            },
        }

    def _exclusive(self, other: Any, label: str, fn: Callable[..., Dict[str, Any]],
                   params: Dict[str, Any]) -> Dict[str, Any]:
        """Automation y meter comparten el transporte: no pueden correr a la vez."""
        if other.busy():
            raise production._bad(f"a {label} is in progress; wait for it or cancel it first")
        return fn(self.song(), params)

    def _build_handlers(self) -> Dict[str, Handler]:
        song = self.song
        return {
            "bridge.reload": self._reload,
            "bridge.version": self._version,
            "bridge.stats": self._stats,
            "state.get": lambda params: handlers.get_state(song(), self._live_info, params),
            "state.detail": lambda params: state_detail.get_state_detail(song(), params),
            "song.set": lambda p: production.song_set(song(), p),
            "track.create": lambda p: production.track_create(song(), p),
            "track.set_mixer": lambda p: production.track_set_mixer(song(), p),
            "track.delete": lambda p: production.track_delete(song(), p),
            "track.set_send": lambda p: production.track_set_send(song(), p),
            "return.list": lambda p: production.return_list(song(), p),
            "return.set_mixer": lambda p: production.return_set_mixer(song(), p),
            "return.device_insert": lambda p: production.return_device_insert(song(), p),
            "return.device_set_param": lambda p: production.return_device_set_param(song(), p),
            "return.create": lambda p: production.return_create(song(), p),
            "clip.place_audio": lambda p: production.clip_place_audio(song(), p),
            "clip.delete_range": lambda p: production.clip_delete_range(song(), p),
            "clip.create_midi": lambda p: production.clip_create_midi(song(), self._live, p),
            "device.insert": lambda p: production.device_insert(song(), p),
            "device.set_param": lambda p: production.device_set_param(song(), p),
            "utility.ensure_last": lambda p: production.utility_ensure_last(song(), p),
            "master.device_insert": lambda p: production.master_device_insert(song(), p),
            "master.device_set_param": lambda p: production.master_device_set_param(song(), p),
            "master.set_mixer": lambda p: production.master_set_mixer(song(), p),
            "compressor.set_sidechain": lambda p: production.compressor_set_sidechain(song(), p),
            "simpler.load": lambda p: production.simpler_load(song(), p),
            "locator.set": lambda p: self.locators.set(song(), p),
            "locator.set_many": lambda p: self.locators.set_many(song(), p),
            "locator.status": lambda p: self.locators.status(song()),
            "locator.clear_all": lambda p: self.locators.clear_all(song(), p),
            "automation.record": lambda p: self._exclusive(self.meter, "meter capture", self.automation.record, p),
            "meter.capture": lambda p: self._exclusive(self.automation, "automation recording", self.meter.capture, p),
            "meter.status": lambda p: self.meter.status(song()),
            "meter.cancel": lambda p: self.meter.cancel(song()),
            "automation.status": lambda p: self.automation.status(song()),
            "automation.cancel": lambda p: self.automation.cancel(song()),
            "automation.clear": lambda p: automation.clear(song(), p),
            "probe.api": lambda params: handlers.probe_api(self._live, self._live_info),
            "spike.automation_session": lambda p: spikes.automation_session(song(), self._live, p),
            "spike.automation_record_start": lambda p: self.spikes.start(song(), self._live, p),
            "spike.automation_record_status": lambda p: self.spikes.status(song()),
            "spike.automation_arm": lambda p: spikes.automation_arm(song(), p),
            "spike.audio_clip": lambda p: spikes_media.audio_clip(song(), self._live, p),
            "spike.devices": lambda p: spikes_media.devices(song(), self._live, p),
            "spike.simpler_slice": lambda p: spikes_media.simpler_slice(song(), self._live, p),
            "spike.cleanup": lambda p: spikes.cleanup(song(), self.spikes),
        }
