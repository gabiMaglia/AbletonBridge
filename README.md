# abletonBridge

Puente entre Claude (via MCP) y Ableton Live, usando un **Remote Script**
que vive dentro de Live y un **servidor MCP** que corre como proceso
externo. Ver decisiones en `engram/02_architecture.md` (ADR-001) y el
contrato completo en `engram/04_api_contracts.md`.

## Estructura del repo

```
remote_script/AbletonBridge/   # corre DENTRO de Ableton Live (stdlib pura)
  protocol.py                  # framing newline-JSON (lado servidor)
  errors.py                    # catalogo de codigos de error
  dispatcher.py                # cola thread-safe -> hilo de UI de Live
  server.py                    # servidor TCP (thread aparte)
  handlers.py                  # ping/state.get/probe.api (LOM, hilo principal)
  surface.py                   # ControlSurface + pump; create_instance en __init__

mcp_server/abletonbridge_mcp/  # proceso normal, venv propio
  protocol.py                  # framing newline-JSON (lado cliente)
  client.py                    # cliente TCP: connect, ping, reconexion
  server.py                    # tools MCP (live_ping, live_get_state, live_probe_api)

tests/                         # pytest: protocolo, dispatcher, cliente,
                                # servidor real (sockets locales), tools
```

**Por que dos paquetes independientes y no uno compartido:** el Remote
Script corre en el interprete embebido de Live, que NO tiene `pip` libre
y debe limitarse a stdlib (`socket`, `json`, `threading`). El servidor
MCP es un proceso normal con su propio venv. `remote_script/` y
`mcp_server/` no se importan entre si para que ningun cambio futuro en
el servidor MCP rompa accidentalmente esa restriccion.

## Instalacion del Remote Script en Ableton Live (11 y 12)

Live carga los Remote Scripts desde una carpeta especifica del sistema.
Esto es **instalacion manual** (copiar carpeta + reiniciar Live) — no hay
instalador automatico en este ticket.

### Windows

1. Cerrar Ableton Live si esta abierto.
2. Copiar la carpeta `remote_script/AbletonBridge/` completa (debe quedar
   `AbletonBridge\__init__.py` directamente dentro) a:
   ```
   %USERPROFILE%\Documents\Ableton\User Library\Remote Scripts\AbletonBridge\
   ```
   (crear `Remote Scripts` si no existe). Si moviste la User Library
   (`Preferences` → `Library`), usar esa ubicacion.
   > Nota: en Live 11 y anteriores tambien se usaba
   > `%APPDATA%\Ableton\Live <version>\Preferences\User Remote Scripts\`;
   > no verificado para Live 12.
3. Abrir Ableton Live → `Preferences` → `Link, Tempo & MIDI` → en
   **Control Surface** (cualquier slot libre) elegir `AbletonBridge`.
   Input/Output pueden quedar en `None`.
4. Reiniciar Live si `AbletonBridge` no aparece en la lista.
5. Log de Live: `%APPDATA%\Ableton\Live 12.4.16\Preferences\Log.txt`
   (tambien `Help` → `Show Log Files`). Buscar `AbletonBridge: listening
   on 127.0.0.1 port <N>`; si hubo error aparece `AbletonBridge: init
   error`.

### macOS

1. Cerrar Ableton Live si esta abierto.
2. Copiar la carpeta `remote_script/AbletonBridge/` a:
   ```
   ~/Music/Ableton/User Library/Remote Scripts/
   ```
   (crear la carpeta `Remote Scripts` si no existe).
3. Mismo paso 3 y 4 que en Windows (`Preferences` → `MIDI` →
   `Control Surfaces` → `AbletonBridge`).

> **Nota de compatibilidad Live 11/12:** la ruta exacta de "User Remote
> Scripts" puede variar segun version de Live; si no aparece la opcion,
> verificar la documentacion de Ableton para la version instalada. El
> Remote Script detecta `api_level` (11 o 12) en el handshake `ping` y
> elige el adaptador correcto internamente — no requiere pasos manuales
> distintos por version.

### Verificacion manual (PO / QA — Claude no puede ejecutar este paso)

No hay Ableton Live disponible en el entorno donde se desarrollo T-002,
asi que **el handshake real contra Live 11 y Live 12 NO fue probado** y
no debe asumirse que funciona sin esta verificacion manual:

1. Instalar el Remote Script segun el OS (arriba) y seleccionarlo en
   Live.
2. Revisar el log de Live (`Help` → `Show Log Files`) para confirmar que
   no hay errores al cargar `AbletonBridge` y que el socket abrio
   (puerto 19845 o el primer libre en 19845-19855).
3. Correr el servidor MCP (ver abajo) y verificar que `live_ping`
   devuelve `{ pong: true, live_version: "...", api_level: 11|12 }`.
   Luego `live_probe_api(client)` devuelve que miembros del LOM existen
   en tu version de Live (insumo para decidir F2+).
4. Repetir en Live 11 y en Live 12 (criterio de aceptacion T-002 exige
   ambos).

## Servidor MCP — desarrollo local

```bash
python -m venv .venv
source .venv/bin/activate   # o .venv\Scripts\activate en Windows
pip install -r requirements.txt
```

Uso minimo (handshake + estado), una vez el Remote Script esta corriendo
dentro de Live:

```python
from mcp_server.abletonbridge_mcp.client import BridgeClient
from mcp_server.abletonbridge_mcp.server import live_ping, live_get_state

client = BridgeClient(host="127.0.0.1", port=19845)
client.connect_with_retry()
print(live_ping(client))
print(live_get_state(client))
```

## Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

Los tests cubren: framing newline-JSON (encode/decode, ambos lados),
catalogo de errores, el `UIDispatcher` (cola thread-safe hacia el hilo de
UI de Live), el `BridgeClient` contra un Remote Script mockeado
(handshake, correlacion por `id`, timeout, reconexion con backoff), el
`BridgeServer` real contra sockets locales (bind + fallback de puerto,
ping end-to-end, comando desconocido), y las tools MCP (`live_ping`,
`live_get_state`) end-to-end contra el mock.

**Lo que NO cubren estos tests** (no testeable sin Ableton instalado):
carga real del Remote Script por Live, handshake real contra Live 11 y
12, y cualquier operacion sobre el LOM real (`song.*`). Ver seccion de
verificacion manual arriba.
