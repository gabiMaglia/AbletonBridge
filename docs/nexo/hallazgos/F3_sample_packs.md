# F3 — Cómo está compuesto un sample pack de música electrónica

> Investigación web del 2026-11-18. Fuentes al final.
> No existe un estándar formal; lo que sigue es lo que se repite entre vendedores.

## Contenido típico (techno y tech house)

| Contenido | Qué es | Frecuencia |
|-----------|--------|------------|
| One-shots | Golpes sueltos: kicks, claps, hats, percusión, FX, stabs | Siempre |
| Loops | Frases ya armadas de drums, bajo, synth, tops | Siempre |
| MIDI | Patrones de bajo y synth, sin sonido propio | Muy frecuente |
| Presets de synth | Casi siempre Serum o Diva (plugins de terceros) | Frecuente |
| Sampler patches | Instrumentos para Kontakt, EXS y similares | Frecuente |
| Stems / track kits | Temas completos desarmados por pista | A veces |

Ejemplos reales de Loopmasters:
- Tech House Weapons: 1.048 WAV, 38 MIDI, 33 sampler patches, 56 presets de Serum, 425 one-shots.
- Tech House (pack a 123 BPM): 370 loops, 295 one-shots y FX, 96 patrones MIDI.
- Tech House Warlock: 161 WAV, 44 MIDI, 134 one-shots, a 124/126/128 BPM.
- Un pack de techno: 22 sampler patches y 124 presets (90 Diva, 34 Serum 2).

## Convenciones

- **Formato:** WAV 24-bit, a 44.1 o 48 kHz. Algunos traen además REX2 y Apple Loops.
- **Carpetas:** primero por tipo (loops y one-shots separados), después por
  instrumento (Kicks, Snares, Hats, Percussion, Bass, Synths, Textures, FX).
  Splice agrupa los loops por tempo.
- **Nombres:** suelen incluir abreviatura del pack, tipo de sonido, BPM y
  tonalidad. Ejemplos:
  - `AE_Bassloop_140BPM_F_GrittyReese.wav`
  - `Loop_DustyRhodes_82BPM_Fmin.wav`
  - `OneShot_Kick_Deep_01.wav`
- Los loops de instrumentos no afinados (batería) **no llevan tonalidad**.
- BPM y tonalidad se ponen "donde aplica": no todo viene etiquetado.
- **Tempos:** tech house 123-128 BPM, techno 130-135 BPM.
- Cada vendedor nombra distinto; la consistencia es interna al pack, no entre packs.

## Implicancias para el nexo

1. **Indexador en dos pasos:** leer carpetas y nombres primero; analizar el audio
   solo cuando falta BPM, tonalidad o tipo.
2. **El MIDI del pack es muy valioso:** se puede leer, entender y reescribir nota
   por nota.
3. **Presets de terceros** (Serum, Diva) solo sirven si el plugin está instalado,
   y cargarlos desde la API de Live es un riesgo a investigar en F1.
4. **Loops vs one-shots** son materiales distintos:
   - Loops: suenan bien rápido, pero son ideas ajenas y poco modificables.
   - One-shots + MIDI propio: el perfil de género manda de verdad, pero es más
     difícil de hacer sonar bien.
5. **Decisión de Gabriel (D-07):** el material se elige a criterio de Claude según
   convenga. Para kick + rumble se pueden usar loops, chopearlos o modificar el
   audio sobre la grilla.

## Pendiente de este frente

- Ver un pack real de los que va a pasar Gabriel y validar estas convenciones.
- Diseñar el esquema del índice (qué campos por sample).
- Definir cómo se detecta el tipo de sonido cuando el nombre no lo dice.

## Fuentes

- https://www.loopmasters.com/genres/40-Techno/products/5250-Techno
- https://www.loopcloud.com/genres/40-Techno/products/18169-Techno-Rampage
- https://loopmasters.com/genres/66-Tech-House/products/5646-Tech-House
- https://www.loopmasters.com/genres/66-Tech-House/products/8367-Underground-Tech-House
- https://www.loopmasters.com/genres/66-Tech-House/products/17037-Tech-House-Visions?bid=12989
- https://creators.splice.com/file-naming
- https://gravitascreate.com/?p=43303
- https://violetrecording.com/how-to-make-a-sample-pack/
- https://blog.native-instruments.com/how-to-make-a-sample-pack/
- https://www.loopcloud.com/cloud/blog/5306-How-to-Sort-Out-Your-Sample-Library
