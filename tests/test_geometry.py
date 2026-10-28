"""Plane geometry behind the take-off, placement and labelling tools (no AutoCAD)."""

from __future__ import annotations

import math

import pytest

from autocad_mcp.acad import geometry as g


def flat(pieces):
    """Pieces as one list of coordinates: pytest 9 approx refuses nested lists."""
    return [value for piece in pieces for point in piece for value in point]


def test_straight_and_arc_segments():
    segs = g.segments([(0, 0), (10, 0), (12, 0)], [0.0, 1.0], closed=False)
    assert segs[0].length == pytest.approx(10)
    arc = segs[1]
    assert arc.radius == pytest.approx(1) and arc.centre == pytest.approx((11, 0))
    assert arc.length == pytest.approx(math.pi)


def test_minor_arc_centre_is_left_of_chord_for_positive_bulge():
    (arc,) = g.segments([(0, 0), (2, 0)], [0.5], closed=False)
    assert arc.centre == pytest.approx((1, 0.75)) and arc.radius == pytest.approx(1.25)


def test_point_at_distance_with_direction():
    segs = g.segments([(0, 0), (10, 0), (10, 10)], [0, 0], closed=False)
    assert g.point_at(segs, 15) == pytest.approx((10, 5, 90))
    x, y, _ = g.point_at(g.segments([(0, 0), (2, 0)], [1.0], closed=False), math.pi / 2)
    assert (x, y) == pytest.approx((1, -1))  # positive bulge = counter-clockwise, bulging right


def test_closed_path_has_a_closing_segment():
    segs = g.segments([(0, 0), (4, 0), (4, 3)], [0, 0, 0], closed=True)
    assert sum(s.length for s in segs) == pytest.approx(12)


def test_centred_positions_leave_equal_ends():
    assert g.centred_positions(10, spacing=3) == pytest.approx([2, 5, 8])
    assert g.centred_positions(10, count=4) == pytest.approx([1.25, 3.75, 6.25, 8.75])
    assert g.centred_positions(2, spacing=3) == pytest.approx([1])


def test_distance_along_path_for_sorting():
    segs = g.segments([(0, 0), (10, 0), (10, 10)], [0, 0], closed=False)
    assert g.distance_along(segs, (4, 1)) == pytest.approx(4)
    assert g.distance_along(segs, (11, 6)) == pytest.approx(16)


def test_segment_outside_a_box():
    box = (4, -1, 6, 1)
    got = g.outside_pieces((0, 0), (10, 0), box)
    assert len(got) == 2 and flat(got) == pytest.approx(flat([((0, 0), (4, 0)), ((6, 0), (10, 0))]))
    assert g.outside_pieces((0, 5), (10, 5), box) == [((0, 5), (10, 5))]
    assert g.outside_pieces((5, 0), (5.5, 0), box) == []


def test_path_outside_a_box_splits_into_runs():
    runs = g.path_outside([(0, 0), (10, 0), (10, 10)], (4, -1, 6, 1))
    assert runs == [[(0, 0), (4, 0)], [(6, 0), (10, 0), (10, 10)]]


def test_connected_runs_by_end_points():
    items = [
        {"handle": "A", "ends": [(0, 0), (10, 0)]},
        {"handle": "B", "ends": [(10, 0.0005), (10, 10)]},
        {"handle": "C", "ends": [(10, 10), (20, 10)]},
        {"handle": "D", "ends": [(50, 50), (60, 50)]},
    ]
    found = g.connected(items, "B", tolerance=0.001)
    assert found["handles"] == ["A", "B", "C"]
    assert sorted(found["open_ends"]) == [(0, 0), (20, 10)]


def test_polygon_centroid_and_area():
    c, area = g.centroid([(0, 0), (4, 0), (4, 2), (0, 2)])
    assert c == pytest.approx((2, 1)) and area == pytest.approx(8)


def test_pieces_between_cuts():
    got = g.pieces((0, 0), (10, 0), [(7, 0), (3, 0)])
    assert len(got) == 3 and flat(got) == pytest.approx(
        flat([((0, 0), (3, 0)), ((3, 0), (7, 0)), ((7, 0), (10, 0))]))


def test_nurbs_length_of_a_straight_spline_and_a_quarter_circle():
    straight = g.nurbs_length([0, 0, 0, 10, 0, 0], [0, 0, 1, 1], 1, [])
    assert straight == pytest.approx(10, rel=1e-6)
    w = math.sqrt(2) / 2
    quarter = g.nurbs_length([1, 0, 0, 1, 1, 0, 0, 1, 0], [0, 0, 0, 1, 1, 1], 2, [1, w, 1])
    assert quarter == pytest.approx(math.pi / 2, rel=1e-4)


def test_ellipse_arc_length():
    assert g.ellipse_length(2, 2, 0, 2 * math.pi) == pytest.approx(4 * math.pi, rel=1e-6)
    assert g.ellipse_length(3, 1, 0, 2 * math.pi) == pytest.approx(13.3649, rel=1e-4)


def test_overlapping_boxes():
    boxes = {"D1": (0, 0, 10, 2), "D2": (8, 0, 18, 2), "D3": (10, 0, 20, 2), "D4": (0, 5, 5, 6)}
    assert g.overlapping(boxes, min_share=0.01) == [("D1", "D2"), ("D2", "D3")]
