import copy
from pathlib import Path

import pytest

from composer.profile import PerfilInvalido, cargar_perfil, validar_perfil


def test_carga_el_perfil_por_defecto(perfil):
    assert perfil.id == "techno-peak-time"
    assert perfil.dato("global", "tempo", "tipico") == 130


def test_todo_bloque_de_primer_nivel_tiene_fuente_y_confianza(perfil):
    for seccion in ("global", "elementos", "reglas"):
        for nombre, bloque in perfil.datos[seccion].items():
            assert "fuente" in bloque and "confianza" in bloque, (seccion, nombre)
    for seccion in ("transiciones", "mezcla", "plantillas"):
        bloque = perfil.datos[seccion]
        assert "fuente" in bloque and "confianza" in bloque, seccion


def test_criterios_de_gabriel_son_confianza_alta(perfil):
    marcados = [(s, n) for s in ("elementos", "reglas") for n, b in perfil.datos[s].items()
                if b.get("criterio_gabriel")]
    assert marcados, "debe haber criterios de Gabriel marcados"
    for s, n in marcados:
        assert perfil.datos[s][n]["confianza"] == "alta", (s, n)


def test_bloque_sin_fuente_es_invalido(perfil):
    datos = copy.deepcopy(perfil.datos)
    del datos["reglas"]["crashes"]["fuente"]
    with pytest.raises(PerfilInvalido, match="crashes"):
        validar_perfil(datos)


def test_confianza_desconocida_es_invalida(perfil):
    datos = copy.deepcopy(perfil.datos)
    datos["elementos"]["kick"]["confianza"] = "altisima"
    with pytest.raises(PerfilInvalido, match="confianza"):
        validar_perfil(datos)


def test_falta_seccion_obligatoria(perfil):
    datos = copy.deepcopy(perfil.datos)
    del datos["reglas"]
    with pytest.raises(PerfilInvalido, match="reglas"):
        validar_perfil(datos)


def test_warp_desconocido_es_invalido(perfil):
    datos = copy.deepcopy(perfil.datos)
    datos["elementos"]["top"]["warp"] = "turbo"
    with pytest.raises(PerfilInvalido, match="warp"):
        validar_perfil(datos)


def test_perfil_no_puede_automatizar_volume(perfil):
    datos = copy.deepcopy(perfil.datos)
    datos["reglas"]["escalera_filtro"]["parametro"] = "volume"
    with pytest.raises(PerfilInvalido, match="D-15"):
        validar_perfil(datos)


def test_plantilla_inexistente(perfil):
    with pytest.raises(PerfilInvalido, match="nope"):
        perfil.plantilla("nope")


def test_archivo_inexistente(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        cargar_perfil(tmp_path / "no.yaml")
