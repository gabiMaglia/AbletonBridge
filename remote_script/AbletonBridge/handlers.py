"""
Handlers de comandos que tocan el LOM. SIEMPRE se ejecutan en el hilo
principal de Live (via UIDispatcher.pump), nunca en el thread del socket.

Reciben `song` / el modulo `Live` por parametro para poder testearse con
objetos falsos fuera de Live. Stdlib pura.
"""
from typing import Any, Dict, List, Tuple

# (modulo Live, clase, miembro). Clave de respuesta: "Clase.miembro".
PROBE_TARGETS: List[Tuple[str, str, List[str]]] = [
    ("Song", "Song", ["create_audio_track", "create_midi_track", "create_return_track", "set_or_delete_cue"]),
    (
        "Track",
        "Track",
        [
            "create_audio_clip", "create_midi_clip", "insert_device",
            "duplicate_clip_to_arrangement", "delete_clip", "arrangement_clips",
        ],
    ),
    ("ClipSlot", "ClipSlot", ["create_audio_clip"]),
    (
        "Clip",
        "Clip",
        [
            "automation_envelope", "create_automation_envelope", "add_warp_marker",
            "move_warp_marker", "remove_warp_marker", "crop", "add_new_notes",
            "get_notes_extended",
        ],
    ),
    ("SimplerDevice", "SimplerDevice", ["replace_sample"]),
    ("RackDevice", "RackDevice", ["insert_chain"]),
    ("Application", "Application", ["browser"]),
    ("Browser", "Browser", ["load_item"]),
]


def read_live_info(live: Any) -> Dict[str, Any]:
    """Version de Live y api_level (= major). Llamar desde el hilo principal."""
    app = live.Application.get_application()
    major = app.get_major_version()
    minor = app.get_minor_version()
    bugfix = app.get_bugfix_version()
    return {"live_version": f"{major}.{minor}.{bugfix}", "api_level": major}


def get_state(song: Any, live_info: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
    """F-005: snapshot del set (contrato 04_api_contracts.md SS B)."""
    include_clips = params.get("include_clips", True)
    tracks = []
    for index, track in enumerate(song.tracks):
        entry: Dict[str, Any] = {
            "index": index,
            "name": track.name,
            "is_midi": bool(track.has_midi_input),
        }
        if include_clips:
            clips = []
            for slot_index, slot in enumerate(track.clip_slots):
                if slot.has_clip:
                    clip = slot.clip
                    clips.append(
                        {
                            "slot_index": slot_index,
                            "name": clip.name,
                            "length_beats": float(clip.length),
                            "is_midi": bool(clip.is_midi_clip),
                        }
                    )
            entry["clips"] = clips
        tracks.append(entry)
    return {
        "tempo": float(song.tempo),
        "is_playing": bool(song.is_playing),
        "live_version": live_info.get("live_version", "unknown"),
        "tracks": tracks,
    }


def probe_api(live: Any, live_info: Dict[str, Any]) -> Dict[str, Any]:
    """Reporta que miembros del LOM existen en esta version de Live."""
    members: Dict[str, Any] = {}
    for module_name, class_name, names in PROBE_TARGETS:
        cls = None
        try:
            cls = getattr(getattr(live, module_name), class_name)
        except Exception:  # noqa: BLE001 - clase ausente => se reporta, no se rompe
            cls = None
        for name in names:
            key = f"{class_name}.{name}"
            if cls is None:
                members[key] = "class_missing"
                continue
            try:
                members[key] = bool(hasattr(cls, name))
            except Exception:  # noqa: BLE001
                members[key] = False
    return {"live_version": live_info.get("live_version", "unknown"), "members": members}
