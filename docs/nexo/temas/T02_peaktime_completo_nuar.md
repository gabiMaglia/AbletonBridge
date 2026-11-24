# T02 — Tema completo, techno peak time

> Pedido por Gabriel el 2026-11-22, después de aprobar T01 ("una locura").
> Pide: tema entero, **voces**, un **puente trippy** con **algo épico sonando a
> lo lejos**, un **buen riser**, un **silencio** y **vuelta al groove**.
> Testeo a oído: Gabriel (D-01).

## Brief

- Techno peak time · 134 BPM · **F (asumido menor)** · 192 compases ≈ 5:44.
- Base: kit `nuar` de T01 (Zenhiser). Voces, coro y atmo trippy: Audentity
  Records - Peak Time Techno. Todo de `G:\LIbrerias\2026` (D-12).

## Material

Z = `Zenhiser Peaktime - Driving Techno\Zenhiser Peaktime - Driving Techno\`
A = `Audentity Records - Peak Time Techno\Audentity Records - Peak Time Techno\`

| Track | Archivo | Warp / pitch | Nota |
|-------|---------|--------------|------|
| KICK | Z `one_shots/drums/kick/..._nuar_G` | Simpler, nota 58 (-2 st) | Igual que T01 |
| TOP, CLAP, RUMBLE, BASS, DRUMS NO KICK, STAB, ATMO | kit `nuar` (T01) | como T01 | |
| LEAD (épico, drop 2) | Z `loops/lead_synth_loops/ZEN_PDT_135_lead_synth_loop_hope_F` | Beats | Elegido por tonalidad y nombre, sin escuchar |
| VOX ACID | A `Loops/Vocals/Female_Vocals/AU_PTT_130_vocal_loop_female_acid` | Complex Pro | Sin tonalidad en el nombre: rítmica |
| VOX ANGEL (puente) | A `.../Female_Vocals/AU_PTT_130_vocal_loop_female_angel_Dm` | Complex Pro, **+3 st (Dm → Fm)** | Experimento: puede sonar artificial; es "trippy" a propósito |
| CHOIR (lo épico a lo lejos) | A `Loops/Vocals/Choirs/AU_PTT_130_vocal_loop_choir_search_Gm` | Complex Pro, **-2 st (Gm → Fm)** | Bajo volumen + mucha reverb |
| ATMO TRIPPY | A `Loops/Atmos_Loops/AU_PTT_130_atmos_loop_wise_Fmin` | Complex | |
| FX | Z sweeps: `rope` (up), `black` (down), `excite` (riser largo, 47,56 tiempos); A `One_Shots/FX/Riser/AU_PTT_fx_riser_one_shot_basic` | Complex | |

Tonalidades: deducidas de los nombres de archivo, **sin medir** (límite
conocido, F2 pendiente). Las transposiciones de voz y coro son la apuesta más
arriesgada del tema.

## Estructura (compases)

| Compases | Sección | Qué pasa |
|----------|---------|----------|
| 1–16 | Intro A | kick + top (DJ-friendly) |
| 17–32 | Intro B | + clap, + rumble; drums sin kick desde el 25 |
| 33–48 | Groove 1 | + bajo; vox acid 41–48 |
| 49–64 | Groove 2 | + stab, + atmo nuar; vox acid 57–64; **compás 64 sin kick**; sweep up `rope` 57–64 |
| 65–96 | Main | todo el groove; vox acid 73–80 y 89–96; sweep down `black` en 65 |
| 97–127 | **Puente trippy** | sin kick/rumble/bajo/drums. Atmo nuar + atmo trippy; **coro a lo lejos** (-22 dB, send reverb alto); **vox angel 105–120 con delay**; top vuelve 113–127; **riser** `excite` + riser Audentity terminan en el 128 |
| **128** | **Silencio** | un compás sin nada (solo colas de reverb/delay) |
| 129–160 | Drop 2 | todo + **lead hope** (épico) + coro más bajo 145–160; vox acid 137–144 y 153–160; sweep down `black` en 129 |
| 161–176 | Outro A | sin stab, lead ni voces; bajo hasta el 168 |
| 177–192 | Outro B | kick + top + clap; rumble afuera |

Locators: Intro A, Intro B, Groove 1, Groove 2, Main, Puente, Silencio, Drop 2,
Outro A, Outro B.

## Mezcla inicial

Como T01, más: LEAD -16 dB · VOX ACID -12 (send reverb -18) · VOX ANGEL -14
(send delay -8) · CHOIR -22 (send reverb -6) · ATMO TRIPPY -20 · FX -14.
Necesita sends: ticket T-009.

## Bitácora

- 2026-11-22: plan escrito. Bloqueado por T-009 (sends) y reinicio de Live.
- 2026-11-22: **primer armado completo en Live.** OK: kick, groove, voces,
  coro, lead, sends y 10 locators (los locators asincrónicos funcionan).
  Fallas: (1) `crop()` no acorta clips de Arrangement y además invalida la
  referencia al clip → el último tile de TOP, ATMO, ATMO TRIPPY y CHOIR suena
  en el **compás 128 (silencio)**; rumble y bajo se pasan al 64. (2) El riser
  `excite` fue auto-warpeado con otro tempo y quedó partido en 2 copias; el
  riser Audentity también, metiéndose en el silencio. Corrección: T-003b
  (tiles parciales vía clip de Session + `duplicate_clip_to_arrangement`;
  one-shots sin warp).
- 2026-11-22: **feedback de Gabriel:** "no está mal". Falta: más risers,
  automatizaciones, algo de mezcla, más emoción. Trabaja por **capas**: se pule
  sobre lo que hay, pasada por pasada (ver "Plan por capas").

## Plan por capas

Cada capa se escucha antes de pasar a la siguiente (D-01).

| Capa | Qué agrega | Estado |
|------|-----------|--------|
| 1. Estructura | Reparar silencio del 128, colas del 64 y risers del puente | Script listo (T-003b) |
| 2. Transiciones | Riser/sweep antes de cada sección de 16/32, reverse atmos, downlifters después de cada drop | Pendiente |
| 3. Automatización | Filtros que abren en builds (atmo, stab, lead), swells de volumen y reverb en el coro, delay throws en voces | Pendiente: T-010 (envelopes de clip) |
| 4. Mezcla | Sidechain de rumble y bajo al kick, high-pass en todo lo que no es grave, cadena de master (EQ, glue, limiter) | Pendiente: T-010 (master + sidechain) |
| 5. Movimiento (emoción) | Definida por Gabriel: movimiento en **todo** el tema (ver abajo) | Pendiente |

### Capa 5 traducida a técnicas

| Escala | Técnica |
|--------|---------|
| Dentro de 8 compases | Algo cambia siempre: filtro o send que se mueve, paneo, variación en el compás 8 (kick que cae el último tiempo, eco de voz, reverse) |
| 8 → 16 → 32 | **Escalera**: cada iteración de una frase llega más lejos (el filtro abre un poco más, se suma una capa, la voz agrega un eco) |
| Entre sonidos | **Pregunta y respuesta**: voz y stab alternan compases; lead responde al coro; un elemento entra cuando otro se apaga |
| Transiciones | **Crossfades** de 4–8 compases (lo que entra sube mientras lo que sale se filtra), reverb compartida para pegar, todo en F |

- 2026-11-22: **capa 1 aplicada** (T-003b). Compás 128 en silencio total
  (verificado: ningún clip); compás 64 sin kick, rumble ni bajo. Tiles parciales
  vía Session + duplicate: todos con largo exacto.
  Pendiente: **risers cortados**. Con `warping=False`, el span del clip en el
  Arrangement queda fijo en el largo con que Live lo creó (32 tiempos para
  `excite`, que dura 47,56; 8 para el de Audentity, que dura 10,3): suena el
  principio del riser y se corta antes del clímax, ~4 compases antes del
  silencio. Arreglo propuesto (T-003c, después de T-010): riser con warp
  activado y warp markers forzados (tiempo 0 ↔ 0 s, tiempo 47,56 ↔ 21,30 s),
  loop = 47,56, vía Session + duplicate, para que termine justo en el 128.

- 2026-11-22: **feedback:** "casi no se nota el cambio, un solo canal de FX con
  dos sonidos". Correcto: la capa 1 solo reparó. Risers: `add_warp_marker`
  acepta un objeto WarpMarker (no floats ni dict) pero da "Segment length out
  of range" → T-003d (cadena de estrategias) + T-011 (`bridge.reload`).
- 2026-11-22: **capa 2, parte loops** (FX en tempo, sin el problema de
  one-shots). Dos canales nuevos:
  - FX BUILD (Drumcoding, 134 BPM): fx_04 29–33, fx_03 91–97, fx_09 120–128
    (Live le adivinó otro tempo: 11 compases comprimidos en 8, suena más
    rápido), fx_05 157–161.
  - FX TEXTURA (Ghosthack, 133 BPM): Fx_003 45–49, Fx_007 77–81, Fx_012
    141–145, Fx_018 173–177.
  Elegidos por nombre y largo, sin escuchar. Pendiente (one-shots, T-003d):
  reverse atmos de Audentity antes de 17, 65, 97, 145 y 177; impactos en 49 y
  129; risers `excite` + Audentity al 128.

- 2026-11-22: tras reinicio (puente 0.2.0 con `bridge.reload`). One-shot con
  cadena T-003d: las 3 estrategias fallan. **Diagnóstico real:** Live auto-warpea
  el riser metiendo el sample ENTERO en su largo adivinado (marker 32 ↔ 21,30 s
  = fin del sample) + un "marcador sombra" en 32,03125 que no se puede borrar.
  O sea: con warp el riser suena **completo pero comprimido**; el corte solo
  pasaba sin warp. Arreglo correcto pendiente: mover el marker final sin tocar
  la sombra.
- **Risers colocados completos (con warp) terminando en el 128:** `excite`
  120–128 (8 compases en vez de 12, ~1,5x) y Audentity 126–128.
- **Capa 2, parte one-shots:** técnica medir → borrar → recolocar para que
  terminen/empiecen en el compás. FX REVERSE (reverse atmos/perc de Audentity
  terminando en 17, 33, 65, 97, 145, 177) y FX IMPACT (Zenhiser `stadium` en
  49, `serious` en 129).

- 2026-11-22: Gabriel pregunta si se aplicó el movimiento dentro de los loops:
  **no** (capa 2 eran transiciones). **Capa 3 aplicada** (script
  `layer3_t02.py`, envelopes de clip T-010, 17 rangos re-colocados, 0 fallas
  según la API; los envelopes de Arrangement no se pueden releer → confirma el
  oído):
  - STAB: Auto Filter (`AutoFilter2`) en **escalera** por frase de 8 (49–96:
    300→1,2k … 1,2k→12k Hz; 129–160: 600→3k … 2,5k→16k) + golpe de reverb en
    el último compás de cada frase.
  - LEAD (129–160): filtro abre 400 Hz → 2,5 kHz → 16 kHz en 32 compases.
  - TOP: paneo ±0,15 que alterna cada 4 compases.
  - ATMO y ATMO TRIPPY: paneo ±0,5 cada 8 compases en **fase opuesta**
    (diálogo); ATMO TRIPPY con swell -30 → -18 dB en el puente.
  - CHOIR: puente -34 → -18 dB y reverb -12 → -2 dB (se acerca de a poco);
    145–160 -28 → -20 dB.
  - VOX ACID: **eco de delay** en el último medio compás de cada frase de 4.

- 2026-11-22: **feedback sobre capa 3:** "no se siente la diferencia". Pide
  variantes y repiques en los cambios de compás, silencios / ausencia de kick y
  FX más dinámicos marcando esos momentos ("detalles que hacen el todo").
  Diagnóstico: el mapeo del filtro es correcto (300 Hz / 1,2 kHz / 12 kHz
  exactos, LP 24 dB); sospecha: en Arrangement los envelopes de clip actúan
  como **modulación relativa**, no automatización absoluta (a investigar).
- 2026-11-22: **capa 4 aplicada: detalles de frase** (`layer4_t02.py`):
  - KICK re-escrito con huecos: fin de 8 → sin el 4to tiempo; fin de 16 → sin
    3ro y 4to; fin de 32 → compás entero sin kick.
  - SNARE FILL (Simpler, snare Audentity `bright`): 4 semicorcheas en
    crescendo (vel 70→118) en el 4to tiempo de los fines de 8 (compases 8, 24,
    40, 56, 72, 88, 136, 152, 168, 184).
  - ROLLS (Drumcoding 134): `drumrolls_02` (¾ compás) al final de 16, 48, 80,
    144, 176; `drumrolls_01` (1 compás) en 32, 64, 96, 160; `drumrolls_05`
    (8,25 compases) del 119,75 al silencio del 128.
  - CRASH (Audentity `moody`) en el 1 de 17, 33, 49, 65, 81, 97, 129, 145,
    161, 177.
  Gabriel pide además **investigar en internet** cómo se hace esto en el
  género (agente lanzado; resultado va a F4).

- 2026-11-22: **criterio del puente** (Gabriel): tensión continua todo el
  tiempo; los elementos entran de a poco, salvo que lleguen como culminación
  de un riser. Revisión del puente actual contra el criterio:
  - 97: ATMO, ATMO TRIPPY y CHOIR entran juntos (el build `fx_03` culmina en
    97, así que solo uno de ellos puede entrar de golpe).
  - 105: VOX ANGEL entra de golpe, sin riser → viola el criterio.
  - 113: TOP vuelve de golpe, sin riser → viola el criterio.
  - La densidad rítmica no crece de forma continua: el roll de 8 compases
    arranca recién en 120.
  Rediseño pendiente del resultado de la investigación (cómo hacer fade-ins
  confiables: envelopes de clip vs automatización de track).

- 2026-11-22: **investigación de arreglo** (F4, sección "Detalles de arreglo").
  Respuesta clave: en Arrangement los envelopes de clip son **solo modulación**
  (relativa a la perilla; en volumen/sends nunca la supera) → la escalera del
  STAB no tenía margen (Auto Filter con la frecuencia casi al máximo). La
  automatización real va en la lane del track → T-012 (`automation.record`,
  grabación en tiempo real, método del spike 2).
- 2026-11-22: **puente v2 aplicado** (`bridge_v2_t02.py`), solo ediciones:
  - Entradas escalonadas cada 4 compases: ATMO 97 (culmina `fx_03`, puede
    entrar de golpe) · ATMO TRIPPY 101 · CHOIR 105 · VOX ANGEL 109–124 ·
    TOP 113.
  - VOX ANGEL y TOP llegan traídos por reverses que terminan justo en 109
    (`expand`, desde 107) y 113 (`riot`, desde 111).
  - Roll de Drumcoding de 8 compases quitado; en su lugar **roll MIDI propio**
    (SNARE FILL) que acelera sin cortes de 113 a 128: negras (vel 35→60),
    corcheas (55→85), semicorcheas (80→105, luego 100→115) y fusas en el 127
    (110→127). 176 notas; termina en el silencio.
  - Pendiente T-012: fade-ins de cada entrada y high-pass que abre en 8
    compases.

- 2026-11-22: **feedback puente v2:** "muchísimo mejor, progreso abismal".
  Todavía le falta **profundidad** y **continuidad**.
- 2026-11-22: **profundidad y continuidad, primera pasada:**
  - Return nuevo **C-HALL** (Live lo nombró "C-C-HALL") con Hybrid Reverb:
    Dark Hall, Decay 8 s, Size 85 %, Predelay 40 ms, low cut 250 Hz, 100 % wet,
    return a -4 dB. Gotcha: el `display` de tiempos va en **ms** (8 → 100 ms;
    hay que pedir 8000).
  - **PAD** (Ghosthack `133_F_Pad Loop_006`) como cama continua 97–127,
    -22 dB, send C -6 dB.
  - Sends a C-HALL: CHOIR -8, ATMO TRIPPY -10, VOX ANGEL -12, ATMO -14 dB.

- 2026-11-22: **Gabriel lee como referencia:** bajó SNARE FILL a -17 dB (muy
  fuerte) y agregó su propio arreglo: el mismo Auto Filter (LP 24 dB SVF,
  reso 29 %, drive 14 %) en ATMO, ATMO TRIPPY, CHOIR y SNARE FILL, cortando
  los agudos rápido y volviéndolos a abrir **con el movimiento del riser**:
  donde termina y empieza el sonido, se filtra todo. → criterio en F4.
- 2026-11-22: **automatización real del puente grabada** (lanes de track):
  ATMO TRIPPY fade-in 101–105; CHOIR entra a -50 dB en 105 y crece a -16 al
  127 (vuelve a -22 en el 128); VOX ANGEL fade-in 109–111; TOP fade-in
  113–117; PAD crece -40 → -16 en todo el puente; master Auto Filter HP
  20 Hz → 900 Hz del 120 al 128 y vuelve a 20 Hz en el silencio.

- 2026-11-22: **regla D-15** (Gabriel, inquebrantable): nunca automatizar el
  volumen/ganancia del track; usar un Utility al final de la cadena. Gabriel
  borró a mano las lanes de volumen (la API no puede borrar lanes). Faders
  devueltos a la mezcla: TOP -14, CHOIR -22, ATMO TRIPPY -20, VOX ANGEL -14,
  PAD -22. CHOIR 145–160 re-colocado sin la envolvente de volumen de la capa
  3. Queda vigente la lane del Auto Filter HP del master (no es volumen).
  Pendiente: regrabar los fades del puente sobre un Utility al final de cada
  cadena (T-013 agrega `utility.ensure_last`).
- 2026-11-22: **fades del puente regrabados respetando D-15**: Utility al final
  de la cadena (`utility.ensure_last`; el nivel se llama `Output` en la API,
  "Gain" en la interfaz) en ATMO TRIPPY, CHOIR, VOX ANGEL, TOP y PAD; lanes
  sobre `Output` relativas a 0 dB (faders intactos en la mezcla). Misma forma
  que antes: ATMO TRIPPY -60 → 0 (101–105), CHOIR -30 → -4 → +4 (105–128),
  VOX ANGEL -40 → 0 (109–111), TOP -30 → 0 (113–117), PAD -20 → +6 (97–128).
- 2026-11-22: Gabriel: "sí, está mucho mejor" (puente con fades en Utility).
- 2026-11-22: **escalera grabada en lane real** (pasada 49–161, ~3,5 min):
  STAB Auto Filter Frequency en diente de sierra por frase de 8 (49–96:
  250→900 … 1,5k→12k Hz; 129–160: 600→3k … 2,5k→16k), 1908 escrituras; LEAD
  400 Hz → 2,5 kHz (145) → 16 kHz (160,9), 544 escrituras. Receta de Gabriel
  aplicada como valores fijos: STAB reso 25 % / drive 14 %; LEAD reso 20 % /
  drive 14 %.

- 2026-11-22: **capa de mezcla base** (`mix_base_t02.py`):
  - **Sidechain** (primera vez en Live real, funciona): Compressor en RUMBLE y
    BASS con entrada de sidechain = KICK (Post FX); Threshold -32 dB, Ratio 4,
    Attack 1 ms, Release 90 ms, Auto Release off.
  - **High-pass** con EQ Eight (banda 1, low cut) por rol: TOP 220, CLAP 200,
    DRUMS NO KICK 160, STAB 180, ATMO/ATMO TRIPPY/PAD 250, CHOIR 220, VOX ACID
    180, VOX ANGEL 200, LEAD 180, FX 200, FX TEXTURA 250, FX IMPACT 120, SNARE
    FILL 180, ROLLS 180, CRASH 300 Hz. EQ al principio de la cadena (después
    del instrumento en tracks MIDI) para que el Utility siga último (D-15).
  - **Master:** Auto Filter (HP del puente) → Glue Compressor (ratio 2,
    threshold -8 dB, attack 10) → Limiter (ceiling -1 dB, release auto).
  - Gotchas: Live no deja efectos de audio antes del instrumento; el Glue no
    tiene "Makeup" (su nivel es `Output`); Ratio del Glue es cuantizado
    (0 = 2).
  - **Error corregido en el momento:** el script eligió el tipo de filtro por
    texto ("Low" + "48") y puso **Low Pass 48dB** en los 19 tracks (sonaban
    apagados). EQ Eight en Live 12.4: 0 High Pass 48dB, 1 High Pass 12dB,
    2 Low Shelf, 3 Bell, 4 Notch, 5 High Shelf, 6 Low Pass 12dB, 7 Low Pass
    48dB. Corregido a 0 (High Pass 48dB) en todos. Lección: elegir valores
    cuantizados por nombre EXACTO, nunca por coincidencia parcial.

- 2026-11-22: **motor T-014 midió el kit:** kick G1 (49,0 Hz, confianza
  alta) → -2 st = F1 confirmado; rumble ambiguo: dominante A1 (~54 Hz) con
  parcial F1 (confianza baja); bajo F2. Si el rumble suena en A, hoy queda una
  3ra mayor sobre el kick. **A/B para el oído de Gabriel:** track nuevo
  `RUMBLE B (-4 st)` (mismos rangos, Complex, -4 st = A→F, misma cadena de
  sidechain), **muteado**. Comparar mutando RUMBLE / desmutando RUMBLE B.
- 2026-11-22: **A/B rumble:** Gabriel: "está bien el -4, ni se nota". Queda
  **RUMBLE B (-4 st) activo** y el RUMBLE original muteado (no se borra).
  Primer resultado del filtro D-13 medición vs oído: la medición (rumble en A)
  no contradice al oído; la diferencia es sutil en este sample porque el rumble
  es un pulso sin fundamental única.
- 2026-11-22: **correcciones de mezcla** según la investigación dedicada (F4,
  "Estándares de mezcla y master"; `mix_fix_t02.py`):
  - Master: Glue attack 10 → **30** ms (deja pasar el ataque del kick);
    Limiter en modo **True Peak**, techo -1 dB.
  - Sidechain del rumble (ambos): release 90 → **200 ms**. Bajo sin cambios.
  - High-pass: pendiente 48 → **12 dB/oct** en los 19 tracks (EQ Eight no
    ofrece 24). Voces: VOX ACID 180 → 110 Hz, VOX ANGEL 200 → 100 Hz.
  - **Graves en mono** < 120 Hz: Utility (último, D-15) con Bass Mono en KICK,
    RUMBLE, RUMBLE B y BASS.
  - Pendiente: thresholds por reducción de ganancia (Glue 1–2 dB, limiter
    ≤3 dB, sidechain rumble 6–12 dB, bajo 4–6 dB) y faders por picos
    medidos: requiere medir (meters de Live o render + motor T-014).
- 2026-11-22: compás 192 corregido: kick entero (respuesta de Gabriel).

- 2026-11-22: **la PC de Gabriel se colgó y reinició**; el set reabierto (lo
  último que guardó) muestra cambios suyos:
  - **STAB:** volvió a estirar los clips (no le gustó la pregunta/respuesta
    en ese instrumento) y sumó **FabFilter Pro-Q 3** y **Waves H-Comp**.
  - **Voces agrupadas** (`15-Group`) con Butch Vig Vocals, Maag EQ4 y Limiter
    (mezcla de voces hecha por él); VOX ANGEL estirada hasta el 127.
  - **RUMBLE B (-4 st) no está**; el RUMBLE original suena sin transponer.
  - Los ecos de delay grabados quedaron a medias (la grabación se cortó
    porque Gabriel tocó el transporte); hay que regrabarlos.
- 2026-11-22: **ecos de delay regrabados** en dos pasadas (41–97 y 97–161),
  completos: VOX ACID al final de cada frase de 4 (y al 64 antes del corte),
  VOX ANGEL en 116 y 124. Return B: ping-pong 3/16, feedback 30 %, EQ 400 Hz –
  3 kHz.
- 2026-11-22: **movimiento en el groove (1–96)**, pedido por Gabriel:
  - Respiración: 27 cortes de 1 tiempo al final de cada frase de 8 en TOP,
    BASS y RUMBLE (junto con el hueco de kick); el 64 conserva su corte de 2.
  - Variación: track **PERC VAR** (Simpler, percusión Zenhiser `doubler`, HP
    200 Hz, -16 dB) con semicorcheas sincopadas en 8, 24, 40, 56, 72, 88.
  - Entradas con filtro (aprobado): Auto Filter LP en CLAP (17→25), DRUMS NO
    KICK (25→33) y BASS (33→41, 200 Hz → 18 kHz), lanes grabadas.
  - Detalle chico: golpe de reverb (send A -6 dB) en el último tiempo del clap
    en 20, 28, 36, 44, 52, 60, 68, 76, 84, 92.
- 2026-11-22: Gabriel: "se siente mucho mejor, seguí" (movimiento en el groove).
- 2026-11-22: **mismo movimiento en drop 2 y outro (129–192):** 18 cortes de
  respiración (TOP, BASS, RUMBLE; el 192 conserva el kick entero) y PERC VAR
  en 136, 152, 168, 184.
- 2026-11-22: **receta de Gabriel en los builds** (filtro siguiendo al riser):
  Auto Filter LP con reso 29 % y drive 14 % en TOP (nuevo), CLAP y DRUMS NO
  KICK; al empezar el riser cierra en 1 tiempo a 600 Hz y abre en curva (1,2k
  → 2,8k → 6,5k → 16k) hasta el drop. Grabado en 29–33, 57–65 y 157–161.
  Riesgo: se fijó Frequency a mano en tracks con lanes ya grabadas → Live puede
  marcar la automatización como "override" (botón Re-Enable Automation).
- 2026-11-22: Gabriel: la receta en los builds "se siente, está bien". Pide
  combinarla con un **high-pass al kick** que empiece 2–3 golpes después de
  que cierra el filtro → Auto Filter HP en KICK (antes del Utility): 20 Hz
  hasta 3 tiempos después del inicio del riser, sube a 300 Hz hasta el drop y
  vuelve a 20 Hz en el drop. Grabado en 29–33, 57–65, 157–161.

- 2026-11-22: **preview I:\TEST2.wav** (export de Gabriel, 24 bit, sin dither):
  -28,7 LUFS integrado, -13,0 dBTP, LRA 4,8 LU; short-term máx -26,7.
  Gabriel corrige: **la mezcla es premaster** (D-16: pico ~-6 dBFS, -18 a
  -23 LUFS, sin limiter de volumen); el mastering va aparte.
- 2026-11-22: **medidores (T-017) en Live real:** `meter.capture` del tema
  entero OK (30 destinos). La escala de `output_meter_*` es la del display de
  Live (casi lineal en dB, comprimida arriba). Calibración bajando el master
  -9/-15/-21/-27/-33 dB en el Main: raw 0,702/0,650/0,571/0,488/0,407 →
  ~0,0087/dB cerca del tope, ~0,0135/dB en la zona media. Ancla: master -9 dB
  ↔ pico del render -13,0 dBFS.
  - El **master estaba en -9 dB** → subido a **-2 dB** (pico premaster
    estimado ~-6 dBFS, ~-21,7 LUFS). **Limiter del master apagado** (D-16);
    Glue suave queda.
  - Balance por picos: RUMBLE ~+5 dB y BASS ~+1,5 dB sobre el kick (la
    investigación pide bajo 3–6 dB debajo del kick). Sesgo: el rumble pica
    entre golpes (sidechain suelto). Decide el oído de Gabriel.
- 2026-11-22: Gabriel escucha el balance kick / rumble / bajo en el Main:
  "se siente bien". Filtro D-13: la medición por picos sugería bajar rumble y
  bajo, pero el oído lo valida tal cual (los picos del rumble entre golpes
  sesgan la comparación). **Balance aprobado.**
- 2026-11-22: **premaster verificado** (render nuevo, I:\TEST2.wav): **-21,66
  LUFS** integrado, **sample peak -6,01 dBFS**, **true peak -5,97 dBTP**, LRA
  4,85 LU. Short-term máx por sección: Intro -20,8 · Groove -20,4 · Main
  -19,9 · Puente -20,1 · Drop2 -19,6 · Outro -20,7. Coincide con lo predicho
  por la calibración de medidores (pico -6, ~-21,7 LUFS). **Cumple D-16.**
  Nota: el export duró 743 s (el tema son ~344 s): el rango de export llega al
  final del Arrangement; para el master conviene exportar 1–193 + cola.

## Mastering (etapa aparte, D-16) — set "T02 Master"

- 2026-11-22: Gabriel abrió un set nuevo y cargó el premaster I:\TEST2.wav en
  el Arrangement **sin warp** (hubo que apagar "Auto-Warp Long Samples": Live
  le había adivinado ~162 BPM). Clip 1 → ~198,8 (354 s: tema + cola). Tempo
  134. El bridge no logra colocar un archivo largo sin warp (one-shot falla:
  sombra de warp markers / span de creación) → paso manual.
- **Cadena v1 en el master:** Utility +6 dB → EQ Eight (HP 12 dB en 25 Hz) →
  Glue (ratio 2, attack 30, threshold -8 dB) → Saturator (drive 3 dB, Soft
  Clip) → Limiter (True Peak, techo -1 dB, input +4 dB). Objetivo club
  ~-8,5 LUFS / -1 dBTP; primera pasada conservadora, se ajusta midiendo.
  Gotcha: Saturator `Post Clip Mode` = No Clip / Soft Clip / Hard Clip.
- **Master v1 medido** (`I:\Sin título1.wav`, 356,1 s, 48 kHz/24 bit):
  **-11,1 LUFS** integrado, TP **-0,95 dBTP** (pasa 0,05 el techo de -1 → en
  v2 el techo va a -1,2), LRA 3,0, PLR 10,2. Short-term mediana por sección:
  Intro -11,8 · Groove A -11,6 · Groove B -10,7 · Main 1 -10,4 · Puente -13,4
  (máx -9,05, el pico más fuerte del tema) · Build -10,1 · Drop 2 -10,9. Crest
  en los drops ~12 dB: queda margen para subir ~2,5 dB hacia -8,5.
- **Alerta:** `I:\TEST2.wav` fue modificado a las 22:15, 1,5 min antes del
  render del master. Hoy mide 743 s, pico 0 dBFS, TP +4,2 dBTP: ya **no** es
  el premaster medido antes (-21,66 LUFS, pico -6,01). Pendiente confirmar con
  Gabriel si se pisó el archivo y desde qué fuente salió el master v1.
  **Confirmado:** Gabriel re-exportó encima. Los primeros 356 s son el tema a
  -20,56 LUFS (+1,1 dB vs el anterior) con **un pico aislado a 0 dBFS / +4,2
  dBTP en el segundo 262,2 (compás ~147, build)**; después vienen 387 s de
  material bajo (-33,5 LUFS) que no son parte del tema.
- **Oído de Gabriel sobre v1:** en sus monitores suena bien; en auriculares y
  otros parlantes **los graves se empastan y las voces se pierden** (falta de
  traducción). La medición coincide: la cadena v1 corrió el balance hacia
  abajo (60-300 Hz +0,4/+0,5 dB, 4-20 kHz -0,7/-1,4 dB vs premaster en Main 1 y
  Drop 2). Glue y Saturator reaccionan a la energía grave y oscurecen el
  resto. Antecedente: en la mezcla los picos de rumble/bajo ya estaban por
  encima del kick (aprobado en sus monitores, que probablemente muestran menos
  grave del que hay).
- Corrección a mi alerta: el export de 743 s no es nuevo (el premaster anterior
  ya duraba eso: el rango llega al final del Arrangement). Lo nuevo es +1,1 dB
  y el ruido del 147.
- **Ruido a 0 dBFS en el Drop 2:** ráfaga de ~450 ms, banda ancha cargada de
  agudos (5-16 kHz a 0 dBFS), en **147,37 → 147,62** (tiempos 2,5–3,5 del
  compás 147; 262,15–262,60 s). Ningún clip arranca ahí (los clips activos
  empiezan en el 145) → sospecha de glitch de plugin en el render. Sin
  identificar la pista todavía. **Gabriel: en Live no suena** → es un glitch
  del render, no de la mezcla. Regla: después de cada export, escanear picos
  aislados antes de masterizar.
- **Agudos en transiciones** (escaneo 5–16 kHz por compás): fuera del 147, los
  picos están en los fines de frase antes de las entradas (32, 48, 63/64,
  160), donde suenan ROLLS, FX REVERSE, FX BUILD, FX sweep y CRASH. Unos 2 dB
  sobre la mediana del groove. El puente trippy (97–127) no tiene picos de
  agudos.
- **Mezcla v2 (traducción) aplicada** en el set T02, a pedido de Gabriel:
  - Faders estáticos: RUMBLE -9,9 → **-12** dB, BASS -12 → **-13,5** dB,
    grupo de voces (15-Group) 0 → **+1,5** dB.
  - EQ Eight nuevo al principio de RUMBLE (campana 250 Hz, -2,5 dB) y de BASS
    (campana 300 Hz, -1,5 dB), Q por defecto 0,71 (el parámetro
    `Resonance A` no se pudo setear por display).
  - High shelf -2,5 dB en 7 kHz (banda 8 del EQ existente) en ROLLS, FX BUILD,
    FX REVERSE, CRASH y FX.
  - Gotcha del bridge: un script externo hizo timeout en `state.get` mientras
    el servidor MCP tenía la conexión abierta; con las tools MCP funcionó.
