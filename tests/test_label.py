"""autocad_add_label: Ajmal's TLD leader rules (TextLeader_V4.lsp), plus an MLEADER option."""

from __future__ import annotations

import asyncio
import json

import pytest

from autocad_mcp.tools import labels
from autocad_mcp.tools.labels import Frame, leader_points, underline_level

# Text box: left 0, right 1000, top 500, height 25, one line spacing.
F = Frame(left=0.0, right=1000.0, top=500.0, height=25.0, spacing=1.0)


def test_underline_sits_between_line_one_and_two():
    # TLD: yU = top - h - (pitch - h) / 2, pitch = h * spacing * 5/3
    assert underline_level(F) == pytest.approx(500 - 25 - (25 * 5 / 3 - 25) / 2)


def test_l_shape_goes_square_then_under_the_whole_text_to_the_far_end():
    yu = underline_level(F)
    pts = leader_points(F, arrow=(1300.0, 200.0), shape="L", extension=0.5)
    # arrow right of the text: far end is the LEFT end, extended by 0.5 x h
    assert pts == [(1300.0, 200.0), (1300.0, yu), (-12.5, yu)]


def test_angled_goes_to_the_near_end_then_under_the_text():
    yu = underline_level(F)
    pts = leader_points(F, arrow=(1300.0, 200.0), shape="angled", extension=0.5)
    assert pts == [(1300.0, 200.0), (1012.5, yu), (-12.5, yu)]


def test_arrow_already_on_the_underline_gives_a_straight_leader():
    yu = underline_level(F)
    pts = leader_points(F, arrow=(1300.0, yu), shape="L", extension=0.5)
    assert pts == [(1300.0, yu), (-12.5, yu)]


def test_arrow_left_of_the_text_runs_to_the_right_end():
    yu = underline_level(F)
    pts = leader_points(F, arrow=(-400.0, 100.0), shape="angled", extension=0.5)
    assert pts == [(-400.0, 100.0), (-12.5, yu), (1012.5, yu)]


def test_unknown_shape_is_refused():
    with pytest.raises(labels.AutocadError, match="shape"):
        leader_points(F, arrow=(0.0, 0.0), shape="curvy", extension=0.5)


class FakeText:
    def __init__(self):
        self.Handle, self.ObjectName, self.Layer = "2A", "AcDbMText", "0"
        self.Height, self.LineSpacingFactor, self.AttachmentPoint = 2.5, 1.0, 1
        self.Document = None

    def GetBoundingBox(self):
        return (0.0, 475.0, 0.0), (1000.0, 500.0, 0.0)


class FakeLeader:
    def __init__(self, pts):
        self.pts, self.Handle, self.ObjectName, self.Layer, self.ScaleFactor = pts, "2B", "AcDbLeader", "0", 1.0
        self.Document = None


class FakeMLeader:
    def __init__(self, pts):
        self.pts, self.Handle, self.ObjectName, self.Layer = pts, "2C", "AcDbMLeader", "0"
        self.TextString, self.ContentType, self.Document = "", 0, None


class FakeSpace:
    def __init__(self):
        self.made = []

    def AddMText(self, p, w, s):
        t = FakeText()
        t.text, t.width = s, w
        self.made.append(t)
        return t

    def AddLeader(self, pts, annotation, kind):
        lead = FakeLeader(list(getattr(pts, 'value', pts)))
        lead.kind = kind
        self.made.append(lead)
        return lead

    def AddMLeader(self, pts, index):
        m = FakeMLeader(list(getattr(pts, 'value', pts)))
        self.made.append(m)
        return m, 0


class FakeDoc:
    def __init__(self):
        self.ModelSpace = FakeSpace()
        self.vars = {"DIMSCALE": 10.0, "CMDACTIVE": 0}

    def GetVariable(self, name):
        return self.vars[name]

    def StartUndoMark(self):
        pass

    def EndUndoMark(self):
        pass


@pytest.fixture
def doc(monkeypatch):
    fake = FakeDoc()

    async def run(fn):
        return fn()

    monkeypatch.setattr(labels, "run", run)
    monkeypatch.setattr(labels, "get_doc", lambda: fake)
    monkeypatch.setattr(labels, "apply_properties", lambda d, e, layer, aci, lt: {})
    monkeypatch.setattr(labels, "require_idle", lambda d: None)
    monkeypatch.setattr(labels, "get_space", lambda d, s: d.ModelSpace)
    return fake


def test_leader_kind_makes_mtext_and_a_leader_with_the_dimscale(doc):
    result = json.loads(asyncio.run(labels.autocad_add_label(
        text="DN100 PIPE", arrow=[1300, 200], position=[0, 500], height=25, shape="angled")))
    text, lead = doc.ModelSpace.made
    assert text.text == "DN100 PIPE" and text.Height == 25
    assert lead.ScaleFactor == 10.0          # arrow sized like the dimensions
    assert lead.Layer == text.Layer          # TLD: leader on the text's layer
    assert len(lead.pts) == 9                # 3 points x (x, y, z)
    # AcLeaderType: 0 line no arrow, 1 SPLINE no arrow, 2 line WITH arrow (live:
    # 1 drew curved leaders without arrows, 2026-10-26)
    assert lead.kind == 2
    assert result["kind"] == "leader" and result["text_handle"] == "2A" and result["leader_handle"] == "2B"


def test_mleader_kind_makes_one_multileader(doc):
    result = json.loads(asyncio.run(labels.autocad_add_label(
        text="DN100 PIPE", arrow=[1300, 200], position=[0, 500], height=25, kind="mleader")))
    (m,) = doc.ModelSpace.made
    assert m.TextString == "DN100 PIPE"
    assert len(m.pts) == 6                   # arrow + landing
    assert result["kind"] == "mleader"


def test_label_is_a_change_level_tool():
    from autocad_mcp.core.risk import Risk, risk_of

    assert risk_of("autocad_add_label") is Risk.CHANGE


class FakeDim:
    def __init__(self):
        self.Handle, self.ObjectName, self.Layer, self.ScaleFactor, self.Document = "3A", "AcDbRotatedDimension", "0", 1.0, None
        self.Measurement = 400.0


def test_dimensions_take_dimscale_like_labels(monkeypatch):
    # Live 2026-10-26: COM-made dimensions ignored DIMSCALE, so text and arrows
    # came out 2.5 mm in a 1:10 detail.
    from autocad_mcp.tools import draw

    fake, dim = FakeDoc(), FakeDim()
    fake.ModelSpace.AddDimRotated = lambda p1, p2, t, a: dim

    async def run(fn):
        return fn()

    monkeypatch.setattr(draw, "run", run)
    monkeypatch.setattr(draw, "get_doc", lambda: fake)
    monkeypatch.setattr(draw, "require_idle", lambda d: None)
    monkeypatch.setattr(draw, "get_space", lambda d, s: d.ModelSpace)
    monkeypatch.setattr(draw, "apply_properties", lambda d, e, layer, aci, lt: {})
    monkeypatch.setattr(draw, "describe", lambda e, include_geometry=True: {"type": "dimension", "measurement": 400.0})
    monkeypatch.setattr(draw, "created_payload", lambda e, notes, **kw: {"created": True, "handle": e.Handle, **kw})
    asyncio.run(draw.autocad_add_dimension(dimension_type="horizontal", point1=[0, 0], point2=[400, 0], text_position=[200, -50]))
    assert dim.ScaleFactor == 10.0
