# F5 — Catálogo de Ableton (capa conceptual)

> Investigación web del 2026-11-18. Fuente principal: manual oficial de Live 12 y
> release notes de Live 12.x (hasta **12.4.16**, 30-10-2026). Fuentes secundarias:
> tutoriales de Attack Magazine, MusicRadar y similares, solo para el uso en techno.
> **Es conceptual.** La lista exacta de parámetros (nombre, mínimo, máximo, default)
> queda **pendiente de volcarla desde el Live instalado vía el puente** (P-03).
> Los números `[n]` remiten a la lista de fuentes del final.

## 1. Fundamentos de Live para producir por API

### Session vs Arrangement
- **Session:** grilla de clip slots por pista y escenas; sirve para armar loops y
  variaciones. **Arrangement:** línea de tiempo; es donde vive el tema terminado.
  Para el nexo: prototipar en Session y volcar a Arrangement la estructura final.

### Clips y warp
- Los clips de audio con **Warp** activo siguen el tempo del Set. Por API:
  `Clip.warping`, `Clip.warp_mode`, `gain`, `pitch_coarse` (±48 st), `pitch_fine`
  y los warp markers (`add_warp_marker`, `move_warp_marker`) [2].
- **Los 7 modos de warp** (valores de `warp_mode` en la API: 0 Beats, 1 Tones,
  2 Texture, 3 Re-Pitch, 4 Complex, 5 REX, 6 Complex Pro) [1][2]:

| Modo | Para qué | Uso en el nexo |
|------|----------|----------------|
| Beats | Material con ritmo dominante: loops de batería y "la mayoría de la música electrónica de baile" [1]. Parámetros: Preserve (Transients o grilla), Transient Loop Mode, Transient Envelope | **Drums, tops, percusión, kick+rumble en loop** |
| Tones | Material con altura clara: voces, instrumentos monofónicos, bajos. Parámetro: Grain Size | **Loops de bajo** con poco cambio de tempo |
| Texture | Sin altura clara: pads, ruido, drones. Grain Size y Fluctuation | Atmósferas, FX |
| Re-Pitch | Tempo y altura juntos, como un tocadiscos | Bajo/kick si se acepta el cambio de tono; risers |
| Complex | Material mixto, temas completos. Formants, Envelope | **Mezclas completas / referencia** |
| Complex Pro | Variante de Complex, "puede dar mayor calidad" | Igual que Complex; más CPU |
| REX | Solo para archivos REX | No aplica |

Complex y Complex Pro gastan bastante más CPU; el manual sugiere congelar o
resamplear [1].

### Simpler
Tres modos [3]:
- **Classic:** instrumento melódico con sample afinado (stabs, bajos sampleados).
- **One-Shot:** monofónico, pensado para golpes de batería y frases cortas.
- **Slicing:** corta el sample de forma no destructiva y cada slice se toca por
  nota MIDI. Útil para rehacer loops de drums o rumble sobre la grilla (D-07).
Tiene filtro, tres envolventes ADSR (amp, filtro, pitch), LFO y Warp propio [3].
Desde 12.4 la API tiene `SimplerDevice.replace_sample` [4].

### Drum Rack
- 128 pads, uno por nota MIDI; cada pad dispara una o más cadenas [5].
- **Choke:** 16 grupos; disparar una cadena silencia a las demás del grupo
  (hat cerrado corta al abierto) [5].
- **Returns internos:** hasta 6 cadenas de retorno con sends por pad (post-fader);
  su salida puede ir a la salida del rack o a los return tracks del Set [5].
- API desde 12.3: `DrumChain.in_note` (qué nota dispara la cadena) [4].

### Racks y macros
- Instrument/Audio/MIDI Effect Racks: cadenas paralelas, cada una en serie.
- **Hasta 16 macros** (8 visibles por defecto), botón Rand y **Variations**
  (estados guardados de macros) [5].
- Chain Selector 0–127 con zonas y fades: permite bancos de sonidos y crossfades [5].
- Desde 12.3 la API permite `Track.insert_device`, `Chain.insert_device` y
  `RackDevice.insert_chain` [4]. Es **clave**: antes no se podía insertar un
  device nativo arbitrario desde un Remote Script.

### Groove Pool (swing)
- Los grooves (`.agr`) se aplican a clips; en audio actúan sobre el warp, así que
  el clip tiene que estar warpeado [6].
- Parámetros: **Base** (resolución de medida), **Quantize**, **Timing**, **Random**
  (humaniza por voz), **Velocity** (−100 a +100) y **Global Amount** (hasta 130%) [6].
- **Commit** escribe el groove en el clip (mueve notas o crea warp markers) [6].
- API: `Song.groove_pool` (solo lectura, desde 11.0) y `Clip.groove`
  (get/set, desde 11.0); `Song.swing_amount` afecta la cuantización [7][2].

### Automatización vs envolventes de clip
- **Automatización:** valor absoluto del parámetro a lo largo del Arrangement (o
  grabada en clips de Session).
- **Envolventes de clip:** viven dentro del clip; pueden ser de **modulación**
  (relativa al valor actual) y pueden tener su propio loop, independiente del
  clip [8]. Útiles para movimientos que se repiten (filtro que respira cada 4 compases).
- API: `Clip.clear_envelope`, `clear_all_envelopes`, `has_envelopes` [2]. La
  escritura de envolventes por API (`automation_envelope` /
  `create_automation_envelope`) existe en el LOM pero **NO VERIFICADO** su alcance
  sobre la automatización del Arrangement.

### Ruteo, sidechain y returns
- Compressor, Glue Compressor, Multiband Dynamics, Roar y Auto Filter tienen
  sección **Sidechain**: se disparan con otra pista o con una banda filtrada [9].
- Para sidechain "limpio", se toma la señal **pre-efectos** de la pista del kick [13].
- **Return tracks:** reverbs y delays compartidos; es la base del rumble (receta 6.2).

### Main y gain staging
- El motor es de 32 bits de punto flotante: superar 0 dB dentro de Live no recorta;
  solo importa al salir de Live (Main, salidas físicas, exportación) [10].
- Medidores Peak (cambios bruscos) y RMS (volumen percibido) [10].
- **Utility** es el device de ganancia: Gain, Width (0% = mono), Mono y **Bass Mono**
  (graves a mono, corte ajustable 50–500 Hz) [9].
- **Limiter** (12.x): modos de techo Standard, Soft Clip y **True Peak**; Maximize
  cambia el techo por un Threshold; ruteo L/R o M/S [9]. Un tutorial usa techo
  −0,3 dB en el Main [15].
- Headroom recomendado antes del master: práctica habitual, sin cifra oficial del
  manual (**NO VERIFICADO** un valor concreto).

## 2. Instrumentos nativos (Suite)

| Device | Para qué sirve | Parámetros clave | Uso típico en techno |
|--------|----------------|------------------|----------------------|
| **Operator** | FM de 4 osciladores + sustractiva [3] | 11 algoritmos, Coarse/Fine/Fixed, Feedback, 7 envolventes (loop/beat/sync), filtro con waveshaper | Kick sintético (seno + env de pitch), **rumble/sub FM**, hats y ruido, bajos, stabs metálicos |
| **Wavetable** | 2 osc. wavetable + sub, 2 filtros [3] | Posición de tabla, efectos de osc (FM/Classic/Modern), ruteo de filtros, matriz, 6 modos de unison | Leads, pads, bajos modernos, stabs |
| **Drift** | Sustractivo simple [3] | 2 osc, LPF + HP, env cíclica, matriz de 3 slots | Bajos y stabs rápidos, baja CPU |
| **Analog** | Analógico virtual (modelado) [3] | 2 osc + ruido, 2 filtros multimodo, 2 LFO | Bajos, pads, **risers de ruido** [16] |
| **Meld** | Bi-tímbrico de "macro osciladores" (12.0) [4] | 2 engines con macros por oscilador, filtros, matriz, MPE; desde 12.2 osc Chord | Texturas, leads, bajos raros, acordes |
| **Simpler** | Sampler simple | Modos Classic/One-Shot/Slicing, filtro, 3 ADSR, warp | One-shots de drums, stabs sampleados, rehacer loops |
| **Sampler** | Multisampler | Zonas (key/vel/select), Round Robin, osc de modulación, 3 LFO | Instrumentos multisampleados; raro en techno |
| **Drum Rack** | Contenedor de batería | Pads, choke, returns internos | **Toda la batería** |
| **Drum Sampler** | One-shot para Drum Rack (12.1) [4] | Start, Length, env AHD, Pitch, 9 Playback Effects, Filter | Kick, clap, hats sampleados con carácter; reemplaza a DS Sampler |
| **Impulse** | Drum sampler de 8 slots [3] | Stretch, filtro, saturador por slot | Kits rápidos; legado |
| **Collision** | Percusión modelada (mazo + resonadores) [3] | Exciters Mallet/Noise, resonadores Beam/Marimba/Membrane/Plate/Pipe/Tube | Percusión metálica, bleeps, tops tonales |
| **Tension** | Cuerda física modelada [3] | Exciter (Bow/Hammer/Plectrum), Damper, Termination, Body | Plucks y percusión tonal oscura (uso marginal) |
| **Electric** | Piano eléctrico modelado [3] | Hammer, Fork, Damper/Pickup | Acordes tipo Rhodes en tech house |
| **Granulator III** | Granular M4L (Robert Henke), viene con Suite 12 [17] | Modos **Classic, Loop, Cloud**; Grain Size, Scan, Capture | Atmósferas, drones, transformar loops |
| **DS Kick** | Kick sintético M4L [11] | Pitch (Hz), Drive, OT, Attack, Click, Decay, Env, Volume | Kick base o capa de sub |
| **DS Snare / Clap / HH / Tom / Cymbal / Clang / FM** | Drum synths M4L [11] | Snare: osc + ruido; Clap: ruido filtrado + delays; Cymbal: seno/pulso + ruido; FM: estilo FM japonés | Claps, hats y percusión sintética |

Notas:
- Que Collision, Tension, Electric, Meld, Roar y los DS sean exclusivos de Suite
  sale de la comparativa de ediciones [18]; el manual no lo marca por device.
  Para el nexo da igual: Gabriel tiene Suite.
- Granulator III: Ableton indica "Standard con Max for Live" y Henke dice "Suite";
  en cualquier caso **está disponible** en Suite [17].
- DS HH no apareció en el texto del manual que se leyó (**NO VERIFICADO** su
  descripción, sí su existencia en la lista de 33.1 [11]).
- External Instrument no es fuente de sonido: rutea MIDI a hardware [3].

## 3. Efectos de audio

### Dinámica
| Device | Para qué | Parámetros clave | Uso en techno |
|--------|----------|------------------|---------------|
| Compressor | Compresión general con sidechain [9] | Threshold, Ratio, Attack, Release, Sidechain (Audio From, EQ) | **Ducking** de bajo/rumble/pads con el kick |
| Glue Compressor | Bus compressor modelado, "pega" grupos [9] | Knee se endurece con el ratio; sidechain | Grupo de kick (−5 dB de GR [13]), bus de drums, Main |
| Multiband Dynamics | Hasta 3 bandas, compresión/expansión arriba y abajo [9] | Umbral superior e inferior por banda | Control de graves en rumble, de-essing de hats |
| Limiter | Limitador de mastering [9] | Ceiling, Standard/Soft Clip/True Peak, Maximize, L/R–M/S | Main; limitar el kick |
| Gate | Deja pasar solo lo que supera el umbral [9] | Threshold, Return, Flip, Lookahead, Hold, Floor | Recortar colas de reverb/rumble; gate rítmico con sidechain |
| Drum Buss | Procesador de batería analógico: compresión, distorsión, graves [9] | Drive, Crunch, Damp, Transients, **Boom** (sub afinado) | **Kick**: Boom afinado a la tónica [19] |

### EQ y filtro
| Device | Para qué | Uso en techno |
|--------|----------|---------------|
| EQ Eight | EQ paramétrico de 8 bandas, modo M/S | Esculpir todo; cortes en 120 Hz/800 Hz del kick [13]; HPF a los laterales |
| EQ Three | EQ de 3 bandas tipo DJ | Kills rápidos, transiciones |
| Channel EQ | 3 bandas tipo consola con HPF de 80 Hz conmutable [9] | Limpieza rápida de pistas |
| Auto Filter | Filtro con LFO, envolvente y sidechain. **Rediseñado en 12.2**: tipos DJ, Comb, Vowel, Resampling, Notch+LP; circuitos SVF, DFM, MS2, PRD; LFO Morph [4] | **Barridos y builds**, oscurecer el envío del rumble |

### Saturación y distorsión
| Device | Para qué | Uso en techno |
|--------|----------|---------------|
| Saturator | Waveshaper con 8 curvas (Analog Clip, Soft Sine, Bass Shaper, Medium/Hard Curve, Sinoid Fold, Digital Clip, Waveshaper) [9] | Calentar kick y bajo; Soft/Hard Clip post para no pasar el Output |
| Roar | Saturación dinámica (12.0) con ruteos Single, Serial, Parallel, Multi Band, Mid Side, Feedback y Delay; filtros, LFOs, matriz [9][4] | Bajos agresivos, rumble sucio, stabs industriales |
| Overdrive | Distorsión con banda enfocada | Saturación del grupo de kick [13] |
| Pedal | Overdrive / Distortion / Fuzz de guitarra [9] | Leads y percusión ácida |
| Redux | Downsampling + bit reduction [9] | Lo-fi en stabs y hats |
| Erosion | Degradación con ruido/seno. **Rediseñado en 12.4** (Noise Blend, Stereo Width); la versión vieja queda como Erosion Legacy [4] | Aire y suciedad en hats |
| Drum Buss / Amp / Cabinet / Dynamic Tube / Vinyl Distortion | Coloración extra | Amp en el envío del rumble [14] |

### Espacio
| Device | Para qué | Uso en techno |
|--------|----------|---------------|
| Reverb | Algorítmica clásica (preset **Dark Hall**) | **Rumble**, profundidad de claps [13] |
| Hybrid Reverb | Convolución + algorítmica (Dark Hall, Quartz, Shimmer, Tides, Prism), ruteo Serial/Parallel [9] | Espacios grandes, rumble con IR |
| Echo | Delay de carácter tape/analógico | Dub en stabs, delays con filtro pasabanda |
| Delay | Delay limpio; **LFO ampliado en 12.4** [4] | Delays de 1/16 o 1/8 punteado |
| Filter Delay | 3 delays filtrados | Tops y percusión espacial |
| Grain Delay | Delay granular con pitch [9] | FX y texturas |
| Spectral Time | Freeze + delay espectral [9] | Colas y transiciones |

### Modulación
| Device | Para qué | Uso en techno |
|--------|----------|---------------|
| Chorus-Ensemble | Chorus/ensemble; Chorus refinado en 12.4 [4] | Ancho de pads y stabs |
| Phaser-Flanger | Phaser, Flanger y Doubler con 2 LFO [9] | Movimiento en hats y loops |
| Auto Pan-Tremolo | Ex Auto Pan (12.3), modos Panning y Tremolo [4] | Pseudo-sidechain, paneo de percusión |
| Shifter | Pitch/frequency shifter con ring mod [9]. Reemplaza al viejo Frequency Shifter (**NO VERIFICADO** la fecha exacta) | Metalizar percusión, risers |
| Auto Shift | Corrección/seguimiento de pitch con formantes (12.1) [4] | Voces |
| Vocoder | Carrier + modulador [9] | Voces robóticas, stabs vocales |
| Corpus | Resonancia de cuerpos físicos | Percusión tonal |
| Resonators | 5 resonadores paralelos afinables [9] | Dar tono a ruido o percusión |
| Spectral Resonator | Resonancias espectrales, tocable por MIDI (16 voces) [9] | Texturas tonales |
| Beat Repeat | Repeticiones y stutter rítmico | Fills y builds |

### Utilidad y medición
| Device | Para qué |
|--------|----------|
| Utility | Gain, Width, Mono, **Bass Mono** [9] |
| Spectrum | Análisis de frecuencia en tiempo real, no altera audio [9] |
| Tuner | Afinación de señales monofónicas [9]; afinar kick y rumble |
| Align Delay, LFO, Envelope Follower, Shaper (M4L) | Modulación de parámetros de otros devices [11] |

## 4. Efectos MIDI y MIDI Tools

**Efectos MIDI** (en la cadena de la pista) [12]:
- **Arpeggiator:** patrones a partir de acordes o notas; gate, retrigger, velocity.
- **Chord:** agrega hasta 6 notas por nota entrante (stabs con una sola tecla).
- **Scale:** remapea a una escala (matriz 13×13).
- **Note Length**, **Pitch**, **Random** (con restricción a escala), **Velocity**
  (rango, curva, random), **CC Control** (12.0).
- M4L: Envelope MIDI, Expression Control, MPE Control, Note Echo, Shaper MIDI [11].

**MIDI Tools del Clip View** (Live 12): paneles **Transform** y **Generate** que
editan las notas del clip, no procesan en tiempo real [8][4]:
- Transformaciones: Arpeggiate, Chop (12.1), Connect, Glissando (12.1), LFO (12.1),
  Ornament, Quantize, Recombine, Span, Strum, Time Warp, Velocity Shaper.
- Generadores: Rhythm, Seed, Shape, Stacks, Euclidean.
- Se pueden sumar MIDI Tools hechas en Max for Live [8].

## 5. Recetas de diseño de sonido (techno peak time)

### 5.1 Kick (capas + saturación) [13][19]
1. Tres capas (agudo/click, medio, grave) en pistas separadas, filtradas y con EQ.
2. Agrupar; **Glue Compressor** con ~−5 dB de reducción.
3. **EQ Eight**: cortar ~120 Hz y ~800 Hz (barro), low shelf en ~80 Hz.
4. **Overdrive** (o Saturator) para densidad; **Limiter** con release Auto.
5. Alternativa sintética: DS Kick u Operator; **Drum Buss** con Boom afinado
   (ej. Drive 30%, Crunch 11%, Boom 17%, Damp 14,9 kHz en un análisis de
   Attack; otro tutorial usa Crunch 24%, Boom 50%, Transients 0) [19].

### 5.2 Rumble (envío de reverb → EQ → sidechain) [13][14][20]
1. Send del grupo de kick a un return, a fondo.
2. En el return: **Reverb** (preset Dark Hall) o Hybrid Reverb al 100% wet;
   ajustar pre-delay y decay.
3. Oscurecer: **Auto Filter** pasabajos (un tutorial lo fija en ~96,6 Hz) y/o Amp
   para saturar [14].
4. **Compressor** con sidechain desde el kick (señal pre-efectos [20]) para que la
   cola bombee en el contratiempo.
5. **EQ Eight** M/S para quitar graves de los laterales, cortar subgraves extremos y
   resonancias (ej. 135 Hz); **Utility** Bass Mono bajo ~120 Hz; Limiter [14].

### 5.3 Bajo (rolling) [15]
- Sub: sample o seno afinado a la tónica, LPF ~80 Hz, saturación ~35% wet.
- Línea: saw/square con ataque rápido (Operator, Analog, Wavetable, Drift);
  semicorcheas **dejando vacía la primera de cada tiempo** para no chocar con el kick.
- EQ Eight: HPF ~65 Hz, LPF ~350 Hz; sidechain del kick con release lento.

### 5.4 Stabs / acordes [21][22]
- **Chord** (ej. menor 7) sobre una sola nota; ataque 0, decay corto, filtro con
  envolvente; EQ para recortar graves y agudos; Redux sutil y compresión suave.
- Espacio: reverb grande (rave) o **Echo** (dub); sidechain del return de reverb al kick.
- Clásico: resamplear el stab y tocarlo desde Simpler.

### 5.5 Hats y tops
- Desde pack: Drum Rack con choke entre hat cerrado y abierto [5]; Groove Pool para
  swing [6].
- Sintéticos: DS HH / DS Cymbal [11]; Operator con ruido. **NO VERIFICADO** una
  receta de techno con fuente para hats sintetizados.
- Capa percusiva extra: duplicar el kick con Delay 1/16 al 100% wet, EQ antes y
  después, y ensanchar [15].

### 5.6 FX y risers [16][23]
- Ruido blanco (Operator o Analog) → filtro pasabajos con cutoff automatizado
  que se abre.
- Auto Filter en un Audio Effect Rack con macros para builds; Beat Repeat para fills.

## 6. Implicancias para el nexo

**Controlable por API (según LOM y release notes):**
- Tempo, escala del Set y desde 12.4.15 la escala por clip [7][4].
- Notas MIDI (`add_new_notes`, `apply_note_modifications`), warp mode, warp markers,
  gain y pitch de clips de audio [2].
- Groove de cada clip (`Clip.groove`) y lectura del Groove Pool [2][7].
- **Insertar devices nativos y cadenas** (`Track.insert_device`,
  `RackDevice.insert_chain`, desde **12.3**) y cambiar el sample de Simpler
  (12.4) [4]. **El entorno verificado tiene 12.1.1: hay que actualizar a 12.4.16
  (D-09) para usar esto.**
- Parámetros de cualquier device vía `DeviceParameter` (se vuelcan en el dump).

**Solo por UI o NO VERIFICADO por API:**
- Cargar un groove nuevo al Groove Pool (`groove_pool` es de solo lectura) [7].
- Ejecutar las **MIDI Tools** de Clip View (Transform/Generate): **NO VERIFICADO**
  que tengan API. Alternativa: que Claude genere las notas directamente.
- Escribir automatización del Arrangement por API: **NO VERIFICADO**.
- Elegir modo de Simpler, "Slice to Drum Rack", Stem Separation (12.3, Suite),
  Bounce: **NO VERIFICADO** por API.

**Catálogo mínimo para empezar** (cubre un tema de techno entero):
1. Drum Rack + Simpler + Drum Sampler (batería y one-shots del pack).
2. Operator y Drift (kick sintético, sub, bajo, ruido, stabs simples).
3. EQ Eight, Compressor (sidechain), Glue Compressor, Utility, Limiter.
4. Saturator, Drum Buss, Overdrive.
5. Reverb, Echo, Auto Filter.
6. Chord y Arpeggiator (MIDI).
Después: Wavetable, Roar, Hybrid Reverb, Multiband Dynamics, Beat Repeat.

## Pendiente de este frente
- Dump de parámetros de los devices del catálogo mínimo vía puente (P-03).
- Verificar en el LOM si las MIDI Tools y la automatización del Arrangement son
  accesibles.
- Actualizar Live a 12.4.16 y confirmar `insert_device` contra el Live real.

## Fuentes
1. https://www.ableton.com/en/manual/audio-clips-tempo-and-warping/
2. https://docs.cycling74.com/apiref/lom/clip/
3. https://www.ableton.com/en/manual/live-instrument-reference/
4. https://www.ableton.com/en/release-notes/live-12/
5. https://www.ableton.com/en/manual/instrument-drum-and-effect-racks/
6. https://www.ableton.com/en/manual/using-grooves/
7. https://docs.cycling74.com/apiref/lom/song/
8. https://www.ableton.com/en/manual/editing-midi/ y https://www.ableton.com/en/manual/automation-and-editing-envelopes/
9. https://www.ableton.com/en/manual/live-audio-effect-reference/
10. https://www.ableton.com/en/manual/mixing/
11. https://www.ableton.com/en/manual/max-for-live-devices/
12. https://www.ableton.com/en/manual/live-midi-effect-reference/
13. https://www.attackmagazine.com/technique/tutorials/adding-reverb-techno-kick/
14. https://musicradar.com/how-to/rumbling-techno-kick
15. https://www.attackmagazine.com/technique/tutorials/warehouse-rolling-techno-bass/
16. https://www.synthtopia.com/content/2010/09/15/ableton-live-tutorial-making-a-white-noise-buildup/
17. https://www.ableton.com/en/packs/granulator-iii/ y https://roberthenke.com/technology/granulator3.html
18. https://www.ableton.com/live/compare-editions/
19. https://www.attackmagazine.com/technique/beat-dissected/underground-resistance-the-final-frontier/ y https://pcaudiolabs.com/how-to-use-the-ableton-live-drum-buss-audio-effect/
20. https://www.bonedo.de/artikel/bass-drum-rumble-rattle-for-techno
21. https://musicradar.com/how-to/rave-chord-stab
22. https://www.ableton.com/en/blog/designing-dub-chords-in-ableton-live-with-el-chooppizza-hotline/
23. https://modeaudio.com/magazine/creating-a-performanceriser-filter-in-ableton
