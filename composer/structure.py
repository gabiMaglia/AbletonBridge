"""Estructura del tema: secciones en compases y grilla de frases 8/16/32. 4/4, compases 1-based."""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from .profile import Perfil

TIPOS_SECCION = ("intro", "groove", "drop", "breakdown", "silence", "outro")
BEATS_POR_COMPAS = 4


def compas_a_beat(compas: int) -> float:
    """Inicio del compas (1-based) en beats desde el origen."""
    return float((compas - 1) * BEATS_POR_COMPAS)


def nivel_de_frase(compas: int) -> int:
    """Nivel de la frase que TERMINA en este compas: 32, 16, 8 o 0 si no cierra ninguna."""
    for nivel in (32, 16, 8):
        if compas % nivel == 0:
            return nivel
    return 0


@dataclass(frozen=True)
class Seccion:
    id: str
    tipo: str
    inicio: int          # primer compas
    compases: int
    spec: Dict[str, Any]  # el dict de la plantilla (suma/quita/solo/ocasionales/transicion)

    @property
    def fin(self) -> int:
        """Ultimo compas, inclusive."""
        return self.inicio + self.compases - 1

    @property
    def beat_inicio(self) -> float:
        return compas_a_beat(self.inicio)

    @property
    def beat_fin(self) -> float:
        """Fin exclusivo en beats."""
        return compas_a_beat(self.fin + 1)


@dataclass(frozen=True)
class Estructura:
    secciones: Sequence[Seccion]

    @property
    def total_compases(self) -> int:
        return self.secciones[-1].fin

    @property
    def beat_final(self) -> float:
        return compas_a_beat(self.total_compases + 1)

    def seccion(self, id_: str) -> Seccion:
        for s in self.secciones:
            if s.id == id_:
                return s
        raise KeyError(id_)

    def seccion_en(self, compas: int) -> Seccion:
        for s in self.secciones:
            if s.inicio <= compas <= s.fin:
                return s
        raise ValueError("el compas %d esta fuera del tema" % compas)

    def anterior(self, sec: Seccion) -> Optional[Seccion]:
        i = list(self.secciones).index(sec)
        return self.secciones[i - 1] if i > 0 else None

    def siguiente(self, sec: Seccion) -> Optional[Seccion]:
        i = list(self.secciones).index(sec)
        return self.secciones[i + 1] if i + 1 < len(self.secciones) else None

    def de_tipo(self, tipo: str) -> List[Seccion]:
        return [s for s in self.secciones if s.tipo == tipo]


def estructura_desde_secciones(specs: Sequence[Dict[str, Any]]) -> Estructura:
    out: List[Seccion] = []
    compas = 1
    for spec in specs:
        if spec["tipo"] not in TIPOS_SECCION:
            raise ValueError("tipo de seccion %r invalido (%s)" % (spec["tipo"], ", ".join(TIPOS_SECCION)))
        if spec["compases"] < 1:
            raise ValueError("la seccion %r necesita al menos 1 compas" % spec["id"])
        out.append(Seccion(id=spec["id"], tipo=spec["tipo"], inicio=compas, compases=spec["compases"], spec=dict(spec)))
        compas += spec["compases"]
    if not out:
        raise ValueError("estructura vacia")
    return Estructura(secciones=tuple(out))


def construir_estructura(perfil: Perfil, plantilla: str, largo_compases: Optional[int] = None) -> Estructura:
    """Estructura de una plantilla del perfil. Si piden otro largo, lo absorbe el ultimo outro (multiplos de 8)."""
    specs = [dict(s) for s in perfil.plantilla(plantilla)["secciones"]]
    if largo_compases is not None:
        diferencia = largo_compases - sum(s["compases"] for s in specs)
        if diferencia:
            outros = [s for s in specs if s["tipo"] == "outro"]
            nuevo = outros[-1]["compases"] + diferencia if outros else 0
            if not outros or nuevo < 8 or nuevo % 8:
                raise ValueError("largo %d imposible: el ultimo outro quedaria de %s compases (min 8, multiplo de 8)"
                                 % (largo_compases, nuevo if outros else "?"))
            outros[-1]["compases"] = nuevo
    return estructura_desde_secciones(specs)
