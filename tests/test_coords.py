"""The UCS transform, and the batch that converts through it (no AutoCAD)."""

from __future__ import annotations

import math

import pytest

from autocad_mcp.acad.coords import (
    WORLD,
    Ucs,
    advice,
    as_vec3,
    box_of,
    corners_box,
    rotate_about,
    rotated_box,
    transform_points,
)
from autocad_mcp.core.risk import Risk, risk_of
from autocad_mcp.tools.batch import to_world_ops


class TestAsVec3:
    def test_pads_short_input_with_zeros(self):
        assert as_vec3([1, 2]) == (1.0, 2.0, 0.0)
        assert as_vec3([1, 2, 3, 4]) == (1.0, 2.0, 3.0)

    def test_unreadable_input_falls_back(self):
        assert as_vec3(None) == (0.0, 0.0, 0.0)
        assert as_vec3("nonsense", (9.0, 9.0, 9.0)) == (9.0, 9.0, 9.0)
        assert as_vec3([]) == (0.0, 0.0, 0.0)


class TestWorldUcs:
    def test_the_world_ucs_is_the_world(self):
        assert WORLD.is_world
        assert not WORLD.moved and not WORLD.rotated and not WORLD.tilted
        assert WORLD.rotation_degrees == 0.0
        assert advice(WORLD) is None

    def test_a_world_point_passes_straight_through(self):
        assert WORLD.to_world((10, 20, 30)) == (10.0, 20.0, 30.0)
        assert WORLD.to_ucs((10, 20, 30)) == (10.0, 20.0, 30.0)


class TestRotatedUcs:
    def test_rotation_is_reported_in_degrees(self):
        assert Ucs.from_rotation(degrees=30).rotation_degrees == pytest.approx(30.0)
        assert Ucs.from_rotation(degrees=-90).rotation_degrees == pytest.approx(270.0)

    def test_a_point_lands_where_a_drafter_expects(self):
        # 100 along the UCS X of a UCS turned 90 degrees is 100 up world Y.
        ucs = Ucs.from_rotation(degrees=90)
        x, y, z = ucs.to_world((100, 0))
        assert (round(x, 9), round(y, 9), round(z, 9)) == (0.0, 100.0, 0.0)

    def test_the_origin_moves_the_point_too(self):
        ucs = Ucs.from_rotation((1000, 500), 0)
        assert ucs.to_world((100, 0)) == (1100.0, 500.0, 0.0)

    @pytest.mark.parametrize("angle", [0, 23, 90, 180, 271.5, 359.9])
    @pytest.mark.parametrize("origin", [(0, 0, 0), (1000, -500, 250)])
    def test_round_trip_is_exact(self, angle, origin):
        ucs = Ucs.from_rotation(origin, angle)
        point = (1234.5, -678.9, 42.0)
        back = ucs.to_ucs(ucs.to_world(point))
        assert back == pytest.approx(point, abs=1e-9)

    def test_moved_and_rotated_are_reported_apart(self):
        moved = Ucs.from_rotation((10, 0), 0)
        assert moved.moved and not moved.rotated and not moved.is_world
        turned = Ucs.from_rotation((0, 0), 45)
        assert turned.rotated and not turned.moved and not turned.is_world

    def test_a_direction_ignores_the_origin(self):
        ucs = Ucs.from_rotation((1000, 500), 90)
        x, y, _ = ucs.direction_to_world((1, 0))
        assert (round(x, 9), round(y, 9)) == (0.0, 1.0)


class TestTiltedUcs:
    def test_a_tilted_ucs_says_so(self):
        # X stays world X, Y goes up: the UCS plane is vertical.
        ucs = Ucs.build((0, 0, 0), (1, 0, 0), (0, 0, 1))
        assert ucs.tilted and ucs.rotated and not ucs.is_world
        assert ucs.z_axis == pytest.approx((0.0, -1.0, 0.0))

    def test_a_flipped_ucs_says_so(self):
        ucs = Ucs.build((0, 0, 0), (1, 0, 0), (0, -1, 0))
        assert ucs.flipped and not ucs.tilted

    def test_advice_names_every_way_it_differs(self):
        note = advice(Ucs.build((5, 5, 5), (1, 0, 0), (0, 0, 1)))
        assert note is not None
        assert "moved off the world origin" in note
        assert "tilted" in note
        assert "autocad_convert_points" in note


class TestBuild:
    def test_axes_are_squared_up_and_normalized(self):
        # Y a long way out of square: the frame still comes back orthonormal.
        ucs = Ucs.build((0, 0, 0), (2, 0, 0), (3, 4, 0))
        assert math.hypot(*ucs.x_axis[:2]) == pytest.approx(1.0)
        assert ucs.x_axis[0] * ucs.y_axis[0] + ucs.x_axis[1] * ucs.y_axis[1] == pytest.approx(0.0)

    def test_parallel_axes_are_refused(self):
        with pytest.raises(ValueError, match="parallel"):
            Ucs.build((0, 0, 0), (1, 0, 0), (2, 0, 0))

    def test_a_zero_length_axis_is_refused(self):
        with pytest.raises(ValueError, match="zero length"):
            Ucs.build((0, 0, 0), (0, 0, 0), (0, 1, 0))

    def test_three_points_build_the_ucs_command_s_frame(self):
        ucs = Ucs.from_three_points((100, 100), (200, 100), (100, 200))
        assert ucs.origin == (100.0, 100.0, 0.0)
        assert ucs.rotation_degrees == 0.0

    def test_three_points_in_a_line_are_refused(self):
        with pytest.raises(ValueError):
            Ucs.from_three_points((0, 0), (1, 0), (2, 0))


class TestHelpers:
    def test_transform_points_both_ways(self):
        ucs = Ucs.from_rotation((0, 0), 90)
        assert transform_points([(1, 0)], ucs, "world")[0] == pytest.approx((0.0, 1.0, 0.0))
        assert transform_points([(0, 1)], ucs, "ucs")[0] == pytest.approx((1.0, 0.0, 0.0))
        with pytest.raises(ValueError):
            transform_points([(0, 0)], ucs, "sideways")

    def test_corners_box_accepts_either_order(self):
        assert corners_box((10, 10), (0, 0)) == (0.0, 0.0, 10.0, 10.0)
        assert corners_box((0, 10), (10, 0)) == (0.0, 0.0, 10.0, 10.0)

    def test_box_of_points(self):
        assert box_of([(0, 0), (5, -2), (3, 9)]) == (0.0, -2.0, 5.0, 9.0)
        with pytest.raises(ValueError):
            box_of([])

    def test_rotate_about_keeps_the_centre_still(self):
        assert rotate_about((10, 0), (0, 0), 90) == pytest.approx((0.0, 10.0, 0.0))
        assert rotate_about((5, 5), (5, 5), 37) == pytest.approx((5.0, 5.0, 0.0))

    def test_rotated_box_grows_to_hold_the_turned_one(self):
        # A 100 x 100 square turned 45 degrees needs 100 * sqrt(2) each way.
        x1, y1, x2, y2 = rotated_box((0, 0, 100, 100), 45)
        assert x2 - x1 == pytest.approx(100 * math.sqrt(2))
        assert y2 - y1 == pytest.approx(100 * math.sqrt(2))

    def test_rotated_box_at_90_is_the_same_box(self):
        assert rotated_box((0, 0, 100, 50), 90) == pytest.approx((25.0, -25.0, 75.0, 75.0))


class TestBatchConversion:
    """autocad_batch_draw with coords='ucs': entmake only writes world coordinates."""

    def test_the_world_path_changes_nothing(self):
        ops = [{"type": "line", "start": [0, 0], "end": [100, 0]}]
        assert to_world_ops(ops, None) == ops

    def test_points_are_converted(self):
        ucs = Ucs.from_rotation((0, 0), 90)
        moved = to_world_ops([{"type": "line", "start": [0, 0], "end": [100, 0]}], ucs)[0]
        assert moved["end"] == pytest.approx([0.0, 100.0, 0.0])

    def test_angles_pick_up_the_ucs_rotation(self):
        ucs = Ucs.from_rotation((0, 0), 30)
        ops = [
            {"type": "arc", "center": [0, 0], "radius": 5, "start_angle": 0, "end_angle": 90},
            {"type": "text", "position": [0, 0], "text": "A", "rotation": 350},
        ]
        arc, text = to_world_ops(ops, ucs)
        assert (arc["start_angle"], arc["end_angle"]) == (30.0, 120.0)
        assert text["rotation"] == pytest.approx(20.0)

    def test_a_rectangle_becomes_the_turned_polyline_it_means(self):
        ucs = Ucs.from_rotation((0, 0), 90)
        moved = to_world_ops([{"type": "rectangle", "corner1": [0, 0], "corner2": [100, 50], "layer": "A"}], ucs)[0]
        assert moved["type"] == "polyline"
        assert moved["closed"] is True
        assert moved["layer"] == "A"
        assert "corner1" not in moved and "corner2" not in moved
        assert len(moved["points"]) == 4
        assert moved["points"][1] == pytest.approx([0.0, 100.0, 0.0])

    def test_a_degenerate_rectangle_is_left_for_the_builder_to_report(self):
        ucs = Ucs.from_rotation((0, 0), 90)
        moved = to_world_ops([{"type": "rectangle", "corner1": [0, 0], "corner2": [0, 50]}], ucs)[0]
        assert moved["type"] == "rectangle"

    def test_a_polyline_s_every_vertex_is_converted(self):
        ucs = Ucs.from_rotation((1000, 0), 0)
        moved = to_world_ops([{"type": "polyline", "points": [[0, 0], [10, 0]]}], ucs)[0]
        assert moved["points"] == [[1000.0, 0.0, 0.0], [1010.0, 0.0, 0.0]]

    def test_unknown_fields_and_types_are_left_alone(self):
        ucs = Ucs.from_rotation((0, 0), 90)
        moved = to_world_ops([{"type": "mystery", "position": [1, 2], "note": "keep me"}], ucs)[0]
        assert moved == {"type": "mystery", "position": [1, 2], "note": "keep me"}


def test_levels():
    assert risk_of("autocad_get_ucs") is Risk.READ
    assert risk_of("autocad_convert_points") is Risk.READ
    assert risk_of("autocad_set_ucs") is Risk.CHANGE
