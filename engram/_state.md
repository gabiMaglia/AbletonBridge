# STATE — abletonBridge · actualizado: 2026-11-24 22:15

**Sprint:** 3 — Saneamiento + validación en Live. T-018, T-022, T-023, T-024 Done (QA). T-019 (verificación en Live) en revisión QA.
**Rama activa:** main (pusheada, b03b85b+) → target: main. Ramas de fix mergeadas y borradas. Suite: 579 verdes.
**En curso:** T-020 QA por lotes de T-002b..T-017 (nerv-qa, To Do: evidencia de Live ya cargada en cada fila).
**Bloqueos:** ninguno. Deuda conocida: T-025 (cliente 30 s < STARTED_CAP 120 s; mitigado con NEXO_MCP_HEAVY_TIMEOUT=130 en .mcp.json).
**Próximo paso sugerido:** T-020 (QA por lotes) → T-026 (spike one-shot, falla en Live) → T-021 (plan T03 end-to-end en Live).
**Ojo operativo:** si Live se pone lento, buscar `Audio queue timeout` en Log.txt y reiniciar Live (DT-09). Deploy del Remote Script = copiar a User Library + `live_bridge_reload` (reiniciar la Superficie de Control NO recarga código).
**Marco vigente:** uso personal, Live 12.4.x (D-09/D-10); testeo a oído (D-01); nunca automatizar volume (D-15); mezcla = premaster (D-16).
**Preguntas abiertas al PO:** 3 (Q-004 parámetros de entrada, Q-005 formato de perfiles, Q-007 S/C EQ del sidechain) + canal de YouTube para el spike de guías (T-028 propuesto).
