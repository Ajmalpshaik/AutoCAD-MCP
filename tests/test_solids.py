"""3D: the helix, the lookup tables, and the levels (no AutoCAD).

The solid calls themselves are COM and are covered by the live checks. What is
checked here is everything that can be got wrong without AutoCAD noticing: the
boolean operation codes, the view directions, and the helix arithmetic.
"""

from __future__ import annotations

import math

import pytest

from autocad_mcp.core.risk import Risk, risk_of
from autocad_mcp.tools.solids import (
    BOOLEAN_OPS,
    VIEW_DIRECTIONS,
    VISUAL_STYLES,
    helix_points,
)


class TestHelix:
    def test_it_starts_on_its_radius_at_its_base(self):
        pts = helix_points(100, 3, 600)
        assert pts[0] == pytest.approx([100.0, 0.0, 0.0])

    def test_a_whole_number_of_turns_comes_back_round(self):
        pts = helix_points(100, 3, 600)
        assert pts[-1][0] == pytest.approx(100.0)
        assert pts[-1][1] == pytest.approx(0.0, abs=1e-6)

    def test_it_rises_to_the_height_asked_for(self):
        pts = helix_points(100, 3, 600)
        assert pts[-1][2] == pytest.approx(600.0)

    def test_the_rise_is_even(self):
        pts = helix_points(100, 2, 400)
        assert pts[len(pts) // 2][2] == pytest.approx(200.0)

    def test_every_point_sits_on_the_radius(self):
        for p in helix_points(250, 2, 500):
            assert math.hypot(p[0], p[1]) == pytest.approx(250.0)

    def test_a_top_radius_makes_a_conical_coil(self):
        pts = helix_points(100, 2, 400, top_radius=50)
        assert math.hypot(pts[0][0], pts[0][1]) == pytest.approx(100.0)
        assert math.hypot(pts[-1][0], pts[-1][1]) == pytest.approx(50.0)

    def test_a_negative_height_winds_downward(self):
        assert helix_points(100, 1, -300)[-1][2] == pytest.approx(-300.0)

    def test_the_centre_moves_the_whole_helix(self):
        pts = helix_points(100, 1, 300, centre=(1000.0, 500.0, 250.0))
        assert pts[0] == pytest.approx([1100.0, 500.0, 250.0])
        assert pts[-1][2] == pytest.approx(550.0)

    def test_more_points_per_turn_gives_more_points(self):
        assert len(helix_points(100, 2, 400, per_turn=12)) < len(
            helix_points(100, 2, 400, per_turn=72)
        )

    def test_a_fraction_of_a_turn_works(self):
        pts = helix_points(100, 0.5, 100)
        assert pts[-1][0] == pytest.approx(-100.0)
        assert pts[-1][2] == pytest.approx(100.0)

    @pytest.mark.parametrize(
        ("radius", "turns", "top", "match"),
        [
            (0, 2, None, "radius above zero"),
            (-5, 2, None, "radius above zero"),
            (100, 0, None, "more than zero turns"),
            (100, -1, None, "more than zero turns"),
            (100, 2, 0, "top_radius must be above zero"),
        ],
    )
    def test_refusals(self, radius, turns, top, match):
        with pytest.raises(ValueError, match=match):
            helix_points(radius, turns, 100, top)


class TestBooleanCodes:
    def test_the_three_operations_have_the_values_autocad_expects(self):
        # acUnion = 0, acIntersection = 1, acSubtraction = 2. Getting these
        # wrong would quietly do the wrong boolean, so they are pinned here.
        assert BOOLEAN_OPS == {"union": 0, "intersect": 1, "subtract": 2}

    def test_the_names_are_the_ones_the_tool_offers(self):
        assert set(BOOLEAN_OPS) == {"union", "intersect", "subtract"}


class TestViewDirections:
    def test_plan_is_the_same_as_top(self):
        assert VIEW_DIRECTIONS["plan"] == VIEW_DIRECTIONS["top"] == (0.0, 0.0, 1.0)

    @pytest.mark.parametrize("name", sorted(VIEW_DIRECTIONS))
    def test_every_direction_is_a_real_unit_of_direction(self, name):
        vector = VIEW_DIRECTIONS[name]
        assert len(vector) == 3
        assert any(abs(v) > 0 for v in vector), name

    def test_the_four_isometrics_each_look_down_from_their_own_corner(self):
        assert VIEW_DIRECTIONS["sw_iso"] == (-1.0, -1.0, 1.0)
        assert VIEW_DIRECTIONS["se_iso"] == (1.0, -1.0, 1.0)
        assert VIEW_DIRECTIONS["ne_iso"] == (1.0, 1.0, 1.0)
        assert VIEW_DIRECTIONS["nw_iso"] == (-1.0, 1.0, 1.0)

    def test_opposite_views_are_opposite(self):
        for a, b in (("top", "bottom"), ("front", "back"), ("left", "right")):
            assert VIEW_DIRECTIONS[a] == tuple(-v for v in VIEW_DIRECTIONS[b])


class TestVisualStyles:
    def test_the_two_a_drawing_actually_uses_are_there(self):
        assert "hidden" in VISUAL_STYLES      # what a shop drawing wants
        assert "2dwireframe" in VISUAL_STYLES  # back to normal drafting

    def test_every_name_is_lower_case_so_the_check_is_case_insensitive(self):
        assert all(name == name.lower() for name in VISUAL_STYLES)


def test_levels():
    assert risk_of("autocad_add_solid") is Risk.CHANGE
    assert risk_of("autocad_extrude_profile") is Risk.CHANGE
    assert risk_of("autocad_solid_boolean") is Risk.CHANGE
    assert risk_of("autocad_draw_3d_path") is Risk.CHANGE
    assert risk_of("autocad_solid_properties") is Risk.READ
    # Only changes what is on screen, like autocad_zoom.
    assert risk_of("autocad_set_3d_view") is Risk.VIEW
