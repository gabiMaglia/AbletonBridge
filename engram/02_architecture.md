# Architecture — abletonBridge

## Stack
| Capa | Tech | Versión | ADR |
|------|------|---------|-----|
| Puente en Ableton | Remote Script (Python embebido de Live) | Live 12.4.16 (D-09) | ADR-001 |
| Servidor MCP | Python (MCP SDK, stdio para Claude Code) | mcp 2.3.0 | ADR-001 / T-016 |
| Transporte puente | Socket TCP local 127.0.0.1:19845 (MCP ⇄ Remote Script) | — | ADR-001 |
| Análisis de audio | `nexo_analysis/` en WSL sobre songTagger fijado (essentia + madmom + librosa) | Py3.11 | ADR-002 / D-14 |
| Compositor | `composer/` (perfiles YAML + reglas de arreglo como código) | pyyaml | T-015 |
| ~~UI control/config + empaquetado~~ | ~~PySide6 + PyInstaller~~ | — | Fuera de alcance por D-10 (uso personal) |

## DB (resumen vivo: tablas y relaciones clave)
N/A (sin base de datos persistente; config en archivo local).

## Índice ADRs
| # | Título | Estado | Fecha |
|---|--------|--------|-------|
| ADR-001 | Remote Script (Python) vs Max for Live para el puente Claude↔Ableton | Aceptado | 2026-06-22 |
| ADR-002 | Reuso de songTagger como motor de análisis + estrategia de deps pesadas (essentia/madmom) en Windows nativo. RIESGO: el repo corre bajo `.venv-wsl` (Linux); essentia/madmom son difíciles/no soportados en Windows nativo. Opciones: (A) análisis-como-servicio, (B) reescribir con librosa puro, (C) análisis offline desacoplado. | Aceptado por decisión del PO D-14 (2026-11-22): paquete propio en WSL, songTagger fijado por commit, adaptador único, tests de contrato. El riesgo de Windows nativo cae con D-10. Cuerpo del ADR pendiente de redactar (nerv-arquitecto). | 2026-11-24 |

---

## ADR-001 — Remote Script (Python) vs Max for Live para el puente Claude↔Ableton

- **Estado:** Aceptado
- **Fecha:** 2026-06-22
- **Decisor:** nerv-arquitecto (decisión de producto pre-acordada con el PO)
- **Tickets:** T-001
- **Reemplaza/Reemplazado por:** —

### Contexto
abletonBridge necesita un componente que viva DENTRO de Ableton Live y exponga el
**Live Object Model (LOM)** —transporte, tracks, clips, notas— a un proceso externo
(el servidor MCP que habla con Claude). Live ofrece dos vías oficiales para correr
código in-process con acceso al LOM:

1. **Remote Script (MIDI Remote Script):** módulos Python que Live carga al arranque
   desde `MIDI Remote Scripts/`. Corren en el intérprete embebido de Live (Py3 en
   Live 11/12) y tienen acceso directo a `Live.Application.get_application()` y al
   árbol `live_set`.
2. **Max for Live (M4L):** dispositivos `.amxd` que corren dentro de Max, con acceso
   al LOM vía el objeto `live.object`/`live.path`.

Restricciones duras del producto (RN-001, RN-003): compatibilidad obligatoria con
Live 11 **y** 12 (ambos Py3) y con ediciones **Standard + Suite**; estilo de producto
Python/PySide6/PyInstaller. El puente es **control-rate**, no audio-rate (§3 requirements).

### Decisión
El puente se implementa como **Remote Script de Python** que abre un **socket TCP local**
para recibir comandos del servidor MCP y operar sobre el LOM in-process.
**Se descarta Max for Live.**

### Alternativas consideradas
| Opción | Pros | Contras | Veredicto |
|--------|------|---------|-----------|
| **A. Remote Script (elegida)** | Disponible en Standard y Suite (M4L NO está en Standard); acceso in-process directo al LOM sin saltos de proceso → menor latencia; 100% Python, alineado con el stack (RN-003); empaquetable como carpeta que el instalador copia | API de Remote Scripts semi-documentada (ingeniería inversa de la comunidad); ciclo de iteración requiere reiniciar Live; corre en el intérprete embebido (no pip libre) | **ELEGIDA** |
| B. Max for Live | API LOM bien documentada (`live.path`/`live.observer`); hot-reload del device | **No existe en Live Standard** → viola RN-001/cobertura de ediciones; agrega dependencia de Max y un runtime extra; salto de proceso Max↔host; mezcla JS/Max con el stack Python | Descartada |
| C. Node for Max | Permite JS/Node dentro de M4L | Hereda TODOS los contras de M4L + runtime Node embebido; fuera del stack | Descartada |

### Consecuencias
**Positivas**
- Una sola base de código Python cubre Live 11/12 y Standard/Suite.
- El servidor MCP y el Remote Script comparten lenguaje y modelos de mensaje.
- Latencia mínima: las llamadas al LOM son in-process; el único hop es el socket local.

**Negativas / costos**
- Dependemos de la API no oficial de Remote Scripts → riesgo de cambios entre versiones
  de Live (mitigado por una capa de adaptación; ver contrato y nota Live 11 vs 12 en
  `04_api_contracts.md`).
- El intérprete embebido de Live limita librerías de terceros: el Remote Script debe
  mantenerse con **stdlib pura** (socket, json, threading). Toda lógica pesada vive en
  el servidor MCP (proceso normal con su propio venv).
- No hay hot-reload: cada cambio del script exige reiniciar Live (afecta DX, no runtime).

### Trade-offs visibles para el PO
- **Costo/plazo:** menor que M4L (sin licencia/depependencia de Max, un solo lenguaje).
- **Cobertura:** Remote Script es la ÚNICA opción que cubre Live Standard; M4L habría
  excluido a una parte de los usuarios → decisión de producto, no solo técnica.
- **UX:** sin impacto para el usuario final; la limitación (reiniciar Live) es solo de
  desarrollo.

---
