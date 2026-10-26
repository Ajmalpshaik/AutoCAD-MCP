"""Standards check, attribute extraction, resources and prompts (no AutoCAD)."""

from __future__ import annotations

import asyncio
import json

from autocad_mcp.core.registry import mcp
from autocad_mcp.tools import register_all
from autocad_mcp.tools.standards import check, rows_to_csv

register_all()

LAYERS = [
    {"name": "0", "color": 7, "linetype": "Continuous"},
    {"name": "Defpoints", "color": 7, "linetype": "Continuous"},
    {"name": "A-WALL", "color": 1, "linetype": "Continuous"},
    {"name": "walls new", "color": 3, "linetype": "Continuous"},
    {"name": "M-DUCT", "color": 5, "linetype": "HIDDEN"},
]

ENTITIES = [
    {"handle": "1A", "type": "AcDbLine", "layer": "A-WALL", "color": 256, "linetype": "ByLayer"},
    {"handle": "1B", "type": "AcDbLine", "layer": "0", "color": 256, "linetype": "ByLayer"},
    {"handle": "1C", "type": "AcDbCircle", "layer": "M-DUCT", "color": 1, "linetype": "ByLayer"},
    {"handle": "1D", "type": "AcDbLine", "layer": "M-DUCT", "color": 256, "linetype": "DASHED"},
]


def _rules(findings):
    return sorted({f["rule"] for f in findings})


def test_layer_name_pattern_skips_0_and_defpoints():
    report = check(LAYERS, [], {"layer_name_pattern": r"^[A-Z]-[A-Z0-9-]+$"})
    names = [f["layer"] for f in report["findings"]]
    assert names == ["walls new"]


def test_required_layer_properties():
    rules = {"layers": {"A-WALL": {"color": 2}, "M-DUCT": {"linetype": "Continuous"}, "E-POWR": {"color": 1}}}
    report = check(LAYERS, [], rules)
    details = {(f["layer"], f["rule"]) for f in report["findings"]}
    assert ("A-WALL", "layer_color") in details
    assert ("M-DUCT", "layer_linetype") in details
    assert ("E-POWR", "layer_missing") in details


def test_entities_on_layer_0():
    report = check(LAYERS, ENTITIES, {"forbid_entities_on_layer_0": True})
    assert [f["handle"] for f in report["findings"]] == ["1B"]


def test_bylayer_colour_and_linetype():
    report = check(LAYERS, ENTITIES, {"require_bylayer_color": True, "require_bylayer_linetype": True})
    assert {(f["handle"], f["rule"]) for f in report["findings"]} == {
        ("1C", "bylayer_color"),
        ("1D", "bylayer_linetype"),
    }


def test_summary_counts_and_limit():
    report = check(LAYERS, ENTITIES, {"require_bylayer_color": True, "forbid_entities_on_layer_0": True, "max_findings": 1})
    assert report["summary"] == {"bylayer_color": 1, "entity_on_layer_0": 1}
    assert len(report["findings"]) == 1
    assert report["truncated"] is True
    assert report["checked"] == {"layers": 5, "entities": 4}


def test_unknown_rule_is_named():
    report = check(LAYERS, [], {"colour_of_my_dreams": True})
    assert report["unknown_rules"] == ["colour_of_my_dreams"]


def test_csv_header_order_and_values():
    rows = [
        {"block": "CAM", "handle": "2A", "layer": "E-CCTV", "insertion": [1.0, 2.0, 0.0], "attributes": {"TAG": "C01", "TYPE": "DOME"}},
        {"block": "CAM", "handle": "2B", "layer": "E-CCTV", "insertion": [3.5, 4.0, 0.0], "attributes": {"TAG": "C02", "IP": "10.0.0.2"}},
    ]
    lines = rows_to_csv(rows).splitlines()
    assert lines[0] == "block,handle,layer,x,y,z,IP,TAG,TYPE"
    assert lines[1] == "CAM,2A,E-CCTV,1.0,2.0,0.0,,C01,DOME"
    assert lines[2] == "CAM,2B,E-CCTV,3.5,4.0,0.0,10.0.0.2,C02,"


def test_new_tools_are_read_level():
    from autocad_mcp.core.risk import Risk, risk_of

    assert risk_of("autocad_check_standards") is Risk.READ
    assert risk_of("autocad_extract_attributes") is Risk.READ


def test_resources_and_prompts_are_registered():
    uris = {str(r.uri) for r in asyncio.run(mcp.list_resources())}
    assert {
        "autocad://drawing/layers",
        "autocad://drawing/blocks",
        "autocad://drawing/styles",
        "autocad://drawing/status",
    } <= uris
    prompts = {p.name for p in asyncio.run(mcp.list_prompts())}
    assert {"check_standards", "draw_from_spec"} <= prompts


def test_resource_goes_through_the_gated_tool(monkeypatch):
    from autocad_mcp.tools import layers, resources

    called = []

    async def fake_list_layers(include_entity_counts=False):
        called.append(include_entity_counts)
        return json.dumps([{"name": "0"}])

    monkeypatch.setattr(layers, "autocad_list_layers", fake_list_layers)
    assert json.loads(asyncio.run(resources.drawing_layers())) == [{"name": "0"}]
    assert called == [False]
