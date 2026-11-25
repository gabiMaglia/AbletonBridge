# STATE — abletonBridge · actualizado: 2026-11-24 23:45

**Sprint:** 3 — Saneamiento + validación en Live. T-018, T-022, T-023, T-024 Done (QA). T-019 en revisión QA. T-028 (spike YouTube) en revisión QA.
**Rama activa:** main. sincronizada con origin/main (ff32a42 pusheado 2026-11-25). Suite: 579 verdes.
**En curso:** nada en ejecución. Próximos: T-020 (QA por lotes, nerv-qa) · T-029/T-030 (compositor: roll_groove y filtro oscuro, nerv-desktop) · T-026 (spike one-shot).
**Bloqueos:** ninguno. Deuda: T-025 (timeouts, mitigado), 6 Done sin engram/qa/<T>.md (P-4), hook de métricas no instalado.
**Próximo paso sugerido:** seguir el spike T-028 con la jerarquía de groove por velocity (A/B en Live, insumo E-002).
**Hecho a oído hoy (perfil techno_peak_time):** kick bloat 390 Hz -3 dB · roll_groove (convive con el roll que acelera) · filtro_oscuro_pre_break. Detalle en docs/nexo/hallazgos/F7_tutoriales_youtube.md.
**Ojo operativo:** Live lento → `Audio queue timeout` en Log.txt → reiniciar Live. Deploy = copiar a User Library + `live_bridge_reload`. Master del PO en -35 dB (no tiene control de volumen externo): no subirlo.
**Preguntas abiertas al PO:** 3 (Q-004, Q-005, Q-007 S/C EQ del sidechain).
