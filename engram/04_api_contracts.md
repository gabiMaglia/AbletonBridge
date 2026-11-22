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
