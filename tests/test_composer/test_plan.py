import json

import pytest

from composer import rules
from composer.model import AUTOMATIZACION, Accion
from composer.plan import agrupar_pasadas, crear_plan, plan_a_json, plan_a_markdown, plan_desde_json


def B(bar):
    return (bar - 1) * 4.0


def lane(rol, objetivo, puntos):
    return Accion(tipo=AUTOMATIZACION, rol=rol, inicio=puntos[0][0], fin=puntos[-1][0],
                  datos={"objetivo": objetivo, "puntos": puntos}, regla="t", por_que="t")


def test_json_ida_y_vuelta_conserva_todo(ctx_t02):
    plan = crear_plan(ctx_t02, nombre="T03")
    otro = plan_desde_json(plan_a_json(plan))
    assert [a.__dict__ for a in otro.acciones] == [a.__dict__ for a in plan.acciones]
    assert otro.meta == plan.meta and otro.elementos == plan.elementos


def test_meta_trae_perfil_tempo_y_largo(ctx_t02):
    plan = crear_plan(ctx_t02, nombre="T03")
    assert plan.meta["perfil"] == "techno-peak-time" and plan.meta["tempo"] == 134.0
    assert plan.meta["total_compases"] == 192 and plan.meta["nombre"] == "T03"


def test_un_plan_con_volume_se_rechaza_al_cargar(ctx_t02):
    datos = json.loads(plan_a_json(crear_plan(ctx_t02, nombre="T03")))
    for a in datos["acciones"]:
        if a["tipo"] == "automatizacion":
            a["datos"]["objetivo"] = "volume"
            break
    with pytest.raises(ValueError, match="D-15"):
        plan_desde_json(json.dumps(datos))


def test_markdown_lista_secciones_reglas_y_pasadas(ctx_t02):
    md = plan_a_markdown(crear_plan(ctx_t02, nombre="T03"))
    assert md.startswith("# ")
    for texto in ("| Compás |", "puente", "silencio", "huecos_kick", "Utility", "Pasadas de grabación"):
        assert texto in md, texto
    assert "| volume" not in md.lower()


def test_pasadas_solapadas_se_fusionan_y_las_disjuntas_no():
    a = lane("stab", {"device": "Auto Filter", "param": "Frequency"}, [[0.0, {"display": 1}], [100.0, {"display": 2}]])
    b = lane("lead", "pan", [[50.0, 0.1], [150.0, 0.0]])
    c = lane("top", "pan", [[1000.0, 0.1], [1100.0, 0.0]])
    pasadas = agrupar_pasadas([c, b, a])
    assert [(p.inicio, p.fin) for p in pasadas] == [(0.0, 150.0), (1000.0, 1100.0)]
    assert len(pasadas[0].lanes) == 2


def test_lanes_del_mismo_destino_se_fusionan_con_un_punto_de_sostenido():
    obj = {"device": "Auto Filter", "param": "Frequency"}
    a = lane("stab", obj, [[0.0, {"display": 250}], [40.0, {"display": 900}]])
    b = lane("stab", obj, [[200.0, {"display": 600}], [240.0, {"display": 3000}]])
    otra = lane("lead", "pan", [[30.0, 0.0], [220.0, 0.2]])            # obliga a una sola pasada
    pasada, = agrupar_pasadas([a, b, otra])
    stab = [x for x in pasada.lanes if x.rol == "stab"]
    assert len(stab) == 1
    pts = stab[0].datos["puntos"]
    assert [p[0] for p in pts] == sorted(p[0] for p in pts)
    # antes de que arranque la 2.a lane se sostiene el ultimo valor de la 1.a (sin rampa de 900 a 600)
    assert [199.99, {"display": 900}] in [[round(p[0], 2), p[1]] for p in pts]


def test_pasada_estima_minutos_a_tempo():
    a = lane("stab", "pan", [[0.0, 0.0], [268.0, 0.1]])               # 268 beats a 134 BPM = 2 min
    pasada, = agrupar_pasadas([a])
    assert pasada.duracion_s(134.0) == pytest.approx(120.0)


def test_el_plan_t02_like_agrupa_en_pocas_pasadas(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    pasadas = agrupar_pasadas(tl.de_tipo(AUTOMATIZACION))
    assert 1 <= len(pasadas) <= 4
