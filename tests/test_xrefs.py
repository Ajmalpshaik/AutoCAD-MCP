"""Attaching and managing xrefs (no AutoCAD)."""

from __future__ import annotations

import asyncio
import json
import math

import pytest

from autocad_mcp.core.risk import Risk, risk_of
from autocad_mcp.tools import xrefs


class Block:
    def __init__(self, name, is_xref=True, path=""):
        self.Name, self.IsXRef, self.Path = name, is_xref, path
        self.calls = []

    def Reload(self):
        self.calls.append("Reload")

    def Unload(self):
        self.calls.append("Unload")

    def Detach(self):
        self.calls.append("Detach")

    def Bind(self, prefix):
        self.calls.append(("Bind", prefix))


class Blocks:
    def __init__(self, *blocks):
        self.items = list(blocks)

    @property
    def Count(self):
        return len(self.items)

    def Item(self, i):
        return self.items[i]


class Reference:
    def __init__(self, name):
        self.Handle, self.ObjectName, self.Layer, self.Name = "3B0", "AcDbBlockReference", "0", name
        self.Document = self

    def HandleToObject(self, handle):
        return self


class Space:
    def __init__(self, doc):
        self.doc, self.calls = doc, []

    def AttachExternalReference(self, path, name, point, sx, sy, sz, rotation, overlay):
        self.calls.append((path, name, tuple(point.value), sx, sy, sz, rotation, overlay))
        self.doc.Blocks.items.append(Block(name, True, path))
        return Reference(name)


class Doc:
    def __init__(self, *blocks):
        self.Blocks = Blocks(Block("*Model_Space", False), *blocks)
        self.ModelSpace = self.PaperSpace = Space(self)

    def GetVariable(self, name):
        return {"UCSORG": (0.0, 0.0, 0.0), "UCSXDIR": (1.0, 0.0, 0.0), "UCSYDIR": (0.0, 1.0, 0.0)}[name]

    def StartUndoMark(self):
        pass

    def EndUndoMark(self):
        pass


def _patch(monkeypatch, fake):
    async def run(fn):
        return fn()

    monkeypatch.setattr(xrefs, "run", run)
    monkeypatch.setattr(xrefs, "get_doc", lambda: fake)
    monkeypatch.setattr(xrefs, "require_idle", lambda d: None)
    monkeypatch.setattr(xrefs, "apply_properties", lambda *a, **k: {})
    return fake


@pytest.fixture
def plan_file(tmp_path):
    path = tmp_path / "A-101 Architect.dwg"
    path.write_bytes(b"AC1032")
    return path


def call(coro):
    answer = asyncio.run(coro)
    assert not answer.startswith("Error"), answer
    return json.loads(answer)


class TestAttach:
    def test_it_is_named_after_the_file_and_placed_as_asked(self, monkeypatch, plan_file):
        fake = _patch(monkeypatch, Doc())
        out = call(xrefs.autocad_attach_xref(path=str(plan_file), insertion=[1000, 500], rotation=90))
        (path, name, point, sx, sy, sz, rotation, overlay), = fake.ModelSpace.calls
        assert name == "A-101 Architect" and path.endswith("A-101 Architect.dwg")
        assert point == (1000.0, 500.0, 0.0) and (sx, sy, sz) == (1.0, 1.0, 1.0)
        assert rotation == pytest.approx(math.pi / 2) and overlay is False
        assert out["name"] == "A-101 Architect" and out["overlay"] is False

    def test_overlay_is_passed_through(self, monkeypatch, plan_file):
        fake = _patch(monkeypatch, Doc())
        call(xrefs.autocad_attach_xref(path=str(plan_file), name="ARCH", overlay=True))
        assert fake.ModelSpace.calls[0][1] == "ARCH" and fake.ModelSpace.calls[0][-1] is True

    def test_a_name_already_in_the_drawing_is_refused(self, monkeypatch, plan_file):
        fake = _patch(monkeypatch, Doc(Block("arch", True)))
        answer = asyncio.run(xrefs.autocad_attach_xref(path=str(plan_file), name="ARCH"))
        assert answer.startswith("Error") and "autocad_manage_xref" in answer
        assert fake.ModelSpace.calls == []

    def test_a_missing_file_is_refused(self, monkeypatch, tmp_path):
        _patch(monkeypatch, Doc())
        answer = asyncio.run(xrefs.autocad_attach_xref(path=str(tmp_path / "nope.dwg")))
        assert answer.startswith("Error") and "No .dwg file" in answer


class TestManage:
    @pytest.mark.parametrize(("action", "expected"), [("reload", "Reload"), ("unload", "Unload")])
    def test_reload_and_unload(self, monkeypatch, action, expected):
        block = Block("ARCH")
        _patch(monkeypatch, Doc(block))
        call(xrefs.autocad_manage_xref(name="arch", action=action))
        assert block.calls == [expected]

    @pytest.mark.parametrize(("action", "expected"), [
        ("detach", "Detach"),
        ("bind", ("Bind", True)),     # names kept apart with ARCH$0$ prefixes
        ("insert", ("Bind", False)),  # names merged into the drawing's own
    ])
    def test_detach_and_bind_need_confirm(self, monkeypatch, action, expected):
        block = Block("ARCH")
        _patch(monkeypatch, Doc(block))
        preview = call(xrefs.autocad_manage_xref(name="ARCH", action=action))
        assert block.calls == [] and preview["confirmed"] is False
        call(xrefs.autocad_manage_xref(name="ARCH", action=action, confirm=True))
        assert block.calls == [expected]

    def test_a_block_that_is_not_an_xref_is_refused(self, monkeypatch):
        block = Block("VALVE", is_xref=False)
        _patch(monkeypatch, Doc(block))
        answer = asyncio.run(xrefs.autocad_manage_xref(name="VALVE", action="reload"))
        assert answer.startswith("Error") and "not an xref" in answer and block.calls == []

    def test_a_missing_xref_points_at_the_list(self, monkeypatch):
        _patch(monkeypatch, Doc())
        answer = asyncio.run(xrefs.autocad_manage_xref(name="GHOST", action="reload"))
        assert answer.startswith("Error") and "autocad_list_blocks" in answer


def test_levels():
    assert risk_of("autocad_attach_xref") is Risk.CHANGE
    assert risk_of("autocad_manage_xref") is Risk.CHANGE


class TurnedDoc(Doc):
    """A plan UCS turned 90 degrees."""

    def GetVariable(self, name):
        return {"UCSORG": (0.0, 0.0, 0.0), "UCSXDIR": (0.0, 1.0, 0.0), "UCSYDIR": (-1.0, 0.0, 0.0)}[name]


def test_with_ucs_coordinates_the_rotation_is_turned_too(monkeypatch, plan_file):
    """coords='ucs' means points and angles: an xref square to a turned grid is turned with it."""
    fake = _patch(monkeypatch, TurnedDoc())
    call(xrefs.autocad_attach_xref(path=str(plan_file), rotation=0, coords="ucs"))
    assert fake.ModelSpace.calls[0][6] == pytest.approx(math.pi / 2)


def test_a_relative_path_is_made_whole_before_autocad_sees_it(monkeypatch, plan_file):
    """AutoCAD would read a relative path from its own folder, not the server's."""
    fake = _patch(monkeypatch, Doc())
    monkeypatch.chdir(plan_file.parent)
    call(xrefs.autocad_attach_xref(path=plan_file.name))
    sent = fake.ModelSpace.calls[0][0]
    assert sent == str(plan_file) and sent == str(plan_file.resolve())
