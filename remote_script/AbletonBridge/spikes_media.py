"""
Spikes TEMPORALES ronda 2 (T-002d): audio clips, devices y Simpler.

Mismas reglas que spikes.py: codigo fijo, params tipados simples, solo pistas
"SPIKE-*", cada paso envuelto y reportado como {"ok", "error"}, nunca levanta
hacia Live. Se borra con el resto de los spikes (spike.cleanup ya limpia
cualquier pista con prefijo SPIKE-).
"""
import os
from typing import Any, Dict, List, Optional, Tuple

from . import lom_read
from .spikes import PREFIX, _float, _new_midi_track, _safe, _step

AUDIO_TRACK = PREFIX + "AUDIO"
DEVICES_TRACK = PREFIX + "DEVICES"
SLICE_TRACK = PREFIX + "SIMPLER-SLICE"
ONESHOT_TRACK = PREFIX + "SIMPLER-ONESHOT"

AUDIO_EXTENSIONS = (".wav", ".aif", ".aiff", ".mp3", ".flac")
INVALID_PATH = {"ok": False, "error": "invalid path"}

# VERIFICAR EN LIVE: valores de Clip.warp_mode (0 Beats,1 Tones,2 Texture,3 Re-Pitch,4 Complex,6 Complex Pro)
WARP_COMPLEX_PRO = 6
# VERIFICAR EN LIVE: SimplerDevice.playback_mode (0 Classic, 1 One-Shot, 2 Slicing)
MODE_ONESHOT = 1
MODE_SLICING = 2

DEVICE_CHAIN = ("EQ Eight", "Saturator", "Compressor", "Drum Buss", "Utility")


def valid_audio_path(path: Any) -> bool:
    return (
        isinstance(path, str)
        and os.path.isabs(path)
        and path.lower().endswith(AUDIO_EXTENSIONS)
        and os.path.isfile(path)
    )


def _new_audio_track(song: Any, name: str) -> Tuple[int, Any]:
    song.create_audio_track(-1)
    index = len(song.tracks) - 1
    track = song.tracks[index]
    track.name = name
    return index, track


_get = lom_read.get


def _warp_markers(clip: Any) -> Any:
    # VERIFICAR EN LIVE: forma de warp_markers (objetos con beat_time/sample_time o dicts)
    def read() -> List[Dict[str, Any]]:
        out = []
        for m in clip.warp_markers:
            if isinstance(m, dict):
                out.append({"beat_time": m.get("beat_time"), "sample_time": m.get("sample_time")})
            else:
                out.append({"beat_time": m.beat_time, "sample_time": m.sample_time})
        return out

    return _safe(read)


CLIP_FIELDS = (
    "is_audio_clip", "file_path", "length", "start_time", "end_time", "warping",
    "warp_mode", "start_marker", "end_marker", "loop_start", "loop_end", "looping",
    "gain", "pitch_coarse",
)


def _clip_info(clip: Any) -> Dict[str, Any]:
    info = {f: _get(clip, f) for f in CLIP_FIELDS}
    info["warp_markers"] = _warp_markers(clip)
    return info


def _set_range(clip: Any, start_attr: str, end_attr: str, start: float, end: float) -> None:
    """Pone start/end sin cruzarlos: si el nuevo inicio pasa del fin actual, primero el fin."""
    if start >= getattr(clip, end_attr):
        setattr(clip, end_attr, end)
        setattr(clip, start_attr, start)
    else:
        setattr(clip, start_attr, start)
        setattr(clip, end_attr, end)


def _find_arrangement_clip(track: Any, position: float) -> Any:
    for clip in track.arrangement_clips:
        if abs(float(clip.start_time) - position) < 1e-6:
            return clip
    return None


def _create_audio_clip(track: Any, path: str, position: float) -> Any:
    # VERIFICAR EN LIVE: create_audio_clip devuelve el Clip; si devuelve None se busca por start_time
    clip = track.create_audio_clip(path, position)
    return clip if clip is not None else _find_arrangement_clip(track, position)


def audio_clip(song: Any, live: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    """Spike: clips de audio en Arrangement (lectura, chop de 1 beat, Complex Pro + pitch)."""
    path = params.get("path")
    if not valid_audio_path(path):
        return dict(INVALID_PATH)
    position = _float(params, "position_beats", 0.0)
    steps: Dict[str, Any] = {}
    out: Dict[str, Any] = {
        "ok": False, "track_index": None, "clips": {}, "steps": steps,
        "complex_pro_mode_value": WARP_COMPLEX_PRO,
    }
    ctx: Dict[str, Any] = {}

    def create_track() -> None:
        out["track_index"], ctx["track"] = _new_audio_track(song, AUDIO_TRACK)

    if not _step(steps, "create_track", create_track)[0]:
        return out
    track = ctx["track"]
    clips: Dict[str, Any] = {}

    for key, pos in (("base", position), ("chop", position + 16.0), ("complex", position + 20.0)):
        def make(key: str = key, pos: float = pos) -> None:
            clip = _create_audio_clip(track, path, pos)
            if clip is None:
                raise RuntimeError("clip not found after create_audio_clip")
            clips[key] = clip

        _step(steps, f"create_{key}", make)

    def chop() -> None:
        clip = clips["chop"]
        _step(steps, "chop_loop", lambda: _set_range(clip, "loop_start", "loop_end", 1.0, 2.0))
        _step(steps, "chop_markers", lambda: _set_range(clip, "start_marker", "end_marker", 1.0, 2.0))
        _step(steps, "chop_looping", lambda: setattr(clip, "looping", True))

    if "chop" in clips:
        chop()

    if "complex" in clips:
        cp = clips["complex"]
        _step(steps, "complex_warping", lambda: setattr(cp, "warping", True))
        _step(steps, "complex_warp_mode", lambda: setattr(cp, "warp_mode", WARP_COMPLEX_PRO))
        _step(steps, "complex_pitch", lambda: setattr(cp, "pitch_coarse", -2))

    for key, clip in clips.items():
        out["clips"][key] = _clip_info(clip)
    out["ok"] = "base" in clips
    return out


def _param_info(param: Any) -> Dict[str, Any]:
    info: Dict[str, Any] = {"name": _get(param, "name")}
    original = _safe(lambda: param.original_name)
    if not str(original).startswith("unavailable"):
        info["original_name"] = original
    info["min"], info["max"] = _get(param, "min"), _get(param, "max")
    quantized = bool(_safe(lambda: param.is_quantized) is True)
    info["is_quantized"] = quantized
    if quantized:
        info["value_items"] = _safe(lambda: list(param.value_items))
    else:
        info["default_value"] = _get(param, "default_value")
    value = _safe(lambda: param.value)
    info["value"] = value
    info["str_for_value"] = _safe(lambda: param.str_for_value(param.value))
    return info


def _device_info(device: Any) -> Dict[str, Any]:
    return {
        "class_name": _get(device, "class_name"),
        "name": _get(device, "name"),
        "parameters": _safe(lambda: [_param_info(p) for p in device.parameters]),
    }


def _find_param(device: Any, name: str) -> Any:
    return next((p for p in device.parameters if p.name == name), None)


def devices(song: Any, live: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    """Spike: insertar devices nativos, volcar parametros y probar set por nombre."""
    steps: Dict[str, Any] = {}
    out: Dict[str, Any] = {
        "ok": False, "track_index": None, "devices": [], "set_params": {},
        "drum_rack": {"ok": False, "error": None}, "steps": steps,
    }
    ctx: Dict[str, Any] = {}

    def create_track() -> None:
        out["track_index"], ctx["track"] = _new_audio_track(song, DEVICES_TRACK)

    if not _step(steps, "create_track", create_track)[0]:
        return out
    track = ctx["track"]
    out["ok"] = True

    inserted: Dict[str, Any] = {}
    for name in DEVICE_CHAIN:
        def insert(name: str = name) -> None:
            dev = track.insert_device(name, len(track.devices))
            if dev is None:  # VERIFICAR EN LIVE: insert_device puede no devolver el device
                dev = track.devices[-1]
            inserted[name] = dev

        _step(steps, f"insert_{name}", insert)

    for name in DEVICE_CHAIN:
        if name in inserted:
            out["devices"].append(_device_info(inserted[name]))

    for dev_name, param_name, frac_of in (("Saturator", "Drive", "max_half"), ("Utility", "Gain", "quarter")):
        dev = inserted.get(dev_name)
        if dev is None:
            continue
        key = f"{dev_name}.{param_name}"

        def set_param(dev: Any = dev, param_name: str = param_name,
                      frac_of: str = frac_of, key: str = key) -> None:
            param = _find_param(dev, param_name)
            if param is None:
                raise LookupError(f"parameter {param_name!r} not found")
            target = param.max * 0.5 if frac_of == "max_half" else param.min + (param.max - param.min) * 0.25
            param.value = target
            out["set_params"][key] = {
                "target": target, "value": param.value,
                "str_for_value": param.str_for_value(param.value),
            }

        _step(steps, f"set_{key}", set_param)

    def drum_rack() -> None:
        dev = track.insert_device("Drum Rack", len(track.devices))
        if dev is None:
            dev = track.devices[-1]
        out["drum_rack"]["class_name"] = _get(dev, "class_name")

    ok, _ = _step(steps, "insert_Drum Rack", drum_rack)
    out["drum_rack"]["ok"] = ok
    out["drum_rack"]["error"] = steps["insert_Drum Rack"]["error"]
    return out


def _add_notes(live: Any, clip: Any, pitches: List[int]) -> None:
    # VERIFICAR EN LIVE: MidiNoteSpecification(pitch,start_time,duration,velocity) ya funciono en Live 12.4.16
    spec = live.Clip.MidiNoteSpecification
    clip.add_new_notes(tuple(
        spec(pitch=p, start_time=float(i), duration=0.5, velocity=100)
        for i, p in enumerate(pitches)
    ))


def _sample_info(sample: Any) -> Dict[str, Any]:
    info = {
        f: _get(sample, f)
        for f in ("file_path", "length", "sample_rate", "slicing_style",
                  "slicing_sensitivity", "slicing_beat_division")
    }
    slices = _safe(lambda: list(sample.slices))
    if isinstance(slices, list):
        info["slices_count"], info["first_slices"] = len(slices), slices[:16]
    else:
        info["slices_count"], info["first_slices"] = slices, slices
    return info


def _simpler_track(song: Any, name: str, path: str, mode: int, steps: Dict[str, Any],
                   prefix: str, ctx: Dict[str, Any]) -> bool:
    """Crea pista MIDI + Simpler + sample + playback_mode. Devuelve si hay device y sample."""
    def create() -> None:
        ctx["index"], ctx["track"] = _new_midi_track(song, name)

    if not _step(steps, f"{prefix}_create_track", create)[0]:
        return False
    track = ctx["track"]

    def insert() -> None:
        dev = track.insert_device("Simpler", len(track.devices))
        if dev is None:
            dev = track.devices[-1]
        ctx["device"] = dev

    if not _step(steps, f"{prefix}_insert_simpler", insert)[0]:
        return False
    dev = ctx["device"]
    if not _step(steps, f"{prefix}_replace_sample", lambda: dev.replace_sample(path))[0]:
        return False
    _step(steps, f"{prefix}_playback_mode", lambda: setattr(dev, "playback_mode", mode))
    return True


def _midi_clip(live: Any, track: Any, steps: Dict[str, Any], prefix: str, pitches: List[int]) -> None:
    ctx: Dict[str, Any] = {}

    def create() -> None:
        slot = track.clip_slots[0]
        slot.create_clip(4.0)
        ctx["clip"] = slot.clip

    if _step(steps, f"{prefix}_create_clip", create)[0]:
        _step(steps, f"{prefix}_add_notes", lambda: _add_notes(live, ctx["clip"], pitches))


def simpler_slice(song: Any, live: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    """Spike: Simpler en Slicing con loop y Simpler one-shot, cada uno con clip MIDI de 1 compas."""
    loop_path, oneshot_path = params.get("loop_path"), params.get("oneshot_path")
    if not (valid_audio_path(loop_path) and valid_audio_path(oneshot_path)):
        return dict(INVALID_PATH)
    steps: Dict[str, Any] = {}
    out: Dict[str, Any] = {"ok": True, "slice": {}, "oneshot": {}, "steps": steps}

    ctx: Dict[str, Any] = {}
    if _simpler_track(song, SLICE_TRACK, loop_path, MODE_SLICING, steps, "slice", ctx):
        dev, track = ctx["device"], ctx["track"]
        out["slice"]["track_index"] = ctx["index"]
        out["slice"]["playback_mode_readback"] = _get(dev, "playback_mode")
        sample = dev.sample
        out["slice"]["sample"] = _sample_info(sample)

        def reslice() -> None:
            length = int(sample.length)
            sample.clear_slices()
            # VERIFICAR EN LIVE: insert_slice recibe frames y puede rechazar una posicion 0
            for i in range(4):
                sample.insert_slice(length * i // 4)

        _step(steps, "slice_clear_slices", reslice)
        out["slice"]["slices_after"] = _safe(lambda: list(sample.slices))
        # Notas 36..39: Simpler en Slicing mapea slices desde C1 (36). VERIFICAR EN LIVE.
        _midi_clip(live, track, steps, "slice", [36, 37, 38, 39])

    ctx2: Dict[str, Any] = {}
    if _simpler_track(song, ONESHOT_TRACK, oneshot_path, MODE_ONESHOT, steps, "oneshot", ctx2):
        dev, track = ctx2["device"], ctx2["track"]
        out["oneshot"]["track_index"] = ctx2["index"]
        out["oneshot"]["playback_mode_readback"] = _get(dev, "playback_mode")
        out["oneshot"]["sample"] = _sample_info(dev.sample)
        out["oneshot"]["parameters"] = _safe(lambda: [_param_info(p) for p in dev.parameters])
        # Pitch 60 (C3) como nota raiz: VERIFICAR EN LIVE.
        _midi_clip(live, track, steps, "oneshot", [60, 60, 60, 60])
    return out
