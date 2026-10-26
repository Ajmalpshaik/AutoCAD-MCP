"""The Heron gate every tool passes through, with the bridge and COM faked."""

from __future__ import annotations

import asyncio
import json
import os

import pytest
import pythoncom

from autocad_mcp.core import audit, connection, gate
from autocad_mcp.core.bridge import NOT_CONNECTED, NOTHING_SENT, BridgeRefused
from autocad_mcp.core.errors import OutcomeUnknown
from autocad_mcp.core.registry import tool_errors

BUSY = pythoncom.com_error(-2147418111, "Call was rejected by callee.", None, None)


class FakeBridge:
    refuse: str | None = None
    answer = "keep"
    calls: list[tuple] = []

    def __init__(self, pid: int) -> None:
        self.pid = pid

    def begin(self, tool, risk, summary, drawing):
        FakeBridge.calls.append(("begin", tool, risk, summary, drawing))
        if FakeBridge.refuse:
            raise BridgeRefused(FakeBridge.refuse)
        return "job1"

    def end(self, job, ok, outcome, summary, ms):
        FakeBridge.calls.append(("end", job, ok, outcome))

    def ask_keep(self, job, summary, handles):
        FakeBridge.calls.append(("ask_keep", job, tuple(handles)))
        return FakeBridge.answer


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("HERON_AUTOCAD_BRIDGE", "on")
    FakeBridge.refuse = None
    FakeBridge.answer = "keep"
    FakeBridge.calls = []
    state = {"drawing": r"C:\a.dwg", "discards": 0}

    async def probe():
        return 1234, state["drawing"]

    async def discard():
        state["discards"] += 1

    monkeypatch.setattr(gate, "Bridge", FakeBridge)
    monkeypatch.setattr(gate, "_probe", probe)
    monkeypatch.setattr(gate, "_discard", discard)
    gate.reset()
    return state


def make_tool(name: str, result: str = '{"created": true, "handle": "2A"}'):
    calls: list[int] = []

    async def tool() -> str:
        calls.append(1)
        return result

    tool.__name__ = name
    return tool_errors(tool), calls


def call(tool) -> str:
    return asyncio.run(tool())


def audit_lines() -> list[dict]:
    folder = audit.audit_dir()
    lines = []
    for path in folder.glob("audit-*.jsonl"):
        lines += [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    return lines


def test_refused_tool_never_runs_work(env):
    FakeBridge.refuse = "Changes is off. " + NOTHING_SENT
    tool, calls = make_tool("autocad_draw_line")
    result = call(tool)
    assert calls == []
    assert result.startswith("Error: Changes is off.")
    assert result.endswith(NOTHING_SENT)


def test_not_connected_status_still_answers(env):
    FakeBridge.refuse = NOT_CONNECTED
    tool, calls = make_tool("autocad_status", '{"connected": true}')
    result = json.loads(call(tool))
    assert calls == [1]
    assert result["heron"] == {"connected": False, "message": NOT_CONNECTED}


def test_end_called_on_success_and_failure(env):
    ok_tool, _ = make_tool("autocad_list_layers", "[]")
    bad_tool, _ = make_tool("autocad_list_layers", "Error: something broke")
    call(ok_tool)
    call(bad_tool)
    ends = [c for c in FakeBridge.calls if c[0] == "end"]
    assert [e[2] for e in ends] == [True, False]


def test_audit_line_fields(env):
    tool, _ = make_tool("autocad_list_layers", "[]")
    call(tool)
    line = audit_lines()[-1]
    assert set(line) == {"at", "conversation", "tool", "risk", "drawing", "ok", "outcome", "ms"}
    assert line["tool"] == "autocad_list_layers"
    assert line["risk"] == "read"
    assert line["drawing"] == r"C:\a.dwg"
    assert line["ok"] is True
    assert line["outcome"] == "done"


def test_audit_write_failure_does_not_fail_tool(env, monkeypatch):
    monkeypatch.setattr(audit, "audit_dir", lambda: os.devnull + r"\nope")
    tool, _ = make_tool("autocad_list_layers", "[]")
    assert call(tool) == "[]"


def test_wrong_drawing_refused_for_change(env):
    look, _ = make_tool("autocad_list_layers", "[]")
    call(look)
    env["drawing"] = r"C:\b.dwg"
    tool, calls = make_tool("autocad_draw_line")
    result = call(tool)
    assert calls == []
    assert r"C:\a.dwg" in result and r"C:\b.dwg" in result
    assert result.endswith(NOTHING_SENT)


def test_wrong_drawing_allowed_for_read(env):
    look, _ = make_tool("autocad_list_layers", "[]")
    call(look)
    env["drawing"] = r"C:\b.dwg"
    tool, calls = make_tool("autocad_list_entities", "[]")
    call(tool)
    assert calls == [1]
    # Having looked, the AI may now change the new drawing.
    draw, draw_calls = make_tool("autocad_draw_line")
    call(draw)
    assert draw_calls == [1]


def test_discard_undoes_once(env):
    FakeBridge.answer = "discard"
    tool, _ = make_tool("autocad_draw_line", '{"created": true, "handle": "2A"}')
    result = call(tool)
    assert ("ask_keep", "job1", ("2A",)) in FakeBridge.calls
    assert env["discards"] == 1
    assert result == "Discarded: nothing was kept."
    assert audit_lines()[-1]["outcome"] == "discarded"


def test_keep_returns_result_unchanged(env):
    tool, _ = make_tool("autocad_draw_line", '{"created": true, "handle": "2A"}')
    assert call(tool) == '{"created": true, "handle": "2A"}'
    assert env["discards"] == 0


def test_read_tools_are_never_asked_to_keep(env):
    tool, _ = make_tool("autocad_get_entity", '{"handle": "2A"}')
    call(tool)
    assert not [c for c in FakeBridge.calls if c[0] == "ask_keep"]


def test_no_retry_after_write_began(monkeypatch):
    monkeypatch.setattr(connection, "RETRY_DELAY", 0)
    attempts: list[int] = []

    def work():
        attempts.append(1)
        connection.mark_writing()
        raise BUSY

    with pytest.raises(OutcomeUnknown) as err:
        connection._with_retry(work)
    assert attempts == [1]
    assert "Read the drawing back before retrying" in str(err.value)


def test_retry_still_happens_before_write(monkeypatch):
    monkeypatch.setattr(connection, "RETRY_DELAY", 0)
    attempts: list[int] = []

    def work():
        attempts.append(1)
        if len(attempts) < 3:
            raise BUSY
        connection.mark_writing()
        return "drawn"

    assert connection._with_retry(work) == "drawn"
    assert len(attempts) == 3


def test_bridge_off_skips_plugin_but_keeps_audit(env, monkeypatch):
    monkeypatch.setenv("HERON_AUTOCAD_BRIDGE", "off")
    tool, calls = make_tool("autocad_draw_line")
    call(tool)
    assert calls == [1]
    assert FakeBridge.calls == []
    assert audit_lines()[-1]["tool"] == "autocad_draw_line"


class _Obj:
    def __init__(self, name, handle="2A", doc=None):
        self.ObjectName = name
        self.Handle = handle
        self.Layer = "0"
        self.Document = doc


class _Doc:
    def __init__(self, found):
        self.found = found

    def HandleToObject(self, handle):
        if self.found is None:
            raise RuntimeError("no such handle")
        return self.found


def test_created_payload_reads_back(monkeypatch):
    from autocad_mcp.tools import _shared

    monkeypatch.setattr(_shared, "describe", lambda e, include_geometry=False: {"type": "line"})
    good = _Obj("AcDbLine", doc=_Doc(_Obj("AcDbLine")))
    assert _shared.created_payload(good, {})["verified"] is True
    missing = _Obj("AcDbLine", doc=_Doc(None))
    payload = _shared.created_payload(missing, {})
    assert payload["verified"] is False
    assert "could not be read back" in payload["warning"]


def test_no_bridge_flag_switches_bridge_off(monkeypatch):
    from autocad_mcp import server

    monkeypatch.setenv("HERON_AUTOCAD_BRIDGE", "on")
    server.apply_options(server.build_parser().parse_args(["--no-bridge"]))
    assert os.environ["HERON_AUTOCAD_BRIDGE"] == "off"


def test_no_autocad_with_bridge_off_lets_the_tool_answer(env, monkeypatch):
    monkeypatch.setenv("HERON_AUTOCAD_BRIDGE", "off")

    async def no_autocad():
        raise gate.AutocadError("No running AutoCAD instance was found.")

    monkeypatch.setattr(gate, "_probe", no_autocad)
    tool, calls = make_tool("autocad_draw_line")
    call(tool)
    assert calls == [1]


def test_no_autocad_with_bridge_on_refuses(env, monkeypatch):
    async def no_autocad():
        raise gate.AutocadError("No running AutoCAD instance was found.")

    monkeypatch.setattr(gate, "_probe", no_autocad)
    tool, calls = make_tool("autocad_draw_line")
    assert call(tool).startswith("Error: No running AutoCAD")
    assert calls == []
