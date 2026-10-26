"""Take-off tools: block counts, total lengths and areas, dynamic block properties.

Ideas from Lee Mac's Block Counter, Total Length & Area and Dynamic Block
Functions (lee-mac.com), written fresh for Heron: no Lee Mac code is used.
"""

from __future__ import annotations

import asyncio
import json

import pytest

from autocad_mcp.tools import takeoff
from autocad_mcp.tools.takeoff import coerce_value, count_blocks, total_lengths

REFS = [
    {"block": "VALVE", "layer": "P-CHW", "visibility": "GATE", "properties": {"Size": 50.0}},
    {"block": "VALVE", "layer": "P-CHW", "visibility": "GATE", "properties": {"Size": 80.0}},
    {"block": "VALVE", "layer": "P-HW", "visibility": "BALL", "properties": {"Size": 50.0}},
    {"block": "ELBOW 90", "layer": "P-CHW", "visibility": None, "properties": {}},
]


def test_counts_by_name_with_total_sorted_by_name():
    report = count_blocks(REFS, "name")
    assert report["rows"] == [{"block": "ELBOW 90", "count": 1}, {"block": "VALVE", "count": 3}]
    assert report["total"] == 4


def test_counts_by_name_and_layer():
    rows = count_blocks(REFS, "name_layer")["rows"]
    assert {"block": "VALVE", "layer": "P-CHW", "count": 2} in rows
    assert {"block": "VALVE", "layer": "P-HW", "count": 1} in rows


def test_counts_by_visibility_state():
    rows = count_blocks(REFS, "name_visibility")["rows"]
    assert {"block": "VALVE", "visibility": "GATE", "count": 2} in rows
    assert {"block": "ELBOW 90", "visibility": None, "count": 1} in rows


def test_counts_by_dynamic_property_values():
    rows = count_blocks(REFS, "name_properties")["rows"]
    assert {"block": "VALVE", "properties": {"Size": 50.0}, "count": 2} in rows
    assert {"block": "VALVE", "properties": {"Size": 80.0}, "count": 1} in rows


ITEMS = [
    {"type": "AcDbLine", "layer": "P-CHW", "length": 1000.0, "area": None},
    {"type": "AcDbPolyline", "layer": "P-CHW", "length": 2500.5, "area": 0.0},
    {"type": "AcDbPolyline", "layer": "A-ROOM", "length": 4000.0, "area": 1000000.0},
    {"type": "AcDbSpline", "layer": "P-CHW", "length": None, "area": None},
]


def test_total_length_by_layer_counts_what_cannot_be_measured():
    report = total_lengths(ITEMS, "layer")
    rows = {row["layer"]: row for row in report["rows"]}
    assert rows["P-CHW"]["length"] == pytest.approx(3500.5)
    assert rows["P-CHW"]["count"] == 3 and rows["P-CHW"]["unmeasured"] == 1
    assert rows["A-ROOM"]["area"] == pytest.approx(1000000.0)
    assert report["total_length"] == pytest.approx(7500.5)


def test_total_length_as_one_group():
    report = total_lengths(ITEMS, "none")
    assert len(report["rows"]) == 1 and report["rows"][0]["count"] == 4


def test_coerce_follows_the_current_value_type():
    assert coerce_value(50.0, "80") == 80.0 and isinstance(coerce_value(50.0, "80"), float)
    assert coerce_value(1, 0) == 0 and isinstance(coerce_value(1, "0"), int)
    assert coerce_value("GATE", "BALL") == "BALL"


def test_coerce_refuses_a_value_not_in_the_allowed_list():
    with pytest.raises(ValueError, match="allowed"):
        coerce_value("GATE", "PLUG", allowed=["GATE", "BALL"])
    assert coerce_value(50.0, 80, allowed=[50.0, 80.0]) == 80.0


class Prop:
    def __init__(self, name, value, allowed=(), read_only=False):
        self.PropertyName, self.Value, self.AllowedValues, self.ReadOnly = name, value, allowed, read_only
        self.Description, self.UnitsType, self.Show = "", 0, True


class Ref:
    def __init__(self, props):
        self.Handle, self.EffectiveName, self.IsDynamicBlock = "2A", "VALVE", True
        self.ObjectName, self.props = "AcDbBlockReference", props

    def GetDynamicBlockProperties(self):
        return self.props


class Doc:
    def __init__(self, ref):
        self.ref = ref

    def HandleToObject(self, handle):
        return self.ref

    def GetVariable(self, name):
        return 0

    def StartUndoMark(self):
        pass

    def EndUndoMark(self):
        pass


@pytest.fixture
def valve(monkeypatch):
    ref = Ref([Prop("Visibility1", "GATE", ("GATE", "BALL")), Prop("Size", 50.0, (50.0, 80.0)), Prop("Origin", (0, 0), read_only=True)])
    doc = Doc(ref)

    async def run(fn):
        return fn()

    monkeypatch.setattr(takeoff, "run", run)
    monkeypatch.setattr(takeoff, "get_doc", lambda: doc)
    monkeypatch.setattr(takeoff, "require_idle", lambda d: None)
    return ref


def test_get_dynamic_properties_lists_values_and_choices(valve):
    result = json.loads(asyncio.run(takeoff.autocad_get_dynamic_properties(handle="2A")))
    props = {p["name"]: p for p in result["properties"]}
    assert result["block"] == "VALVE"
    assert props["Size"]["value"] == 50.0 and props["Size"]["allowed"] == [50.0, 80.0]
    assert props["Visibility1"]["allowed"] == ["GATE", "BALL"]
    assert props["Origin"]["read_only"] is True


def test_set_dynamic_properties_changes_values_and_reports_failures(valve):
    result = json.loads(asyncio.run(takeoff.autocad_set_dynamic_properties(
        handle="2A", values={"Size": "80", "visibility1": "BALL", "Origin": [1, 1], "Nope": 1},
    )))
    props = {p.PropertyName: p for p in valve.props}
    assert props["Size"].Value == 80.0 and props["Visibility1"].Value == "BALL"
    assert set(result["changed"]) == {"Size", "Visibility1"}
    assert set(result["failed"]) == {"Origin", "Nope"}


def test_levels():
    from autocad_mcp.core.risk import Risk, risk_of

    assert risk_of("autocad_count_blocks") is Risk.READ
    assert risk_of("autocad_total_length") is Risk.READ
    assert risk_of("autocad_get_dynamic_properties") is Risk.READ
    assert risk_of("autocad_set_dynamic_properties") is Risk.CHANGE
