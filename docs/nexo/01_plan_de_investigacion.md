# Plan de investigación (Fase 1)

> Cómo se divide la investigación que alimenta la arquitectura del nexo.
> Cada frente produce un md de hallazgos en `docs/nexo/hallazgos/`.
> Estado: borrador en discusión. Última actualización: 2026-11-18.

## Frentes

| # | Frente | Pregunta que responde | Estado |
|---|--------|-----------------------|--------|
| F1 | Control de Live | ¿Qué permite hacer la API de Live 12 y por qué camino? | Probado en Live 12.4.16: puente propio OK, automatización resuelta (2 caminos) |
| F2 | Escucha de referencias | ¿Cómo paso de un link de YouTube o un archivo a datos útiles? | Inventario de motores hecho |
| F3 | Sample packs | ¿Cómo está compuesto un pack y cómo lo indexo? | Primer hallazgo hecho |
| F4 | Conocimiento de género | ¿Cómo se produce, mezcla y masteriza cada género? | Peak time: investigación web hecha; faltan medir referencias (F2) |
| F5 | Catálogo de Ableton | ¿Qué hace cada instrumento, efecto y parámetro de Live 12 Suite? | Capa conceptual hecha; falta volcado real de parámetros vía puente |
| F6 | Composición | ¿Cómo se pasa de perfil + referencia + pack a un arrangement? | Pendiente |
| F7 | Loop de feedback | ¿Cómo se registran las correcciones a oído y cómo vuelven al perfil? | Pendiente |

## Detalle por frente

### F1 — Control de Live
- Qué expone el Live Object Model en 12.1: crear tracks de audio y MIDI, cargar
  samples y devices desde el browser, clips en Session y en Arrangement,
  automatización, warp, slicing, grupos, routing, sends.
- Qué **no** se puede por API (por ejemplo exportar/renderizar) y cómo rodearlo.
- Caminos: Remote Script propio (lo que ya hay), Max for Live, puentes existentes
  (ableton-mcp, AbletonOSC y similares). Decidir construir vs adoptar.
- Primer paso obligatorio: **probar el handshake real** de `abletonBridge` contra
  Live 12.1.1, que nunca se verificó.
- Edición de audio sobre la grilla (chop de loops de kick + rumble, D-07): qué
  operaciones son posibles por API.

### F2 — Escucha de referencias
- Obtener audio desde YouTube y desde path local.
- Qué extraer: tempo, tonalidad, estructura (intro, break, drop), stems,
  balance espectral, loudness, densidad rítmica por elemento.
- Reutilizar los motores ya hechos (songTagger y otros; ver A-01 en visión).
- Formato de salida: un "blueprint" de referencia que F6 pueda consumir.

### F3 — Sample packs
- Composición típica de un pack (hecho: ver `hallazgos/F3_sample_packs.md`).
- Diseño del indexador: carpetas y nombres primero, análisis de audio como
  respaldo.
- Lectura y reutilización del MIDI que traen los packs.
- Qué hacer con presets de terceros (Serum, Diva) y sampler patches.

### F4 — Conocimiento de género
- Arranque: **techno peak time** y **tech house**.
- Fuentes: tracks referentes del género y del sello, tutoriales de YouTube
  (por transcripción), artículos, foros, cursos, entrevistas a productores.
- Qué se destila por género: tempo, tonalidades frecuentes, estructura y
  duración de secciones, patrones rítmicos por elemento, diseño de sonido de
  cada elemento, cadenas de efectos, mezcla (niveles, EQ, compresión, sidechain,
  espacio), master (loudness objetivo, limitación).
- Variación por sello (ej. Drumcode dentro de peak time).
- Definir el **esquema del perfil de género**: mismo formato para todos, para
  que agregar un género nuevo sea repetir el proceso (D-03).

### F5 — Catálogo de Ableton
- Manual de Live 12: concepto de cada instrumento y efecto, y de las
  funciones de edición (warp, slice, groove, automatización).
- Volcado real desde el Live instalado: por device, lista de parámetros con
  nombre, mínimo, máximo y default.
- Recetas de diseño de sonido con devices nativos para los elementos que piden
  los géneros iniciales (kick, rumble, bajo, stabs, hats, FX).

### F6 — Composición
- Cómo se combinan perfil de género + blueprint de referencia + índice del pack.
- Orden de construcción del tema (ej. kick y rumble primero, luego groove,
  luego elementos melódicos, luego arrangement, luego mezcla).
- Qué decide Claude y qué queda parametrizado en el perfil.

### F7 — Loop de feedback
- Cómo Gabriel expresa una corrección a oído y cómo se traduce a un cambio
  concreto en Live.
- Qué correcciones son del tema puntual y cuáles suben al perfil del género.
- Cómo se versionan los perfiles.

## Orden sugerido

1. **F1 primero**, porque es el riesgo que puede invalidar todo: si no se puede
   cargar samples o escribir en el arrangement, cambia el diseño entero.
2. **F5 y F3** en paralelo con F1: no dependen de nada.
3. **F4** (peak time primero), que es el más largo y puede correr en paralelo.
4. **F2** una vez localizados los motores existentes.
5. **F6 y F7** al final: dependen de lo que descubran los anteriores.
