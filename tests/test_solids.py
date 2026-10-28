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


# ---------------------------------------------------------------------------
# Against fake solids (2026-10-28, AutoCAD 2027)
# ---------------------------------------------------------------------------


class FakeSolid:
    def __init__(self, handle, volume, kind="AcDb3dSolid"):
        self.Handle, self.Volume, self.ObjectName = handle, volume, kind
        self.cut = []

    def Boolean(self, code, other):
        self.cut.append((code, other.Handle))
        self.Volume -= other.Volume

    def GetBoundingBox(self):
        return (0.0, 0.0, 0.0), (1.0, 1.0, 1.0)


class FakeViewport:
    Direction = None


class FakeApp:
    def ZoomExtents(self):
        pass


class Fake3dDoc:
    def __init__(self, *entities):
        self.by_handle = {e.Handle: e for e in entities}
        self.ActiveViewport = FakeViewport()
        self.Application = FakeApp()
        self.sent: list[str] = []
        self.set_variables: list[tuple[str, object]] = []

    def HandleToObject(self, handle):
        return self.by_handle[handle]

    def SendCommand(self, text):
        self.sent.append(text)

    def SetVariable(self, name, value):
        # VSCURRENT is a command, not a system variable: AutoCAD 2027 refuses it.
        if name == "VSCURRENT":
            raise ValueError("Error setting system variable")
        self.set_variables.append((name, value))

    def GetVariable(self, name):
        raise ValueError(f"no system variable {name}")

    def Regen(self, which):
        pass

    def StartUndoMark(self):
        pass

    def EndUndoMark(self):
        pass


def _patch(monkeypatch, doc):
    from autocad_mcp.tools import solids

    async def run(fn):
        return fn()

    monkeypatch.setattr(solids, "run", run)
    monkeypatch.setattr(solids, "get_doc", lambda: doc)
    monkeypatch.setattr(solids, "require_idle", lambda d: None)


def test_a_real_3d_solid_is_called_a_3dsolid():
    """AutoCAD names a 3D solid AcDb3dSolid; with no entry it was never matched as one."""
    from autocad_mcp.acad.entities import short_type

    assert short_type(FakeSolid("2E1", 1.0)) == "3dsolid"


def test_boolean_takes_real_solids(monkeypatch):
    """2026-10-28: '2E1 is a AcDb3dSolid, not a 3D solid or a region'."""
    import asyncio
    import json

    from autocad_mcp.tools import solids

    plate, hole = FakeSolid("2E1", 1000.0), FakeSolid("2E2", 100.0)
    _patch(monkeypatch, Fake3dDoc(plate, hole))
    answer = asyncio.run(solids.autocad_solid_boolean(operation="subtract", handle="2E1", others=["2E2"]))
    assert not answer.startswith("Error"), answer
    result = json.loads(answer)
    assert result["consumed"] == ["2E2"]
    assert result["volume_after"] == pytest.approx(900.0)


def test_boolean_still_refuses_a_line_before_consuming_anything(monkeypatch):
    import asyncio

    from autocad_mcp.tools import solids

    plate, line = FakeSolid("2E1", 1000.0), FakeSolid("2E3", 0.0, kind="AcDbLine")
    _patch(monkeypatch, Fake3dDoc(plate, line))
    answer = asyncio.run(solids.autocad_solid_boolean(operation="subtract", handle="2E1", others=["2E3"]))
    assert answer.startswith("Error") and "2E3 is a line" in answer
    assert plate.cut == []


@pytest.mark.parametrize("style", VISUAL_STYLES)
def test_every_visual_style_has_a_vscurrent_option(style):
    from autocad_mcp.tools.solids import VISUAL_STYLE_OPTIONS

    assert VISUAL_STYLE_OPTIONS[style].startswith("_")


def test_the_visual_style_is_set_with_the_vscurrent_command(monkeypatch):
    """2026-10-28: 'not_set: visual_style (Error setting system variable)' — VSCURRENT is a command."""
    import asyncio
    import json

    from autocad_mcp.tools import solids

    doc = Fake3dDoc()
    _patch(monkeypatch, doc)
    answer = asyncio.run(solids.autocad_set_3d_view(visual_style="realistic", zoom_extents=False))
    result = json.loads(answer)
    assert "not_set" not in result, result
    assert doc.sent == ["_.VSCURRENT _Realistic\n"]
    assert result["visual_style"] == "realistic"


def test_a_visual_style_option_autocad_does_not_take_is_cancelled_and_reported(monkeypatch):
    """If VSCURRENT is still asking after its answer, it must not be left waiting for the next tool."""
    import asyncio
    import json

    from autocad_mcp.tools import solids

    class StillAsking(Fake3dDoc):
        def GetVariable(self, name):
            if name == "CMDACTIVE":
                return 0 if self.sent and self.sent[-1].startswith("\x1b") else 1
            return super().GetVariable(name)

    monkeypatch.setattr(solids, "VSCURRENT_WAIT_S", 0.05)
    monkeypatch.setattr(solids, "VSCURRENT_POLL_S", 0.0)
    doc = StillAsking()
    _patch(monkeypatch, doc)
    result = json.loads(asyncio.run(solids.autocad_set_3d_view(visual_style="shaded with edges", zoom_extents=False)))
    assert doc.sent[-1].startswith("\x1b")
    assert any("visual_style" in item for item in result["not_set"]), result


def test_a_visual_style_that_takes_a_moment_is_not_cancelled(monkeypatch):
    """CMDACTIVE can still read 1 just after SendCommand while VSCURRENT finishes; that is not a refusal."""
    import asyncio
    import json

    from autocad_mcp.tools import solids

    class Finishing(Fake3dDoc):
        reads = 0

        def GetVariable(self, name):
            if name == "CMDACTIVE":
                self.reads += 1
                return 1 if self.reads < 3 else 0
            return super().GetVariable(name)

    monkeypatch.setattr(solids, "VSCURRENT_POLL_S", 0.0)
    doc = Finishing()
    _patch(monkeypatch, doc)
    result = json.loads(asyncio.run(solids.autocad_set_3d_view(visual_style="hidden", zoom_extents=False)))
    assert "not_set" not in result, result
    assert doc.sent == ["_.VSCURRENT _Hidden\n"]
