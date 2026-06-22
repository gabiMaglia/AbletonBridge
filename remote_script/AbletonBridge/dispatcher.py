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
from typing import Any, Callable, Optional


class UIDispatcher:
    def __init__(self) -> None:
        self._queue: "queue.Queue[Callable[[], None]]" = queue.Queue()

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

    def run_blocking(self, job: Callable[[], Any], timeout: float = 5.0) -> Any:
        """
        Encola `job` y bloquea el thread llamador hasta que `pump()` lo
        ejecute (o expire `timeout`). Devuelve el resultado de `job` o
        re-lanza su excepcion en el thread llamador.

        Usado por el thread del socket para obtener el resultado de una
        operacion LOM ejecutada en el hilo de UI.
        """
        done = threading.Event()
        outcome: dict = {}

        def wrapped() -> None:
            try:
                outcome["result"] = job()
            except Exception as exc:  # noqa: BLE001 - se re-lanza en el caller
                outcome["error"] = exc
            finally:
                done.set()

        self.submit(wrapped)

        if not done.wait(timeout=timeout):
            raise TimeoutError("UIDispatcher.run_blocking timed out waiting for pump()")

        if "error" in outcome:
            raise outcome["error"]
        return outcome.get("result")
