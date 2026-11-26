# Nexo Claude ↔ Ableton Live 12 — Visión y decisiones

> Documento vivo. Registra lo acordado en conversación con Gabriel.
> Última actualización: 2026-11-18.

## Qué es

Gabriel entrega un **pack de sonidos** y un **brief**, y Claude programa un tema
entero dentro de Ableton Live 12.

Formato del brief:

```
<género> - <sello> - [track de referencia]
ej: techno peak time - Drumcode - https://youtube.com/...
```

- El track de referencia es **opcional**.
- Si es un link de YouTube, hay que obtener el audio y analizarlo.
- Si es un path del disco, hay que analizarlo directamente.

## Ciclo de trabajo

Fase 1 investigar → Fase 2 planificar → Fase 3 ejecutar → Fase 4 testeo, en loop
hasta alcanzar el resultado esperado.

## Decisiones tomadas (por Gabriel)

| # | Decisión | Fecha |
|---|----------|-------|
| D-01 | **El testeo es a oído y lo hace Gabriel.** Él decide cuándo el resultado es el esperado y se corta el loop. No hay criterio automático de aceptación. | 2026-11-18 |
| D-02 | Géneros iniciales: **techno peak time** y **tech house**. | 2026-11-18 |
| D-03 | Tiene que existir la opción de **"entrenar" géneros nuevos**, y lo aprendido se guarda de forma persistente. | 2026-11-18 |
| D-04 | Los datos de género son **parámetros de producción de cada elemento** del tema (kick, bajo, percusión, etc.) y de sus **efectos**, incluyendo fundamentos de **mixing y mastering** del género. | 2026-11-18 |
| D-05 | Cada género requiere una **investigación previa fuerte**: referentes del género, tutoriales de YouTube y todo recurso web sobre cómo se produce. | 2026-11-18 |
| D-06 | Claude debe **conocer a fondo el manual de Ableton**, sus instrumentos y parámetros. | 2026-11-18 |
| D-07 | **Material del pack: a criterio de Claude**, lo que más convenga para llegar al resultado. Para **kick + rumble** se pueden usar loops, chopearlos o modificar el audio sobre la grilla. | 2026-11-18 |
| D-08 | Todo el conocimiento y los acuerdos se guardan en **archivos md**, para no cargar el contexto ni perder nada. | 2026-11-18 |
| D-09 | **La versión de Live no es un límite**: Gabriel puede actualizarla. El diseño apunta a la última 12.4.x estable, hoy **12.4.16** (ver F1). | 2026-11-18 |
| D-10 | **El nexo es de uso personal y no se vende.** Lo que se comercializa son los temas hechos con él. Las licencias de código y la distribución no condicionan el diseño. | 2026-11-18 |
| D-12 | **Fuente de librerías: las carpetas dentro de `G:\LIbrerias\2026`**, en Places del browser de Live (corregido el mismo día: antes decía `F:\2026`, que son proyectos de Gabriel). Si Claude usa material de librería, sale de ahí. | 2026-11-22 |
| D-13 | **Filtro de criterios:** cada criterio de Gabriel se contrasta con (1) lo que dicen las fuentes web y (2) lo que miden los tracks de referencia del género. Acuerdo → sube al perfil con confianza alta. Desacuerdo → Claude lo plantea con evidencia y **decide Gabriel** (D-01 sigue vigente). | 2026-11-22 |
| D-14 | **El motor de análisis (F2) es un paquete nuevo en WSL que usa songTagger como base**, sin modificarlo. Protección del acople: songTagger se usa en una **versión fijada** (tag/commit), a través de **un solo módulo adaptador**, con **tests de contrato** sobre tracks de prueba para detectar cambios silenciosos en las mediciones. | 2026-11-22 |
| D-15 | **Regla de oro, inquebrantable: nunca automatizar el volumen ni la ganancia del track (fader).** Toda automatización de nivel se hace con un **Utility al final de la cadena de efectos** del track. El fader queda libre para la mezcla. | 2026-11-22 |
| D-16 | **La mezcla es un premaster.** Se mezcla con objetivos de premaster, nunca con niveles de master: picos ~**-6 dBFS** (true peak controlado; fuentes van de -6 a -10), loudness integrado ~**-18 a -23 LUFS**, **sin limiter de volumen en el bus master**. El **mastering es una etapa aparte**, con sus propios objetivos (club ~-8,5 LUFS / -1 dBTP; streaming -14 LUFS / -2 dBTP). | 2026-11-22 |
| D-17 | **Norte sonoro: el techno que Gabriel quiere hacer.** Referencia exacta: *Kaufmann (DE) — Bald Ponytail (Original Mix)*, Spectrum (NL), SPCTRM066, 2024-12-13, 130 BPM, 1A. Referencia de apoyo ("suena como me gusta"): *A.D.H.S., Kos_mo — Taste of the Night (Original Mix)*, Drumcode, 2026, 133 BPM, 2A. Copias en `F:\Sets 2026\Referencias`. El corpus del motor (F2) y los perfiles se miden contra este norte. | 2026-11-25 |
| D-11 | **Se sigue con el Remote Script propio** (`abletonBridge`), sin adoptar otro puente. Del código de ableton-mcp (MIT) se toman ideas. Ver F1. | 2026-11-18 |

## Propuestas de Claude (no confirmadas explícitamente por Gabriel)

| # | Propuesta | Estado |
|---|-----------|--------|
| P-01 | "Entrenar" un género = **investigar y destilar** en un perfil estructurado y versionado que Claude lee antes de producir. No es entrenamiento de un modelo. | Sin objeción |
| P-02 | Las **correcciones a oído de Gabriel** se guardan en el perfil del género, así cada tema mejora al siguiente. | Sin objeción |
| P-03 | **Catálogo de devices**: por cada instrumento y efecto de Suite, qué hace cada parámetro y cómo se controla. Dos fuentes: el manual (concepto) y el Live instalado vía puente (nombre exacto, mínimo, máximo, default). Los perfiles de género se escriben encima de este catálogo. | Sin objeción |
| P-04 | Los sonidos que el pack no cubra se **sintetizan con instrumentos nativos de Live** (Operator, Wavetable, Drift, Analog, Meld), sin depender de plugins de terceros. | Deducido, sin confirmar |
| P-05 | **Indexador del pack**: lee carpetas y nombres de archivo primero, y analiza el audio solo cuando falta el dato (BPM, tonalidad, tipo). | Sin objeción |

## Límites conocidos

- **Claude no oye audio.** Los tutoriales se leen por transcripción. Los tracks se
  analizan con motores que devuelven números (tempo, tonalidad, estructura,
  espectro, loudness). Timbre y "feeling" solo se aproximan; ahí manda el oído
  de Gabriel (D-01).

## Estado del entorno (verificado 2026-11-18)

- **Ableton Live 12 Suite, versión 12.1.1**, instalado. Suite incluye Max for Live
  y todos los instrumentos nativos.
- **`abletonBridge/`** (este repo): Remote Script + servidor MCP. Solo implementa
  `live_ping` y `live_get_state`. **Nunca se probó contra un Live real.** 3 commits.
- El roadmap previo está en `engram/01_requirements.md` (fases 1 a 6). La v1 era
  solo notas MIDI en clips; este nexo exige además samples, arrangement, devices
  y automatización.
- **songTagger** (essentia/madmom en WSL) figura como motor de análisis
  reutilizable; su integración quedó sin decidir (Q-006 de requirements). No se
  localizó todavía en el disco.
- `audio-sep/` en el home es solo un venv vacío.
- Engram (memoria persistente) falló en esta sesión por "proyecto ambiguo".

## Preguntas abiertas

| # | Pregunta |
|---|----------|
| A-01 | ~~¿Dónde están las apps de análisis?~~ **Respondida 2026-11-18:** en `C:\Users\Gabriel Maglia\Documents\PersonalProjects\`. Inventario en `hallazgos/F2_escucha_de_referencias.md`. |
| A-02 | ~~¿Solo nativos (P-04) o plugins de terceros?~~ **Respondida 2026-11-22 por los hechos:** Gabriel usa plugins de terceros en T02 (FabFilter Pro-Q 3 y Waves H-Comp en el STAB; Butch Vig Vocals, Maag EQ4 y Limiter en el grupo de voces). P-04 queda como base (nativos para lo que Claude arma), no como exclusiva. |
