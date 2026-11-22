"""
Version del bridge + marca de carga del modulo.

`LOADED_AT` se re-evalua en cada `importlib.reload`, asi el cliente confirma que un
`bridge.reload` tomo efecto comparando el timestamp. Subir VERSION a mano al cambiar el protocolo.
"""
import time

VERSION = "0.2.0"
LOADED_AT = time.time()
