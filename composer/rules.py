"""Reglas de arreglo: funciones puras (estructura + elementos + perfil) -> acciones como dato.

Nada acá toca Live. Convenciones:
- Los tiempos son beats absolutos; los rangos de presencia son [inicio, fin).
- D-15: el nivel se automatiza SOLO en el "Output" de un Utility ultimo en la cadena; Accion lo exige.
- Un rol sin elemento en el set se omite en silencio (el tema se arma con lo que hay).
"""
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .model import (AUTOMATIZACION, CLIP_LOOP, CLIP_ONESHOT, DISPOSITIVO, LOCATOR, MEZCLA, MIDI, PISTA,
                    RETORNO, SIDECHAIN, Accion, Elemento, Run, Timeline)
from .profile import Perfil
from .structure import BEATS_POR_COMPAS, Estructura, Seccion, compas_a_beat, nivel_de_frase

OBJ_UTILITY = {"device": "Utility", "param": "Output"}
OBJ_FILTRO = {"device": "Auto Filter", "param": "Frequency"}
FIN_DE_LANE = 0.1  # beats antes del borde: el ultimo valor se alcanza justo antes de cortar


@dataclass
class Contexto:
    perfil: Perfil
    estructura: Estructura
    elementos: Dict[str, Elemento]
    tempo: float = 130.0

    def tiene(self, rol: str) -> bool:
        return rol in self.elementos


def D(valor: float) -> Dict[str, float]:
    return {"display": valor}


def _num(v: float) -> Any:
    """Enteros como int (mas legible en el plan) y el resto tal cual."""
    return int(v) if float(v).is_integer() else round(v, 3)


# ---------------------------------------------------------------------------------------------
# Intervalos
# ---------------------------------------------------------------------------------------------

def _normalizar(runs: Iterable[Run]) -> List[Run]:
    out: List[Run] = []
    for a, b in sorted(r for r in runs if r[1] > r[0]):
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def _restar(runs: List[Run], hueco: Run) -> List[Run]:
    x, y = hueco
    out: List[Run] = []
    for a, b in runs:
        if b <= x or a >= y:
            out.append((a, b))
            continue
        if a < x:
            out.append((a, x))
        if b > y:
            out.append((y, b))
    return out


def _cubre(runs: List[Run], a: float, b: float) -> bool:
    return any(r0 <= a and b <= r1 for r0, r1 in runs)


# ---------------------------------------------------------------------------------------------
# Presencia de capas
# ---------------------------------------------------------------------------------------------

def _item(item: Any) -> Tuple[str, Optional[int]]:
    if isinstance(item, dict):
        return item["rol"], item.get("desde")
    return item, None


def presencia_base(ctx: Contexto) -> Dict[str, List[Run]]:
    """Cuando suena cada rol segun la plantilla (suma/quita/solo/ocasionales), sin retoques de regla."""
    activos: Dict[str, float] = {}
    runs: Dict[str, List[Run]] = defaultdict(list)

    def cerrar(rol: str, beat: float) -> None:
        if rol in activos:
            ini = activos.pop(rol)
            if beat > ini:
                runs[rol].append((ini, beat))

    def abrir(rol: str, beat: float) -> None:
        activos.setdefault(rol, beat)

    for sec in ctx.estructura.secciones:
        spec = sec.spec
        if "solo" in spec:
            for rol in list(activos):
                cerrar(rol, sec.beat_inicio)
        for item in spec.get("quita", []):
            rol, desde = _item(item)
            cerrar(rol, sec.beat_inicio + ((desde - 1) * BEATS_POR_COMPAS if desde else 0))
        for item in list(spec.get("solo", [])) + list(spec.get("suma", [])):
            rol, desde = _item(item)
            abrir(rol, sec.beat_inicio + ((desde - 1) * BEATS_POR_COMPAS if desde else 0))
        for occ in spec.get("ocasionales", []):
            if occ.get("fraseo") != "ultimos_8_de_16":
                raise ValueError("fraseo desconocido: %r" % occ.get("fraseo"))
            for bar in range(sec.inicio, sec.fin + 1):
                if (bar - 1) % 16 >= 8:
                    runs[occ["rol"]].append((compas_a_beat(bar), compas_a_beat(bar + 1)))
    for rol in list(activos):
        cerrar(rol, ctx.estructura.beat_final)
    return {rol: _normalizar(r) for rol, r in runs.items() if ctx.tiene(rol)}


def _entradas_puente(ctx: Contexto, sec: Seccion) -> List[Tuple[str, float, float, bool]]:
    """[(rol, entrada, salida, es_la_primera)] del puente: entran de a poco cada `paso` compases."""
    cfg = ctx.perfil.regla("puente")
    orden = [r for r in cfg["orden_entrada"] if ctx.tiene(r)]
    out = []
    for i, rol in enumerate(orden):
        bar = sec.inicio + i * cfg["paso_entrada_compases"]
        if bar > sec.fin:
            continue
        salida = sec.beat_fin - cfg.get("salidas_antes_del_final", {}).get(rol, 0) * BEATS_POR_COMPAS
        out.append((rol, compas_a_beat(bar), salida, i == 0))
    return out


def _presencia_sin_cortes(ctx: Contexto) -> Dict[str, List[Run]]:
    runs = {r: list(v) for r, v in presencia_base(ctx).items()}
    for sec in ctx.estructura.de_tipo("breakdown"):
        cfg = ctx.perfil.regla("puente")
        for rol, entrada, salida, _ in _entradas_puente(ctx, sec):
            runs.setdefault(rol, []).append((entrada, salida))
        for rol in cfg.get("cama", []):
            if ctx.tiene(rol):
                runs.setdefault(rol, []).append((sec.beat_inicio, sec.beat_fin))
    return {r: _normalizar(v) for r, v in runs.items()}


def presencia(ctx: Contexto) -> Dict[str, List[Run]]:
    """Presencia final: base + puente, con los huecos de limite de 32, llamado/respuesta y corte previo."""
    runs = _presencia_sin_cortes(ctx)
    est = ctx.estructura
    # 1) limite de seccion tras una frase de 32: caen rumble y bajo ese compas
    hk = ctx.perfil.regla("huecos_kick")
    for sec in est.secciones[1:]:
        bar = sec.inicio - 1
        if nivel_de_frase(bar) == 32:
            for rol in hk["silencian_en_limite_de_seccion_nivel_32"]:
                if rol in runs:
                    runs[rol] = _restar(runs[rol], (compas_a_beat(bar), compas_a_beat(bar + 1)))
    # 2) llamado y respuesta: el que responde calla en las unidades en que llama la voz
    base = presencia_base(ctx)
    for par in ctx.perfil.regla("llamado_respuesta")["pares"]:
        llama, responde = par["llama"], par["responde"]
        if responde not in runs:
            continue
        unidad = par["unidad_compases"] * BEATS_POR_COMPAS
        for a, b in base.get(llama, []):
            k, t = 0, a
            while t < b:
                if k % 2 == 0:
                    runs[responde] = _restar(runs[responde], (t, min(t + unidad, b)))
                k, t = k + 1, t + unidad
    # 3) anacrusa: antes de un drop sin silencio se corta todo salvo lo conservado
    cp = ctx.perfil.regla("corte_previo_al_drop")
    for sec in est.de_tipo("drop"):
        prev = est.anterior(sec)
        if prev is None or prev.tipo == "silence":
            continue
        hueco = (sec.beat_inicio - cp["beats"], sec.beat_inicio)
        for rol in runs:
            if rol not in cp["conserva"]:
                runs[rol] = _restar(runs[rol], hueco)
    return {r: _normalizar(v) for r, v in runs.items() if v}


# ---------------------------------------------------------------------------------------------
# Clips de loops y MIDI de kick
# ---------------------------------------------------------------------------------------------

def regla_clips_loop(ctx: Contexto, pres: Dict[str, List[Run]]) -> List[Accion]:
    acciones = []
    for rol, runs in pres.items():
        cfg = ctx.perfil.rol(rol)
        if cfg["tipo"] != "loop":
            continue
        el = ctx.elementos[rol]
        for a, b in runs:
            if b - a < 1.0:
                continue
            acciones.append(Accion(CLIP_LOOP, rol, a, b, {"warp": el.warp or cfg.get("warp"), "pitch": el.pitch},
                                   "presencia", "capa segun la plantilla de la seccion"))
    return acciones


def regla_huecos_kick(ctx: Contexto, pres: Dict[str, List[Run]]) -> List[Accion]:
    """Kick en negras; el ultimo compas de cada frase pierde tiempos segun el nivel (8 < 16 < 32)."""
    if not ctx.tiene("kick"):
        return []
    cfg = ctx.perfil.regla("huecos_kick")
    por_nivel = {int(k): set(v) for k, v in cfg["por_nivel"].items()}
    ultimo = ctx.estructura.total_compases
    el = ctx.perfil.rol("kick")
    acciones = []
    for a, b in pres.get("kick", []):
        notas = []
        t = a
        while t < b:
            bar, tiempo = int(t // BEATS_POR_COMPAS) + 1, int(t % BEATS_POR_COMPAS) + 1
            sin_hueco = cfg.get("sin_huecos_en_el_ultimo_compas_del_tema") and bar == ultimo
            if sin_hueco or tiempo not in por_nivel.get(nivel_de_frase(bar), ()):
                notas.append({"pitch": el["nota_midi"], "start": t - a, "duration": 0.5, "velocity": el["velocity"]})
            t += 1.0
        if notas:
            acciones.append(Accion(MIDI, "kick", a, b, {"notas": notas}, "huecos_kick",
                                   "kick en negras; el hueco crece con el nivel de la frase (8 < 16 < 32)"))
    return acciones


def _rampa(v0: float, v1: float, i: int, n: int) -> int:
    return int(round(v0 + (v1 - v0) * i / max(1, n - 1)))


def regla_fills(ctx: Contexto, base: Dict[str, List[Run]]) -> List[Accion]:
    """Fin de frase dentro del groove: snare fill (8), roll corto (16) o roll de compas (32)."""
    cfg = ctx.perfil.regla("fills")
    kick = base.get("kick", [])
    acciones = []
    for bar in range(1, ctx.estructura.total_compases):  # el ultimo compas no tiene frase siguiente
        a, b = compas_a_beat(bar), compas_a_beat(bar + 1)
        nivel = nivel_de_frase(bar)
        if not nivel or not _cubre(kick, a, b):
            continue
        if nivel == 8 and ctx.tiene(cfg["snare_fin_de_8"]["rol"]):
            f = cfg["snare_fin_de_8"]
            v0, v1 = f["velocity"]
            notas = [{"pitch": f["nota_midi"], "start": (f["tiempo_inicio"] - 1) + i * f["paso_beats"],
                      "duration": 0.2, "velocity": _rampa(v0, v1, i, f["notas"])} for i in range(f["notas"])]
            acciones.append(Accion(MIDI, f["rol"], a, b, {"notas": notas}, "fills.snare_fin_de_8",
                                   "fin de frase de 8: 4 semicorcheas en crescendo en el 4.o tiempo"))
        elif nivel in (16, 32):
            f = cfg["roll_fin_de_16" if nivel == 16 else "roll_fin_de_32"]
            if ctx.tiene(f["rol"]):
                acciones.append(Accion(CLIP_LOOP, f["rol"], b - f["beats"], b,
                                       {"warp": ctx.perfil.rol(f["rol"]).get("warp"), "pitch": 0},
                                       "fills.roll_fin_de_%d" % nivel,
                                       "roll de bateria que termina justo en el cambio de frase de %d" % nivel))
    return acciones


def regla_crashes(ctx: Contexto) -> List[Accion]:
    if not ctx.tiene("crash"):
        return []
    cfg = ctx.perfil.regla("crashes")
    acciones = []
    for bar in range(cfg["desde_compas"], ctx.estructura.total_compases + 1, cfg["cada_compases"]):
        sec = ctx.estructura.seccion_en(bar)
        if sec.tipo == "silence" or (sec.tipo in cfg["excluir_dentro_de"] and bar != sec.inicio):
            continue
        acciones.append(Accion(CLIP_ONESHOT, "crash", compas_a_beat(bar), None, {"ancla": "inicio"}, "crashes",
                               "crash en el 1 de cada frase de 16 (no en medio de un breakdown)"))
    return acciones


# ---------------------------------------------------------------------------------------------
# Transiciones: reverses, impactos, downlifters, risers, locators
# ---------------------------------------------------------------------------------------------

def regla_transiciones(ctx: Contexto) -> List[Accion]:
    cfg = ctx.perfil.dato("transiciones")
    est = ctx.estructura
    acciones: List[Accion] = []

    def oneshot(rol: str, beat: float, ancla: str, regla: str, por_que: str) -> None:
        if ctx.tiene(rol):
            acciones.append(Accion(CLIP_ONESHOT, rol, beat, None, {"ancla": ancla}, regla, por_que))

    for sec in est.secciones[1:]:
        prev = est.anterior(sec)
        marca = dict(cfg["al_entrar"].get(sec.tipo, {}))
        if prev.tipo == "silence":
            marca.update(cfg["tras_silencio"])
        elif sec.tipo == "drop":
            marca.update(cfg["drop_sin_silencio"])
            if prev.compases < 8:
                marca.pop("riser_antes", None)
        marca.update(sec.spec.get("transicion", {}))
        b = sec.beat_inicio
        if marca.get("reverse"):
            oneshot("reverse", b, "fin", "transiciones.reverse", "reverse que termina justo en el limite de seccion")
        if marca.get("impacto"):
            oneshot("impacto", b, "inicio", "transiciones.impacto", "impacto en el 1 de la seccion")
        if marca.get("downlifter"):
            oneshot("sweep_down", b, "inicio", "transiciones.downlifter", "barrido hacia abajo al entrar el drop")
        if marca.get("riser_antes"):
            oneshot(marca["riser_antes"], b, "fin", "transiciones.riser", "riser que culmina justo en el limite")
        if sec.tipo == "silence":
            oneshot(cfg["riser_adicional_antes_del_silencio"], b, "fin", "transiciones.riser",
                    "segundo riser que termina en el silencio")
    for sec in est.secciones:
        if sec.tipo not in cfg["reverse_cada_16_en"]:
            continue
        for bar in range(sec.inicio + 1, sec.fin + 1):
            if (bar - 1) % 16 == 0:
                oneshot("reverse", compas_a_beat(bar), "fin", "transiciones.reverse",
                        "reverse al cambiar de frase de 16 dentro del drop")
    return acciones


def regla_locators(ctx: Contexto) -> List[Accion]:
    return [Accion(LOCATOR, "", s.beat_inicio, None, {"nombre": s.id}, "locators", "un locator por seccion")
            for s in ctx.estructura.secciones]


# ---------------------------------------------------------------------------------------------
# Puente: tension continua
# ---------------------------------------------------------------------------------------------

def _lane(rol: str, objetivo: Any, puntos: List[List[Any]], regla: str, por_que: str) -> Accion:
    return Accion(AUTOMATIZACION, rol, puntos[0][0], puntos[-1][0],
                  {"objetivo": objetivo, "puntos": puntos}, regla, por_que)


def _agregar(pts: List[List[Any]], beat: float, valor: Any) -> None:
    if not pts or beat > pts[-1][0]:
        pts.append([beat, valor])


def regla_puente(ctx: Contexto, pres: Dict[str, List[Run]]) -> List[Accion]:
    cfg = ctx.perfil.regla("puente")
    acciones: List[Accion] = []
    for sec in ctx.estructura.de_tipo("breakdown"):
        s, fin = sec.beat_inicio, sec.beat_fin
        entradas = _entradas_puente(ctx, sec)
        swell = cfg["swell_final_db"]
        # fades sobre el Utility (D-15); el primero entra de golpe porque culmina el riser anterior
        for rol, entrada, salida, primera in entradas:
            if primera and cfg["entra_de_golpe_el_primero"] and rol not in swell:
                continue
            pts: List[List[Any]] = [[s, D(0)]]
            if not (primera and cfg["entra_de_golpe_el_primero"]):
                f = cfg["fades"].get(rol, cfg["fade_por_defecto"])
                _agregar(pts, entrada, D(f["desde_db"]))
                _agregar(pts, entrada + f["compases"] * BEATS_POR_COMPAS, D(f.get("hasta_db", 0)))
            if rol in swell:
                _agregar(pts, fin - FIN_DE_LANE, D(swell[rol]))
            _agregar(pts, fin, D(0))
            acciones.append(_lane(rol, dict(OBJ_UTILITY), pts, "puente.fade",
                                  "la entrada sube desde abajo en un Utility (D-15): no entra de golpe"))
            if rol in cfg["reverse_antes_de_la_entrada"] and entrada > s and ctx.tiene("reverse"):
                acciones.append(Accion(CLIP_ONESHOT, "reverse", entrada, None, {"ancla": "fin"},
                                       "puente.reverse", "un reverse trae la entrada"))
        for rol in cfg["cama"]:
            if ctx.tiene(rol):
                pts = [[s, D(cfg["cama_desde_db"][rol])]]
                _agregar(pts, fin - FIN_DE_LANE, D(swell[rol]))
                _agregar(pts, fin, D(0))
                acciones.append(_lane(rol, dict(OBJ_UTILITY), pts, "puente.cama",
                                      "la cama crece en todo el puente y vuelve a 0 dB en el silencio"))
        acciones += _roll_del_puente(ctx, sec)
        acciones += _filtros_del_riser(ctx, sec, pres)
    return acciones


def _roll_del_puente(ctx: Contexto, sec: Seccion) -> List[Accion]:
    cfg = ctx.perfil.regla("puente")["roll_snare"]
    if not ctx.tiene(cfg["rol"]):
        return []
    total = sum(e["compases"] for e in cfg["etapas"]) * BEATS_POR_COMPAS
    if total > sec.compases * BEATS_POR_COMPAS:
        return []
    inicio = sec.beat_fin - total
    notas, cursor = [], inicio
    for e in cfg["etapas"]:
        largo = e["compases"] * BEATS_POR_COMPAS
        n = int(round(largo / e["paso_beats"]))
        v0, v1 = e["velocity"]
        for i in range(n):
            notas.append({"pitch": cfg["nota_midi"], "start": cursor - inicio + i * e["paso_beats"],
                          "duration": min(e["paso_beats"] * 0.8, 0.2), "velocity": _rampa(v0, v1, i, n)})
        cursor += largo
    return [Accion(MIDI, cfg["rol"], inicio, sec.beat_fin, {"notas": notas}, "puente.roll",
                   "roll que acelera (negras, corcheas, semicorcheas, fusas) y termina en el silencio")]


def _filtros_del_riser(ctx: Contexto, sec: Seccion, pres: Dict[str, List[Run]]) -> List[Accion]:
    cfg = ctx.perfil.regla("filtro_sigue_al_riser")
    pc = ctx.perfil.regla("puente")
    w0, w1 = sec.beat_fin - pc["riser_compases"] * BEATS_POR_COMPAS, sec.beat_fin
    acciones: List[Accion] = []
    roll = pc["roll_snare"]["rol"]
    for rol in cfg["roles"]:
        if not ctx.tiene(rol):
            continue
        suena = _cubre(pres.get(rol, []), w0, w1) or (
            rol == roll and ctx.tiene(roll) and sum(e["compases"] for e in pc["roll_snare"]["etapas"]) * 4 <= sec.compases * 4)
        if not suena:
            continue
        cierre = w0 + cfg["cierre_beats"]
        pts: List[List[Any]] = [[w0, D(cfg["abierto_hz"])], [cierre, D(cfg["cerrado_hz"])]]
        curva = list(cfg["curva_hz"]) + [cfg["abierto_hz"]]
        for k, hz in enumerate(curva, start=1):
            _agregar(pts, cierre + (w1 - cierre) * k / len(curva), D(hz))
        acciones.append(_lane(rol, dict(OBJ_FILTRO), pts, "filtro_sigue_al_riser",
                              "cierra rapido al arrancar el riser y abre con su movimiento (curva no recta)"))
    m = pc["filtro_master"]
    mw0 = sec.beat_fin - m["compases"] * BEATS_POR_COMPAS
    pts = [[mw0, D(m["desde_hz"])]]
    _agregar(pts, sec.beat_fin - FIN_DE_LANE, D(m["hasta_hz"]))
    _agregar(pts, sec.beat_fin, D(m["desde_hz"]))
    acciones.append(_lane("master", {"device": m["dispositivo"], "param": m["parametro"]}, pts, "puente.filtro_master",
                          "HP del master sube en los ultimos compases y vuelve a 20 Hz en el silencio"))
    return acciones


# ---------------------------------------------------------------------------------------------
# Movimiento dentro del loop
# ---------------------------------------------------------------------------------------------

def _geom(v0: float, v1: float, i: int, n: int) -> int:
    if n <= 1:
        return int(round(v0))
    return int(round(v0 * (v1 / v0) ** (i / (n - 1))))


def regla_escalera(ctx: Contexto, base: Dict[str, List[Run]]) -> List[Accion]:
    """Diente de sierra por frase de 8: cada frase llega mas lejos que la anterior."""
    cfg = ctx.perfil.regla("escalera_filtro")
    frase = cfg["frase_compases"] * BEATS_POR_COMPAS
    acciones = []
    for rol in cfg["roles"]:
        if not ctx.tiene(rol):
            continue
        for k, (a, b) in enumerate(base.get(rol, [])):
            n = int((b - a) // frase)
            if n < 1:
                continue
            tramo = cfg["tramos"][min(k, len(cfg["tramos"]) - 1)]
            pts: List[List[Any]] = []
            for i in range(n):
                p = a + i * frase
                pts.append([p, D(_geom(*tramo["lo_hz"], i, n))])
                pts.append([p + frase - FIN_DE_LANE, D(_geom(*tramo["hi_hz"], i, n))])
            acciones.append(_lane(rol, {"device": cfg["dispositivo"], "param": cfg["parametro"]}, pts,
                                  "escalera_filtro", "cada frase de 8 el filtro llega mas lejos (criterio de Gabriel)"))
    return acciones


def regla_apertura_lead(ctx: Contexto, base: Dict[str, List[Run]]) -> List[Accion]:
    cfg = ctx.perfil.regla("apertura_lead")
    acciones = []
    for rol in cfg["roles"]:
        if not ctx.tiene(rol):
            continue
        for a, b in base.get(rol, []):
            hz = cfg["puntos_hz"]
            pts: List[List[Any]] = []
            for i, v in enumerate(hz):
                t = a + (b - a) * i / (len(hz) - 1)
                _agregar(pts, min(t, b - FIN_DE_LANE) if i == len(hz) - 1 else t, D(v))
            acciones.append(_lane(rol, {"device": cfg["dispositivo"], "param": cfg["parametro"]}, pts,
                                  "apertura_lead", "el filtro abre en todo el tramo del lead"))
    return acciones


def regla_entrada_filtrada(ctx: Contexto, base: Dict[str, List[Run]]) -> List[Accion]:
    cfg = ctx.perfil.regla("entrada_filtrada")
    acciones = []
    for rol in cfg["roles"]:
        for a, b in base.get(rol, []):
            largo = cfg["compases"] * BEATS_POR_COMPAS
            if ctx.estructura.seccion_en(int(a // 4) + 1).tipo == "breakdown" or b - a < largo:
                continue
            acciones.append(_lane(rol, {"device": cfg["dispositivo"], "param": cfg["parametro"]},
                                  [[a, D(cfg["desde_hz"])], [a + largo, D(cfg["hasta_hz"])]],
                                  "entrada_filtrada", "elemento nuevo: entra filtrado y abre en 8 compases"))
    return acciones


def regla_pan(ctx: Contexto, runs: Dict[str, List[Run]]) -> List[Accion]:
    cfg = ctx.perfil.regla("movimiento_pan")
    acciones = []
    for it in cfg["items"]:
        rol = it["rol"]
        paso = it["cada_compases"] * BEATS_POR_COMPAS

        def valor(t: float) -> float:
            return it["fase"] * it["amplitud"] * (1 if int(t // paso) % 2 == 0 else -1)

        for a, b in runs.get(rol, []):
            pts: List[List[Any]] = [[a, valor(a)]]
            g = (int(a // paso) + 1) * paso
            while g < b:
                _agregar(pts, g, valor(g))
                g += paso
            _agregar(pts, b, 0.0)
            acciones.append(_lane(rol, "pan", pts, "movimiento_pan",
                                  "paneo que alterna cada %d compases (dialogo entre capas)" % it["cada_compases"]))
    return acciones


# ---------------------------------------------------------------------------------------------
# Preparacion: pistas, mezcla, dispositivos, sidechain
# ---------------------------------------------------------------------------------------------

def _receta_filtro(ctx: Contexto, rol: str) -> Tuple[Dict[str, Any], Optional[str]]:
    r = ctx.perfil
    if rol in r.regla("filtro_sigue_al_riser")["roles"]:
        c = r.regla("filtro_sigue_al_riser")
        return c["receta"], "Filter Type: %s (confirmar el nombre del param en el catalogo)" % c["receta"]["tipo"]
    for nombre in ("escalera_filtro", "apertura_lead", "entrada_filtrada"):
        if rol in r.regla(nombre)["roles"]:
            return r.regla(nombre)["receta"], None
    return {}, None


def regla_setup(ctx: Contexto, timeline: Timeline) -> List[Accion]:
    """Retornos, pistas, mezcla estatica, dispositivos y sidechain para lo que el timeline usa."""
    p = ctx.perfil
    usados = {a.rol for a in timeline.acciones if a.tipo in (CLIP_LOOP, CLIP_ONESHOT, MIDI)}
    acciones = [Accion(RETORNO, "", 0.0, None, {"id": r["id"], "nombre": r["nombre"]}, "setup", "retornos del tema")
                for r in p.dato("retornos")]
    ids_ret = [r["id"] for r in p.dato("retornos")]
    pistas: Dict[str, List[str]] = {}
    for rol in p.dato("elementos"):
        if rol in usados and ctx.tiene(rol):
            pistas.setdefault(p.rol(rol)["pista"], []).append(rol)
    for nombre, roles in pistas.items():
        primero = p.rol(roles[0])
        kind = "midi" if primero["tipo"] == "midi" else "audio"
        acciones.append(Accion(PISTA, roles[0], 0.0, None, {"nombre": nombre, "kind": kind, "roles": roles},
                               "setup", "una pista por grupo de roles"))
        envios = {ids_ret.index(k): v for k, v in primero.get("envios", {}).items()}
        acciones.append(Accion(MEZCLA, roles[0], 0.0, None,
                               {"volumen_db": primero["nivel_db"], "envios": {str(k): v for k, v in envios.items()}},
                               "setup", "mezcla inicial estatica (el fader queda libre, D-15)"))
        if kind == "midi":
            acciones.append(Accion(DISPOSITIVO, roles[0], 0.0, None, {"nombre": "Simpler", "cargar_muestra": True},
                                   "setup", "Simpler one-shot para el rol MIDI"))
    # filtros: uno por (rol, destino) con lane de Auto Filter, con su receta fija
    vistos = set()
    for a in timeline.de_tipo(AUTOMATIZACION):
        obj = a.datos["objetivo"]
        if isinstance(obj, dict) and obj["device"] == "Auto Filter" and a.rol not in vistos:
            vistos.add(a.rol)
            params, nota = _receta_filtro(ctx, a.rol) if a.rol != "master" else ({}, "HP en el master")
            datos: Dict[str, Any] = {"nombre": "Auto Filter"}
            if params:
                datos["params"] = {"Resonance": params["resonancia_pct"], "Drive": params["drive_pct"]}
            if nota:
                datos["nota"] = nota
            acciones.append(Accion(DISPOSITIVO, a.rol, 0.0, None, datos, "setup",
                                   "Auto Filter con la receta de resonancia/drive (valores fijos)"))
    # sidechain al kick
    sc = p.dato("mezcla", "sidechain")
    if ctx.tiene(sc["fuente_track"]) and sc["fuente_track"] in usados:
        for rol in sc["destinos"]:
            if rol in usados:
                acciones.append(Accion(SIDECHAIN, rol, 0.0, None,
                                       {"fuente": p.rol(sc["fuente_track"])["pista"], "dispositivo": sc["dispositivo"]},
                                       "setup", "rumble y bajo bombean con el kick"))
    # Utility ULTIMO para toda lane de nivel (D-15)
    for rol in sorted({a.rol for a in timeline.de_tipo(AUTOMATIZACION) if a.datos["objetivo"] == OBJ_UTILITY}):
        acciones.append(Accion(DISPOSITIVO, rol, 0.0, None, {"nombre": "Utility", "ultimo": True}, "setup",
                               "D-15: el nivel se automatiza en un Utility al final de la cadena"))
    return acciones


# ---------------------------------------------------------------------------------------------
# Orquestador
# ---------------------------------------------------------------------------------------------

def generar_timeline(ctx: Contexto) -> Timeline:
    base = presencia_base(ctx)
    pres = presencia(ctx)
    tl = Timeline()
    tl.agregar(*regla_clips_loop(ctx, pres))
    tl.agregar(*regla_huecos_kick(ctx, pres))
    tl.agregar(*regla_fills(ctx, base))
    tl.agregar(*regla_crashes(ctx))
    tl.agregar(*regla_transiciones(ctx))
    tl.agregar(*regla_locators(ctx))
    tl.agregar(*regla_puente(ctx, pres))
    tl.agregar(*regla_escalera(ctx, base))
    tl.agregar(*regla_apertura_lead(ctx, base))
    tl.agregar(*regla_entrada_filtrada(ctx, base))
    tl.agregar(*regla_pan(ctx, _presencia_sin_cortes(ctx)))
    tl.agregar(*regla_setup(ctx, tl))
    tl.ordenar()
    return tl
