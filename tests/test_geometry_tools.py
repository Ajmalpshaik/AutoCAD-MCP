"""Geometry and placement tools: polyline info, field labels, segment labels, place along, CSV rows.

Ideas from Lee Mac's Polyline Information, Length & Area Field, Length at
Midpoint, Centered Measure, Point Manager and Automatic Block Break
(lee-mac.com), written fresh for Heron.
"""

from __future__ import annotations

import math

import pytest

from autocad_mcp.tools import geometry_tools as gt


def test_describe_path_lists_segments_arcs_and_centroid():
    path = {"vertices": [(0, 0), (10, 0), (10, 10), (0, 10)], "bulges": [0, 0, 0, 0], "closed": True}
    info = gt.describe_path(path)
    assert info["total_length"] == pytest.approx(40) and info["segment_count"] == 4
    assert info["centroid"] == pytest.approx([5, 5]) and info["closed"] is True
    arc = gt.describe_path({"vertices": [(0, 0), (2, 0)], "bulges": [1.0], "closed": False})["segments"][0]
    assert arc["kind"] == "arc" and arc["radius"] == pytest.approx(1) and arc["sweep_degrees"] == pytest.approx(180)


def test_field_code_for_one_object_and_a_sum():
    assert gt.field_code(["123"], "Length", precision=0) == '%<\\AcObjProp Object(%<\\_ObjId 123>%).Length \\f "%lu2%pr0">%'
    code = gt.field_code(["1", "2"], "Area", precision=2, factor=1e-6)
    assert code == ('%<\\AcExpr (%<\\AcObjProp Object(%<\\_ObjId 1>%).Area>%+%<\\AcObjProp Object(%<\\_ObjId 2>%).Area>%)'
                    ' \\f "%lu2%pr2%ct8[1e-06]">%')


def test_segment_labels_sit_above_and_read_left_to_right():
    path = {"vertices": [(10, 0), (0, 0)], "bulges": [0], "closed": False}  # drawn right to left
    (label,) = gt.segment_labels(path, offset=2, precision=0)
    assert label["text"] == "10" and label["rotation"] == pytest.approx(0)
    assert label["position"] == pytest.approx([5, 2])
    vertical = gt.segment_labels({"vertices": [(0, 0), (0, 5)], "bulges": [0], "closed": False}, offset=1, precision=1, prefix="L=")
    assert vertical[0]["text"] == "L=5.0" and vertical[0]["rotation"] == pytest.approx(90)
    assert vertical[0]["position"] == pytest.approx([-1, 2.5])


def test_segment_labels_split_at_cut_points():
    path = {"vertices": [(0, 0), (10, 0)], "bulges": [0], "closed": False}
    texts = [lab["text"] for lab in gt.segment_labels(path, offset=0, precision=0, cuts=[(3, 0), (20, 0)])]
    assert texts == ["3", "7"]


def test_place_along_centres_and_turns_with_the_run():
    path = {"vertices": [(0, 0), (10, 0), (10, 10)], "bulges": [0, 0], "closed": False}
    spots = gt.places_along(path, spacing=6)
    assert [s["position"] for s in spots] == [pytest.approx([4, 0]), pytest.approx([10, 0]), pytest.approx([10, 6])]
    assert [s["rotation"] for s in spots] == pytest.approx([0, 0, 0])
    spots = gt.places_along(path, count=2, align=True)
    assert spots[1]["position"] == pytest.approx([10, 5]) and spots[1]["rotation"] == pytest.approx(90)


def test_rows_to_places_reads_coordinates_and_attributes():
    rows = [{"X": "100", "y": "200", "Rotation": "90", "TAG": "CAM-01", "block": "DOME"},
            {"x": "5", "y": "6", "TAG": "CAM-02"}]
    places = gt.rows_to_places(rows, default_block="BULLET")
    assert places[0] == {"position": [100.0, 200.0], "rotation": 90.0, "block": "DOME", "attributes": {"TAG": "CAM-01"}}
    assert places[1]["block"] == "BULLET" and places[1]["rotation"] == 0.0


def test_rows_without_coordinates_are_refused():
    with pytest.raises(ValueError, match="row 1"):
        gt.rows_to_places([{"X": "1"}], default_block="B")


def test_break_box_grows_by_the_gap():
    assert gt.grow((0, 0, 10, 4), 1) == (-1, -1, 11, 5)


def test_levels():
    from autocad_mcp.core.risk import Risk, risk_of

    for name in ("polyline_info", "select_connected"):
        assert risk_of(f"autocad_{name}") is Risk.READ
    for name in ("add_field_label", "label_segment_lengths", "place_along", "place_from_csv", "break_at_blocks"):
        assert risk_of(f"autocad_{name}") is Risk.CHANGE


def test_rotation_is_readable():
    assert gt.readable(180) == pytest.approx(0) and gt.readable(270) == pytest.approx(90)
    assert gt.readable(math.degrees(math.atan2(-1, -1)) % 360) == pytest.approx(45)
