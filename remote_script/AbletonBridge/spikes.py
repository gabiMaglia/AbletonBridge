"""
Spikes TEMPORALES (T-002c): automatizacion en Arrangement.

Codigo fijo y revisable, con params tipados simples; NO hay ejecucion de
codigo enviado por el cliente. Solo se toca lo que se crea aca: pistas con
prefijo "SPIKE-". Corre en el hilo principal de Live (via dispatcher / _tick).
Se borra junto con spike.cleanup cuando el spike termine.
"""
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

PREFIX = "SPIKE-"
SESSION_TRACK = PREFIX + "AUTO-SESSION"
RECORD_TRACK = PREFIX + "AUTO-RECORD"


def _int(params: Dict[str, Any], key: str, default: int, lo: int, hi: int) -> int:
    try:
        value = int(params.get(key, default))
    except (TypeError, ValueError):
        value = default
    return max(lo, min(hi, value))


def _float(params: Dict[str, Any], key: str, default: float) -> float:
    try:
        return max(0.0, float(params.get(key, default)))
    except (TypeError, ValueError):
        return default


def _step(steps: Dict[str, Any], name: str, fn: Callable[[], Any]) -> Tuple[bool, Any]:
    """Corre un paso; registra {ok, error} y nunca propaga."""
    try:
        value = fn()
        steps[name] = {"ok": True, "error": None}
        return True, value
    except Exception as exc:  # noqa: BLE001 - el spike debe reportar, no abortar
        steps[name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        return False, None


def _sample_times(length: float) -> List[float]:
    length = float(length)
    return [0.0, length / 2.0, max(0.0, length - 1.0)]


def _read_env(env: Any, length: float) -> List[Dict[str, float]]:
    return [{"time": t, "value": float(env.value_at_time(t))} for t in _sample_times(length)]


def _ramp(env: Any, beats: int, lo: float, hi: float) -> None:
    for i in range(beats):
        frac = i / (beats - 1) if beats > 1 else 1.0
        env.insert_step(float(i), 1.0, lo + (hi - lo) * frac)


def _device(track: Any, name: str) -> Any:
    for dev in track.devices:
        if dev.name == name:
            return dev
    return None


def _first_non_device_on(device: Any) -> Any:
    for param in device.parameters:
        # Saltea parametros cuantizados (ej. Operator "Algorithm"): la rampa
        # necesita un valor continuo.
        if param.name != "Device On" and not getattr(param, "is_quantized", False):
            return param
    return None


def _bool(params: Dict[str, Any], key: str, default: bool) -> bool:
    value = params.get(key, default)
    return value if isinstance(value, bool) else default


def _new_midi_track(song: Any, name: str) -> Tuple[int, Any]:
    song.create_midi_track(-1)
    index = len(song.tracks) - 1
    track = song.tracks[index]
    track.name = name
    return index, track


def _arrangement_clips(track: Any) -> List[Dict[str, float]]:
    return [
        {"start_time": float(c.start_time), "end_time": float(c.end_time)}
        for c in track.arrangement_clips
    ]


def automation_session(song: Any, live: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    """Spike 1: envolventes en un clip de Session y duplicado a Arrangement."""
    bars = _int(params, "bars", 4, 1, 64)
    beats = bars * 4
    steps: Dict[str, Any] = {}
    out: Dict[str, Any] = {
        "track_index": None,
        "devices_loaded": [],
        "autofilter_param_names": [],
        "envelopes_created": {"volume": False, "filter_freq": False},
        "session_envelope_readback": {},
        "arrangement_clips": [],
        "arrangement_envelope": {},
        "automation_state": {},
        "steps": steps,
    }
    ctx: Dict[str, Any] = {}

    def create_track() -> None:
        out["track_index"], ctx["track"] = _new_midi_track(song, SESSION_TRACK)

    if not _step(steps, "create_track", create_track)[0]:
        return out
    track = ctx["track"]

    def insert_devices() -> None:
        track.insert_device("Operator", 0)
        track.insert_device("Auto Filter", 1)

    _step(steps, "insert_devices", insert_devices)
    out["devices_loaded"] = [d.name for d in getattr(track, "devices", [])]
    autofilter = _device(track, "Auto Filter")
    if autofilter is not None:
        out["autofilter_param_names"] = [p.name for p in autofilter.parameters]

    def create_clip() -> None:
        slot = track.clip_slots[0]
        slot.create_clip(float(beats))
        ctx["clip"] = slot.clip

    if not _step(steps, "create_clip", create_clip)[0]:
        return out
    clip = ctx["clip"]

    def add_notes() -> None:
        # VERIFICAR EN LIVE: forma de MidiNoteSpecification / add_new_notes (Live 11+)
        spec = live.Clip.MidiNoteSpecification
        notes = tuple(
            spec(pitch=36, start_time=float(i), duration=0.5, velocity=100) for i in range(beats)
        )
        clip.add_new_notes(notes)

    _step(steps, "add_notes", add_notes)

    targets: Dict[str, Any] = {"volume": track.mixer_device.volume}
    if autofilter is not None:
        freq = next((p for p in autofilter.parameters if "Freq" in p.name), None)
        if freq is not None:
            targets["filter_freq"] = freq

    for key, param in targets.items():
        def make_env(key: str = key, param: Any = param) -> None:
            env = clip.create_automation_envelope(param)
            if key == "volume":
                lo = param.min + 0.05 * (param.max - param.min)
                hi = param.default_value
            else:
                lo, hi = param.min, param.max
            _ramp(env, beats, lo, hi)
            out["envelopes_created"][key] = True
            out["session_envelope_readback"][key] = _read_env(clip.automation_envelope(param), beats)

        _step(steps, f"envelope_{key}", make_env)

    def dup() -> None:
        ctx["arr_clip"] = track.duplicate_clip_to_arrangement(clip, 0.0)

    _step(steps, "duplicate_to_arrangement", dup)

    def read_arrangement() -> None:
        out["arrangement_clips"] = _arrangement_clips(track)
        arr_clip = ctx.get("arr_clip")
        if arr_clip is None and track.arrangement_clips:
            arr_clip = track.arrangement_clips[0]
        if arr_clip is None:
            return
        for key, param in targets.items():
            env = arr_clip.automation_envelope(param)
            entry: Dict[str, Any] = {"present": env is not None}
            if env is not None:
                entry["samples"] = _read_env(env, beats)
            out["arrangement_envelope"][key] = entry

    _step(steps, "read_arrangement", read_arrangement)

    def read_states() -> None:
        for key, param in targets.items():
            out["automation_state"][key] = int(param.automation_state)

    _step(steps, "read_automation_state", read_states)
    return out


class RecordSpike:
    """Spike 2: maquina de estados avanzada desde surface._tick (sin bloquear ni dormir)."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._reset()

    def _reset(self) -> None:
        self.phase = "idle"
        self.steps_applied = 0
        self.errors: List[str] = []
        self._track: Any = None
        self._song: Any = None
        self._op_param_name: Optional[str] = None
        self._start_beat = 0.0
        self._length = 0.0
        self._deadline = 0.0
        self.trace: List[Dict[str, Any]] = []
        self._prev_arm: Optional[bool] = None

    def restore_arm(self, song: Any) -> None:
        """Devuelve Automation Arm a como estaba antes del spike (una sola vez)."""
        if self._prev_arm is None:
            return
        prev, self._prev_arm = self._prev_arm, None
        try:
            song.session_automation_record = prev
        except Exception as exc:  # noqa: BLE001
            self.errors.append(f"restore_arm: {type(exc).__name__}: {exc}")

    def reset(self) -> None:
        self._reset()

    def _op_param(self) -> Any:
        dev = _device(self._track, "Operator")
        return _first_non_device_on(dev) if dev is not None else None

    def start(self, song: Any, live: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        if self.phase == "running":
            return {"started": False, "error": "already running"}
        self._reset()
        bars = _int(params, "bars", 2, 1, 64)
        start_beat = _float(params, "start_beat", 32.0)
        steps: Dict[str, Any] = {}
        ctx: Dict[str, Any] = {}
        out: Dict[str, Any] = {"started": False, "steps": steps}

        def create_track() -> None:
            out["track_index"], ctx["track"] = _new_midi_track(song, RECORD_TRACK)

        if not _step(steps, "create_track", create_track)[0]:
            return out
        self._track = ctx["track"]  # sin armar: solo queremos automatizacion, no notas
        _step(steps, "insert_operator", lambda: self._track.insert_device("Operator", 0))
        op = self._op_param()
        self._op_param_name = op.name if op is not None else None
        out["operator_param"] = self._op_param_name

        def arm() -> None:
            self._prev_arm = bool(song.session_automation_record)
            song.session_automation_record = True

        if _bool(params, "arm", True):
            _step(steps, "arm", arm)

        def transport() -> None:
            # Si el transporte ya corria, current_song_time arrastra una
            # posicion vieja y el primer tick daba la rampa por terminada.
            if getattr(song, "is_playing", False):
                song.stop_playing()
            song.current_song_time = start_beat
            song.record_mode = True  # VERIFICAR EN LIVE: arma grabacion de automatizacion en Arrangement
            song.start_playing()

        if not _step(steps, "transport", transport)[0]:
            self._finish_transport(song)
            self.phase = "error"
            self.errors.append(steps["transport"]["error"])
            return out

        self._song = song
        self._start_beat = start_beat
        self._length = bars * 4.0
        tempo = float(getattr(song, "tempo", 120.0)) or 120.0
        # Timeout de seguridad por reloj por si el transporte nunca avanza.
        self._deadline = self._clock() + (self._length * 60.0 / tempo) * 2.0 + 10.0
        self.phase = "running"
        out["started"] = True
        out["report"] = {
            "session_automation_record": _safe(lambda: bool(song.session_automation_record)),
            "arrangement_overdub": _safe(lambda: bool(song.arrangement_overdub)),
            "re_enable_automation_enabled": _safe(lambda: bool(song.re_enable_automation_enabled)),
        }
        return out

    def _finish_transport(self, song: Any) -> None:
        for fn in (song.stop_playing, lambda: setattr(song, "record_mode", False)):
            try:
                fn()
            except Exception as exc:  # noqa: BLE001
                self.errors.append(f"{type(exc).__name__}: {exc}")
        self.restore_arm(song)

    def tick(self) -> None:
        if self.phase != "running":
            return
        song = self._song
        try:
            song_time = float(song.current_song_time)
            progress = (song_time - self._start_beat) / self._length
            timed_out = self._clock() > self._deadline
            if timed_out and progress < 1.0:
                raise TimeoutError("transport did not reach the end of the ramp")
            # Solo cuenta con el transporte andando y el cursor ya en la rampa.
            if not getattr(song, "is_playing", False) or progress < 0.0:
                return
            progress = min(1.0, progress)
            if len(self.trace) < 200:
                self.trace.append({"song_time": song_time, "progress": progress})
            vol = self._track.mixer_device.volume
            vol.value = vol.min + (vol.default_value - vol.min) * progress
            op = self._op_param()
            if op is not None:
                op.value = op.min + (op.max - op.min) * progress
            self.steps_applied += 1
            if progress >= 1.0:
                self._finish_transport(song)
                self.phase = "done"
        except Exception as exc:  # noqa: BLE001
            self.errors.append(f"{type(exc).__name__}: {exc}")
            self._finish_transport(song)
            self.phase = "error"

    def status(self, song: Any) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "phase": self.phase,
            "steps_applied": self.steps_applied,
            "errors": list(self.errors),
            "trace": list(self.trace),
        }
        if self._track is not None and self.phase in ("done", "error", "running"):
            states: Dict[str, Any] = {}
            states["volume"] = _safe(lambda: int(self._track.mixer_device.volume.automation_state))
            op = self._op_param()
            if op is not None:
                states["operator_param"] = _safe(lambda: int(op.automation_state))
                out["operator_param"] = op.name
            out["automation_state"] = states
            out["arrangement_clips"] = _safe(lambda: _arrangement_clips(self._track)) or []
        return out


def automation_arm(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    """Prende/apaga Automation Arm (song.session_automation_record) y lee de vuelta."""
    enable = _bool(params, "enable", True)
    out: Dict[str, Any] = {"ok": True, "error": None, "before": None, "after": None}
    try:
        out["before"] = bool(song.session_automation_record)
        song.session_automation_record = enable
        out["after"] = bool(song.session_automation_record)
    except Exception as exc:  # noqa: BLE001
        out["ok"], out["error"] = False, f"{type(exc).__name__}: {exc}"
    return out


def _safe(fn: Callable[[], Any]) -> Any:
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001
        return f"unavailable: {type(exc).__name__}"


def cleanup(song: Any, recorder: RecordSpike) -> Dict[str, Any]:
    """Frena el spike y borra SOLO pistas con prefijo SPIKE- (en reversa)."""
    errors: List[str] = []
    recorder.restore_arm(song)
    recorder.reset()
    for fn in (song.stop_playing, lambda: setattr(song, "record_mode", False)):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{type(exc).__name__}: {exc}")
    deleted: List[str] = []
    for index in range(len(song.tracks) - 1, -1, -1):
        name = song.tracks[index].name
        if name.startswith(PREFIX):
            try:
                song.delete_track(index)
                deleted.append(name)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{name}: {type(exc).__name__}: {exc}")
    return {"deleted": deleted, "errors": errors}
