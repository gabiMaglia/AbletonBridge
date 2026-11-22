import pytest

from composer.profile import PerfilInvalido
from composer.structure import (compas_a_beat, construir_estructura, estructura_desde_secciones,
                                nivel_de_frase)


def test_t02_like_son_192_compases_con_secciones_contiguas(perfil):
    est = construir_estructura(perfil, "t02_like")
    assert est.total_compases == 192
    assert [s.id for s in est.secciones][:3] == ["intro_a", "intro_b", "groove_1"]
    # sin huecos ni solapes: cada seccion empieza donde termina la anterior
    for a, b in zip(est.secciones, est.secciones[1:]):
        assert b.inicio == a.fin + 1
    assert est.seccion("puente").inicio == 97 and est.seccion("silencio").inicio == 128
    assert est.seccion("drop_2").inicio == 129


@pytest.mark.parametrize("compas,nivel", [(8, 8), (16, 16), (24, 8), (32, 32), (64, 32),
                                          (48, 16), (7, 0), (1, 0), (96, 32)])
def test_nivel_de_frase(compas, nivel):
    assert nivel_de_frase(compas) == nivel


def test_compas_a_beat():
    assert compas_a_beat(1) == 0.0 and compas_a_beat(17) == 64.0


def test_seccion_en_un_compas(perfil):
    est = construir_estructura(perfil, "t02_like")
    assert est.seccion_en(100).id == "puente"
    assert est.seccion_en(128).id == "silencio"
    with pytest.raises(ValueError):
        est.seccion_en(500)


def test_anterior_y_siguiente(perfil):
    est = construir_estructura(perfil, "t02_like")
    s = est.seccion("silencio")
    assert est.anterior(s).id == "puente" and est.siguiente(s).id == "drop_2"
    assert est.anterior(est.secciones[0]) is None and est.siguiente(est.secciones[-1]) is None


def test_largo_pedido_lo_absorbe_el_ultimo_outro(perfil):
    est = construir_estructura(perfil, "t02_like", largo_compases=208)
    assert est.total_compases == 208
    assert est.secciones[-1].compases == 32


def test_largo_imposible(perfil):
    with pytest.raises(ValueError, match="largo"):
        construir_estructura(perfil, "t02_like", largo_compases=100)


def test_plantilla_estandar_f4(perfil):
    est = construir_estructura(perfil, "peak_time_estandar")
    assert est.total_compases == 32 + 16 + 32 + 32 + 32 + 32


def test_desde_secciones_valida_tipo():
    with pytest.raises(ValueError, match="tipo"):
        estructura_desde_secciones([{"id": "x", "tipo": "raro", "compases": 8}])
