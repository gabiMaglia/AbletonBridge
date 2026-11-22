# Cheat-sheet de tools `live_*` (servidor MCP `nexo-ableton`)

Fuente de verdad: `engram/04_api_contracts.md`. `track` = indice 0-based (cambia al crear/borrar).
`device` = indice en la cadena o nombre exacto. `display` = numero en la unidad del parametro
(dB, Hz, %, ms); `value` = crudo 0..1. Mandar uno solo de los dos. Resultados > 60k caracteres
se vuelcan a `.cache/mcp_results/` y vuelve `{truncated, file, preview}`.

## Estado y diagnostico
- `live_ping()` handshake.
- `live_get_state(include_clips=true)` snapshot liviano.
- `live_get_state_detail(tracks=[1,2], params="changed", include_arrangement=true)` lectura completa de solo lectura.
- `live_probe_api()` que miembros del LOM existen.

## Song
- `live_song_set(tempo=134, loop_start=0, loop_length=32, loop_on=true)` solo lo enviado cambia.

## Pistas y mezcla
- `live_track_create(kind="audio", name="KICK", index=-1)`
- `live_track_set_mixer(track=2, volume_db=-8, pan=0.1, mute=false)` mezcla ESTATICA; nunca automatizar volume (D-15).
- `live_track_delete(track=5, confirm_name="TOP")`
- `live_track_set_send(track=2, send=0, db=-10)`

## Clips
- Audio: `live_clip_place_audio(track=3, path="G:\\LIbrerias\\2026\\...\\loop.wav", start_beat=64, length_beats=32, warp_mode=0, pitch_coarse=-3, gain_db=-2)`
- One-shot que termina en un compas: `live_clip_place_audio(track=4, path="...riser.wav", start_beat=None, length_beats=None, one_shot=true, end_beat=512)`
- Con movimiento: `envelopes=[{"target":{"device":"Auto Filter","param":"Frequency"},"points":[[0,{"display":300}],[32,{"display":12000}]]}], points_span="range"` (en Arrangement es modulacion).
- MIDI: `live_clip_create_midi(track=1, start_beat=0, length_beats=16, notes=[{"pitch":36,"start":0,"duration":0.25,"velocity":110}])`
- Borrar rango: `live_clip_delete_range(track=3, start_beat=64, end_beat=96)`

## Devices (pista)
- `live_device_insert(track=2, name="Auto Filter")`
- `live_device_set_param(track=2, device="Auto Filter", name="Frequency", display=1200)`
- `live_simpler_load(track=6, device=0, path="...snare.wav", playback_mode=1)` (1 one-shot, 2 slicing)
- `live_compressor_set_sidechain(track=2, device="Compressor", source_track_name="KICK")`
- Nivel automatizable (D-15): `live_utility_ensure_last(track=2)` luego el param `Output`. Tambien `track="master"` o `return_=0`.

## Returns y master
- `live_return_create(name="C-HALL")`, `live_return_list()`
- `live_return_device_insert(return_=2, name="Hybrid Reverb")`
- `live_return_device_set_param(return_=2, device=0, name="<nombre exacto de la API>", display=8000)` (tiempos en ms; nombres en `docs/nexo/catalogo/`)
- `live_return_set_mixer(return_=2, volume_db=-4)`
- `live_master_device_insert(name="Auto Filter")`, `live_master_device_set_param(device=0, name="Frequency", display=900)`
- `live_master_set_mixer(volume_db=-1)`

## Locators (asincronos)
- `live_locator_set_many(items=[{"time":0,"name":"INTRO"},{"time":64,"name":"BUILD"}])` luego `live_locator_status()`
- `live_locator_set(time=128, name="DROP")`, `live_locator_clear_all()`

## Automatizacion real (lane de pista, tiempo real)
- `live_automation_record(start_beat=384, end_beat=512, preroll_beats=4, lanes=[{"track":3,"target":{"device":"Utility","param":"Output"},"points":[[384,{"display":-30}],[416,{"display":0}]]}])`
  `track`: indice | `{"return":i}` | `"master"`. `target`: `"pan"` | `{"send":i}` | `{"device":..,"param":..}`. Bloquea hasta terminar; devuelve el status final.
- `live_automation_status()`, `live_automation_cancel()` (restaura el set), `live_automation_clear(track, target, start_beat, end_beat)` best-effort.

## Bridge
- `live_bridge_version()` version, `loaded_at`, `reload_count`.
- `live_bridge_reload()` recarga el Remote Script sin reiniciar Live (modulos nuevos exigen reiniciar Live una vez).

## Spikes (`live_spike_*`)
Temporales de investigacion; solo se registran con la variable `NEXO_MCP_SPIKES=1`.
