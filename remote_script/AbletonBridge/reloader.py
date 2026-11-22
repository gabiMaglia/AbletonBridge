"""
Recarga en caliente de NUESTROS modulos (T-011), sin reiniciar Live.

Este modulo y `surface` NO se recargan: el reloader no puede reemplazarse a si mismo y la
instancia de ControlSurface pertenece a Live (su clase queda ligada al `surface` original);
cambios en ellos o en `__init__` siguen pidiendo reiniciar Live.
Solo se recargan modulos de este paquete, nombrados en RELOAD_ORDER (sin exec/eval).
"""
import importlib
import sys
from typing import Any, Dict, List, Sequence

# Orden de dependencias (cada modulo despues de los que importa); un test lo verifica contra el AST.
RELOAD_ORDER = (
    "errors", "version", "protocol", "lom_read", "dispatcher", "handlers", "production",
    "automation", "spikes", "spikes_media", "state_detail", "server", "runtime",
)


class ReloadResult:
    def __init__(self, modules: List[Any], snapshots: List[Dict[str, Any]]) -> None:
        self.modules = modules
        self._snapshots = snapshots

    def rollback(self) -> None:
        for module, snap in zip(self.modules, self._snapshots):
            restore(module, snap)


def restore(module: Any, snapshot: Dict[str, Any]) -> None:
    # Se actualiza en lugar de vaciar: el thread del socket puede estar usando estos globals.
    d = module.__dict__
    d.update(snapshot)
    for key in [k for k in d if k not in snapshot]:
        del d[key]


def reload_package(package: str, order: Sequence[str] = RELOAD_ORDER) -> ReloadResult:
    """
    Recarga `order` dentro de `package`. Si algo falla (sintaxis, import) deja TODOS los modulos
    como estaban y re-lanza; el resultado exitoso permite `rollback()` si lo que viene despues falla.
    """
    for name in order:
        if not name.isidentifier():  # sin puntos ni '..': nunca salir del paquete
            raise ValueError(f"invalid module name {name!r}")
    modules = []
    for name in order:
        full = f"{package}.{name}"
        try:
            modules.append(sys.modules.get(full) or importlib.import_module(full))
        except ModuleNotFoundError as exc:
            raise ValueError(f"{full} is not a module of this package") from exc
    snapshots = [dict(m.__dict__) for m in modules]
    try:
        for module in modules:
            importlib.reload(module)
    except Exception:
        for module, snap in zip(modules, snapshots):
            restore(module, snap)
        raise
    return ReloadResult(modules, snapshots)
