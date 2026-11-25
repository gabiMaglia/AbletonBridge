# F7 — Tutoriales de YouTube → guías de producción (spike T-028)

> Fecha: 2026-11-24. Canal elegido por Gabriel: **Oscar Underdog** (@OscarUnderdog).
> Extractos crudos (fuente, con citas y timestamps): `docs/nexo/fuentes/youtube/oscar_underdog/*.extract.yaml`.
> Nada de esto se subió todavía al perfil: los cambios los decide Gabriel (D-13, D-01).

## 1. Pipeline probado

| Paso | Herramienta | Costo |
|------|-------------|-------|
| Listar el canal | `yt-dlp --flat-playlist` (solo metadatos) | 0 |
| Bajar texto | `yt-dlp --skip-download --write-auto-subs` (subtítulos automáticos, sin audio) | 0, segundos |
| Limpiar | script propio (dedup de rolling captions, bloques de 30 s con timestamp) | 0 |
| Extraer | 1 agente **Haiku**, esquema fijo: `dicho` / `en_pantalla` / `opinion` + cita verbatim | ~115k tokens Haiku para 5 videos (la transcripción limpia son ~13k; el resto es overhead del agente) |
| Consolidar | orquestador contra `perfiles/techno_peak_time.yaml` | contexto del orquestador |

5 videos = 70 min de video → ~9.900 palabras limpias.

## 2. Rendimiento (lo que define si vale la pena)

| Video | dicho | en pantalla | opinión | huecos visuales |
|-------|------:|------------:|--------:|----------------:|
| Snare rolls (WOiQJSV7hjI) | 11 | 2 | 2 | 4 |
| Kicks con foley (5f_2CcqZ26U) | 10 | 5 | 2 | 5 |
| Mezcla techno en un día (QWgA5l2m2H0) | 2 | 0 | 11 | 2 |
| Dark filters (_aTzO6mdCZQ) | 6 | 3 | 2 | 3 |
| Groove / bounce (7lgyDq8N1J0) | 3 | 2 | 6 | 3 |
| **Total** | **32 (48%)** | **12 (18%)** | **23 (34%)** | **17** |

- **Fidelidad:** 4/4 valores "dichos" verificados textualmente contra la transcripción (55 Hz, 300-500 Hz, 150 Hz, semicorcheas). La extracción barata es confiable en lo que marca como `dicho`.
- **Los tutoriales técnicos rinden; los de filosofía no.** "Easy ideas" (técnica puntual) da 6-11 datos duros; el de mezcla, 2.
- **ASR:** artefactos puntuales ("316th notes") que el extractor marcó como ambiguos en vez de inventar.

## 3. Cruce contra el perfil techno_peak_time

### Confirma (sube confianza si Gabriel acepta)
- **Fundamental del kick 45-55 Hz** ("let's say 55 hertz"). El perfil ya tiene Drum Buss `Boom Freq: 55` y el kick de nuar midió G1 49 Hz → coincide.
- **Semicorcheas como base del roll** (`paso_beats: 0.25`), presente en las etapas del roll del puente.

### Nuevo (el perfil no lo tiene)
- **Kick por zonas:** sub 45-55 Hz · thump 100-200 Hz · click > 200 Hz · bloat a recortar 300-500 Hz (5f_2CcqZ26U 01:30-06:30).
- **Roll con acentos** dentro de las semicorcheas (no solo rampa de velocity) y **reverb que se abre hacia el final del roll** (WOiQJSV7hjI 07:00, 10:00). El perfil tiene el send del roll estático (-16).
- **Roll en loop de 1-4 compases repetido 4 veces antes del break** (WOiQJSV7hjI 06:30-08:00).
- **Filtro oscuro previo al break:** low-pass sobre los graves bajando hasta ~150 Hz, transición de la mitad del largo de la sección; los hats son lo único que conserva agudos (_aTzO6mdCZQ 01:30-09:00). **A/B a oído 2026-11-24:** 8 compases de groove (kick nuar + rumble Audentity "model" + top) → break; sin filtro vs Auto Filter 20 kHz → 150 Hz en compases 5-9 grabado con automation.record sobre kick y rumble → **ganó CON filtro**. En el perfil como `reglas.filtro_oscuro_pre_break` (criterio_gabriel); implementación en el compositor: T-030.
- **Jerarquía de groove por velocity:** downbeat > upbeat > semicorchea débil; acentuar una de cada dos semicorcheas débiles; contorno del shaker baja-media-alta-media (7lgyDq8N1J0). Insumo directo para la épica E-002.

### Contradice / tensiona (decide Gabriel)
- ~~**Dónde recortar el barro del kick:** el perfil hace Bell -2 dB en **250 Hz**; Oscar recorta el bloat en **300-500 Hz**.~~ **DECIDIDO 2026-11-24 a oído (D-01):** A/B en Live con el kick de nuar, Bell -3 dB Q 0,71, 250 Hz vs 390 Hz → **ganó 390 Hz**. Aplicado en `perfiles/techno_peak_time.yaml` (mezcla.plantilla.kick, banda 3) como `criterio_gabriel`. Nota: la profundidad también pasó de -2 a -3 dB, porque así se escuchó.
- **Forma del roll:** el perfil usa un roll que **acelera** (negras → corcheas → semicorcheas → fusas); Oscar usa semicorcheas **constantes con acentos**. **A/B a oído 2026-11-24:** mismo snare (Audentity bright), -17 dB, sin reverb, aterrizando en el compás 17 con el kick → **a Gabriel le gustan AMBOS: conviven**. Variante B probada: loop de 4 compases × 4, acento cada 3 semicorcheas (vel 115 / 75), patrón reiniciado en cada loop. Pendiente: criterio de cuándo usar cada uno (no entra al compositor hasta definirlo).

## 4. Conclusión del spike
El pipeline **vale la pena** con dos condiciones:
1. **Curar videos de técnica puntual** (tipo "Easy ideas"), no de filosofía.
2. **Los huecos visuales son ~1/3 de lo útil:** para los valores que solo están en pantalla, capturar frames de esos timestamps puntuales o que Gabriel los mire.
Costo real dominado por el overhead del agente, no por la transcripción: con un script que llame al modelo directo (sin agente) bajaría mucho.
