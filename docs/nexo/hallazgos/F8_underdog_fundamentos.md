# F8 — Underdog: fundamentos de producción (spike T-028, parte 2)

> Fecha: 2026-11-25. Fuente: 6 videos de **Underdog Electronic Music School** (Oscar), con transcripción + parámetros leídos en pantalla frame a frame.
> Material crudo: `docs/nexo/underdog/*.md`, `*.params.md`, `bases/*.yaml`. Complementa a `F7_tutoriales_youtube.md` (otros 5 videos de Oscar; no se repite lo de ahí).
> **Nada de esto toca el perfil todavía**: los cambios los decide Gabriel (D-01, D-13). Las secciones 4 y 5 son propuestas.

**Convenciones de evidencia.** `D` = dicho (transcripción, sin valor en pantalla) · `P` = en pantalla (con confianza alta/media/baja y frame; el frame `0408_b` = 04:08) · `O` = opinión del autor. Etiquetas de video: `4R` minimalismo, `MT` teoría, `PM` polímetros, `SY` síntesis, `RM` rumble, `TG` trance gate. Nombres API de device verificados por el pedido: Compressor=`Compressor2`, Utility=`StereoGain`, EQ Eight=`Eq8`, Auto Filter=`AutoFilter2`; el resto de los nombres de device van como los muestra Live y su nombre API **no está verificado**.

---

## 1. Índice de los 6 videos

| Etiqueta | Título | URL | Duración | Tempo del set | Sirve para |
|---|---|---|---|---|---|
| 4R | The 4 rules of techno minimalism | https://www.youtube.com/watch?v=mh8jV6IGI84 | 18:12 | 138 | Marco de diseño: groove por banda, movimiento, polímetro, tensión/release; estructura de 16 compases y FX de tensión. |
| MT | Music Theory for Techno | https://www.youtube.com/watch?v=JcjT7zgs6cs | 11:56 | 120 (solo la parte Ableton) | Escalas (menor/frigia), pensar en intervalos, riff repetitivo, timbre sucio en la fuente, secuenciador aleatorio. |
| PM | How to keep your boring loop endlessly spicy with Polymeters | https://www.youtube.com/watch?v=0SPaGLLlBsM | 22:34 | 125 (solo parte del bajo) | Largos de loop concretos (3/5/6/12 pasos vs 16), cuántos polímetros, bajo polimétrico. |
| SY | Synthesis for beginners | https://www.youtube.com/watch?v=eu0zpa7OiYA | 15:43 | n/d | Modelo mental osc→filtro→amp, ADSR y 3 formas de envolvente; solo 1 device con números. |
| RM | Techno Rumble Mastery | https://www.youtube.com/watch?v=oUbACkekJZ8 | 18:43 | 135 | Receta de rumble en 3 niveles con cadenas y valores casi completos (el video más denso). |
| TG | The trance gate technique | https://www.youtube.com/watch?v=DxyQNgNKUf8 | 9:07 | 130 | Gate con sidechain desde una pista trigger: patrones de 16 pasos y valores del Gate. |

**Rendimiento (aprox., ítems con valor en los `.params.md` + dichos del `.md`):**

| Video | dicho | en pantalla | opinión | Valor técnico |
|---|--:|--:|--:|---|
| 4R | ~20 | ~65 | ~6 | Medio: estructura/patrones; casi sin dinámica |
| MT | ~14 | ~35 | ~5 | Medio: escalas y riff exactos; patch con plugins ilegibles |
| PM | ~10 | ~40 | ~5 | Alto para el motor (largos de loop exactos) |
| SY | ~15 | ~14 | ~3 | Bajo: conceptual |
| RM | ~22 | ~110 | ~8 | Muy alto: cadenas y parámetros |
| TG | ~10 | ~45 | ~3 | Alto: Gate completo + patrones |

---

## 2. Técnicas accionables por tema

### 2.1 Rumble desde el kick (RM) — lo más valioso

**Concepto (D, 01:15):** el kick se parte en dos cadenas paralelas, una seca y otra "rumble"; se suman en un grupo. Rumble = **smear → mono → low-pass → duck (sidechain)**.

**Ruteo (P alta, fr 0155/0355/0408):** pista de audio `Rumble` con `Audio From` = pista Kick, tap **Post FX**, `Monitor` = **In** (media). La pista Kick sale al grupo (`Basic level` / `Intermediate` / `Mastery`).

#### Nivel básico — pista Rumble: `Reverb → Utility → Auto Filter → Compressor` (fr 0408)

| Device (API) | Parámetro | Valor | Conf. |
|---|---|---|---|
| Reverb | Decay Time / Dry-Wet | 1.40 s / 100 % | alta |
| Reverb | Size / Predelay / Shape / Stereo | 100 / 2.50 ms / 0.50 / 100 | alta |
| Reverb | Quality / Spin | Eco / on | alta |
| Reverb | Hi Cut | on, ~830 Hz | baja (Hz); on = media |
| Reverb | Lo Cut / Freeze / Flat / Cut | off / off / on / on | media-alta |
| Reverb | Diffusion High | on, 4.50 kHz, 0.70 | alta |
| Reverb | Chorus | on, 0.02 Hz, 0.02 | alta |
| Reverb | Density / Scale | 60 % / 40 % | alta |
| Utility (`StereoGain`) | Width → **Mono** | on | alta |
| Utility | Bass Mono / Gain | off (120 Hz) / 0 dB | alta |
| Auto Filter (`AutoFilter2`) | Tipo / slope / circuit | Low-pass / 24 dB / Clean | alta |
| Auto Filter | Frequency | **163 Hz** (alt 183) | media |
| Auto Filter | Resonance | 14 % | alta |
| Auto Filter | Env Amount / LFO Amount | 0 / 0 (LFO rate 0.11 Hz sin efecto) | alta |
| Compressor (`Compressor2`) | Sidechain | on, Audio From = Kick, Post FX | alta |
| Compressor | SC EQ | on, low-pass, **80 Hz**, Q 0.71 | alta |
| Compressor | Ratio / Attack / Release | **4:1 / 0.46 ms / 81.4 ms** (Auto Release off) | alta |
| Compressor | Threshold | **-25.5 dB** | alta |
| Compressor | Detección / Knee / Lookahead / Env | RMS / 6 dB / 0 ms / Log | media |
| Compressor | Output (makeup) | ~11.3 dB | media |

Dicho extra (D): Auto Filter "corta todo por encima de ~200 Hz, verificá con el oído"; el compresor con sidechain es lo más simple, `LFOTool` es la alternativa que evita depender del kick como trigger; "prestá atención a attack y release para que groovee con el kick".

#### Nivel intermedio — agrega `Delay` y `Saturator`+`EQ Eight`; grupo con `Drum Buss`/`EQ Eight`/`Limiter` (fr 0730-0755)

Cadena Rumble: `Delay → Reverb → Utility → Saturator → Auto Filter → EQ Eight → Compressor`.

| Device | Parámetro | Valor | Conf. |
|---|---|---|---|
| Delay | Sync L/R / link | **2** (=2/16) / on | alta |
| Delay | Feedback / Dry-Wet | 81 % / 69 % | alta / media |
| Delay | Filter / Mode | on, 1.00 kHz, Width 8.00 / Repitch, Ping Pong off | alta |
| Reverb | Decay Time / Dry-Wet | 810 ms / 90 % | alta |
| Saturator | Type / Drive / Output | Soft Sine / 12 dB / **-12 dB** (compensa) | alta |
| Saturator | Color | on, Freq 1.00 kHz, Width 30 %, Base 0, Depth 0; Soft Clip off | alta |
| Auto Filter | Frequency / Res | **183 Hz** (alt 163) / **37 %** | media / alta |
| EQ Eight (`Eq8`) | Banda 3 Bell | 230 Hz, **-8.06 dB**, Q 0.71 | alta |
| Compressor | Ratio / Attack / Release / Threshold | **7.54:1 / 0.07 ms / 95.4 ms** / -25.5 dB | alta |
| Compressor | Out | ~13.2 dB | media |
| Drum Buss (grupo) | Drive / Mode / Crunch | 20 % (alt 29) / Soft / 22 % | media / alta |
| Drum Buss | Damp / Boom / Boom Freq / Decay | 2.73 kHz / **4.8 %** / **50 Hz** / 100 % | alta |
| Drum Buss | Transients / Comp / Output | 0 / off / 0 dB | alta |
| EQ Eight (grupo) | Banda 3 Bell | 235 Hz, -5.58 dB, Q 0.71 | alta |
| Limiter (grupo) | Gain / Ceiling / Lookahead / Release | 2.00 dB / -3.31 dB / 3 ms / 300 ms Auto | alta / media |

D: "el delay a 2/16 enfatiza el contratiempo (upbeat) en vez del tiempo"; saturación fuerte = "se siente fuerte, los parlantes no dan abasto" (O/psicoacústico); recortar low-mids "sin high-pass" (D); limiter en el grupo "para sacar 1-2 dB" (D).

#### Nivel mastery (fr 0958-1300)

| Capa | Cadena y valores | Conf. |
|---|---|---|
| **Texture** (input Kick Post FX): `Delay → Delay → Reverb → Utility → Saturator → EQ Eight → LFOTool` | Delay1: 1/16, FB 81 %, wet 50 %, filter 1 kHz; Delay2: 1/16, FB 56 %, wet 50 %; Reverb 1.76 s, wet 66 %; Saturator igual al intermedio; EQ: HP (freq no vista), Bell 278 Hz +1.86 dB, LP (curva cae antes de ~2 kHz); LFOTool SVF LP rampa, rate "1/4" probable, depth 100 | alta (Delays/Reverb), media (EQ/LFOTool), baja (rate) |
| **Texture, concepto (D)** | Misma cadena del rumble pero **band-pass ~800 Hz-1 kHz** en vez de low-pass, mezclada **muy baja**: "aire y textura crujiente"; LFOTool solo "da movimiento, no corta del todo" | D |
| **+Percussion** `Simpler → Reverb → Decapitator → EQ Eight` | Low tom 909; Simpler Decay 254 ms, Sustain -inf, Vol -12 dB; Reverb 932 ms, wet 91 %; EQ bandas 1 HP, 2 low shelf, 4 bell 303 Hz Q 1.28, 8 LP (~<1 kHz); clip: un golpe cada media nota (~8 en 4 compases) | media-alta; patrón baja |
| **+Atmo** `Simpler → Reverb (Freeze) → EQ Eight → LFOTool` | Clap 808; Reverb **Freeze on**, 6.24 s, wet 100 %; EQ HP **383 Hz** Q 0.53; LFOTool sin abrir | alta |
| **Bus Mastery**: `Audio Effect Rack PLEL → EQ Eight → Limiter → EQ Eight` | Rack: `dry` (vacía), `satu` = Radiator → Decapitator → EQ (HP ~100, bell 4.54 kHz, LP ~8 kHz), `width` = Delay 1/16 offset -1/+1 %, FB 50 %, filter 776 Hz; vol de chains ~0 / -9.7 / -6.6 dB (**baja**). EQ bus 400 Hz -0.62 dB Q 0.71 (bandas 2-4 activas). Limiter Gain 1.00 dB, Ceiling **-2.81 dB**, lookahead 3 ms, release 300 ms Auto | EQ/Limiter alta; chains baja |

**Reglas de uso (D/O):**
- Tras armarlo, **resamplear** las capas para elegir dónde empiezan/terminan: el primer kick suena seco y los delays tardan en arrancar; loopear solo la parte que groovea y cortar las colas.
- **Balance tonal** (O): lo grave "suena bien mientras producís" y tienta a sumar sub; un tema profesional no está enfatizado en el sub. Consejo del autor: subwoofer + Sonarworks.
- **El kick es el protagonista** (O): lo extra no debe sacarle groove.
- **Tempo** (D/O): BPM más lento = más espacio para sincopa del rumble; BPM más alto = grooves más rectos, menos espacio.
- Copiar el rack a otro kick: a veces "se cae" porque está esculpido alrededor de ese kick (D).

### 2.2 Gate trance con sidechain (TG)

**Concepto (D):** sonido largo y sostenido ("pared de sonido": acorde sostenido, o sonido corto + mucha reverb + compresión) + **pista trigger** que nunca se oye y fija el ritmo. El **Gate** de Live escucha la trigger por sidechain.

| Elemento | Valor | Conf. / frame |
|---|---|---|
| Fuente | Pigments, power chords nota + 5ª justa (+7 st) + octava; compás 1: C3-G3-C4; 2: E3-B3-E4; 3 (2 compases): A2-E3-A3; vel 100 | alta (c.1), media (c.2-3), fr 0315 |
| Pista Trigger | clips de audio muy cortos (`Kick idea 1.wav`), uno por hit, grilla 1/16, loop 4 compases | alta, fr 0440 |
| Gate (nombre API sin verificar) Sidechain | on, Audio From = Trigger track, Post FX | alta, fr 0615 |
| Gate | **Threshold -17.9 dB** (con SC; se baja hasta que responda) | alta |
| Gate | Return 3.00 dB · Attack 3.50 ms · Hold 10.0 ms · **Release 15.0 ms** · Floor -40.0 dB · Lookahead 1.5 ms · Flip off · Gain 0 · Mix 100 % | alta |
| Gate | Release 9 ms = más "snappy"; 134 ms = casi no cierra (demos) | alta, fr 0715/0720 |
| Voz: `Reverb(Cathedral) → Gate → Reverb(Cathedral)` | Reverb1: Decay 5.00 s, Predelay 60 ms, Size 180, Dry-Wet 48 %, Hi Cut 3.31 kHz Q 4.22, Density 20 %, Reflect -6 dB; Gate Threshold -12 / -15.9 / -13.0 dB según el momento; Reverb2: Decay **1.22 s**, Dry-Wet **32 %** | alta |

**Patrones de trigger (16 pasos por compás, `x` = hit; lectura geométrica de posiciones de clip, alta/media):**

| Patrón | Cadena de pasos | Origen |
|---|---|---|
| Grupos de 3 | `x..x..x..x..x...` (hits en pasos 0,3,6,9,12) | P alta (fr 0440/0545); D "cada tres 16avos casi siempre suena bien" |
| Transición | `x..x..x..x..x.xx` (compases pares, hits extra en 14 y 15) | P media (fr 0630) |
| Continuo | `xxxxxxxxxxxxxxxx` | P alta (fr 0700) |
| Tríadas con hueco | `xxx.xxx.xxx.xxx.` | P alta (fr 0820/0835) |

Observación (inferencia mía, no del video): `x..x..x..x..x...` se reinicia cada compás (no es un polímetro real: 5 golpes de 3 pasos + 1 paso sobrante). Un trigger con loop de **3 pasos** sí giraría contra el compás de 16.

### 2.3 Los 4 principios del minimalismo (4R)

**Principio 1: groove en graves, medios y agudos (D).** "Groove = al menos dos elementos que rebotan entre sí", no golpes idénticos. Set de ejemplo (909 Core Kit; contraejemplo `Not a groove` = kick a negras, clap en 2 y 4, hat en las "y"):

| Pista del `Yes groove` | Patrón (pasos 1-16) | Nivel de pista | Conf. |
|---|---|---|---|
| Kick (otro sample) | 1, 5, 9, 13 (negras) | 0 dB | alta / media |
| Low Groove | ~8 notas/compás, medio compás repetido 2 veces (corta, corta, larga) | -5.7 dB (alt -5.2) | baja (posición por píxeles) / media |
| Hihat | 3, 7, 11, 15 | -6.3 dB (alt -8.3) | media / baja |
| High Groove | 3, 7, 11, 15, alternando larga/staccato | -14.4 dB | media |
| Clap | 5 y 13 | -12.5 dB | media |
| Mid Groove | 4 y 12 (una 16ava antes de los tiempos 2 y 4) | -12.6 dB | media / baja |

**Principio 2: movimiento (D).** "Sin movimiento aburre, demasiado agota". Tres vías: FX con modulación (phaser/chorus/flanger/delay), tocar filtros y envolventes, LFO/automatización. Demo del hat (P):

| Elemento | Valor | Conf. |
|---|---|---|
| Pista | Simpler (`909HHo1_SP1200R`, Classic, Voices 6, Warp 1 Beat Complex) → Modnetic (flanger, plugin de terceros); 4 semicorcheas (D; clip no legible) | alta / baja |
| Filtro Simpler | 24 dB Clean, Res 0 %, LFO 1 Hz seno | alta |
| Parámetros automatizados | Filter Freq (130 Hz en 05:30, 467 Hz en 06:10), Ve Attack (21.4 → 0.26 ms), Ve Sustain (-42 / -16 / -36 dB) | alta; nombres de lane media-baja |
| Forma de las lanes | Sustain: diente de sierra (sube ~medio compás, cae, vuelve a subir); Attack: rampa descendente; Freq: casi plana. Duración 1 compás | media |
| Ve Decay / Release | 600 ms / 528 ms fijos | alta |

**Truco "demasiado movimiento" → freeze/flatten/loop (P+D):** clap con `Echo` (L/R 375 ms Dotted, Feedback 81 %, LFO a delay time 0.16 Hz seno, Mod x4 Delay 63 %, Decay 50 %, Reverb Post, Dry-Wet 70 %; alta). Se hace *Freeze Track → Flatten* y se **elige un fragmento del audio resultante y se loopea** (loop de 1 tiempo, `0.1.0`, en el clip, warp Beats): un sample con movimiento "horneado" que no se habría programado a mano (D).

**Principio 3: polímetro (ver 2.4).** **Principio 4: tensión y release (D+P):**

| Elemento | Valor | Conf. |
|---|---|---|
| Estructura de la demo | 8 compases de acumulación (33→41) + 4 `build tension` (41→45) + 4 `make 'em wait` (45→49) = 16 | alta (locators) |
| Receta (D) | Construir una "pared de sonido" con todas las frecuencias, **cortarla** para dejar aire, hacer esperar al público, entonces recién el golpe limpio | D |
| FX de tensión | Sonido cualquiera → **reverb enorme** (device nunca mostrado) → freeze + flatten → **Reverse** del clip; "SFX+Reverb+Flatten" 33.3→41.1 (7.2 compases), cola reversa ~44.3→~48.8 | alta (clip) / baja (cola) |
| Niveles | SFX+Reverb+Flatten -9.5 dB; +Reverse -0.6 dB; clap +5.2 dB (signo no visible) | media |
| Capa "no minimal": grupo "I guess it's not minimal anymore" | `pure dirt texture` = resample del grupo `Yes groove` (Post Mixer), 8 clips de 1 compás, -6.1 dB; `Some Gross Foley Rumble` -17.0 dB; `Breakbeat` -14.0 dB de turnaround | media |
| Polímetro como cama del break | quitar kick, hat y clap y dejar solo el polímetro; el público "busca el uno"; la vuelta de todo junto "es el release" | D |

**Cuántas pistas de sonido:** el break se fabrica sacando percusión, no agregando (D).

### 2.4 Polímetros (PM + 4R)

**Definición (D):** loop cuya longitud **no es múltiplo del compás**. Un loop de 16 pasos (1 compás, 4/4) más un loop de N pasos se realinean cada `mcm(16, N)` pasos.

| Largo (pasos de 1/16) | Notación en Live | Realineación con 16 pasos | Valoración del autor | Origen |
|---|---|---|---|---|
| 3 | `0.0.3` | cada 48 pasos (3 compases) | "no está mal" (D) | P alta |
| 5 | `0.1.1` | cada 80 pasos (5 compases) | "menos atractivo", pero mezclado bajo "puede condimentar" (D) | P alta |
| **6** | `0.1.2` | cada 48 (3 compases) | **"su favorito"**, "entretenido" (D); es el que usa en el bajo final | P alta |
| 12 | `0.3.0` (3 tiempos) | cada 48 | primera versión del bajo, descartada (P) | P alta |
| ≈ 7 | `0.1.3` (medido) | cada 112 | polímetro de acordes en 4R (Sylenth1) | P media (medición indirecta) |
| 5 (ticks) | ML-185 Length 5 (de 8) | — | "no múltiplo de 4 da resultados interesantes" (D) | P alta |

**Reglas de uso (D):**
- **Uno o dos** polímetros; "tres o cuatro" y el cerebro "no puede seguir". Ideal: un loop de 1 compás + **un** polímetro.
- Sirve en percusión (rim 808, nota única en el paso 1), en sintes agudos y en **bajo** (Hip-Hop Sub Bass, nota única C1 de 2 pasos, loop 6 pasos).
- Un polímetro bajo en la mezcla ("mezclado bajo") ya "condimenta".
- Se puede **modular su timbre** (filtro automatizado, rampa en los últimos ~24 % del clip: plana hasta ~compás 28 y sube hasta 30; P media) y **pasar por delay** con modulación para volverlo groove.
- En el **break**: puede quedar solo y dura "una eternidad" (D).
- Ejemplos citados (D): Wolfgang Voigt "Studio One" y "Green" (polímetro en sintes y en sub), Cast "Hell on Earth" (303 polimétrico; progresión I→III en mi mayor; el riff baja un semitono con el cambio de acorde).
- El PM usa solo largo de loop de clip; **no** usa LFO ni automatización para generar el polímetro (P).

Tabla de patrón polimétrico para un motor: `loop_pasos ∈ {3, 5, 6}` contra compás de 16; nota única en paso 1; largo de nota 1-2 pasos; instrumento percusivo agudo o sub; máximo 2 capas.

### 2.5 Síntesis (SY) — modelo para sonidos propios

Modelo (D, diagramas P alta): `OSC → FILTER → AMP → FX → oído`, envolvente 1 → filtro, envolvente 2 → amp, LFO → filtro / amp / FX.

| Concepto | Regla | Origen |
|---|---|---|
| ADSR | A, D, R = tiempos (ms); **S = porcentaje** (nivel mientras la tecla está apretada) | D (diagrama P alta) |
| Envolvente "piano" | A corto, D corto, **S ≈ 75 %**, R corto | D |
| Envolvente "drone/atmósfera" | A muy largo, R muy largo, S = 100 % (D deja de importar) | D |
| Envolvente "pluck" | A muy corto, **S = 0 %**; el **largo del sonido lo fija D** | D |
| Filtro | Pasa-bajos: "elige una frecuencia sobre la cual empieza a atenuar"; entre osc y amp | D |
| Auto Filter demo | LP 24 dB Clean; Freq 19.9 kHz → 1.04 kHz → **183 Hz**; Res 14 %; Env Amount 0; LFO Amount 0, Rate 0.11 Hz seno | P alta (fr 0845/0915/0930) |
| Spectrum (visor) | Block 8192, L+R, refresh 60 ms, Line+Max, X log | P alta |
| Movimiento de filtro | 2.º envelope pluck al cutoff = "oscuro→brillante→oscuro"; envelope drone al filtro = abre gradual y cierra gradual al soltar | D |
| LFO | Oscilador lento (~1 vez por segundo, D) mapeado al cutoff: "inestabilidad orgánica" | D |
| Onda | Sierra = brillante y áspera; icono: sierra/triángulo/cuadrada/seno | D+P |
| FX | Delay y reverb posteriores "vuelven épico" cualquier sonido | D |

Nota: el 183 Hz leído aquí con claridad **sugiere** que el Auto Filter del rumble intermedio es 183 Hz (el propio `.params.md` lo marca como probable, no confirmado); en las `bases/` se dejó 163 (básico) y 183 (intermedio).

### 2.6 Teoría y diseño de riffs (MT)

**Reglas del autor (D):** (1) usar teoría normal: raíz, escala, progresión; (2) abrazar la disonancia y la repetición (ostinato); (3) el carácter del sonido (distorsión y desafinación) importa más que las notas.

| Tema | Regla / valor | Origen |
|---|---|---|
| Escala | Evitar la mayor ("resultados felices"); usar **menor** o **frigia** | D |
| Frigia | Como la menor con el **2.º grado bemol**: "da un sentimiento malvado al acercarse a la raíz" | D |
| Pasos en semitonos (7 saltos; el 7.º, de vuelta a la octava, no está en pantalla) | Mayor 2-2-1-2-2-2 · Menor 2-1-2-2-1-2 · Frigia 1-2-2-2-1-2 | P alta (fr 0155) |
| Riff 8 corcheas en C (un compás, una nota por corchea, pasos 1,3,5,...,15) | Menor: C3 D3 Eb3 F3 G3 Ab3 F3 D3 · Frigio: C3 Db3 Eb3 F3 G3 Ab3 F3 Db3 | P alta (notas), media (posiciones inferidas) |
| Progresión | En techno a menudo **solo 2 acordes**, a veces 3; alternativa: quedarse en la raíz y mover el sinte lejos y de vuelta | D |
| Pensar en **intervalos**, no acordes | octava, 5.ª justa, 3.ª menor, 2.ª bemol de la frigia | D |
| Ostinato | Un patrón repetido "termina sonando correcto" aunque sea disonante; riffs **cortos** y **modular el timbre** (filtro/distorsión) en vez de melodías largas | D |
| Arquitectura del techno | Graves (kick+rumble) y hats son **atonales**; lo único con tono es el riff del medio, así que "no tiene que ser armónico respecto de nada" | D (O de diseño) |
| 3 estrategias de riff | (a) loop de 303 con pasos repetidos; (b) **cromático/aleatorio** con un secuenciador por paso (Max for Live); (c) pitches continuos fuera de la escala (modular) | D |
| ML-185 (M4L) Clock 1/16, Swing 0 %, Length 8 → **5**, Coarse 0 st | Pitches aleatorios, 1.ª tirada: +11 +9 +9 +14 -19 +5 +13 +9 st; 2.ª: -20 -4 -14 +23 -23 -8 -18 -17 st | P alta (fr 0950/1005/1020) |
| Timbre | Detune de osciladores / voces apiladas "hasta el punto dulce"; **pitch bend al inicio** de la nota para dar borde; **distorsión en la fuente** en cantidades grandes y domarla después con EQ; reverb antes del Decapitator (modo Punish) | D |
| Patch "Kralle Scream" (Sylenth1 → ValhallaRoom → Decapitator) | Macros (0-127): Detune 75, PitchBend 64, Verb Mix 28, Verb Decay 4, Decap Tone 102, Vibrato 0, Soothe 50. Sylenth1: Osc A1 sierra, Voices 8 (alt 6), Octave +1; Decapitator Punish on, Style P | P alta (macros) / media-baja (Sylenth) |
| 303 | Phoscyon (d16), presets que cambian el timbre | P media |

Observación: los plugins del patch (Sylenth1, ValhallaRoom, Decapitator, soothe2) son de terceros y sus parámetros internos son **ilegibles**: solo las macros son confiables.

---

## 3. Fundamentos condensados para un motor compositor

**Altura (escala y notas).**

| Regla | Valor | Conf. |
|---|---|---|
| Escala por defecto del riff | `frigia` (alterna `menor`); nunca mayor | D |
| Pasos de la frigia desde la raíz (semitonos acumulados) | `[0, 1, 3, 5, 7, 8, 10]` (el último salto de 2 vuelve a 12) | P alta (pasos) + cuenta mía |
| Menor | `[0, 2, 3, 5, 7, 8, 10]` | P alta + cuenta mía |
| Grados característicos | b2 (solo frigia), b3, 4, 5, b6; el b2 se ancla en la raíz | D |
| Intervalos a priorizar | octava (12), 5.ª justa (7), 3.ª menor (3), 2.ª bemol (1) | D |
| Progresión | máx. 2 acordes (a veces 3) o ninguna (raíz fija + intervalos); si hay cambio de acorde el riff baja 1 semitono (caso Cast) | D |
| Riff modelo (8 corcheas, 1 compás) en grados de la frigia | `[1, b2, b3, 4, 5, b6, 4, b2]` | P media (posiciones) |
| Raíz | cualquiera; para el motor, ligar a `global.nota_bajo` (E0..E1) para el bajo | derivado, no del video |
| Aleatoriedad | secuencia aleatoria **fija con semilla**, ≤ 8 pasos, largo no múltiplo de 4 (ej. 5); rango observado ±23 st | P alta |
| Acordes del pad/gate | power chord = raíz + 7 st + 12 st | P alta |

Ejemplo derivado (no está en el video): con raíz **F** (el kick del perfil está en F) la frigia da F Gb Ab Bb C Db Eb. Es una cuenta, no una lectura.

**Ritmo (pasos de 1/16, 16 por compás).**

| Regla | Valor |
|---|---|
| Base del groove | kick `[1,5,9,13]`; clap `[5,13]`; hat en `[3,7,11,15]` |
| Segundo elemento por banda (mínimo) | grave: nota que "rebota" contra el kick; medio: un golpe 1 paso antes del 2 y el 4 (`[4,12]`); agudo: hat con largas/cortas alternadas |
| Loops polimétricos | largos `3`, `5` o `6`; **6 preferido**; máx. 2 voces; realineación cada `mcm(16,N)` pasos |
| Trigger de gate | `x..x..x..x..x...`, `xxxxxxxxxxxxxxxx`, `xxx.xxx.xxx.xxx.` |
| Movimiento | un parámetro de timbre automatizado en una curva **de 1 compás** (diente de sierra o rampa) |
| Tensión | acumular 8 compases, "build" 4, "espera" 4 (suma 16) |
| Break | quitar kick/hat/clap y dejar el polímetro; volver todo junto |

**Timbre / síntesis.**

| Regla | Valor |
|---|---|
| Envolvente por defecto (amp) | `piano` (S≈75 %), `drone` (S=100 %, A/R largos), `pluck` (S=0, largo = D) |
| Filtro | LP 24 dB; cutoff modulado por envolvente o LFO (~1 Hz) |
| Disonancia | detune entre voces + pitch bend inicial + distorsión en la fuente |
| FX de tensión | sonido → reverb enorme → freeze/flatten → reverse |

---

## 4. Cruce contra `techno_peak_time.yaml` (v0.3.0)

Estados: **CONFIRMA** (coincide) · **NUEVO** (el perfil no lo tiene) · **CONTRADICE** (valor o criterio distinto). "Tensión D-15/D-16" se marca aparte.

### 4.1 CONFIRMA

| Ruta del perfil | Perfil | Evidencia Underdog |
|---|---|---|
| `global.tempo` (126-135, típico 130) | 130 | RM 135, TG 130 BPM en pantalla (alta); 4R 138 y MT/PM fuera de rango pero son sets de demo |
| `global.compas` 4/4, `grilla_frases` | 4/4, 8/16/32 | Todos 4/4; 4R: 16 compases de acumulación/espera (D+P) |
| `elementos.rumble.sidechain_a: kick` | kick | RM: sidechain con audio del kick, SC EQ LP 80 Hz (P alta) |
| `mezcla.sidechain.por_destino.rumble.params.Ratio: 4` | 4 | RM básico 4:1 (P alta) |
| `mezcla.sidechain.por_destino.rumble.params.Attack: 1` | 1 ms | RM 0.46 / 0.07 ms: mismo orden (sub-ms), (P alta) |
| `mezcla.plantilla.rumble.utility` (mono bajo) | Bass Mono 120 | RM: rumble en mono (P alta); ver 4.3 por el modo |
| `mezcla.plantilla.rumble.eq` LP | LP 250 Hz | RM: LP de Auto Filter 163-183 Hz y "~200 Hz" (D); mismo criterio, distinta frecuencia (ver 4.2) |
| `mezcla.plantilla.kick.eq` banda 3 (recorte de "barro" low-mids) | Bell -3 dB 390 Hz | RM: recortar low-mids tras saturar (D); 230-235 Hz -5.6/-8 dB (rumble y grupo), 278 Hz +1.86 (texture), 400 Hz -0.62 (bus) |
| `mezcla.plantilla.kick.dinamica` Drum Buss, `Boom Freq: 55` | 55 Hz | RM Boom Freq 50 Hz (P alta): mismo criterio (fundamental del kick ~50 Hz) |
| `reglas.escalera_filtro` / `apertura_lead` / `entrada_filtrada` (filtro con movimiento) | filtros automatizados | 4R/SY: movimiento de timbre vía filtro y envolvente (D); principio 2 |
| `reglas.puente` (tensión continua, todo termina en silencio) | puente con riser, entradas de a poco | 4R principio 4: tensión, "hacer esperar", silencio antes del impacto (D) |
| `transiciones.al_entrar.*.reverse` | reverse antes de secciones | 4R: reverse de reverb tail como FX de tensión (P alta) |
| `elementos.rumble.warp: complex` (criterio Gabriel) | complex | RM: rumble resampleado/loopeado con warp Beats/Complex (4R clip congelado: Beats, P alta); sin conflicto |
| Niveles relativos de `elementos` | kick > bajo ≈ drums ≈ clap > top | 4R: Kick 0, Hat -6.3, Clap -12.5, Mid -12.6, High -14.4 dB (media) — mismo orden |

### 4.2 CONTRADICE (o tensiona de forma medible)

| # | Ruta del perfil | Perfil | Underdog | Evidencia | Nota |
|---|---|---|---|---|---|
| C-1 | `mezcla.sidechain.por_destino.rumble.params.Release` | **200 ms** (corregido por F4 sec.3: 150-300) | **81.4 ms** (básico), **95.4 ms** (intermedio), Auto Release off | RM fr 0408_b / 0747_b (alta), a 135 BPM | Es 2-2.5 veces menor. El bajo del perfil (90 ms) sí coincide con RM. Candidato A/B nº 1 |
| C-2 | `mezcla.sidechain.por_destino.rumble.params.Threshold` | -32 dB | -25.5 dB (SC EQ LP 80 Hz) | RM (alta) | No es contradicción real: el perfil dice "calibrar por reducción". La reducción de RM no se vio. Solo informativo |
| C-3 | `mezcla.plantilla.rumble.eq` banda 2 | **Low Pass 48 dB 250 Hz** | **LP 24 dB, 163-183 Hz** (Auto Filter), "~200 Hz" (D) | RM (media: 163/183 dudoso) | 250 vs ~180: diferencia audible posible |
| C-4 | `mezcla.plantilla.kick.dinamica.params.Boom Amt` (Drum Buss) | **45** | **4.8 %** (en el grupo kick+rumble) | RM fr 0755_g (alta) | ~9x. Pero el de Oscar es sobre **el bus kick+rumble**, no solo el kick; el perfil lo aplica al kick. Revisar unidades antes de comparar (ambos son %) |
| C-5 | `elementos.rumble.tipo: loop` (audio del pack) | rumble = audio de librería | rumble **generado del kick** (resample en pista paralela, Post FX) | RM (alta) | Diferente enfoque de fuente, no de valor. D-07 ya permite usar/chopear loops; esto agrega un camino generativo. Es CONTRADICE solo si se quiere uniformar la fuente |
| C-6 | `mezcla.plantilla.rumble.eq` banda 1 | HP 12 dB **35 Hz** | RM no muestra HP en la cadena básica (solo LP); el HP aparece en texture/atmo (383 Hz en atmo) | RM (alta) | Oscar: "no hagas high-pass, solo despejá low-mids" (D) en el contexto del EQ de low-mids. Tensión de criterio, no de valor |

### 4.3 Tensión con D-15 / D-16 (no son "perfil vs Underdog" sino "método Underdog vs decisión")

| # | Qué hace Underdog | Decisión | Veredicto |
|---|---|---|---|
| T-1 | **Limiter en grupo** (intermedio: Gain 2 dB, Ceiling -3.31 dB; mastery: Gain 1 dB, Ceiling -2.81 dB), "para sacar 1-2 dB" | **D-16:** mezcla premaster, "sin limiter de volumen en el bus master" | Es un limiter de **sub-grupo**, no del master, pero cumple la misma función de subir volumen. **No importar** sin aprobación de Gabriel; si se quiere, medir antes cuánta reducción hace |
| T-2 | **Makeup alto en Compressor** (Output +11.3 / +13.2 dB) y Saturator con Output -12 dB | **D-15** (nivel automatizado solo en Utility) | **No viola D-15**: son valores **estáticos** dentro del device, no automatización. Solo cuidar que el nivel final de pista no saturé el headroom `-6 dBFS` (D-16) |
| T-3 | Automatiza **Simpler Ve Sustain / Ve Attack / Filter Freq** (4R) | D-15 | **No viola D-15**: no es el fader ni el gain de pista. Pero `Ve Sustain` es la envolvente de volumen del sinte; si se implementa, hacerlo vía device y **no** automatizar el `Volume` del Simpler |
| T-4 | Niveles de pista del `Yes groove` van del mixer (-5.7 ... -14.4 dB) y los FX de tensión llegan a **+5.2 dB** (signo no visible) | D-16 (picos ~-6 dBFS) | Solo informativo: esos valores salen de un fader fijo, no de automatización |
| T-5 | **Saturation fuerte + limiter "para que se sienta más fuerte"** | D-16 | Criterio estético (loudness percibido) del autor; el premaster de Gabriel no persigue volumen. Marcar como opinión no adoptable por defecto |

### 4.4 NUEVO (propuestas de ruta en el perfil; todas requieren aprobación de Gabriel, D-13)

| # | Ruta propuesta | Qué agrega | Evidencia | Confianza sugerida |
|---|---|---|---|---|
| N-1 | `global.escala` (nueva) | `frigia` por defecto, `menor` alternativa; nunca mayor; pasos `[0,1,3,5,7,8,10]` | MT P alta (fr 0155) | media (un solo origen) |
| N-2 | `global.riff` (nueva) | riff de 8 corcheas en 1 compás; ostinato corto con timbre modulado; ≤ 2 acordes | MT D + P alta | media |
| N-3 | `reglas.polimetro` (nueva) | `loop_pasos ∈ {3,5,6}` (6 preferido), máx. 2 voces, nota única en paso 1, mezcla baja | PM P alta + D | media |
| N-4 | `reglas.polimetro_en_break` | en `puente`, dejar polímetro solo con kick/hat/clap quitados | 4R D | baja (un solo origen, y solo hablado) |
| N-5 | `reglas.rumble_desde_kick` / `elementos.rumble.fuente: generada` | cadena `Reverb→Utility(Mono)→Auto Filter LP→Compressor SC` desde el kick Post FX | RM P alta | media |
| N-6 | `elementos.rumble.capas` | texture (BP ~800-1000 Hz, muy bajo), percusión baja (low tom + reverb), atmo (reverb Freeze, HP 383 Hz) | RM P alta (valores) / D (concepto) | baja (un solo origen) |
| N-7 | `reglas.delay_smear_rumble` | Delay Sync 2 (2/16) FB 81 % antes de la reverb enfatiza el contratiempo | RM P alta + D | baja |
| N-8 | `reglas.groove_por_banda` | cada banda (grave/medio/agudo) lleva ≥ 2 elementos que "rebotan" | 4R D+P | media |
| N-9 | `reglas.movimiento_hat` | automatizar Filter Freq / envelope en curva de 1 compás (diente de sierra) | 4R P media | baja |
| N-10 | `reglas.freeze_flatten_loop` | convertir un movimiento excesivo en sample y loopear un fragmento | 4R P alta (clip) | baja |
| N-11 | `reglas.trance_gate` | Gate con sidechain desde pista trigger; patrones de 16 pasos; valores del Gate | TG P alta | media |
| N-12 | `reglas.fx_tension_reverse` | reverb enorme → freeze/flatten → reverse | 4R P alta (clip) | media |
| N-13 | `mezcla.sidechain.sc_eq` | SC EQ low-pass 80 Hz Q 0.71 en el Compressor para escuchar solo el grave del kick | RM P alta | media |
| N-14 | `elementos.*.envolvente` (síntesis propia) | envolventes `piano / drone / pluck` con S en % | SY D | baja (solo hablado) |

---

## 5. Candidatos a A/B a oído

> **D-18 (Gabriel, 2026-11-25):** no se resuelven en abstracto. Son alternativas que conviven; cada una se prueba al construir un tema concreto y lo elegido vale para ese tema. Rumble loop vs desde el kick ya figura en el perfil como `elementos.rumble.alternativas_origen`.

Propuestas ordenadas por valor/costo; **Gabriel decide por oído** (D-01). Una sola variable por prueba; todo lo demás igual (mismo kick, mismo nivel, misma reducción de ganancia).

| # | Variable | A | B | Qué escuchar |
|---|---|---|---|---|
| 1 | `Release` del sidechain del rumble | **200 ms** (perfil) | **~90 ms** (RM: 81-95 ms) | Con la misma reducción de ganancia (calibrar Threshold): si el rumble "respira" a tempo entre kicks o queda tapado/colgado; si en 90 ms aparece zumbido o se hace seco |
| 2 | Delay antes de la reverb del rumble | sin Delay | `Delay` Sync **2** (2/16), FB 81 %, filter 1 kHz, wet ~69 % | Si el hueco entre kicks se llena en el contratiempo (offbeat) con groove, o si ensucia el kick y el low-mid; a 130 BPM |
| 3 | 2.º grado del riff/stab | **menor** (`C D Eb F G Ab F D`, transpuesto) | **frigia** (`C Db Eb F G Ab F Db`) | Tensión al caer en la raíz: si b2 da el "malvado" buscado sin sonar dramático; en el rango del lead/stab sobre la raíz del kick |
| 4 | Una voz polimétrica | sin polímetro | un loop de **6 pasos** (`0.1.2`), nota única en el paso 1, nivel bajo | Si se "renueva" cada compás y sigue interesante 32 compases, o distrae/choca con el kick; probar en groove (y luego en el puente) |
| 5 | Origen del rumble | loop de pack (`warp: complex`) | rumble **generado desde el kick** (cadena RM básica) | Mismo nivel y sidechain: cuál "es parte" del kick, si el generado queda más compacto o menos natural |
| 6 | Patrón del trigger de Gate sobre un pad/coro/voz sostenido | `x..x..x..x..x...` | `xxx.xxx.xxx.xxx.` | Gate de RM (Threshold -17.9, Release 15 ms): cuál da más groove sin competir con hats; si el corte "pega" con la voz |

Fuera de la lista (ya descartados o fuera de alcance de A/B): Drum Buss `Boom Amt` 4.8 vs 45 (C-4; antes hay que comprobar unidades y que es sobre otro bus), limiter de grupo (T-1; choca con D-16 antes de probar).

---

## 6. Huecos: lo que el material no resuelve

| Hueco | Detalle |
|---|---|
| Valores de dinámica en 4R/MT/PM/SY/TG | No se ve ningún parámetro de Compressor, Glue ni sidechain en 4R; los únicos son los de RM y el Gate de TG |
| Auto Filter del rumble: 163 vs 183 Hz | El `.params.md` lo deja como probable 183 en intermedio; no se confirmó por otra vía (la confianza de la base es media) |
| Reverb Hi Cut del rumble | "~830 Hz" tapado por el resaltado; no usar |
| Parámetros de Decapitator, Radiator, Sylenth1, ValhallaRoom, soothe2, Modnetic, `LFOTool` | UI cerrada o ilegible; solo hay macros (Kralle) y "Default" |
| Reducción de ganancia del sidechain | RM no muestra el medidor; imposible comparar Threshold con el del perfil |
| Estado on/off de Drum Buss, EQ y Limiter del grupo | El autor hacía A/B en pantalla; no asumir que el estado final es "on" |
| Largo exacto del polímetro de 4R | `≈ 7 pasos` (`0.1.3`) es una **medición**, ningún frame lo muestra; usar solo 3/5/6 que sí se leen |
| Largo de nota (rim, synth, bajo) | Sin campo numérico; solo 1-2 pasos estimados |
| Pitches del Basic Beat y kit de PM | Pitch de pads no leído; solo `C#1` en una nota |
| Posiciones de los riffs 4R (low/mid groove) | Medidas por píxeles; sin piano roll abierto |
| Raíz y tonalidad de los ejemplos | MT usa C; el perfil no define tonalidad. No hay regla de Oscar para elegir la raíz del tema |
| Progresiones | Solo "I→III" en mi mayor (Cast), de oído; en MT no se ve ninguna en pantalla |
| Umbral para "cuántos polímetros" | "1 casi siempre, 2 probablemente bien, más es caótico" (D); sin medición |
| Loudness/espectro de los temas de Oscar | Ninguno medido; no se puede cruzar con `master.club` ni con el norte sonoro (D-17) |
| Compatibilidad del bridge | `live_compressor_set_sidechain` cubre Compressor; **no** hay herramienta verificada para sidechain del `Gate`, ni para `freeze/flatten/reverse` de clips, ni para `LFOTool`/`ML-185` (M4L) |
| Reverb "enorme" de los FX de tensión | El autor lo dice pero el device nunca se muestra |
| Tempo | 138/120/125/135/130: no hay regla de tempo propia de Oscar; solo RM habla de BPM vs sincopa |
| Roles de plugins | Underdog usa Sylenth1/Decapitator/Radiator/Modnetic/soothe2; el perfil solo lista Pro-Q 3, Maag EQ4, Butch Vig Vocals, H-Comp. Sin equivalencia verificada con nativos |

---

*Cierre:* este documento **no cambia el perfil**. Si Gabriel aprueba ítems del 4.4, entran con la confianza que corresponda (D-13), y los 6 A/B de la sección 5 los resuelve su oído, no el análisis.
