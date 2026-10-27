"""Turning an import into a shop drawing: the layer plan and the tidy plan.

All of it is the planning half, which is pure Python — the writing half needs
AutoCAD and is covered by the live checks.
"""

from __future__ import annotations

import json

import pytest

from autocad_mcp.core.errors import AutocadError
from autocad_mcp.core.risk import Risk, risk_of
from autocad_mcp.tools.convert import (
    IFC_RULES,
    MATCH_KEYS,
    TARGET_KEYS,
    load_rules,
    plan_remap,
    plan_tidy,
    rule_hits,
    validate_rules,
)

# What an IFC export actually looks like when it lands: some of it layered by
# class, some of it on layer 0 with the class in the block name.
IMPORT = [
    {"handle": "1A", "type": "polyline", "layer": "IfcWallStandardCase", "color": 7, "linetype": "Continuous"},
    {"handle": "1B", "type": "block", "layer": "0", "color": 7, "linetype": "Continuous", "block_name": "IfcDuctSegment_1442"},
    {"handle": "1C", "type": "block", "layer": "0", "color": 7, "linetype": "Continuous", "block_name": "IfcCableCarrierSegment_9"},
    {"handle": "1D", "type": "text", "layer": "0", "color": 3, "linetype": "Continuous", "text": "ROOM 1"},
    {"handle": "1E", "type": "line", "layer": "Mystery", "color": 7, "linetype": "Continuous"},
    {"handle": "1F", "type": "polyline", "layer": "A-WALL", "color": 256, "linetype": "ByLayer"},
]


class TestRuleHits:
    def test_name_like_matches_the_layer_or_the_block_name(self):
        rule = {"name_like": "*duct*", "layer": "M-HVAC-DUCT"}
        assert rule_hits({"layer": "IfcDuctSegment", "type": "polyline"}, rule)
        assert rule_hits({"layer": "0", "type": "block", "block_name": "IfcDuctSegment_1"}, rule)
        assert not rule_hits({"layer": "A-WALL", "type": "line"}, rule)

    def test_wildcards_and_regex_both_work(self):
        assert rule_hits({"layer": "E-POWR-PANL"}, {"source_layer": "E-*", "layer": "X"})
        assert rule_hits({"layer": "E-POWR-PANL"}, {"source_layer": "/^E-\\w+-PANL$/", "layer": "X"})
        assert not rule_hits({"layer": "M-DUCT"}, {"source_layer": "/^E-/", "layer": "X"})

    def test_matching_is_case_insensitive(self):
        assert rule_hits({"layer": "ifcwall"}, {"name_like": "*WALL*", "layer": "X"})

    def test_criteria_are_all_required(self):
        rule = {"source_layer": "0", "entity_type": "text", "layer": "G-ANNO-TEXT"}
        assert rule_hits({"layer": "0", "type": "text"}, rule)
        assert not rule_hits({"layer": "0", "type": "line"}, rule)
        assert not rule_hits({"layer": "A-WALL", "type": "text"}, rule)

    def test_source_color_matches_the_object_s_own_colour(self):
        rule = {"source_color": 3, "layer": "X"}
        assert rule_hits({"layer": "0", "color": 3}, rule)
        assert not rule_hits({"layer": "0", "color": 7}, rule)

    def test_color_is_the_target_layer_s_colour_not_a_filter(self):
        # The bug this guards: a rule painting A-WALL grey must not match only
        # objects that are already grey.
        rule = {"name_like": "*wall*", "layer": "A-WALL", "color": 8}
        assert rule_hits({"layer": "IfcWall", "color": 7}, rule)

    def test_text_contains_looks_inside_the_text(self):
        rule = {"text_contains": "room", "layer": "A-AREA-IDEN"}
        assert rule_hits({"layer": "0", "type": "text", "text": "ROOM 1"}, rule)
        assert not rule_hits({"layer": "0", "type": "text", "text": "LEVEL 2"}, rule)


class TestValidateRules:
    def test_a_rule_with_no_target_layer_is_refused(self):
        with pytest.raises(ValueError, match="no target 'layer'"):
            validate_rules([{"name_like": "*wall*"}])

    def test_a_rule_that_matches_everything_is_refused(self):
        with pytest.raises(ValueError) as exc:
            validate_rules([{"layer": "EVERYTHING"}])
        assert "whole drawing" in str(exc.value)
        assert "source_color" in str(exc.value)

    def test_an_unknown_key_is_named(self):
        with pytest.raises(ValueError, match="colour"):
            validate_rules([{"name_like": "*x*", "layer": "X", "colour": 1}])

    def test_an_empty_rule_list_is_refused(self):
        with pytest.raises(ValueError, match="no rules"):
            validate_rules([])

    def test_a_rule_that_is_not_an_object_is_refused(self):
        with pytest.raises(ValueError, match="must be an object"):
            validate_rules(["*wall* -> A-WALL"])

    def test_match_and_target_keys_do_not_overlap(self):
        assert not MATCH_KEYS & TARGET_KEYS


class TestPlanRemap:
    def test_the_preset_sorts_a_real_import(self):
        report = plan_remap(IMPORT, list(IFC_RULES), unmatched_layer="X-REVIEW")
        moves = {m["handle"]: m["to"] for m in report["moves"]}
        assert moves["1A"] == "A-WALL"
        assert moves["1B"] == "M-HVAC-DUCT"
        assert moves["1C"] == "E-CABL-TRAY"
        assert moves["1D"] == "G-ANNO-TEXT"
        assert moves["1E"] == "X-REVIEW"
        # already on the right layer: matched, but nothing to move
        assert "1F" not in moves
        assert report["counts"] == {
            "read": 6, "to_move": 5, "already_right": 1, "unmatched": 1, "layers_wanted": 5
        }

    def test_cable_carrier_wins_over_cable_because_it_is_listed_first(self):
        report = plan_remap(
            [{"handle": "1", "type": "block", "layer": "0", "color": 7, "block_name": "IfcCableCarrierSegment"}],
            list(IFC_RULES),
        )
        assert report["moves"][0]["to"] == "E-CABL-TRAY"

    def test_the_first_matching_rule_wins(self):
        rules = [
            {"name_like": "*wall*", "layer": "FIRST"},
            {"name_like": "*wall*", "layer": "SECOND"},
        ]
        report = plan_remap([{"handle": "1", "type": "line", "layer": "IfcWall", "color": 7}], rules)
        assert report["moves"][0]["to"] == "FIRST"

    def test_target_layer_properties_are_collected(self):
        report = plan_remap(IMPORT, list(IFC_RULES))
        assert report["layers"]["A-WALL"] == {"color": 8}
        assert report["layers"]["M-HVAC-DUCT"] == {"color": 4}

    def test_unmatched_objects_stay_put_without_an_unmatched_layer(self):
        report = plan_remap(IMPORT, list(IFC_RULES))
        assert "1E" not in {m["handle"] for m in report["moves"]}
        assert "1E" in report["unmatched"]

    def test_by_rule_counts_what_each_rule_caught(self):
        report = plan_remap(IMPORT, list(IFC_RULES), unmatched_layer="X-REVIEW")
        assert report["by_rule"]["*wall* -> A-WALL"] == 2
        assert report["by_rule"]["unmatched -> X-REVIEW"] == 1

    def test_nothing_is_planned_for_an_empty_drawing(self):
        report = plan_remap([], list(IFC_RULES))
        assert report["moves"] == [] and report["counts"]["read"] == 0

    def test_new_color_is_carried_to_the_move(self):
        rules = [{"name_like": "*wall*", "layer": "A-WALL", "new_color": 1}]
        report = plan_remap([{"handle": "1", "type": "line", "layer": "IfcWall", "color": 7}], rules)
        assert report["moves"][0]["new_color"] == 1


class TestIfcPreset:
    def test_every_preset_rule_is_valid(self):
        validate_rules(list(IFC_RULES))

    def test_every_preset_rule_names_a_discipline_layer(self):
        for rule in IFC_RULES:
            layer = rule["layer"]
            assert layer[:2] in ("A-", "S-", "M-", "P-", "E-", "F-", "C-", "G-"), layer

    def test_the_preset_is_offered_by_name(self):
        assert load_rules(None, None, "ifc") == [dict(r) for r in IFC_RULES]

    def test_an_unknown_preset_lists_the_real_ones(self):
        with pytest.raises(AutocadError, match="ifc"):
            load_rules(None, None, "revit")


class TestLoadRules:
    def test_inline_rules_win(self):
        rules = [{"name_like": "*x*", "layer": "X"}]
        assert load_rules(rules, None, "ifc") == rules

    def test_a_json_file_of_rules(self, tmp_path):
        path = tmp_path / "office.json"
        path.write_text(json.dumps([{"name_like": "*duct*", "layer": "M-DUCT"}]), encoding="utf-8")
        assert load_rules(None, str(path), None)[0]["layer"] == "M-DUCT"

    def test_a_json_object_with_a_rules_key(self, tmp_path):
        path = tmp_path / "office.json"
        path.write_text(json.dumps({"rules": [{"name_like": "*p*", "layer": "P-PIPE"}]}), encoding="utf-8")
        assert load_rules(None, str(path), None)[0]["layer"] == "P-PIPE"

    def test_a_missing_file_says_so(self, tmp_path):
        with pytest.raises(AutocadError, match="Could not read"):
            load_rules(None, str(tmp_path / "nope.json"), None)

    def test_a_file_that_is_not_a_rule_list_says_so(self, tmp_path):
        path = tmp_path / "wrong.json"
        path.write_text('"just a string"', encoding="utf-8")
        with pytest.raises(AutocadError, match="list of rules"):
            load_rules(None, str(path), None)

    def test_nothing_given_asks_for_something(self):
        with pytest.raises(AutocadError, match="preset='ifc'"):
            load_rules(None, None, None)


class TestPlanTidy:
    OBJECTS = [
        {"handle": "2A", "type": "line", "layer": "0", "color": 1, "linetype": "HIDDEN",
         "lineweight": 25, "thickness": 50.0, "elevation": 3200.0, "empty": False},
        {"handle": "2B", "type": "line", "layer": "A-WALL", "color": 256, "linetype": "ByLayer",
         "lineweight": -1, "thickness": 0.0, "elevation": 0.0, "empty": True},
    ]

    def test_only_what_is_actually_wrong_is_planned(self):
        report = plan_tidy(
            self.OBJECTS,
            {"color_bylayer": True, "linetype_bylayer": True, "lineweight_bylayer": True},
        )
        # 2B is already ByLayer throughout, so only 2A needs anything.
        assert report["counts"] == {"color_bylayer": 1, "linetype_bylayer": 1, "lineweight_bylayer": 1}
        assert {j["handle"] for j in report["jobs"]} == {"2A"}

    def test_flatten_only_touches_what_is_off_the_level(self):
        report = plan_tidy(self.OBJECTS, {"flatten_z": 0.0})
        assert report["counts"] == {"flatten_z": 1}
        assert report["jobs"][0]["detail"] == 3200.0

    def test_flatten_to_a_level_other_than_zero(self):
        report = plan_tidy(self.OBJECTS, {"flatten_z": 3200.0})
        assert report["counts"] == {"flatten_z": 1}
        assert report["jobs"][0]["handle"] == "2B"

    def test_layer_zero_geometry_is_moved_off(self):
        report = plan_tidy(self.OBJECTS, {"off_layer_0": "X-REVIEW"})
        assert report["jobs"] == [{"handle": "2A", "do": "off_layer_0", "detail": "X-REVIEW"}]

    def test_empty_objects_are_only_planned_when_asked_for(self):
        assert plan_tidy(self.OBJECTS, {})["counts"] == {}
        assert plan_tidy(self.OBJECTS, {"delete_empty": True})["counts"] == {"delete_empty": 1}

    def test_thickness_is_only_planned_when_it_is_not_zero(self):
        report = plan_tidy(self.OBJECTS, {"zero_thickness": True})
        assert report["counts"] == {"zero_thickness": 1}
        assert report["jobs"][0]["handle"] == "2A"

    def test_nothing_asked_for_is_nothing_planned(self):
        assert plan_tidy(self.OBJECTS, {})["jobs"] == []


def test_levels():
    assert risk_of("autocad_remap_layers") is Risk.CHANGE
    assert risk_of("autocad_tidy_entities") is Risk.CHANGE
