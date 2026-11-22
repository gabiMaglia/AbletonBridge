import json
from pathlib import Path

import numpy as np
import pytest

from nexo_analysis import adapter_songtagger as A

ST_ROOT = Path(r"C:\Users\Gabriel Maglia\Documents\PersonalProjects\songTagger")


def quantized_beats(bpm: float = 130.0, n: int = 800) -> list[float]:
    # madmom trabaja a 100 fps: los beats caen en multiplos de 10 ms
    return [round(k * 60.0 / bpm + 0.013, 2) for k in range(n)]


def raw_worker_output() -> dict:
    beats = quantized_beats()
    return {
        "file": "/mnt/c/x.wav",
        "essentia_bpm": 130.02,
        "essentia_confidence": 3.9,
        "madmom_bpm": 130.43,
        "bpm": 130.43,
        "bpm_source": "madmom",
        "beats": beats,
        "downbeats": beats[::4],
        "key": "C",
        "scale": "minor",
        "key_strength": 0.9,
        "camelot": "5A",
        # campos que la auditoria dice que NO son confiables
        "sections": [{"type": "BUILDUP"}],
        "drops": [{"time": 1.0}],
        "kick_events": [{"event": "kick_in"}],
    }


class FakeRunner:
    def __init__(self, stdout: str = "", returncode: int = 0, stderr: str = ""):
        self.calls: list[list[str]] = []
        self.stdout, self.returncode, self.stderr = stdout, returncode, stderr

    def __call__(self, cmd, timeout=None):
        self.calls.append(list(cmd))
        return A.RunResult(self.returncode, self.stdout, self.stderr)


def test_to_wsl_path():
    assert A.to_wsl_path(r"C:\Users\Gabriel Maglia\a b.wav") == "/mnt/c/Users/Gabriel Maglia/a b.wav"
    assert A.to_wsl_path("G:/LIbrerias/x.wav") == "/mnt/g/LIbrerias/x.wav"
    assert A.to_wsl_path("/already/posix") == "/already/posix"


def test_fit_grid_recovers_true_bpm_from_quantized_beats():
    g = A.fit_grid(quantized_beats(130.0))
    assert g.bpm == pytest.approx(130.0, abs=0.03)
    naive = 60.0 / np.median(np.diff(quantized_beats(130.0)))
    assert abs(naive - 130.0) > 0.3          # el bug C-1 del audit
    assert g.residual_ms < 6


def test_fit_grid_tolerates_missing_beats():
    b = quantized_beats(128.0)
    del b[100:103]
    assert A.fit_grid(b).bpm == pytest.approx(128.0, abs=0.05)


def test_fit_grid_needs_beats():
    with pytest.raises(ValueError):
        A.fit_grid([0.5, 1.0])


def test_normalize_replaces_bpm_with_essentia_and_ignores_unreliable_fields():
    n = A.normalize(raw_worker_output())
    assert n["bpm"]["value"] == pytest.approx(130.02)
    assert n["bpm"]["method"].startswith("essentia")
    assert n["bpm"]["songtagger_quantized"] == pytest.approx(130.43)
    assert n["bpm"]["confidence"] == "high"          # coincide con la grilla ajustada
    assert set(n["ignored"]) == {"sections", "drops", "kick_events"}
    for k in ("sections", "drops", "kick_events"):
        assert k not in n


def test_normalize_flags_minor_bias():
    n = A.normalize(raw_worker_output())
    assert n["key"]["tonic"] == "C" and n["key"]["camelot"] == "5A"
    assert n["key"]["mode_reliable"] is False
    assert any("menor" in w or "minor" in w for w in n["warnings"])


def test_normalize_without_essentia_falls_back_with_low_confidence():
    raw = raw_worker_output()
    del raw["essentia_bpm"]
    n = A.normalize(raw)
    assert n["bpm"]["value"] == pytest.approx(130.0, abs=0.05)    # grilla ajustada, no el cuantizado
    assert n["bpm"]["confidence"] in ("medium", "low")
    assert any("essentia" in w for w in n["warnings"])


def test_normalize_warns_when_estimates_disagree():
    raw = raw_worker_output()
    raw["essentia_bpm"] = 128.0
    n = A.normalize(raw)
    assert n["bpm"]["confidence"] == "medium"
    assert any("difieren" in w for w in n["warnings"])


def test_contract_missing_required_keys_is_rejected():
    raw = raw_worker_output()
    del raw["key"]
    with pytest.raises(A.ContractError) as e:
        A.normalize(raw)
    assert "key" in str(e.value)


@pytest.mark.skipif(not (ST_ROOT / "output").exists(), reason="songTagger no esta en esta maquina")
def test_contract_against_real_songtagger_output():
    f = next((ST_ROOT / "output").glob("*Traffic*.json"))
    n = A.normalize(json.loads(f.read_text(encoding="utf-8")))
    assert n["bpm"]["value"] > 100 and n["key"]["tonic"]


def test_analyze_builds_wsl_command_and_parses_marker_line():
    payload = json.dumps(raw_worker_output())
    runner = FakeRunner(stdout="warning de madmom\nNEXO_JSON:" + payload + "\n")
    cfg = A.SongTaggerConfig(root=ST_ROOT, check_pin=False)
    out = A.analyze(r"C:\music\a.wav", config=cfg, runner=runner)
    cmd = runner.calls[0]
    assert cmd[0] == "wsl.exe" and cmd[1] == "-e"
    assert cmd[2].endswith(".venv-wsl/bin/python")
    assert cmd[3].startswith("/mnt/") and cmd[3].endswith("_songtagger_worker.py")
    assert cmd[-2] == "/mnt/c/Users/Gabriel Maglia/Documents/PersonalProjects/songTagger"
    assert cmd[-1] == "/mnt/c/music/a.wav"
    assert out["bpm"]["value"] == pytest.approx(130.02)


def test_analyze_reports_runner_failure():
    runner = FakeRunner(stdout="", returncode=1, stderr="No module named essentia")
    with pytest.raises(A.SongTaggerError) as e:
        A.analyze("x.wav", config=A.SongTaggerConfig(root=ST_ROOT, check_pin=False), runner=runner)
    assert "essentia" in str(e.value)


def test_analyze_without_marker_is_an_error():
    with pytest.raises(A.SongTaggerError):
        A.analyze("x.wav", config=A.SongTaggerConfig(root=ST_ROOT, check_pin=False), runner=FakeRunner(stdout="hola"))


def test_pin_matches():
    runner = FakeRunner(stdout=A.PINNED_COMMIT + "\n")
    st = A.check_pin(ST_ROOT, runner=runner)
    assert st.ok and runner.calls[0][:3] == ["git", "-C", str(ST_ROOT)]


def test_pin_mismatch_warns_and_analyze_propagates_warning():
    st = A.check_pin(ST_ROOT, runner=FakeRunner(stdout="deadbeef\n"))
    assert not st.ok and st.actual == "deadbeef"

    calls = {"n": 0}

    def runner(cmd, timeout=None):
        calls["n"] += 1
        if cmd[0] == "git":
            return A.RunResult(0, "deadbeef\n", "")
        return A.RunResult(0, "NEXO_JSON:" + json.dumps(raw_worker_output()), "")

    out = A.analyze("x.wav", config=A.SongTaggerConfig(root=ST_ROOT), runner=runner)
    assert any("pin" in w.lower() for w in out["warnings"])
    assert out["songtagger"]["pin_ok"] is False


def test_pinned_commit_is_a_full_sha():
    assert len(A.PINNED_COMMIT) == 40


def test_worker_is_importable_without_essentia():
    # corre en WSL; en Windows solo debe poder importarse (los imports pesados van dentro de main)
    from nexo_analysis import _songtagger_worker as w

    assert callable(w.main)
