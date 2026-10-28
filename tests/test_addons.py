"""Small additions from the Lee Mac study: double offset, label mask, nested block count,
spline length, overlapping dimensions (ideas only; Heron's own code)."""

from __future__ import annotations

import asyncio
import inspect
import json
import math

import pytest

from autocad_mcp.acad.curves import curve_length
from autocad_mcp.tools import labels, modify, takeoff
from autocad_mcp.tools.standards import check


def test_offset_has_both_sides_option():
    assert "both_sides" in inspect.signature(modify.autocad_offset_entities).parameters


def test_label_has_mask_option():
    assert "mask" in inspect.signature(labels.autocad_add_label).parameters


def test_nested_counts_multiply_through_levels():
    top = [{"block": "ROOM", "layer": "A", "visibility": None, "properties": {}}] * 2
    children = {"ROOM": [("DESK", "F"), ("DESK", "F"), ("LIGHT", "E")], "DESK": [("SOCKET", "E")]}
    rows = takeoff.expand_nested(top, children)
    names = sorted(r["block"] for r in rows)
    assert names.count("DESK") == 4 and names.count("SOCKET") == 4 and names.count("LIGHT") == 2
    assert names.count("ROOM") == 2


def test_nested_counts_stop_on_a_loop():
    rows = takeoff.expand_nested([{"block": "A", "layer": "0", "visibility": None, "properties": {}}], {"A": [("A", "0")]})
    assert len(rows) < 50


class Spline:
    ObjectName, Degree, IsRational = "AcDbSpline", 1, False
    ControlPoints = (0.0, 0.0, 0.0, 3.0, 4.0, 0.0)
    Knots = (0.0, 0.0, 1.0, 1.0)
    Weights = ()


class Ellipse:
    ObjectName, MajorRadius, MinorRadius, StartParameter, EndParameter = "AcDbEllipse", 2.0, 2.0, 0.0, math.pi


def test_spline_and_ellipse_have_a_length_now():
    assert curve_length(Spline()) == pytest.approx(5)
    assert curve_length(Ellipse()) == pytest.approx(2 * math.pi)


def test_total_length_uses_curve_length():
    assert takeoff._length(Spline()) == pytest.approx(5)


def test_overlapping_dimensions_rule():
    dims = [
        {"handle": "D1", "type": "AcDbRotatedDimension", "layer": "G-DIMS", "box": (0, 0, 10, 2)},
        {"handle": "D2", "type": "AcDbRotatedDimension", "layer": "G-DIMS", "box": (5, 0, 15, 2)},
        {"handle": "D3", "type": "AcDbRotatedDimension", "layer": "G-DIMS", "box": (15, 0, 25, 2)},
    ]
    report = check([], dims, {"forbid_overlapping_dimensions": True})
    assert [(f["handle"], f["other"]) for f in report["findings"]] == [("D1", "D2")]


def test_offset_both_sides_makes_two_copies(monkeypatch):
    class Line:
        Handle, ObjectName = "1A", "AcDbLine"

        def __init__(self):
            self.made = []

        def Offset(self, d):
            self.made.append(d)

            class New:
                Handle = f"N{len(self.made)}"
            return [New()]

    line = Line()

    class Doc:
        def StartUndoMark(self):
            pass

        def EndUndoMark(self):
            pass

    async def run(fn):
        return fn()

    monkeypatch.setattr(modify, "run", run)
    monkeypatch.setattr(modify, "get_doc", lambda: Doc())
    monkeypatch.setattr(modify, "require_idle", lambda d: None)
    monkeypatch.setattr(modify, "resolve_handle", lambda d, h: line)
    result = json.loads(asyncio.run(modify.autocad_offset_entities(handles=["1A"], distance=50, both_sides=True)))
    assert line.made == [50.0, -50.0] and result["offset"] == 2


def test_total_length_reads_curves_only():
    # Live check 2026-10-26: a label's LEADER was counted as an unmeasured item.
    assert takeoff.is_curve("AcDbLine") and takeoff.is_curve("AcDbSpline") and takeoff.is_curve("AcDbPolyline")
    for kind in ("AcDbLeader", "AcDbMLeader", "AcDbMText", "AcDbBlockReference", "AcDbRotatedDimension", "AcDbHatch"):
        assert not takeoff.is_curve(kind)


def test_a_named_hatch_pattern_is_asked_for_as_predefined(monkeypatch):
    """AcPatternType: 0 is user-defined, 1 is predefined (acad.pat). With 0, AutoCAD
    refuses 'ANSI31' as a bad pattern name; the code passed 0 believing it predefined."""
    from autocad_mcp.tools import draw

    class Hatch:
        Handle, ObjectName, Layer, PatternName, Area = "2B0", "AcDbHatch", "0", "ANSI31", 12.0

        def AppendOuterLoop(self, loops):
            pass

        def Evaluate(self):
            pass

    class Space:
        asked = None

        def AddHatch(self, pattern_type, name, associative):
            Space.asked = (pattern_type, name)
            return Hatch()

    class Boundary:
        ObjectName, Closed = "AcDbPolyline", True

    class Doc:
        ModelSpace = PaperSpace = Space()

        def HandleToObject(self, handle):
            return Boundary()

        def StartUndoMark(self):
            pass

        def EndUndoMark(self):
            pass

    async def run(fn):
        return fn()

    monkeypatch.setattr(draw, "run", run)
    monkeypatch.setattr(draw, "get_doc", lambda: Doc())
    monkeypatch.setattr(draw, "require_idle", lambda d: None)
    monkeypatch.setattr(draw, "apply_properties", lambda *a, **k: {})
    answer = asyncio.run(draw.autocad_add_hatch(boundary_handles=["2A0"], pattern="ansi31"))
    assert not answer.startswith("Error"), answer
    assert Space.asked == (1, "ANSI31")


def test_a_hatch_pattern_not_in_acad_pat_is_tried_as_a_custom_pattern_file(monkeypatch):
    """A pattern from autocad_create_hatch_pattern lives in its own NAME.pat: type 2, custom."""
    from autocad_mcp.tools import draw

    class Hatch:
        Handle, ObjectName, Layer, PatternName, Area = "2B1", "AcDbHatch", "0", "CHW-INS", 1.0

        def AppendOuterLoop(self, loops):
            pass

        def Evaluate(self):
            pass

    class Space:
        asked = []

        def AddHatch(self, pattern_type, name, associative):
            Space.asked.append(pattern_type)
            if pattern_type == 1:
                raise ValueError("Invalid input")  # not in acad.pat
            return Hatch()

    class Boundary:
        ObjectName, Closed = "AcDbPolyline", True

    class Doc:
        ModelSpace = PaperSpace = Space()

        def HandleToObject(self, handle):
            return Boundary()

        def StartUndoMark(self):
            pass

        def EndUndoMark(self):
            pass

    async def run(fn):
        return fn()

    monkeypatch.setattr(draw, "run", run)
    monkeypatch.setattr(draw, "get_doc", lambda: Doc())
    monkeypatch.setattr(draw, "require_idle", lambda d: None)
    monkeypatch.setattr(draw, "apply_properties", lambda *a, **k: {})
    answer = asyncio.run(draw.autocad_add_hatch(boundary_handles=["2A0"], pattern="CHW-INS"))
    assert not answer.startswith("Error"), answer
    assert Space.asked == [1, 2]


def test_a_busy_autocad_is_not_mistaken_for_a_missing_hatch_pattern(monkeypatch):
    """Only a refused name falls back to the custom type; a busy AutoCAD is passed on as busy."""
    import pythoncom

    from autocad_mcp.tools import draw

    class Space:
        asked = []

        def AddHatch(self, pattern_type, name, associative):
            Space.asked.append(pattern_type)
            raise pythoncom.com_error(-2147418111, "Call was rejected by callee.", None, None)

    class Boundary:
        ObjectName, Closed = "AcDbPolyline", True

    class Doc:
        ModelSpace = PaperSpace = Space()

        def HandleToObject(self, handle):
            return Boundary()

        def StartUndoMark(self):
            pass

        def EndUndoMark(self):
            pass

    async def run(fn):
        return fn()

    monkeypatch.setattr(draw, "run", run)
    monkeypatch.setattr(draw, "get_doc", lambda: Doc())
    monkeypatch.setattr(draw, "require_idle", lambda d: None)
    answer = asyncio.run(draw.autocad_add_hatch(boundary_handles=["2A0"], pattern="ANSI31"))
    assert Space.asked == [1]
    assert "no hatch pattern" not in answer.lower()
