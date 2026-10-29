"""Splines, multilines and wipeouts (no AutoCAD).

Each tool is run against a fake drawing that records what AutoCAD would be
sent: the arithmetic (tangents, vertex lists, typed command lines) is what can
be got wrong without AutoCAD noticing.
"""

from __future__ import annotations

import asyncio
import json
import math

import pytest

from autocad_mcp.core.risk import Risk, risk_of
from autocad_mcp.tools import drafting
from autocad_mcp.tools.drafting import spline_tangents


class Entity:
    """A made object: answers the reads created_payload makes."""

    def __init__(self, kind, handle="2C0"):
        self.ObjectName, self.Handle, self.Layer = kind, handle, "0"
        self.Document = self
        self.written = {}

    def HandleToObject(self, handle):
        return self

    def __setattr__(self, name, value):
        if name[0].isupper() and name not in ("ObjectName", "Handle", "Layer", "Document"):
            self.__dict__.setdefault("written", {})[name] = value
        object.__setattr__(self, name, value)


class Space:
    def __init__(self):
        self.calls = []
        self.items = []

    def AddSpline(self, points, start, end):
        self.calls.append(("AddSpline", tuple(points.value), tuple(start.value), tuple(end.value)))
        return Entity("AcDbSpline")

    def AddMLine(self, points):
        self.calls.append(("AddMLine", tuple(points.value)))
        return Entity("AcDbMline")

    @property
    def Count(self):
        return len(self.items)

    def Item(self, index):
        return self.items[index]


class Doc:
    def __init__(self, **variables):
        self.ModelSpace = self.PaperSpace = Space()
        self.variables = {"UCSORG": (0.0, 0.0, 0.0), "UCSXDIR": (1.0, 0.0, 0.0),
                          "UCSYDIR": (0.0, 1.0, 0.0), "CMLSTYLE": "Standard", "CMDACTIVE": 0}
        self.variables.update(variables)
        self.set_calls = []
        self.sent = []

    def GetVariable(self, name):
        return self.variables[name]

    def SetVariable(self, name, value):
        self.set_calls.append((name, value))
        self.variables[name] = value

    def SendCommand(self, text):
        self.sent.append(text)

    def StartUndoMark(self):
        pass

    def EndUndoMark(self):
        pass


@pytest.fixture
def doc(monkeypatch):
    fake = Doc()

    async def run(fn):
        return fn()

    monkeypatch.setattr(drafting, "run", run)
    monkeypatch.setattr(drafting, "get_doc", lambda: fake)
    monkeypatch.setattr(drafting, "require_idle", lambda d: None)
    monkeypatch.setattr(drafting, "apply_properties", lambda *a, **k: {})
    return fake


def call(coro):
    answer = asyncio.run(coro)
    assert not answer.startswith("Error"), answer
    return json.loads(answer)


# ---------------------------------------------------------------------------
# Spline
# ---------------------------------------------------------------------------


class TestSplineTangents:
    def test_by_default_they_follow_the_first_and_last_segments(self):
        start, end = spline_tangents([(0, 0, 0), (10, 0, 0), (10, 10, 0)])
        assert start == pytest.approx((1.0, 0.0, 0.0))
        assert end == pytest.approx((0.0, 1.0, 0.0))

    def test_they_are_never_a_zero_vector(self):
        """AutoCAD's reference does not say what a zero tangent does, so none is ever sent."""
        start, end = spline_tangents([(0, 0, 0), (0, 0, 0), (5, 0, 0), (5, 0, 0)])
        assert start == pytest.approx((1.0, 0.0, 0.0)) and end == pytest.approx((1.0, 0.0, 0.0))

    def test_given_tangents_are_kept_but_made_unit_length(self):
        start, end = spline_tangents([(0, 0, 0), (10, 0, 0)], (0, 5, 0), (3, 4, 0))
        assert start == pytest.approx((0.0, 1.0, 0.0)) and end == pytest.approx((0.6, 0.8, 0.0))

    def test_refusals(self):
        with pytest.raises(ValueError, match="at least two"):
            spline_tangents([(0, 0, 0)])
        with pytest.raises(ValueError, match="all at one place"):
            spline_tangents([(1, 1, 0), (1, 1, 0)])
        with pytest.raises(ValueError, match="cannot be all zeros"):
            spline_tangents([(0, 0, 0), (10, 0, 0)], (0, 0, 0))


def test_a_spline_goes_through_its_fit_points(doc):
    out = call(drafting.autocad_draw_spline(points=[[0, 0], [1000, 500], [2000, 0]]))
    (name, flat, start, end), = doc.ModelSpace.calls
    assert flat == (0.0, 0.0, 0.0, 1000.0, 500.0, 0.0, 2000.0, 0.0, 0.0)
    assert start == pytest.approx((2 / math.sqrt(5), 1 / math.sqrt(5), 0.0))
    assert end == pytest.approx((2 / math.sqrt(5), -1 / math.sqrt(5), 0.0))
    assert out["type"] == "spline" and out["fit_points"] == 3


def test_a_closed_spline_is_closed(doc):
    out = call(drafting.autocad_draw_spline(points=[[0, 0], [1000, 0], [500, 800]], closed=True))
    assert out["closed"] is True and "not_set" not in out


def test_a_closed_spline_needs_three_points(doc):
    answer = asyncio.run(drafting.autocad_draw_spline(points=[[0, 0], [1000, 0]], closed=True))
    assert answer.startswith("Error") and "three" in answer


def test_a_spline_in_a_turned_ucs_turns_its_points_and_tangents(monkeypatch, doc):
    doc.variables.update({"UCSXDIR": (0.0, 1.0, 0.0), "UCSYDIR": (-1.0, 0.0, 0.0)})
    call(drafting.autocad_draw_spline(points=[[0, 0], [100, 0]], start_tangent=[1, 0, 0], coords="ucs"))
    (_, flat, start, _), = doc.ModelSpace.calls
    assert flat[3:5] == pytest.approx((0.0, 100.0))
    assert start == pytest.approx((0.0, 1.0, 0.0))


def test_levels():
    assert risk_of("autocad_draw_spline") is Risk.CHANGE


# ---------------------------------------------------------------------------
# Multiline
# ---------------------------------------------------------------------------


class StyledDoc(Doc):
    """A drawing that has the multiline styles named, and refuses any other."""

    styles = {"STANDARD", "WALL-200"}

    def SetVariable(self, name, value):
        if name == "CMLSTYLE" and str(value).upper() not in self.styles:
            raise ValueError("Error setting system variable")
        super().SetVariable(name, value)


@pytest.fixture
def mdoc(monkeypatch):
    fake = StyledDoc()

    async def run(fn):
        return fn()

    monkeypatch.setattr(drafting, "run", run)
    monkeypatch.setattr(drafting, "get_doc", lambda: fake)
    monkeypatch.setattr(drafting, "require_idle", lambda d: None)
    monkeypatch.setattr(drafting, "apply_properties", lambda *a, **k: {})
    return fake


def test_a_wall_is_a_multiline_through_its_points_at_its_thickness(mdoc):
    """The STANDARD style is one unit wide, so the scale is the wall thickness."""
    out = call(drafting.autocad_draw_multiline(points=[[0, 0], [5000, 0], [5000, 3000]], scale=200))
    (_, flat), = mdoc.ModelSpace.calls
    assert flat == (0.0, 0.0, 0.0, 5000.0, 0.0, 0.0, 5000.0, 3000.0, 0.0)
    assert out["type"] == "multiline"


@pytest.mark.parametrize(("justification", "code"), [("top", 0), ("zero", 1), ("centre", 1), ("bottom", 2)])
def test_justification_is_autocads_code(mdoc, monkeypatch, justification, code):
    made = []
    original = mdoc.ModelSpace.AddMLine

    def add(points):
        entity = original(points)
        made.append(entity)
        return entity

    monkeypatch.setattr(mdoc.ModelSpace, "AddMLine", add)
    call(drafting.autocad_draw_multiline(points=[[0, 0], [1000, 0]], justification=justification, scale=100))
    assert made[0].written["Justification"] == code
    assert made[0].written["MLineScale"] == 100.0


def test_a_style_is_used_and_the_drawings_own_is_put_back(mdoc):
    call(drafting.autocad_draw_multiline(points=[[0, 0], [1000, 0]], style="WALL-200"))
    assert ("CMLSTYLE", "WALL-200") in mdoc.set_calls
    assert mdoc.variables["CMLSTYLE"] == "Standard"


def test_a_style_the_drawing_lacks_is_refused_before_drawing(mdoc):
    answer = asyncio.run(drafting.autocad_draw_multiline(points=[[0, 0], [1000, 0]], style="NOPE"))
    assert answer.startswith("Error") and "MLSTYLE" in answer
    assert mdoc.ModelSpace.calls == []


def test_a_closed_multiline_comes_back_to_its_start_and_says_the_corner_is_not_mitred(mdoc):
    out = call(drafting.autocad_draw_multiline(points=[[0, 0], [4000, 0], [4000, 3000], [0, 3000]], closed=True))
    (_, flat), = mdoc.ModelSpace.calls
    assert flat[-3:] == (0.0, 0.0, 0.0) and len(flat) == 15
    assert "mitre" in out["warning"]


def test_multiline_level():
    assert risk_of("autocad_draw_multiline") is Risk.CHANGE


# ---------------------------------------------------------------------------
# Wipeout
# ---------------------------------------------------------------------------


class Outline(Entity):
    def __init__(self, flat, bulges=None, closed=True):
        super().__init__("AcDbPolyline", "2D1")
        self.Coordinates, self.Closed = tuple(flat), closed
        self._bulges = bulges or [0.0] * (len(flat) // 2)
        self.deleted = False

    def GetBulge(self, i):
        return self._bulges[i]

    def Delete(self):
        self.deleted = True


class WipeoutDoc(Doc):
    """Typing WIPEOUT makes a wipeout in the current space, as AutoCAD does; or, stuck, makes nothing."""

    ActiveSpace = 1

    def __init__(self, takes=True, outline=None):
        super().__init__()
        self.takes, self.outline = takes, outline

    def HandleToObject(self, handle):
        return self.outline

    def SendCommand(self, text):
        super().SendCommand(text)
        if text.startswith("_.WIPEOUT"):
            if self.takes:
                self.ModelSpace.items.append(Entity("AcDbWipeout", "2E9"))
            else:
                self.variables["CMDACTIVE"] = 1
        elif text.startswith("\x1b"):
            self.variables["CMDACTIVE"] = 0


def _wipe(monkeypatch, fake):
    async def run(fn):
        return fn()

    monkeypatch.setattr(drafting, "run", run)
    monkeypatch.setattr(drafting, "get_doc", lambda: fake)
    monkeypatch.setattr(drafting, "require_idle", lambda d: None)
    monkeypatch.setattr(drafting, "apply_properties", lambda *a, **k: {})
    monkeypatch.setattr(drafting, "COMMAND_WAIT_S", 0.05)
    monkeypatch.setattr(drafting, "COMMAND_POLL_S", 0.0)
    return fake


class TestWipeoutCommand:
    def test_every_point_is_world_and_unsnapped(self):
        """'*' takes the point in world coordinates whatever the UCS; '_non' keeps a running snap off it."""
        typed = drafting.wipeout_command([[0, 0], [1200, 0], [1200, 450.5], [0, 450.5]])
        assert typed == "_.WIPEOUT\n_non *0,0\n_non *1200,0\n_non *1200,450.5\n_non *0,450.5\n\n"

    def test_a_repeated_closing_point_is_dropped(self):
        assert drafting.wipeout_command([[0, 0], [10, 0], [10, 10], [0, 0]]).count("_non") == 3

    @pytest.mark.parametrize("points", [[[0, 0], [10, 0]], [[0, 0], [10, 0], [20, 0]]])
    def test_an_outline_with_no_area_is_refused(self, points):
        with pytest.raises(ValueError):
            drafting.wipeout_command(points)


def test_a_wipeout_from_points(monkeypatch):
    fake = _wipe(monkeypatch, WipeoutDoc())
    out = call(drafting.autocad_add_wipeout(points=[[0, 0], [1200, 0], [1200, 450], [0, 450]]))
    assert out["type"] == "wipeout" and out["handle"] == "2E9"
    assert fake.sent[0].startswith("_.WIPEOUT\n_non *0,0\n")


def test_a_wipeout_from_a_closed_polyline_can_take_its_place(monkeypatch):
    outline = Outline([0, 0, 500, 0, 500, 300, 0, 300])
    fake = _wipe(monkeypatch, WipeoutDoc(outline=outline))
    call(drafting.autocad_add_wipeout(boundary_handle="2D1", erase_boundary=True))
    assert "_non *500,300\n" in fake.sent[0]
    assert outline.deleted


def test_a_curved_boundary_is_refused_because_wipeout_edges_are_straight(monkeypatch):
    outline = Outline([0, 0, 500, 0, 500, 300, 0, 300], bulges=[0.0, 0.5, 0.0, 0.0])
    fake = _wipe(monkeypatch, WipeoutDoc(outline=outline))
    answer = asyncio.run(drafting.autocad_add_wipeout(boundary_handle="2D1"))
    assert answer.startswith("Error") and "straight" in answer
    assert fake.sent == []


def test_frames_set_wipeoutframe(monkeypatch):
    fake = _wipe(monkeypatch, WipeoutDoc())
    call(drafting.autocad_add_wipeout(points=[[0, 0], [10, 0], [10, 10]], frames="hide"))
    assert ("WIPEOUTFRAME", 0) in fake.set_calls


def test_a_wipeout_autocad_does_not_take_is_cancelled_and_reported(monkeypatch):
    fake = _wipe(monkeypatch, WipeoutDoc(takes=False))
    answer = asyncio.run(drafting.autocad_add_wipeout(points=[[0, 0], [10, 0], [10, 10]]))
    assert answer.startswith("Error") and "wipeout" in answer.lower()
    assert fake.sent[-1].startswith("\x1b")


def test_wipeout_level():
    assert risk_of("autocad_add_wipeout") is Risk.CHANGE


# ---------------------------------------------------------------------------
# Review fixes (2026-10-28): spaces, flipped outlines, slow commands, numbers
# ---------------------------------------------------------------------------


class TwoSpaceDoc(WipeoutDoc):
    """Model and paper space apart, as in a real drawing; WIPEOUT draws where the work is."""

    def __init__(self, active_space=1, mspace=False, outline=None, appear_after=0):
        super().__init__(outline=outline)
        self.ModelSpace, self.PaperSpace = Space(), Space()
        self.ModelSpace.ObjectID, self.PaperSpace.ObjectID = 11, 22
        self.ActiveSpace, self.MSpace = active_space, mspace
        self.appear_after, self.reads = appear_after, 0

    def SendCommand(self, text):
        self.sent.append(text)
        if text.startswith("_.WIPEOUT"):
            working = self.ModelSpace if (self.ActiveSpace == 1 or self.MSpace) else self.PaperSpace
            self.pending = working

    def _maybe_appear(self):
        pending = getattr(self, "pending", None)
        if pending is not None:
            self.reads += 1
            if self.reads > self.appear_after:
                pending.items.append(Entity("AcDbWipeout", "2EA"))
                self.pending = None


class CountingSpace(Space):
    def __init__(self, doc):
        super().__init__()
        self.doc = doc

    @property
    def Count(self):
        self.doc._maybe_appear()
        return len(self.items)


def _two(monkeypatch, **kwargs):
    fake = TwoSpaceDoc(**kwargs)
    fake.ModelSpace, fake.PaperSpace = CountingSpace(fake), CountingSpace(fake)
    fake.ModelSpace.ObjectID, fake.PaperSpace.ObjectID = 11, 22
    return _wipe(monkeypatch, fake)


SQUARE = [[0, 0], [10, 0], [10, 10], [0, 10]]


def test_a_wipeout_made_inside_a_layout_viewport_is_found_in_model_space(monkeypatch):
    """In a layout with a viewport active, ActiveSpace says paper but WIPEOUT draws in model space."""
    fake = _two(monkeypatch, active_space=0, mspace=True)
    out = call(drafting.autocad_add_wipeout(points=SQUARE))
    assert out["handle"] == "2EA" and fake.ModelSpace.items and not fake.PaperSpace.items


def test_a_boundary_in_the_other_space_is_refused(monkeypatch):
    outline = Outline([0, 0, 500, 0, 500, 300, 0, 300])
    outline.OwnerID = 11  # in model space, while a layout is current
    fake = _two(monkeypatch, active_space=0, outline=outline)
    answer = asyncio.run(drafting.autocad_add_wipeout(boundary_handle="2D1", erase_boundary=True))
    assert answer.startswith("Error") and "space" in answer
    assert fake.sent == [] and not outline.deleted


def test_a_flipped_polyline_is_refused_because_its_corners_would_mirror(monkeypatch):
    """LWPOLYLINE corners are in its own plane; with its normal down they read mirrored in X."""
    outline = Outline([0, 0, 500, 0, 500, 300, 0, 300])
    outline.Normal = (0.0, 0.0, -1.0)
    fake = _two(monkeypatch, outline=outline)
    answer = asyncio.run(drafting.autocad_add_wipeout(boundary_handle="2D1"))
    assert answer.startswith("Error") and "flipped" in answer and fake.sent == []


def test_a_wipeout_that_appears_a_moment_late_is_still_found(monkeypatch):
    fake = _two(monkeypatch, appear_after=3)
    out = call(drafting.autocad_add_wipeout(points=SQUARE))
    assert out["handle"] == "2EA" and not any(s.startswith("\x1b") for s in fake.sent)


def test_a_wipeout_that_never_appears_is_cancelled_too(monkeypatch):
    fake = _two(monkeypatch, appear_after=10**6)
    answer = asyncio.run(drafting.autocad_add_wipeout(points=SQUARE))
    assert answer.startswith("Error") and fake.sent[-1].startswith("\x1b")


@pytest.mark.parametrize(("value", "typed"), [(123456789.123456, "123456789.123456"), (1.4e-14, "0"),
                                             (-0.0, "0"), (2500.5, "2500.5"), (-12.25, "-12.25")])
def test_numbers_are_typed_in_full_and_never_with_an_exponent(value, typed):
    assert drafting._num(value) == typed


class LoggedDoc(StyledDoc):
    def __init__(self):
        super().__init__()
        self.log = []

    def StartUndoMark(self):
        self.log.append("start")

    def EndUndoMark(self):
        self.log.append("end")

    def SetVariable(self, name, value):
        super().SetVariable(name, value)
        self.log.append(("set", name, value))


def test_the_multiline_style_is_put_back_inside_the_same_undo_step(monkeypatch):
    fake = LoggedDoc()
    _wipe(monkeypatch, fake)
    call(drafting.autocad_draw_multiline(points=[[0, 0], [1000, 0]], style="WALL-200"))
    assert fake.log.index(("set", "CMLSTYLE", "Standard")) < fake.log.index("end")


def test_a_multiline_style_is_not_changed_when_the_current_one_cannot_be_read(monkeypatch):
    fake = StyledDoc()
    del fake.variables["CMLSTYLE"]
    _wipe(monkeypatch, fake)
    answer = asyncio.run(drafting.autocad_draw_multiline(points=[[0, 0], [1000, 0]], style="WALL-200"))
    assert answer.startswith("Error") and fake.set_calls == [] and fake.ModelSpace.calls == []


def test_a_closed_multiline_given_its_closing_point_does_not_double_it(mdoc):
    call(drafting.autocad_draw_multiline(points=[[0, 0], [4000, 0], [4000, 3000], [0, 0]], closed=True))
    (_, flat), = mdoc.ModelSpace.calls
    assert len(flat) == 12  # three corners and the way back, not a zero-length last leg


def test_a_closed_spline_given_its_closing_point_does_not_double_it(doc):
    call(drafting.autocad_draw_spline(points=[[0, 0], [1000, 0], [500, 800], [0, 0]], closed=True))
    (_, flat, _, _), = doc.ModelSpace.calls
    assert len(flat) == 9


def test_a_multilines_own_warning_does_not_hide_the_read_back_one(monkeypatch, mdoc):
    def unreadable(entity, notes, **extra):
        return {"created": True, "handle": "2C0", "type": "multiline", "layer": "0",
                "verified": False, "warning": "could not be read back"}

    monkeypatch.setattr(drafting, "created_payload", unreadable)
    out = call(drafting.autocad_draw_multiline(points=[[0, 0], [10, 0], [10, 10]], closed=True))
    assert "read back" in out["warning"] and "mitre" in out["warning"]
