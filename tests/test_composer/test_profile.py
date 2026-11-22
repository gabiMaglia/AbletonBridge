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


# --- T-015b -----------------------------------------------------------------------------------------

def test_cada_rol_de_la_plantilla_de_mezcla_lleva_fuente_y_confianza(perfil):
    roles = perfil.dato("mezcla", "plantilla")
    assert {"kick", "rumble", "bass", "vox_acid", "vox_angel", "top"} <= set(roles)
    for nombre, bloque in roles.items():
        assert bloque["fuente"] and bloque["confianza"] in ("alta", "media", "baja"), nombre


def test_plantilla_sin_fuente_es_invalida(perfil):
    datos = copy.deepcopy(perfil.datos)
    del datos["mezcla"]["plantilla"]["top"]["fuente"]
    with pytest.raises(PerfilInvalido, match="plantilla.top"):
        validar_perfil(datos)


def test_un_tipo_de_filtro_por_coincidencia_parcial_es_invalido(perfil):
    datos = copy.deepcopy(perfil.datos)
    datos["mezcla"]["plantilla"]["top"]["eq"][0]["tipo"] = "High Pass"
    with pytest.raises(PerfilInvalido, match="High Pass"):
        validar_perfil(datos)


def test_valor_item_busca_por_nombre_exacto():
    from composer.profile import ItemDesconocido, valor_item
    assert valor_item("EQ Eight", "1 Filter Type A", "High Pass 48dB") == 0
    assert valor_item("EQ Eight", "1 Filter Type A", "High Pass 12dB") == 1
    assert valor_item("EQ Eight", "3 Filter Type A", "Low Pass 48dB") == 7
    assert valor_item("Utility", "Bass Mono", "On") == 1
    for malo in ("High Pass", "high pass 12db", "Low"):
        with pytest.raises(ItemDesconocido):
            valor_item("EQ Eight", "1 Filter Type A", malo)
    with pytest.raises(ItemDesconocido):
        valor_item("Glue Compressor", "Attack", "30 ms")      # sin catalogo: no se adivina


def test_regla_experimental_y_mono_de_graves(perfil):
    assert perfil.regla("llamado_respuesta")["experimental"] is True
    assert perfil.dato("mezcla", "mono_bajo_hz") == 120
    cat = perfil.dato("mezcla", "plugins", "catalogo")
    assert perfil.dato("mezcla", "plugins", "usar_por_defecto") is False
    assert {"FabFilter Pro-Q 3", "Waves H-Comp", "Butch Vig Vocals", "Maag EQ4"} == set(cat)
    assert perfil.regla("delay_throws_voces")["roles"] == ["vox_acid", "vox_angel"]
