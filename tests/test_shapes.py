"""The parametric shape library: simple words in, correct geometry out.

Every shape is checked against the number it is supposed to produce, not
against itself: a slot's perimeter against two straights plus a circle, a flat
pattern's arc lengths against the girths it has to roll onto, a hexagon's
across-flats against the spanner size asked for. No AutoCAD.
"""

from __future__ import annotations

import math

import pytest

from autocad_mcp.acad import shapes as s
from autocad_mcp.core.risk import Risk, risk_of


def perimeter(op: dict) -> float:
    """A polyline operation's true perimeter, arcs included."""
    pts = op["points"]
    bulges = op.get("bulges") or [0.0] * len(pts)
    closed = bool(op.get("closed"))
    total = 0.0
    for i in range(len(pts) if closed else len(pts) - 1):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        chord = math.dist(a, b)
        bulge = bulges[i] if i < len(bulges) else 0.0
        if abs(bulge) < 1e-12:
            total += chord
        else:
            sweep = 4.0 * math.atan(bulge)
            radius = chord / (2.0 * abs(math.sin(sweep / 2.0)))
            total += abs(sweep) * radius
    return total


def extent(op: dict) -> tuple[float, float]:
    xs = [p[0] for p in op["points"]]
    ys = [p[1] for p in op["points"]]
    return (max(xs) - min(xs), max(ys) - min(ys))


class TestPolygonAndHexagon:
    def test_inscribed_measures_to_a_corner(self):
        op = s.polygon(6, 10)[0]
        assert math.dist(op["points"][0], (0, 0)) == pytest.approx(10.0)

    def test_circumscribed_measures_to_a_flat(self):
        op = s.polygon(6, 10, inscribed=False)[0]
        # A flat at radius 10 puts the corners further out.
        assert math.dist(op["points"][0], (0, 0)) == pytest.approx(10.0 / math.cos(math.pi / 6))

    @pytest.mark.parametrize("sides", [3, 4, 5, 6, 8, 12])
    def test_every_polygon_closes_with_the_right_number_of_sides(self, sides):
        op = s.polygon(sides, 50)[0]
        assert len(op["points"]) == sides
        assert op["closed"] is True

    def test_fewer_than_three_sides_is_refused(self):
        with pytest.raises(ValueError, match="at least 3"):
            s.polygon(2, 10)

    @pytest.mark.parametrize("flats", [10.0, 17.0, 24.0, 30.0])
    def test_across_flats_is_what_a_spanner_reads(self, flats):
        op = s.hexagon(across_flats=flats)[0]
        # A flat top and bottom, so the across-flats size reads vertically.
        assert extent(op)[1] == pytest.approx(flats)

    def test_across_corners_converts_to_the_same_hexagon(self):
        corners = 24.0 / math.cos(math.pi / 6)
        from_corners = s.hexagon(across_corners=corners)[0]["points"]
        from_flats = s.hexagon(across_flats=24.0)[0]["points"]
        assert len(from_corners) == len(from_flats)
        for a, b in zip(from_corners, from_flats, strict=True):
            assert a == pytest.approx(b)

    def test_a_hexagon_needs_one_size_or_the_other(self):
        with pytest.raises(ValueError, match="across_flats"):
            s.hexagon()


class TestSlotAndRoundedRectangle:
    def test_a_slot_is_two_straights_and_a_full_circle(self):
        op = s.slot(120, 40)[0]
        assert perimeter(op) == pytest.approx(2 * 80 + math.pi * 40)

    def test_a_slot_is_one_closed_object(self):
        op = s.slot(120, 40)[0]
        assert op["closed"] is True and op["type"] == "polyline"
        assert len([b for b in op["bulges"] if b]) == 2

    def test_a_slot_no_longer_than_it_is_wide_is_refused(self):
        with pytest.raises(ValueError, match="just a hole"):
            s.slot(40, 40)
        with pytest.raises(ValueError):
            s.slot(30, 40)

    def test_a_rounded_rectangle_loses_the_corners_and_gains_a_circle(self):
        op = s.rounded_rectangle(100, 50, 10)[0]
        assert perimeter(op) == pytest.approx(2 * (80 + 30) + math.pi * 20)

    def test_a_rounded_rectangle_keeps_its_overall_size(self):
        op = s.rounded_rectangle(2400, 1200, 50)[0]
        assert extent(op) == pytest.approx((2400.0, 1200.0))

    def test_the_largest_radius_that_fits_is_half_the_short_side(self):
        s.rounded_rectangle(100, 50, 25)  # exactly half: allowed
        with pytest.raises(ValueError, match="the most it takes is 25"):
            s.rounded_rectangle(100, 50, 30)

    def test_centred_puts_the_origin_in_the_middle(self):
        op = s.rounded_rectangle(100, 50, 10, centred=True)[0]
        xs = [p[0] for p in op["points"]]
        assert min(xs) == pytest.approx(-50.0) and max(xs) == pytest.approx(50.0)


class TestFlangeAndBoltCircle:
    def test_a_flange_is_outside_bore_pitch_circle_and_its_holes(self):
        ops = s.flange(200, 8, 160, 18, bore=100)
        assert len(ops) == 3 + 8
        assert [round(o["radius"], 3) for o in ops[:3]] == [100.0, 50.0, 80.0]

    def test_every_hole_sits_on_the_pitch_circle(self):
        ops = s.flange(200, 8, 160, 18)
        for hole in ops[2:]:
            assert math.dist(hole["center"], (0, 0)) == pytest.approx(80.0)

    def test_the_pitch_circle_can_go_on_its_own_layer(self):
        ops = s.flange(200, 4, 160, 18, layer="M-PIPE", centreline_layer="M-PIPE-CNTR")
        assert ops[0]["layer"] == "M-PIPE"
        assert ops[1]["layer"] == "M-PIPE-CNTR"  # the pitch circle

    def test_a_pitch_circle_outside_the_flange_is_refused(self):
        with pytest.raises(ValueError, match="inside the flange"):
            s.flange(200, 8, 220, 18)

    def test_a_bore_outside_the_pitch_circle_is_refused(self):
        with pytest.raises(ValueError, match="inside the pitch circle"):
            s.flange(200, 8, 160, 18, bore=170)

    def test_holes_are_evenly_spaced(self):
        ops = s.bolt_circle(6, 100, 12)
        angles = sorted(
            round(math.degrees(math.atan2(o["center"][1], o["center"][0])) % 360.0, 6)
            for o in ops
        )
        assert angles == pytest.approx([0.0, 60.0, 120.0, 180.0, 240.0, 300.0])


class TestConeDevelopment:
    @pytest.mark.parametrize(
        ("bottom", "top", "height"),
        [(200, 100, 100), (400, 150, 300), (300, 100, 50), (1000, 900, 200)],
    )
    def test_the_pattern_rolls_onto_the_cone_it_came_from(self, bottom, top, height):
        """The only test that matters for a flat pattern: the arcs have to be
        exactly as long as the girths they wrap round."""
        op = s.cone_development(bottom, top, height)[0]
        radii = sorted({round(math.dist(p, (0, 0)), 6) for p in op["points"]})
        inner, outer = radii[0], radii[-1]
        sweep = 4.0 * math.atan(op["bulges"][1])
        assert sweep * outer == pytest.approx(math.pi * bottom)
        assert sweep * inner == pytest.approx(math.pi * top)

    def test_a_full_cone_has_no_inner_radius(self):
        op = s.cone_development(200, 0, 100)[0]
        radii = sorted({round(math.dist(p, (0, 0)), 6) for p in op["points"]})
        assert radii[0] == pytest.approx(0.0)
        assert radii[-1] == pytest.approx(math.hypot(100, 100))

    def test_a_cylinder_is_refused_rather_than_dividing_by_zero(self):
        with pytest.raises(ValueError, match="wider than the top"):
            s.cone_development(200, 200, 100)

    def test_a_top_wider_than_the_bottom_is_refused(self):
        with pytest.raises(ValueError, match="turn the piece over"):
            s.cone_development(100, 200, 100)

    def test_a_piece_too_shallow_for_one_arc_says_so(self):
        # 500 radius over 100 of height opens out to 353 degrees, where the
        # bulge for a single arc has already run away to 33.
        with pytest.raises(ValueError, match="nearer a flat ring"):
            s.cone_development(1000, 0, 100)

    def test_the_sweep_limit_is_the_only_thing_that_stops_it(self):
        # Just inside the limit still works, so the guard is not over-eager.
        assert s.cone_development(1000, 0, 200)

    def test_a_seam_allowance_adds_an_edge_line(self):
        plain = s.cone_development(200, 100, 150)
        lapped = s.cone_development(200, 100, 150, seam_allowance=10)
        assert len(lapped) == len(plain) + 1


class TestStair:
    def test_a_section_climbs_to_the_top_of_the_flight(self):
        op = s.stair(14, 175, 280, 1200, view="section")[0]
        assert op["points"][-1] == pytest.approx([14 * 280, 14 * 175])

    def test_a_section_has_a_riser_and_a_tread_for_every_step(self):
        op = s.stair(5, 175, 280, 1200, view="section")[0]
        assert len(op["points"]) == 1 + 5 * 2

    def test_a_plan_has_an_outline_a_tread_line_per_step_and_a_walking_line(self):
        ops = s.stair(5, 175, 280, 1200, view="plan")
        assert len(ops) == 1 + (5 - 1) + 1

    def test_the_plan_outline_is_the_whole_going_by_the_width(self):
        ops = s.stair(14, 175, 280, 1200, view="plan")
        assert extent(ops[0]) == pytest.approx((14 * 280.0, 1200.0))

    def test_an_unknown_view_is_refused(self):
        with pytest.raises(ValueError, match="section"):
            s.stair(5, 175, 280, 1200, view="axonometric")


class TestElbowAndTransition:
    def test_an_elbow_is_inside_outside_centreline_and_two_ends(self):
        ops = s.elbow(300, 90, 200)
        assert [o["type"] for o in ops] == ["arc", "arc", "arc", "line", "line"]
        assert [o["radius"] for o in ops[:3]] == pytest.approx([200.0, 400.0, 300.0])

    def test_a_width_that_will_not_fit_the_radius_is_refused(self):
        with pytest.raises(ValueError, match="does not fit"):
            s.elbow(100, 90, 200)

    @pytest.mark.parametrize("angle", [0, 360, 400])
    def test_an_impossible_sweep_is_refused(self, angle):
        with pytest.raises(ValueError, match="between 0 and 360"):
            s.elbow(300, angle, 200)

    def test_a_transition_is_its_outline_and_its_centreline(self):
        ops = s.duct_transition(600, 300, 450)
        assert [o["type"] for o in ops] == ["polyline", "line"]
        assert extent(ops[0]) == pytest.approx((450.0, 600.0))

    def test_an_offset_transition_shifts_only_its_outlet(self):
        ops = s.duct_transition(600, 300, 450, offset=100)
        inlet_low, outlet_low, outlet_high, inlet_high = ops[0]["points"]
        # The inlet keeps its own 600, centred on the origin.
        assert inlet_low[1] == pytest.approx(-300.0)
        assert inlet_high[1] == pytest.approx(300.0)
        # The outlet is 300 wide, centred 100 up.
        assert outlet_low[1] == pytest.approx(-50.0)
        assert outlet_high[1] == pytest.approx(250.0)
        # And the centreline runs from one centre to the other.
        assert ops[1]["start"] == pytest.approx([0.0, 0.0])
        assert ops[1]["end"] == pytest.approx([450.0, 100.0])


class TestSteelSections:
    @pytest.mark.parametrize("profile", s.STEEL_SECTIONS)
    def test_every_profile_builds_and_keeps_its_depth(self, profile):
        ops = s.steel_section(profile, 200, 100, web=6, flange_thickness=10)
        assert ops
        if profile == "chs":
            assert [round(o["radius"], 3) for o in ops] == [100.0, 94.0]
            return
        heights = [extent(o)[1] for o in ops if o["type"] == "polyline"]
        assert max(heights) == pytest.approx(200.0)

    def test_an_i_section_has_twelve_corners(self):
        op = s.steel_section("i", 300, 150, web=8, flange_thickness=12)[0]
        assert len(op["points"]) == 12

    def test_a_hollow_section_is_two_loops(self):
        ops = s.steel_section("rhs", 200, 100, web=6)
        assert len(ops) == 2
        assert extent(ops[1]) == pytest.approx((100 - 12.0, 200 - 12.0))

    def test_an_unknown_profile_lists_the_real_ones(self):
        with pytest.raises(ValueError, match="shs"):
            s.steel_section("universal", 200, 100, web=6, flange_thickness=10)

    def test_a_wall_too_thick_for_the_tube_is_refused(self):
        with pytest.raises(ValueError, match="too thick"):
            s.steel_section("chs", 100, 100, web=60)

    def test_flanges_thicker_than_the_section_are_refused(self):
        with pytest.raises(ValueError, match="too thick"):
            s.steel_section("i", 20, 100, web=6, flange_thickness=15)


class TestGear:
    def test_the_drawing_office_convention_is_three_circles(self):
        ops = s.gear(24, 120)
        assert [o["type"] for o in ops] == ["circle"] * 3
        module = 120 / 24
        assert [round(o["radius"], 6) for o in ops] == [
            (120 + 2 * module) / 2, 60.0, (120 - 2.5 * module) / 2
        ]

    def test_showing_teeth_adds_one_outline_per_tooth(self):
        ops = s.gear(24, 120, show_teeth=True)
        assert len(ops) == 3 + 24

    def test_too_few_teeth_is_refused(self):
        with pytest.raises(ValueError, match="at least 6"):
            s.gear(3, 120)

    def test_an_impossible_pressure_angle_is_refused(self):
        with pytest.raises(ValueError, match="between 0 and 45"):
            s.gear(24, 120, show_teeth=True, pressure_angle=60)


class TestFurniture:
    def test_a_detail_bubble_splits_when_it_is_given_a_sheet(self):
        plain = s.detail_bubble(3, 300)
        split = s.detail_bubble(3, 300, sheet="E-101")
        assert [o["type"] for o in plain] == ["circle", "text"]
        assert [o["type"] for o in split] == ["circle", "line", "text", "text"]
        assert [o["text"] for o in split if o["type"] == "text"] == ["3", "E-101"]

    def test_bubble_text_sits_on_its_point(self):
        assert all(
            o.get("align") == "center" for o in s.detail_bubble(3, 300) if o["type"] == "text"
        )

    def test_a_section_mark_has_a_tail_an_arrow_and_a_bubble_each_end(self):
        ops = s.section_mark(4000, label="A")
        kinds = [o["type"] for o in ops]
        assert kinds.count("circle") == 2            # a bubble each end
        assert kinds.count("polyline") == 2          # an arrowhead each end
        assert [o["text"] for o in ops if o["type"] == "text"] == ["A", "A"]

    def test_a_scale_bar_labels_the_real_distances_not_the_paper_ones(self):
        ops = s.scale_bar("1:50", 100, divisions=5)
        labels = [o["text"] for o in ops if o["type"] == "text"]
        assert labels[:6] == ["0", "1000", "2000", "3000", "4000", "5000"]
        assert labels[-1] == "SCALE 1:50"

    def test_a_scale_bar_alternates_its_divisions(self):
        ops = s.scale_bar("1:100", 100, divisions=4)
        assert sum(1 for o in ops if o["type"] == "polyline") == 4
        assert sum(1 for o in ops if o["type"] == "line") == 2  # the alternate marks

    def test_a_scale_bar_refuses_a_scale_it_cannot_read(self):
        with pytest.raises(ValueError, match="not a scale"):
            s.scale_bar("half size", 100)

    def test_a_level_mark_can_hang_below_its_point(self):
        above = s.level_mark("+3.600", size=150)[0]
        below = s.level_mark("-0.150", size=150, below=True)[0]
        assert max(p[1] for p in above["points"]) > 0
        assert min(p[1] for p in below["points"]) < 0

    def test_a_north_arrow_is_marked_n(self):
        ops = s.north_arrow(1000)
        assert [o["text"] for o in ops if o["type"] == "text"] == ["N"]

    def test_a_revision_tag_is_a_triangle_round_its_number(self):
        ops = s.revision_tag(2, size=200)
        assert [o["type"] for o in ops] == ["polyline", "text"]
        assert len(ops[0]["points"]) == 3


class TestPlacement:
    def test_origin_moves_every_part_of_a_shape(self):
        here = s.flange(200, 4, 160, 18, origin=[1000, 500])
        for op in here:
            assert math.dist(op["center"], (1000, 500)) < 200

    def test_rotation_turns_the_shape_about_its_origin(self):
        op = s.slot(120, 40, rotation=90)[0]
        # A slot 120 long turned upright is 120 tall, 40 wide.
        width, height = extent(op)
        assert height > width

    @pytest.mark.parametrize("kind", sorted(s.SHAPES))
    def test_every_shape_accepts_an_origin(self, kind):
        assert "origin" in s.SHAPES[kind].__code__.co_varnames


class TestRegistry:
    @pytest.mark.parametrize("kind", sorted(s.SHAPES))
    def test_every_shape_has_a_required_list_and_a_docstring(self, kind):
        assert kind in s.REQUIRED
        assert (s.SHAPES[kind].__doc__ or "").strip()

    @pytest.mark.parametrize("kind", sorted(s.SHAPES))
    def test_every_required_setting_is_really_a_parameter(self, kind):
        takes = s.SHAPES[kind].__code__.co_varnames
        for name in s.REQUIRED[kind]:
            assert name in takes, f"{kind} requires {name} but does not take it"

    @pytest.mark.parametrize("kind", sorted(s.SHAPES))
    def test_settings_of_describes_every_shape(self, kind):
        about = s.settings_of(kind)
        assert about["shape"] == kind
        assert about["about"]

    def test_an_unknown_shape_lists_them_all(self):
        with pytest.raises(ValueError) as exc:
            s.build("teapot", {})
        message = str(exc.value)
        for kind in ("flange", "slot", "cone_development", "revision_tag"):
            assert kind in message

    def test_a_missing_setting_is_named(self):
        with pytest.raises(ValueError, match="needs radius"):
            s.build("polygon", {"sides": 6})

    def test_a_setting_the_shape_does_not_take_is_named_with_the_real_ones(self):
        with pytest.raises(ValueError) as exc:
            s.build("polygon", {"sides": 6, "radius": 10, "colour": 1})
        assert "does not take colour" in str(exc.value)
        assert "inscribed" in str(exc.value)

    def test_none_values_are_treated_as_not_given(self):
        # An agent that sends every field with nulls still gets the defaults.
        s.build("polygon", {"sides": 6, "radius": 10, "rotation": None, "layer": None})

    def test_build_names_the_shape_case_insensitively(self):
        assert s.build("ROUNDED-RECTANGLE", {"width": 10, "height": 10, "radius": 2})
        assert s.build("rounded rectangle", {"width": 10, "height": 10, "radius": 2})


# One realistic set of settings per shape, used to prove two things: that every
# shape produces operations the batch can build, and that no shape's bulges
# outnumber its vertices. Kept here so adding a shape without a case fails.
CASES: list[tuple[str, dict]] = [
            ("polygon", {"sides": 6, "radius": 50}),
            ("hexagon", {"across_flats": 24}),
            ("star", {"points": 5, "outer_radius": 100}),
            ("slot", {"length": 120, "width": 40}),
            ("rounded_rectangle", {"width": 100, "height": 50, "radius": 10}),
            ("spiral", {"turns": 2, "start_radius": 10, "end_radius": 50}),
            ("bolt_circle", {"count": 6, "pitch_diameter": 100, "hole_diameter": 12}),
            ("flange", {"outer_diameter": 200, "bolt_count": 8, "pitch_diameter": 160, "hole_diameter": 18}),
            ("elbow", {"centreline_radius": 300, "angle": 90, "width": 200}),
            ("duct_transition", {"width_in": 600, "width_out": 300, "length": 450}),
            ("stair", {"risers": 14, "rise": 175, "going": 280, "width": 1200}),
            ("ladder", {"height": 3000, "width": 450}),
            ("grating", {"width": 1000, "height": 600, "spacing": 30}),
            ("truss", {"span": 6000, "depth": 800, "panels": 6}),
            ("zigzag", {"length": 500, "amplitude": 20, "cycles": 8}),
            ("steel_section", {"profile": "i", "depth": 300, "width": 150, "web": 8, "flange_thickness": 12}),
            ("cone_development", {"bottom_diameter": 200, "top_diameter": 100, "height": 150}),
            ("gear", {"teeth": 24, "pitch_diameter": 120}),
            ("detail_bubble", {"number": 3, "radius": 300}),
            ("section_mark", {"length": 4000}),
            ("north_arrow", {"size": 1000}),
            ("scale_bar", {"scale": "1:50", "length": 100}),
            ("level_mark", {"level": "+3.600"}),
            ("revision_tag", {"number": 2}),
]


class TestOperationShape:
    """Everything generated has to be something autocad_batch_draw accepts."""

    KNOWN = {"line", "circle", "arc", "polyline", "text", "point", "rectangle"}

    def test_every_catalogued_shape_has_a_case(self):
        assert {kind for kind, _ in CASES} == set(s.SHAPES)

    @pytest.mark.parametrize(("kind", "params"), CASES)
    def test_the_operations_are_ones_the_batch_can_build(self, kind, params):
        from autocad_mcp.tools.batch import BUILDERS

        ops = s.build(kind, params)
        assert ops, kind
        for index, op in enumerate(ops):
            assert op["type"] in self.KNOWN, f"{kind} made a '{op['type']}'"
            # The real proof: the batch builder accepts it without complaint.
            BUILDERS[op["type"]](op, index)

    @pytest.mark.parametrize(("kind", "params"), CASES)
    def test_a_bulge_never_outnumbers_its_vertices(self, kind, params):
        for op in s.build(kind, params):
            if op["type"] == "polyline" and op.get("bulges"):
                assert len(op["bulges"]) <= len(op["points"])

    @pytest.mark.parametrize(("kind", "params"), CASES)
    def test_every_shape_can_be_put_on_a_layer(self, kind, params):
        for op in s.build(kind, {**params, "layer": "T-TEST"}):
            assert op["layer"] == "T-TEST"


def test_levels():
    assert risk_of("autocad_make_shape") is Risk.CHANGE
