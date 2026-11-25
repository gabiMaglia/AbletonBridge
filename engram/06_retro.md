# Retro — abletonBridge

> Entradas nuevas ARRIBA. Una por sesión, ≤8 líneas. La escribe el Orquestador en el
> cierre (P-10). Las lecciones de proceso que aplican a CUALQUIER proyecto se promueven
> a ~/.nerv/playbook.md; lo específico de este proyecto queda acá.

### 2026-11-24 — Saneamiento + verificación en Live (T-018..T-027)
- ✅ Verificar en Live real destapó 4 bugs invisibles a 539 tests con fakes (hilo de accept muerto, errores enmascarados por el SDK MCP 2.x, timeouts que mentían, job vencido que corría igual). TDD + QA Strong los cerró el mismo día.
- ✅ QA rechazó T-022 con razón (criterio "se loguea" incumplido); el rework dio evidencia CONCLUYENTE en Live en vez de "no explotó".
- ⚠️ El orquestador diagnosticó a ciegas mientras los errores llegaban vacíos: culpó al bridge por una ruta mal armada propia, y dio por desplegado un fix que no estaba cargado (reiniciar la Superficie de Control no re-importa módulos).
- ⚠️ Se persiguió la "lentitud del bridge" por 3 tickets antes de mirar el Log.txt de Live: la causa era el motor de audio trabado (DT-09).
- ⚠️ Volvió a acumularse una cadena de 3 ramas de fix sin QA ni merge en una tarde: la misma deuda que T-018 había limpiado a la mañana.
- 🎯 Próxima: antes de culpar al código, revisar Log.txt de Live y `live_bridge_stats`; QA + merge por ticket apenas pasa la verificación, no al final del día.
