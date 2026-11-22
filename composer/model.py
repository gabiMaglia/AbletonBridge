"""Tipos compartidos: elementos del tema y acciones del timeline (todo es dato, nada toca Live)."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Acciones de preparacion (beat 0)
RETORNO = "retorno"
PISTA = "pista"
DISPOSITIVO = "dispositivo"
MEZCLA = "mezcla"
SIDECHAIN = "sidechain"
# Acciones sobre la linea de tiempo
CLIP_LOOP = "clip_loop"
CLIP_ONESHOT = "clip_oneshot"
MIDI = "midi"
LOCATOR = "locator"
AUTOMATIZACION = "automatizacion"
# Informativa: deja escrita en el plan una decision de arreglo (el ejecutor no la toca)
DECISION = "decision"

TIPOS = (RETORNO, PISTA, DISPOSITIVO, MEZCLA, SIDECHAIN, CLIP_LOOP, CLIP_ONESHOT, MIDI, LOCATOR,
         AUTOMATIZACION, DECISION)

Run = Tuple[float, float]  # [inicio, fin) en beats

_PARAMS_DE_VOLUMEN = {"volume", "volumen", "vol", "fader", "gain", "track volume"}


@dataclass(frozen=True)
class Elemento:
    """Material de un rol: de donde sale el audio y como entra (los None caen al perfil)."""
    rol: str
    ruta: str
    warp: Optional[str] = None
    pitch: int = 0
    natural_beats: Optional[float] = None  # largo medido de un one-shot, si se conoce
    alternativas: Tuple[str, ...] = ()     # otros archivos del mismo rol: las reglas los rotan


def _validar_objetivo_d15(objetivo: Any) -> None:
    """D-15: ninguna lane puede apuntar al volumen/ganancia del track; el nivel va en Utility.Output."""
    if objetivo == "pan":
        return
    if isinstance(objetivo, str) and objetivo.lower() in _PARAMS_DE_VOLUMEN:
        raise ValueError("D-15: prohibido automatizar el volumen del track; usar Utility 'Output'")
    if isinstance(objetivo, dict):
        param = str(objetivo.get("param", "")).lower()
        if param in _PARAMS_DE_VOLUMEN:
            raise ValueError("D-15: prohibido automatizar volume/gain; usar Utility 'Output' (param %r)" % param)
        if objetivo.get("device") == "Utility" and objetivo.get("param") != "Output":
            raise ValueError("D-15: en un Utility solo se automatiza 'Output' (pedido %r)" % objetivo.get("param"))


@dataclass(frozen=True)
class Accion:
    """Una cosa que hacer. `inicio`/`fin` en beats absolutos (fin puede ser None)."""
    tipo: str
    rol: str
    inicio: float
    fin: Optional[float]
    datos: Dict[str, Any]
    regla: str
    por_que: str

    def __post_init__(self) -> None:
        if self.tipo not in TIPOS:
            raise ValueError("tipo de accion desconocido: %r" % self.tipo)
        if self.tipo == AUTOMATIZACION:
            _validar_objetivo_d15(self.datos.get("objetivo"))
            pts = self.datos.get("puntos") or []
            if not pts:
                raise ValueError("lane sin puntos (%s)" % self.rol)
            beats = [p[0] for p in pts]
            if any(b2 <= b1 for b1, b2 in zip(beats, beats[1:])) or beats[0] < 0:
                raise ValueError("los puntos de una lane deben crecer estrictamente (%s)" % self.rol)


@dataclass
class Timeline:
    acciones: List[Accion] = field(default_factory=list)

    def agregar(self, *acciones: Accion) -> None:
        self.acciones.extend(acciones)

    def de_tipo(self, tipo: str) -> List[Accion]:
        return [a for a in self.acciones if a.tipo == tipo]

    def del_rol(self, rol: str) -> List[Accion]:
        return [a for a in self.acciones if a.rol == rol]

    def ordenar(self) -> None:
        orden = {t: i for i, t in enumerate(TIPOS)}
        self.acciones.sort(key=lambda a: (orden[a.tipo], a.inicio, a.rol, a.regla))

    def lanes_en_conflicto(self) -> List[Tuple[Accion, Accion]]:
        """Pares de lanes del mismo (rol, destino) cuyas ventanas de tiempo se pisan."""
        lanes = self.de_tipo(AUTOMATIZACION)
        malos = []
        for i, a in enumerate(lanes):
            for b in lanes[i + 1:]:
                if (a.rol, repr(a.datos["objetivo"])) == (b.rol, repr(b.datos["objetivo"])):
                    if a.inicio < b.fin and b.inicio < a.fin:
                        malos.append((a, b))
        return malos
