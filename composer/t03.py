"""T03: el plan de un tema tipo T02 generado desde el perfil (solo dry-run, no toca Live).

Uso: python -m composer.t03 [destino.md]   (escribe tambien el .json al lado)
"""
import sys
from pathlib import Path
from typing import List, Optional

from .model import Elemento
from .plan import Plan, crear_plan, plan_a_json, plan_a_markdown
from .profile import cargar_perfil
from .rules import Contexto
from .structure import construir_estructura

TEMPO = 134.0
Z = r"G:\LIbrerias\2026\Zenhiser Peaktime - Driving Techno\Zenhiser Peaktime - Driving Techno"
A = r"G:\LIbrerias\2026\Audentity Records - Peak Time Techno\Audentity Records - Peak Time Techno"
GH = r"G:\LIbrerias\2026\Ghosthack - Treptow Techno\Ghosthack - Treptow Techno"
DC = r"G:\LIbrerias\2026\Innovation Sounds - Drumcoding Techno\Drumcoding Techno\Samples\ROLLS E FILLS"

# Mismo material que T02 (docs/nexo/temas/T02_peaktime_completo_nuar.md). Los rolls, reverses e
# impactos usan UN archivo por rol (T02 variaba por limite): ver preguntas abiertas del handoff.
MATERIAL_T02 = {
    "kick": (Z + r"\one_shots\drums\kick\ZEN_PDT_kick_one_shot_nuar_G.wav", 0),
    "rumble": (Z + r"\loops\rumble_loops\ZEN_PDT_134_rumble_loop_nuar_F.wav", 0),
    "bass": (Z + r"\loops\bass_synth_loops\ZEN_PDT_134_bass_synth_loop_nuar_F.wav", 0),
    "drums": (Z + r"\loops\drum_loops\drum_loops_no_kick\ZEN_PDT_134_drum_loop_no_kick_nuar_F.wav", 0),
    "top": (Z + r"\loops\drum_loops\drum_top_loops\ZEN_PDT_134_drum_top_loop_nuar_F.wav", 0),
    "clap": (Z + r"\loops\perc_loops\ZEN_PDT_134_perc_clap_loop_nuar_F.wav", 0),
    "stab": (Z + r"\loops\stab_synth_loops\ZEN_PDT_134_stab_synth_loop_nuar_F.wav", 0),
    "atmo": (Z + r"\loops\atmo_loops\ZEN_PDT_134_atmo_loop_nuar_F.wav", 0),
    "lead": (Z + r"\loops\lead_synth_loops\ZEN_PDT_135_lead_synth_loop_hope_F.wav", 0),
    "vox_acid": (A + r"\Loops\Vocals\Female_Vocals\AU_PTT_130_vocal_loop_female_acid.wav", 0),
    "vox_angel": (A + r"\Loops\Vocals\Female_Vocals\AU_PTT_130_vocal_loop_female_angel_Dm.wav", 3),
    "choir": (A + r"\Loops\Vocals\Choirs\AU_PTT_130_vocal_loop_choir_search_Gm.wav", -2),
    "atmo_trippy": (A + r"\Loops\Atmos_Loops\AU_PTT_130_atmos_loop_wise_Fmin.wav", 0),
    "pad": (GH + r"\Loops\Pad Loops\Ghosthack-TT_133_F_Pad Loop_006.wav", 0),
    "snare_fill": (A + r"\One_Shots\Drums\Snares\AU_PTT_snare_one_shot_bright.wav", 0),
    "roll": (DC + r"\134_drumrolls_02.wav", 0),
    "roll_32": (DC + r"\134_drumrolls_01.wav", 0),
    "crash": (A + r"\One_Shots\Drums\Crash\AU_PTT_crash_one_shot_moody.wav", 0),
    "impacto": (Z + r"\one_shots\perc_fx_one_shots\ZEN_PDT_perc_fx_one_shot_stadium.wav", 0),
    "reverse": (A + r"\One_Shots\FX\Reverse_Atmos\AU_PTT_fx_reverse_atmos_one_shot_intro.wav", 0),
    "sweep_up": (Z + r"\one_shots\fx_one_shots\fx_sweep_up_one_shots\ZEN_PDT_fx_sweep_up_one_shot_rope.wav", 0),
    "sweep_down": (Z + r"\one_shots\fx_one_shots\fx_sweep_down_one_shots\ZEN_PDT_fx_sweep_down_one_shot_black.wav", 0),
    "riser_largo": (Z + r"\one_shots\fx_one_shots\fx_sweep_up_one_shots\ZEN_PDT_fx_sweep_up_one_shot_excite.wav", 0),
    "riser_corto": (A + r"\One_Shots\FX\Riser\AU_PTT_fx_riser_one_shot_basic.wav", 0),
}
# Largos naturales medidos en T02 (beats a 134 BPM); el ejecutor igual los vuelve a medir en Live.
LARGOS_T02 = {"sweep_up": 31.76, "sweep_down": 15.88, "riser_largo": 47.56, "riser_corto": 4.62 * 134 / 60}


def generar_plan_t03() -> Plan:
    perfil = cargar_perfil()
    elementos = {rol: Elemento(rol=rol, ruta=ruta, pitch=pitch, natural_beats=LARGOS_T02.get(rol))
                 for rol, (ruta, pitch) in MATERIAL_T02.items()}
    ctx = Contexto(perfil=perfil, estructura=construir_estructura(perfil, "t02_like"),
                   elementos=elementos, tempo=TEMPO)
    return crear_plan(ctx, nombre="T03", plantilla="t02_like")


def main(argv: Optional[List[str]] = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    destino = Path(argv[0]) if argv else Path(__file__).resolve().parent.parent / "docs" / "nexo" / "temas" / "T03_plan_generado.md"
    plan = generar_plan_t03()
    destino.write_text(plan_a_markdown(plan), encoding="utf-8")
    destino.with_suffix(".json").write_text(plan_a_json(plan), encoding="utf-8")
    print("plan escrito en %s (%d acciones)" % (destino, len(plan.acciones)))


if __name__ == "__main__":
    main()
