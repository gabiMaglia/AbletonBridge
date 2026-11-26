# Norte sonoro — corpus de referencias de Gabriel (D-17)

> Creado 2026-11-25. Criterio de entrada: **suena como el techno que Gabriel quiere hacer** (su oído, D-01),
> no el sello. Copias de trabajo en `F:\Sets 2026\Referencias` (originales en `F:\Dia 2\PEAKTIME`, sin tocar).
> Datos de sello/fecha/catálogo/BPM/key leídos de los tags (mutagen, solo lectura).
> Objetivo: 10–20 temas → set de verdad de terreno del motor F2 + primer perfil del "norte".

| # | Tema | Sello | Catálogo | Lanzamiento | BPM | Key | Rol / nota de Gabriel |
|---|------|-------|----------|-------------|----:|-----|-----------------------|
| 1 | Kaufmann (DE) — Bald Ponytail (Original Mix) | Spectrum (NL) | SPCTRM066 | 2024-12-13 | 130 | 1A | **Referencia exacta**: "exactamente el tipo de techno que quiero hacer" |
| 2 | A.D.H.S., Kos_mo — Taste of the Night (Original Mix) | Drumcode | DC356 | 2026-09-11 | 133 | 2A | Apoyo: "suena como me gusta" |
| 3 | Kevin de Vries, Juan Elvadin — Feel Me (Original Mix) | Drumcode | DC358 | 2026-10-09 | 133 | 4A | Apoyo |
| 4 | SUDO — Converge (Instrumental Mix) | DCLTD | DCLTD51 | 2026-10-02 | 134 | 1A | Apoyo |
| 5 | Moto Moto — Encantadora (Extended Mix) | Nova Collective | NC149-B | 2025-12-05 | 136 | 1A | Apoyo. **Idea de tema:** hacer algo así con el vocal de "Bailando con las estrellas" |
| 6 | Kaufmann (DE) — John Otto (Original Mix) | Spectrum (NL) | SPCTRM066 | 2024-12-13 | 130 | 2B | Apoyo (mismo EP que #1) |
| 7 | Roman Adam — Wasting Time (Original Mix) | Alula Tunes | ALULA354 | 2026-08-28 | 130 | 2B | Apoyo |
| 8 | Lautaro Gabioud — Looking For You (Original Mix) | Set About Music | SA336 | 2025-12-19 | 132 | 4A | Apoyo |

## Ideas de temas que salieron de acá
- **Vocal "Bailando con las estrellas" al estilo de *Encantadora* (Moto Moto).** Pendiente: conseguir el vocal
  (aislado o acapella) y analizar cómo trata Encantadora la voz (chop, ubicación en la frase, FX).

## Medición del motor F2 v1 (2026-11-25, `nexo_analysis.blueprint`, blueprints en scratchpad)

| # | Dur. (s) | LUFS int. | True peak (dBTP) | LRA (LU) | BPM | Key medida | Key tag |
|---|---------:|----------:|-----------------:|---------:|----:|------------|---------|
| 1 | 356,5 | -6,99 | +1,57 | 2,34 | 130,01 | Ab menor | 1A = Ab m ✓ |
| 2 | 350,5 | -5,80 | 0,00 | 2,30 | 132,95 | Eb menor | 2A = Eb m ✓ |
| 3 | 317,5 | -6,67 | +1,73 | 3,60 | 132,97 | F menor | 4A = F m ✓ |
| 4 | 261,0 | -6,31 | -0,20 | 3,42 | 133,92 | Ab menor | 1A ✓ |
| 5 | 311,0 | -7,00 | +0,11 | 4,96 | 136,00 | Ab menor | 1A ✓ |
| 6 | 350,9 | -6,84 | +1,05 | 3,54 | 129,96 | F# menor | 2B = F# **mayor** ✗ (modo: límite C-3) |
| 7 | 376,6 | -7,74 | -0,18 | 2,15 | 130,01 | F# menor | 2B = F# mayor ✗ (modo) |
| 8 | 356,4 | -7,21 | -0,17 | 3,92 | 131,98 | F menor | 4A ✓ |

- **BPM:** coincide con el tag en los 8 (error ≤ 0,05).
- **Tónica:** coincide en los 8; el **modo** falla en los 2 mayores (el motor siempre dice menor, C-3 conocido).
- **Loudness de master:** **-5,8 a -7,7 LUFS** (mediana ≈ -6,9), LRA 2,2–5,0 LU, 4 de 8 con true peak > 0 dBTP.
  ⚠️ **Tensión con D-16** (objetivo club -8,5 LUFS / -1 dBTP): el norte está ~1,5 LU más fuerte y sin respetar
  -1 dBTP. No afecta la mezcla (premaster) pero sí el objetivo de mastering. Decide Gabriel (D-13).
- **No medido (lo que hay que construir):** secciones (`sections` vacío) y elementos dentro de la mezcla
  (`elements` requiere stems).

## Observaciones tempranas (n = 8, sin valor estadístico todavía)
- Todos 2024-12 a 2026-10: el norte es techno **actual**.
- BPM 130–136; tonalidades menores (A en Camelot) salvo dos 2B.
- Sellos: Spectrum (NL) ×2, Drumcode ×2, DCLTD, Nova Collective, Alula Tunes, Set About Music.
- El corpus Drumcode 2022 (`F:\Sets 2026\Drumcode`, 28 temas) queda como material de validación del motor,
  no como norte.
