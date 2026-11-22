"""T-016: servidor MCP stdio que expone los `live_*` de server.py como tools reales."""
import asyncio
import inspect
import json
import subprocess
import sys
from pathlib import Path

import pytest

from mcp_server.abletonbridge_mcp import server as s
from mcp_server.abletonbridge_mcp import stdio_server as st
from mcp_server.abletonbridge_mcp.client import (
    BridgeCommandError,
    BridgeDisconnectedError,
)

ROOT = Path(__file__).resolve().parents[2]


def public_live_functions(include_spikes: bool = False):
    names = [
        n for n, f in inspect.getmembers(s, inspect.isfunction)
        if n.startswith("live_") and f.__module__ == s.__name__
    ]
    if not include_spikes:
        names = [n for n in names if not n.startswith("live_spike_")]
    return sorted(names)


class FakeClient:
    def __init__(self, result=None):
        self.result = {"ok": True} if result is None else result
        self.sent = []
        self.connected = False
        self.connect_calls = 0
        self.fail_next = None

    def connect_with_retry(self, max_attempts=3):
        self.connect_calls += 1
        self.connected = True

    def close(self):
        self.connected = False

    @property
    def is_connected(self):
        return self.connected

    def send_request(self, cmd, params):
        if self.fail_next is not None:
            exc, self.fail_next = self.fail_next, None
            raise exc
        self.sent.append((cmd, params))
        return self.result

    def ping(self):
        return self.send_request("ping", {})


def list_tools(srv):
    return asyncio.run(srv.list_tools())


def schema_of(tool):
    # mcp 1.x: inputSchema; mcp 2.x: input_schema
    return getattr(tool, "inputSchema", None) or tool.input_schema


# --- registro ---


def test_registered_tools_match_public_live_functions(monkeypatch) -> None:
    monkeypatch.delenv("NEXO_MCP_SPIKES", raising=False)
    srv = st.build_server(client_factory=FakeClient)
    assert sorted(t.name for t in list_tools(srv)) == public_live_functions()


def test_spike_tools_only_with_env_flag(monkeypatch) -> None:
    monkeypatch.setenv("NEXO_MCP_SPIKES", "1")
    srv = st.build_server(client_factory=FakeClient)
    assert sorted(t.name for t in list_tools(srv)) == public_live_functions(include_spikes=True)


def test_schema_hides_injected_params_and_keeps_real_ones(monkeypatch) -> None:
    monkeypatch.delenv("NEXO_MCP_SPIKES", raising=False)
    tools = {t.name: t for t in list_tools(st.build_server(client_factory=FakeClient))}
    for name, tool in tools.items():
        props = schema_of(tool).get("properties", {})
        for hidden in ("client", "sleep", "clock", "cache_dir"):
            assert hidden not in props, (name, hidden)
    assert "return_" in schema_of(tools["live_return_set_mixer"])["properties"]
    assert "lanes" in schema_of(tools["live_automation_record"])["required"]
    assert tools["live_ping"].description  # docstring o descripcion explicita


def test_every_tool_has_a_description(monkeypatch) -> None:
    monkeypatch.delenv("NEXO_MCP_SPIKES", raising=False)
    for t in list_tools(st.build_server(client_factory=FakeClient)):
        assert (t.description or "").strip(), t.name


# --- runtime: conexion lazy, errores, tamano ---


def test_client_is_lazy_and_shared() -> None:
    fake = FakeClient()
    rt = st.BridgeRuntime(client_factory=lambda: fake)
    assert fake.connect_calls == 0
    tools = st.build_tools(rt)
    tools["live_ping"]()
    tools["live_locator_status"]()
    assert fake.connect_calls == 1
    assert [c for c, _ in fake.sent] == ["ping", "locator.status"]


def test_tool_forwards_params_to_existing_function() -> None:
    fake = FakeClient()
    tools = st.build_tools(st.BridgeRuntime(client_factory=lambda: fake))
    tools["live_song_set"](tempo=128.0)
    assert fake.sent[-1] == ("song.set", {"tempo": 128.0})


def test_reconnects_on_next_call_after_disconnect() -> None:
    fake = FakeClient()
    tools = st.build_tools(st.BridgeRuntime(client_factory=lambda: fake))
    tools["live_ping"]()
    fake.fail_next = BridgeDisconnectedError("connection closed by remote script")
    with pytest.raises(RuntimeError, match="BRIDGE_DISCONNECTED"):
        tools["live_ping"]()
    assert fake.connected is False
    tools["live_ping"]()
    assert fake.connect_calls == 2


def test_command_error_keeps_code_in_message() -> None:
    fake = FakeClient()
    tools = st.build_tools(st.BridgeRuntime(client_factory=lambda: fake))
    fake.fail_next = BridgeCommandError("VOLUME_AUTOMATION_FORBIDDEN", "usa Utility Output")
    with pytest.raises(RuntimeError, match="VOLUME_AUTOMATION_FORBIDDEN.*Utility Output"):
        tools["live_ping"]()
    assert fake.connected is True  # un error de dominio no tira la conexion


def test_connect_failure_is_reported_as_runtime_error() -> None:
    class Dead(FakeClient):
        def connect_with_retry(self, max_attempts=3):
            raise BridgeDisconnectedError("could not connect to 127.0.0.1:19845 after 3 attempts")

    tools = st.build_tools(st.BridgeRuntime(client_factory=Dead))
    with pytest.raises(RuntimeError, match="BRIDGE_DISCONNECTED"):
        tools["live_ping"]()


def test_small_result_passes_through(tmp_path) -> None:
    fake = FakeClient({"a": 1})
    rt = st.BridgeRuntime(client_factory=lambda: fake, cache_dir=tmp_path)
    assert st.build_tools(rt)["live_ping"]() == {"a": 1}
    assert list(tmp_path.iterdir()) == []


def test_large_result_is_dumped_to_file_with_summary(tmp_path) -> None:
    big = {"items": [{"n": i, "pad": "x" * 50} for i in range(2000)]}
    fake = FakeClient(big)
    rt = st.BridgeRuntime(client_factory=lambda: fake, cache_dir=tmp_path)
    out = st.build_tools(rt)["live_return_list"]()
    assert out["truncated"] is True
    assert out["chars"] > st.MAX_RESULT_CHARS
    assert len(json.dumps(out)) < 5_000
    saved = json.loads(Path(out["file"]).read_text(encoding="utf-8"))
    assert saved == big
    assert Path(out["file"]).parent == tmp_path.resolve()
    assert out["top_level_keys"] == ["items"]


def test_state_detail_own_dump_is_not_double_wrapped(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(s, "STATE_DETAIL_CACHE", tmp_path / "sd")
    big = {"song": {}, "tracks": [{"index": i, "name": f"t{i}", "devices": [], "pad": "x" * 500}
                                  for i in range(300)]}
    fake = FakeClient(big)
    rt = st.BridgeRuntime(client_factory=lambda: fake, cache_dir=tmp_path / "mcp")
    out = st.build_tools(rt)["live_get_state_detail"]()
    assert out["truncated"] is True and "summary" in out
    assert not (tmp_path / "mcp").exists()


# --- proceso real: handshake + salida limpia en EOF ---


def _rpc(proc, msg):
    proc.stdin.write((json.dumps(msg) + "\n").encode())
    proc.stdin.flush()


def test_stdio_process_handshake_lists_tools_and_exits_on_eof() -> None:
    proc = subprocess.Popen(
        [sys.executable, "-m", "mcp_server.abletonbridge_mcp"],
        cwd=str(ROOT), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env={**__import__("os").environ, "PYTHONPATH": str(ROOT)},
    )
    try:
        _rpc(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-03-26", "capabilities": {},
            "clientInfo": {"name": "pytest", "version": "0"}}})
        init = json.loads(proc.stdout.readline())
        assert init["id"] == 1 and "serverInfo" in init["result"]
        _rpc(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        _rpc(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        listed = json.loads(proc.stdout.readline())
        names = sorted(t["name"] for t in listed["result"]["tools"])
        assert names == public_live_functions()
        proc.stdin.close()  # EOF
        assert proc.wait(timeout=15) == 0
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.stdout.close()
        proc.stderr.close()
