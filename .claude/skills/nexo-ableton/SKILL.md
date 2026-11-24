---
name: nexo-ableton
description: Producir o editar temas en Ableton Live a traves del bridge (tools MCP live_*) con el nexo de Gabriel. Usar cuando se pida armar, editar o mezclar tracks, arreglos, automatizacion, FX, sends o master en Ableton, trabajar un genero (techno peak time, tech house) o usar el nexo.
---

# Nexo Ableton

El nexo produce musica en Ableton Live 12.4.x desde Claude Code. Las acciones son tools
MCP `live_*` (servidor `nexo-ableton`); el conocimiento vive en md del repo y se lee bajo
demanda. Responder en espanol.

## Reglas duras (inquebrantables)

1. **D-01 — Decide el oido de Gabriel.** No hay criterio automatico de "listo". Despues de cada
   capa, pedirle que escuche y esperar su veredicto antes de seguir.
2. **D-15 — Nunca automatizar volumen ni ganancia del track (fader).** El nivel que se mueve
   va en un **Utility al final de la cadena** (`live_utility_ensure_last`), param **`Output`**
   (no "Gain"). `target "volume"` esta rechazado por el bridge. `live_track_set_mixer`
   con `volume_db` solo para mezcla estatica.
3. **D-12 — Librerias solo de `G:\LIbrerias\2026`** (Places del browser de Live). Nada de otras rutas.
4. **D-08 — Todo queda en md** de `docs/nexo/`: acuerdos, criterios nuevos, bitacora del tema.
   Registrar al terminar cada capa, no al final.
5. **Una pregunta por vez.** Y esperar la respuesta.
6. **D-13 — Un criterio nuevo de Gabriel** se contrasta con fuentes y con las mediciones de
   referencias; si hay desacuerdo se plantea con evidencia y decide el.
7. Nunca guardar ni cerrar el set por Gabriel (la API no guarda); borrar pistas pide `confirm_name`.

## Flujo

1. **Brief**: genero, BPM, largo, referencias, pack/libreria. Leer el perfil del genero.
2. **Material**: elegir loops/one-shots (D-07: a criterio de Claude). Medir antes de colocar.
3. **Construir por capas** (cada una termina con "escucha y decime"):
   estructura y ritmica -> melodia/atmosfera -> transiciones (risers, reverses, impactos) ->
   movimiento dentro de loops -> detalles de frase (huecos, fills, crashes) ->
   profundidad (returns, sends) -> automatizacion real.
4. **Oyente**: Gabriel escucha y corrige. Cada correccion se anota en el tema.
5. **Criterios**: lo aprendido sube al perfil del genero con la confianza que diga F4/D-13.

Antes de tocar el set: `live_ping`, `live_get_state` (liviano) y, si hace falta,
`live_get_state_detail` (lo grande se vuelca a `.cache/` con resumen).

## Trampas conocidas del bridge

- **Automatizacion**: en Arrangement los envelopes de clip son **solo modulacion**
  (relativos a la perilla; no superan el valor del knob). Para un movimiento real de lane usar
  `live_automation_record` (graba en tiempo real: ~1 min por 32 compases + preroll).
  Los envelopes de Arrangement no se pueden releer: confirma el oido.
- **Transporte**: `start_playing` arranca del marcador, no del playhead puesto por script. El
  bridge arranca primero y salta despues; no repetirlo a mano.
- **One-shots**: Live los **auto-warpea** metiendo el sample entero en un largo adivinado
  (suena completo pero comprimido). Para que terminen/empiecen en un compas: medir -> borrar ->
  recolocar con `end_beat`. Usar `one_shot=true`.
- **Locators son asincronos**: `live_locator_set_many` y despues `live_locator_status`.
- **Reload vs reinicio**: `live_bridge_reload` recarga modulos sin reiniciar Live, pero un
  modulo **nuevo** que el reloader en memoria no conoce exige reiniciar Live una vez.
  `live_bridge_version` dice que cargo. Si Live reinicia, el servidor MCP reconecta solo en la
  siguiente llamada.
- **Timeouts y reintentos (T-023)**: lecturas 5 s, escrituras pesadas 30 s. Si una escritura da
  `BRIDGE_TIMEOUT`/`BRIDGE_DISCONNECTED` con "pudo haberse ejecutado", Live probablemente la aplico:
  **releer el estado antes de reintentar** (track.create duplicaria). Las lecturas se reintentan solas 1 vez.
- **Unidades de display**: tiempos en **ms** (8 s = 8000), frecuencias en Hz (kHz se normaliza),
  niveles en dB. Preferir `display` sobre `value` crudo (0..1). `within_tolerance` confirma.
- **Nombres de API != interfaz**: Utility `Output`, Compressor=`Compressor2`, Utility=`StereoGain`,
  EQ Eight=`Eq8`, Auto Filter=`AutoFilter2`. Parametros siempre en ingles aunque Live este en espanol.
  Catalogo real: `docs/nexo/catalogo/` y F5.
- **Drum Rack** solo en pista MIDI; en audio solo efectos. Auto Filter nuevo arranca en LP 10 kHz.
- **Grupos** no tienen clips (`arrangement_clips` "unavailable": esperado).
- **El indice de pista cambia** al crear/borrar: releer estado antes de usar indices viejos.
- No hay `live_*` para guardar el set ni borrar lanes (`live_automation_clear` es best-effort;
  a mano o regrabando encima).

## Donde esta el conocimiento (leer solo lo que se necesita)

- Vision y decisiones: `docs/nexo/00_vision_y_decisiones.md`
- Control de Live y bitacora del bridge: `docs/nexo/hallazgos/F1_control_de_live.md`
- Escucha de referencias: `docs/nexo/hallazgos/F2_escucha_de_referencias.md`
- Sample packs: `docs/nexo/hallazgos/F3_sample_packs.md`
- Techno peak time (criterios, arreglo): `docs/nexo/hallazgos/F4_techno_peak_time.md`
- Catalogo de devices Ableton: `docs/nexo/hallazgos/F5_catalogo_ableton.md` y `docs/nexo/catalogo/`
- Perfiles por genero: `docs/nexo/perfiles/` (en construccion)
- Temas ya hechos y su bitacora: `docs/nexo/temas/` (T01, T02)
- Contrato de comandos del bridge: `engram/04_api_contracts.md`
- Cheat-sheet de tools: [reference/comandos.md](reference/comandos.md)

Los md de F1..F5 son largos: buscar con una seccion concreta, no leerlos enteros.
