"""
AbletonBridge ControlSurface — entry point real dentro de Live.

Corre en el hilo principal de Live. El socket vive en otro thread
(server.py) y todo acceso al LOM se encola en el UIDispatcher, que aca se
drena desde `_tick`.
"""
from typing import Any, Callable, List, Optional

from . import handlers, reloader, runtime
from .server import DEFAULT_PORT, FALLBACK_PORT_RANGE

PREFERRED_PORT = DEFAULT_PORT
PORT_RANGE = FALLBACK_PORT_RANGE

try:  # dentro de Live
    from _Framework.ControlSurface import ControlSurface as _Base
except ImportError:  # fuera de Live (tests): stub minimo con la misma superficie

    class _Base:  # type: ignore[no-redef]
        def __init__(self, c_instance: Any) -> None:
            self._c_instance = c_instance
            self.logs: List[str] = []
            self.scheduled: List[Callable[[], None]] = []

        def song(self) -> Any:
            return self._c_instance.song()

        def log_message(self, *msgs: Any) -> None:
            self.logs.append(" ".join(str(m) for m in msgs))

        def show_message(self, msg: str) -> None:
            self.logs.append(msg)

        def schedule_message(self, delay: int, callback: Callable[[], None]) -> None:
            self.scheduled.append(callback)

        def disconnect(self) -> None:
            pass


class AbletonBridge(_Base):
    """
    Cascara fina que Live posee. Todo lo intercambiable vive en `self.runtime`
    (runtime.BridgeRuntime) para poder rearmarlo con `bridge.reload` sin reiniciar Live.
    """

    def __init__(self, c_instance: Any) -> None:
        super().__init__(c_instance)
        self._running = False
        self._reload_pending = False
        self._reload_deferred_logged = False
        self.reload_count = 0
        self.runtime: Optional[runtime.BridgeRuntime] = None
        try:
            import Live  # solo existe dentro de Live

            self._live = Live
            self._live_info = handlers.read_live_info(Live)
            self.runtime = runtime.BridgeRuntime(self, Live, self._live_info, PREFERRED_PORT, PORT_RANGE)
            port = self.runtime.start()
            self._running = True
            self.log_message(f"AbletonBridge: listening on 127.0.0.1 port {port}")
            self.show_message(f"AbletonBridge: port {port}")
            self.schedule_message(1, self._tick)
        except Exception as exc:  # noqa: BLE001 - nunca propagar a Live
            self.log_message(f"AbletonBridge: init error: {exc!r}")

    # Atajos al runtime vigente (los tests y el codigo viejo siguen usando estos nombres).
    @property
    def server(self) -> Any:
        return self.runtime.server if self.runtime is not None else None

    @property
    def dispatcher(self) -> Any:
        return self.runtime.dispatcher if self.runtime is not None else None

    @property
    def spikes(self) -> Any:
        return self.runtime.spikes if self.runtime is not None else None

    @property
    def locators(self) -> Any:
        return self.runtime.locators if self.runtime is not None else None

    def request_reload(self) -> None:
        """Lo llama el thread del socket tras enviar la respuesta de bridge.reload; el reload corre en _tick."""
        self._reload_pending = True

    def _tick(self) -> None:
        # Pump via schedule_message re-encadenado: corre en el hilo principal,
        # como AbletonOSC; update_display tambien serviria pero obliga a
        # acordarse de llamar super() y no aporta nada mas.
        if not self._running:
            return
        if self.runtime is not None:
            self.runtime.tick()
        if self._reload_pending:
            try:
                self._reload()
            except Exception as exc:  # noqa: BLE001 - jamas propagar a Live
                self.log_message(f"AbletonBridge: reload crashed: {exc!r}")
        try:
            self.schedule_message(1, self._tick)
        except Exception as exc:  # noqa: BLE001
            self.log_message(f"AbletonBridge: reschedule error: {exc!r}")

    def _reload(self) -> None:
        """
        Recarga los modulos del paquete y rearma el runtime (puerto liberado y re-bindeado).
        Orden: 1) recargar modulos (si falla, se restauran y el bridge viejo sigue intacto);
        2) detener el runtime viejo y construir uno nuevo con el codigo nuevo; 3) si eso falla,
        volver a los modulos viejos y reconstruir con ellos.
        """
        old = self.runtime
        if old is None:
            self._reload_pending = False
            return
        if old.busy():  # locators/spike a mitad de camino: se pierden al reiniciar la maquina
            if not self._reload_deferred_logged:
                self.log_message("AbletonBridge: reload deferred, locator/spike queue is busy")
                self._reload_deferred_logged = True
            return
        self._reload_pending = self._reload_deferred_logged = False
        port = old.server.port if old.server is not None and old.server.port else PREFERRED_PORT
        try:
            result = reloader.reload_package(__package__ or "AbletonBridge")
        except Exception as exc:  # noqa: BLE001 - SyntaxError, ImportError, lo que sea
            self.log_message(f"AbletonBridge: reload failed, keeping the running bridge: {exc!r}")
            return
        try:
            old.stop()
            self.runtime = self._start_runtime(old, port)
            self.reload_count += 1
            self.log_message(f"AbletonBridge: reloaded, listening on port {self.runtime.server.port}")
        except Exception as exc:  # noqa: BLE001
            self.log_message(f"AbletonBridge: new runtime failed ({exc!r}), rolled back to the old modules")
            result.rollback()
            try:
                self.runtime = self._start_runtime(old, port)
            except Exception as exc2:  # noqa: BLE001
                self._running = False
                self.log_message(f"AbletonBridge: rollback failed too ({exc2!r}); restart Live")

    def _start_runtime(self, old: Any, port: int) -> Any:
        new = runtime.BridgeRuntime(self, self._live, self._live_info, port, PORT_RANGE)
        new.adopt(old)
        new.start()
        return new

    def disconnect(self) -> None:
        self._running = False
        try:
            if self.runtime is not None:
                self.runtime.stop()
        except Exception as exc:  # noqa: BLE001
            self.log_message(f"AbletonBridge: stop error: {exc!r}")
        super().disconnect()
