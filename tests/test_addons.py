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
