"""Senales sinteticas con respuesta conocida (sin audio con copyright)."""
from __future__ import annotations

import numpy as np

SR = 44100


def sine(freq: float, secs: float, amp: float = 1.0, sr: int = SR, phase: float = 0.0) -> np.ndarray:
    t = np.arange(int(secs * sr)) / sr
    return amp * np.sin(2 * np.pi * freq * t + phase)


def stereo(mono: np.ndarray) -> np.ndarray:
    return np.stack([mono, mono], axis=1)


def pink_noise(n: int, seed: int = 0) -> np.ndarray:
    """Ruido rosa por filtrado espectral 1/sqrt(f), normalizado a RMS 1."""
    rng = np.random.default_rng(seed)
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n)
    f[0] = f[1]
    x = np.fft.irfft(spec / np.sqrt(f), n)
    return x / np.sqrt(np.mean(x**2))


def kick(
    f_end: float,
    f_start: float = 160.0,
    glide_tau: float = 0.020,
    decay_tau: float = 0.25,
    secs: float = 0.6,
    click: float = 0.3,
    sr: int = SR,
) -> np.ndarray:
    """Kick con barrido exponencial de pitch hacia f_end y un click inicial."""
    t = np.arange(int(secs * sr)) / sr
    inst = f_end + (f_start - f_end) * np.exp(-t / glide_tau)
    phase = 2 * np.pi * np.cumsum(inst) / sr
    body = np.sin(phase) * np.exp(-t / decay_tau)
    rng = np.random.default_rng(1)
    tick = np.zeros_like(t)
    n = int(0.002 * sr)
    tick[:n] = click * rng.standard_normal(n) * np.hanning(2 * n)[n:]
    return 0.9 * body + tick


def note_hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def rumble_loop(
    f0: float,
    bpm: float = 134.0,
    bars: int = 2,
    h2: float = 0.0,
    noise_db: float | None = None,
    sr: int = SR,
) -> np.ndarray:
    """Rumble: tono grave bombeado a negras (sidechain) con 2do armonico opcional."""
    beat = 60.0 / bpm
    secs = beat * 4 * bars
    t = np.arange(int(secs * sr)) / sr
    pos = (t % beat) / beat
    pump = 0.15 + 0.85 * np.clip(pos / 0.5, 0, 1)
    x = np.sin(2 * np.pi * f0 * t) + h2 * np.sin(2 * np.pi * 2 * f0 * t)
    x = 0.5 * pump * x / max(1.0, 1 + h2)
    if noise_db is not None:
        x = x + 0.5 * 10 ** (noise_db / 20) * pink_noise(len(t)) * pump
    return x
