# T01 — Loop de 32 compases, techno peak time (prueba)

> Primer tema de prueba del nexo. Pedido por Gabriel el 2026-11-22.
> Material: un solo pack, **Zenhiser Peaktime - Driving Techno**, kit `nuar`
> (`G:\LIbrerias\2026\...`, D-12). Testeo a oído: Gabriel (D-01).

## Brief

- Género: techno peak time. Sello de referencia: — . Referencia: — .
- Largo: 32 compases = 4 bloques de 8, cada uno en 2 sub-bloques de 4.
- Tempo **134 BPM**, tonalidad **F** (todo el kit `nuar` está en F).

## Material (kit `nuar`)

Base: `...\Zenhiser Peaktime - Driving Techno\Zenhiser Peaktime - Driving Techno\`

| Elemento | Archivo | Cómo entra |
|----------|---------|------------|
| Kick | `one_shots/drums/kick/ZEN_PDT_kick_one_shot_nuar_G.wav` | Simpler one-shot, negras, **-2 st (G → F)** |
| Rumble | `loops/rumble_loops/ZEN_PDT_134_rumble_loop_nuar_F.wav` | Audio, warp Complex (criterio de Gabriel) |
| Bajo | `loops/bass_synth_loops/ZEN_PDT_134_bass_synth_loop_nuar_F.wav` | Audio, warp Beats |
| Drums sin kick | `loops/drum_loops/drum_loops_no_kick/ZEN_PDT_134_drum_loop_no_kick_nuar_F.wav` | Audio, warp Beats |
| Top | `loops/drum_loops/drum_top_loops/ZEN_PDT_134_drum_top_loop_nuar_F.wav` | Audio, warp Beats |
| Clap | `loops/perc_loops/ZEN_PDT_134_perc_clap_loop_nuar_F.wav` | Audio, warp Beats |
| Stab | `loops/stab_synth_loops/ZEN_PDT_134_stab_synth_loop_nuar_F.wav` | Audio, warp Beats |
| Atmo | `loops/atmo_loops/ZEN_PDT_134_atmo_loop_nuar_F.wav` | Audio, warp Complex |
| Sweep up | `one_shots/fx_one_shots/fx_sweep_up_one_shots/` (uno sin tonalidad) | Audio, termina en el compás 25 |
| Sweep down | `one_shots/fx_one_shots/fx_sweep_down_one_shots/` (uno sin tonalidad) | Audio, arranca en el compás 25 |

Decisión de afinación (filtro D-13): la web afina el kick a la tonalidad del
tema y el rumble sigue al kick; el criterio de Gabriel es rumble contra kick.
Bajar el kick a F cumple ambos. **Basado en nombres de archivo, sin medir.**

## Estructura ("caminito")

Locators en cada sub-bloque de 4 compases.

| Compases | Bloque | Sub | Qué suena | Idea |
|----------|--------|-----|-----------|------|
| 1–4 | A | A1 | kick, top | Arranque DJ-friendly |
| 5–8 | A | A2 | + clap, + rumble | Aparece el groove grave |
| 9–12 | B | B1 | + bajo | Se arma el motor |
| 13–16 | B | B2 | + drums sin kick, + atmo | Groove completo |
| 17–20 | C | C1 | sin kick ni rumble: atmo, stab, top, clap | Respiro / tensión |
| 21–24 | C | C2 | + bajo, + sweep up (termina en 25) | Build hacia el drop |
| 25–28 | D | D1 | todo + sweep down en 25 | Drop |
| 29–32 | D | D2 | todo; compás 32 sin kick | Vuelta al loop |

## Mezcla inicial (puntos de partida, F4)

Kick -6 dB · rumble -10 · bajo -12 · drums sin kick -12 · top -14 · clap -12 ·
stab -16 · atmo -20 · FX -14. Master sin procesar. Sin grupos (la API no puede
crearlos; Gabriel puede agrupar a mano).

## Bitácora

- 2026-11-22: plan escrito. Faltan comandos de producción en el puente (T-003).
- 2026-11-22: **primer armado en Live** con T-003. Sweep up elegido: `rope`
  (31,76 tiempos, compases 17–25); sweep down: `black` (15,88 tiempos, desde
  el 25). Salió bien: tempo, loop, 10 tracks, volúmenes (±0,04 dB), kick en
  Simpler con clips MIDI exactos, tiling, FX.
  Fallas: (1) el recorte del último tile no acorta el clip en el Arrangement
  (DRUMS NO KICK suena en 17–20, ATMO hasta 28, RUMBLE en el 32); (2) los
  locators no se crearon (quedó uno suelto "1" en el compás 25). Corrección en
  curso (`Clip.crop()` + locators asincrónicos).
