"""Reglas de arreglo: funciones puras sobre estructuras chicas y sobre la T02-like completa."""
import pytest

from composer import rules
from composer.model import (AUTOMATIZACION, CLIP_LOOP, CLIP_ONESHOT, DISPOSITIVO, LOCATOR, MIDI,
                            Accion)


def B(bar):
    return (bar - 1) * 4.0


def S(id_, tipo, n, **kw):
    return {"id": id_, "tipo": tipo, "compases": n, **kw}


def runs(tl, rol):
    return sorted((a.inicio, a.fin) for a in tl.del_rol(rol) if a.tipo == CLIP_LOOP)


def utility_lanes(tl):
    return [a for a in tl.de_tipo(AUTOMATIZACION)
            if isinstance(a.datos["objetivo"], dict) and a.datos["objetivo"].get("device") == "Utility"]


# --- D-15 -----------------------------------------------------------------------------------

@pytest.mark.parametrize("objetivo", ["volume", {"param": "volume"}, {"device": "Utility", "param": "Gain"},
                                      {"device": "Mixer", "param": "Volume"}])
def test_una_lane_de_volumen_es_imposible_de_construir(objetivo):
    with pytest.raises(ValueError, match="D-15"):
        Accion(tipo=AUTOMATIZACION, rol="top", inicio=0.0, fin=4.0,
               datos={"objetivo": objetivo, "puntos": [[0.0, {"display": 0}], [4.0, {"display": -6}]]},
               regla="x", por_que="x")


def test_el_timeline_completo_nunca_automatiza_volume(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    lanes = tl.de_tipo(AUTOMATIZACION)
    assert lanes
    for a in lanes:
        obj = a.datos["objetivo"]
        assert obj != "volume"
        if isinstance(obj, dict):
            assert str(obj.get("param", "")).lower() not in ("volume", "gain", "volumen")
    for a in utility_lanes(tl):
        assert a.datos["objetivo"]["param"] == "Output"


def test_no_hay_lanes_solapadas_en_el_mismo_destino(ctx_t02):
    assert rules.generar_timeline(ctx_t02).lanes_en_conflicto() == []


def test_es_determinista(ctx_t02):
    a = rules.generar_timeline(ctx_t02)
    b = rules.generar_timeline(ctx_t02)
    assert [x.__dict__ for x in a.acciones] == [x.__dict__ for x in b.acciones]


# --- presencia ------------------------------------------------------------------------------

def test_presencia_acumulativa_y_solo(make_ctx):
    ctx = make_ctx([S("a", "intro", 8, suma=["kick", "top"]),
                    S("b", "groove", 8, suma=["clap"], quita=["top"]),
                    S("c", "silence", 1, solo=[]),
                    S("d", "drop", 8, suma=["kick"])])
    p = rules.presencia_base(ctx)
    assert p["kick"] == [(0.0, B(17)), (B(18), B(26))]    # el silencio (compas 17) corta el kick
    assert p["top"] == [(0.0, B(9))]
    assert p["clap"] == [(B(9), B(17))]


def test_entrada_y_salida_a_mitad_de_seccion(make_ctx):
    ctx = make_ctx([S("a", "intro", 16, suma=["kick", {"rol": "drums", "desde": 9}]),
                    S("b", "outro", 16, quita=[{"rol": "kick", "desde": 9}])])
    p = rules.presencia_base(ctx)
    assert p["drums"][0][0] == B(9)
    assert p["kick"] == [(0.0, B(25))]


def test_ocasionales_ultimos_8_de_16(make_ctx):
    ctx = make_ctx([S("g", "groove", 32, suma=["kick"],
                      ocasionales=[{"rol": "vox_acid", "fraseo": "ultimos_8_de_16"}])])
    assert rules.presencia_base(ctx)["vox_acid"] == [(B(9), B(17)), (B(25), B(33))]


def test_rol_sin_elemento_no_genera_nada(make_ctx):
    ctx = make_ctx([S("a", "intro", 8, suma=["kick", "top"])], roles=["kick"])
    tl = rules.generar_timeline(ctx)
    assert tl.del_rol("top") == []


# --- huecos de kick -------------------------------------------------------------------------

def kick_notes(tl):
    """{compas: [tiempos (1..4) con kick]} a partir de los clips MIDI del kick."""
    out = {}
    for a in tl.del_rol("kick"):
        if a.tipo != MIDI:
            continue
        for n in a.datos["notas"]:
            beat = a.inicio + n["start"]
            out.setdefault(int(beat // 4) + 1, []).append(int(beat % 4) + 1)
    return out


def test_huecos_de_kick_crecen_con_el_nivel_de_frase(make_ctx):
    ctx = make_ctx([S("d", "drop", 72, suma=["kick"])])
    k = kick_notes(rules.generar_timeline(ctx))
    assert k[7] == [1, 2, 3, 4]                       # compas normal
    assert k[8] == [1, 2, 3]                          # fin de 8: sin el 4.o
    assert k[16] == [1, 2]                            # fin de 16: sin 3.o y 4.o
    assert 32 not in k                                # fin de 32: compas entero sin kick
    assert 64 not in k
    assert k[72] == [1, 2, 3, 4]                      # ultimo compas del tema: sin hueco


def test_kick_usa_la_nota_del_perfil(make_ctx):
    ctx = make_ctx([S("d", "drop", 8, suma=["kick"])])
    notas = [n for a in rules.generar_timeline(ctx).del_rol("kick") if a.tipo == MIDI for n in a.datos["notas"]]
    assert {n["pitch"] for n in notas} == {58} and {n["velocity"] for n in notas} == {110}


# --- fills ----------------------------------------------------------------------------------

def test_snare_fill_en_fines_de_8_que_no_son_de_16_con_rampa(make_ctx):
    ctx = make_ctx([S("d", "drop", 40, suma=["kick", "snare_fill"])])
    fills = [a for a in rules.generar_timeline(ctx).del_rol("snare_fill") if a.tipo == MIDI]
    starts = sorted(a.inicio for a in fills)
    assert starts == [B(8), B(24)]                    # 16 y 32 se resuelven con rolls
    notas = sorted(fills[0].datos["notas"], key=lambda n: n["start"])
    vels = [n["velocity"] for n in notas]
    assert vels[0] == 70 and vels[-1] == 118 and vels == sorted(vels) and len(vels) == 4
    assert [n["start"] for n in notas] == [3.0, 3.25, 3.5, 3.75]


def test_fills_solo_donde_suena_el_groove(make_ctx):
    ctx = make_ctx([S("i", "intro", 8, suma=["top"]), S("d", "drop", 8, suma=["kick"])])
    # el compas 8 no tiene kick (intro sin kick): sin fill
    assert rules.generar_timeline(ctx).del_rol("snare_fill") == []


def test_rolls_terminan_justo_en_el_cambio_de_frase(make_ctx):
    ctx = make_ctx([S("d", "drop", 72, suma=["kick"])])
    tl = rules.generar_timeline(ctx)
    rolls = sorted((a.inicio, a.fin) for a in tl.acciones if a.tipo == CLIP_LOOP and a.rol.startswith("roll"))
    assert (B(16) + 1.0, B(17)) in rolls              # fin de 16: 3/4 de compas, termina en el limite
    assert (B(32), B(33)) in rolls                    # fin de 32: 1 compas
    assert all(b - a in (3.0, 4.0) for a, b in rolls)
    assert not any(a >= B(72) for a, _ in rolls)      # ni fills ni rolls en el ultimo compas


# --- crashes --------------------------------------------------------------------------------

def test_crash_en_el_1_de_cada_16_menos_dentro_del_breakdown(make_ctx):
    ctx = make_ctx([S("d", "drop", 32, suma=["kick"]), S("b", "breakdown", 32, quita=["kick"]),
                    S("d2", "drop", 16, suma=["kick"])])
    crashes = sorted(a.inicio for a in rules.generar_timeline(ctx).del_rol("crash") if a.tipo == CLIP_ONESHOT)
    assert crashes == [B(17), B(33), B(65)]           # 49 cae en el medio del breakdown: no


# --- transiciones: reverses, impactos, risers, silencio --------------------------------------

def oneshots(tl, rol):
    return sorted((a.inicio, a.datos["ancla"]) for a in tl.del_rol(rol) if a.tipo == CLIP_ONESHOT)


def test_riser_largo_termina_justo_donde_empieza_el_silencio(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    assert (B(128), "fin") in oneshots(tl, "riser_largo")
    assert (B(128), "fin") in oneshots(tl, "riser_corto")


def test_reverses_terminan_en_los_limites_de_seccion(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    ends = [b for b, anc in oneshots(tl, "reverse") if anc == "fin"]
    assert B(17) in ends and B(33) in ends and B(97) in ends
    assert B(129) not in ends                          # tras un silencio entra el impacto, no un reverse
    assert B(49) not in ends                           # override de la seccion: impacto
    assert all(anc == "fin" for _, anc in oneshots(tl, "reverse"))


def test_impacto_tras_silencio_y_downlifter_en_los_drops(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    assert (B(129), "inicio") in oneshots(tl, "impacto") and (B(49), "inicio") in oneshots(tl, "impacto")
    assert {b for b, _ in oneshots(tl, "sweep_down")} == {B(65), B(129)}
    assert (B(65), "fin") in oneshots(tl, "sweep_up")  # drop sin silencio: sweep up termina en el drop


def test_nada_suena_durante_el_silencio(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    a, b = B(128), B(129)
    for x in tl.acciones:
        if x.tipo in (CLIP_LOOP, MIDI):
            assert not (x.inicio < b and x.fin > a), (x.rol, x.inicio, x.fin)


def test_corte_previo_al_drop_sin_silencio(make_ctx):
    ctx = make_ctx([S("d", "drop", 16, suma=["kick", "top", "snare_fill"]),
                    S("b", "breakdown", 16, suma=["top", "snare_fill"], quita=["kick"]),
                    S("d2", "drop", 16, suma=["kick"])], roles=["kick", "top", "snare_fill"])
    tl = rules.generar_timeline(ctx)
    fin_bd = B(33)
    assert max(b for _, b in runs(tl, "top") if b <= fin_bd) == fin_bd - 2.0   # anacrusa: 2 tiempos antes
    assert any(a.tipo == MIDI and a.fin >= fin_bd for a in tl.del_rol("snare_fill"))  # el conservado sigue


def test_con_silencio_no_hay_corte(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    assert max(b for _, b in runs(tl, "atmo")) == B(128)   # el puente corre hasta el compas 127 incluido


# --- locators -------------------------------------------------------------------------------

def test_un_locator_por_seccion(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    locs = sorted((a.inicio, a.datos["nombre"]) for a in tl.de_tipo(LOCATOR))
    assert len(locs) == len(ctx_t02.estructura.secciones)
    assert locs[0] == (0.0, "intro_a") and (B(128), "silencio") in locs


# --- puente ---------------------------------------------------------------------------------

def test_puente_entra_de_a_poco_cada_4_compases(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    entradas = {r: min(a for a, _ in runs(tl, r) if a >= B(97)) for r in
                ("atmo", "atmo_trippy", "choir", "vox_angel", "top")}
    assert entradas == {"atmo": B(97), "atmo_trippy": B(101), "choir": B(105), "vox_angel": B(109),
                        "top": B(113)}
    assert max(b for _, b in runs(tl, "vox_angel")) == B(125)        # sale 4 compases antes del final
    assert all(max(b for _, b in runs(tl, r) if b <= B(129)) <= B(128)
               for r in ("atmo", "atmo_trippy", "choir", "top", "pad"))


def test_cada_entrada_menos_la_que_culmina_el_riser_lleva_fade_en_utility_output(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    por_rol = {a.rol: a for a in utility_lanes(tl) if B(97) <= a.inicio < B(129)}
    assert "atmo" not in por_rol                       # entra de golpe: culmina el riser
    for rol, entrada in (("atmo_trippy", 101), ("choir", 105), ("vox_angel", 109), ("top", 113)):
        lane = por_rol[rol]
        assert lane.datos["objetivo"] == {"device": "Utility", "param": "Output"}
        pts = lane.datos["puntos"]
        assert pts[0][0] <= B(entrada)
        sube = [p for p in pts if B(entrada) <= p[0] <= B(entrada) + 32]
        assert sube[0][1]["display"] < sube[-1][1]["display"]          # arranca bajo y sube
    # los fades arrancan en el nivel del perfil
    assert por_rol["atmo_trippy"].datos["puntos"][1][1]["display"] == -60


def test_el_pad_crece_en_todo_el_puente_y_vuelve_a_0_en_el_silencio(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    pad = [a for a in utility_lanes(tl) if a.rol == "pad"][0]
    pts = pad.datos["puntos"]
    assert pts[0] == [B(97), {"display": -20}]
    assert pts[-1] == [B(128), {"display": 0}]
    assert max(p[1]["display"] for p in pts) == 6


def test_roll_de_snare_del_puente_acelera_y_termina_en_el_silencio(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    roll = [a for a in tl.del_rol("snare_fill") if a.tipo == MIDI and a.fin == B(128)][0]
    assert roll.inicio == B(128) - 15 * 4
    notas = sorted(roll.datos["notas"], key=lambda n: n["start"])
    gaps = [round(b["start"] - a["start"], 4) for a, b in zip(notas, notas[1:])]
    assert gaps[0] == 1.0 and gaps[-1] == 0.125
    assert gaps == sorted(gaps, reverse=True)          # solo acelera, nunca desacelera
    assert notas[0]["velocity"] == 35 and notas[-1]["velocity"] == 127
    assert max(n["start"] + n["duration"] for n in notas) <= roll.fin - roll.inicio


def test_filtro_sigue_al_riser(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    lanes = {a.rol: a for a in tl.de_tipo(AUTOMATIZACION)
             if a.datos["objetivo"] == {"device": "Auto Filter", "param": "Frequency"}
             and a.inicio >= B(120) and a.rol != "master"}
    assert set(lanes) >= {"atmo", "atmo_trippy", "choir", "snare_fill"}
    pts = lanes["choir"].datos["puntos"]
    vals = [p[1]["display"] for p in pts]
    assert vals[0] == 16000 and vals[1] == 700          # cierra rapido
    assert vals[-1] == 16000                            # termina abierto
    assert vals[1:] == sorted(vals[1:])                 # y abre acompanando al riser
    assert pts[1][0] - pts[0][0] == 1.0
    assert pts[-1][0] == B(128)


def test_filtro_hp_del_master_abre_en_los_ultimos_8_compases(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    m = [a for a in tl.de_tipo(AUTOMATIZACION) if a.rol == "master"][0]
    assert m.datos["puntos"][0] == [B(120), {"display": 20}]
    assert m.datos["puntos"][-1] == [B(128), {"display": 20}]   # vuelve a 20 Hz en el silencio
    assert max(p[1]["display"] for p in m.datos["puntos"]) == 900


# --- escalera -------------------------------------------------------------------------------

def test_escalera_cada_frase_de_8_llega_mas_lejos(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    lanes = [a for a in tl.del_rol("stab") if a.tipo == AUTOMATIZACION]
    assert len(lanes) == 2                              # un tramo 49-96 y otro 129-160
    pts = lanes[0].datos["puntos"]
    assert len(pts) == 6 * 2                            # 6 frases de 8, lo y hi cada una
    los = [p[1]["display"] for p in pts[0::2]]
    his = [p[1]["display"] for p in pts[1::2]]
    assert los == sorted(los) and his == sorted(his) and len(set(his)) == 6
    assert los[0] == 250 and los[-1] == 1500 and his[0] == 900 and his[-1] == 12000
    assert all(h > l for l, h in zip(los, his))
    assert all(pts[i + 1][0] > pts[i][0] for i in range(len(pts) - 1))
    assert pts[0][0] == B(49) and pts[2][0] == B(57)    # el diente de sierra reinicia cada frase de 8
    assert lanes[1].datos["puntos"][0][1]["display"] == 600


def test_apertura_del_lead_en_todo_el_tramo(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    lane = [a for a in tl.del_rol("lead") if a.tipo == AUTOMATIZACION][0]
    vals = [p[1]["display"] for p in lane.datos["puntos"]]
    assert vals == [400, 2500, 16000]
    assert lane.datos["puntos"][0][0] == B(129) and lane.datos["puntos"][1][0] == B(145)


def test_recetas_de_filtro_como_valores_fijos(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    disp = {(a.rol, a.datos["nombre"]): a.datos for a in tl.de_tipo(DISPOSITIVO)}
    assert disp[("stab", "Auto Filter")]["params"] == {"Resonance": 25, "Drive": 14}
    assert disp[("lead", "Auto Filter")]["params"] == {"Resonance": 20, "Drive": 14}
    assert disp[("choir", "Auto Filter")]["params"] == {"Resonance": 29, "Drive": 14}


# --- llamado y respuesta --------------------------------------------------------------------

def _con_par(ctx, responde):
    import copy
    from composer.profile import Perfil
    datos = copy.deepcopy(ctx.perfil.datos)
    datos["reglas"]["llamado_respuesta"]["pares"] = [{"llama": "vox_acid", "responde": responde, "unidad_compases": 2}]
    ctx.perfil = Perfil(datos=datos)
    return ctx


def test_stab_y_voz_se_alternan_de_a_2_compases_solo_si_se_activa_y_se_asigna(make_ctx):
    sec = [S("m", "drop", 16, suma=["kick", "stab"],
             ocasionales=[{"rol": "vox_acid", "fraseo": "ultimos_8_de_16"}])]
    roles = ["kick", "stab", "vox_acid"]
    ctx = _con_par(make_ctx(sec, roles=roles, reglas_experimentales=True), "stab")
    p = rules.presencia(ctx)
    assert p["vox_acid"] == [(B(9), B(17))]
    # el stab suena en 1-8 y, en 9-16, solo donde la voz calla (11-12 y 15-16)
    assert p["stab"] == [(B(1), B(9)), (B(11), B(13)), (B(15), B(17))]


def test_la_escalera_se_calcula_sobre_la_presencia_base(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    # aunque el stab tenga huecos por llamado y respuesta, la escalera cubre las 6 frases enteras
    assert len([a for a in tl.del_rol("stab") if a.tipo == AUTOMATIZACION][0].datos["puntos"]) == 12


# --- huecos de seccion nivel 32 -------------------------------------------------------------

def test_rumble_y_bajo_caen_solo_en_el_compas_64_que_entra_al_main(ctx_t02):
    p = rules.presencia(ctx_t02)
    en = lambda rol, bar: any(a <= B(bar) and B(bar + 1) <= b for a, b in p[rol])  # noqa: E731
    assert not en("rumble", 64) and not en("bass", 64)
    # en los otros fines de 32 solo cae el kick: rumble y bajo se quedan
    assert en("rumble", 32) and en("rumble", 160) and en("bass", 160)
    assert en("rumble", 63) and en("bass", 63)
    k = kick_notes(rules.generar_timeline(ctx_t02))
    assert 32 not in k and 64 not in k and 160 not in k       # y el kick si cae en todos


# --- movimiento -----------------------------------------------------------------------------

def test_pan_alterna_y_atmos_van_en_fase_opuesta(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    pan = {a.rol: a for a in tl.de_tipo(AUTOMATIZACION) if a.datos["objetivo"] == "pan"}
    top = [p[1] for p in pan["top"].datos["puntos"]]
    assert set(top) == {0.15, -0.15, 0.0}
    a1 = pan["atmo"].datos["puntos"][0][1]
    a2 = pan["atmo_trippy"].datos["puntos"][0][1]
    assert a1 == -a2 and abs(a1) == 0.5
