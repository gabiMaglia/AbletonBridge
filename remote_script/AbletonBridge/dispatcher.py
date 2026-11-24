"""
UIDispatcher — cola thread-safe para despachar trabajo al hilo de UI de Live.

CAVEAT T-001 (critico, ver engram/03_backlog.md T-002): las operaciones
sobre song.*/LOM NO son thread-safe. El socket TCP corre en un thread
aparte (ver server.py); cualquier llamada al LOM DEBE encolarse aca y
ejecutarse cuando Live invoca `pump()` desde su propio scheduler
(equivalente a `schedule_message`/`tick` de ControlSurface).

Esta clase es agnostica de Live: en produccion, el Remote Script registra
`pump` como callback periodico del scheduler de Live. En tests, `pump()`
se llama manualmente desde el thread de test para simular ese tick.

Stdlib pura (queue, threading) — corre en el interprete embebido de Live.
"""
import queue
import threading
import time
from collections import deque
from typing import Any, Callable, Dict, Optional

from . import errors

# Timeouts de espera en cola, por comando (T-024). Deben ser ESTRICTAMENTE menores que los del
# cliente MCP (client.DEFAULT_TIMEOUT 5 s / HEAVY_TIMEOUT 30 s) para que el servidor conteste antes
# de que el cliente se rinda; un test compara ambos mapas. Este modulo no importa mcp_server.
READ_TIMEOUT = 4.0
HEAVY_TIMEOUT = 25.0
# Mismo conjunto que client.HEAVY_COMMANDS (escrituras que en Live tardan segundos).
HEAVY_COMMANDS = frozenset({
    "song.set", "clip.place_audio", "clip.create_midi", "clip.delete_range", "simpler.load",
    "track.create", "return.create", "device.insert", "return.device_insert", "master.device_insert",
})
# Tope duro para un job que YA empezo cuando vence el timeout: se espera su resultado real en vez de
# reportar falla de algo que esta corriendo. Mas alla de esto el hilo del socket no puede quedar colgado.
STARTED_CAP = 120.0
STATS_KEEP = 10


def timeout_for(cmd: str) -> float:
    return HEAVY_TIMEOUT if cmd in HEAVY_COMMANDS else READ_TIMEOUT


class UIDispatcher:
    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._queue: "queue.Queue[Callable[[], None]]" = queue.Queue()
        self._clock = clock
        self._stats_lock = threading.Lock()
        self._stats: Dict[str, Dict[str, Any]] = {}

    def submit(self, job: Callable[[], None]) -> None:
        """Encola un job fire-and-forget. Puede llamarse desde cualquier thread."""
        self._queue.put(job)

    def pump(self) -> None:
        """
        Ejecuta todos los jobs pendientes en el thread que llama a `pump()`.
        En produccion, Live llama esto periodicamente desde el hilo de UI.
        """
        while True:
            try:
                job = self._queue.get_nowait()
            except queue.Empty:
                break
            job()

    def run_blocking(
        self,
        job: Callable[[], Any],
        timeout: float = 5.0,
        cmd: Optional[str] = None,
        started_cap: float = STARTED_CAP,
    ) -> Any:
        """
        Encola `job` y bloquea el thread llamador hasta que `pump()` lo ejecute. Devuelve el
        resultado de `job` o re-lanza su excepcion en el thread llamador.

        Si pasan `timeout` s y el job NO empezo, se cancela (no correra nunca, ni cuando Live
        atienda la cola) y se lanza DISPATCH_TIMEOUT "no se ejecuto". Si ya empezo, se espera a que
        termine (hasta `started_cap` s) y se devuelve su resultado real.

        Con `cmd`, registra tiempo en cola y de ejecucion (ver `stats`).
        """
        done = threading.Event()
        outcome: dict = {}
        lock = threading.Lock()
        state = {"phase": "queued"}  # queued -> started | cancelled
        submitted = self._clock()

        def wrapped() -> None:
            with lock:
                if state["phase"] == "cancelled":
                    return
                state["phase"] = "started"
            began = self._clock()
            try:
                outcome["result"] = job()
            except Exception as exc:  # noqa: BLE001 - se re-lanza en el caller
                outcome["error"] = exc
            finally:
                if cmd:
                    self._record(cmd, began - submitted, self._clock() - began)
                done.set()

        self.submit(wrapped)

        if not done.wait(timeout=timeout):
            with lock:
                cancelled = state["phase"] == "queued"
                if cancelled:
                    state["phase"] = "cancelled"
            label = f" ({cmd})" if cmd else ""
            if cancelled:
                if cmd:
                    self._record_cancelled(cmd)
                raise errors.CommandError(
                    errors.DISPATCH_TIMEOUT,
                    f"no se ejecuto{label}: Live no atendio la cola en {timeout:g} s",
                )
            if not done.wait(timeout=started_cap):
                raise errors.CommandError(
                    errors.DISPATCH_TIMEOUT,
                    f"el comando{label} sigue ejecutandose en Live tras {timeout + started_cap:g} s; "
                    "relee el estado antes de reintentar",
                )

        if "error" in outcome:
            raise outcome["error"]
        return outcome.get("result")

    # -- instrumentacion (DT-09) --

    def _entry(self, cmd: str) -> Dict[str, Any]:
        return self._stats.setdefault(
            cmd, {"count": 0, "cancelled": 0, "last": deque(maxlen=STATS_KEEP)}
        )

    def _record(self, cmd: str, wait_s: float, run_s: float) -> None:
        with self._stats_lock:
            entry = self._entry(cmd)
            entry["count"] += 1
            entry["last"].append({"wait_ms": round(wait_s * 1000, 1), "run_ms": round(run_s * 1000, 1)})

    def _record_cancelled(self, cmd: str) -> None:
        with self._stats_lock:
            self._entry(cmd)["cancelled"] += 1

    def stats(self) -> Dict[str, Dict[str, Any]]:
        """Por cmd: {count, cancelled, last: [{wait_ms, run_ms}] (ultimos STATS_KEEP)}."""
        with self._stats_lock:
            return {
                cmd: {"count": e["count"], "cancelled": e["cancelled"], "last": list(e["last"])}
                for cmd, e in self._stats.items()
            }
