# T03: plan generado (techno-peak-time 0.3.0)

> Generado por `composer` desde el perfil, sin tocar Live. 134 BPM, 192 compases (5:44). Posiciones como `compás.tiempo` (1-based). **Nunca se automatiza volume (D-15):** el nivel va en el Output de un Utility al final de la cadena.

## Estructura

| Compás | Sección | Tipo | Largo | Capas que cambian |
|--------|---------|------|-------|-------------------|
| 1-16 | intro_a | intro | 16 | +kick, +top |
| 17-32 | intro_b | intro | 16 | +clap, +rumble, +drums (desde c.9) |
| 33-48 | groove_1 | groove | 16 | +bass |
| 49-64 | groove_2 | groove | 16 | +stab, +atmo |
| 65-96 | main | drop | 32 | -atmo |
| 97-127 | puente | breakdown | 31 | -kick, -rumble, -bass, -drums, -top, -clap, -stab |
| 128-128 | silencio | silence | 1 | solo: nada |
| 129-160 | drop_2 | drop | 32 | +kick, +rumble, +bass, +drums, +top, +clap, +stab, +lead, +choir (desde c.17) |
| 161-176 | outro_a | outro | 16 | -stab, -lead, -choir, -bass (desde c.9) |
| 177-192 | outro_b | outro | 16 | -rumble, -drums, -bass |

## Preparación

| Pista | Tipo | Roles | Nivel dB | Envíos (retorno: dB) |
|-------|------|-------|----------|----------------------|
| ATMO | audio | atmo | -20 | C-HALL: -14 |
| ATMO TRIPPY | audio | atmo_trippy | -20 | C-HALL: -10 |
| BASS | audio | bass | -12 | - |
| CHOIR | audio | choir | -22 | Reverb: -6, C-HALL: -8 |
| CLAP | audio | clap | -12 | - |
| CRASH | audio | crash | -16 | Reverb: -12 |
| DRUMS NO KICK | audio | drums | -12 | - |
| FX IMPACT | audio | impacto | -14 | - |
| KICK | midi | kick | -6 | - |
| LEAD | audio | lead | -16 | Reverb: -20 |
| PAD | audio | pad | -22 | C-HALL: -6 |
| FX REVERSE | audio | reverse | -14 | - |
| ROLLS | audio | roll, roll_32 | -12 | Reverb: -16 |
| RUMBLE | audio | rumble | -10 | - |
| SNARE FILL | midi | snare_fill | -17 | Reverb: -14 |
| STAB | audio | stab | -16 | - |
| FX | audio | sweep_up, sweep_down, riser_largo, riser_corto | -14 | - |
| TOP | audio | top | -14 | - |
| VOX ACID | audio | vox_acid | -12 | Reverb: -18 |
| VOX ANGEL | audio | vox_angel | -14 | C-HALL: -12 |

Retornos: Reverb, Delay, C-HALL.

| Dispositivo | Rol | Parámetros fijos | Nota |
|-------------|-----|------------------|------|
| EQ Eight | atmo | 1 Frequency A=250; 1 Filter On A=On, 1 Filter Type A=High Pass 12dB |  |
| Auto Filter | atmo | Resonance=29, Drive=14 | Filter Type: LP 24 dB SVF (confirmar el nombre del param en el catalogo) |
| EQ Eight | atmo_trippy | 1 Frequency A=250; 1 Filter On A=On, 1 Filter Type A=High Pass 12dB |  |
| Auto Filter | atmo_trippy | Resonance=29, Drive=14 | Filter Type: LP 24 dB SVF (confirmar el nombre del param en el catalogo) |
| Utility | atmo_trippy | - | último en la cadena (D-15) |
| EQ Eight | bass | 1 Frequency A=30, 2 Frequency A=200, 2 Gain A=-2; 1 Filter On A=On, 1 Filter Type A=High Pass 12dB, 2 Filter On A=On, 2 Filter Type A=Bell |  |
| Saturator | bass | Drive=2; Post Clip Mode=Soft Clip |  |
| Auto Filter | bass | Resonance=20, Drive=10 |  |
| Utility | bass | Bass Freq=120; Bass Mono=On | último en la cadena (D-15) |
| EQ Eight | choir | 1 Frequency A=220; 1 Filter On A=On, 1 Filter Type A=High Pass 12dB |  |
| Auto Filter | choir | Resonance=29, Drive=14 | Filter Type: LP 24 dB SVF (confirmar el nombre del param en el catalogo) |
| Utility | choir | - | último en la cadena (D-15) |
| EQ Eight | clap | 1 Frequency A=200; 1 Filter On A=On, 1 Filter Type A=High Pass 12dB |  |
| Auto Filter | clap | Resonance=20, Drive=10 |  |
| EQ Eight | crash | 1 Frequency A=300; 1 Filter On A=On, 1 Filter Type A=High Pass 12dB |  |
| EQ Eight | drums | 1 Frequency A=160; 1 Filter On A=On, 1 Filter Type A=High Pass 12dB |  |
| Auto Filter | drums | Resonance=20, Drive=10 |  |
| EQ Eight | impacto | 1 Frequency A=120; 1 Filter On A=On, 1 Filter Type A=High Pass 12dB |  |
| Simpler | kick | - |  |
| EQ Eight | kick | 1 Frequency A=25, 2 Frequency A=62, 2 Gain A=2, 3 Frequency A=250, 3 Gain A=-2, 4 Frequency A=3500, 4 Gain A=2; 1 Filter On A=On, 1 Filter Type A=High Pass 12dB, 2 Filter On A=On, 2 Filter Type A=Bell, 3 Filter On A=On, 3 Filter Type A=Bell, 4 Filter On A=On, 4 Filter Type A=Bell |  |
| Drum Buss | kick | Drive=17, Boom Amt=45, Boom Freq=55, Output=-3 |  |
| Utility | kick | Bass Freq=120; Bass Mono=On | último en la cadena (D-15) |
| EQ Eight | lead | 1 Frequency A=180; 1 Filter On A=On, 1 Filter Type A=High Pass 12dB |  |
| Auto Filter | lead | Resonance=20, Drive=14 |  |
| Auto Filter | master | - | HP en el master |
| Glue Compressor | master | Threshold=-8 | a mano: Attack: 30 ms; Ratio: 2:1; Release: 0.8 s o Auto |
| Limiter | master | Ceiling=-1 | a mano: Modo del techo: True Peak |
| EQ Eight | pad | 1 Frequency A=250; 1 Filter On A=On, 1 Filter Type A=High Pass 12dB |  |
| Utility | pad | - | último en la cadena (D-15) |
| EQ Eight | reverse | 1 Frequency A=200; 1 Filter On A=On, 1 Filter Type A=High Pass 12dB |  |
| EQ Eight | roll | 1 Frequency A=180; 1 Filter On A=On, 1 Filter Type A=High Pass 12dB |  |
| EQ Eight | rumble | 1 Frequency A=35, 2 Frequency A=250; 1 Filter On A=On, 1 Filter Type A=High Pass 12dB, 2 Filter On A=On, 2 Filter Type A=Low Pass 48dB |  |
| Auto Filter | rumble | Resonance=20, Drive=10 |  |
| Utility | rumble | Bass Freq=120; Bass Mono=On | último en la cadena (D-15) |
| Simpler | snare_fill | - |  |
| EQ Eight | snare_fill | 1 Frequency A=180; 1 Filter On A=On, 1 Filter Type A=High Pass 12dB |  |
| Auto Filter | snare_fill | Resonance=29, Drive=14 | Filter Type: LP 24 dB SVF (confirmar el nombre del param en el catalogo) |
| EQ Eight | stab | 1 Frequency A=180; 1 Filter On A=On, 1 Filter Type A=High Pass 12dB |  |
| Auto Filter | stab | Resonance=25, Drive=14 |  |
| EQ Eight | sweep_up | 1 Frequency A=200; 1 Filter On A=On, 1 Filter Type A=High Pass 12dB |  |
| EQ Eight | top | 1 Frequency A=220; 1 Filter On A=On, 1 Filter Type A=High Pass 12dB |  |
| Auto Filter | top | Resonance=20, Drive=10 |  |
| Utility | top | - | último en la cadena (D-15) |
| EQ Eight | vox_acid | 1 Frequency A=110, 2 Frequency A=3500, 2 Gain A=1.5, 3 Frequency A=10000, 3 Gain A=1.5; 1 Filter On A=On, 1 Filter Type A=High Pass 12dB, 2 Filter On A=On, 2 Filter Type A=Bell, 3 Filter On A=On, 3 Filter Type A=High Shelf |  |
| Compressor | vox_acid | Threshold=-18, Ratio=3, Attack=10, Release=120; Auto Release On/Off=Off |  |
| Auto Filter | vox_acid | Resonance=20, Drive=10 |  |
| EQ Eight | vox_angel | 1 Frequency A=100, 2 Frequency A=3500, 2 Gain A=1.5, 3 Frequency A=10000, 3 Gain A=1.5; 1 Filter On A=On, 1 Filter Type A=High Pass 12dB, 2 Filter On A=On, 2 Filter Type A=Bell, 3 Filter On A=On, 3 Filter Type A=High Shelf |  |
| Compressor | vox_angel | Threshold=-18, Ratio=3, Attack=10, Release=120; Auto Release On/Off=Off |  |
| Auto Filter | vox_angel | Resonance=20, Drive=10 |  |
| Utility | vox_angel | - | último en la cadena (D-15) |
| Compressor | bass | Threshold=-32, Ratio=4, Attack=1, Release=90; Auto Release On/Off=Off | sidechain desde KICK |
| Compressor | rumble | Threshold=-32, Ratio=4, Attack=1, Release=200; Auto Release On/Off=Off | sidechain desde KICK |

## Decisiones de arreglo

| Compás | Regla | Qué |
|--------|-------|-----|
| 64 | rumble_y_bajo | rumble y bajo caen solo aca (fin de 32 que entra al main); en los demas fines de 32 solo cae el kick |
| 64.3 | corte_previo_al_drop | corte de 2 tiempos antes de main: solo queda snare_fill |
| 192 | ultimo_compas | ultimo compas: kick entero, sin hueco ni fills |

Regla experimental `llamado_respuesta`: desactivada (sin instrumento asignado).

## Capas (clips de loop)

| Rol | Compases | Warp | Pitch |
|-----|----------|------|-------|
| top | 1-64.3, 65-97, 113-128, 129-193 | beats | 0 |
| clap | 17-64.3, 65-97, 129-193 | beats | 0 |
| rumble | 17-64, 65-97, 129-177 | complex | 0 |
| drums | 25-64.3, 65-97, 129-177 | beats | 0 |
| bass | 33-64, 65-97, 129-169 | beats | 0 |
| vox_acid | 41-49, 57-64.3, 73-81, 89-97, 137-145, 153-161 | complex_pro | 0 |
| atmo | 49-64.3, 97-128 | complex | 0 |
| stab | 49-64.3, 65-97, 129-161 | beats | 0 |
| pad | 97-128 | complex | 0 |
| atmo_trippy | 101-128 | complex | 0 |
| choir | 105-128, 145-161 | complex_pro | -2 |
| vox_angel | 109-125 | complex_pro | 3 |
| lead | 129-161 | beats | 0 |

## Eventos de arreglo

Kick: 3 clips MIDI, 604 notas; huecos por nivel de frase (regla `huecos_kick`).

| Compás | Rol | Qué | Regla |
|--------|-----|-----|-------|
| 1 | - | locator 'intro_a' | locators |
| 8 | snare_fill | 4 notas MIDI hasta 9 | fills.snare_fin_de_8 |
| 16.2 | roll | loop 16.2-17 | fills.roll_fin_de_16 |
| 17 | - | locator 'intro_b' | locators |
| 17 | crash | one-shot que empieza aca | crashes |
| 17 | reverse | one-shot que termina aca | transiciones.reverse |
| 24 | snare_fill | 4 notas MIDI hasta 25 | fills.snare_fin_de_8 |
| 32 | roll_32 | loop 32-33 | fills.roll_fin_de_32 |
| 33 | - | locator 'groove_1' | locators |
| 33 | crash | one-shot que empieza aca | crashes |
| 33 | reverse | one-shot que termina aca | transiciones.reverse |
| 40 | snare_fill | 4 notas MIDI hasta 41 | fills.snare_fin_de_8 |
| 48.2 | roll | loop 48.2-49 | fills.roll_fin_de_16 |
| 49 | - | locator 'groove_2' | locators |
| 49 | crash | one-shot que empieza aca | crashes |
| 49 | impacto | one-shot que empieza aca | transiciones.impacto |
| 56 | snare_fill | 4 notas MIDI hasta 57 | fills.snare_fin_de_8 |
| 64 | roll_32 | loop 64-65 | fills.roll_fin_de_32 |
| 65 | - | locator 'main' | locators |
| 65 | crash | one-shot que empieza aca | crashes |
| 65 | sweep_down | one-shot que empieza aca | transiciones.downlifter |
| 65 | sweep_up | one-shot que termina aca | transiciones.riser |
| 72 | snare_fill | 4 notas MIDI hasta 73 | fills.snare_fin_de_8 |
| 80.2 | roll | loop 80.2-81 | fills.roll_fin_de_16 |
| 81 | crash | one-shot que empieza aca | crashes |
| 81 | reverse | one-shot que termina aca | transiciones.reverse |
| 88 | snare_fill | 4 notas MIDI hasta 89 | fills.snare_fin_de_8 |
| 96 | roll_32 | loop 96-97 | fills.roll_fin_de_32 |
| 97 | - | locator 'puente' | locators |
| 97 | crash | one-shot que empieza aca | crashes |
| 97 | reverse | one-shot que termina aca | transiciones.reverse |
| 109 | reverse | one-shot que termina aca | puente.reverse |
| 113 | reverse | one-shot que termina aca | puente.reverse |
| 113 | snare_fill | 176 notas MIDI hasta 128 | puente.roll |
| 128 | - | locator 'silencio' | locators |
| 128 | riser_corto | one-shot que termina aca | transiciones.riser |
| 128 | riser_largo | one-shot que termina aca | transiciones.riser |
| 129 | - | locator 'drop_2' | locators |
| 129 | crash | one-shot que empieza aca | crashes |
| 129 | impacto | one-shot que empieza aca | transiciones.impacto |
| 129 | sweep_down | one-shot que empieza aca | transiciones.downlifter |
| 136 | snare_fill | 4 notas MIDI hasta 137 | fills.snare_fin_de_8 |
| 144.2 | roll | loop 144.2-145 | fills.roll_fin_de_16 |
| 145 | crash | one-shot que empieza aca | crashes |
| 145 | reverse | one-shot que termina aca | transiciones.reverse |
| 152 | snare_fill | 4 notas MIDI hasta 153 | fills.snare_fin_de_8 |
| 160 | roll_32 | loop 160-161 | fills.roll_fin_de_32 |
| 161 | - | locator 'outro_a' | locators |
| 161 | crash | one-shot que empieza aca | crashes |
| 161 | reverse | one-shot que termina aca | transiciones.reverse |
| 168 | snare_fill | 4 notas MIDI hasta 169 | fills.snare_fin_de_8 |
| 176.2 | roll | loop 176.2-177 | fills.roll_fin_de_16 |
| 177 | - | locator 'outro_b' | locators |
| 177 | crash | one-shot que empieza aca | crashes |
| 177 | reverse | one-shot que termina aca | transiciones.reverse |
| 184 | snare_fill | 4 notas MIDI hasta 185 | fills.snare_fin_de_8 |

## Automatización

| Rol | Destino | Compases | Puntos | Valores | Regla |
|-----|---------|----------|--------|---------|-------|
| top | Auto Filter / Frequency | 1-9 | 2 | 300 .. 16000 | entrada_filtrada |
| top | pan | 1-97 | 25 | -0.15 .. 0.15 | movimiento_pan |
| clap | Auto Filter / Frequency | 17-25 | 2 | 300 .. 16000 | entrada_filtrada |
| rumble | Auto Filter / Frequency | 17-25 | 2 | 300 .. 16000 | entrada_filtrada |
| drums | Auto Filter / Frequency | 25-33 | 2 | 300 .. 16000 | entrada_filtrada |
| bass | Auto Filter / Frequency | 33-41 | 2 | 300 .. 16000 | entrada_filtrada |
| vox_acid | Auto Filter / Frequency | 41-49 | 2 | 300 .. 16000 | entrada_filtrada |
| vox_acid | send Delay | 44.3-49 | 8 | -60 .. -8 | delay_throws_voces |
| atmo | Auto Filter / Frequency | 49-57 | 2 | 300 .. 16000 | entrada_filtrada |
| atmo | pan | 49-65 | 3 | -0.5 .. 0.5 | movimiento_pan |
| stab | Auto Filter / Frequency | 49-96.4.9 | 12 | 250 .. 12000 | escalera_filtro |
| vox_acid | send Delay | 60.3-61 | 4 | -60 .. -8 | delay_throws_voces |
| vox_acid | send Delay | 76.3-81 | 8 | -60 .. -8 | delay_throws_voces |
| vox_acid | send Delay | 92.3-97 | 8 | -60 .. -8 | delay_throws_voces |
| atmo | pan | 97-128 | 5 | -0.5 .. 0.5 | movimiento_pan |
| atmo_trippy | Utility / Output | 97-128 | 4 | -60 .. 0 | puente.fade |
| choir | Utility / Output | 97-128 | 5 | -30 .. 4 | puente.fade |
| pad | Utility / Output | 97-128 | 3 | -20 .. 6 | puente.cama |
| top | Utility / Output | 97-128 | 4 | -30 .. 0 | puente.fade |
| vox_angel | Utility / Output | 97-128 | 4 | -40 .. 0 | puente.fade |
| atmo_trippy | Auto Filter / Frequency | 101-109 | 2 | 300 .. 16000 | entrada_filtrada |
| atmo_trippy | pan | 101-128 | 5 | -0.5 .. 0.5 | movimiento_pan |
| choir | Auto Filter / Frequency | 105-113 | 2 | 300 .. 16000 | entrada_filtrada |
| vox_angel | Auto Filter / Frequency | 109-117 | 2 | 300 .. 16000 | entrada_filtrada |
| vox_angel | send Delay | 112.3-125 | 16 | -60 .. -8 | delay_throws_voces |
| top | Auto Filter / Frequency | 113-121 | 2 | 300 .. 16000 | entrada_filtrada |
| top | pan | 113-128 | 5 | -0.15 .. 0.15 | movimiento_pan |
| atmo | Auto Filter / Frequency | 120-128 | 6 | 700 .. 16000 | filtro_sigue_al_riser |
| atmo_trippy | Auto Filter / Frequency | 120-128 | 6 | 700 .. 16000 | filtro_sigue_al_riser |
| choir | Auto Filter / Frequency | 120-128 | 6 | 700 .. 16000 | filtro_sigue_al_riser |
| master | Auto Filter / Frequency | 120-128 | 3 | 20 .. 900 | puente.filtro_master |
| snare_fill | Auto Filter / Frequency | 120-128 | 6 | 700 .. 16000 | filtro_sigue_al_riser |
| lead | Auto Filter / Frequency | 129-160.4.9 | 3 | 400 .. 16000 | apertura_lead |
| stab | Auto Filter / Frequency | 129-160.4.9 | 8 | 600 .. 16000 | escalera_filtro |
| top | pan | 129-193 | 17 | -0.15 .. 0.15 | movimiento_pan |
| vox_acid | send Delay | 140.3-145 | 8 | -60 .. -8 | delay_throws_voces |
| vox_acid | send Delay | 156.3-161 | 8 | -60 .. -8 | delay_throws_voces |

## Pasadas de grabación

`automation.record` graba en tiempo real: una pasada por rango contiguo.

| # | Compases | Duración estimada | Lanes |
|---|----------|-------------------|-------|
| 1 | 1-97 | 2:52 | 11 |
| 2 | 97-128 | 0:56 | 16 |
| 3 | 129-193 | 1:55 | 4 |

Total de grabación: 5:42.

## Reglas aplicadas

| Regla | Acciones |
|-------|----------|
| apertura_lead | 1 |
| corte_previo_al_drop | 1 |
| crashes | 10 |
| delay_throws_voces | 7 |
| entrada_filtrada | 11 |
| escalera_filtro | 2 |
| fills.roll_fin_de_16 | 5 |
| fills.roll_fin_de_32 | 4 |
| fills.snare_fin_de_8 | 10 |
| filtro_sigue_al_riser | 4 |
| huecos_kick | 3 |
| locators | 10 |
| movimiento_pan | 6 |
| presencia | 33 |
| puente.cama | 1 |
| puente.fade | 4 |
| puente.filtro_master | 1 |
| puente.reverse | 2 |
| puente.roll | 1 |
| rumble_y_bajo | 1 |
| setup | 95 |
| transiciones.downlifter | 2 |
| transiciones.impacto | 2 |
| transiciones.reverse | 7 |
| transiciones.riser | 3 |
| ultimo_compas | 1 |

## Respuestas de Gabriel a las preguntas abiertas (2026-11-22)

1. **Fines de 32:** rumble y bajo caen **solo en el compás 64** (antes del
   Main). En los demás fines de 32 (32, 160) se quedan.
2. **Último compás del tema:** kick **entero**, sin hueco ni fills (como ya
   hace el compositor). En T02 hay que corregir el compás 192.
3. **Corte de 2 tiempos antes del Main (65):** sí (solo queda el snare fill).
4. **Pregunta y respuesta voz/stab:** probada y **rechazada en el stab**. La regla queda
   como experimental, desactivada por defecto y sin instrumento asignado.
5. **Filtro que sigue al riser** (cierra en 1 tiempo al empezar los últimos 8
   del puente, abre en curva): está bien así.
6. **FX:** variar archivos por transición (no uno por rol).
7. **Entrada filtrada** de elementos nuevos (8 compases, 300 Hz → 16 kHz): sí.
8. **Ecos de delay en las voces** como automatización grabada del send: sí.
   Además: **mezclar mejor las voces**.

9. **A-02 (plugins de terceros):** Gabriel usa FabFilter Pro-Q 3, Waves H-Comp, Butch Vig
   Vocals y Maag EQ4. El perfil los admite por nombre como opcionales (`mezcla.plugins`); el
   default sigue siendo nativo.
