import importlib.util

# El motor tiene sus propias dependencias (nexo_analysis/requirements.txt); sin ellas se omite.
_DEPS = ("numpy", "scipy", "soundfile", "pyloudnorm")
collect_ignore_glob = [] if all(importlib.util.find_spec(m) for m in _DEPS) else ["test_*.py"]
