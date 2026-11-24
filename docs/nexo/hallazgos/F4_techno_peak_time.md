# F4 — Techno peak time: cómo se produce, mezcla y masteriza

> Investigación web del 2026-11-18. Fuentes numeradas al final ([S1], [S2]...).
> Cada número es un **punto de partida**, no una regla. El oído de Gabriel decide
> (D-01). Lo que no se pudo confirmar dice **NO VERIFICADO**.
> Casi todas las fuentes son tutoriales y blogs, no datos medidos. Las únicas
> estadísticas sobre catálogo real vienen de Mixgraph ([S11]–[S18]).
> Grilla: 16 pasos por compás, pasos 1-5-9-13 = tiempos; 3-7-11-15 = contratiempos.

## 1. Qué es el género

**Beatport** separó el techno en dos categorías a fines de 2020:
"Peak Time / Driving" y "Raw / Deep / Hypnotic" [S39]. La mayoría de los
lanzamientos de techno cae en la primera [S39]. Más tarde se separó también
"Hard Techno" (Mixgraph lo mide aparte [S13]).

Rasgos de peak time según tutoriales: bajos que pulsan, baterías duras,
sintes que evolucionan, energía constante para pista grande y festival [S1].

| Estilo | Tempo típico | Diferencia con peak time |
|--------|--------------|--------------------------|
| **Peak time / driving** | mediana 130 BPM [S11] | Referencia de este documento |
| Raw / deep / hypnotic | 130–140 BPM [S10] | Más experimental, menos "show". Sintes que no suenan a saw/square clásicos, más textura y repetición [S39] |
| Hard techno | mediana 145 BPM [S11]; rango 140–160 [S15] | Más rápido, kick distorsionado, más fuerte (mediana -7,3 LUFS contra -8,6) [S13] |
| Tech house | mediana 126 BPM, mitad entre 124–128 [S16] | Swing y funk de house, el bajo es protagonista, percusión con shuffle; el techno es más recto y mecánico [S16] |

### Drumcode y su sonido

- Sello sueco de **Adam Beyer**, fundado en 1996; en 2026 cumple 30 años [S40].
- Se lo describe como **sello "big room"**: sonido grande, pensado para
  escenarios grandes [S29].
- DJ Mag asocia el "sonido Drumcode" (desde ~2010: Fitzpatrick, Capriati,
  Ben Sims) con **bajos grandes y retumbantes, ritmos con funk y melodías y
  breakdowns dramáticos** [S28].
- Un tutorial de estilo Drumcode (Beyer, Space 92, Eli Brown) lo reduce a:
  bajos que empujan, percusión nítida y texturas vocales hipnóticas, con bajo
  en semicorcheas, acid, lead unísono ancho y stabs de acordes [S2]. Es una
  reconstrucción de aficionado, no palabra de Beyer.
- No se encontró a Beyer describiendo sintes o técnicas de mezcla concretas
  [S28]. **NO VERIFICADO** cualquier "receta oficial".

**Referentes:** Adam Beyer, Enrico Sangiuliano, Amelie Lens, Bart Skils,
Layton Giordani, Eli Brown, Space 92, Kevin de Vries (Drumcode / afines);
Charlotte de Witte (KNTXT); Reinier Zonneveld (Filth on Acid).

## 2. Parámetros globales

| Parámetro | Valor | Fuente / nota |
|-----------|-------|---------------|
| Tempo | **126–135 BPM**, típico **130** | Mediana 130 en 24.997 tracks [S11]. Otra vista de Mixgraph da mediana 126 (120–128) [S12] — **las fuentes no coinciden**. Tutoriales: 126–132 [S1], 128–135 [S5], ~135 Drumcode [S2], 120–135 [S10] |
| Tempo por artista | Lens mediana 133; De Witte mediana 136 | [S17] [S18] |
| Compás | 4/4 | 100% de 443.460 tracks medidos [S14] |
| Tonalidad | Sin estadística confiable | Ejemplos: "Your Mind" (Beyer & Skils) 10A = Si menor [S20]; acid en F# [S3]; kick afinado a F0 [S4]; bajo en G [S7]; bajos en F0 y A0 [S10]. Predominio de menores: **NO VERIFICADO** |
| Rango de nota del bajo | E0–E1 (≈41–82 Hz) | Lo que un sub de club reproduce bien [S10] |
| Duración | ~6–7 min (extended mix) | **NO VERIFICADO**. Ejemplos sueltos de Beatport entre 4:40 y 6:06 |
| Largo de sección | Bloques de 8, 16 o 32 compases | [S10] [S14] |
| Breakdowns | Normalmente 1 grande, a veces 2 | Plantilla de [S10]: intro, breakdown, drop, variación, breakdown, drop, outro. Cantidad típica: **NO VERIFICADO** |

### Estructura de referencia (para 130 BPM, ~6:30)

Plantilla propuesta combinando [S1], [S9], [S10], [S14]. Un compás a 130 BPM
dura 1,85 s; 32 compases ≈ 59 s.

| Sección | Compases | Qué pasa |
|---------|----------|----------|
| Intro DJ | 32 (2×16) | Kick + rumble + percusión mínima; la segunda mitad suma hats/bajo [S1] [S10] |
| Build 1 | 16 | Entran sintes, hats, ride; risers [S1] |
| Drop 1 | 32 | Todos los elementos [S1] |
| Breakdown | 16–32 | Sin kick; queda bajo o synth; últimos 8 compases construyen al drop [S10] [S14] |
| Drop 2 | 32+ | Variaciones, a veces más largo [S10] |
| Outro DJ | 32 | Se quitan elementos de a uno [S1] |

- Los DJs cuentan en frases de 8 compases; los cambios caen en límites de
  8/16/32 [S10].
- Cada 8 o 16 compases entra o sale algo hasta el primer breakdown [S10].
- Umek: tras 16 o 32 compases se quita un kick (hueco de 1 golpe) para soltar
  tensión, y ahí se mete un elemento nuevo [S9].
- En los análisis de Attack, el breakdown arranca en el compás 33 [búsqueda,
  artículos de Lone y ROBPM].

## 3. Por elemento

### Tabla resumen

| Elemento | Patrón (pasos de 16) | Rango útil | Nivel relativo | Entra / sale |
|----------|---------------------|------------|----------------|--------------|
| Kick | 1-5-9-13 | Cuerpo ~65 Hz, punch 80–200 Hz, click ~3,5 kHz [S21] | Referencia (lo más fuerte) | Todo el tema menos breakdown |
| Rumble | Contratiempos o continuo detrás del kick | Sub, LP ~800 Hz [S8] | Bajo el kick | Con el kick |
| Bajo rolling | 16avos, vacío el 1er 16avo de cada tiempo [S7] | HP ~65 / LP ~350 Hz [S7] | Bajo el kick [S36b] | Intro tardía → drops |
| Clap/snare | 5 y 13 | Medios | Medio | Build en adelante |
| Hat cerrado | Contratiempo + 16avos | Agudos | Bajo (vel ≤70%) [S5] | Intro 2ª mitad |
| Hat abierto | 3-7-11-15 [S34] | Agudos | Bajo (vel ~50%) [S4] | Build / drops |
| Ride | Corcheas (pasos impares) [S5] [S10] | HP ~1 kHz [S5] | Bajo | Drops [S1] |
| Percusión / tops | Varios, a veces 3/16 | Medios-agudos | Bajo | Gradual [S2] |
| Stabs / acordes | Sincopados, 1–2 compases | Medios | Medio | Drops |
| Lead / acid | Loop 1–2 compases [S1] | Medios (sin graves) | Medio-alto en drop | Build → drops |
| Pads / atmósfera | Sostenido | Amplio, HP | Muy bajo | Todo el tema [S3] |
| Vocales | Frase corta repetida [S2] | Medios | Medio | Breakdown / drop |
| FX | En límites de frase | Todo | Variable | Transiciones |

### Kick

- **Diseño:** capa grave + capa de transitorio; con EQ se quita lo que se
  superpone [S1]. Ejemplo de cortes: capa grave con LP en 225 Hz, capa de
  ataque con HP en 170 Hz y LP en 9,9 kHz [S22]. Base típica: 909 muy
  comprimido con envolvente de pitch marcada [S5].
- Peak time usa un kick **más corto y con punch** que el raw, pero con mucho
  grave [S10].
- **EQ:** HP 20 Hz (12–18 dB/oct); +1–3 dB en ~65 Hz; recorte en ~400 Hz;
  +1–3 dB en ~3,5 kHz; LP en 15 kHz [S21]. Variante: corte en ~50 Hz y
  -3 dB en ~500 Hz cuando el rumble aporta el sub [S5].
- **Afinación:** resonar el kick en la tónica del tema (ej. F0) con Drum Buss
  o una campana estrecha [S4].
- **Procesamiento:** saturación y compresión rápida [S1]; chequear en mono
  [S1]. Drum Buss de ejemplo: Drive 17%, Boom 45% a 55 Hz, Out -3 dB [S5].
- **Kick fantasma** con baja velocity antes de los tiempos 2 y 4 [S4].
- Un tutorial deja el fader del kick en ~-6 dB para headroom [S3].

### Rumble / sub

- Segundo kick con decay más largo, transitorio quitado [S5], o el mismo kick
  mandado a reverb [S6].
- **Cadena típica** (Attack): kick → send a reverb (preset Dark Hall, send al
  máximo) → overdrive → LP → **sidechain desde el kick** para que bombee [S6].
  Reverb larga y bien húmeda → LP con resonancia y drive < 4 dB → sidechain
  (Kickstart) [S5]. MusicRadar: LP a 800 Hz, 48 dB/oct [S8].
- EQ de bus del kick+rumble: corte ~120 Hz, corte ~800 Hz, shelf +~80 Hz;
  compresión suave ~-5 dB de reducción [S6].
- Tiempos de reverb, predelay y ajustes de sidechain: **NO VERIFICADO**
  (ninguna fuente los da en texto).
- D-07: kick + rumble pueden venir de loops del pack, chopeados.

### Bajo (rolling / offbeat)

- **Patrón rolling:** 16avos con notas cortas (non-legato) [S2]; el primer
  16avo de cada tiempo queda **vacío** (lo ocupa el kick) [S7]. Variante
  offbeat: solo contratiempos (3-7-11-15).
- **Diseño:** saw o square, envolvente de filtro rápida para que se oiga el
  ataque [S7]. Drumcode: mid-bass saw "plucky" + top-bass que copia el patrón
  con saltos de octava [S2].
- **EQ:** HP ~65 Hz, LP ~350 Hz, corte suave en ~100 Hz, boost suave en
  ~330 Hz [S7]. En el estilo Drumcode el mid-bass corta todo el sub [S2].
- Capa de sub separada: LP ~80 Hz, overdrive ~35% wet [S7].
- **Compresión:** OTT Depth 30%, Time 200% [S2].
- **Sidechain:** fuerte y empinado bajo el kick [S2], pero dejando que la cola
  de las notas se superponga un poco [S7]. Otra fuente pide sidechain "que se
  sienta, no que se oiga" [búsqueda, fuente no individualizada] — **las fuentes
  difieren**.
- En breakdowns/builds: automatizar LP [S1]; Umek sube un HP de 25 a 174 Hz y
  lo vuelve a 25 Hz en el golpe siguiente [S9].

### Clap / snare

- Clap en cada segundo tiempo (pasos 5 y 13), usado con mesura [S1].
- Variante de Attack: claps en la grilla de 16 a lo largo de 2 compases, con
  ghost notes de baja velocity alrededor; reverb y delay a ~10% wet [S4].
- Redobles de clap en 16avos en el compás 4 de cada 4, desde el tiempo 2 [S10].
- Snare sincopado en 1.1–1.2 y 2.3–2.4, cada 2 compases [S10].
- Send de reverb de 1–2 s; claps con más send que snares [S10].

### Hats cerrados y abiertos

- **Cerrado:** contratiempo + uno en 16avos rápidos [S4]; velocity ≤70%,
  LP con resonancia 92% y drive 8 dB [S5].
- **Abierto:** en 3-7-11-15 [S34]; velocity ~50%, algunos golpes quitados, el
  del tiempo 2 apenas atrasado [S4]. Decay más corto en el primer golpe y más
  largo en el segundo [S5].
- Mismo grupo de mute (choke) para que el cerrado corte al abierto [búsqueda,
  Attack].
- Micro-timing con LFO sinusoidal sobre el tiempo de un delay 100% wet [S4].

### Ride

- Corcheas, con la segunda de cada par más corta y suave [S5]; o en cada
  corchea con acentos en 1 y 3 [S10].
- HP en 1 kHz, decay apenas acortado, sidechain al kick [S5].
- Delay de 3/16 [S10]. Un ejemplo baja el loop de ride 2 semitonos [S3].
- Entra en secciones clave, sobre todo drops [S1].

### Percusión / tops

- Loops de tops con capas propias y EQ [S1]; reverb corta [S1].
- Shaker en contratiempo, uno de cada dos con menos velocity [S5].
- Un golpe de percusión con reverb al final de cada 4 compases [S3].
- Toms alternados en 16avos con LP de distinta resonancia (groove grave) [S4].
- Se van sumando de a poco [S2].

### Stabs / acordes

- Drumcode: lead + capas percusivas + saws desafinados formando un acorde
  menor, todo a un bus con distorsión, OTT suave, delay ping-pong, boost de
  agudos, reverb y sidechain [S2]. Valores: **NO VERIFICADO**.

### Leads, hooks y acid

- Un loop de 1 o 2 compases alcanza [S1]. Movimiento con LFO/automatización
  de cutoff y resonancia [S1].
- **Lead unísono Drumcode:** 9 voces de unísono una octava abajo + 1 voz,
  distorsión de válvula, OTT, reverb 48% wet con 1,5 s de decay, sidechain
  sutil al 50% [S2].
- **Acid (303):** mono legato, filtro resonante con envolvente corta; low cut,
  boost de medios, OTT, sidechain; una octava arriba [S2]. Abrir/cerrar el
  cutoff en 4–8 compases [S3].
- En Live sin plugins de terceros (P-04): equivalentes nativos a resolver en F5.

### Pads y atmósferas

- Dos capas: una tonal y otra industrial/ruidosa [S2]; ambiente de depósito
  "apenas audible" corriendo todo el tema [S3].
- Pad con trance-gate rítmico, automatizado on/off [S3].
- Saw sweep: LFO de 1 compás abriendo el filtro, reverb + delay pesados [S2].

### Vocales y vocal chops

- Frase corta repetida arriba del arreglo [S2].
- Chop de 2–3 segmentos con delay fuerte para ancho estéreo + reverb [S3].
- Delay de 3/16 [S10] o corchea con puntillo/negra; automatizar el feedback
  en transiciones y cortar cuando vuelve el kick [S33].
- EQ quitando graves, distorsión, ping-pong, reverb, sidechain al kick [S3].

### FX

- **Riser:** ruido blanco con HP automatizado + sintes con pitch-bend [S1].
- **Impactos:** crash/boom; **sub drop** antes del drop [S1]. Impacto largo
  en el tiempo 1 de cada frase de 16 [S10]; sweep metálico cada 8 [S10].
- **Transiciones:** sweeps de impacto y barridos de filtro hacia abajo [S2].
- **Reverse:** kick con reverb >1 s 100% wet, bounce en 8 compases, en
  reversa [S10].
- Bajar el ruido antes del drop para que pegue más [S9].
- Largo exacto del riser (¿8 compases?): **NO VERIFICADO**.

## 4. Groove

| Aspecto | Valor | Fuente |
|---------|-------|--------|
| Swing | **0–20%** en peak time; 50–54% en otro ejemplo | 20% [S4]; 50–54% [S5]; EDMProd: el techno es recto, el swing es de house [S10]. **Las fuentes difieren**: 50–54% en escalas tipo MPC equivale a casi recto (NO VERIFICADO que sea esa escala) |
| Velocity hats | ≤70%, alternar fuerte/débil | [S5] |
| Velocity open hat | ~50% | [S4] |
| Ghost notes | Kick antes de 2 y 4; claps alrededor | [S4] |
| Micro-timing | Open hat del tiempo 2 levemente atrasado; delay modulado en hats | [S4] |
| Polirritmia | Loops de 3/16 contra 4/4; delay de corchea con puntillo; clip de largo impar | [S32]; ride y vocal con delay 3/16 [S10] |

En Live: largo de clip de 3/16 dentro de un 4/4 genera el desfase [S32].
EDMProd sugiere LFOs de filtro en 1/4 o 1/8 y no 3/16 para el bajo [S10].

## 5. Mezcla

| Tema | Recomendación | Fuente |
|------|---------------|--------|
| Gain staging | Pistas entre -12 y -18 dBFS antes de procesar | Blog de baja autoridad (búsqueda) — tomar como guía |
| Elemento de referencia | Kick (o bajo) en -10 dB y armar alrededor | [S36] |
| Kick vs bajo | Kick siempre un poco más fuerte que el bajo | [S36b] (atribución a esa página por fragmento de búsqueda, sin abrirla) |
| Headroom pre-master | Picos del bus master ~-6 dBFS | Varias fuentes (búsqueda) |
| Mono | Todo por debajo de **~100 Hz** en mono | [S23]; otras fuentes 80–120 Hz |
| Sidechain | Bajo, rumble, ride, acid, lead, stabs, vocales, pads al kick | [S2] [S3] [S5] |
| Profundidad del sidechain | Bajo: fuerte; lead: sutil (50%) | [S2]. Ejemplo de -5 a -6 dB de reducción con ataque rápido y release medio [Attack, búsqueda] — **NO VERIFICADO** a qué elemento aplica |
| Alternativa al sidechain | Shaper de transitorios: -3 dB de ataque por 20–30 ms | Búsqueda, fuente no individualizada — **NO VERIFICADO** |
| Afinación | Todo afinado, incluso la batería | [S23] |

**Buses sugeridos** (deducido de [S2] [S5] [S6]):
- **Kick+rumble** (compresión suave, EQ de bus [S6]).
- **Drums/tops** (Drum Buss [S5]).
- **Bass** (mid + top + sub).
- **Music** (stabs a un bus [S2], leads, pads).
- **FX / vocales**.
- **Returns:** reverb corta (plate/room) para percusión [S1], reverb de 1–2 s
  para claps [S10], reverb larga sidechaineada para el rumble [S6], delay
  ping-pong y delay 3/16 [S5] [S10].

Balance espectral por referencia: comparar con un track comercial en lugar de
usar dB fijos [búsqueda]. Encaja con el track de referencia opcional del brief.

## 6. Master

| Parámetro | Club | Streaming |
|-----------|------|-----------|
| LUFS integrado | **-8,6** mediana medida (mitad central -9,9 a -7,6) [S13]; rango de blogs -8 a -6 [S25] | Las plataformas bajan el volumen; se puede usar el mismo master [búsqueda] |
| Short-term en drops | **~-6 LUFS** como techo agresivo [S24] | Igual |
| True peak | **-1 dBTP** (seguro para MP3/AAC) | -1 dBTP |
| Más fuerte | -5 integrado es aceptable en un "banger" de techno [S26]; por encima de -6 suele degradar [búsqueda] | — |

- Ojo: la medición de Mixgraph usa previews de 120 s, o sea **la parte más
  fuerte**, no el track entero [S13].
- **True peak:** con limitador a -1 dBTP, AAC 128 kbps sube en promedio
  +2,3 dB y MP3 320 kbps no sube [S13]. Algunos presets de DJ usan
  -0,3 dBTP [búsqueda]; **las fuentes difieren**.
- **Cadena:** EQ → compresor de glue → (saturación) → limitador [S27].
  Glue: ratio 1,5:1–2:1, ataque ≥30 ms, 1–2 dB de reducción [S27]. Computer
  Music dispara el glue desde el kick, ataque 30 ms, 2:1, release 0,8 s, con
  bombeo deliberado [S27].
- El techno tiene poco rango dinámico entre secciones (LRA bajo) [búsqueda].
- **Evitar:** sobrecomprimir (suena sin vida) [búsqueda]; pasar 0 dBFS [S25].

## 7. Variación por sello

| Sello | Sonido | Tempo | Fuente |
|-------|--------|-------|--------|
| **Drumcode** | Big room; bajo grande y rodante, percusión nítida, leads anchos, breakdowns dramáticos, vocales hipnóticas | ~126–135 (ej. "Your Mind" 126–131) | [S2] [S20] [S28] [S29] |
| **KNTXT** (Charlotte de Witte) | Acid 303 que "chilla", kicks que bombean, vocales etéreas; más oscuro | 135–140; sets en vivo 134–152 | [S18] [S19] [S30]; Lens ~133–140 [S17] |
| **Filth on Acid** (Reinier Zonneveld) | Acid techno, sello fundado en 2017 | Alto, cercano a hard techno: **NO VERIFICADO** | [S31] |

Diferencias de mezcla o master entre sellos: **NO VERIFICADO** (no hay datos).

## 8. Propuesta de esquema de perfil de género (D-03 / P-01)

Formato único. Cada valor lleva `fuente` y `confianza` (alta = medido,
media = varios tutoriales, baja = uno solo o NO VERIFICADO). Las correcciones
de Gabriel (P-02) van en `correcciones_oido` y pisan los valores de base.

```yaml
perfil:
  id: techno-peak-time
  version: 0.1.0
  fecha: 2026-11-18
  beatport: "Techno (Peak Time / Driving)"
  sellos_referencia: [Drumcode, KNTXT, Filth on Acid]
  artistas_referencia: [Adam Beyer, Enrico Sangiuliano, Amelie Lens,
                        Bart Skils, Layton Giordani, Eli Brown, Charlotte de Witte]

global:
  tempo: {min: 126, tipico: 130, max: 135, fuente: [S11, S1, S5], confianza: alta}
  compas: "4/4"
  tonalidad: {preferidas: [menor], ejemplos: [Bm, F#m, Fm, Gm], confianza: baja}
  nota_bajo: {min: E0, max: E1}
  duracion_min: {min: 5.5, tipico: 6.5, max: 7.5, confianza: baja}
  frase_compases: 8
  swing: {min: 0, tipico: 10, max: 20, confianza: baja}

arreglo:              # compases
  - {seccion: intro,     compases: 32, elementos: [kick, rumble, perc_min]}
  - {seccion: build,     compases: 16, elementos: [+hats, +bajo, +riser]}
  - {seccion: drop1,     compases: 32, elementos: [todo]}
  - {seccion: breakdown, compases: 32, elementos: [-kick, bajo_o_synth, pad, vocal]}
  - {seccion: drop2,     compases: 32, elementos: [todo, variacion]}
  - {seccion: outro,     compases: 32, elementos: [quitar_de_a_uno]}
  reglas:
    - "cambio cada 8 o 16 compases"
    - "impacto en tiempo 1 de cada frase de 16"
    - "ultimos 8 compases del breakdown construyen al drop"

elementos:
  kick:
    patron: [1, 5, 9, 13]
    eq: {hp_hz: 20, cuerpo_hz: 65, corte_hz: 400, click_hz: 3500, lp_hz: 15000}
    afinar_a_tonica: true
    saturacion: media
    nivel: referencia      # 0 dB relativo
    seccion: {sale_en: [breakdown]}
  rumble:
    fuente: "reverb del kick | kick largo | loop del pack"
    cadena: [reverb_larga, overdrive, lp_800hz_48db, sidechain_kick]
    nivel_rel_db: null     # NO VERIFICADO
  bajo:
    tipo: rolling
    patron: "16avos, vacio el 1er 16avo de cada tiempo"
    eq: {hp_hz: 65, lp_hz: 350, corte_hz: 100, boost_hz: 330}
    sidechain: fuerte
    nivel_rel_db: null     # "un poco bajo el kick"
  clap: {patron: [5, 13], reverb_s: [1, 2], seccion: {entra_en: build}}
  hat_cerrado: {patron: "contratiempos + 16avos", vel_max: 0.7}
  hat_abierto: {patron: [3, 7, 11, 15], vel: 0.5, choke_con: hat_cerrado}
  ride: {patron: "corcheas", hp_hz: 1000, delay: "3/16", seccion: {entra_en: drop}}
  perc: {patron: libre, polirritmia: "3/16", reverb: corta}
  stab: {largo_loop_compases: [1, 2], bus: music, sidechain: medio}
  lead: {largo_loop_compases: [1, 2], reverb: {wet: 0.48, decay_s: 1.5}, sidechain: 0.5}
  acid: {mono_legato: true, mover_cutoff_compases: [4, 8]}
  pad: {nivel: muy_bajo, seccion: {presente: siempre}}
  vocal: {tipo: "frase corta repetida", delay: ["3/16", "1/8D"]}
  fx: {riser: "ruido blanco + HP", impacto: "tiempo 1 frase 16", sub_drop: "antes del drop"}

mezcla:
  referencia: {elemento: kick, nivel_dbfs: -10}
  mono_bajo_hz: 100
  headroom_pre_master_dbfs: -6
  buses: [kick_rumble, drums, bass, music, fx_vocal]
  returns: [reverb_corta, reverb_1_2s, reverb_larga_sc, delay_pingpong, delay_3_16]

master:
  club: {lufs_integrado: [-9.9, -7.6], tipico: -8.6, lufs_short_drop: -6, true_peak_dbtp: -1.0}
  streaming: {mismo_master: true}
  cadena: [eq, glue_2a1_30ms_1a2db, saturacion_opcional, limitador]

correcciones_oido: []   # P-02: fecha, track, que dijo Gabriel, que se cambio
```

## 9. Pendiente / NO VERIFICADO

- **Tonalidades frecuentes:** no hay estadística de peak time. Medir con
  songTagger (A-01) un set de 30–50 tracks Drumcode/KNTXT.
- **Tempo:** dos medianas de Mixgraph distintas (130 vs 126) [S11] [S12].
- **Duración total** y **largo real de secciones**: falta medir tracks reales.
- **Cantidad de breakdowns** típica.
- **Niveles relativos en dB** entre elementos (bajo, hats, clap vs kick):
  ninguna fuente los da. Proponer: medir stems o tracks de referencia.
- **Ajustes de sidechain** (ratio, attack, release, dB) por elemento.
- **Tiempos de reverb del rumble** (decay, predelay).
- **Swing:** valores contradictorios (20% vs 50–54%), falta saber la escala.
- **Filth on Acid:** tempo y rasgos de producción.
- **Diferencias de mezcla/master por sello.**
- **Largo de risers** y armado exacto de la transición al drop.
- Escala de velocity, presets nativos de Live para cada elemento → F5.
- Varias fuentes de foro/blog de baja autoridad (gain staging -12/-18,
  -0,3 dBTP, sidechain sutil) solo se vieron en resultados de búsqueda.

## Fuentes

- [S1] https://www.beatportal.com/articles/783088-step-by-step-guide-to-producing-techno-peak-time-driving-in-the-style-of-layton-giordani-eli-brown-and-adam-beyer
- [S2] https://theproducerschool.com/blogs/featured-blogs/how-to-create-techno-beats-inspired-by-drumcode-artists
- [S3] https://theproducerschool.com/blogs/featured-blogs/how-to-create-techno-music-like-charlotte-de-witte
- [S4] https://www.attackmagazine.com/technique/beat-dissected/rolling-techno/
- [S5] https://www.attackmagazine.com/technique/beat-dissected/dark-techno-rumble/
- [S6] https://www.attackmagazine.com/technique/tutorials/adding-reverb-techno-kick/
- [S7] https://www.attackmagazine.com/technique/tutorials/warehouse-rolling-techno-bass/
- [S8] https://musicradar.com/how-to/how-to-create-rumbling-techno-kick-drums-with-reverb
- [S9] https://www.musicradar.com/tuition/tech/umeks-guide-to-breakdowns-510309
- [S10] https://www.edmprod.com/how-to-make-techno/
- [S11] https://www.mixgraph.io/glossary/peak-time
- [S12] https://www.mixgraph.io/artists/new-echo
- [S13] https://www.mixgraph.io/tools/lufs-meter
- [S14] https://www.mixgraph.io/glossary/breakdown
- [S15] https://www.mixgraph.io/bpm-for
- [S16] https://www.mixgraph.io/bpm-for/tech-house y https://www.zipdj.com/?p=37355
- [S17] https://www.mixgraph.io/artists/amelie-lens
- [S18] https://www.mixgraph.io/tracks/charlotte-de-witte-formula
- [S19] https://mixprism.eu/set/charlotte-de-witte-at-tomorrowland-belgium-2025-main-stage-c-fjnSF0K7
- [S20] https://www.mixgraph.io/tracks/adam-beyer-your-mind y https://www.drumcode.se/releases/your-mind
- [S21] https://www.musicguymixing.com/?p=1616
- [S22] https://audiotent.com/blogs/production-tips/layering-processing-techno-kick
- [S23] https://www.aulart.com/hannes-bieger-4-techno-tips/
- [S24] https://www.masteringthemix.com/blogs/learn/am-i-mastering-loud-enough-how-to-hit-the-perfect-lufs-every-time
- [S25] https://www.samplesoundmusic.com/blogs/news/mastering-techno-loudness-dynamics-and-club-readiness
- [S26] https://www.edmprod.com/lufs/
- [S27] https://violetrecording.com/mastering-chain-explained/ y https://www.pressreader.com/australia/computer-music/20170907/283622465248954
- [S28] https://djmag.com/longreads/adam-beyer-technos-uncompromising-kingpin (403; leído solo por fragmento de búsqueda)
- [S29] https://elektrodaily.com/drumcode-feature-and-wmc-label-showcase-review/
- [S30] https://mixmag.asia/read/charlotte-de-witte-reveals-new-ep-apollo-news
- [S31] https://wikipedia.com/wiki/Reinier_Zonneveld
- [S32] https://makingmusic.ableton.com/asynchronous-or-polyrhythmic-loops
- [S33] https://output.com/blog/best-techno-vocal-plugins
- [S34] https://www.aulart.com/create-a-detroit-techno-pattern-with-the-tr-909
- [S36] https://www.waves.com/how-to-mix-electronic-music
- [S36b] https://www.productionmusiclive.com/blogs/news/10-mixing-tips-from-jonas-saalbach-radikon
- [S39] https://www.beatportal.com/articles/440314-beatport-is-expanding-its-techno-categories
- [S40] https://www.beatportal.com/articles/1718221-drumcode-celebrates-30-years-with-20-track-compilation-featuring-amelie-lens-alan-fitzpatrick-nicole-moudaber-and-more
- Otras consultadas sin datos útiles: https://mixedinkey.com/captain-plugins/wiki/how-to-arrange-a-dance-music-track/ ,
  https://kapiko.pages.dev/genres/techno/ (datos contradictorios, descartada).

## Criterios de Gabriel (observados en sus sets)

> Primeras entradas para P-02. Fuente: lectura con `state.detail` de su loop
> `TESTLOOP` (2026-11-22) y su explicación.

Cada criterio pasa por el filtro D-13: web + referencias medidas.

| Fecha | Criterio | Evidencia | Filtro web | Filtro referencias | Estado |
|-------|----------|-----------|------------|--------------------|--------|
| 2026-11-22 | **El rumble se afina de oído, sobre todo contra el kick**, aunque la tonalidad del nombre del archivo diga otra cosa (rumble "A#" transpuesto -3 st). Hay que medir la nota real del kick y del rumble y alinearlas. | `TESTLOOP`: rumble -3 st | **Coincide.** El rumble se construye desde el kick (otro kick de cola larga, reverb o Drum Buss resonando en la nota del kick) y hay herramientas que detectan la nota del kick para afinar el rumble [MusicRadar, Attack, KVR T-Rumble]. Matiz: varias fuentes afinan primero el **kick a la tonalidad del tema** (raíz, 5ta o 7ma, no hay acuerdo) y el rumble lo sigue. | Pendiente (F2) | Confianza alta |
| 2026-11-22 | Warp **Complex** para rumble y voz; **Beats** para loops rítmicos y de synth. | `TESTLOOP` | **Coincide en parte.** Beats para material rítmico: acuerdo general. Complex/Complex Pro para voz: recomendado. Para material con nota definida y monofónico (bajo, voz) varias fuentes prefieren **Tones**; Complex para material mezclado. Un rumble de loop (kick + cola) es material mezclado, así que Complex es razonable. Todas coinciden en que decide el oído [Ableton manual, Soundfly, Ask.Audio, foro Ableton]. | Pendiente (F2) | Confianza media: comparar Complex vs Tones en rumbles limpios |
| 2026-11-22 | **High-pass al kick en los builds**, combinado con el filtro que sigue al riser: el HP arranca 2–3 golpes después de que se cierra el filtro, sube durante el build (adelgaza el kick) y vuelve de golpe a cero en el drop. | Técnica propuesta por Gabriel (T02) | Pendiente | Pendiente | Confianza alta (técnica de Gabriel) |
| 2026-11-22 | **Pregunta y respuesta voz/stab: rechazada en el STAB** (Gabriel estiró los clips de nuevo: "no me gustó el recurso en ese instrumento"). | Prueba en T02 | — | — | Confianza alta |
| 2026-11-22 | Aprobados por Gabriel: corte de 2 tiempos antes del Main (queda el snare fill); FX variados por transición; elementos nuevos entran con filtro que abre en 8 compases; ecos de delay en voces al final de frase; filtro siguiendo al riser (cierra en 1 tiempo, abre en curva). A probar: pregunta y respuesta voz/stab. Pide **mejor mezcla de voces**. | Respuestas de Gabriel (preguntas T-015) | — | — | Confianza alta (aprobados) |
| 2026-11-22 | **Último compás del tema: kick entero**, sin hueco ni fills (salida limpia para el DJ). | Respuesta de Gabriel (pregunta T-015) | — | — | Confianza alta |
| 2026-11-22 | Rumble y bajo **solo se sacan en el fin de 32 que entra al Main** (compás 64); en los demás fines de 32 se mantienen (solo cae el kick). | Respuesta de Gabriel (pregunta T-015) | — | — | Confianza alta |
| 2026-11-22 | **Filtro con resonancia siguiendo al riser:** Auto Filter LP 24 dB (SVF), resonancia ~29 %, drive ~14 % en capas atmosféricas, coro y fills; corta los agudos rápido y los vuelve a abrir **sincronizado con el movimiento del riser** (donde termina y empieza el sonido, se filtra todo). Fills de snare a ~-17 dB (a -14 estaban muy fuertes). | Arreglo hecho por Gabriel en T02 | Pendiente | Pendiente | Confianza alta (hecho por Gabriel) |
| 2026-11-22 | **Puente = tensión continua.** Todo el puente progresa; los elementos **entran de a poco, siempre**. La única excepción: un elemento puede entrar de golpe si es la **culminación de un riser**. | Feedback de Gabriel sobre el puente de T02 | Pendiente (investigación en curso) | Pendiente (F2) | Confianza alta |
| 2026-11-22 | **Movimiento constante (emoción en todo el tema).** El tema siempre va de un punto a otro: hay que recrear sensación de movimiento **dentro del loop** para no perder la atención del público. Progresiones dentro de 8/16/32 compases: una progresión aislada se vuelve más compleja en la siguiente iteración o con la entrada de un sonido. **Todo dialoga con todo**, con coherencia musical y transiciones suaves entre sonidos. | Explicación de Gabriel sobre T02 | Pendiente | Pendiente (F2: medir variación por frase en referencias) | Confianza alta (criterio central de Gabriel) |
| 2026-11-22 | **Se produce por capas**, una sobre otra, hasta el producto final. Un tema armado solo con loops "no está mal" pero le falta **emoción**: más **risers**, **automatizaciones** y **mezcla**. | Feedback de Gabriel sobre T02 | Pendiente | — | Confianza alta (criterio de método) |
| 2026-11-22 | Un loop puede armarse **sin devices**: solo elección de loops, warp, transposición y volumen. | `TESTLOOP` | **Válido como boceto, no como tema terminado.** Las fuentes de F4 ponen procesamiento como parte del género (sidechain, saturación, bus de drums, master). | — | Observación, no criterio |

Fuentes del filtro:
- https://musicradar.com/how-to/rumbling-techno-kick
- https://www.attackmagazine.com/technique/beat-dissected/dark-techno-rumble/
- https://www.attackmagazine.com/technique/beat-dissected/rolling-techno/
- https://www.kvraudio.com/product/t-rumble-by-q-audio/details
- https://futureproofmusicschool.com/blog/making-hard-techno-a-path-to-unique-sound-design
- https://community.vcvrack.com/t/how-to-make-techno-kick-with-rumble-bass/7656
- https://www.ableton.com/de/manual/audio-clips-tempo-and-warping/
- https://flypaper.soundfly.com/produce/how-to-warp-audio-in-ableton-live/
- https://ask.audio/articles/effective-warping-tips-in-ableton-live-9
- https://forum.ableton.com/viewtopic.php?p=800299

## Detalles de arreglo: variaciones, fills, tensión y transiciones (investigación 2026-11-22)

> Investigación web del 2026-11-22. Responde al criterio **Movimiento constante**
> de Gabriel y al feedback sobre T02: loops + "escalera" de filtro = estático.
> Fuentes numeradas [T1]...[T30] al final de esta sección. Como en el resto del
> documento, cada número es un **punto de partida**. Lo que solo se vio en un
> fragmento de búsqueda se marca *(fragmento)*; lo que no tiene fuente dice
> **NO VERIFICADO**.
> Hallazgo general: **no se encontró ninguna entrevista** de Beyer, Sangiuliano,
> Lens, De Witte, Zonneveld o De Vries con reglas concretas de arreglo (compases,
> fills, dB). Lo más cercano: De Witte pide "seguir modulando y dando forma a la
> percusión básica" para que el tema fluya [T12]. Todo lo demás viene de
> tutoriales (Attack, MusicRadar, EDMProd) y foros.

### Filtro web del criterio "Movimiento constante"

**Coincide.** Las fuentes repiten la misma idea con otras palabras:

- Las transiciones son donde se pierde o se gana un tema; es fácil hacer
  discos aburridos si no se les dedica tiempo [T6] *(fragmento de Future Music
  vía búsqueda)*.
- Solo sumar y quitar partes es "super aburrido"; hacen falta patrones
  intermedios con un fill o un acorde distinto al final [Gearspace, fragmento].
- Más útil que sumar capas: **cambiar el material que ya suena** (acortar un
  bajo de 2 compases a medio compás y después volver a abrirlo; un break de
  batería de medio compás que se expande después) [T15].
- Conservar los acordes y cambiar su ritmo (de pluck a notas largas) da una
  sección nueva coherente con la anterior [T25].
- El tema puede vivir de pocos elementos si los efectos y la automatización
  cambian: BEC arma un track de 15 elementos con un motivo de 2 notas y la
  tensión sale de reverb y cutoff que se abren hacia el drop [T13].

Esto confirma lo que Gabriel describe: **la progresión está dentro del loop**
(parámetros, notas, largo de clip), no solo en la entrada y salida de pistas.

### 1. Cómo se mantiene vivo un loop

#### Jerarquía de cambios por frase

La referencia más concreta es un usuario del foro de Ableton (ethios4), que
presenta su esquema como punto de partida que "imita el fraseo natural" [T15]:

| Compás dentro de un ciclo de 32 | Qué pasa |
|---------------------------------|----------|
| 4, 12, 20, 28 | Cambio chico |
| 8, 24 | Variación pequeña |
| 16, 32 | **Fill de batería** |

Encaja con lo que ya está en este documento: algo entra o sale cada 8 o 16
compases [S10] [T27 *(fragmento)*]; golpe de percusión con reverb al final de
cada 4 compases [S3]; redoble de clap en el compás 4 de cada 4 [S10].

#### Micro-variación (cada compás o cada 2)

| Técnica | Valor | Fuente |
|---------|-------|--------|
| **Cortes de fin de compás**: quitar capas del hat en el tiempo 4 de cada compás; acortar el loop de percusión para que pare en el tiempo 4; tape-stop (fade-out corto con caída de pitch) en un loop de audio | Cada compás | [T9] |
| Muteo del **bajo en el tiempo 4** del último compás | Cada 8 compases (ciclo de acordes) | [T9] |
| Velocity aleatoria (Velocity MIDI effect con Random) y phaser sutil | Continuo | [T15] |
| LFOs y step sequencers aleatorios sobre la batería para "humanizarla" (Secret Cinema) | Continuo | [T13] |
| Tremolator (Soundtoys) para un efecto aleatorio en hats y claps (De Witte) | Continuo | [T12] |
| Envolvente de clip con largo que **no divide** al loop (ej. volumen sobre un loop de 4 compases) para que la repetición nunca sea idéntica | Continuo | [T15] |
| Paneo que cambia cada 2 compases | Cada 2 | [T18] (fuente de baja autoridad) |
| Capa extra en uno de cada 2 o 4 claps, desafinada | Cada 2–4 tiempos | [T7] |
| Llamado y respuesta entre dos loops que se alternan, o dos claves aguda/grave | Cada compás o 2 | [T23] [T24] *(fragmentos)* |

#### Macro-movimiento (8–32 compases)

| Técnica | Valor | Fuente |
|---------|-------|--------|
| Filtro que se abre de oscuro a brillante | 4–8 compases | [T18] |
| Movimientos lentos apilados: filtro +5% cada 8 compases; el cambio acumulado en 32 se nota | 8 / 32 | [T18] |
| Distorsión del bajo subiendo de a poco | 8 compases | [T18] |
| Filtro (cutoff) automatizado para crear tensión | 16 o 32 compases | [T28] *(fragmento)* |
| Cutoff resonante que sube "unos compases" y vuelve | 2–4 compases (NO VERIFICADO el número; la fuente dice "a few bars") | [T17] |
| Envío de delay más alto cuando el tema está "a pleno o construyendo", más bajo en partes calmas | Por sección | [T17] |
| Acid: abrir/cerrar cutoff | 4–8 compases | [S3] |
| Automatización distinta grabada en cada sección de 16 (estilo Jeff Mills) | Cada 16 | [T28] *(fragmento)* |

**Densidad de cambios:** ninguna fuente da un número de "cambios por compás".
El dato más concreto es la jerarquía de [T15] y que beatkitchen usa ejemplos
con **3 automatizaciones simultáneas** en líneas de tiempo separadas [T18].
Cantidad ideal: **NO VERIFICADO** — medir en referencias (F2).

#### "Eventos únicos" (ear candy)

Ableton (*Making Music*) los llama **unique events** y los divide en tres [T16]:

1. **Evento suelto:** un golpe, nota o acorde de un instrumento que no suena en
   el resto del tema. En un límite de sección suena a transición; fuera de
   la grilla, a sorpresa.
2. **Gesto musical:** cambio de notas de una sola vez dentro de un patrón
   repetido. Cambiar notas a mitad de frase sorprende más que cerca de la
   transición.
3. **Gesto de procesamiento:** una cadena de efectos en bypass que se enciende
   una vez y se apaga. Si es muy corto o cae en un lugar raro de la frase,
   llama más la atención.

Regla: **usarlos con moderación**; si hay demasiados, el oyente espera lo
inesperado y se pierde el efecto [T16]. Ejemplos de duración: una cola de
reverb de medio segundo en un solo snare, un bitcrusher de 2 tiempos [T18].

### 2. Fills y marcas de fin de frase

#### Huecos de kick y silencios

| Técnica | Dónde / cuánto | Fuente |
|---------|----------------|--------|
| Quitar **un kick** tras 16 o 32 compases para soltar tensión, y en el hueco meter algo nuevo (synth, bajo, ruido, crash) | Fin de frase de 16/32 | [S9]/[T11] (Umek). Qué tiempo exacto: no lo dice |
| Quitar el kick al final de una frase de 8 + crash al inicio de la siguiente | Fin de frase de 8 | [T22] *(fragmento, foro)* |
| Mutear un elemento (kick o snare) o un grupo entero (drums, bass) en el **último** tiempo o compás antes de la sección, **o** en el **primer** tiempo o compás de la nueva | 1 tiempo o 1 compás | [T6] |
| Mutear todo unos tiempos y dejar un vocal, sample o stab de bajo solo | "unos tiempos" | [T6] |
| **Anacrusa:** mutear todo **2 tiempos** antes del primer tiempo fuerte, que se escuche solo la nota de entrada | 2 tiempos | [T6] |
| En los últimos tiempos antes del breakdown: mutear canales y envíos de reverb, dejar solo un fill; la reverb vuelve en el drop | "un par de tiempos" | [T5] |
| Bajo muteado un instante: "se siente más pesado" cuando vuelve | Breve | [T29] *(fragmento, MusicTech)* |

#### Fills de batería y redobles

| Técnica | Valor | Fuente |
|---------|-------|--------|
| Fill en el **último compás** del build con sonidos que **no** están en el groove principal | 1 compás | [T5] |
| Una edición distinta en **cada tiempo** del último compás (glitch con mesura) | 4 edits | [T5] |
| Redoble de snare en 16avos sobre los **2 últimos compases** de la intro, con +~2 dB de volumen y sustain en subida | 2 compases | [T6] |
| Redoble con rampa de velocity **1 → 127** | 1 compás o más | [T2] |
| Redoble que acelera: negras → corcheas → 16avos (sin cambiar tempo) | — | [T2] |
| Redoble que **para en 2.4** (tiempo 2, último 16avo) y deja una pausa; rellenarla con un sonido "chocante" | Pausa de largo no dado | [T2] |
| Velocity: primera de cada grupo de 4 fuerte, las otras 3 más suaves | — | [T2] |
| Mismo snare en 3 notas MIDI con EQ distinta, velocity variada en las primeras 6 notas del patrón de 16avos | — | [T7] |
| Ride con caída de pitch automatizada como fill antes del drop | Compás 3 | [Attack Spastik, fragmento] |

#### FX de transición

| FX | Valores | Fuente |
|----|---------|--------|
| **Crash** en el tiempo 1 de la sección de 8 o 16 | — | [T6] |
| **Reverse cymbal** al final de secciones de 8 o 16 compases; termina justo al final del compás, lleva al tiempo 1 | Reverb plate ~30% wet, 1 s | [T6] [T4] |
| Reverse crash "largo": reverb 15,3 s, room 93%, 100% wet, invertido, pico justo antes del drop, **corte bajo 300 Hz** | — | [T8] |
| **Ruido blanco** con HP automatizado **1 kHz → 10 kHz** en un MIDI de **8 compases** | 8 compases | [T8] |
| Ruido en bandpass con cutoff que sube; reverb hall ~3 s | — | [T4] |
| **Faller** (ruido blanco que baja) marcando el inicio del drop | — | [T1] |
| **Delay throw:** subir el envío en la última palabra o golpe de la frase para que se oigan las repeticiones; automatizar feedback | Último golpe | [T26] *(fragmento)* |
| Pitch-down de hat o ride en transiciones, volver a 0 después | 4–8 compases | [T7] |
| **Beat Repeat** en 1/16 con Chance 100% para transiciones; encenderlo/apagarlo con automatización | — | [T30] *(fragmentos)* |
| **Gate rítmico** (Volcano "Chopped") en el master solo durante el último acorde antes del drop | 1 acorde | [T3] |
| Comb filter en la batería de **~100 Hz a 3 kHz** durante el breakdown sin kick | Breakdown | [T3] |

#### Cómo escala con el largo de frase

Ninguna fuente da una tabla 8 vs 16 vs 32. Lo que sí sale de [T15], [S9],
[S10], [T6] es una **regla de proporción**: cuanto más larga la frase que
termina, más grande el marcador (cambio chico → variación → fill → hueco de
kick + elemento nuevo). Valores exactos por nivel: **NO VERIFICADO** — ver la
plantilla de la sección 5, que los propone.

### 3. Tensión y liberación

#### Armado del breakdown (dos análisis de Attack [T1])

| Track | Largo | Cómo crece |
|-------|-------|------------|
| Hayden James – "Good Life" | **24 compases = 3 × 8** (~50 s) | 1–8: progresión original. 9–16: progresión nueva que comparte los 2 primeros acordes. 17–24: **un solo acorde repetido** ("el oyente empieza a extrañar la progresión completa" → tensión). Últimos 4 compases: kick y vocal pasan de negras a **corcheas**. Todo salvo el piano se corta **2 tiempos antes** del final del compás 24. Redoble termina en 32avos. Piano con high-cut en los últimos 8 |
| HI-LO – "Kronos" | **32 compases** (~61 s) | Arranca solo con clap en 2 y 4; el bajo pierde los graves. Fills de bajo desde el compás 9. Entra hat en contratiempo. Redoble que sube de volumen en compases 16–24 y **se corta ~2 s antes** del drop. Últimos 8: pad más difuso (reverb grande). Riser + sweep que quita graves hasta el drop; el regreso de los graves = "impacto" |

Para peak time el breakdown es de 16–32 compases y los últimos 8 construyen al
drop [S10] [S14]; los dos ejemplos de arriba encajan en ese rango.

#### Build

| Recurso | Valor | Fuente |
|---------|-------|--------|
| Largo del build | **8 compases** como default seguro | [T14] |
| HP sobre los acordes | **200 Hz → 20 kHz** a lo largo del breakdown | [T8] |
| HP sobre la batería | **250 Hz** encendido durante los compases previos al drop (ejemplo: 15–17), apagado en el drop | [T5] |
| HP en el bajo (Umek) | **25 → 174 Hz** en el break, vuelve a 25 Hz **en el golpe siguiente** | [S9] |
| HP general | Quitar < **100 Hz** en el build crea el hueco que el drop llena | [T14] |
| HP en master | Sube de a poco y se **apaga** en el drop | [T3] |
| Reverb larga en build | Predelay ~7,5–8 ms, decay ≥ 6 s; subir el envío y volverlo a normal **antes** del drop | [T7] [T8] |
| Decay/release de synth | Subirlos antes del break, bajarlos para el drop | [T7] |
| Volumen general | Bajar "unos dB" a lo largo del breakdown y volver a pleno en el drop (dB exactos: NO VERIFICADO) | [T14] |
| Ruido | Bajar el ruido en el break chico para que el drop explote más | [S9] |
| Regla | El build **nunca** debe sonar más fuerte que el drop | [T14] |
| Macro de tensión | 0 → 100 a lo largo del build, vuelve a 0 en el drop | [T18] |

#### Silencio antes del drop

| Largo | Fuente |
|-------|--------|
| **2 tiempos** (todo salvo un elemento) | [T1] (Hayden James), [T6] (anacrusa) |
| **Medio compás o 1 compás**, con una cola de reverb para que no sea "aire muerto" | [T14] (EDM en general, no techno) |
| Redoble que para en **2.4** del último compás | [T2] |
| "Fake drop": se niega el drop unos tiempos más | Fragmento de búsqueda, NO VERIFICADO |

#### Impacto del drop

Vuelven los graves y el kick [T1] [T14]; faller o crash en el tiempo 1 [T1]
[T6]; la reverb que se había apagado vuelve en el drop [T5]; impacto largo en
el tiempo 1 de cada frase de 16 [S10]. Un elemento nuevo (ej. un vocal) puede
aparecer completo justo antes del drop o insinuarse durante el build [T5].

### 4. Interacción y entrada de elementos

| Técnica | Detalle | Fuente |
|---------|---------|--------|
| **Filter-in con HP** | Una parte con muchos agudos entra con HP en **8 compases**; la resonancia se sube donde suena bien y se baja para no disparar picos. Evitar automatizaciones en línea recta | [T10] |
| Bajo filtrado | Igual que el lead, pero el filtro se mueve **más rápido al final** de la frase para que el sub pegue | [T10] |
| Salida | La misma transición **en reversa** saca el elemento al final de la sección (mejor en pads y bajos) | [T10] |
| Fade largo | Synth o capa rítmica nueva con volumen o filtro en **32 o 64 compases** (contexto minimal) | MusicRadar minimal *(fragmento)* |
| Melodía filtrada (Umek) | 16 compases después del hueco de kick entra filtrada y se abre de a poco | [S9] |
| Insinuar el riff | Entra y sale el riff principal; la versión completa aparece a **2/3** del tema | [T15] |
| Kick suave primero (Umek) | El kick del principio es más corto y débil; después se cambia por uno más grande | [S9] |
| Llamado y respuesta | Dos loops alternados; claves aguda/grave que se contestan; claps en redoble como respuesta al snare | [T23] [T24] *(fragmentos)* |
| Entrada a mitad de tiempo (half-time) en la primera pasada | **NO VERIFICADO** — no se encontró fuente | — |

### 5. Plantilla por nivel de frase (para aplicar automáticamente)

Leyenda: **A** = automatización de audio (envolvente o parámetro de device);
**E** = edición de arreglo (cortar, mutear, mover, duplicar, cambiar notas);
**S** = sample o clip nuevo (one-shot, FX). Los valores con fuente salen de las
tablas de arriba; los marcados **(propuesta)** son elección de diseño para el
sistema, **no** vienen de la web y los decide el oído de Gabriel.

#### Nivel 1: dentro de cada compás / cada 2 compases (micro)

| # | Acción | Tipo | Valor | Origen |
|---|--------|------|-------|--------|
| 1.1 | Quitar capa de hat o cortar perc en el tiempo 4 | E | Algunos compases, no todos (propuesta) | [T9] |
| 1.2 | Velocity con aleatoriedad leve en hats/perc | E | Rango: NO VERIFICADO | [T15] |
| 1.3 | Envolvente de largo impar sobre volumen o filtro de una perc | A | Largo que no divida 4 compases (ej. 3 o 5 tiempos, propuesta) | [T15] |
| 1.4 | Llamado y respuesta entre 2 percusiones | E | Alternar cada 1–2 compases | [T23] |

#### Nivel 2: fin de frase de 8 compases

| # | Acción | Tipo | Valor | Origen |
|---|--------|------|-------|--------|
| 2.1 | Variación pequeña: cambio de notas o de patrón en el compás 8 | E | 1 compás | [T15] [T16] |
| 2.2 | Mutear el bajo en el tiempo 4 del compás 8 | E | 1 tiempo | [T9] |
| 2.3 | Reverse cymbal que termina en el final del compás 8 | S | 1 compás (propuesta) | [T6] [T4] |
| 2.4 | Delay throw en el último golpe de un stab/vocal | A | Envío arriba 1 golpe, abajo en el tiempo 1 | [T26] |
| 2.5 | Filtro lento de un elemento: un paso más abierto | A | +5% por cada 8 compases | [T18] |
| 2.6 | Sweep metálico | S | Cada 8 | [S10] |

#### Nivel 3: fin de frase de 16 compases

| # | Acción | Tipo | Valor | Origen |
|---|--------|------|-------|--------|
| 3.1 | **Fill de batería** en el compás 16 con sonidos que no están en el groove | E/S | 1 compás | [T15] [T5] |
| 3.2 | Redoble de clap en 16avos desde el tiempo 2 del compás 16 | E | 3 tiempos | [S10] |
| 3.3 | **Hueco de kick**: quitar 1 kick en el último compás (o mutear el kick del tiempo 1 siguiente) | E | 1 tiempo | [S9] [T6] |
| 3.4 | En el hueco: crash, ruido o synth | S | — | [S9] |
| 3.5 | Crash / impacto largo en el tiempo 1 del compás 17 | S | — | [T6] [S10] |
| 3.6 | Entra o sale un elemento (filter-in con HP en 8 compases) | A+E | 8 compases | [T10] [S10] |
| 3.7 | Gesto de procesamiento único (Beat Repeat 1/16 o gate en el último tiempo) | A | 1–2 tiempos; máximo 1 cada 32 compases (propuesta) | [T16] [T30] |

#### Nivel 4: fin de frase de 32 compases / cambio de sección

| # | Acción | Tipo | Valor | Origen |
|---|--------|------|-------|--------|
| 4.1 | Fill grande (o redoble de 2 compases con +~2 dB) | E | 2 compases | [T6] [T15] |
| 4.2 | Hueco de kick + elemento nuevo | E/S | 1 tiempo – 1 compás | [S9] |
| 4.3 | Mutear todo salvo 1 elemento **2 tiempos** antes del tiempo 1 | E | 2 tiempos | [T1] [T6] |
| 4.4 | HP 250 Hz en el bus de batería durante el último compás, off en el 1 | A | 1–2 compases | [T5] |
| 4.5 | Cambio armónico o rítmico del elemento principal (misma armonía, ritmo distinto) | E | Nueva sección | [T25] |

#### Breakdown y drop (16–32 compases)

| # | Acción | Tipo | Valor | Origen |
|---|--------|------|-------|--------|
| B.1 | Kick fuera; bajo sin graves (HP o EQ) | E+A | Todo el breakdown | [T1] [S10] |
| B.2 | Estructura 3×8 o 4×8: el último bloque se **simplifica** (1 acorde) para crear falta | E | 8 compases | [T1] |
| B.3 | HP en acordes 200 Hz → 20 kHz | A | Todo el breakdown | [T8] |
| B.4 | Envío a reverb larga (≥ 6 s) subiendo; vuelve a normal antes del drop | A | Últimos 8 | [T7] [T8] |
| B.5 | Riser de ruido HP 1 → 10 kHz | S+A | 8 compases | [T8] |
| B.6 | Redoble: negras → corcheas → 16avos (→ 32avos al final), velocity 1→127 | E | ~8 compases | [T2] [T14] [T1] |
| B.7 | Volumen general bajando "unos dB" (valor NO VERIFICADO) | A | Todo el breakdown | [T14] |
| B.8 | Silencio o corte de **2 tiempos** (o redoble que para en 2.4) | E | 2 tiempos | [T1] [T2] |
| B.9 | Drop: vuelven kick y graves, faller/crash en el 1, reverb normal | E+S | Tiempo 1 | [T1] [T6] |

#### Reglas generales para el sistema

1. Ninguna frase de 8 compases termina igual que la anterior (propuesta,
   deducida de [T15] y del criterio de Gabriel).
2. Cada vez que entra un sonido, **otro cambia** (filtro, notas o largo de clip)
   — traducción directa de "una progresión se vuelve más compleja con la
   entrada de un sonido" (criterio de Gabriel); fuente de apoyo [T15] [T25].
3. Al menos un movimiento lento (filtro, drive, envío) activo en todo momento,
   con distintos largos para que no coincidan (propuesta, apoyo [T18] [T15]).
4. Los eventos únicos se usan poco [T16].
5. Las curvas no son rectas [T10].

### 6. Ableton: envolventes de clip en Arrangement (pregunta técnica)

Fuente principal: manual de Live 12, capítulos *Clip Envelopes* [T19] y
*Automation and Editing Envelopes* [T20].

| Pregunta | Respuesta | Fuente |
|----------|-----------|--------|
| ¿Las envolventes de clip en Arrangement son modulación? | **Sí.** "En el Arrangement, los clips solo tienen envolventes de **modulación**; las envolventes de automatización están en el carril de automatización de la pista." Por eso en Arrangement no aparecen los botones Automation/Modulation | [T19] §27.1, §27.3 |
| ¿Qué pasa con la automatización de un clip de Session al pasarlo al Arrangement? | "Toda automatización de Session View se convierte en **automatización de pista** cuando los clips se **graban o copian** al Arrangement View." | [T20] §25.2 |
| ¿Y si se copia por API (`Track.duplicate_clip_to_arrangement`)? | **NO VERIFICADO.** El manual habla de grabar o copiar con el mouse; no se encontró documentación de qué hace el LOM con las envolventes | — |
| ¿Cómo escala la modulación? | Es **relativa**. La automatización fija el valor absoluto; la modulación solo puede actuar sobre ese valor | [T19] §27.3 |
| Volumen de clip (Clip Gain) | Porcentaje del valor del slider: **nunca supera** el valor fijado, puede bajar hasta silencio | [T19] §27.2.3 |
| Volumen de pista | Modulación sobre la ganancia post-efectos; un punto bajo el fader muestra el valor real. El ejemplo del manual muestra que la modulación puede subir hasta el valor permitido por la automatización | [T19] §27.3, §27.3.1 |
| Envíos | No puede abrir el envío más que la perilla; sí puede bajarlo a -inf dB | [T19] §27.3.1 |
| Paneo | La posición de la perilla define la intensidad; en el centro cubre todo el rango, a fondo a la izquierda no tiene efecto | [T19] §27.3.2 |
| Transposición | Se **suma** al valor de Transpose (rango -48..+48 st) | [T19] §27.2.2 |
| Parámetros de devices (cutoff, etc.) | "Solo puede cambiarlos **relativo a su valor actual**"; no puede fijar un valor exacto. El manual **no da** el rango numérico | [T19] §27.3.3 |
| Interacción con automatización | Si hay automatización en el mismo parámetro, la automatización define el valor y la modulación se mueve dentro de ese rango | [T19] §27.3; Sound On Sound [T21] |

**Hipótesis de por qué los filtros escritos por API "no hicieron nada"**
(todas **NO VERIFICADAS**, para probar en Live):

1. La envolvente quedó en un clip de **Arrangement** → es modulación relativa a
   la posición de la perilla. Si la perilla estaba en un extremo (ej. cutoff
   de LP al máximo), la modulación puede tener poco o nada de recorrido, como
   pasa con el paneo a fondo o los envíos [T19].
2. Había automatización de pista en el mismo parámetro, que fija el valor
   absoluto y limita la modulación [T19].
3. La envolvente se escribió en un clip de Session y después el clip se pasó por
   API; no está confirmado que el LOM convierta eso en automatización de pista
   como lo hace la copia manual [T20].

**Prueba propuesta:** (a) poner la perilla del filtro en un valor medio y repetir
la envolvente en Arrangement; (b) comparar con la misma envolvente como
automatización de un clip de Session grabado al Arrangement (camino confirmado
por el manual [T20]); (c) leer el valor del parámetro durante la reproducción
para ver si se mueve.

### Fuentes de esta sección

- [T1] https://www.attackmagazine.com/technique/the-breakdown/what-is-the-recipe-for-an-effective-breakdown/
- [T2] https://www.attackmagazine.com/technique/tutorials/10-snare-rolls-for-the-drop/
- [T3] https://www.attackmagazine.com/technique/tutorials/filter-fills/
- [T4] https://www.attackmagazine.com/technique/tutorials/essential-transition-fx-technique-masterclass/ (pág. 1: ruido blanco; pág. 5: reverse crash)
- [T5] https://www.musicradar.com/how-to/6-essential-build-up-edit-and-fill-tricks
- [T6] https://www.musicradar.com/tuition/tech/10-steps-to-more-effective-transitions-605656
- [T7] https://musicradar.com/news/14-techno-tips
- [T8] https://www.musicradar.com/how-to/build-up-break-down
- [T9] https://www.musicradar.com/tuition/tech/how-to-breathe-life-into-loops-with-end-bar-cuts-and-drops-555173
- [T10] https://www.musicradar.com/tuition/tech/how-to-make-a-filtered-dance-music-transition-216375
- [T11] = [S9] https://www.musicradar.com/tuition/tech/umeks-guide-to-breakdowns-510309
- [T12] https://www.musicradar.com/news/tech/charlotte-de-wittes-top-10-tips-for-producers-637781
- [T13] https://www.musicradar.com/music-tech/record-everything-all-the-time-and-keep-it-all-8-pro-techno-producers-explain-how-they-create-their-tracks
- [T14] https://www.edmprod.com/ultimate-guide-build-ups/
- [T15] https://forum.ableton.com/viewtopic.php?p=652315 (foro: opiniones de usuarios)
- [T16] https://makingmusic.ableton.com/unique-events
- [T17] https://www.loopmasters.com/articles/4328-16-Techno-Tips-The-Essential-Guide-for-Music-Producers
- [T18] https://beatkitchen.io/guides/electronic-music/08-automation-and-movement/ (baja autoridad)
- [T19] https://www.ableton.com/en/live-manual/12/clip-envelopes/
- [T20] https://www.ableton.com/en/manual/automation-and-editing-envelopes/
- [T21] https://www.soundonsound.com/techniques/using-clip-envelopes-ableton-live
- [T22] https://forum.image-line.com/viewtopic.php?p=1676822 (fragmento de búsqueda)
- [T23] https://www.musicradar.com/tutorials/music-production-tutorials/its-tougher-and-faster-than-ever-jump-aboard-the-modern-hardgroove-train-and-learn-to-build-a-club-ready-beat (fragmento)
- [T24] https://www.attackmagazine.com/technique/beat-dissected/truncate-style-melodic-percussion/ (fragmento)
- [T25] https://www.edmprod.com/how-to-avoid-the-8-bar-loop-trap/
- [T26] https://www.pressreader.com/australia/computer-music/20190220/282956746427224 y https://www.puremix.com/blog/chris-lord-alge-delay-throw-vocals (fragmentos)
- [T27] https://www.native-instruments.com/blogs/blog/dark-techno (fragmento)
- [T28] https://violetrecording.com/how-to-make-techno/ y https://www.musicradar.com/how-to/how-to-program-jeff-mills-style-rolling-tr-909-drums (fragmentos)
- [T29] https://musictech.com/tutorials/genre-techno-3/ (403; fragmento)
- [T30] https://www.soundonsound.com/node/4906116 , https://djtechtools.com/2011/01/04/controllerism-ideas-for-ableton-multiple-beat-repeats/ , https://mixdownmag.com.au/features/ableton-dummy-clips-beat-repeat/ (fragmentos)
- Otras: https://www.attackmagazine.com/technique/beat-dissected/spastik-style-percussive-techno/ (fragmento),
  https://www.musicradar.com/how-to/9-minimal-track-arrangement-tips-find-out-how-a-little-can-go-a-long-way (fragmento),
  https://www.productionmusiclive.com/blogs/news/how-to-make-techno (sin números),
  https://www.productionmusiclive.com/blogs/news/drumcode-style-techno-track-walkthrough-with-johannes-menzel-from-kick-processing-to-mastering (sin datos de arreglo en texto).
- Sin resultado útil: entrevistas de Beyer, Sangiuliano, Lens, Zonneveld, De Vries, Giordani, Eli Brown; Point Blank, Sonic Academy; hilo de r/TechnoProduction "tips on arrangement" (respuestas escasas).

## Estándares de mezcla y master (investigación dedicada, 2026-11-22)

> Investigación web del 2026-11-22. Completa los huecos de las secciones 5 y 6
> (niveles relativos, sidechain, reverb, master) y valida los valores que hoy
> aplica el sistema. Fuentes [M1]...[M31] al final de esta sección. Lo que solo
> se vio en un fragmento de búsqueda dice *(fragmento)*; lo que no tiene fuente
> dice **NO VERIFICADO**. Como siempre, todo es **punto de partida** (D-01) y
> respeta D-15 (nunca automatizar el volumen de pista; Utility al final).
> Hallazgo general: **ninguna fuente da una tabla completa de dB por elemento
> para techno.** Hay números firmes para kick, bajo, sidechain, master y
> filtros de returns; para hats, clap, stabs, pads y FX solo hay rangos de
> filtro y el consejo de nivelar contra una referencia.

### 1. Gain staging y niveles relativos

#### Referencia de nivel

| Dato | Valor | Fuente |
|------|-------|--------|
| Pico del kick (medido en el medidor de la pista, no en el fader) | **justo bajo -6 dBFS** | [M4]; coincide con el fader del kick a ~-6 dB de [S3] |
| Alternativas | Kick a -8 dBFS y subir el bajo hasta que ambos sumen pico entre -1 y 0 dB [M5] *(fragmento)*; kick y bajo con fader en -10 dB y armar el resto alrededor [M6] [S36] | Las fuentes difieren: -6 / -8 / -10 |
| Pistas individuales | ~-20 dB RMS, -10 a -6 dB de pico ("enfoque de seguridad") | [M7] (respuesta del editor de Attack a un comentario) |
| Ninguna pista sobre | -6 dBFS de pico | [M4] |
| Bus master pre-master | **no pasar -3 dBFS** de pico [M4]; ~-6 dBFS según la sección 5 | Las fuentes difieren; -6 es la opción más segura |

**Importante para el sistema:** el fader de Live es una **ganancia**, no un
nivel. "Kick -6" en el fader solo da -6 dBFS de pico si el clip pica en 0 dBFS.
Los valores de fader actuales (kick -6, bajo -12, etc.) **solo tienen sentido si
se miden los picos resultantes** en cada pista. Recomendación (deducida de
[M4] [M5] [M7]): fijar **objetivos de pico por pista** y ajustar el fader hasta
alcanzarlos, en lugar de aplicar valores de fader fijos. Lectura de medidores de
pista por API: **NO VERIFICADO** en esta sección.

#### Relación entre elementos

| Elemento | Relación con el kick | Fuente | Estado del valor actual |
|----------|----------------------|--------|-------------------------|
| Bajo | Pico **3–6 dB bajo el kick**; en LUFS de corto plazo **aproximadamente igual** al kick. Si embarra, bajar 1–2 dB. El mismo artículo dice en otro lugar "dentro de 3 dB" (contradicción interna) | [M1] | Fader -12 vs kick -6 = 6 dB: **en el borde del rango**. Medir picos |
| Rumble | Sin dato | — | -10: **SIN FUENTE** |
| Clap, hats, tops, perc | Sin dato. Solo "ver dónde pica el clap respecto del kick y después los hats" (foro, fragmento) | [M8b] *(fragmento)* | Valores actuales: **SIN FUENTE** |
| Stabs, leads, pads, coro, FX | Sin dato. Pads "muy bajos" (sección 3) | — | **SIN FUENTE**; orden relativo coherente con la sección 3 |

Conclusión: el único valor relativo con respaldo es **bajo 3–6 dB de pico bajo el
kick**. Para el resto, la fuente más concreta es un método, no un número.

#### Métodos de nivelación

- **Ruido rosa:** poner ruido rosa en el master a un nivel fijo (ej. ~-14 dB) y
  subir cada pista en solo hasta que **apenas se oiga** sobre el ruido
  [M8] *(fragmento CreativeLive)*. Explicación técnica de por qué funciona
  (misma energía por octava): Sound On Sound [M8]. Para techno: empezar por el
  kick y después el segundo elemento más fuerte [M8] *(fragmento, Medium)*.
- **Pasos de 3 dB:** mover el fader en pasos de 3 dB hasta que suene muy fuerte
  o muy suave y elegir el punto medio [M4]. Útil para un sistema que itera con
  feedback de Gabriel.
- **Track de referencia:** ya está en la sección 5; sigue siendo lo más usado.

### 2. EQ por elemento

| Elemento | HP | LP | Campanas / cortes | Fuente |
|----------|----|----|-------------------|--------|
| Kick | 20–30 Hz (12–18 dB/oct) | ~15 kHz | +1–3 dB en 60–65 Hz (rango de punch en techno: **60–100 Hz**); cortes suaves en **~200 y ~800 Hz** (o ~400 Hz); click +1–3 dB en ~3,5 kHz (rango 2–5 kHz); en mezclas oscuras, pequeños realces en **7–10 kHz** | [S21] [M9] [M10] |
| Rumble | ~30–40 Hz | **250 Hz** (punto de partida) a **800 Hz** (48 dB/oct) | — | [M29] *(fragmento)*; [S8] |
| Sub / bajo | **30 Hz, 24 dB/oct** ("no más alto") | — | -2 dB en 200 Hz para dejar lugar al cuerpo del kick | [M1] |
| Mid-bass / top-bass | 65 Hz [S7]; 50–90 Hz con 24 dB/oct cuando hay capa de sub [M6] | ~350 Hz | Corte suave ~100 Hz, realce ~330 Hz | [S7] [M6] |
| Clap / snare | ~150 Hz *(sin fuente específica)* | — | "Punch" del snare 150–300 Hz *(fragmento, baja autoridad)* | **NO VERIFICADO** |
| Hats / tops | **100–300 Hz** (iZotope 100; eMastered 150; Produce Like A Pro hasta 300). iZotope: los cambios se oyen sobre 300–500 Hz en platillos | — | — | [M12] [M30] *(fragmentos)* |
| Ride | 1 kHz | — | — | [S5] |
| Todo lo que no es kick ni bajo | **≥120 Hz** ("cortar de 120 Hz para abajo salvo kick y bajo"); EDMProd: 60–120 Hz | — | — | [M6]; [M13] *(fragmento)* |
| Synths / leads / stabs | 100–200 Hz; un foro: 82–270 Hz según el sonido | — | — | [M13] *(fragmentos)* |
| Pads | Sin regla única; ejemplo de iZotope a **430 Hz** | — | — | [M13] *(fragmento)* |
| Voces | 80–100 Hz (mezcla general) | — | — | [M15b] *(fragmentos)* — techno: **NO VERIFICADO** |
| Returns de reverb | **200–400 Hz** | **5–10 kHz** | Variante "Abbey Road": HP hasta 600 Hz, LP 6–7 kHz | [M16] *(fragmentos)* |
| Returns de delay (ping-pong) | **400 Hz** | **3 kHz** | — | [M14] |
| Delay corto (slap) | 250 Hz | 8 kHz | — | [M14] |

**Pendiente de los filtros.** Las fuentes que la indican usan **12–24 dB/oct**
([S21], [M1], [M6]); la única con 48 dB/oct es el LP del rumble [S8]. Un
eMastered advierte que en hats con cuerpo una caída suave suena mejor que un
corte [M12] *(fragmento)*. Que EQ Eight ofrezca 12 y 48 dB/oct como opciones de
corte: **NO VERIFICADO** en el manual en esta investigación.

### 3. Dinámica

#### Sidechain kick → graves

| Parámetro | Valor | Fuente |
|-----------|-------|--------|
| Attack | 1–3 ms (ejemplo 2 ms) [M1]; 1–10 ms [M2]; "lo más rápido posible", ojo con clicks en el mínimo [M3] | Coinciden: rápido |
| Release | **80–120 ms** (ejemplo 100 ms) para ducking limpio del bajo [M1]; 30–300 ms en general; **200–350 ms a 128 BPM** para bombeo marcado [M2]; "según el decay del kick y el BPM" [M3]; 20–75 ms = ducking sutil (fragmento) | **Las fuentes difieren** según se busque limpieza o bombeo |
| Ratio | **4:1–6:1** [M1]; 4:1–10:1 [M2] | — |
| Threshold | Ninguna fuente da un valor absoluto: se fija hasta lograr la reducción buscada [M2] [M3] | — |
| Reducción | **4–6 dB** por golpe (bajo) [M1]; hasta **6 dB** sin que se note el bombeo [M3]; **6–12 dB** para bombeo [M2] | — |
| Multibanda | 20–200 Hz: **-8 a -12 dB**; 200 Hz–2 kHz: **-2 a -4 dB**; >2 kHz: nada | [M2] |
| Delay con ducking | Compresor 8:1, 6–8 dB de reducción, sin makeup | [M14] |

**Release según tempo** (cálculo: 60.000 / BPM [M2]):

| BPM | Negra | Corchea | Semicorchea |
|-----|-------|---------|-------------|
| 130 | 462 ms | 231 ms | 115 ms |
| 132 | 455 ms | 227 ms | 114 ms |
| 135 | 444 ms | 222 ms | 111 ms |

El "200–350 ms a 128 BPM" de [M2] cae entre la corchea y algo más de 3/4 de
negra. El release de 90 ms actual queda **por debajo de la semicorchea**:
correcto para un bajo "que se sienta, no que se oiga" [M1], corto para un
rumble que debe bombear [S5] [S6].

**Valores actuales del sistema** (threshold -32 dB, ratio 4, attack 1 ms,
release 90 ms, en rumble y bajo):

- Ratio 4 y attack 1 ms: **dentro de rango** [M1] [M2].
- Threshold -32 dB: **no se puede validar** como número absoluto; depende del
  nivel del kick que entra por el sidechain. Hay que **medir la reducción** y
  ajustar a 4–6 dB (bajo) o 6–12 dB (rumble).
- Release 90 ms: válido para el bajo (rango 80–120 [M1]); para el rumble, la
  sección 3 pide bombeo [S5] [S6], así que conviene **150–300 ms** (propuesta
  dentro del rango de [M2]).

**Alternativas nativas sin compresor:**
- **Auto Pan** como tremolo sincronizado: **Phase 0%** (las dos LFO juntas, solo
  volumen), onda diente de sierra para recuperación rápida, Shape para
  endurecer; solo sirve con kick en negras [M26] *(fragmentos)*.
- **Auto Filter** con sidechain: el bajo se oscurece en vez de bajar [M26].
- Envolvente con kick fantasma: el volumen vuelve al valor inicial dentro de
  una negra [M2]. **Choca con D-15** si se hace sobre el volumen de pista;
  hacerlo sobre un Utility no final o sobre Auto Pan.
- Compresor de Live: lookahead de **0, 1 o 10 ms**; con sidechain externo no hay
  makeup automático [M18].

#### Compresión, Drum Buss y saturación

| Dónde | Valores | Fuente |
|-------|---------|--------|
| Kick (compresor) | Ratio 4, attack **27 ms**, release **177 ms**, threshold -19 dB (un ejemplo con plugin de consola) | [M11] |
| Clap | "Igual que el kick pero ratio más alto" (sin número) | [M11] |
| Bus de drums | Ratio y threshold bajos (sin número) | [M11] |
| Drum Buss (techno) | Drive **17%**, Boom **45%** en **55 Hz**, Out **-3 dB** | [S5] |
| Drum Buss (general) | Crunch 24%, Boom 50%, Damp 3,16 kHz | [M28] *(fragmento)* |
| Rangos de Drum Buss | Drive/Crunch/Boom/Decay/Dry-Wet 0–100%; Transients -1 a +1 (actúa sobre >100 Hz); Boom Freq **30–90 Hz**; Damp 500 Hz–20 kHz; Output -40 a +3 dB | [M19] [M18] |
| Saturación del bajo | Soft clip, drive **5–15%** (ejemplo 10%); agrega armónicos en ~100–800 Hz para sistemas chicos | [M1] |
| OTT en bajo | Depth 30%, Time 200% | [S2] |
| Glue en bus de batería/master | 30 ms de attack, release medio, 2:1, **1,5–2 dB** de reducción (usuario de foro) | [M31] *(fragmento)* |
| Compresión paralela | **NO VERIFICADO** (ninguna fuente con números para techno) | — |

Boom de Drum Buss: afinarlo a la tónica (ej. F0 = 43,7 Hz) [M28]
*(fragmento)*; coincide con [S4].

### 4. Espacio

#### Reverb por rol

| Rol | Tipo | Decay | Pre-delay | Fuente |
|-----|------|-------|-----------|--------|
| Percusión / tops | Room / plate corta | **0,4–0,9 s** | **≤10 ms** | [M17] *(fragmento)*; [S1] |
| Clap / snare | Plate | **1–2 s** (otras fuentes 2,7–4 s en plates generales) | 0 ms | [S10]; [M17] *(fragmentos)* |
| Clap (Attack) | — | — | **En tiempo con el tema** | [M17] *(fragmento)* |
| Profundidad | Dos rooms con el mismo decay y pre-delays distintos = dos planos | — | — | Foro *(fragmento)* [M17] |
| Lead | — | 1,5 s, 48% wet | — | [S2] |
| Build | Larga | ≥6 s | 7,5–8 ms | [T7] [T8] |
| Rumble | Hall oscura, send alto | **NO VERIFICADO** | **NO VERIFICADO** | [S6] |
| Pads | **NO VERIFICADO** (solo "reverb + delay pesados") | — | — | [S2] |

#### Delays

| Uso | Valor | Fuente |
|-----|-------|--------|
| Voz en dance (ping-pong) | **1/8 con puntillo** | [M15] *(fragmento)* |
| Ping-pong genérico | 1/4 o 1/8, **feedback 40–50%**, HP 400 Hz / LP 3 kHz | [M14] |
| Delay throws | 1/2 o 1/4; una repetición para frase, varias para una palabra | [M14] |
| Ride / vocal techno | 3/16 | [S10] |
| Clap | ~10% wet | [S4] |

#### Mono y ancho

| Dato | Valor | Fuente |
|------|-------|--------|
| Utility Bass Mono | Rango del parámetro **50–500 Hz** | [M18] |
| Corte mono recomendado | **120 Hz** en Utility [M1]; 100 Hz [S23] [M27]; algunas fuentes hasta 250 Hz *(fragmento)* | **Las fuentes difieren**: 100–120 Hz |
| Centro | Kick, bajo, voz principal, snare en el centro | [M27] *(fragmentos)* |
| Abrir | Pads, synths, percusión, capas de voz | [M27] *(fragmentos)* |
| Utility Width | 0% = mono; >100% = ensanchar | [M18] |
| Paneo de ejemplo | Snare -10, clap +10, hats -15 (no es techno) | [M27] *(fragmento)* |
| Ancho por elemento en % | **NO VERIFICADO** | — |

### 5. Master y loudness

#### Objetivos

| Medida | Club | Streaming | Fuente |
|--------|------|-----------|--------|
| LUFS integrado | **-8,6** mediana peak time (mitad central -9,9 a -7,6; 75 tracks, previews de 120 s) [M20]; tabla de MTM: **-6 a -9** [M21]; Nihil Young: ~-7 en melodic techno [M25] *(fragmento)* | Spotify normaliza a **-14** (Loud -11, Quiet -19) [M22]; Apple -16 [M21] [M23] | — |
| Short-term en drops | **-4 a -6 LUFS** en los clubs más fuertes [M21] | — | — |
| True peak | **-1 dBTP** [M23]; MTM para club: -0,1 dBTP [M21]. Medido: a -1 dBTP, MP3 320 kbps no sube (peor caso +0,5 dB) [M20] | **-1 dBTP**; **-2 dBTP si el master es más fuerte que -14 LUFS** [M22] | **Las fuentes difieren** para club |
| Rango dinámico | Club: "no más de 8 DR"; streaming: >9 DR [M21] | — | — |
| LRA | ~5,6 LU en peak time (subestimado: mide 2 min) [M20] | — | — |
| Crest factor / PLR | **NO VERIFICADO** (no hay mediciones de techno) | — | — |
| Top dance (no techno) | -6,2 a -8,7 LUFS, true peak +0,2 a +0,9 dBTP | [M25] *(fragmento iZotope)* | — |

- Beatport **no normaliza**: el archivo suena al nivel entregado [M20].
- **¿Dos masters?** Lo habitual es uno solo [M21] [M23]; MTM recomienda
  variaciones por destino (~10 min extra) [M21]. Como el master de club queda
  más fuerte que -14 LUFS, Spotify pide **-2 dBTP** [M22]. Propuesta: **un
  master de club** (-8,5 a -7,5 LUFS, -1 dBTP) y una **variante de streaming**
  con la misma cadena y techo a -2 dBTP o menos limitación ("aflojar el
  limitador" [M21]).

#### Cadena y límites de procesamiento

| Paso | Valores | Fuente |
|------|---------|--------|
| Glue | Ratio 1,5:1–2:1, **attack ≥30 ms**, release 0,8 s o auto, **1–2 dB** de reducción | [S27] [M31] *(fragmento)* |
| Glue Soft Clip | Salida máxima **-0,5 dB**; no transparente, distorsiona | [M18] |
| Clipper antes del limitador | 0,5–2 dB de clipping; controla transitorios de kick y snare antes del limitador | [M24] *(fragmentos)* |
| Limitador | Reducción **≤2,5–3 dB**; el kick pierde punch pasados **3–4 dB** de reducción (en el bus de mezcla, observación personal) | [M24] *(fragmentos)*; [M23] |
| Limiter de Live | Lookahead 1,5 / 3 / 6 ms; release Auto; modos L/R y M/S; techo **Standard, Soft Clip o True Peak** | [M18] |
| Kick | "En la mayoría del techno el kick es el transitorio más fuerte de la mezcla" → es lo primero que sufre con el limitador | [M23] |

**Valores actuales del master** (Glue ratio 2, threshold -8 dB, attack 10 →
Limiter techo -1 dB):

- Ratio 2: **correcto** [S27].
- Attack 10 ms: **cambiar a 30 ms**; todas las fuentes de glue de master piden
  ≥30 ms para dejar pasar el transitorio del kick [S27] [M31].
- Threshold -8 dB: **no validable** como número; ajustarlo hasta **1–2 dB** de
  reducción en el drop [S27].
- Limiter: activar el modo **True Peak** con techo -1 dB (el techo estándar
  limita picos de muestra, y un pico de 0 dB de muestra puede ser +0,3/+0,5
  dBTP [M23]). Controlar que la reducción no pase **~3 dB** [M23] [M24].
- Falta medir el LUFS integrado y de corto plazo después del limitador:
  objetivo club -9,9 a -7,6 integrado [M20], drops no más fuertes que ~-6
  short-term [S24].

### 6. Plantilla de mezcla con devices nativos

Orden de cadena: **EQ Eight → dinámica (Compressor/Drum Buss/Glue) →
saturación (Saturator/Roar) → espacio por send → Utility al final (D-15)**. Las
filas marcan cada valor actual: **OK** (respaldado), **CAMBIAR** (las fuentes
dicen otra cosa), **SIN FUENTE** (plausible, ninguna fuente lo da) y
**(propuesta)** = elección de diseño, no de la web.

| Rol | Cadena y valores de partida | Objetivo de nivel | Valor actual → estado |
|-----|-----------------------------|-------------------|-----------------------|
| Kick | EQ Eight: HP 20–30 Hz; +1–3 dB a 60–65 Hz; -2/-3 dB en ~200–400 Hz; +1–3 dB a 3,5 kHz [S21] [M9] → Drum Buss: Drive 17%, Boom 45% en la tónica (30–90 Hz), Out -3 dB [S5] → Utility | Pico ~-6 dBFS [M4] | Fader -6: **OK** si el pico medido da ~-6 dBFS |
| Rumble | EQ Eight: HP 30–40 Hz, LP 250–800 Hz 48 dB/oct [M29] [S8] → Compressor SC kick: ratio 4–10, attack 1–3 ms, release **150–300 ms** (propuesta dentro de [M2]), reducción 6–12 dB → Utility Width 0% | Bajo el kick (sin dB) | Release 90 → **CAMBIAR** (si se busca bombeo); fader -10 → **SIN FUENTE** |
| Bajo | EQ Eight: HP 30 Hz (sub) o 65 Hz (mid-bass); -2 dB en 200 Hz [M1] [S7] → Compressor SC kick: ratio 4–6, attack 1–3 ms, release 80–120 ms, reducción 4–6 dB [M1] → Saturator suave 5–15% [M1] → Utility Bass Mono 100–120 Hz | Pico 3–6 dB bajo el kick [M1] | SC ratio 4 / atk 1 / rel 90: **OK**; threshold -32 → **calibrar por reducción**; fader -12 → **OK en el borde**, medir |
| Clap | EQ Eight HP ~150–200 Hz → send plate 1–2 s | Sin dato | HP 200: **SIN FUENTE** (plausible); fader -12: **SIN FUENTE** |
| Tops / hats | EQ Eight HP 100–300 Hz [M12] | Sin dato | HP 220: **OK** (dentro de rango); fader -14: **SIN FUENTE** |
| Ride | EQ Eight HP 1 kHz [S5]; SC suave | Sin dato | — |
| Loop de percusión | EQ Eight HP ≥120 Hz [M6] → send room 0,4–0,9 s [M17] | Sin dato | HP 160: **OK**; fader -12: **SIN FUENTE** |
| Stabs / leads | EQ Eight HP 100–200 Hz [M13] → SC 2–4 dB de reducción (banda media de [M2]; lead "50%" [S2]) → send reverb 1,5 s [S2] | Sin dato | HP 180: **OK**; faders -16: **SIN FUENTE** |
| Pads / atmos | EQ Eight HP 100–430 Hz (sin regla única [M13]) → SC 2–4 dB → Utility Width >100% | "Muy bajo" | HP 250: **OK** (dentro de rango); fader -20: **SIN FUENTE** |
| Coro | Igual que pads | Sin dato | HP 220: **SIN FUENTE** (coherente con pads); fader -22: **SIN FUENTE** |
| Voces | EQ Eight HP (fuentes generales: 80–100 Hz) → send delay 1/8 con puntillo, feedback 40–50%, return HP 400 / LP 3 kHz [M14] [M15] | Sin dato | HP 180–200: **más alto que las fuentes** — razonable para chops en mezcla densa, **NO VERIFICADO**; faders -12/-14: **SIN FUENTE** |
| FX / risers | HP automatizado en el riser (1 → 10 kHz [T8]) | Variable | HP 200: **SIN FUENTE** |
| Impactos | HP ≥120 Hz salvo booms y sub drops | Variable | HP 120: **OK para crashes/impactos agudos; CAMBIAR para sub drops**, que necesitan graves ([S1]: el sub drop es parte del impacto) |
| Crash | EQ Eight HP 300–500 Hz [M30] | Variable | HP 300: **OK** |
| Fills de snare | Igual que clap | -17 dB (criterio de Gabriel) | **OK** (oído de Gabriel, P-02) |
| Return reverb | Reverb/Hybrid Reverb 100% wet → EQ Eight HP 200–400 Hz, LP 5–10 kHz [M16] | — | — |
| Return delay | Echo/Delay 100% wet, feedback 40–50%, HP 400 Hz, LP 3 kHz [M14]; opcional Compressor SC 8:1, 6–8 dB [M14] | — | — |
| Master | EQ Eight (correctivo) → Glue: ratio 2, attack **30 ms**, release 0,8 s/auto, 1–2 dB de reducción [S27] → (Saturator o Glue Soft Clip, 0,5–2 dB [M24]) → Limiter modo **True Peak**, techo -1 dB, reducción ≤3 dB [M23] [M24] | -9,9 a -7,6 LUFS integrado [M20] | Ratio 2: **OK**; attack 10 → **CAMBIAR a 30**; threshold -8 → **calibrar por reducción**; techo -1 → **OK**, agregar modo True Peak |
| Todos los HP | Pendiente | — | 48 dB/oct en todos → **CAMBIAR**: las fuentes usan 12–24 dB/oct; 48 solo en el LP del rumble [S8] |

**Pendiente / NO VERIFICADO de esta sección:** dB relativos de hats, clap,
stabs, pads, coro y FX; compresión paralela; ancho estéreo en %; tiempos de
reverb del rumble y de pads; crest factor/PLR medido en techno; pendientes
disponibles en EQ Eight; lectura de medidores por API. Propuesta: medir stems o
tracks de referencia (F2) con picos y LUFS de corto plazo por elemento.

### Fuentes de esta sección

- [M1] https://theproducerschool.com/blogs/featured-blogs/how-to-mix-sub-bass-for-tech-house-without-it-disappearing-on-club-systems (tech house, aplicado por analogía)
- [M2] https://www.gearnews.com/sidechain-compression-in-techno-workshop/
- [M3] https://www.attackmagazine.com/technique/ten-production-tips-for-better-basslines/4
- [M4] https://soundation.com/learn/music-production/volume-mastery
- [M5] https://magneticmag.com/2025/04/christophe-salin-shares-6-crucial-mixdown-tips-thatll-make-your-music-cleaner-more-professional-instantly/ (fragmento)
- [M6] https://www.izotope.com/en/learn/12-tips-for-mixing-and-producing-edm
- [M7] https://www.attackmagazine.com/technique/tutorials/the-essential-guide-to-levels/ (comentario del editor)
- [M8] https://site.creativelive.com/class/mixing-electronic-music-ableton-live-isaac-cotec/lessons/what-is-loudness (fragmento), https://www.soundonsound.com/techniques/mixing-pink-noise-reference , https://medium.com/@abletoninua/mix-tech-series-part-1-levels-panning-theory-basics-selected-studio-practices-and-a-few-pro-609978e9462f (fragmento)
- [M8b] https://www.kvraudio.com/forum/viewtopic.php?p=8700433 (foro, fragmento)
- [M9] https://www.edmprod.com/eq-kick-drums/
- [M10] https://www.izotope.com/en/learn/5-tips-for-balancing-edm-kicks-in-the-mix
- [M11] https://www.attackmagazine.com/technique/tutorials/mixing-techno-drums-with-excite-audios-lifeline-console/
- [M12] https://www.izotope.com/en/learn/how-to-mix-hi-hats , https://producelikeapro.com/blog/how-to-use-audio-pass-filters-in-your-mixes/ , https://emastered.com/blog/hi-hat-eq (fragmentos)
- [M13] https://www.edmprod.com/audio-filters/ , https://www.izotope.com/en/learn/5-tips-for-mixing-pads , https://www.audeobox.com/learn/glossary/high-pass-filter/ , https://gearspace.com/threads/highpass-filtering.989627/ (fragmentos)
- [M14] https://lewitt-audio.com/blog/5-tips-for-vocal-delay
- [M15] https://musictech.net/tutorials/simon-field-teaches-you-how-to-strip-back-a-track-to-make-room-for-vocals/ (fragmento)
- [M15b] https://producelikeapro.com/blog/four-perspectives-on-mixing-vocals-insights-from-marc-daniel-nelson-bob-horn-darrell-thorp-and-ariel-chobaz/ , https://www.bax-shop.co.uk/blog/studio-recording/mixing-flawless-vocals-in-5-steps/ (fragmentos)
- [M16] https://www.sweetwater.com/insync/effect-tip-use-a-high-pass-filter-before-reverb/ , https://flypaper.soundfly.com/tips/the-abbey-road-trick-how-to-eq-reverb-sends-to-free-up-space-in-a-mix/ , https://fohonline.com/?p=140445 (fragmentos)
- [M17] https://www.soundonsound.com/techniques/reverb-what-do-all-those-knobs-do , https://www.musicradar.com/how-to/explainers-reverb-parameters-and-how-they-work , https://attackmagazine.com/technique/tutorials/how-to-use-reverb-in-a-mix/2 , https://gearspace.com/threads/rhythmic-reverb-setup.1375779/ (fragmentos)
- [M18] https://www.ableton.com/en/live-manual/12/live-audio-effect-reference/ (Compressor, Drum Buss, Glue Compressor, Limiter, Utility)
- [M19] https://docs.cycling74.com/reference/abl.device.drumbuss~
- [M20] = [S13] https://www.mixgraph.io/tools/lufs-meter (muestra de 900 tracks medida el 2026-08-11)
- [M21] https://www.masteringthemix.com/blogs/learn/song-mastering-for-cd-club-play-and-streaming
- [M22] https://support.spotify.com/au/artists/article/loudness-normalization/
- [M23] https://www.gearnews.com/loudness-war/
- [M24] https://splice.com/blog/mastering-101-limiting , https://splice.com/blog/mastering-101-signal-flow-metering/ , https://www.newfangledaudio.com/post/when-to-clip-vs-when-to-limit-and-why-order-matters (fragmentos)
- [M25] https://www.izotope.com/en/learn/dance-electronic-analysis , https://blog.native-instruments.com/mastering-with-nihil-young/ (fragmentos)
- [M26] https://iconcollective.edu/ableton-live-auto-pan-tips , https://www.ableton.com/en/blog/sidechain-compression-part-2-common-and-uncommon-uses/ (fragmentos)
- [M27] https://www.masteringthemix.com/pages/how-to-get-the-right-stereo-width , https://musicradar.com/how-to/10-tips-stereo-width (fragmentos)
- [M28] https://pcaudiolabs.com/how-to-use-the-ableton-live-drum-buss-audio-effect/ , https://liveschool.net/blog/ableton-live-tutorial-enhancing-loops-drum-buss/ (fragmentos)
- [M29] https://www.bonedo.de/artikel/bass-drum-rumble-rattle-for-techno (fragmento)
- [M30] https://www.izotope.com/en/learn/how-to-eq-drums.html (fragmento)
- [M31] https://forum.ableton.com/viewtopic.php?p=1834364 (foro, fragmento)
- Sin datos útiles: https://www.productionmusiclive.com/blogs/news/drumcode-style-techno-track-walkthrough-with-johannes-menzel-from-kick-processing-to-mastering (sin números en texto); valores discretos de attack/ratio del Glue Compressor (el manual no los lista): **NO VERIFICADO**.

### Objetivos de premaster (D-16, búsqueda 2026-11-22)

Pedido por Gabriel: la mezcla es premaster; buscar sus valores objetivo.

| Medida | Objetivo premaster | Fuentes |
|--------|--------------------|---------|
| Pico (sample, con true peak controlado) | **-6 dBFS** (rango citado: -6 a -10) | [Waves](https://www.waves.com/essential-mastering-levels-tips), [iZotope](https://www.izotope.com/learn/headroom-how-to-set-levels-mixing-and-mastering), [LANDR](https://blog.landr.com/headroom-audio), [MasteringBOX](https://www.masteringbox.com/learn/headroom-for-mastering) |
| Loudness integrado | **-18 a -23 LUFS** (una fuente da -25 a -19; otra -23 para mezclar) | [Integraudio](https://integraudio.com/how-loud-mix-before-mastering/), [Major Mixing](https://majormixing.com/how-loud-should-mix-be-before-mastering), [Sonarworks](https://www.sonarworks.com/blog/learn/what-level-should-i-master-for-streaming) |
| Bus master | **Sin limiter para ganar volumen** (compresión de glue suave aceptable) | [iZotope](https://www.izotope.com/learn/headroom-how-to-set-levels-mixing-and-mastering), [Ask.Audio](https://ask.audio/articles/how-loudness-standards-relate-to-edm-and-club-music-production) |

Las fuentes no son específicas de techno peak time: confianza media. Los
objetivos de **master** (club -8,5 LUFS / -1 dBTP; streaming -14 / -2 dBTP)
quedan para la etapa de mastering.

**Primer preview de T02 (I:\TEST2.wav):** -28,7 LUFS integrado, -13,0 dBTP →
le faltan ~7 dB de nivel para el premaster (pico -6 → ~-21,7 LUFS, dentro del
rango).
