"""Sheet arithmetic: paper, scales, frames, viewport windows (no AutoCAD)."""

from __future__ import annotations

import pytest

from autocad_mcp.acad.sheets import (
    ISO_MARGINS_MM,
    PAPER_SIZES_MM,
    STANDARD_SCALES,
    centre_of,
    corner_point,
    dim_scale,
    fit_scale,
    frame,
    grid_boxes,
    inset,
    media_dimensions,
    model_window,
    paper_size,
    parse_scale,
    reserve,
    scale_text,
    sheet_plan,
    size_of,
    text_height,
)
from autocad_mcp.core.risk import Risk, risk_of


class TestParseScale:
    @pytest.mark.parametrize(
        ("given", "expected"),
        [
            ("1:50", 0.02), ("1:100", 0.01), ("1:1", 1.0), ("2:1", 2.0),
            ("1/50", 0.02), ("1=50", 0.02), (" 1 : 50 ", 0.02),
            ("SCALE 1:50", 0.02), ("1:2.5", 0.4), (0.02, 0.02), (1, 1.0),
        ],
    )
    def test_every_way_a_drafter_writes_it(self, given, expected):
        assert parse_scale(given) == pytest.approx(expected)

    @pytest.mark.parametrize("given", ["", "half size", "1:0", "0:1", "-1:50", "1:-50", None])
    def test_nonsense_is_refused_with_advice(self, given):
        with pytest.raises(ValueError) as exc:
            parse_scale(given)
        assert "1:50" in str(exc.value) or "zero" in str(exc.value)

    @pytest.mark.parametrize(
        ("ratio", "text"),
        [(0.02, "1:50"), (0.01, "1:100"), (1.0, "1:1"), (2.0, "2:1"), (0.4, "1:2.5")],
    )
    def test_back_to_the_text_on_the_sheet(self, ratio, text):
        assert scale_text(ratio) == text

    @pytest.mark.parametrize("text", STANDARD_SCALES)
    def test_every_standard_scale_round_trips(self, text):
        assert scale_text(parse_scale(text)) == text

    def test_dimscale_and_text_height_follow_from_the_scale(self):
        assert dim_scale("1:50") == pytest.approx(50.0)
        assert text_height(2.5, "1:10") == pytest.approx(25.0)
        assert text_height(2.5, "1:50") == pytest.approx(125.0)


class TestPaperSize:
    def test_iso_sizes(self):
        assert paper_size("A3") == (420.0, 297.0)
        assert paper_size("A1") == (841.0, 594.0)
        assert paper_size("a4") == (297.0, 210.0)

    def test_portrait_turns_the_sheet(self):
        assert paper_size("A3", "portrait") == (297.0, 420.0)

    def test_imperial_sizes_come_out_in_millimetres(self):
        width, height = paper_size("ANSI D")
        assert (round(width, 1), round(height, 1)) == (863.6, 558.8)
        assert paper_size("D") == paper_size("ANSI D")
        assert round(paper_size("ARCH E1")[0], 1) == 1066.8

    def test_spelling_is_forgiving(self):
        assert paper_size("arch_e1") == paper_size("ARCH E1")
        assert paper_size("ansi-b") == paper_size("ANSI B")

    def test_an_unknown_size_lists_the_known_ones(self):
        with pytest.raises(ValueError) as exc:
            paper_size("A9")
        for name in ("A0", "A4", "ANSI D", "ARCH E1"):
            assert name in str(exc.value)

    def test_every_listed_size_is_landscape(self):
        for name, (width, height) in PAPER_SIZES_MM.items():
            assert width >= height, name


class TestFrame:
    def test_iso_5457_margins_by_default(self):
        # 20 mm on the binding edge, 10 elsewhere.
        assert frame(420.0, 297.0) == (20.0, 10.0, 410.0, 287.0)
        assert ISO_MARGINS_MM == (20.0, 10.0, 10.0, 10.0)

    def test_one_number_is_used_on_all_four_sides(self):
        assert frame(100.0, 100.0, [5]) == (5.0, 5.0, 95.0, 95.0)

    def test_two_numbers_are_sides_then_ends(self):
        assert frame(100.0, 100.0, [5, 10]) == (5.0, 10.0, 95.0, 90.0)

    def test_four_numbers_are_left_bottom_right_top(self):
        assert frame(100.0, 100.0, [1, 2, 3, 4]) == (1.0, 2.0, 97.0, 96.0)

    def test_three_numbers_are_refused(self):
        with pytest.raises(ValueError, match="1, 2 or 4"):
            frame(100.0, 100.0, [1, 2, 3])

    def test_margins_that_leave_no_room_are_refused(self):
        with pytest.raises(ValueError, match="no room"):
            frame(100.0, 100.0, [60])


class TestBoxes:
    def test_corner_point_for_the_title_block(self):
        box = (20.0, 10.0, 410.0, 287.0)
        assert corner_point(box) == (410.0, 10.0)  # ISO 5457: bottom right
        assert corner_point(box, "top-left") == (20.0, 287.0)
        assert corner_point(box, "center") == (215.0, 148.5)
        assert corner_point(box, "bottom_centre") == (215.0, 10.0)

    def test_an_unknown_corner_lists_the_corners(self):
        with pytest.raises(ValueError, match="bottom-right"):
            corner_point((0, 0, 1, 1), "middle-ish")

    def test_reserve_takes_a_strip_off_one_side(self):
        assert reserve((0, 0, 420, 297), "right", 180) == (0, 0, 240, 297)
        assert reserve((0, 0, 420, 297), "bottom", 50) == (0, 50, 420, 297)
        with pytest.raises(ValueError, match="no drawing space"):
            reserve((0, 0, 100, 100), "right", 150)
        with pytest.raises(ValueError, match="not a side"):
            reserve((0, 0, 100, 100), "diagonally", 10)

    def test_inset_pulls_the_box_in(self):
        assert inset((0, 0, 100, 100), 5) == (5, 5, 95, 95)
        with pytest.raises(ValueError, match="no room"):
            inset((0, 0, 10, 10), 20)

    def test_centre_and_size(self):
        assert centre_of((0, 0, 100, 50)) == (50.0, 25.0)
        assert size_of((10, 10, 110, 60)) == (100.0, 50.0)


class TestModelWindow:
    def test_a_viewport_at_a_scale_looks_at_the_right_area(self):
        # 180 x 120 mm of paper at 1:50 is 9000 x 6000 drawing units.
        box = model_window((0, 0), 180, 120, "1:50")
        assert size_of(box) == pytest.approx((9000.0, 6000.0))
        assert centre_of(box) == pytest.approx((0.0, 0.0))

    def test_the_window_is_centred_on_the_point_given(self):
        box = model_window((1000, 2000), 100, 100, "1:10")
        assert centre_of(box) == pytest.approx((1000.0, 2000.0))

    def test_the_window_keeps_the_viewport_s_proportions(self):
        # This is what makes the scale come out exactly, not nearly.
        pw, ph = 180.0, 120.0
        box = model_window((0, 0), pw, ph, "1:50")
        width, height = size_of(box)
        assert width / height == pytest.approx(pw / ph)


class TestFitScale:
    def test_the_largest_standard_scale_that_fits(self):
        assert fit_scale((0, 0, 9000, 6000), 190, 275) == ("1:50", pytest.approx(0.02))
        # 900 wide needs 180 mm at 1:5, which fits 190 mm of paper.
        assert fit_scale((0, 0, 900, 450), 190, 275) == ("1:5", pytest.approx(0.2))
        # 1000 wide would need 200 mm at 1:5, so it steps down.
        assert fit_scale((0, 0, 1000, 500), 190, 275) == ("1:10", pytest.approx(0.1))

    def test_a_tight_fit_steps_down_to_the_next_scale(self):
        # 9000 wide needs 180 mm at 1:50; 179 mm of paper cannot take it.
        assert fit_scale((0, 0, 9000, 6000), 179, 275)[0] == "1:75"

    def test_an_area_too_big_for_every_scale_says_so(self):
        with pytest.raises(ValueError) as exc:
            fit_scale((0, 0, 1e9, 1e9), 10, 10)
        assert "1:5000" in str(exc.value)

    def test_an_area_with_no_size_is_refused(self):
        with pytest.raises(ValueError, match="no size"):
            fit_scale((0, 0, 0, 100), 190, 275)


class TestGridBoxes:
    def test_reads_left_to_right_then_down(self):
        boxes = grid_boxes((0, 0, 100, 100), 2, 2)
        assert boxes[0] == (0.0, 50.0, 50.0, 100.0)  # top left first
        assert boxes[1] == (50.0, 50.0, 100.0, 100.0)
        assert boxes[2] == (0.0, 0.0, 50.0, 50.0)

    def test_the_gap_comes_out_of_the_boxes(self):
        boxes = grid_boxes((0, 0, 100, 100), 2, 1, gap=20)
        assert size_of(boxes[0]) == (40.0, 100.0)

    def test_a_grid_that_will_not_fit_is_refused(self):
        with pytest.raises(ValueError, match="no room"):
            grid_boxes((0, 0, 10, 10), 5, 5, gap=10)
        with pytest.raises(ValueError, match="at least one"):
            grid_boxes((0, 0, 10, 10), 0, 1)


class TestMediaDimensions:
    @pytest.mark.parametrize(
        ("media", "expected"),
        [
            ("ISO_full_bleed_A3_(420.00_x_297.00_MM)", (420.0, 297.0)),
            ("ISO A1 (841.00 x 594.00 MM)", (841.0, 594.0)),
            ("ANSI_A_(11.00_x_8.50_Inches)", (11.0, 8.5)),
            ("ARCH_E1_(42.00_x_30.00_Inches)", (42.0, 30.0)),
        ],
    )
    def test_the_size_is_read_out_of_the_name(self, media, expected):
        assert media_dimensions(media) == expected

    @pytest.mark.parametrize("media", ["", "Letter", None, "PublishToWeb_(1280.00_x_1024.00_Pixels)"])
    def test_a_name_with_no_sheet_in_it_comes_back_empty(self, media):
        assert media_dimensions(media) is None


class TestSheetPlan:
    def test_a3_landscape_with_a_title_block_strip(self):
        plan = sheet_plan("A3", "landscape", title_block_width=180, gap=2)
        assert plan["paper"] == [420.0, 297.0]
        assert plan["orientation"] == "landscape"
        assert plan["frame"] == [20.0, 10.0, 410.0, 287.0]
        assert plan["title_block_at"] == [410.0, 10.0]
        # 410 - 180 = 230, less the 2 mm gap
        assert plan["drawing_space"] == [22.0, 12.0, 228.0, 285.0]
        assert plan["drawing_space_size"] == [206.0, 273.0]

    def test_portrait_is_reported_as_portrait(self):
        assert sheet_plan("A4", "portrait")["orientation"] == "portrait"

    def test_the_drawing_space_is_the_frame_when_nothing_is_reserved(self):
        plan = sheet_plan("A1")
        assert plan["drawing_space"] == plan["frame"]


def test_levels():
    assert risk_of("autocad_create_layout") is Risk.CHANGE
    assert risk_of("autocad_page_setup") is Risk.CHANGE
    assert risk_of("autocad_place_title_block") is Risk.CHANGE
    assert risk_of("autocad_add_viewport") is Risk.CHANGE
    assert risk_of("autocad_list_views") is Risk.READ
    assert risk_of("autocad_save_view") is Risk.CHANGE
