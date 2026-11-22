"""
Helpers de LECTURA del LOM compartidos (spikes y state.detail).

Regla: un campo ilegible nunca aborta la lectura completa; se reporta como
"unavailable: <ExcType>". Stdlib pura (corre en el Python embebido de Live).
"""
from typing import Any, Callable

UNAVAILABLE = "unavailable"


def safe(fn: Callable[[], Any]) -> Any:
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 - un campo roto no frena el resto
        return f"{UNAVAILABLE}: {type(exc).__name__}"


def get(obj: Any, attr: str) -> Any:
    return safe(lambda: getattr(obj, attr))


def is_unavailable(value: Any) -> bool:
    return isinstance(value, str) and value.startswith(UNAVAILABLE)
