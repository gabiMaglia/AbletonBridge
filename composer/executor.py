"""Ejecutor: lleva un plan al puente con un cliente inyectable (o lo imprime en dry-run).

Respeta lo que T02 enseno:
- one-shots: se mide el largo natural (se coloca lejos del tema, se lee el span, se borra) y despues
  se coloca anclado al inicio o al fin; el span se mide una vez por archivo;
- tiles: `clip.place_audio` ya resuelve el largo exacto, se pide un clip por rango contiguo;
- locators: set_many + sondeo de status hasta que no quede nada pendiente;
- automatizacion grabada: una pasada por rango contiguo (agrupar_pasadas), y el nivel va al
  `target` que devuelve `utility.ensure_last` (D-15).
"""
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from .model import (AUTOMATIZACION, CLIP_LOOP, CLIP_ONESHOT, DISPOSITIVO, LOCATOR, MEZCLA, MIDI, PISTA,
                    RETORNO, SIDECHAIN, Accion)
from .plan import Plan, agrupar_pasadas
from .profile import WARP_MODES, ItemDesconocido, valor_item

MEDIR_EN_BEAT = 4800.0       # lejos del tema: ahi se mide el largo natural de un one-shot
MEDIR_LARGO = 64.0
MAX_LANES_POR_LLAMADA = 16   # tope de automation.record
PREROLL_BEATS = 4.0
PLAYBACK_ONE_SHOT = 1


@dataclass
class Llamada:
    nombre: str
    kwargs: Dict[str, Any]


@dataclass
class Informe:
    llamadas: List[Llamada] = field(default_factory=list)
    advertencias: List[str] = field(default_factory=list)


def _corto(v: Any) -> str:
    if isinstance(v, list):
        return "[%d items]" % len(v)
    return repr(v)


def formatear_llamadas(llamadas: List[Llamada]) -> str:
    return "\n".join("%s(%s)" % (l.nombre, ", ".join("%s=%s" % (k, _corto(v)) for k, v in l.kwargs.items()))
                     for l in llamadas)


class Ejecutor:
    def __init__(self, api: Any, client: Any, dry_run: bool = False,
                 sleep: Callable[[float], None] = time.sleep, max_polls: int = 80, intervalo: float = 0.5) -> None:
        if api is None:  # recien aca se importa el servidor MCP (solo uso de lectura)
            from mcp_server.abletonbridge_mcp import server as api  # type: ignore
        self.api, self.client, self.dry_run = api, client, dry_run
        self.sleep, self.max_polls, self.intervalo = sleep, max_polls, intervalo
        self.informe = Informe()
        self._pistas = 0
        self._retornos = 0

    # -- llamadas ---------------------------------------------------------------------------------

    def _llamar(self, nombre: str, **kw: Any) -> Dict[str, Any]:
        self.informe.llamadas.append(Llamada(nombre, kw))
        if self.dry_run:
            return self._simular(nombre, kw)
        return getattr(self.api, nombre)(self.client, **kw)

    def _simular(self, nombre: str, kw: Dict[str, Any]) -> Dict[str, Any]:
        if nombre == "live_track_create":
            self._pistas += 1
            return {"index": self._pistas - 1}
        if nombre == "live_return_list":
            return {"returns": [], "count": 0}
        if nombre == "live_return_create":
            self._retornos += 1
            return {"index": self._retornos - 1}
        if nombre == "live_device_insert":
            return {"index": 0}
        if nombre == "live_clip_place_audio":
            return {"ok": True, "clips": [{"span": kw.get("length_beats") or 8.0}], "warnings": []}
        if nombre == "live_utility_ensure_last":
            return {"target": {"device": "<Utility>", "param": "Output"}}
        if nombre == "live_locator_status":
            return {"pending": 0, "errors": []}
        if nombre == "live_automation_record":
            return {"phase": "done", "errors": []}
        return {"ok": True}

    def _avisar(self, texto: str) -> None:
        self.informe.advertencias.append(texto)

    # -- flujo ------------------------------------------------------------------------------------

    def ejecutar(self, plan: Plan) -> Informe:
        self.plan = plan
        self._llamar("live_song_set", tempo=plan.meta["tempo"])
        self._preparar_retornos()
        self._preparar_pistas()
        self._dispositivos()
        self._mezcla()
        self._clips()
        self._locators()
        self._utilities()
        self._automatizacion()
        return self.informe

    def _preparar_retornos(self) -> None:
        deseados = [(a.datos["id"], a.datos["nombre"]) for a in self.plan.de_tipo(RETORNO)]
        existentes = [r["name"] for r in self._llamar("live_return_list").get("returns", [])]
        for _, nombre in deseados:
            if not any(nombre in e for e in existentes):
                self._llamar("live_return_create", name=nombre)
        listado = [r["name"] for r in self._llamar("live_return_list").get("returns", [])]
        # el indice de envio de cada retorno del plan (Live suele prefijar el nombre: "C-C-HALL")
        self.ret_idx: Dict[int, int] = {}
        for pos, (_, nombre) in enumerate(deseados):
            self.ret_idx[pos] = next((i for i, e in enumerate(listado) if nombre in e), pos)

    def _preparar_pistas(self) -> None:
        self.pista: Dict[str, int] = {}
        self.nombre_pista: Dict[str, str] = {}
        for a in self.plan.de_tipo(PISTA):
            idx = self._llamar("live_track_create", kind=a.datos["kind"], name=a.datos["nombre"])["index"]
            for rol in a.datos["roles"]:
                self.pista[rol] = idx
                self.nombre_pista[rol] = a.datos["nombre"]

    def _track(self, rol: str) -> Any:
        return "master" if rol == "master" else self.pista[rol]

    def _seguro(self, que: str, nombre: str, **kw: Any) -> Optional[Dict[str, Any]]:
        """Llamada de configuracion que puede fallar (param inexistente, plugin ausente): se informa y sigue."""
        try:
            return self._llamar(nombre, **kw)
        except Exception as exc:  # noqa: BLE001 - el puente lanza varios tipos de error
            self._avisar("%s: %s" % (que, exc))
            return None

    def _aplicar_valores(self, rol: str, nombre: str, d: Dict[str, Any], track: Any, device: Any) -> None:
        """params (display) e items cuantizados (nombre EXACTO -> crudo) de un device ya insertado."""
        def poner(param: str, **valor: Any) -> None:
            if rol == "master":
                self._seguro("%s / %s" % (nombre, param), "live_master_device_set_param",
                             device=device, name=param, **valor)
            else:
                self._seguro("%s en %s / %s" % (nombre, rol, param), "live_device_set_param",
                             track=track, device=device, name=param, **valor)
        for param, v in d.get("params", {}).items():
            poner(param, display=v)
        for param, item in d.get("items", {}).items():
            try:
                poner(param, value=valor_item(nombre, param, item))
            except ItemDesconocido as exc:
                self._avisar("%s en %s: %s" % (nombre, rol or "master", exc))
        for texto in d.get("a_mano", []):
            self._avisar("%s en %s: a mano: %s" % (nombre, rol or "master", texto))

    def _dispositivos(self) -> None:
        self.disp: Dict[Tuple[str, str], int] = {}
        # la cadena se arma en el orden de F4 sec. 6 (EQ -> filtro -> dinamica -> saturacion); sort estable
        pendientes = [a for a in self.plan.acciones
                      if a.tipo in (DISPOSITIVO, SIDECHAIN) and not a.datos.get("ultimo")]
        for a in sorted(pendientes, key=lambda x: x.datos.get("orden", 50)):
            d = a.datos
            if a.tipo == SIDECHAIN:
                nombre = d["dispositivo"]
                idx = self._llamar("live_device_insert", track=self.pista[a.rol], name=nombre)["index"]
                self._llamar("live_compressor_set_sidechain", track=self.pista[a.rol], device=idx,
                             source_track_name=d["fuente"])
                self._aplicar_valores(a.rol, nombre, d, self.pista[a.rol], idx)
                continue
            if a.rol == "master":
                self._seguro("master / %s" % d["nombre"], "live_master_device_insert", name=d["nombre"])
                idx, track = d["nombre"], None
            else:
                r = self._seguro("%s en %s" % (d["nombre"], a.rol), "live_device_insert",
                                 track=self.pista[a.rol], name=d["nombre"])
                if r is None:
                    continue
                idx, track = r["index"], self.pista[a.rol]
                self.disp[(a.rol, d["nombre"])] = idx
                if d.get("cargar_muestra"):
                    self._llamar("live_simpler_load", track=track, device=idx,
                                 path=self.plan.elementos[a.rol]["ruta"], playback_mode=PLAYBACK_ONE_SHOT)
            if d.get("plugin"):
                self._avisar("%s en %s: plugin de terceros (reemplaza %s); sus valores van a mano (equivale a %s)" % (
                    d["nombre"], a.rol or "master", d["reemplaza"], d.get("equivale")))
            else:
                self._aplicar_valores(a.rol, d["nombre"], d, track, idx)
            if d.get("nota"):
                self._avisar("%s en %s: %s (a mano si el puente no lo expone)" % (
                    d["nombre"], a.rol or "master", d["nota"]))

    def _mezcla(self) -> None:
        for a in self.plan.de_tipo(MEZCLA):
            self._llamar("live_track_set_mixer", track=self.pista[a.rol], volume_db=a.datos["volumen_db"])
            for k, db in a.datos["envios"].items():
                self._llamar("live_track_set_send", track=self.pista[a.rol], send=self.ret_idx[int(k)], db=db)

    # -- clips ------------------------------------------------------------------------------------

    def _warp(self, rol: str, a: Accion) -> Optional[int]:
        nombre = a.datos.get("warp") or self.plan.elementos[rol].get("warp")
        return WARP_MODES[nombre] if nombre else None

    def _clips(self) -> None:
        self.spans: Dict[Tuple[str, Optional[int]], float] = {}
        acciones = [a for a in self.plan.acciones if a.tipo in (CLIP_LOOP, MIDI, CLIP_ONESHOT)]
        for a in sorted(acciones, key=lambda x: (self.pista[x.rol], x.inicio)):
            if a.tipo == CLIP_LOOP:
                self._colocar(a, a.rol, a.inicio, a.fin - a.inicio)
            elif a.tipo == MIDI:
                r = self._llamar("live_clip_create_midi", track=self.pista[a.rol], start_beat=a.inicio,
                                 length_beats=a.fin - a.inicio, notes=a.datos["notas"])
                if r.get("ok") is False:
                    self._avisar("midi %s %s: %s" % (a.rol, a.inicio, r.get("warnings")))
            else:
                self._oneshot(a)

    def _colocar(self, a: Accion, rol: str, inicio: float, largo: float) -> Dict[str, Any]:
        el = self.plan.elementos[rol]
        r = self._llamar("live_clip_place_audio", track=self.pista[rol], path=a.datos.get("ruta") or el["ruta"],
                         start_beat=inicio,
                         length_beats=largo, warp_mode=self._warp(rol, a), pitch_coarse=a.datos.get("pitch", el["pitch"]))
        if r.get("ok") is False:
            self._avisar("clip %s en beat %g: %s" % (rol, inicio, r.get("warnings")))
        return r

    def _oneshot(self, a: Accion) -> None:
        el = self.plan.elementos[a.rol]
        warp = self._warp(a.rol, a)
        ruta = a.datos.get("ruta") or el["ruta"]
        clave = (ruta, warp)
        if clave not in self.spans:
            if self.dry_run and el.get("natural_beats") and ruta == el["ruta"]:
                self.spans[clave] = el["natural_beats"]
            else:
                r = self._llamar("live_clip_place_audio", track=self.pista[a.rol], path=ruta,
                                 start_beat=MEDIR_EN_BEAT, length_beats=MEDIR_LARGO, warp_mode=warp)
                self.spans[clave] = float(r["clips"][0]["span"])
                self._llamar("live_clip_delete_range", track=self.pista[a.rol], start_beat=MEDIR_EN_BEAT,
                             end_beat=MEDIR_EN_BEAT + MEDIR_LARGO)
        span = self.spans[clave]
        inicio = a.inicio - span if a.datos["ancla"] == "fin" else a.inicio
        if inicio < 0:
            self._avisar("one-shot %s no entra: terminaria en el beat %g con %g de largo" % (a.rol, a.inicio, span))
            return
        self._colocar(a, a.rol, inicio, span)

    # -- locators, utilities, automatizacion ----------------------------------------------------------

    def _locators(self) -> None:
        items = [{"time": a.inicio, "name": a.datos["nombre"]} for a in self.plan.de_tipo(LOCATOR)]
        if not items:
            return
        self._llamar("live_locator_set_many", items=items)
        for i in range(self.max_polls):
            st = self._llamar("live_locator_status")
            if not st.get("pending"):
                if st.get("errors"):
                    self._avisar("locators con error: %s" % st["errors"])
                return
            self.sleep(self.intervalo)
        self._avisar("los locators seguian pendientes tras %d sondeos" % self.max_polls)

    def _utilities(self) -> None:
        self.objetivo_utility: Dict[str, Any] = {}
        for a in self.plan.de_tipo(DISPOSITIVO):
            if a.datos.get("ultimo"):
                r = self._llamar("live_utility_ensure_last", track=self._track(a.rol))
                self.objetivo_utility[a.rol] = r["target"]
                if a.datos.get("items") or a.datos.get("params"):   # p. ej. Bass Mono de los graves
                    self._aplicar_valores(a.rol, "Utility", a.datos, self._track(a.rol), r["target"]["device"])

    def _automatizacion(self) -> None:
        lanes = self.plan.de_tipo(AUTOMATIZACION)
        for n, pasada in enumerate(agrupar_pasadas(lanes), start=1):
            pedidas = [self._lane(l) for l in pasada.lanes]
            for i in range(0, len(pedidas), MAX_LANES_POR_LLAMADA):
                st = self._llamar("live_automation_record", start_beat=pasada.inicio, end_beat=pasada.fin,
                                  lanes=pedidas[i:i + MAX_LANES_POR_LLAMADA], preroll_beats=PREROLL_BEATS)
                if st.get("phase") != "done" or st.get("errors"):
                    self._avisar("pasada %d: fase %s, errores %s" % (n, st.get("phase"), st.get("errors")))

    def _lane(self, a: Accion) -> Dict[str, Any]:
        objetivo = a.datos["objetivo"]
        if isinstance(objetivo, dict) and "send" in objetivo:   # posicion en el plan -> indice real del retorno
            objetivo = {"send": self.ret_idx[objetivo["send"]]}
        elif isinstance(objetivo, dict) and objetivo["device"] == "Utility":
            objetivo = self.objetivo_utility[a.rol]
        return {"track": self._track(a.rol), "target": objetivo, "points": a.datos["puntos"]}
