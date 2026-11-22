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
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import errors, lom_read
from .errors import CommandError

AUDIO_EXTENSIONS = (".wav", ".aif", ".aiff", ".mp3", ".flac")
# VERIFICAR EN LIVE: Clip.warp_mode (0 Beats,1 Tones,2 Texture,3 Re-Pitch,4 Complex,6 Complex Pro)
WARP_MODES = (0, 1, 2, 3, 4, 6)
EPS = 1e-6
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


def find_raw_for_db(lo: float, hi: float, display_of: Callable[[float], Any],
                    target: float, tol: float = DB_TOLERANCE) -> Tuple[float, bool]:
    """
    Biseccion sobre [lo, hi] (display monotono creciente) buscando el valor crudo
    cuyo display se acerca a `target` dB. Devuelve (crudo, dentro_de_tolerancia).
    """
    def db(raw: float) -> float:
        d = parse_db(display_of(raw))
        if d is None:
            raise ValueError("display is not parseable as dB")
        return _NEG_INF if d == -math.inf else d

    best, best_err = lo, abs(db(lo) - target)
    err_hi = abs(db(hi) - target)
    if err_hi < best_err:
        best, best_err = hi, err_hi
    a, b = lo, hi
    for _ in range(48):
        if best_err <= tol + 1e-9:
            break
        mid = (a + b) / 2.0
        d = db(mid)
        err = abs(d - target)
        if err < best_err:
            best, best_err = mid, err
        if d < target:
            a = mid
        else:
            b = mid
    return best, best_err <= tol + 1e-9


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


def track_set_mixer(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    idx, track = _track(song, params)
    raw_db = params.get("volume_db")
    target_db: Optional[float] = None
    minus_inf = False
    if isinstance(raw_db, str):
        if raw_db.strip().lower() not in ("-inf", "-infinity"):
            raise _bad("volume_db must be a number or '-inf'")
        minus_inf = True
    elif raw_db is not None:
        if not _is_num(raw_db):
            raise _bad("volume_db must be a number or '-inf'")
        target_db = float(raw_db)
    pan = _num(params, "pan", lo=-1.0, hi=1.0)
    mute = _opt_bool(params, "mute")
    solo = _opt_bool(params, "solo")

    out: Dict[str, Any] = {"track": idx}
    mixer = track.mixer_device
    if minus_inf or target_db is not None:
        vol = mixer.volume
        within = True
        if minus_inf:
            vol.value = vol.min
        else:
            raw, within = find_raw_for_db(float(vol.min), float(vol.max), vol.str_for_value, target_db)
            vol.value = raw
        out["volume"] = dict(_readback(vol), within_tolerance=within)
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


def _trim(clip: Any, target: float, steps: Dict[str, Any], prefix: str) -> bool:
    """Recorta el clip a `target` beats moviendo end_marker/loop_end. True si la longitud quedo."""
    # VERIFICAR EN LIVE: si recortar end_marker alcanza en clips de Arrangement o hace falta loop_end
    _step(steps, f"{prefix}_trim_end_marker",
          lambda: setattr(clip, "end_marker", float(clip.start_marker) + target))
    _step(steps, f"{prefix}_trim_loop_end",
          lambda: setattr(clip, "loop_end", float(clip.loop_start) + target))
    length = lom_read.safe(lambda: float(clip.length))
    return isinstance(length, float) and abs(length - target) <= 1e-3


def _clip_summary(clip: Any) -> Dict[str, Any]:
    return {
        "start_time": lom_read.get(clip, "start_time"),
        "end_time": lom_read.get(clip, "end_time"),
        "length": lom_read.get(clip, "length"),
        "warp_mode": lom_read.get(clip, "warp_mode"),
        "pitch_coarse": lom_read.get(clip, "pitch_coarse"),
    }


def _gain_display(clip: Any, raw: float) -> Any:
    clip.gain = raw
    return clip.gain_display_string


def clip_place_audio(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    idx, track = _track(song, params)
    if track.has_midi_input:
        raise _bad("track must be an audio track")
    path = _audio_path(params)
    start = _req_num(params, "start_beat", lo=0.0)
    total = _req_num(params, "length_beats", positive=True)
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

    steps: Dict[str, Any] = {}
    warnings: List[str] = []
    clips: List[Dict[str, Any]] = []
    gain_info: Optional[Dict[str, Any]] = {"applied": False} if gain_db is not None else None
    gain_raw: Optional[float] = None
    pos, remaining, n = start, total, 0
    trim_failed = False

    while remaining > EPS and n < MAX_COPIES:
        key = f"copy{n}"
        ok, clip = _step(steps, f"{key}_create", lambda: _new_audio_clip(track, path, pos))
        if not ok:
            warnings.append(f"{key}: clip creation failed: {steps[f'{key}_create']['error']}")
            break
        if warp_mode is not None:
            _step(steps, f"{key}_warp_mode", lambda: setattr(clip, "warp_mode", warp_mode))
        if pitch is not None:
            _step(steps, f"{key}_pitch", lambda: setattr(clip, "pitch_coarse", pitch))
        if loop_start is not None:
            _step(steps, f"{key}_loop", lambda: _set_range(clip, "loop_start", "loop_end", loop_start, loop_end))
            _step(steps, f"{key}_markers", lambda: _set_range(clip, "start_marker", "end_marker", loop_start, loop_end))
            _step(steps, f"{key}_looping", lambda: setattr(clip, "looping", True))
        if gain_db is not None:
            gain_raw = _apply_gain(clip, key, gain_db, gain_raw, steps, gain_info, warnings)

        length = lom_read.safe(lambda: float(clip.length))
        if not isinstance(length, float) or length <= EPS:
            warnings.append(f"{key}: clip has no usable length ({length}); stopped tiling")
            clips.append(_clip_summary(clip))
            break
        if length > remaining + EPS:
            if not _trim(clip, remaining, steps, key):
                warnings.append(f"{key}: trim to {remaining} beats not applied; clip overruns the requested length")
                trim_failed = True
            length = remaining
        clips.append(_clip_summary(clip))
        pos += length
        remaining -= length
        n += 1

    if remaining > EPS and n >= MAX_COPIES:
        warnings.append(f"stopped after {MAX_COPIES} copies")
    covered = total - max(remaining, 0.0)
    ok_all = bool(clips) and remaining <= EPS and not trim_failed
    out: Dict[str, Any] = {
        "ok": ok_all, "track": idx, "clips": clips,
        "covered_beats": covered, "warnings": warnings, "steps": steps,
    }
    if gain_info is not None:
        out["gain"] = gain_info
    return out


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

    # VERIFICAR EN LIVE: orden de argumentos de Track.create_midi_clip (start_time, length)
    clip = track.create_midi_clip(start, length)
    if clip is None:
        clip = _find_arrangement_clip(track, start)
    if clip is None:
        raise RuntimeError("clip not found after create_midi_clip")
    if notes:
        spec = live.Clip.MidiNoteSpecification
        clip.add_new_notes(tuple(
            spec(pitch=n["pitch"], start_time=n["start"], duration=n["duration"], velocity=n["velocity"])
            for n in notes
        ))
    count = lom_read.safe(lambda: len(clip.get_all_notes_extended()))
    return {
        "track": idx,
        "start_time": lom_read.get(clip, "start_time"),
        "end_time": lom_read.get(clip, "end_time"),
        "length": lom_read.get(clip, "length"),
        "name": lom_read.get(clip, "name"),
        "note_count": count if isinstance(count, int) else len(notes),
    }


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


def device_insert(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    _, track = _track(song, params)
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


def device_set_param(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    _, track = _track(song, params)
    dev_index, dev = _device(track, params)
    name = _name(params, "name")
    value = params.get("value")
    if not _is_num(value):
        raise _bad("value must be a number (raw, see str_for_value for units)")
    param = next((p for p in dev.parameters if p.name == name), None)
    if param is None:
        raise _bad(f"parameter {name!r} not found (exact, case-sensitive API name)")
    if not float(param.min) - EPS <= value <= float(param.max) + EPS:
        raise _bad(f"value {value} outside [{param.min}, {param.max}]")
    param.value = float(value)
    return {"device": dev_index, "name": name, "min": float(param.min), "max": float(param.max),
            **_readback(param)}


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


def locator_set(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    time = _req_num(params, "time", lo=0.0)
    name = _name(params, "name")
    previous = song.current_song_time
    try:
        song.current_song_time = time
        # set_or_delete_cue alterna: si ya hay cue en ese tiempo lo borraria
        if _cue_at(song, time) is None:
            song.set_or_delete_cue()
        cue = _cue_at(song, time)
        if cue is None:
            raise RuntimeError("cue point was not created at the requested time")
        cue.name = name
    finally:
        try:
            song.current_song_time = previous
        except Exception:  # noqa: BLE001 - restaurar la posicion es best-effort
            pass
    return {"cue_points": _cues(song)}


def locator_clear_all(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    previous = song.current_song_time
    removed = 0
    try:
        for _ in range(1000):
            cues = list(song.cue_points)
            if not cues:
                break
            song.current_song_time = float(cues[0].time)
            song.set_or_delete_cue()
            if len(list(song.cue_points)) >= len(cues):
                break  # sin progreso: no insistir
            removed += 1
    finally:
        try:
            song.current_song_time = previous
        except Exception:  # noqa: BLE001
            pass
    return {"removed": removed, "cue_points": _cues(song)}
