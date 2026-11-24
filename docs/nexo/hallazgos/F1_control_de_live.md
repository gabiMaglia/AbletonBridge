# F1 — Control de Live

> Investigación web del 2026-11-18 (docs del LOM, release notes de Live 12,
> código y issues de los puentes, docs oficiales de Claude Code). Fuentes al final.
> **Nada de esto se probó todavía contra el Live instalado.** Lo que dice
> "NO VERIFICADO" no se pudo confirmar en ninguna fuente.

## Hallazgo principal

**El límite es la versión de Live, no el puente.** Todos los puentes (el nuestro,
ableton-mcp, AbletonOSC, Max for Live) usan la misma API de Live. Varias llamadas
críticas para el nexo llegaron después de la 12.1.1 instalada:

| Llamada | Para qué la necesitamos | Desde |
|---------|-------------------------|-------|
| `Track.create_midi_clip(start, length)` | Clip MIDI directo en Arrangement | 12.1.10 (M4L; en Python NO VERIFICADO) |
| `Track.create_audio_clip(path, position)` | Sample del pack directo en Arrangement | 12.2 |
| `Track.insert_device(name, index)` | Cargar un device nativo por nombre | 12.3 |
| `RackDevice.insert_chain`, `DrumChain.in_note` | Armar racks y drum racks | 12.3 |
| `SimplerDevice.replace_sample(path)` | Poner un one-shot del pack en Simpler | 12.4 |
| Fixes de crash en `create_audio_clip`, `create_midi_clip`, `duplicate_clip_to_arrangement` | Estabilidad del arrangement | 12.3 / 12.4 |

Última versión disponible a la fecha: **12.4.16** (30/10/2026, bugfix de
instalación en Windows sobre 12.4.15). Verificado en las release notes.

Ableton no publica referencia oficial de la API de Python. Todo método se
comprueba en runtime con `hasattr()` antes de usarlo, y en Python los argumentos
son solo posicionales.

## Qué se puede hacer (en 12.4.x)

### Tracks, mixer y ruteo
- Crear tracks de audio, MIDI y return; borrar y duplicar (`Song.create_*_track`).
- Volumen, pan y sends vía `Track.mixer_device` (son `DeviceParameter`).
- Ruteo de entrada y salida (`input/output_routing_type/channel`).
- **No se puede crear un group track ni agrupar tracks.** Solo se lee si un
  track está agrupado.

### Samples
- **Session:** `ClipSlot.create_audio_clip(path)` con ruta absoluta (existe desde
  12.0.5 según foro; en 12.1.1 probablemente sí).
- **Arrangement:** `Track.create_audio_clip(path, position)` desde 12.2.
- **Browser:** `browser.load_item(item)` no acepta rutas arbitrarias. El archivo
  tiene que estar en un lugar del browser (Places, User Library). Para el pack
  esto significa **agregar la carpeta del pack a Places** o usar las llamadas
  por ruta.
- **Simpler:** `replace_sample(path)` desde 12.4.
- Cargar un sample en un pad de Drum Rack: NO VERIFICADO.

### Devices
- Nativos por nombre: `Track.insert_device` (12.3). No sirve para plugins ni M4L.
- Nativos, presets, plugins VST/AU y M4L vía browser: `browser.load_item` (carga
  en el track seleccionado, tipo hotswap; comportamiento exacto NO VERIFICADO).
- Presets de plugin: `PluginDevice.presets` / `selected_preset_index`.
- Racks: `insert_chain` (12.3).

### Arrangement
- Leer clips: `Track.arrangement_clips`.
- Crear: `create_midi_clip` / `create_audio_clip` (ver tabla de versiones), o
  `duplicate_clip_to_arrangement(clip, time)` desde Session.
- Borrar: `Track.delete_clip(clip)`.
- **Mover un clip no se puede** (`start_time` es solo lectura): se duplica en la
  nueva posición y se borra el original.
- Recortar dentro del clip: `start_marker`, `end_marker`, `loop_start`,
  `loop_end`, `looping`.
- Locators: `Song.set_or_delete_cue()` en la posición del playhead
  (`current_song_time`), y `CuePoint.name`. Sirve para marcar intro/break/drop.

### Automatización — el hueco más grande
- **Envelopes de clip:** sí (`Clip.create_automation_envelope(param)`,
  `Envelope.insert_step(time, length, value)`). Solo desde Python, no desde M4L.
- **Lanes de automatización del track en Arrangement: NO hay API.**
  `automation_envelope` devuelve None en clips de Arrangement.
- Workarounds a probar:
  1. Escribir envelopes en un clip de Session y duplicarlo al Arrangement.
     Que la automatización sobreviva a la duplicación es NO VERIFICADO.
  2. Grabar automatización: activar `record_mode`, reproducir y cambiar
     `DeviceParameter.value` desde el script en tiempo real. Lento (tiempo real)
     y sensible al timing.
  3. Automatizar dentro de cada clip (envelopes de clip en clips de audio/MIDI
     de Session antes de pasarlos). Mismo riesgo que el punto 1.
- **Ningún puente existente resuelve esto.** Hay que construirlo igual.

### Warp
Todo disponible: `warping`, `warp_mode` (0 a 6), `warp_markers`,
`add_warp_marker` / `move_warp_marker` / `remove_warp_marker`, `pitch_coarse`,
`pitch_fine`, `gain`. 12.1.5 corrigió un crash al setear `looping` y `warping`
en el mismo evento.

### Slicing y chop (D-07: kick + rumble)
- Simpler en modo Slicing: `playback_mode = 2`, `Sample.insert_slice`,
  `move_slice`, `remove_slice`, `clear_slices`, `slicing_style`,
  `slicing_sensitivity`, `slicing_beat_division`.
- Edición del sample dentro de Simpler: `crop()`, `reverse()`, `warp_as`,
  `warp_double`, `warp_half`.
- **"Slice to New MIDI Track" y "Slice to Drum Rack" no están en la API.**
  Equivalente posible: Simpler en Slicing + clip MIDI que dispare las slices.

### Edición sobre la grilla
- `Clip.crop()`, `quantize`; `duplicate_loop` y `duplicate_region` solo MIDI.
- **No hay split, consolidate, reverse de clip de audio ni fades por API.**
- Chop de un loop de audio en Arrangement = varias copias del mismo clip con
  distintos `start_marker`/`end_marker` (vía duplicar + recortar). Viable en
  teoría, NO VERIFICADO en la práctica.
- Notas MIDI: `add_new_notes`, `get_notes_extended`, `apply_note_modifications`,
  `remove_notes_extended` (11.0+).

### Lo que no existe por API
Exportar/renderizar, freeze/flatten, bounce/resample, guardar el set, crear
grupos. Workarounds externos (atajos de teclado, automatización de UI del SO,
grabar en un track de resample) NO VERIFICADOS. Por D-01 el render y el guardado
los puede hacer Gabriel a mano sin costo real.

### Parámetros (base para el catálogo F5 / P-03)
`Device.parameters` expone **solo los parámetros automatizables**. Cada uno trae
`name`, `original_name`, `min`, `max`, `default_value` (no cuantizados),
`value_items` (cuantizados), `is_quantized`, `value`, `str_for_value(v)`.
`Device.class_name` sirve para agrupar. El volcado del catálogo es viable con el
puente propio.

## Puentes existentes

| | Nuestro Remote Script | ableton-mcp | AbletonOSC | Max for Live | Extensions SDK |
|---|---|---|---|---|---|
| Qué es | Remote Script + MCP (Python) | Remote Script + MCP (Python), MIT | Remote Script con OSC, MIT | Device .amxd en el set | SDK oficial de Ableton (JS, Node 24) |
| Transporte | TCP JSON, **127.0.0.1**, 19845 | TCP JSON, 127.0.0.1:9877, sin auth | **UDP en 0.0.0.0**, sin auth | Interno; afuera lo que armes | NO VERIFICADO |
| Estado | 2 tools, nunca probado en Live | 3.4k ★, activo (sep 2026), v1.7.1 | 853 ★, sin push desde nov 2025 | Oficial | **Beta, requiere Live 12.4.5 Suite** |
| Browser / devices | — | Sí (`load_item` por URI) | No | **No hay Browser**; `insert_device` desde 12.3 | NO VERIFICADO |
| Audio por ruta | — | Sí, solo Session; auto-warpea (#137) | No | Sí (misma API) | NO VERIFICADO |
| Arrangement | — | Solo leer / duplicar | Solo leer | Misma API | NO VERIFICADO |
| Automatización | — | Solo lectura | No | No | NO VERIFICADO |
| Warp markers | — | Solo lectura | Solo `warp_mode` | Sí | NO VERIFICADO |
| Slicing | — | No | No | Sí | NO VERIFICADO |
| Notas / parámetros | — | Sí / Sí (sin chequear rango) | Sí / Sí | Sí / Sí | Sí (con transacciones y undo) |

Notas:
- **ableton-mcp:** el más completo para "IA que arma temas", pero trae
  **telemetría activada por defecto**, bugs de timeout (#136: si vence el
  timeout la orden igual se ejecuta y el cliente recibe error), auto-warp al
  crear audio (#137), no carga efectos en el master en Live 12 (#127) y
  desconexiones en Windows (#90). Su código (MIT) es buena referencia.
- **AbletonOSC:** bueno para MIDI y parámetros, inútil para producir (sin
  browser, sin audio, arrangement solo lectura) y expuesto a la LAN.
- **Max for Live:** sin Browser, depende de un device cargado, corre en el hilo
  de baja prioridad (`defer`/`deferlow`). Ningún método que necesitemos es
  exclusivo de M4L: la API es la misma. Sirve como **plan B** para algo puntual.
- **Extensions SDK:** el único camino oficial y con undo/transacciones, pero está
  en beta y no se sabe si cubre browser, audio y automatización. Revisar cuando
  salga estable. Hay MCPs de la comunidad montados encima (ej. alaarab/livemcp,
  no revisado).
- No existe un MCP oficial de Ableton para controlar Live (NO VERIFICADO, una
  sola fuente secundaria).

## Cómo se conecta con Claude Code (sin API key)

- Claude Code con login de suscripción usa servidores MCP locales (stdio) sin
  API key. Se registran con `claude mcp add --transport stdio ...` o con un
  `.mcp.json` en el repo (scope project, commiteable). En Windows: ruta absoluta
  al `python.exe` del venv.
- **Skill** (`.claude/skills/<nombre>/SKILL.md` + archivos de apoyo): el
  conocimiento del nexo (perfiles de género, catálogo de devices, reglas de
  flujo) vive como md enlazados desde la skill. Claude carga solo el que
  necesita. Encaja con D-08.
- **Plugin**: empaqueta skill + MCP (+ subagentes, hooks) para instalar en un
  paso (`claude --plugin-dir` para probar). Solo vale la pena cuando haya que
  distribuirlo.
- Límites que condicionan el diseño:
  - Respuesta de una tool MCP: tope de 25.000 tokens (`MAX_MCP_OUTPUT_TOKENS`).
    El catálogo de devices se vuelca a archivo o por partes, nunca entero.
  - En Windows el servidor tiene que salir limpio al recibir EOF en stdin.
  - Cuotas de uso de la suscripción y llamadas largas: NO VERIFICADO.
- Si una skill puede restringir tools MCP con `allowed-tools`: NO VERIFICADO.

## Recomendación

1. **Seguir con el Remote Script propio.** Ya tiene lo que los otros no:
   bind a 127.0.0.1, cola hacia el hilo de UI, sin telemetría, y es Python
   (catálogo de devices y envelopes de clip solo están en Python). Ningún puente
   cubre automatización de Arrangement ni warp markers, así que adoptar uno no
   ahorra lo difícil. Tomar ideas del código de ableton-mcp (MIT).
2. **Actualizar Live a 12.4.x** antes de construir: destraba arrangement por
   ruta, `insert_device`, racks y `replace_sample`. Sin eso el nexo depende de
   Session + `duplicate_clip_to_arrangement` y del browser.
3. **Primera prueba real** (pendiente desde T-002): handshake + un script de
   sondeo que liste qué métodos existen (`hasattr`) en el Live instalado.
4. **Spike de automatización** apenas haya handshake: probar los workarounds
   (envelopes de Session duplicados y grabación). Es el riesgo que puede cambiar
   el diseño.
5. Empaquetado: MCP (acciones) + skill (conocimiento en md). Plugin más adelante.

## Prueba real (bitácora)

- **2026-11-22:** Gabriel instaló **Live 12.4.16** (confirmado en el log de Live).
  Antes de probar se detectó que el Remote Script **no podía cargarse**: le
  faltaba `create_instance(c_instance)`, el punto de entrada que Live busca.
  Los tests de T-002 no lo detectaron porque nunca simulan la carga desde Live.
  Se abrió T-002b: punto de entrada + bombeo de la cola en el hilo de Live +
  comando `probe_api` (lista qué métodos existen de verdad con `hasattr`).
- La User Library está en `C:\Users\Gabriel Maglia\Documents\Ableton\User Library`.
  El script se instala en `User Library\Remote Scripts\AbletonBridge\`.
- **2026-11-22 — primera conexión real OK.** Live cargó el script
  ("listening on 127.0.0.1 port 19845"). Desde afuera respondieron `ping`
  (`live_version 12.4.16`, `api_level 12`), `get_state` (tempo, tracks) y
  `probe_api`.
- **`probe_api`: los 23 métodos sondeados existen en 12.4.16.** Entre ellos
  `Track.create_audio_clip`, `Track.create_midi_clip`, `Track.insert_device`,
  `SimplerDevice.replace_sample`, `RackDevice.insert_chain`, los de warp
  markers, envelopes de clip, `Clip.crop` y `Browser.load_item`. Existir no
  significa que se comporten como dice la doc: eso se prueba uso por uso.
- Sigue abierto el riesgo mayor: **automatización en Arrangement** (spike).
- **2026-11-22 — spike 1 (Session → Arrangement): FUNCIONA, con matiz.**
  Se escribieron envelopes de volumen y de `Frequency` (Auto Filter) en un clip
  MIDI de Session y se duplicó con `duplicate_clip_to_arrangement`. Gabriel
  confirmó a oído y a la vista: en el Arrangement la automatización suena y
  **vive adentro del clip** (envelopes de clip), **no en la lane del track**.
  - La API no puede leer esos envelopes en el clip de Arrangement
    (`automation_envelope` devuelve None), aunque existen.
  - `automation_state = 1` en ambos parámetros.
  - Al releer el envelope en Session, los valores no forman una rampa pareja
    (0,85 → 0,42 → 0,80): pendiente revisar cómo se escriben los pasos.
  - Implicancia: la automatización queda atada al clip. Para un barrido largo
    (ej. filtro en un build de 32 compases) el clip tiene que cubrir toda la
    sección. Sirve para el nexo, pero no es la lane "normal" del track.
  - Nombres reales de parámetros de Auto Filter (12.4) obtenidos: 45, entre
    ellos `Frequency`, `Resonance`, `Filter Type`, `Drive`, `Dry/Wet`,
    `S/C On` (primer dato real para el catálogo, P-03).
- **2026-11-22 — spike 2 (grabar automatización en Arrangement): NO GRABA**
  (intento 2, con el transporte corregido). Con `record_mode = True` y el
  transporte corriendo del compás 9 al 11, el script cambió volumen y
  `Transpose` de Operator en 40 pasos, pero no quedó automatización en la lane
  (`automation_state = 0`, confirmado a la vista por Gabriel). El intento 1
  falló por un bug del spike (contaba con la posición vieja del transporte).
  Hipótesis: falta **Automation Arm** encendido (no se sabe si la API lo expone).
- **2026-11-22 — spike 2, intento 3: GRABA en la lane del track.** Con
  **Automation Arm** encendido a mano, la misma rampa quedó grabada como
  automatización del Arrangement (`automation_state = 1`; Gabriel vio la curva
  de `Transpose` de Operator en la lane, compases 9 a 11).
  - **Automation Arm = `song.session_automation_record`** (pasó de `false` a
    `true` al encenderlo). Según la doc del LOM es escribible: falta confirmar
    que el script lo pueda encender solo.
  - Costo: se graba **en tiempo real** (lo que dura la sección). Se pueden
    grabar varios parámetros en la misma pasada.

### Conclusión de automatización

Hay dos caminos que funcionan y se complementan:

| Camino | Dónde queda | Velocidad | Uso en el nexo |
|--------|-------------|-----------|----------------|
| Envelopes de clip + `duplicate_clip_to_arrangement` | Adentro del clip | Instantáneo | Movimientos atados a un elemento (filtro de un loop, volumen de un stab) |
| Grabación con Automation Arm + `record_mode` | Lane del track | Tiempo real | Movimientos de sección o de mezcla (builds, breakdowns, sends, master) |

El riesgo que podía invalidar el diseño queda **descartado**.

### Ronda 2 de spikes (2026-11-22, T-002d)

| Spike | Resultado | Detalle |
|-------|-----------|---------|
| Automation Arm por API | **Dudoso** | Se escribió `session_automation_record = False` y la relectura siguió dando `True`. Falta confirmar a la vista. |
| Audio por ruta al Arrangement | **OK** | `Track.create_audio_clip(path, pos)` creó el clip con warp activado (modo 0 = Beats) y ajustado al tempo del set. |
| Chop sobre la grilla | **OK** | Copia del mismo archivo con `loop_start`/`start_marker` = 1 y `loop_end`/`end_marker` = 2: clip que repite un solo tiempo del loop. |
| Warp mode + pitch | **OK** | `warp_mode = 6` es Complex Pro; `pitch_coarse = -2` aplicado. |
| Devices por nombre | **OK** | EQ Eight, Saturator, Compressor, Drum Buss y Utility insertados en cadena. Volcado completo de parámetros en `docs/nexo/catalogo/devices_spike_2026-11-22.json`. |
| Drum Rack en track de audio | Falla esperada | Live: "solo pueden insertarse efectos de audio en una pista de audio". Va en track MIDI. |
| Simpler + `replace_sample` | **OK** | Loop cargado por ruta; `playback_mode = 2` (Slicing) generó 8 slices automáticas; `clear_slices` + 4 `insert_slice` dejó 4 slices parejas. |
| Simpler one-shot | **OK** | Kick 808 cargado, `playback_mode = 1` (One-Shot). |

Hallazgos que cambian el diseño:
- **Los valores de parámetros son crudos, casi siempre 0 a 1.** La unidad real
  solo sale de `str_for_value` (ej. Saturator Drive 0,5 = "0.0 dB"; Utility
  Bass Freq 0,38 = "120 Hz"). El catálogo (P-03) tiene que mapear valor crudo ↔
  valor con unidad, muestreando `str_for_value`.
- **Los nombres de la API no siempre son los de la interfaz:** la ganancia de
  Utility es `Output`, no `Gain`. El catálogo se arma con los nombres reales
  del volcado, nunca de memoria.
- `class_name` interno difiere del nombre visible: Compressor = `Compressor2`,
  Utility = `StereoGain`, EQ Eight = `Eq8`.
- Live está en español: los mensajes de error llegan en español, pero los
  nombres de parámetros llegan en inglés.

### Lectura completa del set (T-008, `state.detail`) — 2026-11-22

Funciona en Live real: leyó canción, grupo, 6 tracks, clips con warp y
transposición, returns con sus devices y master, en una sola llamada (~25 KB).
Detalles: en un track de grupo `arrangement_clips` da "unavailable"
(los grupos no tienen clips; esperado). `warp_mode` 4 = Complex.

Primera lectura de un loop de Gabriel (`TESTLOOP`, 134 BPM, pack ZEN_PDT):
- Sin devices en ningún track ni en el master: el trabajo está en la
  **elección de loops, warp, transposición y volúmenes**.
- Sonando: arp (-10 dB), rumble (-8 dB, Complex, **transpuesto -3**: de A# a
  G), top (-17,8 dB), vox (-5 dB, Complex). Muteados: acid (-3,6 dB) y drums
  (-3 dB).
- Warp: Beats para loops rítmicos y de synth; Complex para rumble y voz.
- Returns A-Reverb (2,5 s) y B-Delay creados pero sin envíos.

Pendientes de la ronda 2:
- **Automation Arm contradictorio:** la API leyó `session_automation_record =
  True` antes y después de escribir `False`, pero Gabriel vio el botón
  **apagado**. La relectura no es confiable o la propiedad no es exactamente ese
  botón. Repetir con observación directa.
- **Crash de Live a las 16:30:36** (`EXCEPTION_ACCESS_VIOLATION`, con crashdump
  en `Preferences\Crash`). En el log, justo antes, el driver de audio pasó a
  "No Audio" y se guardaron preferencias; no hay líneas de AbletonBridge cerca.
  **No se puede atribuir al script** con lo que hay; queda en observación.
- Audio de Gabriel: driver WaveOut (Traktor Audio 10), buffer 4096, 85 ms de
  latencia (dato de entorno, no afecta al puente).

- Al cerrar Live sin guardar se perdió el set del spike 1: la API no puede
  guardar el set (ya sabido); guardar queda en manos de Gabriel.

## Decisiones pendientes

| # | Pregunta | Para quién |
|---|----------|------------|
| F1-Q1 | ~~¿Actualizar Live?~~ Resuelto por D-09: la versión no es un límite. Objetivo: última 12.4.x estable. | — |
| F1-Q2 | ~~¿Remote Script propio u otro puente?~~ Resuelto por D-11: Remote Script propio. | — |

## Fuentes

API de Live:
- https://www.ableton.com/en/release-notes/live-12/
- https://docs.cycling74.com/apiref/lom/track/ (y `clip`, `clipslot`, `song`,
  `simplerdevice`, `sample`, `deviceparameter`, `mixerdevice`, `rackdevice`,
  `plugindevice`, `device`, `application`)
- https://docs.cycling74.com/apiref/js/liveapi/
- https://photonicvelocity.github.io/LiveAPI/ (docstrings Python de Live 12.3.6)
- https://cycling74.com/forums/function-createaudioclip-class-clipslot-and-track-missing-lom
- https://cycling74.com/forums/writing-an-ableton-drum-rack-from-node-for-max-because-the-live-api-cant

Puentes:
- https://github.com/ahujasid/ableton-mcp (y su `AbletonMCP_Remote_Script/__init__.py`, issues #85 #90 #100 #127 #136 #137)
- https://github.com/ideoforms/AbletonOSC (issues #112 #121 #123 #124 #174 #212)
- https://github.com/leolabs/ableton-js
- https://github.com/Simon-Kansara/ableton-live-mcp-server
- https://www.ableton.com/en/live/extensions/
- https://www.ableton.com/en/blog/introducing-extensions-sdk
- https://www.issoh.co.jp/tech/details/10266/

Claude Code:
- https://code.claude.com/docs/en/mcp.md
- https://code.claude.com/docs/en/skills.md
- https://code.claude.com/docs/en/plugins/overview.md
- https://code.claude.com/docs/en/authentication.md

### Automatización grabada (T-012) — hallazgos en Live real (2026-11-22)

- `Song.start_playing()` arranca desde el **marcador de inicio** del
  Arrangement, no desde un `current_song_time` puesto por script con el
  transporte parado (pedido 712 → arrancó en 160).
- `Song.continue_playing()` con el transporte parado tampoco respeta ese
  `current_song_time` (arrancó en 1216).
- **Lo que funciona:** arrancar el transporte y, ya andando, asignar
  `current_song_time`: Live salta enseguida. La grabación (`record_mode`) se
  activa recién cuando el cursor cae en la ventana preroll → start.
- Primera grabación real OK: 6 lanes (5 volúmenes + Frequency del Auto Filter
  del master) en el puente de T02, 32 compases + preroll en ~1 minuto.
- `reload` no recarga módulos que el reloader en memoria no conoce: agregar un
  módulo nuevo al orden de recarga exige **un** reinicio de Live.
- Auto Filter recién insertado: low-pass en **10 kHz** (por eso la modulación
  de clip "hacia arriba" no tenía margen).
