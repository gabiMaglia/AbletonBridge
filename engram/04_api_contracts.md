# API Contracts — abletonBridge

## Convenciones
- El "contrato" principal es el protocolo entre el servidor MCP y el Remote Script (comandos sobre socket TCP local) + las tools MCP expuestas a Claude. Se documentará acá al definir el MVP.

## Índice
| Comando / Tool | Dirección | Estado | Últ. cambio |
|----------------|-----------|--------|-------------|
| Protocolo socket TCP (envelope JSON) | MCP ⇄ RemoteScript | Definido (T-001) | 2026-06-22 |
| `live.transport` (play/stop/set_tempo) | MCP → RS | Definido (T-001) | 2026-06-22 |
| `live.create_midi_track` | MCP → RS | Definido (T-001) | 2026-06-22 |
| `live.create_midi_clip` | MCP → RS | Definido (T-001) | 2026-06-22 |
| `live.insert_notes` | MCP → RS | Definido (T-001) | 2026-06-22 |
| `live.get_state` | MCP → RS | Definido (T-001) | 2026-06-22 |

---

## A. Protocolo del puente — socket TCP local (MCP ⇄ Remote Script)

### Transporte
- **Tipo:** TCP, `127.0.0.1` (loopback únicamente; nunca bind a `0.0.0.0`).
- **Puerto:** `19845` por defecto (configurable en la UI/config local). Rango sugerido
  para fallback automático si ocupado: `19845–19855`. El servidor (lado Remote Script)
  escribe el puerto efectivo en el archivo de config para que el MCP lo descubra.
- **Rol:** el **Remote Script es el servidor** (escucha; vive con Live). El **servidor MCP
  es el cliente** (conecta; puede reconectar si Live reinicia).
- **Concurrencia:** el Remote Script atiende una conexión MCP a la vez. Las operaciones
  sobre el LOM se ejecutan en el **hilo de la UI de Live** (ver §C, nota de threading).

### Framing
Mensajes JSON UTF-8 delimitados por **newline** (`\n`) — *newline-delimited JSON*.
Un mensaje = una línea = un objeto JSON. Sin saltos de línea internos (JSON compacto).

### Envelope — Request (MCP → RS)
```json
{ "id": "uuid-v4", "cmd": "transport.play", "params": { } }
```
| Campo | Tipo | Req | Descripción |
|-------|------|-----|-------------|
| `id` | string | sí | UUID v4. Correlaciona request↔response. |
| `cmd` | string | sí | Comando namespaced (`transport.play`, `track.create_midi`, …). |
| `params` | object | sí | Parámetros del comando (`{}` si no aplica). |

### Envelope — Response (RS → MCP)
```json
{ "id": "uuid-v4", "ok": true,  "result": { } }
{ "id": "uuid-v4", "ok": false, "error": { "code": "TRACK_NOT_FOUND", "message": "…" } }
```
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | string | Mismo `id` del request (correlación). |
| `ok` | bool | `true` = éxito; `false` = error de dominio. |
| `result` | object | Payload en éxito (presente solo si `ok=true`). |
| `error` | object | `{ code, message }` en fallo (presente solo si `ok=false`). |

### Correlación y timeouts
- **Correlación:** por `id` (UUID). El MCP mantiene un mapa `id → future`; las respuestas
  pueden volver fuera de orden. El RS SIEMPRE devuelve el `id` recibido.
- **Timeout de request (MCP):** 5 s por defecto por comando. Al vencer → el MCP resuelve
  la tool con error `BRIDGE_TIMEOUT` y descarta la entrada del mapa.
- **Handshake/keepalive:** comando `ping` → `{ "ok": true, "result": { "pong": true,
  "live_version": "12.0.5", "api_level": 12 } }`. El MCP hace `ping` al conectar para
  resolver la versión de Live y elegir adaptadores (ver §C).
- **Reconexión:** si la conexión cae (Live cerrado/reiniciado), el MCP reintenta con
  backoff (1s, 2s, 4s, máx 4s) y re-emite `ping` al reconectar.

### Códigos de error (catálogo base)
| `code` | Capa | Significado |
|--------|------|-------------|
| `BRIDGE_TIMEOUT` | MCP | El RS no respondió dentro del timeout. |
| `BRIDGE_DISCONNECTED` | MCP | No hay conexión con el Remote Script (Live cerrado). |
| `BAD_REQUEST` | RS | JSON inválido o falta `cmd`/`id`/`params`. |
| `UNKNOWN_CMD` | RS | `cmd` no reconocido. |
| `INVALID_PARAMS` | RS | Tipos/rangos de `params` inválidos. |
| `TRACK_NOT_FOUND` | RS | Índice de track inexistente. |
| `CLIP_SLOT_NOT_FOUND` | RS | (track, slot) inexistente. |
| `CLIP_NOT_FOUND` | RS | No hay clip en el slot indicado. |
| `SLOT_OCCUPIED` | RS | Ya existe un clip en el slot al crear. |
| `NOT_MIDI_TRACK` | RS | La operación requiere un track MIDI. |
| `LOM_ERROR` | RS | Excepción del Live API al ejecutar (mensaje en `message`). |

---

## B. Superficie de tools MCP (Claude → MCP → RS) — F-001..F-005

> Convención: la tool MCP valida params, traduce a un `cmd` del socket, espera la
> response correlacionada y devuelve `result` (o levanta el error). Tipos en notación
> simple (`int`, `float`, `str`, `bool`).

### F-001 · Transporte

**`live_play`** — inicia la reproducción del set.
- Params: `{}`
- Retorno: `{ "is_playing": true }`
- Errores: `BRIDGE_TIMEOUT`, `BRIDGE_DISCONNECTED`, `LOM_ERROR`
- → `cmd: "transport.play"` · LOM: `song.start_playing()` / `song.is_playing = True`

**`live_stop`** — detiene la reproducción.
- Params: `{}`
- Retorno: `{ "is_playing": false }`
- Errores: idem F-001
- → `cmd: "transport.stop"` · LOM: `song.stop_playing()`

**`live_set_tempo`** — fija el tempo del set.
- Params: `{ "bpm": float }` — rango válido Live: `20.0–999.0`
- Retorno: `{ "tempo": float }`
- Errores: `INVALID_PARAMS` (fuera de rango), `LOM_ERROR`, transporte
- → `cmd: "transport.set_tempo"` · LOM: `song.tempo = bpm`

### F-002 · Crear track MIDI

**`live_create_midi_track`** — crea un track MIDI y lo nombra.
- Params: `{ "name": str (opcional), "index": int (opcional, -1 = al final) }`
- Retorno: `{ "track_index": int, "name": str }`
- Errores: `INVALID_PARAMS` (index fuera de rango), `LOM_ERROR`, transporte
- → `cmd: "track.create_midi"` · LOM: `song.create_midi_track(index)`; luego
  `song.tracks[i].name = name` si se pasó nombre. `track_index` es la posición real
  resultante (a devolver tras crear, no asumir).

### F-003 · Crear clip MIDI

**`live_create_midi_clip`** — crea un clip MIDI vacío en (track, slot).
- Params: `{ "track_index": int, "slot_index": int, "length_beats": float }`
  (`length_beats` = longitud en *beats*; p.ej. 4.0 = 1 compás en 4/4)
- Retorno: `{ "track_index": int, "slot_index": int, "length_beats": float }`
- Errores: `TRACK_NOT_FOUND`, `CLIP_SLOT_NOT_FOUND`, `SLOT_OCCUPIED`,
  `NOT_MIDI_TRACK`, `INVALID_PARAMS`, `LOM_ERROR`
- → `cmd: "clip.create_midi"` · LOM: `clip_slot.create_clip(length_beats)` sobre
  `song.tracks[t].clip_slots[s]`. Si `clip_slot.has_clip` → `SLOT_OCCUPIED`.

### F-004 · Insertar notas en un clip

**`live_insert_notes`** — inserta notas (acordes/stabs/progresiones) en un clip existente.
- Params:
  ```json
  { "track_index": int, "slot_index": int,
    "notes": [ { "pitch": int, "start": float, "duration": float,
                 "velocity": int, "mute": bool } ] }
  ```
  - `pitch` 0–127 · `start`/`duration` en beats (≥0, >0) · `velocity` 1–127 ·
    `mute` opcional (default false). Acordes = varias notas con el mismo `start`.
- Retorno: `{ "inserted": int }` (cantidad de notas agregadas)
- Errores: `CLIP_NOT_FOUND`, `TRACK_NOT_FOUND`, `INVALID_PARAMS`, `LOM_ERROR`
- → `cmd: "clip.insert_notes"` · LOM: ver nota Live 11 vs 12 en §C (API de notas
  cambió). El RS encapsula ambas variantes; el contrato MCP es estable.

### F-005 · Leer estado del set

**`live_get_state`** — snapshot del set (tempo, tracks, clips).
- Params: `{ "include_clips": bool (opcional, default true) }`
- Retorno:
  ```json
  { "tempo": float, "is_playing": bool, "live_version": str,
    "tracks": [ { "index": int, "name": str, "is_midi": bool,
      "clips": [ { "slot_index": int, "name": str,
                   "length_beats": float, "is_midi": bool } ] } ] }
  ```
- Errores: `BRIDGE_TIMEOUT`, `BRIDGE_DISCONNECTED`, `LOM_ERROR`
- → `cmd: "state.get"` · LOM: itera `song.tracks[*]` y `clip_slots[*]`.

### Lectura completa · `state.detail` (T-008)

**`live_get_state_detail`** — lectura estructural completa del set, ESTRICTAMENTE de solo lectura (nunca asigna nada del LOM). Permite a Claude "escuchar" leyendo: tracks, grupos, mixer, devices+parametros, clips (Session y Arrangement), returns, master, locators.
- Params: `{ "tracks": [int] (opcional, default todos; indices fuera de rango se ignoran, salen ordenados),
  "params": "changed" (default) | "all" | "none", "include_arrangement": bool (true), "include_session": bool (true) }`
  - `changed`: solo parametros con `value != default_value` (los ilegibles se incluyen); "Device On" solo si el device esta apagado. `none`: sin clave `parameters`.
  - `params` invalido o `tracks` no-lista de enteros => `LOM_ERROR` (ValueError).
- Valores de parametros: RAW (0..1 en la mayoria) + `display` = `str_for_value(value)`; las unidades solo salen de `display`. Los nombres son los de la API, no los de la UI (ej. Utility gain = "Output"; `class_name` Compressor2, StereoGain, Eq8).
- Retorno:
  ```json
  { "song": { "tempo", "signature_numerator", "signature_denominator", "song_length",
              "current_song_time", "is_playing", "loop": {"on","start","length"},
              "cue_points": [{"name","time"}], "root_note", "scale_name" },
    "tracks": [ { "index", "name", "kind": "audio|midi|group", "is_foldable", "is_grouped",
                  "group_name"?, "color_index", "mute", "solo", "arm", "output_routing",
                  "mixer": { "volume": {"value","display"}, "panning": {...}, "sends": [{...}] },
                  "devices": [ DEVICE ],
                  "session_clips": [ {"slot", "name", "length", "is_audio", ...CLIP} ],
                  "arrangement_clips": [ {"start_time","end_time","name","length","is_audio", ...CLIP} ] } ],
    "returns": [ { "index", "name", "kind": "return", "mute", "solo", "mixer", "devices" } ],
    "master":  { "name", "mixer": {"volume","panning"}, "devices" } }
  ```
  - `CLIP` audio: `file_path, warping, warp_mode, pitch_coarse, pitch_fine, gain, gain_display (gain_display_string), looping, loop_start, loop_end, start_marker, end_marker`. MIDI: `note_count` (len de `get_all_notes_extended`), `looping, loop_start, loop_end, start_marker, end_marker`.
  - `DEVICE`: `{ class_name, name, type?, is_active, parameters?: [{name, value, display, min, max, is_quantized}], chains?: [{name, mute, solo, in_note? (Drum Rack), devices: [DEVICE]}], chains_truncated? }`. Chains recursivas hasta profundidad 3 (mas alla: `chains_truncated: true`).
- Todo campo ilegible = `"unavailable: <ExcType>"` (ej. `arm` en un grupo); nunca aborta la lectura completa.
- Guard de tamano (en la tool MCP): si el JSON supera 60.000 caracteres se escribe a `<repo>/.cache/state_detail/state_detail_<timestamp>.json` y se devuelve `{ "truncated": true, "file": <ruta absoluta>, "summary": { "tracks": [{index,name,kind,devices:[nombres]}], "returns": [...], "master_devices": [...] } }`.
- Errores: `BRIDGE_TIMEOUT`, `BRIDGE_DISCONNECTED`, `LOM_ERROR`
- → `cmd: "state.detail"` (hilo principal via dispatcher).
- VERIFICAR EN LIVE: `Song.root_note/scale_name` (Live 11+), `Clip.gain_display_string`, `Clip.get_all_notes_extended` (len), `DrumChain.in_note`, `Track.output_routing_type.display_name`, `Track.color_index`, `Device.type`, `return_tracks[*].mixer_device.sends` (puede estar vacio), `master_track.mixer_device` sin sends, `Track.group_track.name`.

### Diagnóstico · `probe_api` (T-002b)

**`live_probe_api`** — informa qué miembros del LOM existen en la versión de Live conectada.
- Params: `{}`
- Retorno: `{ "live_version": str, "members": { "<Clase>.<miembro>": true | false | "class_missing" } }`
  (`"class_missing"` = la clase `Live.<Mod>.<Clase>` no existe; se usa `hasattr` sobre la clase)
- Miembros inspeccionados: Song (create_audio_track, create_midi_track, create_return_track,
  set_or_delete_cue) · Track (create_audio_clip, create_midi_clip, insert_device,
  duplicate_clip_to_arrangement, delete_clip, arrangement_clips) · ClipSlot (create_audio_clip) ·
  Clip (automation_envelope, create_automation_envelope, add_warp_marker, move_warp_marker,
  remove_warp_marker, crop, add_new_notes, get_notes_extended) · SimplerDevice (replace_sample) ·
  RackDevice (insert_chain) · Application (browser) · Browser (load_item).
- Errores: `BRIDGE_TIMEOUT`, `BRIDGE_DISCONNECTED`, `LOM_ERROR`
- → `cmd: "probe.api"` (convención de `cmd` con punto, como `state.get`).

---

## C. Compatibilidad Live 11 vs Live 12 (Live API)

Ambas corren Python 3 (cubierto por RN-001). Diferencias a encapsular en el Remote
Script (la superficie MCP de §B NO cambia entre versiones):

1. **Inserción de notas (impacta F-004 — crítico):**
   - **Live 11:** `clip.set_notes(tuple_of_notes)` / `clip.get_notes(...)`, donde cada
     nota es la tupla `(pitch, start, duration, velocity, mute)`.
   - **Live 12:** API moderna `clip.add_new_notes(Live.Clip.MidiNoteSpecification(...))`
     y `clip.get_notes_extended(...)` con objetos en vez de tuplas (la vieja sigue
     presente pero deprecada).
   - **Decisión:** el RS detecta `api_level` (via `ping`) y usa un adaptador
     `NotesCodec` por versión. Recomendado preferir la API extendida en 12.
2. **`ping`/handshake** devuelve `live_version` y `api_level` (11 ó 12) → el MCP y el RS
   eligen el adaptador correcto al conectar. NO inferir versión por otros medios.
3. **El resto (transporte, create_midi_track, create_clip, iteración de tracks/slots)**
   es estable entre 11 y 12 → sin adaptador.

> Regla NERV: cualquier cambio futuro en esta superficie pasa por el Arquitecto como
> árbitro de contratos (P-4). Backend/Desktop implementan contra §A/§B, no al revés.

---

---

## Spikes (temporales) — T-002c, automatización en Arrangement

Solo investigación; se eliminan tras el spike. Código fijo (sin exec/eval), params simples.
Solo tocan pistas `SPIKE-*`. Cada paso va en try/except y se reporta como `{"ok": bool, "error": str|None}`.

**`live_spike_automation_session`** → `cmd: spike.automation_session` · params `{ bars: int=4 (1..64) }`
Crea pista MIDI `SPIKE-AUTO-SESSION` (Operator + Auto Filter), clip de bars*4 beats con notas (pitch 36,
una por beat), envolventes de clip para volumen y Auto Filter "Freq*", rampa con `insert_step`, y
`duplicate_clip_to_arrangement(clip, 0.0)`.
Retorno: `{ track_index, devices_loaded[], autofilter_param_names[], envelopes_created{volume,filter_freq},
session_envelope_readback{<k>:[{time,value}x3]}, arrangement_clips[{start_time,end_time}],
arrangement_envelope{<k>:{present, samples?}}, automation_state{<k>:int}, steps{<paso>:{ok,error}} }`
Pasos: create_track, insert_devices, create_clip, add_notes, envelope_volume, envelope_filter_freq,
duplicate_to_arrangement, read_arrangement, read_automation_state.

**`live_spike_automation_record_start`** → `cmd: spike.automation_record_start` · params `{ start_beat: float=32.0, bars: int=2 }`
Crea `SPIKE-AUTO-RECORD` (Operator, sin armar), `current_song_time=start_beat`, `record_mode=True`,
`start_playing()`; luego `_tick` rampa volumen y el primer parámetro de Operator distinto de "Device On".
Retorno inmediato: `{ started: bool, track_index, operator_param, steps{}, report{session_automation_record,
arrangement_overdub, re_enable_automation_enabled} }` (o `{started:false,error}` si ya corre).

**`live_spike_automation_record_status`** → `cmd: spike.automation_record_status` · params `{}`
Retorno: `{ phase: idle|running|done|error, steps_applied, errors[], automation_state{volume,operator_param},
operator_param, arrangement_clips[] }` (los 3 últimos tras start). Timeout de seguridad: 2x duración + 10 s.

**`live_spike_cleanup`** → `cmd: spike.cleanup` · params `{}`
Frena la máquina, `record_mode=False`, `stop_playing`, borra pistas `SPIKE-*` en reversa.
Retorno: `{ deleted[], errors[] }`.

VERIFICAR EN LIVE: forma de `Live.Clip.MidiNoteSpecification(pitch,start_time,duration,velocity)` y
`add_new_notes(tuple)`; `insert_device("Operator"/"Auto Filter", idx)` (nombres y que no falle); nombres
de parámetros de Auto Filter (se reportan); `song.record_mode` como arm de automation en Arrangement;
`song.re_enable_automation_enabled`/`arrangement_overdub`/`session_automation_record` (solo lectura).

### Ronda 2 — T-002d (arm, audio, devices, Simpler)

Mismas reglas (código fijo, solo `SPIKE-*`, pasos `{ok,error}`, `spike.cleanup` borra también estas pistas).
Paths de audio: absolutos, existentes, extensión `.wav/.aif/.aiff/.mp3/.flac`; si no, `{ok:false, error:"invalid path"}` sin tocar Live.

**`live_spike_automation_arm`** → `spike.automation_arm` · `{ enable: bool=true }`
Setea `song.session_automation_record`. Retorno: `{ ok, error, before, after }`.

**`live_spike_automation_record_start`** ahora acepta `arm: bool=true`: prende `session_automation_record` antes de grabar
y lo restaura al valor previo al terminar (done/error) o en `spike.cleanup`. Paso nuevo en `steps`: `arm`.

**`live_spike_audio_clip`** → `spike.audio_clip` · `{ path, position_beats: float=0.0 }`
Pista de audio `SPIKE-AUDIO`; `create_audio_clip(path, pos)` en `pos` (base), `pos+16` (chop 1 beat:
loop_start/end y start/end_marker 1.0→2.0, `looping=True`) y `pos+20` (`warp_mode=6` Complex Pro, `pitch_coarse=-2`).
Retorno: `{ ok, track_index, complex_pro_mode_value, clips{base,chop,complex}:{is_audio_clip,file_path,length,start_time,end_time,
warping,warp_mode,warp_markers[{beat_time,sample_time}],start_marker,end_marker,loop_start,loop_end,looping,gain,pitch_coarse}, steps }`.
Un campo ilegible se reporta como `"unavailable: <Error>"`.

**`live_spike_devices`** → `spike.devices` · `{}`
Pista de audio `SPIKE-DEVICES` con EQ Eight, Saturator, Compressor, Drum Buss, Utility (en ese orden) y luego Drum Rack.
Retorno: `{ ok, track_index, devices[{class_name,name,parameters[{name,original_name?,min,max,default_value?(solo no cuantizados),
is_quantized,value_items?(cuantizados),value,str_for_value}]}], set_params{"Saturator.Drive":{target,value,str_for_value},
"Utility.Gain":{...}}, drum_rack{ok,error,class_name?}, steps }`.

**`live_spike_simpler_slice`** → `spike.simpler_slice` · `{ loop_path, oneshot_path }`
`SPIKE-SIMPLER-SLICE`: Simpler + `replace_sample(loop)`, `playback_mode=2`, lectura del sample, `clear_slices` + 4 `insert_slice`
equiespaciadas (frames), clip MIDI de 4 beats con notas 36..39. `SPIKE-SIMPLER-ONESHOT`: Simpler + `replace_sample(oneshot)`,
`playback_mode=1`, clip con pitch 60 x4.
Retorno: `{ ok, slice{track_index,playback_mode_readback,sample{file_path,length,sample_rate,slicing_style,slicing_sensitivity,
slicing_beat_division,slices_count,first_slices[<=16]},slices_after[]}, oneshot{track_index,playback_mode_readback,sample,parameters[]}, steps }`.

VERIFICAR EN LIVE: valores de `warp_mode` (6 = Complex Pro) y `playback_mode` (0/1/2); forma de `warp_markers`; que
`create_audio_clip` devuelva el Clip; orden/validez al setear loop/markers y `looping` en clip de Arrangement; `insert_device`
devuelve Device; `original_name`/`value_items`/`str_for_value`; `Sample.sample_rate`, `slicing_*`, `slices`; `clear_slices`
+ `insert_slice` en frame 0; notas 36..39 disparan slices y 60 es la raíz del one-shot; `insert_device("Drum Rack")`.

---

## Producción v1 (T-003) — comandos permanentes

Todos corren en el hilo principal (dispatcher), con params tipados (sin exec/eval). Errores de validación con código propio (`errors.CommandError`): `INVALID_PARAMS`, `TRACK_NOT_FOUND`, `NOT_MIDI_TRACK`; fallas de la API de Live => `LOM_ERROR`. Los comandos multi-paso devuelven `steps: {nombre: {ok, error}}` y `warnings` en vez de abortar. `track` = índice 0-based (se invalida al crear/borrar tracks). `device` = índice en `track.devices` o nombre exacto. Valores de parámetros RAW; la unidad solo sale de `display` (`str_for_value`).

| cmd (tool MCP) | Params | Respuesta |
|---|---|---|
| `song.set` (`live_song_set`) | `tempo?` (20..999), `signature_numerator?` (1..99), `signature_denominator?` (1,2,4,8,16), `loop_start?` (>=0), `loop_length?` (>0), `loop_on?` (bool) | readback `{tempo, signature_numerator, signature_denominator, loop_start, loop_length, loop_on}` |
| `track.create` (`live_track_create`) | `kind` "audio"\|"midi", `name`, `index=-1` (append; 0..len) | `{index, name}` |
| `track.set_mixer` (`live_track_set_mixer`) | `track`, `volume_db?` (número o "-inf"), `pan?` (-1..1), `mute?`, `solo?` | `{track, volume?:{value, display, within_tolerance}, panning?:{value, display}, mute?, solo?}` solo las claves pedidas |
| `track.delete` (`live_track_delete`) | `track`, `confirm_name` (== nombre actual, exacto) | `{deleted, index, track_count}` |
| `clip.place_audio` (`live_clip_place_audio`) | `track` (audio), `path` (absoluto, existente, .wav/.aif/.aiff/.mp3/.flac), `start_beat` (>=0), `length_beats` (>0; opcional solo con `one_shot`), `warp_mode?` (0,1,2,3,4,6), `pitch_coarse?` (-48..48), `gain_db?`, `loop_start?`+`loop_end?` (juntos; sección del archivo), `one_shot?` (bool, default false; sin warp, 1 sola copia, incompatible con loop_*) | `{ok, track, clips:[{start_time,end_time,span,length,warp_mode,warping,pitch_coarse,method:"create_audio_clip"\|"session_duplicate"}], covered_beats, sample_beats? (solo one_shot), gain?:{applied,value,display,within_tolerance,error?}, warnings:[str], steps}` |
| `clip.delete_range` (`live_clip_delete_range`) | `track`, `start_beat` (>=0), `end_beat` (> start) | `{track, deleted:[{start_time,end_time}], count, warnings}`. Borra (`Track.delete_clip`) los clips de Arrangement contenidos POR COMPLETO en el rango; los que cruzan el borde no se tocan |
| `clip.create_midi` (`live_clip_create_midi`) | `track` (MIDI), `start_beat`, `length_beats`, `notes:[{pitch 0..127, start>=0, duration>0, velocity 1..127}]` (puede ser `[]`) | `{track, start_time, end_time, length, name, note_count}` |
| `device.insert` (`live_device_insert`) | `track`, `name` (nativo, p.ej. "Saturator"), `index=-1` | `{index, class_name, name}` |
| `device.set_param` (`live_device_set_param`) | `track`, `device`, `name` (exacto, sensible a mayúsculas, nombre de API), `value` (raw dentro de [min,max]) | `{device, name, min, max, value, display}` |
| `simpler.load` (`live_simpler_load`) | `track`, `device` (un Simpler), `path`, `playback_mode?` (0 Classic, 1 One-Shot, 2 Slicing) | `{ok, device, file_path, playback_mode, steps}` |
| `locator.set` (`live_locator_set`, wrapper de 1 item) | `time` (>=0), `name` | `{queued:true, id}` (ASÍNCRONO) |
| `locator.set_many` (`live_locator_set_many`) | `items:[{time>=0, name}]` (1..256; se valida todo antes de encolar) | `{queued:true, id, count}` |
| `locator.status` (`live_locator_status`) | — | `{pending, done:[{name,time}], errors:[{name,time,error}], id, cue_points:[{name,time}]}` |
| `locator.clear_all` (`live_locator_clear_all`) | — | `{queued, id, count}` (ASÍNCRONO; `queued:false` si no hay cues) |
| `track.set_send` (`live_track_set_send`) | `track`, `send` (índice int en `mixer_device.sends`), `db` (número o "-inf") | `{value, display, within_tolerance}`. `INVALID_PARAMS` si `send` fuera de rango o `db` ausente/inválido; `TRACK_NOT_FOUND` |
| `return.list` (`live_return_list`) | — | `{returns:[{index, name, devices:[nombres], volume:{value, display}}], count}` (envuelto en dict: el cliente convierte `[]` en `{}`) |
| `return.set_mixer` (`live_return_set_mixer`) | `return` (índice), `volume_db?`, `pan?`, `mute?` (sin `solo`: `INVALID_PARAMS`) | igual que `track.set_mixer` pero con `return` en vez de `track`. `TRACK_NOT_FOUND` si el return no existe |
| `return.device_insert` (`live_return_device_insert`) | `return`, `name`, `index=-1` | `{index, class_name, name}` |
| `return.device_set_param` (`live_return_device_set_param`) | `return`, `device`, `name`, `value` | `{device, name, min, max, value, display}` |
| `return.create` (`live_return_create`) | `name?` | `{index, name}` (llama `song.create_return_track()` sin args y renombra si hay `name`) |

Semántica:
- `track.set_send` / `return.set_mixer.volume_db`: misma bisección que `track.set_mixer.volume_db` (helper compartido `_set_db`), sobre `mixer_device.sends[send]` / `volume`.
- `track.set_mixer.volume_db`: bisección sobre `[min,max]` de `mixer_device.volume` contra `str_for_value` (monótono), tolerancia 0.1 dB. Si el objetivo no es alcanzable (p.ej. +30 dB) deja el valor más cercano y `within_tolerance: false`. `"-inf"` => `min`.
- `clip.place_audio` (T-003b, reemplaza el camino crop()): en Live 12.4.16 los markers y `Clip.crop()` NO acortan un clip de Arrangement (y tras crop la referencia Python queda invalida). Cada tile: (a) se crea con `Track.create_audio_clip`; si su span natural (`end_time-start_time`) entra en lo que falta queda así (`method:create_audio_clip`); (b) si pasaría del final, o si hay `loop_start/loop_end`, se arma en un slot de Session scratch del mismo track (primer slot sin clip; si no hay, `song.create_scene(-1)` y se borra la escena al final): `slot.create_audio_clip(path)`, warp/pitch/gain, loop_start/loop_end y markers = largo requerido, `looping=True`, `track.duplicate_clip_to_arrangement(clip, pos)` (el span = largo de loop del clip de Session), `slot.delete_clip()` (`method:session_duplicate`). El clip de Arrangement SIEMPRE se re-busca en `track.arrangement_clips` por `start_time` (nunca se usa una referencia previa). Se verifica `span == largo requerido` (tol 0.01); si no, `ok:false` + warning con el span real. `one_shot:true`: `warping=False`, una sola copia en `start_beat` sin recorte; `length_beats` solo se usa para avisar si el clip real es más largo; `covered_beats` = span real; `sample_beats` = `sample_length/sample_rate*tempo/60` si Live lo expone. Tope 512 copias. `gain_db` busca el crudo por bisección sobre `Clip.gain` leyendo `gain_display_string` (1.ª copia; las demás reusan); si no se puede, `gain.applied:false` + warning y el resto sigue.
- Locators (ASÍNCRONOS, maquina de estados avanzada desde `surface._tick`): Live aplica `current_song_time` en un tick posterior, por eso setear el playhead y llamar `set_or_delete_cue` en la misma llamada crea el cue en la posicion VIEJA (bug real en 12.4.16). Por item: fase `moving` (setea el playhead y espera a que `current_song_time` ≈ target, tolerancia 0.01, timeout 2 s) -> `set_or_delete_cue` solo si corresponde (crear si no hay cue; borrar si hay) -> `verify` en el tick siguiente (renombra / confirma borrado). Al vaciar la cola se restaura el playhead. Un item que falla/timeout va a `errors` y la cola sigue. `status` se limpia al encolar un lote con la cola ociosa. `locator.clear_all` usa el mismo mecanismo (operacion delete por cue). Flujo MCP: `live_locator_set_many` -> pollear `live_locator_status` hasta `pending == 0`.
- `track.delete` exige `confirm_name` igual al nombre actual (guarda contra índices viejos).

VERIFICAR EN LIVE: (1) `Track.create_midi_clip(start_time, length)` orden de args y que devuelva el Clip; (2) tiling: `clip.length` tras `create_audio_clip` en beats y copias contiguas sin solaparse; (3) trim: que `Clip.crop()` tras setear `end_marker`/`loop_end` deje `end_time - start_time` == length_beats (e.g. loop de 32 en beat 48 con length 16 => end_time 64) y que con looping on no siga sonando hasta el largo natural; (4) `gain_db`: `Clip.gain` 0..1 + `gain_display_string` actualizado tras asignar; (5) locators async: `current_song_time` converge en 1-2 ticks, el cue aparece en el tick siguiente a `set_or_delete_cue`, `cue_points[*].name` es escribible y el borrado (clear_all) funciona con el playhead sobre el cue; (6) `song.loop` (on/off), `loop_start`, `loop_length` escribibles; (7) `insert_device(name, index)` con `index` = len(devices); (8) `Song.delete_track(index)`; (9) `volume.str_for_value` devuelve "x dB" parseable (y "-inf dB" en el mínimo); (10) `Device.name` coincide con el nombre pedido en `device`-por-nombre; (11) `loop_start/loop_end` + markers en `place_audio` dan `length = loop_end-loop_start`.

VERIFICAR EN LIVE (T-009): (1) `song.create_return_track()` sin args y el nuevo return queda al final de `return_tracks`; (2) `mixer_device.sends[i].str_for_value` devuelve "x dB" parseable ("-inf dB" en el mínimo) y es monótono; rango/`max` del send (¿+6 dB?); (3) `insert_device` sobre un `Track` de `return_tracks` (mismo API que en tracks); (4) `return_tracks[i].mute` y `mixer_device.panning` escribibles; (5) `Device.name` de returns por defecto ("Reverb", "Delay").

VERIFICAR EN LIVE (T-003b): (1) `ClipSlot.create_audio_clip(path)` en un slot vacío de track de audio y que `slot.clip` quede válido; (2) con `loop_end`/`end_marker` menores al natural en el clip de Session (orden de seteo, `looping=True`), `duplicate_clip_to_arrangement` da span == largo de loop y conserva warp/pitch/gain/envelopes; (3) `song.create_scene(-1)` agrega al final y `song.delete_scene(idx)` limpia (tracks sin slot libre); (4) `Track.delete_clip(clip)` sobre clips de Arrangement (descarte del tile natural y `clip.delete_range`); (5) one_shot: `warping=False` en Arrangement, `end_time` resultante, y si `Clip.sample_length` (muestras) / `sample_rate` existen (`sample_beats`); si el span real de un riser difiere del esperado, el trim de one-shots (markers en segundos con warping off) queda pendiente; (6) `track.arrangement_clips` refleja los clips nuevos en el mismo tick (re-búsqueda por start_time inmediata).


## Automatización por envelopes, master y sidechain (T-010)

Base: hallazgo spike 1 (docs/nexo/hallazgos/F1_control_de_live.md): los envelopes de clip escritos en un clip de SESSION sobreviven a `duplicate_clip_to_arrangement` y suenan en Arrangement; `Clip.automation_envelope()` devuelve None en clips de Arrangement, así que NO se pueden releer ahí (el reporte es lo escrito, no una lectura).

### `envelopes` en `clip.place_audio` y `clip.create_midi`

Params nuevos (opcionales): `envelopes: [{target, points}]` (1..16) y `points_span: "tile"` (default) `| "range"`.

- `target`: `"volume"` | `"pan"` | `{"send": i}` | `{"device": index|nombre, "param": nombre exacto de API}` (del mismo track).
- `points`: `[[t_beats, valor], ...]` (1..256, `t` >= 0 estrictamente creciente). `valor` = número RAW dentro de [min,max] del parámetro, o `{"display": n}` = número en la unidad del `str_for_value` (dB, Hz, %, ms). Se resuelve por bisección una sola vez por valor (ver "Valores por unidad").
- `points_span "tile"`: `t` es relativo al inicio de CADA tile (la curva se repite en cada tile). `"range"`: `t` es relativo a `start_beat` del pedido completo; cada tile recibe su tajada (barrido de 16 compases a través de varios tiles). Fuera de los puntos se sostiene el primer/último valor.
- Escritura: con envelopes TODO tile pasa por el slot de Session (`method:"session_duplicate"`, también en tiles que entrarían enteros). `clip.create_midi` arma el clip en un slot scratch con `ClipSlot.create_clip(length)`, agrega notas, envelopes, `duplicate_clip_to_arrangement`, y borra el scratch. Cada envelope: `clip.create_automation_envelope(param)` + `insert_step(t, dur, valor)` cada 0.25 beat (dur 0.25; el último paso se acorta al borde), valor = poligonal interpolada en `t` (muestreada al inicio del paso), en espacio RAW (entre dos puntos `display` interpola lineal en raw, no en dB/Hz).
- Todo se valida antes de tocar el set (`INVALID_PARAMS`). Incompatible con `one_shot`.
- Respuesta: cada clip de `place_audio` suma `envelopes:[{target, param, ok, steps, error?}]`; `create_midi` devuelve además `{method:"session_duplicate", ok, envelopes, warnings, steps}`. Un envelope que falla: `ok:false` en su entrada + warning + `ok:false` global, el clip igual queda colocado y los demás envelopes siguen. `warnings` incluye los `display` inalcanzables (se usa el más cercano).

### Valores por unidad (`display`)

`_raw_for_display(param, n)`: bisección sobre [min,max] contra `str_for_value`, 48 iteraciones, display monótono creciente O decreciente. El número se toma del texto con normalización `kHz`→Hz y `s`→ms; displays no numéricos (`1/4`, nombres) => `INVALID_PARAMS`. `within_tolerance` = |obtenido − pedido| <= 0.5 % del rango de display (o 0.1 dB si el rango incluye -inf). Aplica a `device.set_param`, `return.device_set_param`, `master.device_set_param` (`display` en vez de `value`, exactamente uno; la respuesta agrega `within_tolerance` solo en ese caso; `display` de la respuesta sigue siendo el string) y a los puntos `{"display": n}`.

### Master y sidechain

| cmd (tool MCP) | Params | Respuesta |
|---|---|---|
| `master.device_insert` (`live_master_device_insert`) | `name`, `index=-1` | `{index, class_name, name}` |
| `master.device_set_param` (`live_master_device_set_param`) | `device`, `name`, `value` XOR `display` | `{device, name, min, max, value, display, within_tolerance?}` |
| `master.set_mixer` (`live_master_set_mixer`) | `volume_db` (número o "-inf"; requerido) | `{volume:{value, display, within_tolerance}}` |
| `compressor.set_sidechain` (`live_compressor_set_sidechain`) | `track`, `device` (índice o nombre), `source_track_name` | `{ok, track, device, input_routing_type, available_input_routing_types:[nombres], input_routing_channel, available_input_routing_channels:[nombres], sidechain_on, sc_params:[{name, value, display}], warnings, steps}` |

`compressor.set_sidechain`: el device debe exponer `available_input_routing_types` / `input_routing_type` (Compressor en Live 11+); si no => `INVALID_PARAMS` claro. Elige el tipo de ruteo por `display_name` (exacto; si no, sin mayúsculas; si no, sin prefijo "N-"; ambiguo o inexistente => `INVALID_PARAMS` con la lista disponible), lo asigna, y activa el param `"S/C On"` (=max) si existe (si no, warning y `ok:false`). `sc_params` lista TODOS los params cuyo nombre contiene "S/C" (en el spike: S/C Listen, S/C EQ On/Type/Freq/Q/Gain, S/C On, S/C Gain, S/C Mix). El canal de entrada (Post FX / Pre FX) no se toca: solo se reporta.

VERIFICAR EN LIVE (T-010): (1) `ClipSlot.create_clip(length)` en un track MIDI y `duplicate_clip_to_arrangement` de un clip MIDI de Session conserva notas y envelopes; (2) `Clip.create_automation_envelope(param)` en un clip de Session para `mixer_device.volume`, `panning`, `sends[i]` y params de device (¿devuelve el Envelope? ¿falla si ya existe uno?); (3) `insert_step(time, duration, value)` acepta valores en [min,max] y pasos de 0.25 hasta el borde del loop; la rampa suena pareja (el spike 1 mostró un readback irregular 0.85→0.42→0.80: confirmar si era el paso de 1 beat); (4) los tiempos del envelope son relativos al INICIO DEL LOOP del clip (importa con `loop_start` != 0 en `place_audio`); (5) tiles con envelopes en audio: `clip.length` del clip de Session recién creado == largo natural en beats (se usa para decidir el largo del tile); (6) `str_for_value` de los params usados con `display` (Frequency en Hz/kHz, Dry/Wet %, etc.) es numérico y monótono; (7) `Song.master_track.insert_device` y `master_track.mixer_device.volume` (rango/`str_for_value` en dB); (8) Compressor: `available_input_routing_types`/`input_routing_type` existen, `display_name` de un track (¿con prefijo "N-"?), asignar el tipo actualiza `available_input_routing_channels` en el mismo tick, y el parámetro se llama exactamente `S/C On`; (9) con el sidechain activo el ducking se escucha (Compressor en bajo/rumble con fuente kick).
