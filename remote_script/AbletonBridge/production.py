"""
Comandos de produccion v1 (T-003): permanentes, params tipados, sin exec/eval.

Corren SIEMPRE en el hilo principal de Live (via dispatcher). Reciben `song`
(y `live` cuando hace falta) para testearse con un LOM falso. Los errores de
validacion salen como errors.CommandError con su codigo; los de la API de Live
se dejan subir (el servidor los responde como LOM_ERROR) salvo en los pasos
multi-operacion, que se reportan como {ok, error} sin abortar el resto.
Stdlib pura.
"""
import math
import os
import re
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from . import errors, lom_read
from .errors import CommandError

AUDIO_EXTENSIONS = (".wav", ".aif", ".aiff", ".mp3", ".flac")
# VERIFICAR EN LIVE: Clip.warp_mode (0 Beats,1 Tones,2 Texture,3 Re-Pitch,4 Complex,6 Complex Pro)
WARP_MODES = (0, 1, 2, 3, 4, 6)
EPS = 1e-6
SPAN_TOL = 0.01
ONE_SHOT_TOL = 0.05
MARKER_TOL = 1e-3
DB_TOLERANCE = 0.1
MAX_COPIES = 512
_NEG_INF = -1e9
_DB_RE = re.compile(r"[-+]?\d+(?:[.,]\d+)?")


def _bad(message: str) -> CommandError:
    return CommandError(errors.INVALID_PARAMS, message)


def _is_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _num(params: Dict[str, Any], key: str, lo: Optional[float] = None, hi: Optional[float] = None,
         positive: bool = False) -> Optional[float]:
    """Numero opcional validado. `positive` = estrictamente > 0."""
    if key not in params or params[key] is None:
        return None
    v = params[key]
    if not _is_num(v):
        raise _bad(f"{key} must be a number")
    if positive and v <= 0:
        raise _bad(f"{key} must be > 0")
    if lo is not None and v < lo:
        raise _bad(f"{key} must be >= {lo}")
    if hi is not None and v > hi:
        raise _bad(f"{key} must be <= {hi}")
    return float(v)


def _req_num(params: Dict[str, Any], key: str, **kw: Any) -> float:
    v = _num(params, key, **kw)
    if v is None:
        raise _bad(f"{key} is required")
    return v


def _opt_bool(params: Dict[str, Any], key: str) -> Optional[bool]:
    if key not in params or params[key] is None:
        return None
    if not isinstance(params[key], bool):
        raise _bad(f"{key} must be a boolean")
    return params[key]


def _opt_int(params: Dict[str, Any], key: str, lo: int, hi: int) -> Optional[int]:
    if key not in params or params[key] is None:
        return None
    v = params[key]
    if not _is_int(v) or not lo <= v <= hi:
        raise _bad(f"{key} must be an integer in [{lo}, {hi}]")
    return v


def _name(params: Dict[str, Any], key: str) -> str:
    v = params.get(key)
    if not isinstance(v, str) or not v.strip():
        raise _bad(f"{key} must be a non-empty string")
    return v


def _track(song: Any, params: Dict[str, Any], key: str = "track") -> Tuple[int, Any]:
    idx = params.get(key)
    if not _is_int(idx) or not 0 <= idx < len(song.tracks):
        raise CommandError(errors.TRACK_NOT_FOUND, f"track {idx!r} not found")
    return idx, song.tracks[idx]


def _return(song: Any, params: Dict[str, Any]) -> Tuple[int, Any]:
    idx = params.get("return")
    if not _is_int(idx) or not 0 <= idx < len(song.return_tracks):
        raise CommandError(errors.TRACK_NOT_FOUND, f"return {idx!r} not found")
    return idx, song.return_tracks[idx]


def _step(steps: Dict[str, Any], name: str, fn: Callable[[], Any]) -> Tuple[bool, Any]:
    try:
        value = fn()
        steps[name] = {"ok": True, "error": None}
        return True, value
    except Exception as exc:  # noqa: BLE001 - reportar sin abortar el resto
        steps[name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        return False, None


def valid_audio_path(path: Any) -> bool:
    return (
        isinstance(path, str) and os.path.isabs(path)
        and path.lower().endswith(AUDIO_EXTENSIONS) and os.path.isfile(path)
    )


def _audio_path(params: Dict[str, Any], key: str = "path") -> str:
    path = params.get(key)
    if not valid_audio_path(path):
        raise _bad("path must be an absolute path to an existing audio file "
                   f"({', '.join(AUDIO_EXTENSIONS)})")
    return path


# --- dB <-> raw ----------------------------------------------------------


def parse_db(text: Any) -> Optional[float]:
    """'-6.2 dB' -> -6.2, '-inf dB' -> -inf, sin numero -> None."""
    if not isinstance(text, str):
        return None
    t = text.strip().replace("−", "-").lower()
    if "inf" in t:
        return -math.inf if "-" in t else math.inf
    m = _DB_RE.search(t)
    return float(m.group(0).replace(",", ".")) if m else None


def parse_display(text: Any) -> Optional[float]:
    """Como parse_db pero normaliza unidades: kHz -> Hz, s -> ms. None si no es un numero."""
    v = parse_db(text)
    if v is None or math.isinf(v) or not isinstance(text, str):
        return v
    t = text.lower()
    if re.search(r"\d\s*/\s*\d", t):  # divisiones musicales ("1/4"): no hay escala numerica
        return None
    if re.search(r"\d\s*khz", t):
        return v * 1000.0
    if re.search(r"\d\s*s\b", t):  # "1.5 s"; "200 ms" no matchea
        return v * 1000.0
    return v


def find_raw_for_db(lo: float, hi: float, display_of: Callable[[float], Any],
                    target: float, tol: float = DB_TOLERANCE,
                    parse: Callable[[Any], Optional[float]] = parse_db) -> Tuple[float, bool]:
    """
    Biseccion sobre [lo, hi] (display monotono, creciente o decreciente) buscando el valor
    crudo cuyo display se acerca a `target`. Devuelve (crudo, dentro_de_tolerancia).
    """
    def db(raw: float) -> float:
        d = parse(display_of(raw))
        if d is None:
            raise ValueError("display is not parseable as a number")
        return _NEG_INF if d == -math.inf else d

    best, best_err = lo, abs(db(lo) - target)
    err_hi = abs(db(hi) - target)
    if err_hi < best_err:
        best, best_err = hi, err_hi
    increasing = db(hi) >= db(lo)
    a, b = lo, hi
    for _ in range(48):
        if best_err <= tol + 1e-9:
            break
        mid = (a + b) / 2.0
        d = db(mid)
        err = abs(d - target)
        if err < best_err:
            best, best_err = mid, err
        if (d < target) == increasing:
            a = mid
        else:
            b = mid
    return best, best_err <= tol + 1e-9


DISPLAY_TOL_FRAC = 0.005  # tolerancia de display por unidad: 0.5% del rango del parametro


def _raw_for_display(param: Any, target: float) -> Tuple[float, bool]:
    """Crudo de `param` cuyo str_for_value se acerca a `target` (unidad del display). (crudo, within)."""
    lo, hi = float(param.min), float(param.max)

    def shown(raw: float) -> Any:
        return param.str_for_value(raw)

    try:
        d_lo, d_hi = parse_display(shown(lo)), parse_display(shown(hi))
        if d_lo is None or d_hi is None:
            raise ValueError("unparseable")
        raw, _ = find_raw_for_db(lo, hi, shown, target, tol=1e-9, parse=parse_display)
        got = parse_display(shown(raw))
    except ValueError:
        raise _bad(f"parameter {param.name!r}: display {shown(lo)!r} is not numeric, "
                   "so a value by unit cannot be resolved (use raw value)") from None
    span = abs(d_hi - d_lo)
    tol = DISPLAY_TOL_FRAC * span if math.isfinite(span) else DB_TOLERANCE
    return raw, got is not None and abs(got - target) <= tol


def _db_arg(params: Dict[str, Any], key: str) -> Optional[Tuple[Optional[float], bool]]:
    """(objetivo_dB, es_-inf) o None si la clave no vino."""
    raw = params.get(key)
    if raw is None:
        return None
    if isinstance(raw, str):
        if raw.strip().lower() not in ("-inf", "-infinity"):
            raise _bad(f"{key} must be a number or '-inf'")
        return None, True
    if not _is_num(raw):
        raise _bad(f"{key} must be a number or '-inf'")
    return float(raw), False


def _set_db(param: Any, target: Tuple[Optional[float], bool]) -> Dict[str, Any]:
    """Biseccion de `param` (volume/send) hasta `target` dB; readback + within_tolerance."""
    db, minus_inf = target
    within = True
    if minus_inf:
        param.value = param.min
    else:
        raw, within = find_raw_for_db(float(param.min), float(param.max), param.str_for_value, db)
        param.value = raw
    return dict(_readback(param), within_tolerance=within)


def _readback(param: Any) -> Dict[str, Any]:
    return {"value": float(param.value), "display": param.str_for_value(param.value)}


# --- song.set ------------------------------------------------------------


def song_set(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    tempo = _num(params, "tempo", lo=20.0, hi=999.0)
    numerator = _opt_int(params, "signature_numerator", 1, 99)
    denominator = _opt_int(params, "signature_denominator", 1, 16)
    if denominator is not None and denominator not in (1, 2, 4, 8, 16):
        raise _bad("signature_denominator must be one of 1, 2, 4, 8, 16")
    loop_start = _num(params, "loop_start", lo=0.0)
    loop_length = _num(params, "loop_length", positive=True)
    loop_on = _opt_bool(params, "loop_on")

    if tempo is not None:
        song.tempo = tempo
    if numerator is not None:
        song.signature_numerator = numerator
    if denominator is not None:
        song.signature_denominator = denominator
    if loop_start is not None:
        song.loop_start = loop_start
    if loop_length is not None:
        song.loop_length = loop_length
    if loop_on is not None:
        song.loop = loop_on
    return {
        "tempo": float(song.tempo),
        "signature_numerator": int(song.signature_numerator),
        "signature_denominator": int(song.signature_denominator),
        "loop_start": float(song.loop_start),
        "loop_length": float(song.loop_length),
        "loop_on": bool(song.loop),
    }


# --- track.create / track.delete / track.set_mixer -------------------------


def track_create(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    kind = params.get("kind")
    if kind not in ("audio", "midi"):
        raise _bad("kind must be 'audio' or 'midi'")
    name = _name(params, "name")
    index = params.get("index", -1)
    if not _is_int(index) or not -1 <= index <= len(song.tracks):
        raise _bad(f"index must be -1 (append) or an integer in [0, {len(song.tracks)}]")
    if kind == "audio":
        song.create_audio_track(index)
    else:
        song.create_midi_track(index)
    real = len(song.tracks) - 1 if index == -1 else index
    song.tracks[real].name = name
    return {"index": real, "name": str(song.tracks[real].name)}


def track_delete(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    idx, track = _track(song, params)
    confirm = params.get("confirm_name")
    current = str(track.name)
    if not isinstance(confirm, str) or confirm != current:
        raise _bad(f"confirm_name must equal the track's current name ({current!r})")
    song.delete_track(idx)
    return {"deleted": current, "index": idx, "track_count": len(song.tracks)}


def _apply_mixer(track: Any, params: Dict[str, Any], out: Dict[str, Any], allow_solo: bool) -> Dict[str, Any]:
    """Cuerpo comun de track.set_mixer / return.set_mixer (valida todo antes de escribir)."""
    vol = _db_arg(params, "volume_db")
    pan = _num(params, "pan", lo=-1.0, hi=1.0)
    mute = _opt_bool(params, "mute")
    solo = _opt_bool(params, "solo") if allow_solo else None
    if not allow_solo and params.get("solo") is not None:
        raise _bad("solo is not available on return tracks")

    mixer = track.mixer_device
    if vol is not None:
        out["volume"] = _set_db(mixer.volume, vol)
    if pan is not None:
        mixer.panning.value = pan
        out["panning"] = _readback(mixer.panning)
    if mute is not None:
        track.mute = mute
        out["mute"] = bool(track.mute)
    if solo is not None:
        track.solo = solo
        out["solo"] = bool(track.solo)
    return out


def track_set_mixer(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    idx, track = _track(song, params)
    return _apply_mixer(track, params, {"track": idx}, allow_solo=True)


# --- sends / returns (T-009) -------------------------------------------------


def track_set_send(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    _, track = _track(song, params)
    send = params.get("send")
    sends = list(track.mixer_device.sends)
    if not _is_int(send) or not 0 <= send < len(sends):
        raise _bad(f"send must be an integer in [0, {len(sends) - 1}]")
    target = _db_arg(params, "db")
    if target is None:
        raise _bad("db is required (number or '-inf')")
    return _set_db(sends[send], target)


def return_list(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    # Envuelto en dict: el protocolo es de objetos y el cliente convierte [] vacio en {}
    returns = [
        {"index": i, "name": str(t.name), "devices": [str(d.name) for d in t.devices],
         "volume": _readback(t.mixer_device.volume)}
        for i, t in enumerate(song.return_tracks)
    ]
    return {"returns": returns, "count": len(returns)}


def return_set_mixer(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    idx, track = _return(song, params)
    return _apply_mixer(track, params, {"return": idx}, allow_solo=False)


def return_create(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    name = params.get("name")
    if name is not None:
        name = _name(params, "name")
    song.create_return_track()  # VERIFICAR EN LIVE: sin argumentos, agrega al final
    idx = len(song.return_tracks) - 1
    if name is not None:
        song.return_tracks[idx].name = name
    return {"index": idx, "name": str(song.return_tracks[idx].name)}


# --- envelopes de clip (T-010) -------------------------------------------------

ENV_STEP = 0.25  # beats por paso de la rampa
MAX_ENVELOPES = 16
MAX_ENV_POINTS = 256
POINTS_SPANS = ("tile", "range")


def _env_param(track: Any, target: Any) -> Tuple[Any, Any]:
    """(parametro, etiqueta del target) para un target de envelope sobre `track`."""
    mixer = track.mixer_device
    if target == "volume":
        return mixer.volume, "volume"
    if target == "pan":
        return mixer.panning, "pan"
    if isinstance(target, dict) and set(target) == {"send"}:
        sends = list(mixer.sends)
        idx = target["send"]
        if not _is_int(idx) or not 0 <= idx < len(sends):
            raise _bad(f"target.send must be an integer in [0, {len(sends) - 1}]")
        return sends[idx], {"send": idx}
    if isinstance(target, dict) and set(target) == {"device", "param"}:
        _, dev = _device(track, {"device": target["device"]})
        name = target["param"]
        param = next((p for p in dev.parameters if p.name == name), None) if isinstance(name, str) else None
        if param is None:
            raise _bad(f"target.param {name!r} not found on the device (exact API name)")
        return param, {"device": target["device"], "param": name}
    raise _bad('target must be "volume", "pan", {"send": i} or {"device": index|name, "param": name}')


def _env_points(param: Any, raw_points: Any, label: str, notes: List[str]) -> List[Tuple[float, float]]:
    if not isinstance(raw_points, list) or not 1 <= len(raw_points) <= MAX_ENV_POINTS:
        raise _bad(f"{label}: points must be a list of 1..{MAX_ENV_POINTS} [time, value] pairs")
    lo, hi = float(param.min), float(param.max)
    cache: Dict[float, float] = {}
    out: List[Tuple[float, float]] = []
    for i, pt in enumerate(raw_points):
        if not isinstance(pt, (list, tuple)) or len(pt) != 2:
            raise _bad(f"{label}: points[{i}] must be [time, value]")
        t, v = pt
        if not _is_num(t) or t < 0:
            raise _bad(f"{label}: points[{i}] time must be a number >= 0")
        if out and t <= out[-1][0]:
            raise _bad(f"{label}: point times must be strictly increasing")
        if isinstance(v, dict):
            target = v.get("display")
            if set(v) != {"display"} or not _is_num(target):
                raise _bad(f'{label}: points[{i}] value must be a number or {{"display": number}}')
            if target not in cache:
                raw, within = _raw_for_display(param, float(target))
                cache[target] = raw
                if not within:
                    notes.append(f"{label}: display {target} not reachable; closest is "
                                 f"{param.str_for_value(raw)}")
            value = cache[target]
        elif _is_num(v) and lo - EPS <= v <= hi + EPS:
            value = min(max(float(v), lo), hi)
        else:
            raise _bad(f"{label}: points[{i}] value must be a number in [{lo}, {hi}] or "
                       '{"display": number}')
        out.append((float(t), value))
    return out


def _parse_envelopes(track: Any, params: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[str], str]:
    """Valida TODO antes de tocar el set. (specs, avisos, points_span)."""
    mode = params.get("points_span", "tile")
    if mode not in POINTS_SPANS:
        raise _bad(f"points_span must be one of {POINTS_SPANS}")
    raw = params.get("envelopes")
    if raw is None:
        return [], [], mode
    if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_ENVELOPES:
        raise _bad(f"envelopes must be a list of 1..{MAX_ENVELOPES} objects")
    specs: List[Dict[str, Any]] = []
    notes: List[str] = []
    for i, env in enumerate(raw):
        if not isinstance(env, dict) or "target" not in env:
            raise _bad(f"envelopes[{i}] must be an object with target and points")
        param, label = _env_param(track, env["target"])
        specs.append({"label": label, "param": param, "param_name": str(param.name),
                      "points": _env_points(param, env.get("points"), f"envelopes[{i}]", notes)})
    return specs, notes, mode


def _interp(points: List[Tuple[float, float]], t: float) -> float:
    """Valor de la poligonal en `t`; fuera de los puntos se sostiene el primero/ultimo."""
    if t <= points[0][0]:
        return points[0][1]
    for (t0, v0), (t1, v1) in zip(points, points[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    return points[-1][1]


def _write_envelopes(clip: Any, specs: List[Dict[str, Any]], offset: float, required: float,
                     mode: str) -> List[Dict[str, Any]]:
    """
    Escribe cada envelope en el clip de SESSION como rampa de pasos de ENV_STEP beats. En modo
    "range" el tile muestrea la poligonal desplazada `offset` (su inicio dentro del rango).
    Un envelope que falla se reporta; no aborta el resto.
    """
    reports: List[Dict[str, Any]] = []
    count = max(1, int(math.ceil(required / ENV_STEP - EPS)))
    shift = offset if mode == "range" else 0.0
    for spec in specs:
        entry: Dict[str, Any] = {"target": spec["label"], "param": spec["param_name"]}
        try:
            env = clip.create_automation_envelope(spec["param"])
            if env is None:  # VERIFICAR EN LIVE: create_* puede no devolver el envelope
                env = clip.automation_envelope(spec["param"])
            for i in range(count):
                s = i * ENV_STEP
                env.insert_step(s, min(ENV_STEP, required - s), _interp(spec["points"], s + shift))
            entry.update(ok=True, steps=count)
        except Exception as exc:  # noqa: BLE001 - un envelope roto no frena a los demas
            entry.update(ok=False, error=f"{type(exc).__name__}: {exc}")
        reports.append(entry)
    return reports


# --- clip.place_audio ----------------------------------------------------


def _find_arrangement_clip(track: Any, position: float) -> Any:
    for clip in track.arrangement_clips:
        if abs(float(clip.start_time) - position) < EPS:
            return clip
    return None


def _set_range(clip: Any, start_attr: str, end_attr: str, start: float, end: float) -> None:
    """Pone start/end sin cruzarlos: si el nuevo inicio pasa del fin actual, primero el fin."""
    if start >= getattr(clip, end_attr):
        setattr(clip, end_attr, end)
        setattr(clip, start_attr, start)
    else:
        setattr(clip, start_attr, start)
        setattr(clip, end_attr, end)


def _span(clip: Any) -> Optional[float]:
    """Largo real en Arrangement (end_time - start_time); NO es clip.length."""
    start = lom_read.safe(lambda: float(clip.start_time))
    end = lom_read.safe(lambda: float(clip.end_time))
    return end - start if isinstance(start, float) and isinstance(end, float) else None


def _clip_summary(clip: Any, method: str) -> Dict[str, Any]:
    return {
        "start_time": lom_read.get(clip, "start_time"),
        "end_time": lom_read.get(clip, "end_time"),
        "span": _span(clip),
        "length": lom_read.get(clip, "length"),
        "warp_mode": lom_read.get(clip, "warp_mode"),
        "warping": lom_read.get(clip, "warping"),
        "pitch_coarse": lom_read.get(clip, "pitch_coarse"),
        "method": method,
    }


def _gain_display(clip: Any, raw: float) -> Any:
    clip.gain = raw
    return clip.gain_display_string


class _Scratch:
    """
    Slot de Session vacio para armar tiles parciales (el clip de Session fija el span al
    duplicarlo). Si el track no tiene slot libre crea una escena, y la borra al liberar.
    """

    def __init__(self, song: Any, track: Any) -> None:
        self._song, self._track = song, track
        self._scene: Optional[int] = None
        self.slot: Any = None

    def acquire(self) -> Any:
        if self.slot is not None:
            return self.slot
        for slot in self._track.clip_slots:
            if not slot.has_clip:
                self.slot = slot
                return slot
        self._song.create_scene(-1)  # VERIFICAR EN LIVE: -1 agrega al final
        self._scene = len(self._song.scenes) - 1
        self.slot = self._track.clip_slots[self._scene]
        return self.slot

    def release(self, steps: Dict[str, Any]) -> None:
        if self.slot is not None and self.slot.has_clip:
            _step(steps, "scratch_delete_clip", lambda: self.slot.delete_clip())
        if self._scene is not None:
            _step(steps, "scratch_delete_scene", lambda: self._song.delete_scene(self._scene))


def _apply_clip_settings(clip: Any, key: str, warp_mode: Optional[int], pitch: Optional[int],
                         steps: Dict[str, Any]) -> None:
    if warp_mode is not None:
        _step(steps, f"{key}_warp_mode", lambda: setattr(clip, "warp_mode", warp_mode))
    if pitch is not None:
        _step(steps, f"{key}_pitch", lambda: setattr(clip, "pitch_coarse", pitch))


def _session_tile(track: Any, scratch: _Scratch, path: str, pos: float,
                  required: Union[float, Callable[[Any], float]],
                  section_start: Optional[float], key: str, steps: Dict[str, Any],
                  setup: Callable[[Any], None],
                  finish: Optional[Callable[[Any, float], None]] = None) -> Tuple[bool, float]:
    """
    Arma el tile en el slot scratch (loop == `required`) y lo duplica al Arrangement en `pos`.
    `required` puede ser una funcion del clip de Session (largo natural recortado a lo que
    falta). `finish(clip, required)` corre con el loop ya fijado y antes de duplicar (envelopes).
    Devuelve (ok, required). El clip de Arrangement se re-busca aparte.
    """
    ok, slot = _step(steps, f"{key}_scratch", scratch.acquire)
    if not ok:
        return False, 0.0
    ok, _ = _step(steps, f"{key}_session_create", lambda: slot.create_audio_clip(path))
    if not ok:
        return False, 0.0
    clip = slot.clip  # nunca se confia en lo que devuelve create_audio_clip
    setup(clip)
    if callable(required):
        resolve = required
        ok, value = _step(steps, f"{key}_natural", lambda: float(resolve(clip)))
        if not ok or value <= EPS:
            _step(steps, f"{key}_scratch_clear", lambda: slot.delete_clip())
            return False, 0.0
        required = value
    base = section_start
    if base is None:
        base = lom_read.safe(lambda: float(clip.start_marker))
        base = base if isinstance(base, float) else 0.0
    # VERIFICAR EN LIVE: orden/aceptacion de loop_end y end_marker menores al natural
    _step(steps, f"{key}_loop", lambda: _set_range(clip, "loop_start", "loop_end", base, base + required))
    _step(steps, f"{key}_markers", lambda: _set_range(clip, "start_marker", "end_marker", base, base + required))
    _step(steps, f"{key}_looping", lambda: setattr(clip, "looping", True))
    if finish is not None:
        finish(clip, required)
    dup_ok, _ = _step(steps, f"{key}_duplicate", lambda: track.duplicate_clip_to_arrangement(clip, pos))
    _step(steps, f"{key}_scratch_clear", lambda: slot.delete_clip())
    return dup_ok, required


def _marker_rows(clip: Any) -> List[Dict[str, float]]:
    # VERIFICAR EN LIVE: warp_markers como objetos con beat_time/sample_time (o dicts)
    rows = []
    for m in clip.warp_markers:
        get = (lambda k: m[k]) if isinstance(m, dict) else (lambda k: getattr(m, k))
        rows.append({"beat_time": float(get("beat_time")), "sample_time": float(get("sample_time"))})
    return rows


def _add_warp_marker(clip: Any, beat_time: float, sample_time: float) -> None:
    """
    En Live 12.4 `Clip.add_warp_marker` recibe UN objeto warp marker, no (beat, sample):
    (float, float) da ArgumentError (visto en real). Se prueba Live.Clip.WarpMarker y, si no
    existe o no se acepta, un dict con las mismas claves (formato de la API de Max for Live).
    """
    candidates: List[Any] = []
    try:
        import Live  # solo existe dentro de Live

        marker_cls = getattr(Live.Clip, "WarpMarker", None)
        if marker_cls is not None:
            candidates.append(lambda: marker_cls(beat_time=beat_time, sample_time=sample_time))
    except ImportError:
        pass
    candidates.append(lambda: {"beat_time": beat_time, "sample_time": sample_time})
    errors: List[str] = []
    for build in candidates:
        try:
            clip.add_warp_marker(build())
            return
        except Exception as exc:  # noqa: BLE001 - se prueba la siguiente forma
            errors.append(f"{type(exc).__name__}: {exc}")
    raise RuntimeError("add_warp_marker rejected every form: " + " | ".join(errors))


def _force_warp_markers(clip: Any, sample_beats: float, secs: float) -> None:
    """
    Deja SOLO dos markers: (0 beat, 0 s) y (sample_beats, secs), asi todo el sample cae en
    `sample_beats` al tempo actual. Se agrega primero el del final y despues se borran los
    intermedios (incluido el ancla automatico pegado al inicio, ej. beat 0.03125).
    """
    if not any(abs(r["beat_time"] - sample_beats) <= MARKER_TOL for r in _marker_rows(clip)):
        _add_warp_marker(clip, sample_beats, secs)
    for row in _marker_rows(clip):
        beat = row["beat_time"]
        if abs(beat) > MARKER_TOL and abs(beat - sample_beats) > MARKER_TOL:
            clip.remove_warp_marker(beat)
    if not any(abs(r["beat_time"]) <= MARKER_TOL for r in _marker_rows(clip)):
        _add_warp_marker(clip, 0.0, 0.0)
    rows = sorted(_marker_rows(clip), key=lambda r: r["beat_time"])
    first, last = rows[0], rows[-1]
    if abs(first["beat_time"]) > MARKER_TOL or abs(first["sample_time"]) > MARKER_TOL:
        raise RuntimeError(f"first warp marker is {first}, expected beat 0 / sample 0")
    if abs(last["beat_time"] - sample_beats) > MARKER_TOL or abs(last["sample_time"] - secs) > MARKER_TOL:
        raise RuntimeError(f"last warp marker is {last}, expected beat {sample_beats} / sample {secs}")


ONE_SHOT_STRATEGIES = ("unwarped_session", "forced_markers", "move_end_marker")


def _must(steps: Dict[str, Any], name: str, fn: Callable[[], Any]) -> Any:
    """Como _step pero un fallo aborta la estrategia (el error queda en `steps` y en la excepcion)."""
    ok, value = _step(steps, name, fn)
    if not ok:
        raise RuntimeError(f"{name}: {steps[name]['error']}")
    return value


def _clip_diagnostics(clip: Any) -> Dict[str, Any]:
    """Lectura pura del clip de Session recien creado, para decidir con evidencia real."""
    diag: Dict[str, Any] = {k: lom_read.get(clip, k) for k in (
        "warping", "length", "start_marker", "end_marker", "loop_start", "loop_end",
        "sample_length", "sample_rate")}
    diag["warp_markers"] = lom_read.safe(lambda: _marker_rows(clip))
    return diag


def _prep_unwarped(clip: Any, secs: float, steps: Dict[str, Any], name: str) -> None:
    """A: sin warp loop/markers van en SEGUNDOS (LOM docs): el sample entero = [0, secs]."""
    _must(steps, f"{name}_warping", lambda: setattr(clip, "warping", False))
    _must(steps, f"{name}_loop", lambda: _set_range(clip, "loop_start", "loop_end", 0.0, secs))
    _step(steps, f"{name}_markers", lambda: _set_range(clip, "start_marker", "end_marker", 0.0, secs))
    _step(steps, f"{name}_looping", lambda: setattr(clip, "looping", False))


def _finish_warped(clip: Any, sample_beats: float, steps: Dict[str, Any], name: str) -> None:
    _step(steps, f"{name}_loop", lambda: _set_range(clip, "loop_start", "loop_end", 0.0, sample_beats))
    _step(steps, f"{name}_markers", lambda: _set_range(clip, "start_marker", "end_marker", 0.0, sample_beats))
    _step(steps, f"{name}_looping", lambda: setattr(clip, "looping", False))


def _prep_forced_markers(clip: Any, sample_beats: float, secs: float, mode: int,
                         steps: Dict[str, Any], name: str) -> None:
    """B: primero se extiende el clip (un marker mas alla de end_marker da 'Segment length out of range')."""
    _step(steps, f"{name}_warping", lambda: setattr(clip, "warping", True))
    _step(steps, f"{name}_warp_mode", lambda: setattr(clip, "warp_mode", mode))
    _step(steps, f"{name}_extend_end", lambda: setattr(clip, "end_marker", sample_beats))
    _step(steps, f"{name}_extend_loop", lambda: setattr(clip, "loop_end", sample_beats))
    _must(steps, f"{name}_warp_markers", lambda: _force_warp_markers(clip, sample_beats, secs))
    _finish_warped(clip, sample_beats, steps, name)


def _prep_move_end_marker(clip: Any, sample_beats: float, secs: float, mode: int,
                          steps: Dict[str, Any], name: str) -> None:
    """C: se ancla un marker en el fin actual del clip (dentro de rango) y se lo mueve a sample_beats."""
    _step(steps, f"{name}_warping", lambda: setattr(clip, "warping", True))
    _step(steps, f"{name}_warp_mode", lambda: setattr(clip, "warp_mode", mode))

    def move() -> None:
        end_beat = float(clip.end_marker)
        rows = _marker_rows(clip)
        last = max(rows, key=lambda r: r["beat_time"]) if rows else None
        if last is None or abs(last["beat_time"] - end_beat) > MARKER_TOL:
            # Se asume que el fin del clip auto-warpeado cae en el fin del sample
            _add_warp_marker(clip, end_beat, secs)
            last = {"beat_time": end_beat}
        if abs(last["beat_time"] - sample_beats) > MARKER_TOL:
            clip.move_warp_marker(last["beat_time"], sample_beats - last["beat_time"])

    _must(steps, f"{name}_move_marker", move)
    _step(steps, f"{name}_extend_end", lambda: setattr(clip, "end_marker", sample_beats))
    _step(steps, f"{name}_extend_loop", lambda: setattr(clip, "loop_end", sample_beats))
    _must(steps, f"{name}_warp_markers", lambda: _force_warp_markers(clip, sample_beats, secs))
    _finish_warped(clip, sample_beats, steps, name)


def _place_one_shot(song: Any, track: Any, idx: int, path: str, start: Optional[float],
                    end_beat: Optional[float], total: Optional[float], warp_mode: Optional[int],
                    pitch: Optional[int], gain_db: Optional[float]) -> Dict[str, Any]:
    """
    Una sola copia con el sample entero a `sample_beats` (sin loop). El span de Arrangement lo
    fija el clip de Session al duplicarlo; se prueban estrategias en orden hasta que el span
    duplicado coincida (ONE_SHOT_STRATEGIES). Entre estrategias se borra la copia y el clip scratch.
    """
    method = "session_duplicate_oneshot"
    steps: Dict[str, Any] = {}
    warnings: List[str] = []
    clips: List[Dict[str, Any]] = []
    gain_info: Optional[Dict[str, Any]] = {"applied": False} if gain_db is not None else None
    sample_beats: Optional[float] = None
    markers: Any = None
    span: Optional[float] = None
    strategy: Optional[str] = None
    strategy_errors: Dict[str, str] = {}
    diagnostics: Optional[Dict[str, Any]] = None
    gain_raw: Optional[float] = None
    scratch = _Scratch(song, track)
    mode = 4 if warp_mode is None else warp_mode

    try:
        ok, slot = _step(steps, "copy0_scratch", scratch.acquire)
        ok = ok and _step(steps, "copy0_session_create", lambda: slot.create_audio_clip(path))[0]
        if not ok:
            warnings.append("one_shot: could not build the clip in a Session slot; see steps")
        else:
            clip = slot.clip  # nunca se confia en lo que devuelve create_audio_clip
            diagnostics = _clip_diagnostics(clip)
            # VERIFICAR EN LIVE: Clip.sample_length (muestras) y sample_rate en un clip de Session
            got, secs = _step(steps, "copy0_sample_length",
                              lambda: float(clip.sample_length) / float(clip.sample_rate))
            if not got or secs <= EPS:
                warnings.append("one_shot: sample_length/sample_rate unavailable, "
                                "cannot compute the exact duration")
            else:
                sample_beats = secs * float(song.tempo) / 60.0
                if end_beat is not None:
                    start = end_beat - sample_beats
                    if start < -SPAN_TOL:
                        raise _bad(f"end_beat {end_beat} is before the sample length ({sample_beats} beats)")
                    start = max(start, 0.0)
                assert start is not None
                preps: Dict[str, Callable[[Any], None]] = {
                    "unwarped_session": lambda c: _prep_unwarped(c, secs, steps, "unwarped_session"),
                    "forced_markers": lambda c: _prep_forced_markers(
                        c, sample_beats, secs, mode, steps, "forced_markers"),
                    "move_end_marker": lambda c: _prep_move_end_marker(
                        c, sample_beats, secs, mode, steps, "move_end_marker"),
                }
                for name in ONE_SHOT_STRATEGIES:
                    if name != ONE_SHOT_STRATEGIES[0]:  # el primer clip se reusa en A; el resto, uno limpio
                        if slot.has_clip:
                            _step(steps, f"{name}_scratch_clear", lambda: slot.delete_clip())
                        if not _step(steps, f"{name}_session_create", lambda: slot.create_audio_clip(path))[0]:
                            strategy_errors[name] = steps[f"{name}_session_create"]["error"]
                            continue
                    clip = slot.clip
                    try:
                        preps[name](clip)
                        if pitch is not None:
                            _step(steps, f"{name}_pitch", lambda: setattr(clip, "pitch_coarse", pitch))
                        if gain_db is not None and gain_info is not None:
                            gain_raw = _apply_gain(clip, name, gain_db, gain_raw, steps, gain_info, warnings)
                        placed, err = _duplicate_one_shot(track, clip, start, sample_beats, name, steps)
                    except Exception as exc:  # noqa: BLE001 - se pasa a la siguiente estrategia
                        placed, err = None, str(exc)
                    if placed is not None:
                        strategy = name
                        clips.append(_clip_summary(placed, method))
                        span = clips[0]["span"]
                        markers = lom_read.safe(lambda: _marker_rows(placed))
                        break
                    strategy_errors[name] = err or "unknown error"
    finally:
        scratch.release(steps)
    if not clips:  # con exito, los intentos fallidos quedan solo en strategy_errors
        warnings.extend(f"one_shot[{n}]: {e}" for n, e in strategy_errors.items())
    if span is not None and total is not None and span > total + SPAN_TOL:
        warnings.append(f"one_shot: clip is {span} beats, longer than the requested {total} "
                        "(one_shot placement is start-only, not trimmed)")
    good = (bool(clips) and isinstance(span, float) and sample_beats is not None
            and abs(span - sample_beats) <= ONE_SHOT_TOL)
    out: Dict[str, Any] = {
        "ok": good, "track": idx, "clips": clips, "method": method, "strategy": strategy,
        "strategy_errors": strategy_errors, "diagnostics": diagnostics,
        "covered_beats": span if isinstance(span, float) else 0.0, "sample_beats": sample_beats,
        "warp_markers": markers if isinstance(markers, list) else None,
        "warnings": warnings, "steps": steps,
    }
    if gain_info is not None:
        out["gain"] = gain_info
    return out


def _duplicate_one_shot(track: Any, clip: Any, start: float, sample_beats: float, name: str,
                        steps: Dict[str, Any]) -> Tuple[Any, Optional[str]]:
    """
    Duplica al Arrangement; si el span no coincide reintenta con looping=True (span = loop).
    Devuelve (clip colocado, None) o (None, error) habiendo borrado cualquier copia mala.
    """
    last_span: Optional[float] = None
    for attempt in (0, 1):
        suffix = "" if attempt == 0 else "_retry"
        if attempt:
            _step(steps, f"{name}_looping{suffix}", lambda: setattr(clip, "looping", True))
        if not _step(steps, f"{name}_duplicate{suffix}",
                     lambda: track.duplicate_clip_to_arrangement(clip, start))[0]:
            return None, f"duplicate_clip_to_arrangement failed: {steps[f'{name}_duplicate{suffix}']['error']}"
        placed = _find_arrangement_clip(track, start)
        if placed is None:
            return None, f"clip not found in arrangement_clips at beat {start}"
        last_span = _span(placed)
        if last_span is not None and abs(last_span - sample_beats) <= ONE_SHOT_TOL:
            return placed, None
        gone = _step(steps, f"{name}_discard{suffix}", lambda: track.delete_clip(placed))[0]
        if not gone:
            return None, (f"expected span {sample_beats} beats but arrangement span is {last_span} "
                          "(and the bad copy could not be deleted)")
    return None, f"expected span {sample_beats} beats but arrangement span is {last_span}"


def clip_place_audio(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    idx, track = _track(song, params)
    if track.has_midi_input:
        raise _bad("track must be an audio track")
    path = _audio_path(params)
    start = _num(params, "start_beat", lo=0.0)
    end_beat = _num(params, "end_beat", positive=True)
    one_shot = bool(_opt_bool(params, "one_shot"))
    if end_beat is not None and not one_shot:
        raise _bad("end_beat is only valid with one_shot")
    if one_shot and (start is None) == (end_beat is None):
        raise _bad("one_shot needs exactly one of start_beat or end_beat")
    if start is None and not one_shot:
        raise _bad("start_beat is required")
    total = _num(params, "length_beats", positive=True)
    if total is None and not one_shot:
        raise _bad("length_beats is required (unless one_shot is true)")
    warp_mode = params.get("warp_mode")
    if warp_mode is not None and (not _is_int(warp_mode) or warp_mode not in WARP_MODES):
        raise _bad(f"warp_mode must be one of {WARP_MODES}")
    pitch = _opt_int(params, "pitch_coarse", -48, 48)
    gain_db = _num(params, "gain_db")
    loop_start = _num(params, "loop_start", lo=0.0)
    loop_end = _num(params, "loop_end", positive=True)
    if (loop_start is None) != (loop_end is None):
        raise _bad("loop_start and loop_end must be given together")
    if loop_start is not None and loop_end <= loop_start:
        raise _bad("loop_end must be > loop_start")
    env_specs, env_notes, env_mode = _parse_envelopes(track, params)
    if one_shot:
        if loop_start is not None:
            raise _bad("one_shot cannot be combined with loop_start/loop_end")
        if env_specs:
            raise _bad("one_shot cannot be combined with envelopes (they need the Session path)")
        return _place_one_shot(song, track, idx, path, start, end_beat, total, warp_mode, pitch, gain_db)

    steps: Dict[str, Any] = {}
    warnings: List[str] = []
    clips: List[Dict[str, Any]] = []
    gain_info: Optional[Dict[str, Any]] = {"applied": False} if gain_db is not None else None
    gain_raw: Optional[float] = None
    section = None if loop_start is None else loop_end - loop_start
    scratch = _Scratch(song, track)
    pos, remaining, n = start, total, 0
    trim_failed = False
    env_failed = False
    warnings.extend(env_notes)
    env_reports: Dict[str, List[Dict[str, Any]]] = {}

    def finish_for(key: str, tile_pos: float) -> Optional[Callable[[Any, float], None]]:
        if not env_specs:
            return None

        def run(clip: Any, required: float) -> None:
            env_reports[key] = _write_envelopes(clip, env_specs, tile_pos - start, required, env_mode)
        return run

    def setup(key: str) -> Callable[[Any], None]:
        def run(clip: Any) -> None:
            nonlocal gain_raw
            _apply_clip_settings(clip, key, warp_mode, pitch, steps)
            if gain_db is not None:
                gain_raw = _apply_gain(clip, key, gain_db, gain_raw, steps, gain_info, warnings)
        return run

    try:
        while remaining > EPS and n < MAX_COPIES:
            key = f"copy{n}"
            method = "session_duplicate"
            if section is not None:
                required = min(section, remaining)
                built, _ = _session_tile(track, scratch, path, pos, required, loop_start, key, steps,
                                         setup(key), finish_for(key, pos))
            elif env_specs:
                # Con envelopes TODO tile pasa por Session (los de Arrangement no se pueden escribir)
                left = remaining
                built, required = _session_tile(track, scratch, path, pos, lambda c: min(float(c.length), left),
                                                None, key, steps, setup(key), finish_for(key, pos))
            else:
                ok, clip = _step(steps, f"{key}_create", lambda: _new_audio_clip(track, path, pos))
                if not ok:
                    warnings.append(f"{key}: clip creation failed: {steps[f'{key}_create']['error']}")
                    break
                setup(key)(clip)
                natural = lom_read.safe(lambda: _span(clip))
                if not isinstance(natural, float) or natural <= EPS:
                    natural = lom_read.safe(lambda: float(clip.length))
                if not isinstance(natural, float) or natural <= EPS:
                    warnings.append(f"{key}: clip has no usable length ({natural}); stopped tiling")
                    clips.append(_clip_summary(clip, "create_audio_clip"))
                    break
                if natural <= remaining + EPS:
                    required, built, method = natural, True, "create_audio_clip"
                else:
                    # El tile natural pasaria del final: se descarta y se rearma con loop exacto
                    required = remaining
                    gone, _ = _step(steps, f"{key}_discard", lambda: track.delete_clip(clip))
                    if not gone:
                        warnings.append(f"{key}: could not discard the full-length clip; stopped")
                        trim_failed = True
                        break
                    built, _ = _session_tile(track, scratch, path, pos, required, None, key, steps, setup(key))
            if not built:
                warnings.append(f"{key}: session-slot build failed; see steps")
                trim_failed = True
                break
            placed = _find_arrangement_clip(track, pos)
            if placed is None:
                warnings.append(f"{key}: clip not found in arrangement_clips at beat {pos}")
                trim_failed = True
                break
            clips.append(_clip_summary(placed, method))
            if key in env_reports:
                clips[-1]["envelopes"] = env_reports[key]
                for e in env_reports[key]:
                    if not e["ok"]:
                        env_failed = True
                        warnings.append(f"{key}: envelope {e['target']} failed: {e['error']}")
            actual = _span(placed)
            if actual is None or abs(actual - required) > SPAN_TOL:
                warnings.append(f"{key}: requested {required} beats but arrangement span is "
                                f"{actual} beats (end_time - start_time); trim not applied")
                trim_failed = True
            pos += required
            remaining -= required
            n += 1
    finally:
        scratch.release(steps)

    if remaining > EPS and n >= MAX_COPIES:
        warnings.append(f"stopped after {MAX_COPIES} copies")
    covered = total - max(remaining, 0.0)
    ok_all = bool(clips) and remaining <= EPS and not trim_failed and not env_failed
    out: Dict[str, Any] = {
        "ok": ok_all, "track": idx, "clips": clips,
        "covered_beats": covered, "warnings": warnings, "steps": steps,
    }
    if gain_info is not None:
        out["gain"] = gain_info
    return out


def clip_delete_range(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    """Borra los clips de Arrangement contenidos por completo en [start_beat, end_beat]."""
    idx, track = _track(song, params)
    lo = _req_num(params, "start_beat", lo=0.0)
    hi = _req_num(params, "end_beat", positive=True)
    if hi <= lo:
        raise _bad("end_beat must be > start_beat")

    def inside(c: Any) -> bool:
        s, e = lom_read.safe(lambda: float(c.start_time)), lom_read.safe(lambda: float(c.end_time))
        return isinstance(s, float) and isinstance(e, float) and s >= lo - EPS and e <= hi + EPS

    deleted: List[Dict[str, Any]] = []
    warnings: List[str] = []
    for _ in range(MAX_COPIES * 4):
        # Se re-lee la lista en cada vuelta: borrar un clip puede invalidar las referencias
        victim = next((c for c in track.arrangement_clips if inside(c)), None)
        if victim is None:
            break
        span = {"start_time": float(victim.start_time), "end_time": float(victim.end_time)}
        try:
            track.delete_clip(victim)
        except Exception as exc:  # noqa: BLE001 - evitar bucle infinito sobre un clip que no se borra
            warnings.append(f"delete_clip failed at {span['start_time']}: {type(exc).__name__}: {exc}")
            break
        deleted.append(span)
    return {"track": idx, "deleted": deleted, "count": len(deleted), "warnings": warnings}


def _new_audio_clip(track: Any, path: str, position: float) -> Any:
    # VERIFICAR EN LIVE: create_audio_clip devuelve el Clip; si no, se busca por start_time
    clip = track.create_audio_clip(path, position)
    clip = clip if clip is not None else _find_arrangement_clip(track, position)
    if clip is None:
        raise RuntimeError("clip not found after create_audio_clip")
    return clip


def _apply_gain(clip: Any, key: str, gain_db: float, known_raw: Optional[float],
                steps: Dict[str, Any], info: Dict[str, Any], warnings: List[str]) -> Optional[float]:
    """La primera copia busca el crudo por biseccion contra gain_display_string; las demas reusan."""
    if known_raw is not None:
        _step(steps, f"{key}_gain", lambda: setattr(clip, "gain", known_raw))
        return known_raw
    if info.get("error"):
        return None  # ya fallo en una copia anterior; no se reintenta

    def search() -> float:
        # VERIFICAR EN LIVE: Clip.gain 0..1 y gain_display_string legible tras cada asignacion
        raw, within = find_raw_for_db(0.0, 1.0, lambda r: _gain_display(clip, r), gain_db)
        clip.gain = raw
        info.update(applied=True, value=float(clip.gain), display=clip.gain_display_string,
                    within_tolerance=within)
        return float(clip.gain)

    ok, raw = _step(steps, f"{key}_gain", search)
    if not ok:
        info["error"] = steps[f"{key}_gain"]["error"]
        warnings.append(f"gain_db skipped: {info['error']}")
        return None
    return raw


# --- clip.create_midi ----------------------------------------------------


def _notes(params: Dict[str, Any]) -> List[Dict[str, float]]:
    notes = params.get("notes")
    if not isinstance(notes, list):
        raise _bad("notes must be a list")
    out = []
    for i, n in enumerate(notes):
        if not isinstance(n, dict):
            raise _bad(f"notes[{i}] must be an object")
        pitch = n.get("pitch")
        if not _is_int(pitch) or not 0 <= pitch <= 127:
            raise _bad(f"notes[{i}].pitch must be an integer 0..127")
        start, dur, vel = n.get("start"), n.get("duration"), n.get("velocity")
        if not _is_num(start) or start < 0:
            raise _bad(f"notes[{i}].start must be a number >= 0")
        if not _is_num(dur) or dur <= 0:
            raise _bad(f"notes[{i}].duration must be a number > 0")
        if not _is_num(vel) or not 1 <= vel <= 127:
            raise _bad(f"notes[{i}].velocity must be a number in [1, 127]")
        out.append({"pitch": pitch, "start": float(start), "duration": float(dur), "velocity": float(vel)})
    return out


def clip_create_midi(song: Any, live: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    idx, track = _track(song, params)
    if not track.has_midi_input:
        raise CommandError(errors.NOT_MIDI_TRACK, f"track {idx} is not a MIDI track")
    start = _req_num(params, "start_beat", lo=0.0)
    length = _req_num(params, "length_beats", positive=True)
    notes = _notes(params)
    env_specs, env_notes, env_mode = _parse_envelopes(track, params)
    if env_specs:
        return _create_midi_with_envelopes(song, live, idx, track, start, length, notes,
                                           env_specs, env_notes, env_mode)

    # VERIFICAR EN LIVE: orden de argumentos de Track.create_midi_clip (start_time, length)
    clip = track.create_midi_clip(start, length)
    if clip is None:
        clip = _find_arrangement_clip(track, start)
    if clip is None:
        raise RuntimeError("clip not found after create_midi_clip")
    _add_notes(live, clip, notes)
    return _midi_summary(idx, clip, notes)


def _add_notes(live: Any, clip: Any, notes: List[Dict[str, float]]) -> None:
    if notes:
        spec = live.Clip.MidiNoteSpecification
        clip.add_new_notes(tuple(
            spec(pitch=n["pitch"], start_time=n["start"], duration=n["duration"], velocity=n["velocity"])
            for n in notes
        ))


def _midi_summary(idx: int, clip: Any, notes: List[Dict[str, float]]) -> Dict[str, Any]:
    count = lom_read.safe(lambda: len(clip.get_all_notes_extended()))
    return {
        "track": idx,
        "start_time": lom_read.get(clip, "start_time"),
        "end_time": lom_read.get(clip, "end_time"),
        "length": lom_read.get(clip, "length"),
        "name": lom_read.get(clip, "name"),
        "note_count": count if isinstance(count, int) else len(notes),
    }


def _create_midi_with_envelopes(song: Any, live: Any, idx: int, track: Any, start: float, length: float,
                                notes: List[Dict[str, float]], specs: List[Dict[str, Any]],
                                notes_warn: List[str], mode: str) -> Dict[str, Any]:
    """Clip MIDI armado en un slot de Session (notas + envelopes) y duplicado al Arrangement."""
    steps: Dict[str, Any] = {}
    scratch = _Scratch(song, track)
    reports: List[Dict[str, Any]] = []
    try:
        ok, slot = _step(steps, "scratch", scratch.acquire)
        if not ok:
            raise RuntimeError(f"no scratch slot: {steps['scratch']['error']}")
        slot.create_clip(length)  # VERIFICAR EN LIVE: ClipSlot.create_clip(length) en track MIDI
        clip = slot.clip
        _add_notes(live, clip, notes)
        reports = _write_envelopes(clip, specs, 0.0, length, mode)
        track.duplicate_clip_to_arrangement(clip, start)
        _step(steps, "scratch_clear", lambda: slot.delete_clip())
    finally:
        scratch.release(steps)
    placed = _find_arrangement_clip(track, start)
    if placed is None:
        raise RuntimeError("clip not found in arrangement_clips after duplicate_clip_to_arrangement")
    warnings = list(notes_warn)
    warnings += [f"envelope {e['target']} failed: {e['error']}" for e in reports if not e["ok"]]
    return dict(_midi_summary(idx, placed, notes), method="session_duplicate",
                ok=all(e["ok"] for e in reports), envelopes=reports, warnings=warnings, steps=steps)


# --- device.insert / device.set_param / simpler.load -------------------------


def _device(track: Any, params: Dict[str, Any]) -> Tuple[int, Any]:
    spec = params.get("device")
    devices = list(track.devices)
    if _is_int(spec):
        if 0 <= spec < len(devices):
            return spec, devices[spec]
    elif isinstance(spec, str):
        for i, d in enumerate(devices):
            if d.name == spec:
                return i, d
    raise _bad(f"device {spec!r} not found on the track (index or exact name)")


def _insert_device(track: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    name = _name(params, "name")
    index = params.get("index", -1)
    count = len(track.devices)
    if not _is_int(index) or not -1 <= index <= count:
        raise _bad(f"index must be -1 (append) or an integer in [0, {count}]")
    pos = count if index == -1 else index
    dev = track.insert_device(name, pos)
    if dev is None:  # VERIFICAR EN LIVE: insert_device puede no devolver el device
        dev = track.devices[pos]
    return {"index": pos, "class_name": lom_read.get(dev, "class_name"), "name": lom_read.get(dev, "name")}


def device_insert(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    return _insert_device(_track(song, params)[1], params)


def return_device_insert(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    return _insert_device(_return(song, params)[1], params)


def _set_device_param(track: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    dev_index, dev = _device(track, params)
    name = _name(params, "name")
    value, display = params.get("value"), params.get("display")
    if (value is None) == (display is None):
        raise _bad("give exactly one of value (raw) or display (number in the parameter's unit)")
    if not _is_num(value if display is None else display):
        raise _bad("value / display must be a number (value is raw, display is in the unit of str_for_value)")
    param = next((p for p in dev.parameters if p.name == name), None)
    if param is None:
        raise _bad(f"parameter {name!r} not found (exact, case-sensitive API name)")
    extra: Dict[str, Any] = {}
    if display is not None:
        raw, within = _raw_for_display(param, float(display))
        param.value = raw
        extra["within_tolerance"] = within
    else:
        if not float(param.min) - EPS <= value <= float(param.max) + EPS:
            raise _bad(f"value {value} outside [{param.min}, {param.max}]")
        param.value = float(value)
    return {"device": dev_index, "name": name, "min": float(param.min), "max": float(param.max),
            **_readback(param), **extra}


def device_set_param(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    return _set_device_param(_track(song, params)[1], params)


def return_device_set_param(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    return _set_device_param(_return(song, params)[1], params)


# --- master y sidechain (T-010) --------------------------------------------------


def master_device_insert(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    return _insert_device(song.master_track, params)


def master_device_set_param(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    return _set_device_param(song.master_track, params)


def master_set_mixer(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    vol = _db_arg(params, "volume_db")
    if vol is None:
        raise _bad("volume_db is required (number or '-inf')")
    return {"volume": _set_db(song.master_track.mixer_device.volume, vol)}


_TRACK_PREFIX = re.compile(r"^\d+\s*-\s*")


def _match_routing(types: List[Any], wanted: str) -> Any:
    """Tipo de ruteo cuyo display_name es el track pedido (exacto, sin mayusculas, o sin prefijo "N-")."""
    tiers: List[Callable[[str], bool]] = [
        lambda n: n == wanted,
        lambda n: n.lower() == wanted.lower(),
        lambda n: _TRACK_PREFIX.sub("", n).lower() == wanted.lower(),
    ]
    names = [str(t.display_name) for t in types]
    for tier in tiers:
        hits = [t for t, n in zip(types, names) if tier(n)]
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            raise _bad(f"source_track_name {wanted!r} is ambiguous among routing types {names}")
    raise _bad(f"no input routing type for {wanted!r}; available: {names}")


def compressor_set_sidechain(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    idx, track = _track(song, params)
    dev_index, dev = _device(track, params)
    source = _name(params, "source_track_name")
    if not (hasattr(dev, "available_input_routing_types") and hasattr(dev, "input_routing_type")):
        raise _bad(f"device {dev.name!r} does not expose input_routing_type / "
                   "available_input_routing_types (needs a Compressor on Live 11+)")
    match = _match_routing(list(dev.available_input_routing_types), source)
    wanted = str(match.display_name)

    steps: Dict[str, Any] = {}
    warnings: List[str] = []
    sc_params = [p for p in dev.parameters if "S/C" in p.name]
    sc_on = next((p for p in sc_params if p.name == "S/C On"), None)
    routed, _ = _step(steps, "set_input_routing_type", lambda: setattr(dev, "input_routing_type", match))
    if routed and sc_on is not None:
        _step(steps, "enable_sidechain", lambda: setattr(sc_on, "value", float(sc_on.max)))
    elif sc_on is None:
        warnings.append(f"parameter 'S/C On' not found; sidechain not enabled "
                        f"(S/C params: {[p.name for p in sc_params]})")

    def names(attr: str) -> Any:
        return lom_read.safe(lambda: [str(t.display_name) for t in getattr(dev, attr)])

    current = lom_read.safe(lambda: str(dev.input_routing_type.display_name))
    on = None if sc_on is None else bool(float(sc_on.value) >= 0.5)
    return {
        "ok": all(s["ok"] for s in steps.values()) and current == wanted and on is True,
        "track": idx, "device": dev_index,
        "input_routing_type": current,
        "available_input_routing_types": names("available_input_routing_types"),
        "input_routing_channel": lom_read.safe(lambda: str(dev.input_routing_channel.display_name)),
        "available_input_routing_channels": names("available_input_routing_channels"),
        "sidechain_on": on,
        "sc_params": [dict(name=p.name, **_readback(p)) for p in sc_params],
        "warnings": warnings, "steps": steps,
    }


def simpler_load(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    _, track = _track(song, params)
    dev_index, dev = _device(track, params)
    if not hasattr(dev, "replace_sample"):
        raise _bad("device is not a Simpler")
    path = _audio_path(params)
    mode = _opt_int(params, "playback_mode", 0, 2)  # 0 Classic, 1 One-Shot, 2 Slicing

    steps: Dict[str, Any] = {}
    _step(steps, "replace_sample", lambda: dev.replace_sample(path))
    if mode is not None and steps["replace_sample"]["ok"]:
        _step(steps, "playback_mode", lambda: setattr(dev, "playback_mode", mode))
    return {
        "ok": all(s["ok"] for s in steps.values()),
        "device": dev_index,
        "file_path": lom_read.safe(lambda: dev.sample.file_path),
        "playback_mode": lom_read.get(dev, "playback_mode"),
        "steps": steps,
    }


# --- locators ------------------------------------------------------------


def _cues(song: Any) -> List[Dict[str, Any]]:
    cues = [{"name": str(c.name), "time": float(c.time)} for c in song.cue_points]
    return sorted(cues, key=lambda c: c["time"])


def _cue_at(song: Any, time: float) -> Any:
    return next((c for c in song.cue_points if abs(float(c.time) - time) < EPS), None)


MAX_LOCATOR_ITEMS = 256
LOCATOR_TIME_TOL = 0.01
LOCATOR_TIMEOUT_S = 2.0


def _cue_near(song: Any, time_: float) -> Any:
    return next((c for c in song.cue_points if abs(float(c.time) - time_) <= LOCATOR_TIME_TOL), None)


class LocatorQueue:
    """
    Locators asincronos: Live aplica `current_song_time` en un tick posterior, asi que
    mover el playhead y llamar set_or_delete_cue en la misma llamada opera sobre la
    posicion VIEJA. Maquina de estados avanzada desde surface._tick:
      moving (espera playhead ~ target) -> act (set/delete cue) -> verify (renombra / confirma)
    y al vaciar la cola se restaura el playhead original.
    """

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._queue: List[Dict[str, Any]] = []
        self._cur: Optional[Dict[str, Any]] = None
        self._phase = "idle"
        self._deadline = 0.0
        self._previous: Optional[float] = None
        self._restore = False
        self._next_id = 0
        self._last_id: Optional[int] = None
        self._done: List[Dict[str, Any]] = []
        self._errors: List[Dict[str, Any]] = []

    # -- API de comandos --

    def set_many(self, song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        items = params.get("items")
        if not isinstance(items, list) or not 1 <= len(items) <= MAX_LOCATOR_ITEMS:
            raise _bad(f"items must be a list of 1..{MAX_LOCATOR_ITEMS} objects")
        ops = []
        for i, it in enumerate(items):
            if not isinstance(it, dict):
                raise _bad(f"items[{i}] must be an object")
            t = it.get("time")
            if not _is_num(t) or t < 0:
                raise _bad(f"items[{i}].time must be a number >= 0")
            n = it.get("name")
            if not isinstance(n, str) or not n.strip():
                raise _bad(f"items[{i}].name must be a non-empty string")
            ops.append({"op": "set", "time": float(t), "name": n})
        return self._enqueue(ops)

    def set(self, song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        out = self.set_many(song, {"items": [{"time": params.get("time"), "name": params.get("name")}]})
        return {"queued": out["queued"], "id": out["id"]}

    def clear_all(self, song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        ops = [{"op": "delete", "time": c["time"], "name": c["name"]} for c in _cues(song)]
        if not ops:
            return {"queued": False, "id": None, "count": 0}
        return self._enqueue(ops)

    def _enqueue(self, ops: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not self._busy():
            self._done, self._errors = [], []  # lote nuevo con la cola ociosa: status empieza limpio
        self._next_id += 1
        self._last_id = self._next_id
        self._queue.extend(ops)
        self._restore = False  # el playhead se restaura al terminar el lote nuevo
        return {"queued": True, "id": self._next_id, "count": len(ops)}

    def _busy(self) -> bool:
        return bool(self._queue) or self._cur is not None

    def status(self, song: Any) -> Dict[str, Any]:
        return {
            "pending": len(self._queue) + (1 if self._cur is not None else 0),
            "done": list(self._done),
            "errors": list(self._errors),
            "id": self._last_id,
            "cue_points": _cues(song),
        }

    # -- maquina de estados --

    def tick(self, song: Any) -> None:
        if self._cur is None:
            if self._queue:
                self._start_next(song)
            elif self._restore:
                self._restore = False
                self._restore_playhead(song)
            return
        cur = self._cur
        try:
            if self._clock() > self._deadline:
                raise TimeoutError(f"timeout in phase {self._phase}")
            if self._phase == "moving":
                if abs(float(song.current_song_time) - cur["time"]) <= LOCATOR_TIME_TOL:
                    self._act(song, cur)
            elif self._phase == "verify":
                self._verify(song, cur)
        except TimeoutError as exc:
            self._fail(cur, str(exc))
        except Exception as exc:  # noqa: BLE001 - un item roto no traba la cola
            self._fail(cur, f"{type(exc).__name__}: {exc}")

    def _start_next(self, song: Any) -> None:
        if self._previous is None:
            self._previous = float(song.current_song_time)
        cur = self._queue.pop(0)
        self._cur, self._phase = cur, "moving"
        self._deadline = self._clock() + LOCATOR_TIMEOUT_S
        try:
            song.current_song_time = cur["time"]
        except Exception as exc:  # noqa: BLE001
            self._fail(cur, f"{type(exc).__name__}: {exc}")

    def _act(self, song: Any, cur: Dict[str, Any]) -> None:
        # set_or_delete_cue alterna: crear solo si no hay cue, borrar solo si hay
        exists = _cue_near(song, cur["time"]) is not None
        if (cur["op"] == "set") != exists:
            song.set_or_delete_cue()
        self._phase = "verify"
        self._deadline = self._clock() + LOCATOR_TIMEOUT_S

    def _verify(self, song: Any, cur: Dict[str, Any]) -> None:
        cue = _cue_near(song, cur["time"])
        if cur["op"] == "set":
            if cue is None:
                return  # puede aparecer en el proximo tick; el timeout corta
            cue.name = cur["name"]
        elif cue is not None:
            return
        self._done.append({"name": cur["name"], "time": cur["time"]})
        self._finish()

    def _fail(self, cur: Dict[str, Any], error: str) -> None:
        self._errors.append({"name": cur["name"], "time": cur["time"], "error": error})
        self._finish()

    def _finish(self) -> None:
        self._cur, self._phase = None, "idle"
        if not self._queue:
            self._restore = True

    def _restore_playhead(self, song: Any) -> None:
        previous, self._previous = self._previous, None
        if previous is not None:
            try:
                song.current_song_time = previous
            except Exception:  # noqa: BLE001 - restaurar la posicion es best-effort
                pass
