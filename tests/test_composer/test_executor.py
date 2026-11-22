"""El ejecutor contra un cliente falso que registra las llamadas (nunca toca Live)."""
from typing import Any, Dict, List

import pytest

from composer import rules
from composer.executor import Ejecutor, formatear_llamadas
from composer.model import AUTOMATIZACION
from composer.plan import crear_plan

S = lambda id_, tipo, n, **kw: {"id": id_, "tipo": tipo, "compases": n, **kw}  # noqa: E731


def B(bar):
    return (bar - 1) * 4.0


class FakeApi:
    """Imita las funciones live_* de server.py: registra (nombre, kwargs) y responde lo minimo."""

    def __init__(self, natural: float = 8.0, pending_polls: int = 2, ok: bool = True):
        self.calls: List[tuple] = []
        self.natural, self.pending, self.ok = natural, pending_polls, ok
        self.tracks = 0
        self.returns: List[str] = []

    def _rec(self, name, kw):
        self.calls.append((name, kw))

    def names(self):
        return [n for n, _ in self.calls]

    def kw(self, name):
        return [k for n, k in self.calls if n == name]

    def __getattr__(self, name):
        if not name.startswith("live_"):
            raise AttributeError(name)

        def fn(client, **kw):
            self._rec(name, kw)
            if name == "live_track_create":
                self.tracks += 1
                return {"index": self.tracks - 1, "name": kw["name"]}
            if name == "live_device_insert":
                return {"index": 0}
            if name == "live_return_list":
                return {"returns": [{"index": i, "name": n} for i, n in enumerate(self.returns)], "count": len(self.returns)}
            if name == "live_return_create":
                self.returns.append(kw.get("name"))
                return {"index": len(self.returns) - 1}
            if name == "live_clip_place_audio":
                span = self.natural if kw["start_beat"] > 1000 else kw["length_beats"]
                return {"ok": self.ok, "clips": [{"span": span}], "warnings": [] if self.ok else ["boom"]}
            if name == "live_utility_ensure_last":
                return {"target": {"device": 7, "param": "Output"}, "inserted": True}
            if name == "live_locator_status":
                self.pending -= 1
                return {"pending": max(0, self.pending), "errors": [], "cue_points": []}
            if name == "live_automation_record":
                return {"phase": "done", "errors": [], "lanes": []}
            return {"ok": True}
        return fn


def plan_de(make_ctx, secciones, roles):
    return crear_plan(make_ctx(secciones, roles=roles), nombre="x")


def test_dry_run_no_llama_a_la_api_y_devuelve_las_llamadas(make_ctx):
    plan = plan_de(make_ctx, [S("a", "intro", 8, suma=["kick", "top"])], ["kick", "top"])
    api = FakeApi()
    informe = Ejecutor(api, client=None, dry_run=True).ejecutar(plan)
    assert api.calls == []
    nombres = [l.nombre for l in informe.llamadas]
    assert nombres[0] == "live_song_set" and "live_track_create" in nombres
    assert "live_clip_place_audio" in nombres and "live_clip_create_midi" in nombres
    assert "live_clip_place_audio" in formatear_llamadas(informe.llamadas)


def test_primero_pistas_despues_clips_despues_locators_y_al_final_automatizacion(make_ctx):
    plan = plan_de(make_ctx, [S("a", "intro", 8, suma=["kick", "top", "pad", "atmo_trippy"]),
                              S("b", "breakdown", 16, quita=["kick"])], ["kick", "top", "pad", "atmo_trippy"])
    api = FakeApi()
    Ejecutor(api, None, sleep=lambda s: None).ejecutar(plan)
    n = api.names()
    assert n.index("live_track_create") < n.index("live_clip_place_audio") < n.index("live_locator_set_many")
    assert n.index("live_locator_set_many") < n.index("live_utility_ensure_last") <= n.index("live_automation_record")
    assert n.count("live_track_create") == 4


def test_loops_usan_el_warp_y_el_pitch_del_perfil(make_ctx):
    plan = plan_de(make_ctx, [S("a", "intro", 8, suma=["rumble", "top", "choir"])], ["rumble", "top", "choir"])
    api = FakeApi()
    Ejecutor(api, None, sleep=lambda s: None).ejecutar(plan)
    por_pista = {k["path"].split("\\")[-1]: k for k in api.kw("live_clip_place_audio")}
    assert por_pista["rumble.wav"]["warp_mode"] == 4        # complex
    assert por_pista["top.wav"]["warp_mode"] == 0           # beats
    assert por_pista["choir.wav"]["warp_mode"] == 6         # complex pro
    assert por_pista["top.wav"]["start_beat"] == 0.0 and por_pista["top.wav"]["length_beats"] == 32.0


def test_kick_es_midi_con_simpler_cargado(make_ctx):
    plan = plan_de(make_ctx, [S("a", "intro", 4, suma=["kick"])], ["kick"])
    api = FakeApi()
    Ejecutor(api, None, sleep=lambda s: None).ejecutar(plan)
    assert api.kw("live_track_create")[0]["kind"] == "midi"
    assert api.kw("live_device_insert")[0]["name"] == "Simpler"
    assert api.kw("live_simpler_load")[0]["playback_mode"] == 1
    midi = api.kw("live_clip_create_midi")[0]
    assert midi["length_beats"] == 16.0 and len(midi["notes"]) == 16


def test_mezcla_estatica_y_sends(make_ctx):
    plan = plan_de(make_ctx, [S("a", "intro", 8, suma=["atmo"])], ["atmo"])
    api = FakeApi()
    Ejecutor(api, None, sleep=lambda s: None).ejecutar(plan)
    assert api.kw("live_track_set_mixer")[0]["volume_db"] == -20
    envio = api.kw("live_track_set_send")[0]
    assert envio["db"] == -14 and envio["send"] == 2          # hall es el 3.er retorno
    assert [r["name"] for r in api.kw("live_return_create")] == ["Reverb", "Delay", "C-HALL"]


def test_oneshot_se_mide_se_borra_y_se_recoloca_anclado_al_final(make_ctx):
    plan = plan_de(make_ctx, [S("a", "intro", 32, suma=["kick"]), S("b", "groove", 32, suma=["top"])],
                   ["kick", "top", "reverse"])
    api = FakeApi(natural=6.0)
    Ejecutor(api, None, sleep=lambda s: None).ejecutar(plan)
    rev = [(i, c) for i, c in enumerate(api.calls)
           if c[0] == "live_clip_place_audio" and c[1]["path"].endswith("reverse.wav")]
    assert rev, "se coloco el reverse"
    medicion, final = rev[0][1][1], rev[1][1][1]
    assert medicion["start_beat"] > 1000                      # se mide lejos del tema
    idx = [n for n, _ in api.calls]
    assert "live_clip_delete_range" in idx[rev[0][0]:rev[1][0]]   # y se borra antes de recolocar
    assert final["start_beat"] == pytest.approx(B(33) - 6.0) and final["length_beats"] == 6.0
    # el span se mide una sola vez por archivo
    assert len([1 for _, c in rev if c[1]["start_beat"] > 1000]) == 1


def test_locators_se_sondean_hasta_que_no_quede_pendiente(make_ctx):
    plan = plan_de(make_ctx, [S("a", "intro", 8, suma=["kick"]), S("b", "drop", 8)], ["kick"])
    api = FakeApi(pending_polls=3)
    dormidas: List[float] = []
    Ejecutor(api, None, sleep=dormidas.append).ejecutar(plan)
    assert len(api.kw("live_locator_status")) == 3 and len(dormidas) >= 2
    assert [i["name"] for i in api.kw("live_locator_set_many")[0]["items"]] == ["a", "b"]


def test_automatizacion_usa_el_target_que_devuelve_ensure_last(make_ctx):
    plan = plan_de(make_ctx, [S("a", "intro", 8, suma=["kick"]), S("p", "breakdown", 16, quita=["kick"]),
                              S("s", "silence", 1, solo=[])],
                   ["kick", "atmo_trippy", "atmo"])
    api = FakeApi()
    Ejecutor(api, None, sleep=lambda s: None).ejecutar(plan)
    rec = api.kw("live_automation_record")
    assert rec
    objetivos = [ln["target"] for r in rec for ln in r["lanes"]]
    assert {"device": 7, "param": "Output"} in objetivos
    assert all(t != "volume" for t in objetivos)
    assert api.kw("live_utility_ensure_last")


def test_una_pasada_por_rango_contiguo(make_ctx, ctx_t02):
    plan = crear_plan(ctx_t02, nombre="T03")
    api = FakeApi()
    informe = Ejecutor(api, None, dry_run=True).ejecutar(plan)
    rec = [l for l in informe.llamadas if l.nombre == "live_automation_record"]
    rangos = sorted((r.kwargs["start_beat"], r.kwargs["end_beat"]) for r in rec)
    assert all(a[1] <= b[0] for a, b in zip(rangos, rangos[1:])), "las pasadas no se pisan"
    assert api.calls == []


def test_un_fallo_de_colocacion_se_informa_y_sigue(make_ctx):
    plan = plan_de(make_ctx, [S("a", "intro", 8, suma=["top"])], ["top"])
    api = FakeApi(ok=False)
    informe = Ejecutor(api, None, sleep=lambda s: None).ejecutar(plan)
    assert any("boom" in a for a in informe.advertencias)
    assert "live_locator_set_many" in api.names()


def test_sidechain_de_rumble_y_bajo_al_kick(make_ctx):
    plan = plan_de(make_ctx, [S("a", "intro", 16, suma=["kick", "rumble", "bass"])], ["kick", "rumble", "bass"])
    api = FakeApi()
    Ejecutor(api, None, sleep=lambda s: None).ejecutar(plan)
    sc = api.kw("live_compressor_set_sidechain")
    assert len(sc) == 2 and {k["source_track_name"] for k in sc} == {"KICK"}


def test_plan_con_lane_de_volumen_nunca_llega_al_ejecutor(ctx_t02):
    tl = rules.generar_timeline(ctx_t02)
    assert not [a for a in tl.de_tipo(AUTOMATIZACION) if a.datos["objetivo"] == "volume"]
