"""Carga y validacion del perfil de genero (YAML, esquema F4 sec. 8)."""
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

PERFIL_POR_DEFECTO = Path(__file__).resolve().parent.parent / "docs" / "nexo" / "perfiles" / "techno_peak_time.yaml"

# Nombres de warp del perfil -> modo de Live (Clip.warp_mode)
WARP_MODES: Dict[str, int] = {"beats": 0, "tones": 1, "texture": 2, "repitch": 3, "complex": 4, "complex_pro": 6}

SECCIONES_OBLIGATORIAS = ("perfil", "global", "elementos", "reglas", "transiciones", "mezcla", "plantillas")
# Secciones cuyos bloques hijos llevan fuente y confianza cada uno...
SECCIONES_ANOTADAS = ("global", "elementos", "reglas")
# ...y secciones que se anotan enteras (un solo origen para todo el bloque).
SECCIONES_ANOTADAS_ENTERAS = ("transiciones", "mezcla", "plantillas")
CONFIANZAS = ("alta", "media", "baja")
_PARAMS_DE_VOLUMEN = {"volume", "volumen", "gain", "fader"}


class PerfilInvalido(ValueError):
    pass


def _revisar_d15(nodo: Any, ruta: str) -> None:
    """D-15: ningun parametro a automatizar puede ser el volumen del track."""
    if isinstance(nodo, dict):
        for k, v in nodo.items():
            if k in ("parametro", "param") and str(v).lower() in _PARAMS_DE_VOLUMEN:
                raise PerfilInvalido(
                    "D-15: %s.%s = %r automatizaria el volumen (usar el Output de un Utility)" % (ruta, k, v))
            _revisar_d15(v, "%s.%s" % (ruta, k))
    elif isinstance(nodo, list):
        for i, v in enumerate(nodo):
            _revisar_d15(v, "%s[%d]" % (ruta, i))


def validar_perfil(datos: Dict[str, Any]) -> None:
    for sec in SECCIONES_OBLIGATORIAS:
        if sec not in datos:
            raise PerfilInvalido("falta la seccion obligatoria %r" % sec)
    bloques = [("%s.%s" % (sec, nombre), b) for sec in SECCIONES_ANOTADAS for nombre, b in datos[sec].items()]
    bloques += [(sec, datos[sec]) for sec in SECCIONES_ANOTADAS_ENTERAS]
    for nombre, bloque in bloques:
        if not isinstance(bloque, dict):
            raise PerfilInvalido("%s debe ser un bloque con fuente y confianza" % nombre)
        for campo in ("fuente", "confianza"):
            if campo not in bloque:
                raise PerfilInvalido("%s: falta %r" % (nombre, campo))
        if bloque["confianza"] not in CONFIANZAS:
            raise PerfilInvalido("%s: confianza %r desconocida (%s)" % (
                nombre, bloque["confianza"], "/".join(CONFIANZAS)))
        if bloque.get("criterio_gabriel") and bloque["confianza"] != "alta":
            raise PerfilInvalido("%s: un criterio de Gabriel lleva confianza alta (D-13)" % nombre)
    for nombre, el in datos["elementos"].items():
        warp = el.get("warp")
        if warp is not None and warp not in WARP_MODES:
            raise PerfilInvalido("elementos.%s: warp %r desconocido (%s)" % (nombre, warp, ", ".join(WARP_MODES)))
        if el.get("tipo") not in ("loop", "oneshot", "midi"):
            raise PerfilInvalido("elementos.%s: tipo %r invalido" % (nombre, el.get("tipo")))
    _revisar_d15(datos, "perfil")


@dataclass(frozen=True)
class Perfil:
    datos: Dict[str, Any]

    @property
    def id(self) -> str:
        return self.datos["perfil"]["id"]

    @property
    def version(self) -> str:
        return str(self.datos["perfil"]["version"])

    def dato(self, *camino: str) -> Any:
        nodo: Any = self.datos
        for k in camino:
            nodo = nodo[k]
        return nodo

    def rol(self, nombre: str) -> Dict[str, Any]:
        try:
            return self.datos["elementos"][nombre]
        except KeyError:
            raise PerfilInvalido("rol desconocido %r" % nombre)

    def regla(self, nombre: str) -> Dict[str, Any]:
        return self.datos["reglas"][nombre]

    def plantilla(self, nombre: str) -> Dict[str, Any]:
        plantillas = self.datos["plantillas"]
        if nombre not in plantillas or not isinstance(plantillas[nombre], dict) or "secciones" not in plantillas[nombre]:
            raise PerfilInvalido("plantilla %r inexistente" % nombre)
        return plantillas[nombre]


def cargar_perfil(path: Optional[Path] = None) -> Perfil:
    ruta = Path(path) if path else PERFIL_POR_DEFECTO
    with open(ruta, encoding="utf-8") as fh:
        datos = yaml.safe_load(fh)
    validar_perfil(datos)
    return Perfil(datos=datos)
