"""
state.detail: lectura completa del set, ESTRICTAMENTE de solo lectura.

Corre en el hilo principal (via dispatcher). Nunca se asigna un atributo del
LOM aca. Cada campo pasa por `lom_read.safe`: lo ilegible se reporta como
"unavailable: <ExcType>" y no aborta el resto.
"""
from typing import Any, Dict, List, Optional

from .lom_read import get, is_unavailable, safe

PARAM_MODES = ("changed", "all", "none")
MAX_CHAIN_DEPTH = 3
DEVICE_ON = "Device On"

# VERIFICAR EN LIVE: nombres exactos de los campos de audio/MIDI clip en Live 12.
AUDIO_CLIP_FIELDS = (
    "file_path", "warping", "warp_mode", "pitch_coarse", "pitch_fine", "gain",
    "looping", "loop_start", "loop_end", "start_marker", "end_marker",
)
MIDI_CLIP_FIELDS = ("looping", "loop_start", "loop_end", "start_marker", "end_marker")


def get_state_detail(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    mode = params.get("params", "changed")
    if mode not in PARAM_MODES:
        raise ValueError(f"params must be one of {PARAM_MODES}, got {mode!r}")
    wanted = _track_filter(params.get("tracks"))
    opts = {
        "mode": mode,
        "session": _flag(params, "include_session"),
        "arrangement": _flag(params, "include_arrangement"),
    }

    all_tracks = list(song.tracks)
    indices = range(len(all_tracks)) if wanted is None else sorted(i for i in set(wanted) if 0 <= i < len(all_tracks))
    out: Dict[str, Any] = {
        "song": _song_block(song),
        "tracks": [_track(all_tracks[i], i, opts, "track") for i in indices],
        "returns": safe(lambda: [_track(t, i, opts, "return") for i, t in enumerate(song.return_tracks)]),
        "master": safe(lambda: _track(song.master_track, None, opts, "master")),
    }
    return out


def _flag(params: Dict[str, Any], key: str) -> bool:
    value = params.get(key, True)
    return value if isinstance(value, bool) else True


def _track_filter(value: Any) -> Optional[List[int]]:
    if value is None:
        return None
    if not isinstance(value, list) or not all(isinstance(i, int) and not isinstance(i, bool) for i in value):
        raise ValueError("tracks must be a list of integers")
    return value


def _song_block(song: Any) -> Dict[str, Any]:
    return {
        "tempo": get(song, "tempo"),
        "signature_numerator": get(song, "signature_numerator"),
        "signature_denominator": get(song, "signature_denominator"),
        "song_length": get(song, "song_length"),
        "current_song_time": get(song, "current_song_time"),
        "is_playing": get(song, "is_playing"),
        "loop": {"on": get(song, "loop"), "start": get(song, "loop_start"), "length": get(song, "loop_length")},
        "cue_points": safe(lambda: [{"name": get(c, "name"), "time": get(c, "time")} for c in song.cue_points]),
        # VERIFICAR EN LIVE: root_note/scale_name existen desde Live 11 (Scale Mode)
        "root_note": get(song, "root_note"),
        "scale_name": get(song, "scale_name"),
    }


def _kind(track: Any) -> str:
    if get(track, "is_foldable") is True:
        return "group"
    return "midi" if get(track, "has_midi_input") is True else "audio"


def _track(track: Any, index: Optional[int], opts: Dict[str, Any], role: str) -> Dict[str, Any]:
    entry: Dict[str, Any] = {}
    if index is not None:
        entry["index"] = index
    entry["name"] = get(track, "name")
    if role == "track":
        entry["kind"] = _kind(track)
        entry["is_foldable"] = get(track, "is_foldable")
        entry["is_grouped"] = get(track, "is_grouped")
        if entry["is_grouped"] is True:
            entry["group_name"] = safe(lambda: track.group_track.name)
        entry["color_index"] = get(track, "color_index")
        entry["mute"] = get(track, "mute")
        entry["solo"] = get(track, "solo")
        entry["arm"] = get(track, "arm")  # los grupos no pueden armarse: queda "unavailable"
        entry["output_routing"] = safe(lambda: track.output_routing_type.display_name)
    elif role == "return":
        entry["kind"] = "return"
        entry["mute"] = get(track, "mute")
        entry["solo"] = get(track, "solo")
    entry["mixer"] = safe(lambda: _mixer(track.mixer_device, with_sends=role != "master"))
    entry["devices"] = safe(lambda: _devices(track.devices, opts["mode"], 0))
    if role == "track":
        if opts["session"]:
            entry["session_clips"] = safe(lambda: _session_clips(track))
        if opts["arrangement"]:
            entry["arrangement_clips"] = safe(lambda: _arrangement_clips(track))
    return entry


def _value_display(param: Any) -> Dict[str, Any]:
    value = get(param, "value")
    return {"value": value, "display": safe(lambda: param.str_for_value(param.value))}


def _mixer(mixer: Any, with_sends: bool) -> Dict[str, Any]:
    out = {
        "volume": safe(lambda: _value_display(mixer.volume)),
        "panning": safe(lambda: _value_display(mixer.panning)),
    }
    if with_sends:
        out["sends"] = safe(lambda: [_value_display(s) for s in mixer.sends])
    return out


def _param_entry(param: Any) -> Dict[str, Any]:
    entry = {"name": get(param, "name")}
    entry.update(_value_display(param))
    entry["min"] = get(param, "min")
    entry["max"] = get(param, "max")
    entry["is_quantized"] = get(param, "is_quantized")
    return entry


def _is_changed(param: Any) -> bool:
    value, default = get(param, "value"), get(param, "default_value")
    if get(param, "name") == DEVICE_ON:
        # Solo interesa si el device esta apagado.
        return not is_unavailable(value) and not value
    if is_unavailable(value) or is_unavailable(default):
        return True  # ante la duda se reporta
    return value != default


def _parameters(device: Any, mode: str) -> List[Dict[str, Any]]:
    params = device.parameters
    if mode == "changed":
        params = [p for p in params if _is_changed(p)]
    return [safe(lambda p=p: _param_entry(p)) for p in params]


def _devices(devices: Any, mode: str, chain_depth: int) -> List[Dict[str, Any]]:
    return [safe(lambda d=d: _device(d, mode, chain_depth)) for d in devices]


def _device(device: Any, mode: str, chain_depth: int) -> Dict[str, Any]:
    entry: Dict[str, Any] = {
        "class_name": get(device, "class_name"),
        "name": get(device, "name"),
    }
    dtype = get(device, "type")
    if not is_unavailable(dtype):
        entry["type"] = dtype
    entry["is_active"] = get(device, "is_active")
    if mode != "none":
        entry["parameters"] = safe(lambda: _parameters(device, mode))
    if get(device, "can_have_chains") is True:
        if chain_depth >= MAX_CHAIN_DEPTH:
            entry["chains_truncated"] = True
        else:
            entry["chains"] = safe(lambda: [_chain(c, mode, chain_depth + 1) for c in device.chains])
    return entry


def _chain(chain: Any, mode: str, chain_depth: int) -> Dict[str, Any]:
    entry: Dict[str, Any] = {
        "name": get(chain, "name"),
        "mute": get(chain, "mute"),
        "solo": get(chain, "solo"),
    }
    in_note = get(chain, "in_note")  # solo DrumChain
    if not is_unavailable(in_note):
        entry["in_note"] = in_note
    entry["devices"] = safe(lambda: _devices(chain.devices, mode, chain_depth))
    return entry


def _clip_entry(clip: Any) -> Dict[str, Any]:
    entry: Dict[str, Any] = {"name": get(clip, "name"), "length": get(clip, "length")}
    is_audio = get(clip, "is_audio_clip") is True
    entry["is_audio"] = is_audio
    if is_audio:
        for field in AUDIO_CLIP_FIELDS:
            entry[field] = get(clip, field)
        entry["gain_display"] = get(clip, "gain_display_string")
    else:
        entry["note_count"] = safe(lambda: len(clip.get_all_notes_extended()))
        for field in MIDI_CLIP_FIELDS:
            entry[field] = get(clip, field)
    return entry


def _session_clips(track: Any) -> List[Dict[str, Any]]:
    out = []
    for slot_index, slot in enumerate(track.clip_slots):
        if get(slot, "has_clip") is True:
            entry: Dict[str, Any] = {"slot": slot_index}
            clip = get(slot, "clip")
            if is_unavailable(clip):
                entry["clip"] = clip
            else:
                entry.update(_clip_entry(clip))
            out.append(entry)
    return out


def _arrangement_clips(track: Any) -> List[Dict[str, Any]]:
    out = []
    for clip in track.arrangement_clips:
        entry = {"start_time": get(clip, "start_time"), "end_time": get(clip, "end_time")}
        entry.update(_clip_entry(clip))
        out.append(entry)
    return out
