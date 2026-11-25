from pathlib import Path

from composer.model import AUTOMATIZACION
from composer.t03 import generar_plan_t03, main


def test_el_plan_t03_es_de_192_compases_y_no_tiene_volume():
    plan = generar_plan_t03()
    assert plan.meta["total_compases"] == 192 and plan.meta["tempo"] == 134.0
    for a in plan.acciones:
        if a.tipo == AUTOMATIZACION:
            assert a.datos["objetivo"] != "volume"


def test_main_escribe_el_markdown_y_el_json(tmp_path: Path):
    destino = tmp_path / "T03_plan_generado.md"
    main([str(destino)])
    assert destino.read_text(encoding="utf-8").startswith("# T03")
    assert destino.with_suffix(".json").exists()


def test_dry_run_del_plan_t03_no_pide_volume_ni_mas_de_16_lanes_por_pasada():
    from composer.executor import Ejecutor

    informe = Ejecutor(None, None, dry_run=True).ejecutar(generar_plan_t03())
    nombres = [l.nombre for l in informe.llamadas]
    assert nombres.count("live_track_create") == 20 and "live_automation_record" in nombres
    for l in informe.llamadas:
        if l.nombre == "live_automation_record":
            assert len(l.kwargs["lanes"]) <= 16
            assert all(ln["target"] != "volume" for ln in l.kwargs["lanes"])


def test_t03_usa_archivos_variados_y_ecos_de_voz():
    from composer.model import CLIP_ONESHOT
    plan = generar_plan_t03()
    rutas = {a.datos.get("ruta") for a in plan.acciones if a.rol == "reverse" and a.tipo == CLIP_ONESHOT}
    assert len(rutas) >= 3
    assert any(a.regla == "delay_throws_voces" for a in plan.acciones)
    assert plan.meta["experimentales"] == {"llamado_respuesta": False, "roll_groove": False}


def test_los_archivos_alternativos_del_t03_existen_o_se_omite():
    import os
    from composer.t03 import MATERIAL_T02, ALTERNATIVAS_FX
    if not os.path.isdir(MATERIAL_T02["kick"][0].rsplit("\\", 4)[0]):
        return
    for rol, rutas in ALTERNATIVAS_FX.items():
        for r in rutas:
            assert os.path.exists(r), (rol, r)
