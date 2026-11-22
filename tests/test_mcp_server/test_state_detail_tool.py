"""live_get_state_detail: envio del cmd y guard de tamano (volcado a archivo)."""
import json
from pathlib import Path

from mcp_server.abletonbridge_mcp import server as s


class C:
    def __init__(self, result):
        self.result = result
        self.sent = []

    def send_request(self, cmd, params):
        self.sent.append((cmd, params))
        return self.result


def test_sends_expected_cmd_and_defaults(tmp_path) -> None:
    c = C({"song": {}, "tracks": []})
    out = s.live_get_state_detail(c, cache_dir=tmp_path)
    assert c.sent == [(
        "state.detail",
        {"params": "changed", "include_arrangement": True, "include_session": True},
    )]
    assert out == {"song": {}, "tracks": []}


def test_forwards_track_filter(tmp_path) -> None:
    c = C({"tracks": []})
    s.live_get_state_detail(c, tracks=[1, 2], params="all", include_session=False, cache_dir=tmp_path)
    assert c.sent[0][1] == {
        "tracks": [1, 2], "params": "all",
        "include_arrangement": True, "include_session": False,
    }


def test_large_result_is_written_to_file_with_summary(tmp_path) -> None:
    big = {
        "song": {"tempo": 120.0},
        "tracks": [
            {"index": 0, "name": "Kick", "kind": "audio",
             "devices": [{"name": "EQ", "class_name": "Eq8", "blob": "x" * 70_000}]},
            {"index": 1, "name": "Mel", "kind": "midi", "devices": []},
        ],
        "returns": [], "master": {"devices": []},
    }
    out = s.live_get_state_detail(C(big), cache_dir=tmp_path / "cache")
    assert out["truncated"] is True
    path = Path(out["file"])
    assert path.is_absolute() and path.parent == tmp_path / "cache"
    assert json.loads(path.read_text(encoding="utf-8")) == big
    assert out["summary"]["tracks"] == [
        {"index": 0, "name": "Kick", "kind": "audio", "devices": ["EQ"]},
        {"index": 1, "name": "Mel", "kind": "midi", "devices": []},
    ]


def test_small_result_not_truncated(tmp_path) -> None:
    out = s.live_get_state_detail(C({"tracks": []}), cache_dir=tmp_path / "c")
    assert "truncated" not in out
    assert not (tmp_path / "c").exists()
