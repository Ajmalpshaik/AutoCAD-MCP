"""Revision clouds, and the annotation tools' levels (no AutoCAD).

The cloud is the part with real geometry in it: its arcs have to divide the
boundary exactly and bulge outward whichever way the boundary was traced.
"""

from __future__ import annotations

import math

import pytest

from autocad_mcp.core.risk import Risk, risk_of
from autocad_mcp.tools.annotate import (
    CLOUD_BULGE,
    MAX_CLOUD_ARCS,
    box_outline,
    resample,
    revision_cloud,
    signed_area,
)

BOX = [(0, 0), (1000, 0), (1000, 600), (0, 600)]
PERIMETER = 2 * (1000 + 600)


class TestResample:
    @pytest.mark.parametrize("step", [50, 100, 137, 250, 400])
    def test_the_spacing_divides_the_path_exactly(self, step):
        """What stops the last arc of a cloud being a stub: the step is adjusted
        so a whole number of arcs fits the boundary."""
        pts = resample(BOX, step, True)
        count = len(pts)
        assert count == round(PERIMETER / step)
        spacing = PERIMETER / count
        # The points are spaced evenly *along the path*, so a chord is never
        # longer than that spacing - and is shorter only where one cuts a
        # corner, which is the one place the path bends.
        chords = [math.dist(pts[i], pts[(i + 1) % count]) for i in range(count)]
        assert max(chords) <= spacing + 1e-9
        short = [c for c in chords if c < spacing - 1e-9]
        assert len(short) <= 4, "only the four corners may shorten a chord"

    @pytest.mark.parametrize("step", [50, 100, 160, 200])
    def test_a_step_that_already_divides_the_path_is_left_alone(self, step):
        pts = resample(BOX, step, True)
        assert PERIMETER / len(pts) == pytest.approx(step)

    def test_the_count_is_near_what_was_asked_for(self):
        assert len(resample(BOX, 100, True)) == 32  # 3200 / 100

    def test_an_open_path_keeps_both_ends(self):
        pts = resample([(0, 0), (1000, 0)], 100, False)
        assert pts[0] == pytest.approx((0.0, 0.0))
        assert pts[-1] == pytest.approx((1000.0, 0.0))
        assert len(pts) == 11

    def test_a_closed_path_does_not_repeat_its_start(self):
        pts = resample(BOX, 100, True)
        assert math.dist(pts[0], pts[-1]) > 1.0

    @pytest.mark.parametrize(
        ("path", "step", "match"),
        [
            ([(0, 0)], 10, "at least two points"),
            (BOX, 0, "above zero"),
            (BOX, -5, "above zero"),
            ([(0, 0), (0, 0), (0, 0)], 10, "no length"),
            (BOX, 0.1, str(MAX_CLOUD_ARCS)),
        ],
    )
    def test_refusals(self, path, step, match):
        with pytest.raises(ValueError, match=match):
            resample(path, step, True)


class TestSignedArea:
    def test_anticlockwise_is_positive(self):
        assert signed_area(BOX) > 0

    def test_clockwise_is_negative(self):
        assert signed_area(list(reversed(BOX))) < 0


class TestRevisionCloud:
    def test_it_is_one_closed_polyline_with_a_bulge_per_vertex(self):
        op = revision_cloud(BOX, 200)[0]
        assert op["type"] == "polyline" and op["closed"] is True
        assert len(op["bulges"]) == len(op["points"])

    def test_the_arcs_bulge_outward_whichever_way_the_boundary_runs(self):
        anticlockwise = revision_cloud(BOX, 200)[0]
        clockwise = revision_cloud(list(reversed(BOX)), 200)[0]
        assert anticlockwise["bulges"][0] == pytest.approx(-CLOUD_BULGE)
        assert clockwise["bulges"][0] == pytest.approx(CLOUD_BULGE)

    def test_the_arc_rises_a_quarter_of_its_chord_like_revcloud(self):
        op = revision_cloud(BOX, 200)[0]
        chord = math.dist(op["points"][0], op["points"][1])
        sweep = 4.0 * math.atan(abs(op["bulges"][0]))
        radius = chord / (2.0 * math.sin(sweep / 2.0))
        rise = radius * (1.0 - math.cos(sweep / 2.0))
        assert rise / chord == pytest.approx(0.25, abs=1e-9)

    def test_an_open_cloud_is_not_closed(self):
        op = revision_cloud([(0, 0), (1000, 0)], 100, closed=False)[0]
        assert "closed" not in op

    def test_the_layer_and_colour_are_carried(self):
        op = revision_cloud(BOX, 200, layer="G-ANNO-REVS", color=1)[0]
        assert op["layer"] == "G-ANNO-REVS" and op["color"] == 1

    def test_it_is_an_operation_the_batch_can_build(self):
        from autocad_mcp.tools.batch import BUILDERS

        BUILDERS["polyline"](revision_cloud(BOX, 200)[0], 0)

    def test_a_boundary_too_small_for_an_arc_is_refused(self):
        with pytest.raises(ValueError):
            revision_cloud([(0, 0), (0, 0)], 100)


class TestBoxOutline:
    def test_it_runs_anticlockwise(self):
        assert signed_area(box_outline((0, 0, 100, 50))) > 0

    def test_growing_pushes_every_side_out(self):
        assert box_outline((0, 0, 100, 50), 10) == [
            (-10.0, -10.0), (110.0, -10.0), (110.0, 60.0), (-10.0, 60.0)
        ]

    def test_a_box_with_no_size_is_refused(self):
        with pytest.raises(ValueError, match="no size"):
            box_outline((5, 5, 5, 5))


def test_levels():
    assert risk_of("autocad_add_multileader") is Risk.CHANGE
    assert risk_of("autocad_add_table") is Risk.CHANGE
    assert risk_of("autocad_add_revision_cloud") is Risk.CHANGE
