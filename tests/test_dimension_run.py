"""Laying a run of dimensions out, and centre marks (no AutoCAD)."""

from __future__ import annotations

import math

import pytest

from autocad_mcp.core.risk import Risk, risk_of
from autocad_mcp.tools.dimensions import (
    MAX_POINTS,
    centre_mark_ops,
    measure,
    order_along,
    plan_run,
)

GRID = [[0, 0], [3000, 0], [7500, 0], [12000, 0]]


class TestOrdering:
    def test_a_horizontal_run_sorts_by_x(self):
        assert order_along([(7500, 0), (0, 0), (3000, 0)], "horizontal") == [
            (0, 0), (3000, 0), (7500, 0)
        ]

    def test_a_vertical_run_sorts_by_y(self):
        assert order_along([(0, 2700), (0, 0), (0, 5400)], "vertical") == [
            (0, 0), (0, 2700), (0, 5400)
        ]

    def test_an_aligned_run_sorts_along_its_own_direction(self):
        pts = [(0, 0), (600, 800), (300, 400)]
        assert order_along(pts, "aligned") == [(0, 0), (300, 400), (600, 800)]

    def test_points_all_at_once_place_keep_their_order(self):
        same = [(5, 5), (5, 5)]
        assert order_along(same, "aligned") == same


class TestMeasure:
    def test_each_axis_measures_what_it_says(self):
        assert measure((0, 0), (300, 400), "horizontal") == 300
        assert measure((0, 0), (300, 400), "vertical") == 400
        assert measure((0, 0), (300, 400), "aligned") == 500


class TestChain:
    def test_a_chain_dimensions_each_gap_in_order(self):
        plan = plan_run(GRID, "chain", "horizontal", 500)
        assert [e["measurement"] for e in plan] == [3000.0, 4500.0, 4500.0]

    def test_a_chain_sits_on_one_dimension_line(self):
        plan = plan_run(GRID, "chain", "horizontal", 500)
        assert {e["row"] for e in plan} == {0}
        assert {e["text_position"][1] for e in plan} == {500.0}

    def test_an_overall_goes_on_a_line_beyond_the_chain(self):
        plan = plan_run(GRID, "chain", "horizontal", 500, include_overall=True)
        overall = plan[-1]
        assert overall["kind"] == "overall"
        assert overall["measurement"] == 12000.0
        assert overall["row"] == 1
        assert overall["text_position"][1] == pytest.approx(1000.0)

    def test_the_chain_adds_up_to_the_overall(self):
        plan = plan_run(GRID, "chain", "horizontal", 500, include_overall=True)
        chain = sum(e["measurement"] for e in plan if e["kind"] == "chain")
        assert chain == pytest.approx(next(e["measurement"] for e in plan if e["kind"] == "overall"))

    def test_jumbled_points_are_put_in_order_first(self):
        jumbled = [[7500, 0], [0, 0], [12000, 0], [3000, 0]]
        assert [e["measurement"] for e in plan_run(jumbled, "chain", "horizontal", 500)] == [
            3000.0, 4500.0, 4500.0
        ]

    def test_sorting_can_be_turned_off(self):
        jumbled = [[7500, 0], [0, 0], [12000, 0]]
        assert [e["measurement"] for e in plan_run(jumbled, "chain", "horizontal", 500, sort=False)] == [
            7500.0, 12000.0
        ]

    def test_points_at_the_same_place_are_skipped_not_zero_dimensioned(self):
        plan = plan_run([[0, 0], [0, 0], [1000, 0]], "chain", "horizontal", 100)
        assert [e["measurement"] for e in plan] == [1000.0]


class TestBaseline:
    def test_every_dimension_runs_back_to_the_first_point(self):
        plan = plan_run(GRID, "baseline", "horizontal", 500)
        assert [e["measurement"] for e in plan] == [3000.0, 7500.0, 12000.0]
        assert all(tuple(e["point1"]) == (0.0, 0.0) for e in plan)

    def test_each_one_steps_clear_of_the_last(self):
        plan = plan_run(GRID, "baseline", "horizontal", 500)
        assert [e["row"] for e in plan] == [0, 1, 2]
        assert [e["text_position"][1] for e in plan] == pytest.approx([500.0, 1000.0, 1500.0])

    def test_spacing_sets_the_step_on_its_own(self):
        plan = plan_run(GRID, "baseline", "horizontal", 500, spacing=200)
        assert [e["text_position"][1] for e in plan] == pytest.approx([500.0, 700.0, 900.0])

    def test_a_negative_offset_steps_the_other_way(self):
        plan = plan_run(GRID, "baseline", "horizontal", -500)
        assert [e["text_position"][1] for e in plan] == pytest.approx([-500.0, -1000.0, -1500.0])


class TestAxes:
    def test_a_vertical_run_offsets_in_x(self):
        plan = plan_run([[0, 0], [0, 2700]], "chain", "vertical", -400)
        assert plan[0]["measurement"] == 2700.0
        assert plan[0]["text_position"][0] == pytest.approx(-400.0)

    def test_an_aligned_run_offsets_perpendicular_to_itself(self):
        plan = plan_run([[0, 0], [3000, 4000]], "overall", "aligned", 500)
        entry = plan[0]
        assert entry["measurement"] == pytest.approx(5000.0)
        assert math.dist(entry["text_position"], (1500, 2000)) == pytest.approx(500.0)

    def test_a_horizontal_dimension_ignores_a_difference_in_y(self):
        plan = plan_run([[0, 0], [3000, 900]], "overall", "horizontal", 500)
        assert plan[0]["measurement"] == 3000.0


class TestOrdinate:
    def test_every_point_gets_its_distance_from_the_datum(self):
        plan = plan_run([[0, 0], [1200, 0], [3600, 0]], "ordinate", "horizontal", 800, datum=[0, 0])
        assert [e["measurement"] for e in plan] == [0.0, 1200.0, 3600.0]

    def test_the_leader_ends_at_the_offset(self):
        plan = plan_run([[1200, 0]], "ordinate", "horizontal", 800)
        assert plan[0]["point2"] == pytest.approx((1200.0, 800.0))

    def test_a_vertical_ordinate_measures_y(self):
        plan = plan_run([[0, 0], [0, 1500]], "ordinate", "vertical", 500, datum=[0, 0])
        assert [e["measurement"] for e in plan] == [0.0, 1500.0]

    def test_the_datum_defaults_to_the_first_point(self):
        plan = plan_run([[1000, 0], [2000, 0]], "ordinate", "horizontal", 500)
        assert [e["measurement"] for e in plan] == [0.0, 1000.0]

    def test_one_point_is_enough_for_an_ordinate(self):
        assert len(plan_run([[5, 5]], "ordinate", "horizontal", 100)) == 1


class TestRefusals:
    def test_a_chain_needs_two_points(self):
        with pytest.raises(ValueError, match="at least two points"):
            plan_run([[0, 0]], "chain", "horizontal", 100)

    def test_an_unknown_mode_or_axis_is_named(self):
        with pytest.raises(ValueError, match="mode must be"):
            plan_run(GRID, "sideways", "horizontal", 100)
        with pytest.raises(ValueError, match="axis must be"):
            plan_run(GRID, "chain", "diagonal", 100)

    def test_a_run_with_no_length_says_so(self):
        with pytest.raises(ValueError, match="no dimension with a length"):
            plan_run([[0, 0], [0, 500]], "chain", "horizontal", 100)

    def test_a_malformed_point_is_named_by_its_index(self):
        with pytest.raises(ValueError, match="point 1"):
            plan_run([[0, 0], [5]], "chain", "horizontal", 100)

    def test_too_many_points_is_refused(self):
        many = [[i * 10, 0] for i in range(MAX_POINTS + 1)]
        with pytest.raises(ValueError, match=str(MAX_POINTS)):
            plan_run(many, "chain", "horizontal", 100)


class TestCentreMarks:
    def test_a_plain_mark_is_a_cross_on_the_centre(self):
        ops = centre_mark_ops([100, 100], 50)
        assert len(ops) == 2
        assert ops[0]["start"] == [95.0, 100.0] and ops[0]["end"] == [105.0, 100.0]
        assert ops[1]["start"] == [100.0, 95.0] and ops[1]["end"] == [100.0, 105.0]

    def test_the_default_size_is_a_tenth_of_the_radius(self):
        ops = centre_mark_ops([0, 0], 200)
        assert ops[0]["end"][0] == pytest.approx(20.0)

    def test_extend_adds_centre_lines_past_the_circle(self):
        ops = centre_mark_ops([0, 0], 50, size=5, extend=10)
        assert len(ops) == 6
        reach = max(abs(c) for op in ops for c in (op["start"][0], op["end"][0]))
        assert reach == pytest.approx(60.0)

    def test_the_layer_and_colour_reach_every_line(self):
        ops = centre_mark_ops([0, 0], 50, extend=5, layer="G-ANNO", color=1)
        assert all(op["layer"] == "G-ANNO" and op["color"] == 1 for op in ops)

    def test_a_zero_radius_is_refused(self):
        with pytest.raises(ValueError, match="above zero"):
            centre_mark_ops([0, 0], 0)

    def test_the_lines_are_ones_the_batch_can_build(self):
        from autocad_mcp.tools.batch import BUILDERS

        for index, op in enumerate(centre_mark_ops([10, 10], 50, extend=5)):
            BUILDERS[op["type"]](op, index)


def test_levels():
    assert risk_of("autocad_dimension_run") is Risk.CHANGE
    assert risk_of("autocad_add_centre_marks") is Risk.CHANGE
