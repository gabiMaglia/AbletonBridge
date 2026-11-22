# F2 — Escucha de referencias

> Primer hallazgo del 2026-11-18: inventario de motores ya hechos en
> `C:\Users\Gabriel Maglia\Documents\PersonalProjects\` (respuesta a A-01).
> Leído en el código; no se ejecutó nada. "INFERIDO" = deducido, no leído.

## songTagger — motor principal reutilizable

Ruta: `PersonalProjects\songTagger\`. Python 3.11.

| Qué mide | Cómo | Archivo |
|----------|------|---------|
| Carga de audio (mono, 44.1 kHz; mp3/wav/flac/aiff) | essentia `MonoLoader` | `analyzer/audio_loader.py` |
| BPM, beats y downbeats | essentia `RhythmExtractor2013` + madmom (RNN+DBN), con corrección de medio/doble tempo | `analyzer/rhythm.py` |
| Tonalidad + Camelot | essentia `KeyExtractor` perfil `edmm` (pensado para electrónica) | `analyzer/key_detector.py` |
| Curva de energía por beat | RMS + flux + banda grave, normalizada 0–1 | `analyzer/energy.py` |
| Textura (ACID/INDUSTRIAL/MELODIC/RAW/FUNKY) | centroide, ZCR y flatness con umbrales | `analyzer/texture.py` |
| Secciones (INTRO/BUILDUP/DROP/BREAKDOWN/BODY/OUTRO) y drops | heurística sobre la curva de energía, ventanas de 16 beats alineadas a downbeats | `analyzer/section_detector.py` |
| Golpes de kick | energía grave por beat | `analyzer/kick_detector.py` |

- **Uso:** CLI `main.py -i <archivo|carpeta> -o <salida>`; también UI PySide6.
- **Salida:** un JSON por track con bpm, beats, downbeats, key, camelot,
  energy_curve, texture, `sections[{type, start_time, end_time, ...}]`, drops,
  kick_events, cues. Ejemplo:
  `output/5A - 130 - Metodi Hristov - Traffic (Original Mix).json`.
- **Estado:** 280 tracks analizados (~42 s por track); 102 tests, último run
  sin fallas (INFERIDO por la caché de pytest).
- **Corre solo en WSL/Linux** (essentia no tiene wheels para Windows). La UI de
  Windows lo llama vía `wsl.exe`. Por D-10 (uso personal) esto ya no es un
  problema de distribución, solo un paso más en el flujo.

### Lo que songTagger NO tiene

- **Loudness:** no mide LUFS ni true peak (la "energía" es RMS normalizada).
- **Stems:** no separa (no hay demucs ni spleeter).
- **YouTube:** no descarga.
- **Balance espectral completo:** solo una banda grave + centroide.
- **Densidad rítmica por elemento:** solo detecta el kick.

## Otros proyectos

| Proyecto | Qué aporta | Evidencia |
|----------|-----------|-----------|
| MoneyPrinterTurbo | Transcripción con **faster-whisper** (large-v3, CPU int8) y ffmpeg | `app/services/subtitle.py`, `video.py` |
| trackMyVoice | Sidecar de **faster-whisper** (modelo base) | `tauri_base_boilerplate-main/sidecar/main.py` |
| multimediaApp | yt-dlp + ffmpeg + Whisper **solo planificados**, sin código | `engram/02_architecture.md` |
| listBuddy (y docs) | Espectrograma STFT en numpy, nada más | `spectro_worker.py` |
| entangle, FollowMe, HUMANODEMASIADOHUMANO, Tauri base Project, networkMonitor | Nada relevante | — |

## Cobertura frente a lo que pide F2

| Necesidad | Hoy | Hueco |
|-----------|-----|-------|
| Bajar audio de YouTube | Nada en código | Falta (yt-dlp) |
| Tempo, tonalidad, secciones | songTagger (WSL) | Validar secciones en techno peak time |
| Loudness (LUFS integrado/short-term, true peak) | Nada | Falta (ej. pyloudnorm) |
| Balance espectral por bandas | Parcial | Falta |
| Stems y densidad por elemento | Nada | Falta (separación de stems) |
| Transcribir tutoriales (F4) | faster-whisper en 2 repos | Reusable |

## Implicancias

1. songTagger cubre la **estructura** de la referencia (BPM, tonalidad,
   secciones), que es justo lo que F4 no pudo sacar de la web (duración real,
   breakdowns, tonalidades frecuentes).
2. Para **mezcla y master** (niveles, LUFS, balance espectral) hay que agregar
   motores nuevos; ninguno de los repos los tiene.
3. La transcripción de tutoriales se puede reusar de MoneyPrinterTurbo
   (faster-whisper), sin construir nada nuevo.

## Pendiente de este frente

- Decidir dónde viven los motores nuevos (¿dentro de songTagger o aparte?).
- Investigar yt-dlp, medición de loudness y separación de stems.
- Definir el formato del "blueprint" de referencia que consume F6.
- **Detectar la nota fundamental del kick y del rumble** (samples del pack y
  referencias). Gabriel afina el rumble contra el kick (ver F4, "Criterios de
  Gabriel"); songTagger no mide esto.

## Diseño del motor de análisis (investigación 2026-11-22)

> Investigación web, sin ejecutar nada. Versiones leídas en PyPI/GitHub el
> 2026-11-22. "NO VERIFICADO" = afirmación sin fuente confirmada en esta sesión.
> Objetivo: que Claude obtenga **números** de referencias y samples para
> (a) armar perfiles de género, (b) aplicar el filtro D-13 y (c) elegir y
> afinar samples.

### Resumen de herramientas

| Necesidad | Herramienta recomendada | Versión / licencia | Windows | Madurez |
|-----------|------------------------|--------------------|---------|---------|
| Bajar audio de YouTube | **yt-dlp** + ffmpeg (+ Deno) | 2026.10.26 / Unlicense [1] | Sí (exe o pip) | Muy activa |
| Loudness (I, S, M, LRA) | **pyloudnorm** | 0.2.0 (2026-01-04) / MIT [2] | Sí | Estable, simple |
| True peak | **ffmpeg `ebur128=peak=true`** | LGPL/GPL según build [3][4] | Sí | Muy madura |
| Pitch de kick/rumble | **numpy/scipy (FFT propia)**; librosa `pyin` como control | librosa 1.0.1 / ISC [5] | Sí | Madura |
| Stems | **demucs `htdemucs`** (base); **audio-separator** (RoFormer) como mejora | demucs MIT, archivado [6]; audio-separator 0.48.0 / MIT [7] | Sí (CPU o CUDA) | demucs congelado; audio-separator activo |
| Balance espectral y ancho estéreo | numpy/scipy + soundfile | BSD | Sí | — |
| Onsets y grilla | madmom (ya en songTagger) o librosa | madmom 0.16.1 (2018) [8] | Dudosa | madmom sin releases desde 2018 |
| Estructura (BPM, key, secciones) | **songTagger** existente | essentia AGPL-3.0 [9] | **No** (solo WSL) | Probado en 280 tracks |

### 1. Audio desde YouTube

- **yt-dlp** 2026.10.26, Unlicense; requiere Python ≥ 3.11 (compatible con el
  entorno de songTagger). Necesita **ffmpeg/ffprobe** para postproceso y, para
  soporte completo de YouTube, el paquete `yt-dlp-ejs` más un runtime de
  JavaScript (se recomienda **Deno**) [1].
- Comando propuesto: `yt-dlp -f bestaudio -x --audio-format wav -o "<id>.%(ext)s" <url>`.
  `-f bestaudio` toma el mejor stream solo-audio y `-x` lo extrae con ffmpeg.
  Que `--audio-format best` evite recodificar es conocimiento general, NO
  VERIFICADO en la doc leída. Pasar a WAV solo evita recodificar dos veces; no
  recupera calidad.
- **Límite de la fuente:** YouTube entrega audio con pérdida (normalmente Opus o
  AAC, NO VERIFICADO el bitrate exacto). Afecta poco a BPM, tonalidad, notas
  graves y LUFS integrado, pero sí afecta **true peak** (la decodificación
  genera sobrepicos) y el **balance por encima de ~16 kHz**. Por eso cada valor
  del blueprint lleva `source_quality` (ver §8) y, si existe, se prefiere el
  archivo local (WAV/AIFF comprado).
- **Términos de uso:** los ToS de YouTube prohíben "descargar" contenido salvo
  autorización expresa del servicio o del titular [10]. El uso aquí es personal y
  analítico (D-10): el audio no se redistribuye ni entra en los temas. Igual es
  una violación de ToS; la decisión de usarlo queda en manos de Gabriel.
  Alternativa limpia: comprar el track en Beatport/Bandcamp y pasar el path.

### 2. Loudness (BS.1770-4 / EBU R128)

| Opción | Mide | Ventaja | Límite |
|--------|------|---------|--------|
| pyloudnorm 0.2.0 | Integrado, LRA (EBU Tech 3342) [2] | API numpy simple; el modo de filtro `DeMan` se declara "fully compliant" [2] | **No mide true peak** [2][11]; el README no declara validación contra el material de prueba EBU [11]. Short-term/momentary hay que armarlos con ventanas propias (3 s / 400 ms) |
| ffmpeg `ebur128` | M (400 ms), S (3 s), I, LRA; `peak=true` agrega true peak [3][4] | Referencia de la industria; `metadata=1` expone `lavfi.r128.M` y similares por frame [3] | Salida como texto/log que hay que parsear; según un ticket, el filtro **cambia la frecuencia de muestreo** al encadenar [4] |
| essentia `LoudnessEBUR128` | M y S como vectores, I, LRA; hop ≤ 0,1 s [12] | Ya está en el entorno de songTagger | Solo **estéreo**; **sin true peak**; cita BS.1770-2, no la -4 [12] |

**Recomendación:** pyloudnorm para la curva (I + S/M con ventanas propias, lo
que se necesita por sección) y **ffmpeg `ebur128=peak=true`** como fuente única
de true peak y como verificación cruzada del integrado. Si los dos difieren en
más de ~0,5 LU, se marca baja confianza (umbral propuesto por Claude, sin
fuente). Ninguna de las tres herramientas declaró en lo leído una
certificación formal contra BS.1770-4: precisión exacta NO VERIFICADA.

### 3. Nota fundamental de kick, rumble y bajo

Salida en todos los casos: `hz`, `note` (ej. `F1`), `cents` (−50..+50), con
`midi = 69 + 12·log2(f/440)`.

**Por qué no alcanza con pYIN/CREPE:**
- CREPE trabaja a 16 kHz con 360 bins de 20 cents = 6 octavas [13]; el piso en
  C1 ≈ 32,7 Hz es del paper, NO VERIFICADO en esta sesión. Está entrenado con
  fuentes monofónicas con nota sostenida, no con kicks: rendimiento en kicks NO
  VERIFICADO.
- pYIN (librosa) funciona con `fmin` bajo, pero la ventana tiene que contener
  varios períodos: a 40 Hz, un período dura 25 ms, y la cola de un kick dura
  pocos cientos de ms con caída de pitch. Sirve como **segunda opinión**, no
  como método principal.

**Método principal propuesto (FFT del cuerpo):**

| Caso | Pasos |
|------|-------|
| **Kick one-shot** (pack) | 1) Detectar el ataque. 2) Saltar el transitorio (~15–30 ms). 3) Ventana Hann sobre el cuerpo (~30–300 ms o hasta −30 dB). 4) FFT con zero-padding (resolución ≤ 0,5 Hz) e interpolación parabólica del pico entre **30 y 120 Hz**. 5) Repetir en ventanas cortas para medir el **pitch glide** (inicio → final) y reportar la nota del tramo estable. |
| **Kick dentro de una mezcla** | 1) Tomar los golpes (`kick_events`/beats de songTagger). 2) Usar el stem de drums si existe; si no, pasabajos ~150 Hz. 3) Promediar el espectro de N golpes alineados (el promedio refuerza el kick y diluye el resto). 4) Mismo pico 30–120 Hz. Si el rumble cae en la misma ventana, se mide sesgado: por eso se cruza con el punto siguiente. |
| **Rumble / bajo** (loop o mezcla) | Espectro promedio de largo plazo de la banda 30–150 Hz **entre golpes de kick** (ventanas en contratiempo), o del stem `bass`. Reportar los 2–3 picos más fuertes. En un rumble hecho con reverb de kick, el pico debería coincidir con la nota del kick (ver F4). |

- Resultado clave para el criterio de Gabriel: `rumble_vs_kick_semitones` =
  diferencia en semitonos entre las dos notas. Así se contrasta (D-13) si en las
  referencias el rumble está a 0 st, a la 5ta, etc.
- Precisión: a 45 Hz un semitono son ~2,7 Hz; con zero-padding + interpolación
  la resolución alcanza, pero la **ambigüedad de octava** (fundamental débil,
  segundo armónico fuerte) es el riesgo principal. Regla propuesta: si hay pico
  en f/2 dentro de −12 dB del principal, se reporta f/2 y se baja la confianza.
  Sin fuente: es una heurística de Claude a validar con samples de nota
  conocida (los del pack que traen nota en el nombre).

### 4. Separación de stems

| Herramienta | Calidad (benchmarks generales) | Costo | Notas |
|-------------|-------------------------------|-------|-------|
| demucs `htdemucs` | 9,0 dB SDR en MUSDB HQ [6] | CPU ≈ 1,5× la duración del track [6] | **Repositorio archivado** el 2025-01-01; solo fixes en el fork `adefossez/demucs` [6]. MIT. En Windows depende de ffmpeg porque torchaudio tiene soporte limitado [6] |
| demucs `htdemucs_ft` | Algo mejor [6] | ~4× más lento que `htdemucs` [6] | — |
| audio-separator 0.48.0 (BS-RoFormer, MelBand, MDX, Demucs) | Entradas BS-RoFormer en MVSEP rondan 11–13 dB SDR en bass/drums [14][15] | Sin cifras de tiempo en CPU: NO VERIFICADO | MIT. CUDA soportado; en Windows con DirectML los RoFormer caen a CPU [7]. `--list_models --list_filter drums` lista modelos [7] |

- **Electrónica:** no se encontró benchmark específico de música electrónica
  [14]. Los números de arriba son de datasets generales (rock/pop). Hay que
  validar con 2–3 referencias de techno: ¿el rumble va al stem `bass` o al de
  `drums`?
- MVSEP publica modelos de **sub-stems de batería** (kick, snare, toms, hats)
  con kick ≈ 17,6 dB y hats/platos 4,8–6,6 dB SDR [14]. Si están disponibles
  en audio-separator (NO VERIFICADO), resuelven el punto 6. Los hats quedan
  pobres.
- GPU: si la PC tiene NVIDIA, WSL2 y Windows pueden usar CUDA. Si no, el costo
  en CPU de un track de 7 min con htdemucs ronda los 10 min (estimación por la
  regla 1,5×). Se cachea por hash del archivo.

### 5. Balance espectral y estéreo

- **Bandas propuestas** (convención de Claude, a ajustar): sub 20–60, low
  60–120, low-mid 120–500, mid 500–2k, high-mid 2k–6k, high 6k–20k Hz.
- Cálculo: STFT (numpy/scipy), energía por banda en dB **relativa al total**
  (así el balance no depende del volumen), agregada por compás y luego por
  sección usando downbeats/secciones de songTagger.
- **Estéreo:** correlación L/R y ancho Side/Mid por banda. La métrica clave para
  techno es `mono_below_hz`: la frecuencia más alta por debajo de la cual la
  correlación se mantiene ≥ 0,9 (umbral propuesto, sin fuente).
- Hay que cargar **estéreo**: el `MonoLoader` de songTagger descarta esta
  información. Usar `soundfile` para leer.

### 6. Densidad y patrones por elemento

- **Factible con cautela.** Onsets sobre el stem de drums con madmom
  (`CNNOnsetProcessor`, ya disponible en songTagger) o
  `librosa.onset.onset_detect`. Para separar elementos sin sub-stems, usar
  onsets por banda: kick < 150 Hz, clap/snare 1–4 kHz, hats > 6 kHz
  (heurística, NO VERIFICADO su desempeño en techno).
- **Grilla de 16 pasos:** con los downbeats de songTagger, cada compás se
  divide en 16; cada onset se cuantiza al paso más cercano y se guarda el
  patrón como cadena (`"x...x...x...x..."`) más la probabilidad de cada paso
  sobre todos los compases de la sección.
- **Swing:** desvío medio de los pasos pares respecto de la grilla recta, como %
  del paso de 1/16. Con hats separados con 5–7 dB SDR, la medida es ruidosa:
  confianza media como techo.
- **madmom:** última release 0.16.1 de 2018; clasificadores hasta Python 3.7 y
  sin soporte de Windows confirmado [8]. Los **modelos** son CC BY-NC-SA 4.0
  [8]: para analizar referencias en uso personal no hay conflicto con D-10,
  porque el modelo no forma parte de los temas que se venden (interpretación de
  Claude, no consulta legal).

### 7. Dónde corre

| Opción | A favor | En contra |
|--------|---------|-----------|
| **A. Paquete nuevo en WSL, junto a songTagger** | Reusa essentia/madmom sin portar nada; un solo entorno Linux; CUDA disponible en WSL2 si hay NVIDIA | Llamada vía `wsl.exe` desde Windows (ya es el patrón de la UI de songTagger); rutas `F:\` ↔ `/mnt/f` |
| B. Paquete nativo Windows | Sin WSL en el camino | essentia **no tiene wheels para Windows** (la última release solo publica Linux/macOS) [9]; habría que reemplazar BPM/key/secciones |
| C. Extender songTagger por dentro | Un solo repo | Mezcla torch/demucs con un proyecto que ya funciona; riesgo de romper los 102 tests |

**Recomendación: A.** Un paquete nuevo (nombre a definir) en WSL, en su propio
venv con Python 3.11, que **importa songTagger como librería** para la
estructura y agrega loudness, pitch, espectro, estéreo, stems y densidad.
CLI única: `analyze <url|path> --out blueprint.json`. El MCP/Claude en Windows
la llama por `wsl.exe` y lee el JSON. Stems y descargas se cachean por hash.

Ojo: **librosa 1.0.1 exige Python ≥ 3.12** [5]. Con 3.11 hay que fijar
`librosa<1.0` (que 0.11 soporte 3.11 es NO VERIFICADO), o subir el venv nuevo a
3.12 si essentia/madmom lo permiten (NO VERIFICADO).

### 8. Esquema del blueprint (lo que consume F6)

Cada valor medido es un objeto `{value, confidence, method}`, con
`confidence` en `high | medium | low`. Así D-13 sabe cuánto pesa cada número.

```json
{
  "schema_version": "0.1",
  "source": {
    "kind": "youtube | file",
    "uri": "https://youtube.com/... | F:\\2026\\...",
    "sha256": "…",
    "source_quality": "lossy_youtube | lossy_file | lossless",
    "analyzed_at": "2026-11-22T00:00:00Z",
    "tools": {"songTagger": "git:…", "pyloudnorm": "0.2.0", "demucs": "htdemucs"}
  },
  "global": {
    "duration_s":      {"value": 412.3, "confidence": "high", "method": "decoder"},
    "bpm":             {"value": 132.0, "confidence": "high", "method": "songTagger"},
    "key":             {"value": "F minor", "camelot": "4A", "confidence": "medium", "method": "essentia edmm"},
    "bars":            {"value": 227, "confidence": "high", "method": "downbeats"},
    "lufs_integrated": {"value": -7.8, "confidence": "high", "method": "pyloudnorm+ffmpeg"},
    "true_peak_dbtp":  {"value": 0.4, "confidence": "low", "method": "ffmpeg ebur128 (fuente con pérdida)"},
    "lra_lu":          {"value": 4.1, "confidence": "high", "method": "pyloudnorm"},
    "short_term_lufs_curve": {"hop_s": 1.0, "values": [-9.1, -8.4]},
    "spectral_balance_db": {"sub": -6.2, "low": -5.1, "low_mid": -9.8, "mid": -13.0, "high_mid": -16.4, "high": -21.7},
    "mono_below_hz":   {"value": 140, "confidence": "medium", "method": "corr>=0.9"}
  },
  "sections": [
    {
      "type": "BREAKDOWN",
      "start_bar": 97, "end_bar": 128, "start_s": 174.5, "end_s": 232.7,
      "lufs_short_term_mean": -11.2,
      "spectral_balance_db": {"sub": -14.0, "low": -10.1},
      "stereo_width": 0.42,
      "elements_present": ["rumble", "pad", "fx"],
      "kick_present": false
    }
  ],
  "elements": {
    "kick": {
      "note":    {"hz": 43.8, "note": "F1", "cents": +8, "confidence": "medium", "method": "fft_body_avg_on_hits"},
      "glide_st": {"value": 5.2, "confidence": "low"},
      "pattern_16": {"value": "x...x...x...x...", "confidence": "high"},
      "hits_per_bar": 4
    },
    "rumble": {
      "note": {"hz": 43.6, "note": "F1", "cents": 0, "confidence": "medium", "method": "lt_spectrum_offbeat"},
      "rumble_vs_kick_semitones": {"value": 0, "confidence": "medium"}
    },
    "bass":  {"note_peaks_hz": [43.6, 87.3], "confidence": "low"},
    "hats":  {"pattern_16": "..x...x...x...x.", "density_per_bar": 8, "swing_pct": 3.0, "confidence": "low"},
    "clap":  {"pattern_16": "....x.......x...", "confidence": "medium"}
  },
  "warnings": ["true peak medido sobre audio con pérdida"]
}
```

- `sections` usa los tipos de songTagger, con compases (lo que necesita el
  arrangement en Live) además de segundos.
- El mismo esquema, sin `sections`, sirve para **samples del pack**
  (`kind: "file"`, solo `elements` y `global` reducido); P-05 lo usaría cuando
  el nombre del archivo no alcanza.
- El perfil de género (F4) agrega N blueprints: medianas y rangos por campo,
  ponderados por `confidence`.

### Decisiones abiertas para Gabriel

1. ¿Se acepta usar yt-dlp contra los ToS de YouTube (uso personal), o las
   referencias se compran y se pasan como archivo?
2. ¿Hay GPU NVIDIA? Define si stems corre en minutos o en ~1,5× la duración
   del track por track.
3. Arquitectura A (paquete nuevo en WSL que importa songTagger): ¿se aprueba?
4. ¿Validar demucs vs BS-RoFormer con 2–3 referencias de techno antes de elegir?

### Fuentes

- [1] https://pypi.org/project/yt-dlp/
- [2] https://pypi.org/project/pyloudnorm/
- [3] https://ffmpeg.org/ffmpeg-filters.html#ebur128-1
- [4] https://ffmpeg.org/pipermail/ffmpeg-user/2014-June/021850.html ;
  https://trac.ffmpeg.org/ticket/7812
- [5] https://pypi.org/project/librosa/
- [6] https://github.com/facebookresearch/demucs
- [7] https://pypi.org/project/audio-separator/
- [8] https://pypi.org/project/madmom/
- [9] https://pypi.org/project/essentia/
- [10] https://www.youtube.com/static?template=terms
- [11] https://github.com/csteinmetz1/pyloudnorm
- [12] https://essentia.upf.edu/reference/std_LoudnessEBUR128.html
- [13] https://github.com/marl/crepe ; paper: https://arxiv.org/abs/1802.06182
- [14] https://mvsep.com/quality_checker/leaderboard.php ;
  https://mvsep.com/quality_checker/entry/9933 ;
  https://mvsep.com/quality_checker/entry/10058
- [15] https://mvsep.com/quality_checker/entry/7762 ; https://arxiv.org/pdf/2309.02612

## Auditoría del motor de análisis (Fable, 2026-11-22)

> Auditoría en tres fases: estado del arte, revisión de songTagger y del diseño
> de arriba, y recomendación. Se leyó el código de songTagger y su
> `batch_run.log` (corrida real de 280 tracks); **no se ejecutó ningún
> análisis de audio ni se instaló nada**. Las URLs se leyeron el 2026-11-22.
> "NO VERIFICADO" = sin fuente confirmada en esta sesión. Rutas de código
> relativas a `PersonalProjects\songTagger\`. Referencias `[A#]` al final de
> esta sección.

### Veredicto en una línea

**Cambiar mucho, no todo.** La arquitectura de D-14 (paquete nuevo en WSL,
adaptador único, tests de contrato) se sostiene. Lo que no se sostiene es
tratar a songTagger como fuente confiable de la estructura: sus secciones,
su "kick" y su BPM final no sirven tal cual para un blueprint. De songTagger
solo son reutilizables dos llamadas a librerías de terceros (beats/downbeats
de madmom y tonalidad de essentia), y ambas necesitan corrección o segunda
opinión.

### Evidencia nueva: lo que dice el log de los 280 tracks

Los archivos de la librería se llaman `<Camelot> - <BPM> - <artista> - <título>`
(ej. `10A - 128 - Charles D (USA) - Traction.flac`). Se parseó
`batch_run.log` y se comparó lo medido con lo que dice el nombre, en 276
tracks con datos completos. **El origen de las etiquetas del nombre es NO
VERIFICADO** (¿Mixed In Key, Beatport?), así que esto es concordancia con
otra herramienta, no exactitud contra verdad de terreno.

| Medida | Resultado | Lectura |
|--------|-----------|---------|
| BPM final (madmom) vs nombre | Coincide a ±0,5 BPM en **124/276**; mediana de diferencia 0,6 BPM | El BPM final solo toma **11 valores distintos** (127,7 · 130,4 · 133,3 · 136,4…), o sea 60/(k·0,01 s). Es un error de cuantización, ver C-1 |
| BPM de essentia vs nombre | Coincide a ±0,5 BPM en **251/276**; mediana 0,0 | El estimador que el pipeline descarta es el que mejor coincide |
| Tonalidad vs Camelot del nombre | Igual en **226/276** (82%); 24 paralelas, 13 a la quinta, 13 otras | Las 24 "paralelas" son exactamente los tracks que el nombre da como mayores |
| Modo detectado | **276/276 menor** | El perfil `edmm` no puede devolver mayor, ver C-3 |
| Secciones por track | Mediana **18** (máx. 41) en tracks de ~6:20 | F4 espera 6–8 |
| Primera etiqueta | BUILDUP en 156, INTRO en 105 | — |
| INTRO que no es la primera sección | **114/276** tracks | Etiquetas sin coherencia temporal |
| Drops por track | Mediana **6** (rango 2–10) | F4 espera 2–3 |
| Tiempo | 42,4 s/track; en el primer track madmom ocupa ~46 de ~51 s | Una sola observación de reparto |

### Fase 1 — Estado del arte y buenas prácticas

| Tarea | Cómo se resuelve hoy | Qué importa para techno / tech house |
|-------|---------------------|--------------------------------------|
| **Beats y downbeats** | Redes que dan activaciones por frame más un decodificador. madmom: RNN + DBN. **Beat This!** (ISMIR 2024): transformer sin DBN; declara superar el estado del arte en F1 y reconoce peor desempeño en métricas de continuidad [A2]. **All-In-One** (WASPAA 2023): beats, downbeats y estructura en un solo modelo sobre audio separado en stems [A1] | La música hecha en DAW tiene **tempo constante**: después de detectar beats conviene ajustar una grilla recta por mínimos cuadrados (BPM y fase), en lugar de usar los beats crudos. En 4x4 la fase del compás es ambigua; se resuelve mejor con la frase que con el downbeat aislado. Ninguna fuente leída reporta resultados específicos en techno: NO VERIFICADO |
| **Tempo** | Evaluación estándar sobre GiantSteps Tempo: 664 previews de 2 min de Beatport [A9]. Sus etiquetas originales vienen de un foro de tempos disputados; Schreiber y Müller las rehicieron por crowdsourcing [A9] | El error clásico es de octava (mitad/doble). En el rango 120–140 el riesgo real es la **precisión fina** (130,0 vs 130,4) |
| **Tonalidad** | Perfiles de clases de altura correlacionados con un cromagrama (essentia: `edma`, `edmm`, `bgate`, `braw`, de Faraldo et al. 2016/2017) [A4][A5], o redes (Korzeniowski y Widmer 2017; S-KEY, ICASSP 2025) [A7][A8]. Dataset: GiantSteps Key, 604 previews de Beatport [A8]. Métrica MIREX: 1,0 acierto; 0,5 quinta; 0,3 relativa; 0,2 paralela [A6] | El techno tiene poco contenido tonal: la confusión relativa/paralela/quinta es esperable. Conviene **dos estimadores independientes** y bajar la confianza si no coinciden |
| **Estructura** | Clásico: matriz de autosimilitud + curva de novedad, agrupado en marcos como MSAF [A12]. Moderno: All-In-One, entrenado en Harmonix Set (912 tracks de **pop occidental**) con etiquetas intro/outro/break/bridge/inst/solo/verse/chorus [A1][A11]. Orientado a DJ: detección de cue points | En EDM los eventos estructurales caen en el downbeat del primer compás de un período, y las frases son potencias de dos compases [A13]. En EDM-CUE (4.710 tracks, 21k cue points) los cues se agrupan en múltiplos de 8 y 16 compases [A14]. Buena práctica: **calcular novedad solo en límites de compás y restringir a la grilla de frases** |
| **Loudness** | ITU-R BS.1770 (vigente: **-5, 11/2023**; la -4 está superada) [A15] + EBU R128. Implementaciones: libebur128 (MIT; M, S, I, LRA y true peak) [A16], ffmpeg `ebur128`, pyloudnorm | True peak exige sobremuestreo; se mide sobre el archivo estéreo, no sobre un mono |
| **Nota de kick / sub** | No se encontró benchmark ni método estándar (NO VERIFICADO que exista). Los estimadores de pitch generales están pensados para notas sostenidas | Kick = barrido de pitch + cola. Importa la frecuencia del **tramo estable** y la resolución en 35–70 Hz, donde un semitono son 2–4 Hz |
| **Separación de stems** | Demucs (archivado), familia RoFormer; ver §4 del diseño | Sin benchmark de electrónica (ya señalado arriba) |
| **Transcripción de batería** | ADTOF: 5 clases, ~359 h de datos de juegos de ritmo; existe port a PyTorch sin madmom [A17] | Desempeño en techno NO VERIFICADO |
| **Swing** | Razón de swing a partir de onsets o de autocorrelación local [A18] | Exige resolución temporal de pocos ms, ver D-f |

**Prácticas de implementación que aplican acá**

1. **Evaluar contra verdad de terreno** con `mir_eval`: F de beats con ventana
   de 70 ms y descartando los primeros 5 s [A19]; puntaje ponderado de
   tonalidad [A6]; aciertos de límites de sección con ventana de 0,5 s por
   defecto [A20]. Para este proyecto la ventana útil es **en compases** (límite
   exacto o ±1 compás), que se deriva fácil.
2. **Reproducibilidad:** dependencias con versión exacta (lockfile), modelos
   identificados por hash, semillas fijas en separación de stems, y las
   versiones grabadas dentro de cada blueprint.
3. **Caché** por `hash(archivo) + versión de herramienta + parámetros`, por
   etapa (stems, beats, etc.), no solo por archivo.
4. **Confianza calibrada:** una etiqueta `high` debe corresponder a una tasa de
   acierto medida en el set de validación. La "fuerza" de un algoritmo
   (correlación, delta de energía) no es una probabilidad.
5. **Fixtures de audio:** sintéticos con respuesta conocida (clicks a BPM
   exacto, senos de frecuencia conocida) más tracks reales referenciados por
   hash, sin subirlos al repo.

### Fase 2 — Auditoría

Severidad: **CRÍTICO** = produce números incorrectos que el compositor (F6) o
el filtro D-13 usarían como ciertos. **IMPORTANTE** = degrada la confianza o
bloquea D-14. **MENOR** = deuda.

#### songTagger, por analizador

| # | Sev. | Hallazgo | Evidencia |
|---|------|----------|-----------|
| C-1 | CRÍTICO | **El BPM final está cuantizado.** Se calcula como `60 / mediana(intervalos)` sobre beats de madmom a 100 fps, o sea intervalos múltiplos de 10 ms. Un track de 130 BPM sale 130,43; uno de 128 sale 127,66. Con 130,43 en vez de 130, la grilla se corre ~3 beats (¾ de compás) en 7 minutos | `analyzer/rhythm.py:79-80`, `:161-163`. Log: 11 valores distintos en 276 tracks. Ejemplo: `Traffic` da `bpm: 130.43`, y el promedio de sus propios beats (primero a último) da 130,004 |
| C-2 | CRÍTICO | **Las secciones no representan la forma del tema.** Ventanas fijas de 16 beats contadas desde el beat 0 (el parámetro `downbeats` se recibe y no se usa), clasificadas por umbrales sobre una energía normalizada min-max por track. Sin contexto: INTRO es "energía baja en el primer 25%", aunque venga después de un DROP. Un comentario del código dice que el BREAKDOWN tras un drop "lo maneja el llamador", y ningún llamador lo hace. No hay restricción de frase de 8/16/32 compases | `analyzer/section_detector.py:22-26`, `:58-60`, `:104-109`, `:119-121`; `analyzer/energy.py:111-113,129`. Log: mediana 18 secciones, INTRO fuera de lugar en 114/276 |
| C-3 | CRÍTICO | **La tonalidad nunca puede salir mayor.** El perfil `edmm` tiene el perfil mayor plano; el código fuente de essentia dice que "reporta los modos mayores como menores" [A5]. En tech house el sesgo puede pesar más (proporción de mayores NO VERIFICADA). Además el valor por defecto de essentia es `bgate`, no `edmm` [A4] | `analyzer/key_detector.py:22`. Log: 276/276 menor |
| I-1 | IMPORTANTE | **`kick_events` no son golpes de kick.** Son transiciones "entra/sale el grave": energía 20–200 Hz por beat, suavizada 8 beats, con umbral 0,35 sobre un valor normalizado por track. Rumble y bajo viven en esa misma banda: un breakdown con sub sostenido puede contar como "kick activo". El evento además se desplaza al downbeat más cercano, hasta 4 beats | `analyzer/kick_detector.py:57-58,61-62,117-124`; `config.py:27-28,117-122`; `analyzer/energy.py:147` |
| I-2 | IMPORTANTE | **BPM y grilla pueden contradecirse.** `resolve_bpm` corrige el BPM (×2, ÷2, o lo toma del nombre del archivo) pero el pipeline usa siempre los beats de madmom sin tocar | `pipeline.py:61-68`; `analyzer/rhythm.py:165-185` |
| I-3 | IMPORTANTE | **El BPM puede venir del nombre del archivo** (primer número de 3 cifras entre 100 y 175). En esta librería todos los nombres traen BPM, así que ante desacuerdo el "dato medido" es una etiqueta externa (5 casos en el log). Queda registrado en `bpm_source`, pero el diseño no lo propaga | `analyzer/rhythm.py:106-114,177-181` |
| I-4 | IMPORTANTE | **Fase del compás sin validar.** madmom con `beats_per_bar=[4]`; si madmom falla, el pipeline toma `beats[::4]`, fase arbitraria. No hay chequeo de que el "1" coincida con el inicio de frase | `analyzer/rhythm.py:65-70`; `pipeline.py:71` |
| I-5 | IMPORTANTE | **Los tests no validan mediciones.** 88 funciones `def test_` (el inventario dice 102; diferencia NO VERIFICADA). Usan arreglos sintéticos o ruido blanco y afirman formas y rangos (`len(drops) >= 1`, `"DROP" in types`). No hay ningún archivo de audio, ni test de `key_detector`, `audio_loader`, la llamada a madmom o el pipeline completo | `tests/test_sections.py:37-47`, `tests/test_energy.py:38,49`, `tests/test_rhythm.py:6` |
| I-6 | IMPORTANTE | **No es una librería importable ni tiene versión fijable.** Sin `pyproject.toml`; módulos de nivel superior llamados `config`, `output`, `analyzer` (riesgo de choque de nombres al importar desde otro paquete); `requirements.txt` sin versiones; sin tags de git, 4 commits, árbol con cambios sin commitear. Al importar `rhythm.py` se parchea numpy global (`np.int`, `np.float`…) para que madmom 0.16.1 funcione | `requirements.txt`; `analyzer/rhythm.py:10-16` |
| M-1 | MENOR | El suavizado con `np.convolve(mode="same")` rellena con ceros los bordes: los primeros beats quedan atenuados y la primera ventana parece "en subida". Causa probable (INFERIDO) de que 156/276 tracks empiecen en BUILDUP | `analyzer/energy.py:122-124`; `analyzer/section_detector.py:124-132` |
| M-2 | MENOR | Confianza de drop saturada: `delta / 0,4`, ×1,15 si cae en downbeat. En el ejemplo hay 7 drops, todos con confianza 1,0 | `analyzer/section_detector.py:203-205`; `config.py:58-59` |
| M-3 | MENOR | Se pierden los últimos beats (`n_beats // window`) | `analyzer/section_detector.py:55` |
| M-4 | MENOR | `analyze_track` es monolítico: no se pueden pedir solo beats; siempre corre textura, clasificación DJ y cues. El audio se decodifica dos veces (essentia y madmom) y el modelo de madmom se instancia por track | `pipeline.py:29-139`; `analyzer/rhythm.py:64` |
| M-5 | MENOR | Carga mono a 44,1 kHz: impide loudness BS.1770, true peak y estéreo (el diseño ya lo señala) | `analyzer/audio_loader.py:40` |

**Rendimiento.** Los ~42 s/track son casi todos de la red de downbeats de
madmom en CPU (una observación del log; sin perfilado). No es el cuello de
botella del motor nuevo: la separación de stems cuesta más. Con caché por
etapa deja de importar.

**Lo que songTagger hace bien:** los beats de madmom son una base sólida (en el
ejemplo dan 130,004 BPM de promedio y un downbeat cada 4 beats sin saltos), y
`config.py` centraliza los umbrales. Es una buena herramienta para lo que fue
hecha: etiquetar una librería de DJ. Sus umbrales están calibrados por
percentiles de esa librería, no contra anotaciones.

#### Diseño propuesto (sección "Diseño del motor de análisis")

| # | Sev. | Hallazgo |
|---|------|----------|
| D-a | CRÍTICO | El esquema declara `bpm` con `confidence: high, method: songTagger` y `sections` con "los tipos de songTagger". Con C-1 y C-2, esos dos campos serían los menos confiables del blueprint, y F6 arma el arrangement sobre ellos |
| D-b | CRÍTICO | **No hay plan de validación.** Ninguna medida tiene verdad de terreno ni métrica. Los tests de contrato de D-14 detectan que un número *cambió*, no que esté *bien* |
| D-c | IMPORTANTE | §3 dice "tomar los golpes (`kick_events`/beats de songTagger)". `kick_events` no contiene golpes (I-1). Los golpes hay que derivarlos de la grilla más un detector de onsets en banda grave |
| D-d | IMPORTANTE | §3, pitch por FFT: el zero-padding **interpola**, no agrega resolución. Con una ventana Hann de ~270 ms el lóbulo principal mide ~15 Hz: un kick en 49 Hz y un rumble en 55 Hz no se separan, y ese intervalo es justo el criterio de Gabriel a contrastar. Sirve para un componente aislado; para dos hace falta separarlos en el tiempo (golpe vs contratiempo, como ya propone) y usar ventanas largas sobre el rumble |
| D-e | IMPORTANTE | La confianza `high/medium/low` se asigna a mano por método. Sin calibración, D-13 pondera con pesos sin respaldo |
| D-f | IMPORTANTE | §6, swing: pasar de 50% a 54% a 130 BPM mueve el contratiempo ~9 ms. madmom trabaja a 100 fps (10 ms). Hace falta detección de onsets con salto de 2–3 ms y medir contra la grilla ajustada, no contra beats crudos |
| D-g | MENOR | §2 cita BS.1770-4; la vigente es la -5 [A15] (impacto en estéreo NO VERIFICADO). Usar pyloudnorm para la curva y ffmpeg para true peak obliga a mantener dos caminos; ffmpeg o libebur128 dan todo de una sola fuente [A16] y pyloudnorm puede quedar como control cruzado |
| D-h | MENOR | Falta en el esquema la grilla explícita (`bpm`, `first_downbeat_s`, residuo del ajuste), y la clave de caché no incluye versiones |
| D-i | MENOR | Licencias de modelos: madmom CC BY-NC-SA [A3]; pesos de S-KEY "solo investigación no comercial" [A8]; ADTOF CC BY-NC-SA [A17]. La interpretación de §6 (uso analítico personal, D-10) es razonable, pero los temas se venden: es una decisión de Gabriel, no técnica |

Lo que el diseño acierta: arquitectura A, `source_quality`, caché por hash,
separar kick y rumble midiendo en golpe vs contratiempo, validar stems con
techno antes de elegir, y marcar la ambigüedad de octava.

### Fase 3 — Alternativas y recomendación

| Componente | Hoy | Alternativa | Licencia / estado / requisitos | Evidencia | Veredicto |
|-----------|-----|-------------|-------------------------------|-----------|-----------|
| Beats | madmom RNN+DBN | **Beat This!** | MIT en código y pesos; PyTorch ≥ 2.0; corre en CPU; Windows no mencionado [A2] | Declara mejor F1 que el estado del arte y peor continuidad; test en GTZAN; sin datos de EDM [A2] | **Mantener madmom** como base. Probar Beat This! solo si el set de validación muestra fallas |
| BPM | mediana de intervalos | Ajuste de grilla recta sobre los beats | numpy | Log propio: essentia coincide en 251/276, el valor final en 124/276 | **Reemplazar** (en el adaptador, sin tocar songTagger) |
| Downbeat / frase | madmom, sin validar | Elegir la fase y el origen de frase que maximicen la novedad en límites de 8 compases | Propio | Principio respaldado por [A13][A14]; implementación a validar | **Mejorar** |
| Tonalidad | essentia `edmm` | essentia `bgate` + un segundo estimador (CNN de tonalidad de madmom, NO VERIFICADO en esta sesión; o S-KEY) | essentia AGPL; S-KEY: código MIT, pesos no comerciales, sin paquete pip [A8] | Korzeniowski y Widmer: 74,3% en GiantSteps según un resultado de búsqueda (fuente exacta NO VERIFICADA) [A7]. No se halló tabla que compare `edmm`, `bgate` y S-KEY en GiantSteps: NO VERIFICADO | **Mejorar**: dos estimadores, confianza por acuerdo |
| Estructura | heurística de energía | (a) Propia: features por compás + novedad restringida a frases + etiquetas por reglas sobre elementos medidos (kick presente, sub, densidad de hats). (b) **All-In-One** para límites | allin1: MIT; requiere NATTEN (wheels para Linux/WSL con NVIDIA; si no, compilar) y madmom desde git [A1][A10]; issue abierto de incompatibilidad con NATTEN 0.17.5 [A10] | Declara estado del arte en Harmonix (pop) [A1]; sus etiquetas son verse/chorus, no build/drop; desempeño en techno NO VERIFICADO | **Reemplazar** por (a); evaluar (b) como comparación |
| Presencia de kick | banda 20–200 Hz | Onsets en banda grave sobre la grilla (golpe presente por tiempo) y, con stems, sobre `drums` | Propio | — | **Reemplazar** |
| Loudness | no existe | ffmpeg `ebur128` o libebur128 | libebur128 MIT; M/S/I/LRA + true peak [A16] | Conformidad con las señales de prueba EBU: NO VERIFICADA en lo leído | **Agregar** |
| Nota kick/rumble | no existe | Método del diseño + corrección D-d + segundo estimador por período (autocorrelación sobre la cola filtrada) | numpy/scipy | Sin benchmark público | **Agregar con validación propia** |
| Stems | no existe | demucs → RoFormer si hace falta | Ver §4 | Ver §4 | **Agregar** (sin cambios al diseño) |
| Patrones | no existe | Onsets por banda plegados a 16 pasos; ADTOF como opción | ADTOF: CC BY-NC-SA, 5 clases [A17] | Techno NO VERIFICADO | **Agregar**; empezar por la versión simple |

**Relación con D-14.** No se propone reabrirla. La arquitectura queda igual.
Sí hay una **propuesta para Gabriel**: leer "songTagger como base" como
"songTagger es el proveedor inicial detrás del adaptador", y permitir que el
adaptador (a) recalcule el BPM, (b) ignore `sections`, `drops` y
`kick_events`, y (c) sume un segundo estimador de tonalidad. Si D-14 se lee
como "la estructura sale de songTagger", este veredicto **la contradice** y
decide Gabriel. Nota práctica: fijar versión exige que songTagger tenga un
commit limpio y un tag; hoy no los tiene (I-6).

#### Plan priorizado

| Orden | Paso | Esfuerzo | Qué destraba |
|-------|------|----------|--------------|
| 1 | **Set de verdad de terreno + arnés de evaluación.** 10–20 tracks peak time anotados por Gabriel en Live: BPM exacto, posición del compás 1, límites de sección en compases con etiqueta (intro/build/drop/break/outro) y, si puede, nota del kick. Más: los 276 nombres de archivo como etiqueta débil de BPM/Camelot (confirmar su origen) y GiantSteps Tempo/Key [A8][A9]. Medir songTagger tal cual como línea de base | S | Todo lo demás: sin esto no se puede afirmar que algo mejoró |
| 2 | **Adaptador con correcciones:** grilla recta por regresión (BPM, fase, residuo), descarte de secciones/kick de songTagger, tonalidad con `bgate` + segundo estimador | S | Corrige C-1, C-3, I-2 e I-3 sin tocar songTagger |
| 3 | **Loudness** (integrado, short-term por compás, LRA, true peak) con carga estéreo | S | Mezcla y master de F4 |
| 4 | **Estructura nueva:** matriz de features por compás, novedad en la grilla de 8 compases, etiquetas por reglas. Comparar contra allin1 en el set del paso 1 | M | Corrige C-2; es lo que más necesita F6 |
| 5 | **Nota de kick y rumble**, validada con kicks sintéticos de frecuencia conocida y con samples del pack que traen la nota en el nombre | M | Criterio de Gabriel (rumble vs kick) para D-13 |
| 6 | Stems, patrones de 16 pasos y swing | M–L | Densidad por elemento; va último porque depende de 2 y 4 |
| 7 | Reproducibilidad: lockfile, versiones en el blueprint, caché por etapa, calibración de confianza con los resultados del paso 1 | S | Tests de contrato de D-14 con sentido |

#### Cómo validar cada mejora

| Medida | Verdad de terreno | Métrica | Umbral sugerido (propuesta, sin fuente) |
|--------|-------------------|---------|------------------------------------------|
| BPM | Anotación de Gabriel; nombres de archivo | Error absoluto | ≤ 0,05 BPM en tempo constante |
| Beats / compás 1 | Warp markers de Gabriel | F de beats (70 ms) [A19]; % de tracks con fase de compás correcta | Fase correcta en todos los tracks del set |
| Tonalidad | GiantSteps Key; Camelot de los nombres | Puntaje ponderado MIREX [A6] | Mejor que la línea de base del paso 1 |
| Secciones | Anotación de Gabriel en compases | Aciertos de límite exacto y a ±1 compás; cantidad de secciones vs anotadas | A definir tras medir la línea de base |
| Loudness | Señales sintéticas de nivel conocido; un medidor de referencia | Diferencia en LU | ≤ 0,1 LU en señales sintéticas |
| Nota kick/rumble | Kicks sintéticos; pack con nota en el nombre | Error en cents; % de errores de octava | ≤ 20 cents y 0 errores de octava en sintéticos |

D-01 sigue mandando: estos números dicen si el motor **mide** bien, no si el
tema suena bien.

### Fuentes de la auditoría

- [A1] https://github.com/mir-aidj/all-in-one ; https://arxiv.org/abs/2307.16425
- [A2] https://github.com/CPJKU/beat_this ; https://arxiv.org/abs/2407.21658
- [A3] https://github.com/CPJKU/madmom
- [A4] https://essentia.upf.edu/reference/std_KeyExtractor.html
- [A5] https://raw.githubusercontent.com/MTG/essentia/master/src/algorithms/tonal/key.cpp
- [A6] https://mir-eval.readthedocs.io/latest/api/key.html
- [A7] https://arxiv.org/pdf/1706.02921 (Korzeniowski y Widmer)
- [A8] https://github.com/deezer/skey ; https://arxiv.org/abs/2501.12907 ; GiantSteps Key: https://zenodo.org/record/1095690
- [A9] https://github.com/GiantSteps/giantsteps-tempo-dataset ; https://ismir2018.ismir.net/doc/pdfs/220_Paper.pdf
- [A10] https://github.com/mir-aidj/all-in-one/issues ; https://pypi.org/project/natten/
- [A11] https://github.com/urinieto/harmonixset
- [A12] https://github.com/urinieto/msaf
- [A13] https://arxiv.org/abs/2007.08411 (Zehren et al., cue points para DJ)
- [A14] https://arxiv.org/abs/2407.06823 (EDM-CUE / CUE-DETR)
- [A15] https://www.itu.int/rec/R-REC-BS.1770
- [A16] https://github.com/jiixyj/libebur128
- [A17] https://github.com/MZehren/ADTOF
- [A18] https://dafx.de/paper-archive/details/dAxTOO3pHjYwTaMRKMs8PQ ; https://www.ismir2015.uma.es/articles/143_Paper.pdf
- [A19] https://mir-eval.readthedocs.io/latest/api/beat.html
- [A20] https://mir-eval.readthedocs.io/latest/api/segment.html

## Motor v1 (T-014)

> 2026-11-22. Paquete `nexo_analysis/` en la raíz del repo, tests en
> `tests/test_nexo_analysis/` (78 verdes, señales sintéticas, sin audio con
> copyright). Se corrió contra el pack Zenhiser Peaktime (solo lectura).
> Salidas reales en `docs/nexo/hallazgos/data/F2_*.json`.

### Qué se construyó

| Módulo | Qué hace |
|--------|----------|
| `loudness.py` | LUFS integrado, curva short-term (ventana 3 s, hop 1 s), LRA, sample peak y true peak. Usa ffmpeg `ebur128=peak=true` si hay ffmpeg y path; si no, cálculo propio (K-weighting de pyloudnorm, gating BS.1770, LRA EBU 3342, true peak por sobremuestreo 4x polifásico). Cada valor trae el método usado en `method` |
| `pitch.py` | Nota fundamental: kick one-shot (salta ~20 ms de ataque, FFT Hann + interpolación parabólica en 30–150 Hz sobre ventanas del cuerpo, mediana del tramo estable, glide con frecuencia instantánea de 3–10 ms, pYIN de librosa como segunda opinión si está instalada), loop de rumble/bajo (mediana de picos por frame de 0,5 s, estabilidad, picos del espectro promedio, picos competidores) y `interval(kick, rumble, target_key)` con el `pitch_coarse` que alinea el rumble al kick y a la tónica de una tonalidad. Regla de octava del audit: pico en f/2 a menos de 12 dB ⇒ se reporta f/2 con confianza baja. CLI: `python -m nexo_analysis.pitch --kick k.wav --rumble r.wav --key "F minor"` |
| `index_pack.py` | `python -m nexo_analysis.index_pack <carpeta> --out x.json [--include nuar]`. Parsea BPM, tonalidad y kit del nombre, clasifica kick/rumble/bass por carpeta y nombre, mide la nota real solo de esos tres, duración en s y compases al BPM del nombre, `name_key` vs `measured_key` y `key_mismatch` |
| `adapter_songtagger.py` + `_songtagger_worker.py` | Único contacto con songTagger (D-14). `wsl.exe -e <songTagger>/.venv-wsl/bin/python worker root audio`. El worker llama a `extract_rhythm`, `refine_beats_madmom` y `detect_key` de songTagger sin modificarlo y expone el BPM de essentia (que su pipeline descarta). El adaptador usa el BPM de essentia, lo contrasta con una grilla recta ajustada sobre los beats de madmom, ignora `sections`/`drops`/`kick_events`, marca el sesgo a modo menor y verifica el hash del commit (`PINNED_COMMIT`, aviso si difiere). Runner inyectable; hay tests de contrato con salida simulada y contra un JSON real de songTagger |
| `blueprint.py` | `python -m nexo_analysis.blueprint <audio> [--role kick/rumble/bass] --out bp.json`. Esquema 0.1 de §8, cada valor `{value, confidence, method}`. No inventa lo que no mide: `sections` queda `[]` y `elements` solo trae el rol pedido, ambos declarados en `warnings` |

Dependencias en `nexo_analysis/requirements.txt` (numpy, scipy, soundfile,
pyloudnorm 0.2.0; librosa opcional). Entorno local `.venv-analysis` (ignorado
por git), Python 3.14 en esta máquina; el código no usa nada posterior a 3.11.

### Números medidos (pack Zenhiser Peaktime, kit `nuar`)

| Archivo | Nombre dice | Medido | Confianza |
|---------|-------------|--------|-----------|
| `kick_one_shot_nuar_G` | G | **G1, 49,01 Hz (+0,3 cents)**; dispersión entre frames 6 cents; glide inicial 2,7 st; pYIN 50,45 Hz (coincide a menos de 100 cents) | alta |
| `134_rumble_loop_nuar_F` | F | **A1, 54,0 Hz (−31 cents)**, pero no es una nota única: picos 54,0 · 44,4 · 76,4 · 66,1 Hz; el de 44,4 (F1 +28/+40 cents) está a 1,5 dB del dominante; estabilidad 0,63 | baja |
| `134_bass_synth_loop_nuar_F` | F | **F2, 86,6 Hz (−14 cents)**; estabilidad 0,37 (el bajo se mueve entre 80 y 100 Hz) | baja |

- Intervalo kick→rumble con la nota dominante medida: el rumble queda **+1,69 st
  sobre el kick** (A1 vs G1); `pitch_coarse` rumble→kick = −2 con residuo
  +31 cents. Contra el bajo (F2): el kick está 2 st sobre F.
- **¿Apoya o contradice "kick −2 st a F para igualar el rumble"?** Apoya la
  mitad kick: G1 = 49,01 Hz, y −2 st da 43,65 Hz = F1 exacto. Sobre el rumble
  **no concluye**: su parcial de F1 existe (44,4 Hz, unos 30–40 cents sobre F1)
  pero la energía dominante está en A1 (~54,7 Hz), y el espectro es un peine de
  líneas cada 2,233 Hz (= 134 BPM; el rumble es un pulso idéntico por tiempo,
  correlación entre pulsos 0,999) entre 42 y 60 Hz, sin fundamental única. El
  F del nombre lo respaldan el bajo del mismo kit (F2) y la tonalidad que
  essentia da para el bajo (F menor). Essentia da **A menor (fuerza 0,65)** para
  el rumble, coincidente con la medición propia. Conclusión práctica: para este
  kit el rumble no se debe afinar "por nota medida" sino por oído contra el
  parcial de F1; el motor lo marca `low` y lista los picos competidores.
- `index_pack` sobre `nuar`: 14 archivos, 4 medidos, 1 desajuste (el rumble,
  A vs F). Duraciones: loops de rumble/bajo 7,164 s = 4,0 compases a 134 BPM;
  atmo, drums, música, stab y perc 14,328 s = 8 compases.
- Adaptador con WSL real (loop de rumble, una corrida): essentia **134,01 BPM**
  (real 134), grilla de beats 133,99 BPM (residuo 2,75 ms), songTagger
  **133,33** (cuantizado, confirma C-1). Pin: HEAD de songTagger igual a
  `71a97430…` (pero con cambios sin commitear, ver I-6). En el loop de bajo
  essentia dio 133,60: en loops cortos (7 s) el BPM del nombre es más fiable.
- Loudness del rumble: −12,8 LUFS, true peak −1,0 dBTP; del bajo: −14,1 LUFS.
  Sin cross-check con ffmpeg (no está instalado), medido con el método numérico.

### Límites (leer antes de confiar en un número)

1. **ffmpeg no está instalado** en esta máquina: LUFS, LRA y true peak salieron
   del método numérico propio. Validado con señales sintéticas (seno estéreo
   −20 dBFS ⇒ −20,0 LUFS; diferencia de 10 LU ⇒ LRA 10 ± 1; pico intermuestra
   ⇒ 0 dBTP ± 0,15) y contra `pyloudnorm` (≤ 0,05 LU). No hay medidor
   certificado de comparación. El true peak numérico descarta 32 muestras por
   borde de archivo (el filtro rebota contra el corte).
2. **Rumbles bombeados:** el sidechain por tiempo crea un peine de líneas cada
   `bpm/60` Hz; con ventanas de 0,5 s la nota sale con error de hasta ~±30
   cents y puede caer en el semitono vecino. Es el límite D-d del audit, no
   un bug: el motor lo informa con `competing_peaks` y confianza `low`, pero no
   lo resuelve. Falta una variante que analice el pulso plegado por compás.
3. Pitch **solo sobre samples aislados**. No hay medición de kick dentro de una
   mezcla ni separación de stems (lo que pide el diseño §3 para referencias).
4. El `glide_st` es de confianza baja (frecuencia instantánea de 3–10 ms con
   filtrado a 250 Hz).
5. El adaptador falla si WSL/essentia no están; en tests corre con runner falso.
   Una sola corrida real. No se midió el tiempo por track. `sections`,
   `drops` y `kick_events` de songTagger se descartan; el reemplazo
   (estructura propia) no está en v1.
6. La tonalidad del adaptador es solo indicativa: el modo siempre sale menor
   (C-3) y no se agregó el segundo estimador.
7. Plataforma: Windows nativo para todo menos el adaptador (WSL). macOS no
   probado ni aplicable al adaptador. El plan gate (`engram/plans/T-014.md`) no
   estaba estampado.
