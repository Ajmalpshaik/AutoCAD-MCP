"""autocad_batch_labels: many TLD labels in one AutoCAD call and one undo step."""

from __future__ import annotations

import asyncio
import json

import pytest
from test_label import FakeDoc

from autocad_mcp.tools import labels
from autocad_mcp.tools.labels import leaders_crossing


class CountingDoc(FakeDoc):
    def __init__(self):
        super().__init__()
        self.undo_marks = 0

    def StartUndoMark(self):
        self.undo_marks += 1


@pytest.fixture
def doc(monkeypatch):
    fake = CountingDoc()
    calls = []

    async def run(fn):
        calls.append(fn)
        return fn()

    monkeypatch.setattr(labels, "run", run)
    monkeypatch.setattr(labels, "get_doc", lambda: fake)
    monkeypatch.setattr(labels, "apply_properties", lambda d, e, layer, aci, lt: {})
    monkeypatch.setattr(labels, "require_idle", lambda d: None)
    monkeypatch.setattr(labels, "get_space", lambda d, s: d.ModelSpace)
    fake.calls = calls
    return fake


def batch(**kw):
    return json.loads(asyncio.run(labels.autocad_batch_labels(**kw)))


THREE = [
    {"text": "POLE CAP", "arrow": [40, 6015], "position": [1100, 6300]},
    {"text": "BRACKET", "arrow": [250, 5780], "position": [1100, 6100]},
    {"text": "CAMERA", "arrow": [524, 5660], "position": [1100, 5900]},
]


def test_all_labels_go_in_one_call_and_one_undo_step(doc):
    result = batch(labels=THREE, height=62.5)
    assert len(doc.calls) == 1               # one trip to AutoCAD, not three
    assert doc.undo_marks == 1               # one Ctrl+Z removes the lot
    texts = [e for e in doc.ModelSpace.made if e.ObjectName == "AcDbMText"]
    assert [t.text for t in texts] == ["POLE CAP", "BRACKET", "CAMERA"]
    assert all(t.Height == 62.5 for t in texts)
    assert result["created"] == 3 and len(result["labels"]) == 3


def test_a_label_can_override_the_shared_settings(doc):
    items = [dict(THREE[0]), {**THREE[1], "height": 30, "text_align": "right", "shape": "L"}]
    result = batch(labels=items, height=62.5, shape="angled")
    first, second = result["labels"]
    assert first["shape"] == "angled" and second["shape"] == "L"
    texts = [e for e in doc.ModelSpace.made if e.ObjectName == "AcDbMText"]
    assert texts[1].Height == 30 and texts[1].AttachmentPoint == 3


def test_a_bad_label_stops_the_batch_before_anything_is_drawn(doc):
    items = [THREE[0], {"text": "NO ARROW", "position": [0, 0]}]
    out = asyncio.run(labels.autocad_batch_labels(labels=items, height=25))
    assert out.startswith("Error") and "label 1" in out and "arrow" in out
    assert doc.ModelSpace.made == []


def test_arrow_scale_overrides_dimscale(doc):
    # Live 2026-10-26: DIMSCALE was still 10 from a 1:10 detail, so 1:25 labels got small arrows.
    result = batch(labels=THREE, height=62.5, arrow_scale=25)
    leaders = [e for e in doc.ModelSpace.made if e.ObjectName == "AcDbLeader"]
    assert all(lead.ScaleFactor == 25 for lead in leaders)
    assert result["arrow_scale"] == 25


def test_without_arrow_scale_the_arrows_follow_dimscale(doc):
    batch(labels=THREE, height=62.5)
    leaders = [e for e in doc.ModelSpace.made if e.ObjectName == "AcDbLeader"]
    assert all(lead.ScaleFactor == 10.0 for lead in leaders)


def test_crossing_leaders_are_found():
    a = [(0.0, 0.0), (100.0, 100.0), (200.0, 100.0)]
    b = [(0.0, 100.0), (100.0, 0.0), (200.0, 0.0)]
    c = [(0.0, 300.0), (100.0, 400.0)]
    assert leaders_crossing([a, b, c]) == [[0, 1]]


def test_leaders_meeting_only_at_an_end_do_not_count_as_crossing():
    a = [(0.0, 0.0), (100.0, 100.0)]
    b = [(100.0, 100.0), (200.0, 0.0)]
    assert leaders_crossing([a, b]) == []


def test_the_result_reports_crossings(doc, monkeypatch):
    monkeypatch.setattr(labels, "leaders_crossing", lambda pts: [[0, 2]])
    result = batch(labels=THREE, height=62.5)
    assert result["crossing"] == [[0, 2]]


def test_batch_labels_is_a_change_level_tool():
    from autocad_mcp.core.risk import Risk, risk_of

    assert risk_of("autocad_batch_labels") is Risk.CHANGE
