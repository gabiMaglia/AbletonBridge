"""T-015b: respuestas del PO (fines de 32, FX variados, entrada filtrada, ecos de voz, plantilla de mezcla)."""
import pytest

from composer import rules
from composer.model import (AUTOMATIZACION, CLIP_LOOP, CLIP_ONESHOT, DECISION, DISPOSITIVO, MEZCLA, MIDI,
                            SIDECHAIN)

AF = {"device": "Auto Filter", "param": "Frequency"}


def B(bar):
    return (bar - 1) * 4.0


def S(id_, tipo, n, **kw):
    return {"id": id_, "tipo": tipo, "compases": n, **kw}


def lanes(tl, rol, objetivo):
    return sorted((a for a in tl.del_rol(rol) if a.tipo == AUTOMATIZACION and a.datos["objetivo"] == objetivo),
                  key=lambda a: a.inicio)


def disp(tl, rol, nombre):
    return [a.datos for a in tl.del_rol(rol) if a.tipo == DISPOSITIVO and a.datos["nombre"] == nombre]


# --- 2 y 3: ultimo compas y corte previo quedan escritos en el plan ------------------------------------

def test_decisiones_de_arreglo_explicitas_en_el_timeline(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    dec = {a.regla: a for a in tl.de_tipo(DECISION)}
    assert dec["corte_previo_al_drop"].inicio == B(65) - 2.0 and dec["corte_previo_al_drop"].fin == B(65)
    assert "snare_fill" in dec["corte_previo_al_drop"].datos["conserva"]
    ultimo = dec["ultimo_compas"]
    assert ultimo.inicio == B(192) and ultimo.fin == B(193)
    # y el compas 192 de verdad tiene el kick entero y nada de fills
    k = [n for a in tl.del_rol("kick") if a.tipo == MIDI for n in a.datos["notas"] if a.inicio + n["start"] >= B(192)]
    assert len(k) == 4
    assert not [a for a in tl.acciones if a.tipo in (MIDI, CLIP_LOOP) and a.rol in ("snare_fill", "roll", "roll_32")
                and a.fin > B(192)]
    assert dec["rumble_y_bajo"].inicio == B(64)


# --- 4: llamado y respuesta experimental -----------------------------------------------------------

def test_llamado_respuesta_viene_desactivado_y_sin_instrumento(perfil, make_ctx):
    r = perfil.regla("llamado_respuesta")
    assert r["experimental"] is True and r["activa_por_defecto"] is False
    assert [p["responde"] for p in r["pares"]] == [None]          # el PO rechazo el stab
    sec = [S("m", "drop", 16, suma=["kick", "stab"], ocasionales=[{"rol": "vox_acid", "fraseo": "ultimos_8_de_16"}])]
    roles = ["kick", "stab", "vox_acid"]
    base = rules.presencia(make_ctx(sec, roles=roles))
    assert base["stab"] == [(0.0, B(17))]                          # por defecto el stab no se toca
    # activarla sin instrumento asignado tampoco cambia nada
    assert rules.presencia(make_ctx(sec, roles=roles, reglas_experimentales=True))["stab"] == base["stab"]


# --- 6: FX variados -----------------------------------------------------------------------------------

def reverses(tl):
    return sorted((a for a in tl.del_rol("reverse") if a.tipo == CLIP_ONESHOT), key=lambda a: (a.inicio, a.regla))


GROOVES = [S("i", "intro", 16, suma=["kick"]), S("g1", "groove", 16), S("g2", "groove", 16), S("g3", "groove", 16),
           S("g4", "groove", 16)]


def test_los_fx_rotan_archivos_sin_repetir_seguido(make_ctx):
    ctx = make_ctx(GROOVES, roles=["kick", "reverse"], alternativas={"reverse": ["C:\\pack\\rev_b.wav", "C:\\pack\\rev_c.wav"]})
    rutas = [a.datos["ruta"] for a in reverses(rules.generar_timeline(ctx))]
    assert len(rutas) == 4
    assert rutas[:3] == ["C:\\pack\\reverse.wav", "C:\\pack\\rev_b.wav", "C:\\pack\\rev_c.wav"]
    assert all(a != b for a, b in zip(rutas, rutas[1:]))
    again = [a.datos["ruta"] for a in reverses(rules.generar_timeline(ctx))]
    assert again == rutas                                   # determinista


def test_con_dos_archivos_alterna_y_con_uno_no_agrega_ruta(make_ctx):
    dos = make_ctx(GROOVES, roles=["kick", "reverse"], alternativas={"reverse": ["C:\\pack\\rev_b.wav"]})
    rutas = [a.datos["ruta"] for a in reverses(rules.generar_timeline(dos))]
    assert rutas == ["C:\\pack\\reverse.wav", "C:\\pack\\rev_b.wav"] * 2
    uno = make_ctx(GROOVES, roles=["kick", "reverse"])
    assert all("ruta" not in a.datos for a in reverses(rules.generar_timeline(uno)))


def test_los_rolls_tambien_rotan(make_ctx):
    ctx = make_ctx([S("d", "drop", 100, suma=["kick"])], roles=["kick", "roll"],
                   alternativas={"roll": ["C:\\pack\\roll_b.wav"]})
    rolls = sorted((a for a in rules.generar_timeline(ctx).del_rol("roll") if a.tipo == CLIP_LOOP),
                   key=lambda a: a.inicio)
    rutas = [a.datos["ruta"] for a in rolls]
    assert len(rutas) >= 3 and all(a != b for a, b in zip(rutas, rutas[1:]))


# --- 7: entrada filtrada de elementos nuevos ----------------------------------------------------------------

def test_elemento_nuevo_entra_filtrado_300_a_16k_en_8_compases(make_ctx):
    ctx = make_ctx([S("a", "intro", 16, suma=["kick", "top"]), S("b", "groove", 16, suma=["clap"])],
                   roles=["kick", "top", "clap"])
    tl = rules.generar_timeline(ctx)
    top, = lanes(tl, "top", AF)
    assert top.datos["puntos"] == [[0.0, {"display": 300}], [B(9), {"display": 16000}]]
    clap, = lanes(tl, "clap", AF)
    assert clap.datos["puntos"] == [[B(17), {"display": 300}], [B(25), {"display": 16000}]]
    assert clap.regla == "entrada_filtrada" and clap.tipo == AUTOMATIZACION
    assert disp(tl, "clap", "Auto Filter")               # y el device se inserta si falta


def test_solo_la_primera_aparicion_cuenta_como_nueva(make_ctx):
    ctx = make_ctx([S("a", "intro", 16, suma=["kick", "top"]), S("b", "groove", 16, quita=["top"]),
                    S("c", "groove", 16, suma=["top"])], roles=["kick", "top"])
    assert len(lanes(rules.generar_timeline(ctx), "top", AF)) == 1


def test_entrada_filtrada_en_el_puente_salvo_la_que_culmina_el_riser(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    por_rol = {r: [l for l in lanes(tl, r, AF) if l.regla == "entrada_filtrada"]
               for r in ("atmo", "atmo_trippy", "choir", "vox_angel", "top", "pad")}
    assert [l.inicio for l in por_rol["atmo_trippy"]] == [B(101)]
    assert [l.inicio for l in por_rol["choir"]] == [B(105)]
    assert [l.inicio for l in por_rol["vox_angel"]] == [B(109)]
    assert B(113) in [l.inicio for l in por_rol["top"]]
    assert not [l for l in por_rol["atmo"] if l.inicio == B(97)]       # culminacion del riser: entra de golpe
    assert not por_rol["pad"]
    # stab y lead ya tienen su propia lane de filtro: no se les suma otra
    assert not [l for r in ("stab", "lead") for l in lanes(tl, r, AF) if l.regla == "entrada_filtrada"]
    assert tl.lanes_en_conflicto() == []


# --- 8: ecos de delay en las voces + cadena de voz ---------------------------------------------------------

def test_eco_de_delay_en_el_ultimo_medio_compas_de_cada_frase_de_voz(make_ctx):
    sec = [S("m", "drop", 16, suma=["kick"], ocasionales=[{"rol": "vox_acid", "fraseo": "ultimos_8_de_16"}])]
    tl = rules.generar_timeline(make_ctx(sec, roles=["kick", "vox_acid"]))
    delay_pos = [a.datos["id"] for a in tl.acciones if a.tipo == "retorno"].index("delay")
    lane, = lanes(tl, "vox_acid", {"send": delay_pos})
    off, pico = {"display": -60}, {"display": -8}
    assert lane.datos["puntos"] == [
        [B(13) - 2.0, off], [B(13) - 1.75, pico], [B(13) - 0.25, pico], [B(13), off],
        [B(17) - 2.0, off], [B(17) - 1.75, pico], [B(17) - 0.25, pico], [B(17), off]]
    assert lane.regla == "delay_throws_voces"


def test_vox_angel_pierde_el_delay_estatico_y_lo_recibe_por_throws(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    ret = [a.datos["id"] for a in tl.acciones if a.tipo == "retorno"]
    mz = [a for a in tl.de_tipo(MEZCLA) if a.rol == "vox_angel"][0]
    assert str(ret.index("delay")) not in mz.datos["envios"]
    lane = lanes(tl, "vox_angel", {"send": ret.index("delay")})
    assert lane and lane[0].datos["puntos"][0][0] == B(113) - 2.0     # fin de la 1.a frase de 4 compases
    assert tl.lanes_en_conflicto() == []


def test_cadena_de_voz_hp_100_a_110_y_compresor_sin_inventar_fuentes(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    for rol, hp in (("vox_acid", 110), ("vox_angel", 100)):
        eq, = disp(tl, rol, "EQ Eight")
        assert eq["items"]["1 Filter Type A"] == "High Pass 12dB" and eq["params"]["1 Frequency A"] == hp
        assert disp(tl, rol, "Compressor")
        assert not disp(tl, rol, "Saturator")                # sin fuente en F4: no se agrega


# --- 9: plantilla de mezcla -------------------------------------------------------------------------------------

def test_high_pass_de_12_db_por_rol_con_nombre_exacto(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    for rol, hz in (("top", 220), ("clap", 200), ("drums", 160), ("stab", 180), ("atmo", 250), ("choir", 220),
                    ("snare_fill", 180), ("crash", 300), ("impacto", 120)):
        eq, = disp(tl, rol, "EQ Eight")
        assert eq["items"] == {"1 Filter On A": "On", "1 Filter Type A": "High Pass 12dB"}, rol
        assert eq["params"]["1 Frequency A"] == hz, rol


def test_cadena_de_graves_kick_rumble_y_bajo(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    assert disp(tl, "kick", "Drum Buss")
    eq_rumble, = disp(tl, "rumble", "EQ Eight")
    assert eq_rumble["items"]["2 Filter Type A"] == "Low Pass 48dB" and eq_rumble["params"]["2 Frequency A"] == 250
    sat, = disp(tl, "bass", "Saturator")
    assert sat["items"]["Post Clip Mode"] == "Soft Clip"


def test_bass_mono_en_utility_ultimo_solo_para_los_graves(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    for rol in ("kick", "rumble", "bass"):
        ut, = [d for d in disp(tl, rol, "Utility") if d.get("ultimo")]
        assert ut["items"] == {"Bass Mono": "On"} and ut["params"] == {"Bass Freq": 120}
    ut_atmo, = disp(tl, "atmo_trippy", "Utility")
    assert "items" not in ut_atmo and ut_atmo["ultimo"] is True


def test_sidechain_con_valores_de_la_investigacion(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    sc = {a.rol: a.datos for a in tl.de_tipo(SIDECHAIN)}
    assert sc["rumble"]["params"] == {"Threshold": -32, "Ratio": 4, "Attack": 1, "Release": 200}
    assert sc["bass"]["params"]["Release"] == 90
    assert sc["rumble"]["items"] == {"Auto Release On/Off": "Off"}


def test_cadena_de_master_glue_30ms_y_limiter_true_peak(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    glue, = disp(tl, "master", "Glue Compressor")
    assert glue["params"]["Threshold"] == -8 and any("Attack" in t and "30" in t for t in glue["a_mano"])
    lim, = disp(tl, "master", "Limiter")
    assert lim["params"]["Ceiling"] == -1 and any("True Peak" in t for t in lim["a_mano"])


# --- plugins de terceros opcionales (A-02) --------------------------------------------------------------------

def test_por_defecto_la_cadena_es_nativa(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    assert not [a for a in tl.de_tipo(DISPOSITIVO) if a.datos.get("plugin")]


def test_plugins_por_nombre_reemplazan_al_nativo_donde_corresponde(ctx_t02):
    ctx_t02.plugins = ("FabFilter Pro-Q 3", "Maag EQ4", "Butch Vig Vocals", "Waves H-Comp")
    tl = rules.generar_timeline(ctx_t02)
    assert [d["nombre"] for d in disp(tl, "top", "FabFilter Pro-Q 3")] == ["FabFilter Pro-Q 3"]
    assert not disp(tl, "top", "EQ Eight")
    assert disp(tl, "top", "FabFilter Pro-Q 3")[0]["plugin"] is True
    # en las voces gana el primero de la lista que aplica (Pro-Q 3 va con "*", pero el orden manda)
    assert disp(tl, "vox_acid", "FabFilter Pro-Q 3") and not disp(tl, "vox_acid", "Maag EQ4")
    assert disp(tl, "vox_acid", "Butch Vig Vocals") and not disp(tl, "vox_acid", "Compressor")
    assert disp(tl, "master", "Waves H-Comp") and not disp(tl, "master", "Glue Compressor")
    # el compresor del sidechain y el limiter siguen nativos
    assert [a for a in tl.de_tipo(SIDECHAIN) if a.rol == "rumble"] and disp(tl, "master", "Limiter")


def test_un_plugin_que_no_esta_en_el_catalogo_es_error(ctx_t02):
    ctx_t02.plugins = ("Plugin Inventado",)
    with pytest.raises(ValueError, match="Plugin Inventado"):
        rules.generar_timeline(ctx_t02)
