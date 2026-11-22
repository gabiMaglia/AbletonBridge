"""Plan: el timeline serializado (JSON para la maquina, Markdown para Gabriel y el orquestador)."""
import json
from collections import Counter, OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .model import (AUTOMATIZACION, CLIP_LOOP, CLIP_ONESHOT, DECISION, DISPOSITIVO, LOCATOR, MEZCLA, MIDI,
                    PISTA, RETORNO, SIDECHAIN, Accion)
from .rules import Contexto, generar_timeline

HOLD = 0.01  # beats: punto de sostenido antes de que arranque una lane fusionada


@dataclass
class Plan:
    meta: Dict[str, Any]
    secciones: List[Dict[str, Any]]
    elementos: Dict[str, Dict[str, Any]]
    acciones: List[Accion] = field(default_factory=list)

    def de_tipo(self, tipo: str) -> List[Accion]:
        return [a for a in self.acciones if a.tipo == tipo]


def crear_plan(ctx: Contexto, nombre: str, plantilla: Optional[str] = None) -> Plan:
    tl = generar_timeline(ctx)
    p = ctx.perfil
    return Plan(
        meta={"nombre": nombre, "perfil": p.id, "perfil_version": p.version, "plantilla": plantilla,
              "tempo": ctx.tempo, "total_compases": ctx.estructura.total_compases,
              # reglas marcadas `experimental` en el perfil y si quedaron activas en este plan
              "experimentales": {n: bool(ctx.reglas_experimentales or r.get("activa_por_defecto", False))
                                 for n, r in p.datos["reglas"].items() if r.get("experimental")},
              "plugins": list(ctx.plugins)},
        secciones=[{"id": s.id, "tipo": s.tipo, "inicio": s.inicio, "compases": s.compases,
                    "suma": [_nombre(i) for i in s.spec.get("suma", [])],
                    "quita": [_nombre(i) for i in s.spec.get("quita", [])],
                    "solo": s.spec.get("solo")} for s in ctx.estructura.secciones],
        elementos={r: {"ruta": e.ruta, "warp": e.warp or p.rol(r).get("warp"), "pitch": e.pitch,
                       "natural_beats": e.natural_beats, "alternativas": list(e.alternativas)} for r, e in ctx.elementos.items()},
        acciones=tl.acciones,
    )


def _nombre(item: Any) -> str:
    if isinstance(item, dict):
        return "%s (desde c.%s)" % (item["rol"], item.get("desde"))
    return item


# --- JSON ----------------------------------------------------------------------------------------

def plan_a_json(plan: Plan) -> str:
    return json.dumps({"meta": plan.meta, "secciones": plan.secciones, "elementos": plan.elementos,
                       "acciones": [a.__dict__ for a in plan.acciones]}, indent=1, ensure_ascii=False)


def plan_desde_json(texto: str) -> Plan:
    """Reconstruye el plan; cada Accion se re-valida (una lane de volume falla aca, D-15)."""
    d = json.loads(texto)
    return Plan(meta=d["meta"], secciones=d["secciones"], elementos=d["elementos"],
                acciones=[Accion(**a) for a in d["acciones"]])


# --- pasadas de grabacion ------------------------------------------------------------------------

@dataclass
class Pasada:
    inicio: float
    fin: float
    lanes: List[Accion]

    def duracion_s(self, tempo: float) -> float:
        return (self.fin - self.inicio) * 60.0 / tempo


def _fusionar(lanes: List[Accion]) -> List[Accion]:
    """Lanes del mismo (rol, destino) en una pasada: una sola, sosteniendo el valor entre tramos."""
    grupos: "OrderedDict[Any, List[Accion]]" = OrderedDict()
    for ln in sorted(lanes, key=lambda x: x.inicio):
        grupos.setdefault((ln.rol, repr(ln.datos["objetivo"])), []).append(ln)
    out = []
    for grupo in grupos.values():
        if len(grupo) == 1:
            out.append(grupo[0])
            continue
        pts: List[List[Any]] = []
        for ln in grupo:
            nuevos = [list(p) for p in ln.datos["puntos"]]
            if pts and nuevos[0][0] - HOLD > pts[-1][0]:
                pts.append([round(nuevos[0][0] - HOLD, 4), pts[-1][1]])
            pts.extend(nuevos)
        out.append(Accion(AUTOMATIZACION, grupo[0].rol, pts[0][0], pts[-1][0],
                          {"objetivo": grupo[0].datos["objetivo"], "puntos": pts}, grupo[0].regla, grupo[0].por_que))
    return out


def agrupar_pasadas(lanes: List[Accion]) -> List[Pasada]:
    """Una pasada de grabacion por rango contiguo (las lanes que se pisan van juntas)."""
    pasadas: List[Pasada] = []
    for ln in sorted(lanes, key=lambda x: (x.inicio, x.fin)):
        if pasadas and ln.inicio < pasadas[-1].fin:
            pasadas[-1].lanes.append(ln)
            pasadas[-1].fin = max(pasadas[-1].fin, ln.fin)
        else:
            pasadas.append(Pasada(ln.inicio, ln.fin, [ln]))
    for p in pasadas:
        p.lanes = _fusionar(p.lanes)
    return pasadas


# --- Markdown ------------------------------------------------------------------------------------

def _pos(beat: float) -> str:
    bar, resto = int(beat // 4) + 1, beat % 4
    return str(bar) if resto == 0 else "%d.%s" % (bar, ("%g" % (resto + 1)))


def _rangos(runs: List[Any]) -> str:
    return ", ".join("%s-%s" % (_pos(a), _pos(b)) for a, b in runs)


def _destino(obj: Any, retornos: Optional[List[str]] = None) -> str:
    if isinstance(obj, dict) and "send" in obj:
        pos = obj["send"]
        return "send %s" % (retornos[pos] if retornos and pos < len(retornos) else pos)
    if isinstance(obj, dict):
        return "%s / %s" % (obj["device"], obj["param"])
    return str(obj)


def _detalle_dispositivo(d: Dict[str, Any]) -> str:
    partes = []
    for clave in ("params", "items"):
        if d.get(clave):
            partes.append(", ".join("%s=%s" % kv for kv in d[clave].items()))
    if d.get("equivale"):
        partes.append("equivale a %s" % d["equivale"])
    return "; ".join(partes) or "-"


def _resumen_valores(pts: List[List[Any]]) -> str:
    vals = [p[1]["display"] if isinstance(p[1], dict) else p[1] for p in pts]
    return "%g .. %g" % (min(vals), max(vals))


def plan_a_markdown(plan: Plan) -> str:
    m = plan.meta
    L: List[str] = []
    L.append("# %s: plan generado (%s %s)" % (m["nombre"], m["perfil"], m["perfil_version"]))
    L.append("")
    L.append("> Generado por `composer` desde el perfil, sin tocar Live. %d BPM, %d compases (%s). "
             "Posiciones como `compás.tiempo` (1-based). **Nunca se automatiza volume (D-15):** "
             "el nivel va en el Output de un Utility al final de la cadena." % (
                 m["tempo"], m["total_compases"], _min_seg(m["total_compases"], m["tempo"])))
    L.append("")
    L.append("## Estructura")
    L.append("")
    L.append("| Compás | Sección | Tipo | Largo | Capas que cambian |")
    L.append("|--------|---------|------|-------|-------------------|")
    for s in plan.secciones:
        cambios = []
        if s["solo"] is not None:
            cambios.append("solo: " + (", ".join(s["solo"]) or "nada"))
        cambios += ["+" + x for x in s["suma"]] + ["-" + x for x in s["quita"]]
        L.append("| %d-%d | %s | %s | %d | %s |" % (s["inicio"], s["inicio"] + s["compases"] - 1, s["id"], s["tipo"],
                                                  s["compases"], ", ".join(cambios)))
    L.append("")

    L.append("## Preparación")
    L.append("")
    L.append("| Pista | Tipo | Roles | Nivel dB | Envíos (retorno: dB) |")
    L.append("|-------|------|-------|----------|----------------------|")
    retornos = [r.datos["nombre"] for r in plan.de_tipo(RETORNO)]
    mezcla = {a.rol: a for a in plan.de_tipo(MEZCLA)}
    for a in plan.de_tipo(PISTA):
        mz = mezcla[a.rol].datos
        envios = ", ".join("%s: %g" % (retornos[int(k)], v) for k, v in mz["envios"].items())
        L.append("| %s | %s | %s | %g | %s |" % (a.datos["nombre"], a.datos["kind"], ", ".join(a.datos["roles"]),
                                                 mz["volumen_db"], envios or "-"))
    L.append("")
    L.append("Retornos: " + ", ".join(retornos) + ".")
    L.append("")
    L.append("| Dispositivo | Rol | Parámetros fijos | Nota |")
    L.append("|-------------|-----|------------------|------|")
    for a in plan.de_tipo(DISPOSITIVO) + plan.de_tipo(SIDECHAIN):
        d = a.datos
        nombre = d.get("nombre") or d["dispositivo"]
        extra = "último en la cadena (D-15)" if d.get("ultimo") else d.get("nota", "")
        if a.tipo == SIDECHAIN:
            extra = "sidechain desde %s" % d["fuente"]
        if d.get("plugin"):
            extra = "plugin de terceros (reemplaza %s): valores a mano" % d["reemplaza"]
        if d.get("a_mano"):
            extra = "a mano: " + "; ".join(d["a_mano"])
        L.append("| %s | %s | %s | %s |" % (nombre, a.rol or "master", _detalle_dispositivo(d), extra))
    L.append("")

    L.append("## Decisiones de arreglo")
    L.append("")
    L.append("| Compás | Regla | Qué |")
    L.append("|--------|-------|-----|")
    for a in sorted(plan.de_tipo(DECISION), key=lambda x: x.inicio):
        L.append("| %s | %s | %s |" % (_pos(a.inicio), a.regla, a.datos["que"]))
    L.append("")
    for nombre, activa in m.get("experimentales", {}).items():
        L.append("Regla experimental `%s`: %s." % (nombre, "ACTIVA" if activa else "desactivada (sin instrumento asignado)"))
    if m.get("plugins"):
        L.append("Plugins de terceros pedidos: %s." % ", ".join(m["plugins"]))
    L.append("")

    L.append("## Capas (clips de loop)")
    L.append("")
    L.append("| Rol | Compases | Warp | Pitch |")
    L.append("|-----|----------|------|-------|")
    capas: "OrderedDict[str, List[Any]]" = OrderedDict()
    for a in plan.de_tipo(CLIP_LOOP):
        if a.regla == "presencia":
            capas.setdefault(a.rol, []).append((a.inicio, a.fin))
    for rol, runs in capas.items():
        el = plan.elementos[rol]
        L.append("| %s | %s | %s | %s |" % (rol, _rangos(runs), el["warp"], el["pitch"]))
    L.append("")

    L.append("## Eventos de arreglo")
    L.append("")
    kicks = [a for a in plan.de_tipo(MIDI) if a.rol == "kick"]
    if kicks:
        notas = sum(len(a.datos["notas"]) for a in kicks)
        L.append("Kick: %d clips MIDI, %d notas; huecos por nivel de frase (regla `huecos_kick`)." % (len(kicks), notas))
        L.append("")
    L.append("| Compás | Rol | Qué | Regla |")
    L.append("|--------|-----|-----|-------|")
    eventos = [a for a in plan.acciones if a.tipo in (CLIP_ONESHOT, MIDI, LOCATOR)
               or (a.tipo == CLIP_LOOP and a.regla != "presencia")]
    for a in sorted((e for e in eventos if e.rol != "kick"), key=lambda x: (x.inicio, x.rol)):
        if a.tipo == LOCATOR:
            que = "locator '%s'" % a.datos["nombre"]
        elif a.tipo == CLIP_ONESHOT:
            que = "one-shot que %s aca" % ("termina" if a.datos["ancla"] == "fin" else "empieza")
        elif a.tipo == MIDI:
            que = "%d notas MIDI hasta %s" % (len(a.datos["notas"]), _pos(a.fin))
        else:
            que = "loop %s-%s" % (_pos(a.inicio), _pos(a.fin))
        L.append("| %s | %s | %s | %s |" % (_pos(a.inicio), a.rol or "-", que, a.regla))
    L.append("")

    lanes = plan.de_tipo(AUTOMATIZACION)
    L.append("## Automatización")
    L.append("")
    L.append("| Rol | Destino | Compases | Puntos | Valores | Regla |")
    L.append("|-----|---------|----------|--------|---------|-------|")
    for a in lanes:
        L.append("| %s | %s | %s-%s | %d | %s | %s |" % (a.rol, _destino(a.datos["objetivo"], retornos), _pos(a.inicio),
                                                          _pos(a.fin), len(a.datos["puntos"]),
                                                          _resumen_valores(a.datos["puntos"]), a.regla))
    L.append("")
    L.append("## Pasadas de grabación")
    L.append("")
    L.append("`automation.record` graba en tiempo real: una pasada por rango contiguo.")
    L.append("")
    L.append("| # | Compases | Duración estimada | Lanes |")
    L.append("|---|----------|-------------------|-------|")
    total = 0.0
    for i, p in enumerate(agrupar_pasadas(lanes), start=1):
        seg = p.duracion_s(m["tempo"])
        total += seg
        L.append("| %d | %s-%s | %s | %d |" % (i, _pos(p.inicio), _pos(p.fin), _min_seg_s(seg), len(p.lanes)))
    L.append("")
    L.append("Total de grabación: %s." % _min_seg_s(total))
    L.append("")

    L.append("## Reglas aplicadas")
    L.append("")
    L.append("| Regla | Acciones |")
    L.append("|-------|----------|")
    for regla, n in sorted(Counter(a.regla for a in plan.acciones).items()):
        L.append("| %s | %d |" % (regla, n))
    L.append("")
    return "\n".join(L)


def _min_seg(compases: int, tempo: float) -> str:
    return _min_seg_s(compases * 4 * 60.0 / tempo)


def _min_seg_s(seg: float) -> str:
    total = int(round(seg))
    return "%d:%02d" % (total // 60, total % 60)
