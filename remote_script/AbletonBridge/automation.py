"""
automation.record (T-012): escribe automatizacion REAL de pista (lane de Arrangement) grabando.

Los envelopes de clip en Arrangement son solo modulacion; un lane real solo se obtiene grabando:
Automation Arm (`session_automation_record`) + `record_mode` + transporte andando + cambiar
`DeviceParameter.value` desde el hilo principal (spike 2). La maquina de estados se avanza desde
runtime.tick, sin bloquear ni dormir:
  queued -> seeking (playhead al preroll) -> preroll (transporte andando) -> recording (punch-in)
  -> done | error | cancelled
Todo se valida y resuelve (incluido `display` -> raw) antes de tocar el set. Stdlib pura.
"""
import bisect
import math
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import production
from .errors import CommandError
from .production import _bad, _is_int, _is_num, _raw_for_display

MAX_LANES = 16
MAX_POINTS = 4096
MAX_PREROLL = 64.0
EPS_FRAC = 1e-4  # no reescribir si el valor cambio menos del 0.01% del rango
SEEK_TOL = 0.01  # beats: tolerancia para dar por aplicado un current_song_time
SEEK_WINDOW = 0.5  # beats antes del preroll que se aceptan como "ya llegó"
SEEK_RETRY_TICKS = 3  # ticks entre pedidos de salto mientras no llega
PUNCH_TOL = 1e-6
ACTIVE = ("queued", "seeking", "preroll", "recording")
FINAL = ("done", "error", "cancelled")

Points = List[Tuple[float, float]]


def interp(points: Points, t: float) -> float:
    """Poligonal lineal en `t`; antes del primer / despues del ultimo punto se sostiene el valor."""
    times = [p[0] for p in points]
    if t <= times[0]:
        return points[0][1]
    i = bisect.bisect_left(times, t)
    if i >= len(points):
        return points[-1][1]
    (t0, v0), (t1, v1) = points[i - 1], points[i]
    return v0 + (v1 - v0) * (t - t0) / (t1 - t0)


def _resolve_track(song: Any, spec: Any) -> Tuple[Any, Any]:
    """(objeto track, etiqueta) para un indice, {"return": i} o "master"."""
    if spec == "master":
        return song.master_track, "master"
    if isinstance(spec, dict) and set(spec) == {"return"}:
        idx = spec["return"]
        if not _is_int(idx) or not 0 <= idx < len(song.return_tracks):
            raise _bad(f"track.return {idx!r} not found")
        return song.return_tracks[idx], {"return": idx}
    if _is_int(spec):
        if not 0 <= spec < len(song.tracks):
            raise _bad(f"track {spec!r} not found")
        return song.tracks[spec], spec
    raise _bad('track must be an index, {"return": i} or "master"')


def _resolve_param(song: Any, track_spec: Any, target: Any, label: str) -> Tuple[Any, Any, Any, Any]:
    """(track, track_label, param, target_label)."""
    track, track_label = _resolve_track(song, track_spec)
    try:
        param, target_label = production._env_param(track, target)
    except CommandError:
        raise
    except (AttributeError, TypeError) as exc:  # p. ej. send en master
        raise _bad(f"{label}: target {target!r} is not available on this track") from exc
    return track, track_label, param, target_label


class _Lane:
    def __init__(self, track_label: Any, target_label: Any, param: Any, points: Points) -> None:
        self.track, self.target, self.param, self.points = track_label, target_label, param, points
        self.param_name = str(param.name)
        self.lo, self.hi = float(param.min), float(param.max)
        self.last_written: Optional[float] = None
        self.writes = 0

    def write(self, value: float, force: bool = False) -> None:
        value = min(max(value, self.lo), self.hi)
        prev = self.last_written
        if not force and prev is not None and abs(value - prev) <= EPS_FRAC * (self.hi - self.lo):
            return
        self.param.value = value
        self.last_written = value
        self.writes += 1

    def report(self) -> Dict[str, Any]:
        return {"track": self.track, "target": self.target, "param_name": self.param_name,
                "last_value": self.last_written, "writes": self.writes}


def _parse_points(param: Any, raw: Any, label: str, notes: List[str]) -> Points:
    if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_POINTS:
        raise _bad(f"{label}: points must be a list of 1..{MAX_POINTS} [beat, value] pairs")
    lo, hi = float(param.min), float(param.max)
    cache: Dict[float, float] = {}
    out: Points = []
    for i, pt in enumerate(raw):
        if not isinstance(pt, (list, tuple)) or len(pt) != 2:
            raise _bad(f"{label}: points[{i}] must be [beat, value]")
        t, v = pt
        if not _is_num(t) or t < 0:
            raise _bad(f"{label}: points[{i}] beat must be a number >= 0")
        if out and t <= out[-1][0]:
            raise _bad(f"{label}: point beats must be strictly increasing")
        if isinstance(v, dict):
            want = v.get("display")
            if set(v) != {"display"} or not _is_num(want):
                raise _bad(f'{label}: points[{i}] value must be a number or {{"display": number}}')
            if want not in cache:
                raw_v, within = _raw_for_display(param, float(want))
                cache[want] = raw_v
                if not within:
                    notes.append(f"{label}: display {want} not reachable; closest is {param.str_for_value(raw_v)}")
            value = cache[want]
        elif _is_num(v) and lo - production.EPS <= v <= hi + production.EPS:
            value = min(max(float(v), lo), hi)
        else:
            raise _bad(f"{label}: points[{i}] value must be a number in [{lo}, {hi}] or "
                       '{"display": number}')
        out.append((float(t), value))
    return out


class AutomationRecorder:
    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._reset()

    def _reset(self) -> None:
        self.phase = "idle"
        self.errors: List[str] = []
        self.notes: List[str] = []
        self._lanes: List[_Lane] = []
        self._start = 0.0
        self._end = 0.0
        self._preroll_beats = 0.0
        self._tempo = 120.0
        self._deadline = 0.0
        self._seek_to = 0.0
        self._current: Optional[float] = None
        self._touched = False
        self._prev_arm: Optional[bool] = None
        self._prev_time: Optional[float] = None
        self._disarmed: List[Tuple[Any, int, str]] = []

    # -- comandos --

    def busy(self) -> bool:
        return self.phase in ACTIVE

    def record(self, song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        if self.busy():
            raise _bad(f"a recording is already {self.phase}; cancel it first (automation.cancel)")
        start = production._req_num(params, "start_beat", lo=0.0)
        end = production._req_num(params, "end_beat", lo=0.0)
        if end <= start:
            raise _bad("end_beat must be > start_beat")
        preroll = production._num(params, "preroll_beats", lo=0.0, hi=MAX_PREROLL)
        preroll = 4.0 if preroll is None else preroll
        raw = params.get("lanes")
        if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_LANES:
            raise _bad(f"lanes must be a list of 1..{MAX_LANES} objects")
        notes: List[str] = []
        lanes: List[_Lane] = []
        for i, item in enumerate(raw):
            if not isinstance(item, dict) or "track" not in item or "target" not in item:
                raise _bad(f"lanes[{i}] must be an object with track, target and points")
            _, track_label, param, target_label = _resolve_param(song, item["track"], item["target"], f"lanes[{i}]")
            points = _parse_points(param, item.get("points"), f"lanes[{i}]", notes)
            lanes.append(_Lane(track_label, target_label, param, points))
        tempo = float(getattr(song, "tempo", 120.0)) or 120.0
        expected = (end - start + preroll) * 60.0 / tempo
        self._reset()
        self._lanes, self.notes = lanes, notes
        self._start, self._end, self._preroll_beats, self._tempo = start, end, preroll, tempo
        # Tope de reloj por si el transporte nunca avanza (o el usuario lo frena): el doble + 20 s.
        self._deadline = self._clock() + expected * 2.0 + 20.0
        self.phase = "queued"
        return {"queued": True, "phase": self.phase, "lanes": len(lanes), "tempo": tempo,
                "expected_seconds": expected, "warnings": list(notes)}

    def cancel(self, song: Any) -> Dict[str, Any]:
        if not self.busy():
            return {"cancelled": False, "phase": self.phase}
        self._finalize(song)
        self.phase = "cancelled"
        return {"cancelled": True, "phase": self.phase, "errors": list(self.errors)}

    def status(self, song: Any) -> Dict[str, Any]:
        span = self._end - self._start
        if self.phase == "done":
            progress = 1.0
        elif self.phase in ("recording", "error", "cancelled") and self._current is not None and span > 0:
            progress = min(1.0, max(0.0, (self._current - self._start) / span))
        else:
            progress = 0.0
        return {
            "phase": self.phase, "progress": progress, "current_beat": self._current,
            "start_beat": self._start, "end_beat": self._end, "tempo": self._tempo,
            "lanes": [lane.report() for lane in self._lanes], "errors": list(self.errors),
            "warnings": list(self.notes),
            "disarmed_tracks": [{"track": i, "name": n} for _, i, n in self._disarmed],
        }

    # -- maquina de estados (hilo principal) --

    def tick(self, song: Any) -> None:
        if self.phase not in ACTIVE:
            return
        try:
            if self._clock() > self._deadline:
                raise TimeoutError(f"timeout in phase {self.phase}: the transport did not reach the end of the recording")
            getattr(self, "_" + self.phase)(song)
        except Exception as exc:  # noqa: BLE001 - nunca propagar a Live
            self.errors.append(f"{type(exc).__name__}: {exc}")
            self._finalize(song)
            self.phase = "error"

    def _queued(self, song: Any) -> None:
        self._touched = True
        self._prev_arm = bool(song.session_automation_record)
        self._prev_time = float(song.current_song_time)
        if getattr(song, "is_playing", False):
            song.stop_playing()
        # Grabar no debe capturar audio/MIDI: se desarman las pistas armadas y se reportan.
        for i, track in enumerate(song.tracks):
            if getattr(track, "can_be_armed", True) and getattr(track, "arm", False):
                self._disarmed.append((track, i, str(track.name)))
                track.arm = False
        song.session_automation_record = True
        song.record_mode = False
        self._seek_to = max(0.0, self._start - self._preroll_beats)
        for lane in self._lanes:
            lane.write(interp(lane.points, self._start), force=True)
        # Con el transporte parado, ni start_playing() (marcador de inicio) ni continue_playing()
        # respetan un current_song_time puesto por script (visto en Live 12.4.16). Se arranca
        # en cualquier lado y se salta al preroll con el transporte andando (salto inmediato).
        song.start_playing()
        self._seek_wait = 0
        self.phase = "seeking"

    def _seeking(self, song: Any) -> None:
        if not getattr(song, "is_playing", False):
            return
        t = float(song.current_song_time)
        self._current = t
        # Ventana de llegada: del preroll al start; si no hay preroll (start en 0) se acepta
        # medio tiempo después del start y el punch-in ocurre en el tick siguiente.
        hi = self._start - PUNCH_TOL if self._start > self._seek_to else self._seek_to + SEEK_WINDOW
        if self._seek_to - SEEK_WINDOW <= t < hi:
            self.phase = "preroll"
            return
        # Todavía no está en la ventana de preroll: (re)pedir el salto cada pocos ticks.
        if self._seek_wait <= 0:
            song.current_song_time = self._seek_to
            self._seek_wait = SEEK_RETRY_TICKS
        else:
            self._seek_wait -= 1

    def _preroll(self, song: Any) -> None:
        t = float(song.current_song_time)
        self._current = t
        if not getattr(song, "is_playing", False) or t < self._start - PUNCH_TOL:
            return
        song.record_mode = True  # punch-in
        self.phase = "recording"
        for lane in self._lanes:  # forzado: que el valor inicial quede dentro de la ventana grabada
            lane.write(interp(lane.points, t), force=True)

    def _recording(self, song: Any) -> None:
        t = float(song.current_song_time)
        self._current = t
        if t >= self._end:
            for lane in self._lanes:
                lane.write(interp(lane.points, self._end), force=True)
            self._finalize(song)
            self.phase = "done"
            return
        for lane in self._lanes:
            lane.write(interp(lane.points, t))

    def _finalize(self, song: Any) -> None:
        """Restaura el set; cada paso aislado (uno roto no impide los demas)."""
        if not self._touched:
            return

        def attempt(fn: Callable[[], Any]) -> None:
            try:
                fn()
            except Exception as exc:  # noqa: BLE001
                self.errors.append(f"restore: {type(exc).__name__}: {exc}")

        attempt(lambda: setattr(song, "record_mode", False))
        attempt(song.stop_playing)
        if self._prev_time is not None:
            attempt(lambda: setattr(song, "current_song_time", self._prev_time))
        if self._prev_arm is not None:
            attempt(lambda: setattr(song, "session_automation_record", self._prev_arm))
        for track, _, _ in self._disarmed:
            attempt(lambda t=track: setattr(t, "arm", True))
        self._touched = False


def clear(song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    """Best-effort: el LOM no documenta borrar el lane de un parametro; se usa si existe, si no se informa."""
    if "track" not in params or "target" not in params:
        raise _bad("track and target are required")
    _, track_label, param, target_label = _resolve_param(song, params["track"], params["target"], "clear")
    start = production._num(params, "start_beat", lo=0.0)
    end = production._num(params, "end_beat", lo=0.0)
    if (start is None) != (end is None):
        raise _bad("give both start_beat and end_beat, or neither")
    if start is not None and end is not None and end <= start:
        raise _bad("end_beat must be > start_beat")
    out: Dict[str, Any] = {"track": track_label, "target": target_label, "param_name": str(param.name),
                           "supported": False, "cleared": False}
    fn = getattr(param, "clear_automation", None)
    if not callable(fn):
        out["note"] = ("unsupported: this Live build exposes no way to clear a track automation lane; "
                       "record over it with automation.record or delete the range manually")
        return out
    out["supported"] = True
    try:
        fn() if start is None else fn(start, end)
        out["cleared"] = True
    except Exception as exc:  # noqa: BLE001
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out
