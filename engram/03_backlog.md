# Backlog — abletonBridge

> Estados: Backlog → To Do → En progreso → En revisión QA → Done | Bloqueado | Reemplazado
> Solo nerv-qa escribe "Done". Mapear SIEMPRE el ID externo si existe.
> Niv (P-11, nivel de revisión QA): A=Advisory (default) · S=Strong · X=Adversarial.
> "Live" = verificación manual en Live 12.4.16 (bloques VERIFICAR EN LIVE de 04_api_contracts.md): ✅ probado · ⚠️ parcial · ❌ pendiente · n/a.
> Saneamiento 2026-11-24 (T-018): T-002b..T-017 se ejecutaron el 2026-11-22 sin alta en backlog ni plan gate; se dan de alta acá con su estado real según 05_handoff_log.md.

## Sprint 0 — Intake + definición de requirements
| ID | Ext (ADO/Jira) | Tarea | Asignado | Estado | Niv | Criterios de aceptación | Rama |
|----|----------------|-------|----------|--------|-----|--------------------------|------|

## Sprint 1 — Motor de control (Fase 1) — CERRADO por reemplazo
| ID | Ext | Tarea | Asignado | Estado | Niv | Criterios de aceptación | Rama |
|----|-----|-------|----------|--------|-----|--------------------------|------|
| T-001 | — | ADR-001 formal (Remote Script vs M4L) + contrato del puente | nerv-arquitecto | Done | S | ADR-001 en 02_architecture.md + contrato en 04_api_contracts.md. | feature/T-001-bridge-contract |
| T-002 | — | Scaffold repo + Remote Script base + MCP server base + handshake | nerv-desktop | Done | S | Ver veredicto QA. Caveats: LOM no thread-safe (scheduler de UI), stdlib pura, track_index volátil. | feature/T-002-scaffold |
| T-003-orig | — | F-001 Transporte: play / stop / set tempo | — | Reemplazado | A | Tempo cubierto por `song.set` (T-003). **play/stop NO expuestos como comando público** (solo internos de automation/meter) → DT-04. | — |
| T-004-orig | — | F-002 Crear track MIDI + nombrar | — | Reemplazado | A | Cubierto por `track.create` (kind + nombre) (T-003). | — |
| T-005-orig | — | F-003 Crear clip MIDI en un slot | — | Reemplazado | A | Cubierto por `clip.create_midi` en Arrangement (T-003/T-010). | — |
| T-006-orig | — | F-004 Insertar notas en un clip | — | Reemplazado | A | Cubierto por `clip.create_midi` con notas (T-003). | — |
| T-007-orig | — | F-005 Leer estado del set | — | Reemplazado | A | Cubierto por `state.get` (T-002) + `state.detail` (T-008). | — |

## Sprint 2 — Nexo: producción, mezcla, análisis y compositor (2026-11-22)
| ID | Ext | Tarea | Asignado | Estado | Niv | Live | Criterios / notas | Rama |
|----|-----|-------|----------|--------|-----|------|-------------------|------|
| T-002b | — | Fix: `create_instance`, pump de main-thread, `probe.api` | nerv-desktop | En revisión QA | A | ✅ | Handshake real OK en 12.4.16; 23/23 métodos del LOM presentes. | feature/T-002-scaffold |
| T-002c | — | Spike automatización en Arrangement | nerv-desktop | En revisión QA | A | ⚠️ | Spike temporal (spikes.py). Hallazgos en F1. Ver DT-05. | feature/T-002-scaffold |
| T-002d | — | Spikes ronda 2: arm, audio clips, devices, Simpler | nerv-desktop | En revisión QA | A | ⚠️ | Spike temporal (spikes_media.py). Generó `catalogo/devices_spike_2026-11-22.json`. Ver DT-05. | feature/T-002-scaffold |
| T-008 | — | `state.detail`: lectura completa read-only del set | nerv-desktop | En revisión QA | A | ❌ | Volcado a .cache/state_detail/ si >60k chars. | feature/T-002-scaffold |
| T-003 | — | Comandos de producción v1 (song/track/clip/device/simpler/locators) | nerv-desktop | En revisión QA | A | ⚠️ | 1ª corrida real hecha (bugs crop + locators async corregidos). Re-probar VERIFICAR 3 y 5. | feature/T-002-scaffold |
| T-003b | — | Largo exacto de clips de audio vía Session + `clip.delete_range` | nerv-desktop | En revisión QA | A | ❌ | VERIFICAR EN LIVE T-003b. | feature/T-002-scaffold |
| T-003c | — | One-shots largos con duración exacta (warp markers, `end_beat`) | nerv-desktop | En revisión QA | A | ❌ | VERIFICAR EN LIVE T-003c. | feature/T-002-scaffold |
| T-003d | — | One-shot: cadena de estrategias A/B/C + diagnostics | nerv-desktop | En revisión QA | A | ❌ | VERIFICAR EN LIVE T-003d. | feature/T-002-scaffold |
| T-009 | — | Sends y returns | nerv-desktop | En revisión QA | A | ❌ | VERIFICAR EN LIVE T-009. | feature/T-002-scaffold |
| T-010 | — | Envelopes de clip, master, sidechain, valores por unidad | nerv-desktop | En revisión QA | A | ❌ | VERIFICAR EN LIVE T-010. | feature/T-002-scaffold |
| T-011 | — | `bridge.reload` / `bridge.version` (hot reload) | nerv-desktop | En revisión QA | A | ❌ | Primer reload exige reiniciar Live una vez. VERIFICAR EN LIVE T-011. | feature/T-002-scaffold |
| T-012 | — | `automation.record`: lanes reales vía Automation Arm | nerv-desktop | En revisión QA | S | ❌ | Restaura arm/playhead/record_mode. VERIFICAR EN LIVE T-012. | feature/T-002-scaffold |
| T-013 | — | Regla D-15 en código + `utility.ensure_last` | nerv-desktop | En revisión QA | S | ❌ | Volume no automatizable; param de nivel real = `Output`. VERIFICAR EN LIVE T-013. | feature/T-002-scaffold |
| T-016 | — | Servidor MCP stdio + skill `nexo-ableton` | nerv-ai | En revisión QA | A | ⚠️ | Claude Code ya carga el server (tools `live_*` visibles en sesión 2026-11-24). Falta 1 tool contra Live real. | feature/T-002-scaffold |
| T-014 | — | Motor de análisis v1 (`nexo_analysis/`) | nerv-desktop | En revisión QA | A | n/a | Probado con WSL real. songTagger fijado en commit `71a9743` + tests de contrato (D-14). Ver DT-03. | feature/T-002-scaffold |
| T-015 | — | Compositor: perfil de género + reglas de arreglo + ejecutor dry-run | nerv-desktop | En revisión QA | A | ❌ | Plan T03 generado solo en dry-run. | feature/T-002-scaffold |
| T-015b | — | Compositor: respuestas del PO (fines de 32, FX, entrada filtrada, ecos, plantilla de mezcla, plugins) | nerv-desktop | En revisión QA | A | ❌ | Huecos: valores de voces (propuesta), items cuantizados "a mano", cadenas de retornos. | feature/T-002-scaffold |
| T-017 | — | `meter.capture/status/cancel`: lectura de medidores | nerv-desktop | En revisión QA | A | ❌ | Exclusión mutua con automation.record. VERIFICAR EN LIVE T-017. | feature/T-002-scaffold |

## Sprint 3 — Saneamiento + validación en Live (desde 2026-11-24)
| ID | Ext | Tarea | Asignado | Estado | Niv | Criterios de aceptación | Rama |
|----|-----|-------|----------|--------|-----|--------------------------|------|
| T-018 | — | Saneamiento de engram + git | nerv-orquestador | En progreso | A | Backlog refleja T-002b..T-017; state al día; Q-xx reconciliadas con D-xx; ADR-002 cerrado según D-14; docs sin trackear commiteados; rama `main` creada y pusheada. | feature/T-002-scaffold |
| T-019 | — | Sesión de verificación en Live: bloques VERIFICAR EN LIVE (T-003..T-017) | nerv-orquestador + PO | Backlog | S | Cada bloque marcado ✅/❌ con evidencia; bugs → tickets nuevos. Orden sugerido: T-011 → T-003* → T-009/T-010 → T-013 → T-012 → T-017. | — |
| T-020 | — | QA por lotes de T-002b..T-017 | nerv-qa | Backlog | S | Veredicto por ticket. Depende de T-019 para los que tocan Live. | — |
| T-021 | — | Ejecutar plan T03 contra Live real (primer tema end-to-end) | nerv-desktop | Backlog | A | El ejecutor del compositor aplica el plan T03 en un set nuevo; Gabriel valida a oído (D-01). Depende de T-019. | — |

## Épicas (roadmap)
| ID | Épica | Fase | Estado | Niv | Notas |
|----|-------|------|--------|-----|-------|
| E-001 | Audio: importar tema + chopear/slice + warp | 2 | En progreso | A | Parcial: `clip.place_audio`, one-shots, `simpler.load` (T-003*). Falta chop/slice. |
| E-002 | Groove: extraer de audio/MIDI + groove maestro + aplicar | 3 | Backlog | A | Sin arrancar. |
| E-003 | Procesamiento determinista: agrupar + EQ/compresor + routing | 4 | En progreso | S | Parcial: devices, sends/returns, sidechain, master, plantilla de mezcla por rol (T-009/T-010/T-015b). Falta agrupar pistas. |
| E-004 | Motor de criterio asistido: diagnóstico + propuestas | 5 | En progreso | S | Parcial: análisis offline (T-014) + medidores en vivo (T-017). Criterio final = oído de Gabriel (D-01); objetivos premaster (D-16). |
| E-005 | Perfiles de género (techno peak time primero) | 6 | En progreso | A | Parcial: `perfiles/techno_peak_time.yaml` + reglas (T-015/T-015b). Falta tech house (D-02) y "entrenar géneros" (D-03). |

## Veredictos QA
| Tarea | Veredicto | Defectos (si rechazo) | Fecha |
|-------|-----------|------------------------|-------|
| T-001 | Aprobado (sign-off PO — artefacto de diseño) | — | 2026-06-22 |
| T-002 | Aprobado | — Contrato §A cumplido (framing, envelope, correlación id, timeout 5s, backoff 1/2/4s, catálogo errores); UIDispatcher thread-safe correcto; remote_script/ 100% stdlib; pytest 39/39 passed; tests honestos; socket atado a 127.0.0.1. | 2026-06-22 |

## Deuda técnica
| ID | Descripción | Origen | Prioridad |
|----|-------------|--------|-----------|
| DT-01 | Plan gate sin estampar: no existe `engram/plans/` para T-002b..T-017. Decidir si se estampa retroactivo o se acepta la excepción documentada. | T-018 | Media |
| DT-02 | 16 tickets probados solo contra fakes; bloques VERIFICAR EN LIVE pendientes (→ T-019). | Sprint 2 | Alta |
| DT-03 | songTagger tiene cambios sin commitear (auditoría I-6): el commit fijado no garantiza el código exacto que corre. | T-014 | Media |
| DT-04 | Transporte play/stop no expuesto como comando/tool pública (F-001 incompleto). | T-018 | Baja |
| DT-05 | Spikes temporales (`spikes.py`, `spikes_media.py`, cmds `spike.*`) siguen en el Remote Script; retirar o aislar tras T-019. | T-002c/d | Baja |

## Histórico (sprints cerrados: 3 líneas c/u, máx. 5 sprints; el resto a ~/.nerv/archive/)
- **Sprint 1 (2026-06-21..22):** T-001/T-002 Done (QA Strong). T-003..T-007 originales reemplazados por el alcance del nexo (Sprint 2), ver filas `-orig`.
