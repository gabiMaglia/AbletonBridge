"""
AbletonBridge ControlSurface — entry point real dentro de Live.

Corre en el hilo principal de Live. El socket vive en otro thread
(server.py) y todo acceso al LOM se encola en el UIDispatcher, que aca se
drena desde `_tick`.
"""
from typing import Any, Callable, Dict, List, Optional

from . import handlers
from .dispatcher import UIDispatcher
from .server import BridgeServer, DEFAULT_PORT, FALLBACK_PORT_RANGE

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
    def __init__(self, c_instance: Any) -> None:
        super().__init__(c_instance)
        self._running = False
        self.dispatcher = UIDispatcher()
        self.server: Optional[BridgeServer] = None
        try:
            import Live  # solo existe dentro de Live

            self._live = Live
            self._live_info = handlers.read_live_info(Live)
            self.server = BridgeServer(
                dispatcher=self.dispatcher,
                live_info_provider=lambda: self._live_info,
                preferred_port=PREFERRED_PORT,
                port_range=PORT_RANGE,
                handlers=self._build_handlers(),
            )
            port = self.server.bind()
            self.server.start()
            self._running = True
            self.log_message(f"AbletonBridge: listening on 127.0.0.1 port {port}")
            self.show_message(f"AbletonBridge: port {port}")
            self.schedule_message(1, self._tick)
        except Exception as exc:  # noqa: BLE001 - nunca propagar a Live
            self.log_message(f"AbletonBridge: init error: {exc!r}")

    def _build_handlers(self) -> Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]]:
        return {
            "state.get": lambda params: handlers.get_state(self.song(), self._live_info, params),
            "probe.api": lambda params: handlers.probe_api(self._live, self._live_info),
        }

    def _tick(self) -> None:
        # Pump via schedule_message re-encadenado: corre en el hilo principal,
        # como AbletonOSC; update_display tambien serviria pero obliga a
        # acordarse de llamar super() y no aporta nada mas.
        if not self._running:
            return
        try:
            self.dispatcher.pump()
        except Exception as exc:  # noqa: BLE001
            self.log_message(f"AbletonBridge: tick error: {exc!r}")
        try:
            self.schedule_message(1, self._tick)
        except Exception as exc:  # noqa: BLE001
            self.log_message(f"AbletonBridge: reschedule error: {exc!r}")

    def disconnect(self) -> None:
        self._running = False
        try:
            if self.server is not None:
                self.server.stop()
        except Exception as exc:  # noqa: BLE001
            self.log_message(f"AbletonBridge: stop error: {exc!r}")
        super().disconnect()
