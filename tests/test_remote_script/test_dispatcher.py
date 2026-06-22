"""
Tests del mecanismo de despacho thread-safe hacia el hilo de UI de Live.

CAVEAT T-001 (critico): las operaciones sobre song.*/LOM NO son thread-safe.
El socket corre en un thread aparte; toda operacion sobre el LOM debe
encolarse y ejecutarse via el scheduler del Remote Script (equivalente a
`schedule_message` de ControlSurface), nunca directamente desde el thread
del socket.

Estos tests NO dependen de Ableton: simulan el "tick" del scheduler que en
produccion dispara Live, y verifican que el trabajo encolado desde otro
thread se ejecuta en el thread que llama a `pump()` (proxy del hilo de UI).
"""
import threading
import time

import pytest

from remote_script.AbletonBridge.dispatcher import UIDispatcher


def test_pump_runs_job_submitted_from_same_thread() -> None:
    dispatcher = UIDispatcher()
    calls = []
    dispatcher.submit(lambda: calls.append("ran"))
    dispatcher.pump()
    assert calls == ["ran"]


def test_pump_executes_jobs_in_fifo_order() -> None:
    dispatcher = UIDispatcher()
    order = []
    dispatcher.submit(lambda: order.append(1))
    dispatcher.submit(lambda: order.append(2))
    dispatcher.submit(lambda: order.append(3))
    dispatcher.pump()
    assert order == [1, 2, 3]


def test_pump_without_pending_jobs_is_noop() -> None:
    dispatcher = UIDispatcher()
    dispatcher.pump()  # no debe lanzar ni bloquear


def test_job_submitted_from_worker_thread_runs_on_pump_thread() -> None:
    dispatcher = UIDispatcher()
    submitting_thread_id = []
    running_thread_id = []

    def job() -> None:
        running_thread_id.append(threading.get_ident())

    def worker() -> None:
        submitting_thread_id.append(threading.get_ident())
        dispatcher.submit(job)

    t = threading.Thread(target=worker)
    t.start()
    t.join(timeout=2)

    dispatcher.pump()  # corre en el thread de test == "hilo de UI" simulado

    assert running_thread_id[0] == threading.get_ident()
    assert submitting_thread_id[0] != threading.get_ident()


def test_run_blocking_returns_result_to_caller_thread() -> None:
    """
    Patron sincronico: el thread del socket necesita el resultado de la
    operacion LOM para construir la response. `run_blocking` encola el job,
    espera (con timeout) a que `pump()` lo ejecute, y devuelve su resultado.
    """
    dispatcher = UIDispatcher()
    result_holder = {}

    def call_from_socket_thread() -> None:
        result_holder["value"] = dispatcher.run_blocking(lambda: 21 * 2, timeout=2.0)

    t = threading.Thread(target=call_from_socket_thread)
    t.start()

    # Simula el scheduler de Live llamando pump() periodicamente.
    deadline = time.time() + 2.0
    while t.is_alive() and time.time() < deadline:
        dispatcher.pump()
        time.sleep(0.01)
    t.join(timeout=2)

    assert result_holder["value"] == 42


def test_run_blocking_propagates_exception_from_job() -> None:
    dispatcher = UIDispatcher()

    def job() -> None:
        raise ValueError("boom")

    errors_seen = []

    def call_from_socket_thread() -> None:
        try:
            dispatcher.run_blocking(job, timeout=2.0)
        except ValueError as exc:
            errors_seen.append(exc)

    t = threading.Thread(target=call_from_socket_thread)
    t.start()
    deadline = time.time() + 2.0
    while t.is_alive() and time.time() < deadline:
        dispatcher.pump()
        time.sleep(0.01)
    t.join(timeout=2)

    assert len(errors_seen) == 1
    assert str(errors_seen[0]) == "boom"


def test_run_blocking_times_out_if_pump_never_called() -> None:
    dispatcher = UIDispatcher()
    with pytest.raises(TimeoutError):
        dispatcher.run_blocking(lambda: 1, timeout=0.1)
