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
import json
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


# --- T-017: medicion de niveles (solo lectura) -------------------------------------------------
# Vive aqui y no en un modulo nuevo: el reloader instalado no conoce modulos nuevos (haria falta
# reiniciar Live). Reusa el transporte de AutomationRecorder (start + salto con el transporte andando).

METER_ACTIVE = ("queued", "seeking", "preroll", "measuring")
METER_MAX_BIN_BARS = 64
METER_STATUS_BUDGET = 55_000  # caracteres de JSON; por encima se omiten los bins (tope MCP ~60k)
DB_UNCALIBRATED = "db_estimate_uncalibrated"
DB_CALIBRATED = "db_calibrated"


class MeterCalibration:
    """raw (0..1 del medidor) -> dBFS. Sin puntos: 20*log10(raw), sin calibrar. Con puntos: lineal por
    tramos en espacio log10(raw), extrapolando con la pendiente del tramo extremo (1 punto: 20 dB/decada)."""

    def __init__(self, points: Optional[List[List[float]]]) -> None:
        self.points: List[Tuple[float, float]] = sorted(
            (math.log10(float(r)), float(d)) for r, d in (points or []))
        self.label = DB_CALIBRATED if self.points else DB_UNCALIBRATED

    @classmethod
    def parse(cls, raw: Any) -> "MeterCalibration":
        if raw is None:
            return cls(None)
        pts = raw.get("points") if isinstance(raw, dict) else None
        if not isinstance(pts, list) or not 1 <= len(pts) <= 64:
            raise _bad("calibration must be {points: [[raw, dbfs], ...]} with 1..64 points")
        seen = set()
        for i, p in enumerate(pts):
            if (not isinstance(p, (list, tuple)) or len(p) != 2 or not _is_num(p[0]) or not _is_num(p[1])
                    or p[0] <= 0):
                raise _bad(f"calibration.points[{i}] must be [raw > 0, dbfs]")
            if p[0] in seen:
                raise _bad("calibration.points raw values must be distinct")
            seen.add(p[0])
        return cls(pts)

    def to_db(self, raw: Optional[float]) -> Optional[float]:
        if raw is None or raw <= 0:
            return None
        if not self.points:
            return 20.0 * math.log10(raw)
        x = math.log10(raw)
        pts = self.points
        if len(pts) == 1:
            return pts[0][1] + 20.0 * (x - pts[0][0])
        i = min(max(bisect.bisect_left([p[0] for p in pts], x), 1), len(pts) - 1)
        (x0, d0), (x1, d1) = pts[i - 1], pts[i]
        return d0 + (d1 - d0) * (x - x0) / (x1 - x0)


def _r(v: Optional[float], nd: int) -> Optional[float]:
    return None if v is None else round(v, nd)


class _Acc:
    """Pico (max), suma, suma de cuadrados y cantidad de muestras."""

    __slots__ = ("peak", "sum", "sq", "n")

    def __init__(self) -> None:
        self.peak, self.sum, self.sq, self.n = 0.0, 0.0, 0.0, 0

    def add(self, v: float) -> None:
        self.peak = max(self.peak, v)
        self.sum += v
        self.sq += v * v
        self.n += 1

    def rms(self) -> float:
        return math.sqrt(self.sq / self.n) if self.n else 0.0

    def mean(self) -> float:
        return self.sum / self.n if self.n else 0.0


def _read_meter(track: Any) -> Optional[float]:
    """Nivel crudo 0..1: max(L, R); output_meter_level solo si no hay L/R. None si no hay nada.
    Una propiedad que revienta propaga: la aisla el llamador por target."""
    vals = [float(v) for v in (getattr(track, "output_meter_left", None),
                               getattr(track, "output_meter_right", None)) if v is not None]
    if not vals:
        level = getattr(track, "output_meter_level", None)
        if level is not None:
            vals.append(float(level))
    return max(vals) if vals else None


def _find_gr_sources(track: Any) -> List[Tuple[str, str, Callable[[], float]]]:
    """(device, fuente, lector) de todo atributo/parametro con 'reduction' en el nombre (guardado):
    el LOM no documenta gain reduction, asi que solo se informa lo que realmente exista."""
    found: List[Tuple[str, str, Callable[[], float]]] = []
    try:
        devices = list(getattr(track, "devices", None) or [])
    except Exception:  # noqa: BLE001
        return found
    for dev in devices:
        dname = str(getattr(dev, "name", "?"))
        try:
            attrs = [a for a in dir(dev) if "reduction" in a.lower() and not a.startswith("_")]
            for a in attrs:
                if isinstance(getattr(dev, a, None), (int, float)):
                    found.append((dname, a, lambda d=dev, a=a: float(getattr(d, a))))
            for p in list(getattr(dev, "parameters", None) or []):
                pname = str(getattr(p, "name", ""))
                if "reduction" in pname.lower():
                    found.append((dname, f"param:{pname}", lambda p=p: float(p.value)))
        except Exception:  # noqa: BLE001
            continue
    return found


def _fader_display(track: Any) -> Optional[str]:
    try:
        vol = track.mixer_device.volume
        return str(vol.str_for_value(vol.value))
    except Exception:  # noqa: BLE001
        return None


class _Target:
    def __init__(self, kind: str, index: Optional[int], track: Any) -> None:
        self.kind, self.index, self.track = kind, index, track
        self.name = str(getattr(track, "name", "?"))
        self.fader = _fader_display(track)
        self.total = _Acc()
        self.bins: Dict[int, _Acc] = {}
        self.gr = [(d, s, fn, _Acc()) for d, s, fn in _find_gr_sources(track)]
        self.failed: Optional[str] = None


class MeterCapture:
    """meter.capture: lee los medidores de salida mientras Live reproduce [start, end). Solo lectura."""

    _seeking = AutomationRecorder._seeking  # mismo salto "start y luego saltar" (spike 2)

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._reset()

    def _reset(self) -> None:
        self.phase = "idle"
        self.errors: List[str] = []
        self.notes: List[str] = []
        self._targets: List[_Target] = []
        self._cal = MeterCalibration(None)
        self._start = self._end = self._preroll_beats = self._seek_to = 0.0
        self._bar_beats = 4.0
        self._bin_bars = 8
        self._tempo = 120.0
        self._deadline = 0.0
        self._current: Optional[float] = None
        self._seek_wait = 0
        self._touched = False
        self._prev_time: Optional[float] = None

    def busy(self) -> bool:
        return self.phase in METER_ACTIVE

    # -- comandos --

    def capture(self, song: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        if self.busy():
            raise _bad(f"a meter capture is already {self.phase}; cancel it first (meter.cancel)")
        start = production._req_num(params, "start_beat", lo=0.0)
        end = production._req_num(params, "end_beat", lo=0.0)
        if end <= start:
            raise _bad("end_beat must be > start_beat")
        preroll = production._num(params, "preroll_beats", lo=0.0, hi=MAX_PREROLL)
        preroll = 2.0 if preroll is None else preroll
        bin_bars = params.get("bin_bars", 8)
        if not _is_int(bin_bars) or not 1 <= bin_bars <= METER_MAX_BIN_BARS:
            raise _bad(f"bin_bars must be an integer 1..{METER_MAX_BIN_BARS}")
        inc_ret = params.get("include_returns", True)
        inc_master = params.get("include_master", True)
        if not isinstance(inc_ret, bool) or not isinstance(inc_master, bool):
            raise _bad("include_returns and include_master must be booleans")
        cal = MeterCalibration.parse(params.get("calibration"))
        spec = params.get("tracks", "all")
        if spec == "all":
            idxs = list(range(len(song.tracks)))
        elif isinstance(spec, list) and spec and all(_is_int(i) for i in spec):
            missing = [i for i in spec if not 0 <= i < len(song.tracks)]
            if missing:
                raise _bad(f"track {missing[0]!r} not found")
            idxs = list(dict.fromkeys(spec))
        else:
            raise _bad('tracks must be "all" or a non-empty list of track indices')

        notes: List[str] = []
        targets: List[_Target] = []

        def add(kind: str, index: Optional[int], track: Any) -> None:
            if getattr(track, "has_audio_output", True) is False:
                notes.append(f"{getattr(track, 'name', '?')}: MIDI-only output (no audio), skipped")
                return
            targets.append(_Target(kind, index, track))

        for i in idxs:
            add("track", i, song.tracks[i])
        if inc_ret:
            for i, tr in enumerate(song.return_tracks):
                add("return", i, tr)
        if inc_master:
            add("master", None, song.master_track)
        if not targets:
            raise _bad("no measurable audio targets selected")

        tempo = float(getattr(song, "tempo", 120.0)) or 120.0
        num = float(getattr(song, "signature_numerator", 4) or 4)
        den = float(getattr(song, "signature_denominator", 4) or 4)
        expected = (end - start + preroll) * 60.0 / tempo
        self._reset()
        self._targets, self._cal, self.notes = targets, cal, notes
        self._start, self._end, self._preroll_beats, self._tempo = start, end, preroll, tempo
        self._bar_beats, self._bin_bars = num * 4.0 / den, bin_bars
        self._deadline = self._clock() + expected * 2.0 + 20.0
        self.phase = "queued"
        return {"queued": True, "phase": self.phase, "targets": len(targets), "tempo": tempo,
                "expected_seconds": expected, "db_mapping": cal.label, "warnings": list(notes)}

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
        elif self.phase in ("measuring", "error", "cancelled") and self._current is not None and span > 0:
            progress = min(1.0, max(0.0, (self._current - self._start) / span))
        else:
            progress = 0.0
        warnings = list(self.notes)
        warnings += [f"{t.name}: meter read failed ({t.failed})" for t in self._targets if t.failed]
        out: Dict[str, Any] = {
            "phase": self.phase, "progress": round(progress, 3), "current_beat": self._current,
            "start_beat": self._start, "end_beat": self._end, "tempo": self._tempo,
            "db_mapping": self._cal.label, "bin_bars": self._bin_bars,
            "targets": [self._report(t) for t in self._targets], "errors": list(self.errors),
            "warnings": warnings,
        }
        if len(json.dumps(out)) > METER_STATUS_BUDGET:
            for t in out["targets"]:
                t.pop("bins", None)
            warnings.append("bins omitted: result too large; use a larger bin_bars or fewer tracks")
        return out

    def _report(self, t: _Target) -> Dict[str, Any]:
        db = self._cal.to_db
        rep: Dict[str, Any] = {
            "kind": t.kind, "index": t.index, "name": t.name, "fader_display": t.fader,
            "samples": t.total.n, "peak_raw": _r(t.total.peak, 4), "peak_db_est": _r(db(t.total.peak), 1),
            "rms_raw": _r(t.total.rms(), 4), "rms_db_est": _r(db(t.total.rms()), 1),
        }
        bins = []
        for idx in sorted(t.bins):
            a = t.bins[idx]
            bin_start = self._start + idx * self._bin_bars * self._bar_beats
            bar_from = int(math.floor(bin_start / self._bar_beats + 1e-9)) + 1
            bins.append({"bar_from": bar_from, "bar_to": bar_from + self._bin_bars - 1,
                         "peak_raw": _r(a.peak, 4), "peak_db_est": _r(db(a.peak), 1),
                         "rms_db_est": _r(db(a.rms()), 1)})
        rep["bins"] = bins
        sampled = [{"device": d, "source": s, "max": _r(a.peak, 2), "mean": _r(a.mean(), 2)}
                   for d, s, _, a in t.gr if a.n]
        rep["gain_reduction"] = sampled or "unavailable"
        return rep

    # -- maquina de estados (hilo principal) --

    def tick(self, song: Any) -> None:
        if self.phase not in METER_ACTIVE:
            return
        try:
            if self._clock() > self._deadline:
                raise TimeoutError(f"timeout in phase {self.phase}: the transport did not reach the end of the range")
            getattr(self, "_" + self.phase)(song)
        except Exception as exc:  # noqa: BLE001 - nunca propagar a Live
            self.errors.append(f"{type(exc).__name__}: {exc}")
            self._finalize(song)
            self.phase = "error"

    def _queued(self, song: Any) -> None:
        self._touched = True
        self._prev_time = float(song.current_song_time)
        if getattr(song, "is_playing", False):
            song.stop_playing()
        self._seek_to = max(0.0, self._start - self._preroll_beats)
        song.start_playing()
        self._seek_wait = 0
        self.phase = "seeking"

    def _preroll(self, song: Any) -> None:
        t = float(song.current_song_time)
        self._current = t
        if not getattr(song, "is_playing", False) or t < self._start - PUNCH_TOL:
            return
        self.phase = "measuring"
        self._measuring(song)

    def _measuring(self, song: Any) -> None:
        t = float(song.current_song_time)
        self._current = t
        if t >= self._end:
            self._finalize(song)
            self.phase = "done"
            return
        idx = int((t - self._start) // (self._bin_bars * self._bar_beats))
        for tg in self._targets:
            self._sample(tg, idx)

    def _sample(self, tg: _Target, idx: int) -> None:
        try:
            v = _read_meter(tg.track)
        except Exception as exc:  # noqa: BLE001 - aislado por target
            tg.failed = f"{type(exc).__name__}: {exc}"
            return
        if v is not None:
            tg.total.add(v)
            tg.bins.setdefault(idx, _Acc()).add(v)
        for _, _, fn, acc in tg.gr:
            try:
                acc.add(abs(fn()))
            except Exception:  # noqa: BLE001
                pass

    def _finalize(self, song: Any) -> None:
        """Restaura transporte y playhead; jamas se toca record_mode ni Automation Arm."""
        if not self._touched:
            return

        def attempt(fn: Callable[[], Any]) -> None:
            try:
                fn()
            except Exception as exc:  # noqa: BLE001
                self.errors.append(f"restore: {type(exc).__name__}: {exc}")

        attempt(song.stop_playing)
        if self._prev_time is not None:
            attempt(lambda: setattr(song, "current_song_time", self._prev_time))
        self._touched = False
