# Handoff Log — abletonBridge

> Entradas nuevas ARRIBA. Máx. 6 líneas por entrada. Al superar 30 entradas,
> el Orquestador mueve las más viejas a ~/.nerv/archive/abletonBridge-handoffs-[fecha].md
> OJO: las entradas del 2026-11-22 quedaron ABAJO (violando la regla). Se dejan como están; desde 2026-11-24 vuelven arriba.

### 2026-11-24 nerv-desktop->nerv-orquestador T-024 (retorno)
- estado: En revision QA. `run_blocking` ahora cancela el job que vence SIN empezar (error `DISPATCH_TIMEOUT` "no se ejecuto: Live no atendio la cola en N s", nunca corre despues) y espera al que YA empezo (tope duro 120 s). Timeout por comando: lecturas 4 s, pesadas 25 s (< 5 s / 30 s del cliente; test de invariante importa ambos mapas).
- archivos: remote_script/AbletonBridge/{dispatcher,errors,server,runtime}.py; mcp_server/.../{server,stdio_server}.py (tool `live_bridge_stats`, idempotente); tests/test_remote_script/test_dispatch_timeouts.py (+14), test_dispatcher.py, test_bridge_tools.py; contrato 04 + SKILL.md.
- instrumentacion DT-09: nuevo cmd `bridge.stats` -> por cmd {count, cancelled, ultimos 10 {wait_ms, run_ms}} + timeouts vigentes.
- TDD: 14 tests rojos antes; suite 576 passed (antes 562). Sin modulo nuevo: `bridge.reload` alcanza (surface/reloader intactos), NO hace falta reiniciar Live; si el reload esta ya cargado con codigo previo, el primer reload tras desplegar basta. Reiniciar el proceso MCP para ver la tool nueva.
- riesgos: `TimeoutError` ya no sale de run_blocking (ahora CommandError; unico test viejo ajustado). Stats en memoria (se pierden en reload). Sin validar en Live real; el orquestador despliega.

### 2026-11-24 nerv-ai->nerv-orquestador T-023 (retorno)
- estado: En revision QA. Errores del bridge llegan como `ToolError` ("CODE: msg", tambien excepciones inesperadas con tipo); timeout por comando (5 s lecturas, 30 s escrituras pesadas, env NEXO_MCP_TIMEOUT / NEXO_MCP_HEAVY_TIMEOUT); reintento unico solo para lecturas tras conexion caida.
- archivos: mcp_server/abletonbridge_mcp/{client,stdio_server}.py; tests/test_mcp_server/{test_timeouts,test_stdio_server}.py; SKILL.md (Trampas). Protocolo y Remote Script intactos.
- TDD: 20 tests rojos antes; suite 562 passed (antes 543). Escritura con timeout/caida tras enviar: mensaje "pudo haberse ejecutado, relee el estado".
- riesgos: escrituras nunca se reintentan solas (el 1er write tras recrear la superficie sigue fallando, con mensaje claro). Sin validar en Live real. REINICIAR el proceso MCP (/mcp reconnect).
- como probar: `.venv\Scripts\python -m pytest tests/test_mcp_server`; en Live, song.set con loop y place_audio parcial ya no deben dar FAILED.

### 2026-11-24 nerv-desktop->nerv-orquestador T-022 (retorno)
- estado: En revision QA. `_serve_forever` envuelve `_handle_connection` en try/except: un OSError (10053/10054) u otra excepcion de UNA conexion ya no mata el thread de accept. Sin log (live_stderr sin flush); stdlib pura, protocolo intacto.
- archivos: remote_script/AbletonBridge/server.py; tests/test_remote_script/test_server.py (+4 tests con sockets falsos: sendall 10053, recv 10054, no-OSError, after_response intacto).
- TDD: 3 de los 4 tests en rojo antes del fix (el de after_response es guarda de regresion). Suite completa 543 passed (antes 539).
- riesgos: error por conexion se traga en silencio (sin diagnostico). Sin validar en Live real; el orquestador despliega a la User Library.
- como probar: `.venv\Scripts\python -m pytest` (Windows); en Live, abortar un cliente a mitad de respuesta y verificar que live_ping sigue respondiendo.

### 2026-11-24 nerv-orquestador T-018 (saneamiento de engram)
- Backlog reconciliado con el código: alta de T-002b..T-017 (Sprint 2, todos "En revisión QA", columna Live ✅/⚠️/❌), T-003..T-007 originales → "Reemplazado" (filas `-orig`), Sprint 3 nuevo (T-018..T-021), épicas E-001/003/004/005 a "En progreso", DT-01..DT-05.
- Requirements: Q-001 obsoleta (D-10), Q-003 resuelta (D-01+D-16), Q-005 parcial (perfil YAML), Q-006 resuelta (D-14); RN-003 obsoleta. Architecture: stack actualizado, ADR-002 aceptado por D-14 (cuerpo pendiente).
- Hallazgo: play/stop no tienen tool pública (DT-04). No existe rama `main` local ni remota: todo vive en feature/T-002-scaffold.

### 2026-06-22 nerv-desktop→nerv-orquestador T-002 (retorno)
- estado: En revisión QA. Scaffold + handshake `ping` + tool `live_get_state` E2E (vs RS mockeado y BridgeServer real). 39 tests pytest GREEN, TDD respetado. 3 commits en feature/T-002-scaffold, sin push.
- archivos: remote_script/AbletonBridge/{protocol,errors,dispatcher,server}.py; mcp_server/abletonbridge_mcp/{protocol,client,server}.py; tests/*; requirements.txt; README.md; .gitignore.
- riesgos: (1) handshake real Live 11/12 NO probado (sin Ableton) → pasos manuales en README, valida PO. (2) remote_script/ y mcp_server/ paquetes 100% independientes (sin import cruzado) para blindar stdlib-only → proponer como convención. (3) UIDispatcher.run_blocking (cola FIFO en hilo de pump) listo y testeado → T-003+ DEBE usarlo para toda op LOM. (4) Windows: SO_REUSEADDR permite bind duplicado (≠ Linux) → ajustado test de fallback de puerto.
- validación: auto `pytest tests/ -v` → 39 passed; manual = copiar remote_script a User Remote Scripts, activar en Live 11 y 12, verificar live_ping.

### 2026-06-22 nerv-qa→nerv-orquestador T-002 (veredicto)
- APROBADO (Strong, 4 lentes). pytest 39/39. Contrato §A cumplido; UIDispatcher thread-safe correcto; remote_script/ 100% stdlib; socket en 127.0.0.1; tests honestos (no simulan Ableton). T-002 marcado Done por QA.
- GATE abierto: validación manual del handshake en Live real pendiente del PO (no testeable por agentes) → hacerla antes de T-003+.

### 2026-06-22 nerv-orquestador→nerv-qa T-002 (Niv S)
- Encargo: auditar T-002 (Strong: 4 lentes — riesgo, resiliencia, legibilidad, fiabilidad) contra criterios de aceptación y contrato.
- Leer: 03_backlog.md (T-002 + caveats), 04_api_contracts.md (§A,§B,§C), y el código en remote_script/ + mcp_server/ + tests/.
- Foco: adherencia al contrato (envelope, correlación, errores, timeouts), thread-safety (UIDispatcher), calidad de tests. Veredicto Aprobado/Rechazado (defectos numerados si rechazo).

### 2026-06-22 nerv-orquestador→nerv-desktop T-002 (Niv S, Strict TDD)
- Encargo: scaffold del repo + Remote Script base + servidor MCP base + handshake `ping`, según contrato 04_api_contracts.md. Resolver thread-safety del LOM (ops en hilo UI de Live vía scheduler del Remote Script).
- Leer: 04_api_contracts.md (§A,§B,§C), 02_architecture.md (ADR-001), 03_backlog.md (T-002). Strict TDD con pytest.
- Caveat: la parte que toca Ableton NO es testeable por el agente (no hay Live) → unit-tests sobre protocolo/MCP con RS mockeado; la validación E2E real la hace el PO en Live 11/12.

### 2026-06-22 nerv-arquitecto→nerv-orquestador T-001 (retorno)
- estado: COMPLETO. ADR-001 Aceptado + contrato del puente definido (revisión adversarial corrida).
- archivos: 02_architecture.md (ADR-001 completo), 04_api_contracts.md (§A protocolo TCP newline-JSON :19845, correlación UUID, timeouts, errores; §B 6 tools F-001..005; §C compat Live 11 vs 12).
- riesgos: (1) LOM NO thread-safe → ops en hilo UI de Live (resuelve T-002); (2) insert_notes difiere Live 11 (`set_notes`) vs 12 (`add_new_notes`) → adaptador NotesCodec por api_level; (3) `track_index` se invalida tras crear/borrar tracks.
- validación: criterios T-001 OK; prueba real recién en T-002 (handshake ping→live_version en Live 11 y 12).

### 2026-06-21 nerv-orquestador→nerv-arquitecto T-001 (Niv S)
- Encargo: formalizar ADR-001 (Remote Script vs M4L, ya decidido) + diseñar el contrato del puente (socket TCP local MCP↔RemoteScript + superficie de tools MCP para F-001..F-005). Sin código de implementación.
- Leer: engram/01_requirements.md (§1,§2,§7), 02_architecture.md (stack+ADRs), 03_backlog.md (T-001). Escribe: 02_architecture.md (ADR-001) + 04_api_contracts.md (contrato).
- Restricción: compatibilidad Live 11 y 12 (Py3). Devolver handoff de retorno estructurado.

### 2026-06-21 nerv-orquestador (hallazgo: repo reusable songTagger)
- PO aportó `songTagger` (C:\Users\Gabriel Maglia\Documents\PersonalProjects\songTagger + GitHub). Es un pipeline de análisis DJ para techno/peak-time MADURO: BPM/beats/downbeats (essentia+madmom), key+Camelot, curva de energía, secciones (intro/buildup/drop/breakdown/outro), drops, textura, cue points. Reuso directo para Fases 2/3/5 → es el motor de análisis.
- CAVEAT CRÍTICO: el repo tiene `.venv-wsl` → corre bajo WSL/Linux. essentia/madmom son difíciles/no soportados en Windows nativo. abletonBridge debe correr en Windows comercial → NO se puede pedir WSL al cliente. Decisión abierta en ADR-002 (Q-006).
- Próximo: PO elige estrategia de deps → formalizar ADR-001 + ADR-002 con nerv-arquitecto antes de tickets de implementación.

### 2026-06-21 nerv-orquestador (alta de proyecto)
- Proyecto dado de alta en el registry. Engram creado desde plantilla (estilo trafficMe).
- Decisión de arquitectura con PO: puente vía Remote Script (Python), no Max for Live, por compatibilidad Live 11/12 (Standard+Suite) y rendimiento (acceso in-process al LOM). A formalizar como ADR-001 por nerv-arquitecto.
- Pendiente: definir requirements/MVP (Q-001 alcance "ejecutable", Q-002 acciones del MVP) antes de cualquier handoff de implementación.

### 2026-11-22 nerv-orquestador->nerv-desktop T-002b (fix de T-002)
- Fix: faltaba `create_instance` en el Remote Script. Agregados surface.py (ControlSurface + pump schedule_message), handlers.py (ping/state.get/probe.api), tool MCP live_probe_api, README Live 12 Windows. Tests 55 verdes. Estado: En revision QA. Sin probar en Live real.

### 2026-11-22 nerv-orquestador->nerv-desktop T-002c (spike automatizacion Arrangement)
- Agregados spikes.py (automation_session, RecordSpike state machine via _tick, cleanup) + 4 tools MCP + contrato "Spikes (temporales)". Tests 70 verdes. En revision QA. Sin probar en Live real (VERIFICAR EN LIVE: add_new_notes, insert_device, record_mode).

### 2026-11-22 nerv-orquestador->nerv-desktop T-002d (spikes ronda 2)
- Agregados spikes_media.py (audio_clip, devices, simpler_slice), automation_arm + arm en record_start (restaura al terminar), 4 tools MCP + contrato. Tests 102 verdes. En revision QA. Sin probar en Live real (ver lista VERIFICAR EN LIVE en contratos).

### 2026-11-22 nerv-orquestador->nerv-desktop T-008 (state.detail)
- Agregados state_detail.py (lectura completa read-only, wrappers safe), lom_read.py (helpers compartidos, spikes ahora los reusan), cmd `state.detail`, tool MCP live_get_state_detail con volcado a .cache/state_detail/ (>60k chars) + contrato permanente. Tests 123 verdes. En revision QA. Sin probar en Live real (ver VERIFICAR EN LIVE en contrato).

### 2026-11-22 nerv-orquestador->nerv-desktop T-003 (comandos de produccion v1)
- Agregados production.py (11 comandos: song.set, track.create/set_mixer/delete, clip.place_audio/create_midi, device.insert/set_param, simpler.load, locator.set/clear_all), errors.CommandError (el servidor responde su `code` en vez de LOM_ERROR), 11 tools MCP `live_*` + seccion "Produccion v1" del contrato. Tests 181 verdes. En revision QA. Sin probar en Live real (ver VERIFICAR EN LIVE en el contrato). Nota: no existia engram/plans/T-003.md (plan gate no estampado) y el T-003 del backlog es otro ticket (Transporte).

### 2026-11-22 nerv-orquestador->nerv-desktop T-003 fixes (primera corrida REAL en Live 12.4.16)
- BUG 1 place_audio: markers no acortan el span de Arrangement -> ahora `Clip.crop()` + verificacion por `end_time-start_time`; cada clip devuelve `span`; warning con span real si no recorta. BUG 2 locators: `current_song_time` se aplica en un tick posterior -> `production.LocatorQueue` (maquina de estados desde `_tick`), cmds `locator.set` (queued), `locator.set_many`, `locator.status`, `locator.clear_all` async; tools MCP `live_locator_set_many`, `live_locator_status`. Tests 186 verdes (fakes modelan span independiente y playhead diferido). En revision QA. Re-probar en Live (ver VERIFICAR EN LIVE 3 y 5).

### 2026-11-22 nerv-orquestador->nerv-desktop T-009 (sends y returns)
- Agregados `track.set_send`, `return.list/set_mixer/device_insert/device_set_param/create` + 6 tools MCP `live_*`. Refactor: helpers `_db_arg`/`_set_db` (biseccion compartida), `_apply_mixer`, `_insert_device`/`_set_device_param` aceptan un objeto track (tracks y returns). `return.list` devuelve `{returns, count}` (no lista pelada). Tests 202 verdes. En revision QA. Sin probar en Live real (ver VERIFICAR EN LIVE T-009 en contrato). No existe engram/plans/T-009.md (plan gate sin estampar).

### 2026-11-22 nerv-orquestador->nerv-desktop T-003b (largo exacto de clips de audio)
- `clip.place_audio` reescrito: tiles parciales / loop_* via slot de Session scratch + `duplicate_clip_to_arrangement` (sin crop), re-busqueda por start_time, verificacion de span (tol 0.01), `method`/`warping` por clip, `one_shot` (sin warp, 1 copia, sin trim). Nuevo `clip.delete_range` + tool `live_clip_delete_range`. Tests 211 verdes (fakes modelan span fijo en Arrangement y span=loop al duplicar). En revision QA. Re-probar en Live (VERIFICAR EN LIVE T-003b en contrato).

### 2026-11-22 nerv-orquestador->nerv-desktop T-010 (envelopes, master, sidechain)
- `clip.place_audio` / `clip.create_midi` aceptan `envelopes` + `points_span` (tile|range): todo tile pasa por Session y se escriben rampas de 0.25 beat con `create_automation_envelope`/`insert_step`; reporte por tile. Nuevo `_raw_for_display` (bisección por unidad, kHz/s normalizados, display creciente o decreciente) usado por `device.set_param`/`return.device_set_param`/`master.device_set_param` (`display`) y por puntos `{"display": n}`. Nuevos cmds `master.device_insert`, `master.device_set_param`, `master.set_mixer`, `compressor.set_sidechain` + 4 tools MCP. Tests 261 verdes. En revision QA. Sin probar en Live real (VERIFICAR EN LIVE T-010 en contrato). No existe engram/plans/T-010.md (plan gate sin estampar).

### 2026-11-22 nerv-orquestador->nerv-desktop T-003c (one-shots largos con duracion exacta)
- `clip.place_audio one_shot` ahora usa slot de Session scratch: warping on (Complex por defecto), warp markers forzados a (0,0)..(sample_beats, secs), loop/markers = sample_beats, `looping=False` (reintento con True si el span no coincide), duplicate + re-busqueda + verificacion (tol 0.05). Nuevo `end_beat` (alternativa a `start_beat`). Respuesta suma `method:"session_duplicate_oneshot"`, `warp_markers`. Falla de markers => `ok:false`, nada colocado. Tool MCP `live_clip_place_audio` suma `end_beat`. Tests 270 verdes. En revision QA. Sin probar en Live real (VERIFICAR EN LIVE T-003c en contrato). No existe engram/plans/T-003c.md (plan gate sin estampar).

### 2026-11-22 nerv-orquestador->nerv-desktop T-003d (one-shot: cadena de estrategias)
- `_place_one_shot` prueba A `unwarped_session` (loop/markers en segundos), B `forced_markers` (extiende end_marker/loop_end antes del marker), C `move_end_marker` (`move_warp_marker`) hasta que el span duplicado == sample_beats; respuesta suma `strategy`, `strategy_errors`, `diagnostics` del primer clip de Session. Fake de test modela la evidencia real (marker > end_marker => "Segment length out of range"). Tests 278 verdes. En revision QA. Sin probar en Live real (VERIFICAR EN LIVE T-003d en contrato). No existe engram/plans/T-003d.md (plan gate sin estampar).

### 2026-11-22 nerv-orquestador->nerv-desktop T-011 (bridge.reload)
- Estado intercambiable movido a `runtime.BridgeRuntime` (servidor, dispatcher, handlers, spikes, locators); `surface` queda como cascara (propiedades `server/dispatcher/spikes/locators` delegan). Nuevos: `version.py` (VERSION + LOADED_AT), `reloader.py` (reload en orden + rollback de `__dict__`), `BridgeServer.after_response`, cmds `bridge.reload`/`bridge.version`, tools MCP `live_bridge_reload`/`live_bridge_version`. Tests 299 verdes (incluye reload real en subproceso limpio). En revision QA. Sin probar en Live real (VERIFICAR EN LIVE T-011 en contrato). El primer reload requiere reiniciar Live una vez (la surface instalada es vieja). No existe engram/plans/T-011.md (plan gate sin estampar).

### 2026-11-22 nerv-orquestador->nerv-desktop T-012 (automatizacion de track grabada)
- Nuevo `automation.py` (`AutomationRecorder` + `interp` + `clear`), cmds `automation.record/status/cancel/clear` (runtime.py: handlers, tick aislado, `busy()`), `automation` agregado a `RELOAD_ORDER` (reloader.py), 4 tools MCP `live_automation_*` (record sondea status con tope = beats a tempo + 20 s). Grabacion por Automation Arm + record_mode + escritura de `param.value` desde el tick; desarma pistas armadas y restaura todo. Tests 355 verdes. En revision QA. Sin probar en Live real (VERIFICAR EN LIVE T-012 en contrato). No existe engram/plans/T-012.md (plan gate sin estampar). Cambios en reloader.py (RELOAD_ORDER): el reloader en memoria es el viejo, asi que `live_bridge_reload` alcanza para usar `automation` (se importa por primera vez), pero ediciones FUTURAS de automation.py solo se recargan en caliente tras reiniciar Live una vez.

### 2026-11-22 nerv-orquestador->nerv-desktop T-013 (regla D-15: prohibido automatizar volume)
- `_env_param` rechaza `target "volume"` (clip envelopes, `automation.record/clear`) con mensaje que nombra el param real `Output` y `utility.ensure_last`. Nuevo cmd `utility.ensure_last` + tool `live_utility_ensure_last` (Utility ultimo en track / return / master; idempotente; si existe pero no es ultimo agrega otro y avisa). Param de nivel REAL del Utility en Live 12.4.16 segun `devices_spike_2026-11-22.json`: `Output` (-1..1, display dB), NO "Gain". 34 tests migrados a Utility `Output` sin debilitar aserciones + tests nuevos. Suite 376 verdes. En revision QA. Sin probar en Live real (VERIFICAR EN LIVE T-013 en contrato).

### 2026-11-22 nerv-orquestador->nerv-ai T-016 (nexo como skill de Claude Code + servidor MCP stdio)
- Nuevo `stdio_server.py` + `__main__.py`: envuelve los 35 `live_*` publicos (spikes solo con `NEXO_MCP_SPIKES=1`) con un BridgeClient compartido y perezoso, errores `CODE: mensaje`, guard de 60k chars a `.cache/mcp_results/`, salida limpia en EOF. Sin cambiar firmas de `server.py`. SDK `mcp` instalado = 2.3.0 (`MCPServer`, no `FastMCP`); fallback a 1.x sin probar. `.mcp.json` (venv absoluto), skill `.claude/skills/nexo-ableton/` (+ `reference/comandos.md`), README "Usar desde Claude Code", `mcp>=1.2` en requirements. Tests 389 verdes (13 nuevos, incluyen subproceso real: initialize + tools/list + EOF). En revision QA. NO probado: Claude Code real cargando el servidor ni una tool contra Live real. No existe engram/plans/T-016.md (plan gate sin estampar) ni T-016 en el backlog.

### 2026-11-22 nerv-orquestador->nerv-desktop T-014 (motor de analisis v1)
- Nuevo paquete `nexo_analysis/` (loudness, pitch, index_pack, adapter_songtagger + worker WSL, blueprint) + `tests/test_nexo_analysis/` (78 verdes, sinteticos), `nexo_analysis/requirements.txt`, `.venv-analysis` ignorado. Medido en el kit nuar: kick G1 49.01 Hz (alta); rumble A1 ~54 Hz con parcial F1 44.4 Hz, confianza baja (no hay nota unica, pulso por tiempo); bajo F2 86.6 Hz. Kick -2 st => F1 exacto; el rumble ni confirma ni contradice. Adaptador probado con WSL real (essentia 134.01 vs songTagger cuantizado 133.33). Sin ffmpeg: loudness numerico. En revision QA. No existia engram/plans/T-014.md (plan gate sin estampar). Detalle en docs/nexo/hallazgos/F2_escucha_de_referencias.md "Motor v1 (T-014)".

### 2026-11-22 nerv-orquestador->nerv-desktop T-015 (perfil de genero + reglas de arreglo como codigo)
- Nuevo paquete `composer/` (profile, structure, rules, plan, executor, t03, model) + perfil `docs/nexo/perfiles/techno_peak_time.yaml` (esquema F4 con fuente/confianza por bloque; criterios de Gabriel marcados `criterio_gabriel`). Reglas puras que emiten un timeline como dato: capas por seccion (suma/quita/solo/ocasionales), huecos de kick por nivel de frase 8/16/32, snare fills y rolls, crashes, reverses/impactos/downlifters/risers que terminan en el limite, silencio y corte previo al drop, puente de tension continua (entradas cada 4 compases con fade en Utility `Output`, pad, roll que acelera, filtro que sigue al riser, HP de master), escalera de filtro, llamado y respuesta, pan alterno. D-15 impuesto en `Accion` (una lane de volume no se puede construir) y en el perfil. `executor` con cliente inyectable y dry-run. Plan generado (dry-run, sin tocar Live): `docs/nexo/temas/T03_plan_generado.md/.json`. Tests 87 en `tests/test_composer` (suite completa 463 verdes sin contar `test_stdio_server.py` de otro agente). En revision QA. Sin probar en Live real. No existe engram/plans/T-015.md ni T-015 en el backlog (plan gate sin estampar). Dependencia nueva: pyyaml (`composer/requirements.txt`).

### 2026-11-22 nerv-orquestador->nerv-desktop T-015b (compositor: respuestas del PO)
- Fines de 32: rumble/bajo caen solo en el compas que entra al primer drop (64); en los otros solo cae el kick. Ultimo compas con kick entero y corte de 2 tiempos antes del Main quedan escritos en el plan (acciones `decision`, seccion "Decisiones de arreglo"). Voz/stab RECHAZADA en el stab: la regla queda `experimental`, `activa_por_defecto: false`, sin instrumento (`responde: null`); `Contexto.reglas_experimentales` la habilita. FX variados: `Elemento.alternativas` + rotacion determinista sin repetir seguido (`variedad_fx`; T03 con ~20 archivos reales). Entrada filtrada: Auto Filter 300 Hz -> 16 kHz en 8 compases como lane grabada en la primera aparicion y en entradas del puente (no en la que culmina el riser; stab/lead ya tienen su lane; recortada si choca con otra lane del mismo filtro). Ecos de delay en voces: lane grabada del send al retorno Delay (-60 -> -8 dB) en el ultimo medio compas de cada frase de 4; el send estatico de vox_angel se quito. Plantilla de mezcla por rol en el perfil (HP 12 dB/oct por nombre EXACTO via `valor_item`, kick Drum Buss, bajo Saturator, sidechain con valores, Bass Mono 120 Hz en Utility ultimo para kick/rumble/bass, master Glue/Limiter) y el ejecutor la aplica en orden EQ -> filtro -> dinamica -> saturacion -> Utility; fallos de params se informan y siguen. A-02: plugins de terceros (FabFilter Pro-Q 3, Maag EQ4, Butch Vig Vocals, Waves H-Comp) opcionales por nombre (`Contexto.plugins`, `mezcla.plugins`); nativo es el default; sus valores van a mano. Suite 514 verdes. En revision QA. Sin probar en Live real. No existe engram/plans/T-015b.md ni T-015b en el backlog (plan gate sin estampar). Huecos: F4 no da valores de presencia/aire/compresor/de-esser de voces (van como `propuesta`, confianza baja, sin de-esser ni saturador de voz); items cuantizados de Glue/Limiter/Auto Filter sin catalogo (Attack 30 ms, Ratio, True Peak) quedan "a mano"; cadenas de los retornos (HP 400/LP 3 k del delay) no se configuran.

### 2026-11-22 nerv-orquestador->nerv-desktop T-017 (lectura de medidores)
- `meter.capture/status/cancel` + tools MCP `live_meter_capture/status/cancel`. Clase `MeterCapture` DENTRO de `automation.py` (sin modulos nuevos: hot reload alcanza; reusa `AutomationRecorder._seeking`), handlers/tick/busy en `runtime.py`; no se tocaron surface/reloader/__init__. Solo lectura (sin record_mode ni Automation Arm). Por target: fader_display, peak/rms crudos + dB estimado (`db_estimate_uncalibrated`, o `db_calibrated` con `calibration.points`, interpolacion lineal en log), bins por `bin_bars`, gain_reduction solo si el LOM expone algo con "reduction" (si no, "unavailable"). Exclusion mutua con `automation.record`. Tests 539 verdes (25 nuevos). En revision QA. Sin probar en Live real (VERIFICAR EN LIVE T-017 en contrato). No existe engram/plans/T-017.md ni T-017 en el backlog (plan gate sin estampar).
