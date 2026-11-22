import sys
import types
from pathlib import Path
from typing import Dict, Iterable

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# Miembros del LOM que probe_api inspecciona, por clase.
FAKE_LOM_CLASSES = {
    "Song": ["create_audio_track", "create_midi_track", "create_return_track", "set_or_delete_cue"],
    "Track": [
        "create_audio_clip", "create_midi_clip", "insert_device",
        "duplicate_clip_to_arrangement", "delete_clip", "arrangement_clips",
    ],
    "ClipSlot": ["create_audio_clip"],
    "Clip": [
        "automation_envelope", "create_automation_envelope", "add_warp_marker",
        "move_warp_marker", "remove_warp_marker", "crop", "add_new_notes",
        "get_notes_extended",
    ],
    "SimplerDevice": ["replace_sample"],
    "RackDevice": ["insert_chain"],
    "Application": ["browser"],
    "Browser": ["load_item"],
}


def build_fake_live(
    version: tuple = (12, 4, 16),
    missing_members: Iterable[str] = (),
    missing_classes: Iterable[str] = (),
) -> types.ModuleType:
    """Arma un modulo `Live` falso. `missing_members` usa 'Clase.miembro'."""
    missing = set(missing_members)
    gone = set(missing_classes)
    live = types.ModuleType("Live")
    for cls_name, members in FAKE_LOM_CLASSES.items():
        sub = types.ModuleType(f"Live.{cls_name}")
        if cls_name not in gone:
            attrs: Dict[str, object] = {
                m: (lambda self: None) for m in members if f"{cls_name}.{m}" not in missing
            }
            setattr(sub, cls_name, type(cls_name, (), attrs))
        setattr(live, cls_name, sub)

    major, minor, bugfix = version
    app = types.SimpleNamespace(
        get_major_version=lambda: major,
        get_minor_version=lambda: minor,
        get_bugfix_version=lambda: bugfix,
    )
    live.Application.get_application = lambda: app
    return live


@pytest.fixture
def fake_live(monkeypatch):
    """Instala un `Live` falso en sys.modules (default: Live 12.4.16 completo)."""
    live = build_fake_live()
    monkeypatch.setitem(sys.modules, "Live", live)
    return live


@pytest.fixture
def install_fake_live(monkeypatch):
    def _install(**kwargs):
        live = build_fake_live(**kwargs)
        monkeypatch.setitem(sys.modules, "Live", live)
        return live

    return _install
