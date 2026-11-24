# Requirements — abletonBridge

## 1. Visión (1 frase)
Puente que permite a Claude (vía MCP) controlar Ableton Live 11/12 a través de un Remote Script de Python, con UI de control/config en escritorio y modelo freemium/donación.

## 2. Funcionalidades (IN — v1 / Motor de control)
| ID | Funcionalidad | MoSCoW | Estado |
|----|---------------|--------|--------|
| F-001 | Transporte: play / stop / set tempo | Must | Backlog |
| F-002 | Crear track MIDI y nombrarlo | Must | Backlog |
| F-003 | Crear clip MIDI en un slot | Must | Backlog |
| F-004 | Insertar notas en un clip (acordes, stabs, progresiones) | Must | Backlog |
| F-005 | Leer estado del set (tempo, tracks, clips) | Must | Backlog |

## 3. Fuera de alcance de v1 (diferido — ver Roadmap §7)
- Procesamiento de audio en tiempo real (el puente es control-rate, no audio-rate). [permanente]
- Soporte Live ≤10 (Python 2) — solo Live 11 y 12 (Python 3). [permanente]
- Chopeo de audio, groove maestro, mezcla/master asistido, plantillas de género: NO en v1 — son fases posteriores del roadmap (§7), se construyen sobre el motor de control.

## 4. Reglas de negocio
> **2026-11-18:** RN-001, RN-002 y RN-003 quedan **obsoletas** por D-09 y D-10
> (`docs/nexo/00_vision_y_decisiones.md`): uso personal, sin venta ni
> distribución, y apuntando solo a Live 12.4.x.

| ID | Regla | Origen/fecha |
|----|-------|--------------|
| RN-001 | Compatibilidad obligatoria Live 11 y Live 12 (ambos Python 3). | PO 2026-06-21 |
| RN-002 | Modelo freemium con donación (no pago obligatorio en v1). | PO 2026-06-21 |
| RN-003 | Mismo estilo de producto que trafficMe: Python + PySide6 + empaquetado PyInstaller. **[OBSOLETA — D-10]** | PO 2026-06-21 |

## 5. Enlaces (espejo del registry: tracker, board, Figma)
- Repo: https://github.com/gabiMaglia/abletonBridge
- Tracker: ninguno (gestión en engram /md)
- Board: —
- Figma: —

## 6. Preguntas abiertas al PO
| # | Pregunta | De | Respuesta | Fecha |
|---|----------|----|-----------|-------|
| Q-001 | Alcance "ejecutable": ¿el entregable v1 es (a) instalador que coloca el Remote Script en la carpeta de Ableton + UI de control, o (b) además incluye el servidor MCP empaquetado? | nerv-orquestador | OBSOLETA (2026-11-24): D-10 — uso personal, sin venta ni distribución → no hay instalador ni empaquetado. El MCP se usa desde Claude Code vía `.mcp.json` (T-016). | 2026-06-21 |
| Q-002 | MVP funcional v1 | nerv-orquestador | RESUELTO: F-001..F-005 (transporte, track MIDI, clip, notas, lectura de estado) | 2026-06-21 |
| Q-003 | "Sellar/sonar profesional": ¿alcance = estándar TÉCNICO (loudness/niveles correctos, mezcla limpia, género-apropiado) o expectativa de que la herramienta GARANTICE calidad firmable? (firmar es musical, no solo técnico — definir alcance realista del motor de criterio, Fase 5) | nerv-orquestador | RESUELTA (2026-11-24) por D-01 + D-16: el criterio final es el oído de Gabriel; la herramienta diagnostica y propone contra objetivos de premaster. No garantiza "firmable". | 2026-06-21 |
| Q-004 | "Cualquier tema que respete ciertos parámetros": ¿cuáles son esos parámetros de entrada mínimos? (¿stems separados vs master ya mezclado?, ¿BPM/key conocidos?, ¿formato/cantidad de pistas?) | nerv-orquestador | (pendiente) | 2026-06-21 |
| Q-005 | Plantillas de género modulares/descargables: ¿qué define una plantilla (cadena de devices + grooves + targets de loudness/EQ)? ¿cómo se distribuyen (repo, marketplace, paquete local)? | nerv-orquestador | PARCIAL (2026-11-24): la distribución deja de aplicar (D-10). De hecho, el formato es un perfil YAML por género (`docs/nexo/perfiles/techno_peak_time.yaml`, T-015) + reglas en `composer/`. Falta que el PO lo confirme como formato definitivo y defina cómo "entrenar" un género nuevo (D-03). | 2026-06-21 |
| Q-006 | Reuso songTagger: ¿cómo integramos su análisis (essentia/madmom, hoy en WSL) en un producto Windows comercial? (A) análisis-como-servicio, (B) reescribir con librosa puro, (C) análisis offline desacoplado → define ADR-002 | nerv-orquestador | RESUELTA por D-14 (PO 2026-11-22): paquete propio en WSL sobre songTagger fijado por commit, un solo adaptador, tests de contrato. El riesgo de Windows nativo desaparece con D-10. Implementado en T-014. | 2026-06-21 |

## 7. Roadmap por fases (visión PO 2026-06-21)
> v1 entrega el **motor de control**. Las capacidades musicales/ingeniería se construyen ENCIMA, por fases.
> Dos motores distintos: **control** (determinista, 100% construible) y **criterio** (asistido — diagnostica y propone, ejecuta con tu aprobación; NO es un auto-master mágico).

| Fase | Capacidad | Epic | Motor |
|------|-----------|------|-------|
| 1 (v1) | Transporte, tracks, clips, notas, lectura de estado | F-001..F-005 | control |
| 2 | Audio: importar tema, chopear/slice, warp | E-001 | control |
| 3 | Groove: extraer de audio/MIDI, definir groove maestro, aplicarlo a todas las pistas | E-002 | control |
| 4 | Procesamiento determinista: agrupar pistas, insertar/setear EQ y compresor, routing | E-003 | control |
| 5 | Diagnóstico asistido: LUFS/picos/balance espectral, detección de faltas + propuestas por género | E-004 | criterio |
| 6 | Plantillas/skills de género modulares y descargables (peak time techno primero) | E-005 | control+criterio |
