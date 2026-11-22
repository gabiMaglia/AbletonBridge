# Handoff Log — abletonBridge

> Entradas nuevas ARRIBA. Máx. 6 líneas por entrada. Al superar 30 entradas,
> el Orquestador mueve las más viejas a ~/.nerv/archive/abletonBridge-handoffs-[fecha].md

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
