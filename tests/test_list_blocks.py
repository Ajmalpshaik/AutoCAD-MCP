"""autocad_list_blocks counts dynamic blocks by real name and skips nameless definitions.

Live check 2026-10-26 (AutoCAD 2027, sample "Mechanical - Metric.dwg"): two
definitions with a blank name were listed, and a hex nut changed to M6 (its
reference renamed *U44 by AutoCAD) was missing from its block's count.
"""

from __future__ import annotations

import asyncio
import json

import pytest

from autocad_mcp.tools import layers


class Definition:
    def __init__(self, name, dynamic=False):
        self.Name, self.Count, self.IsLayout, self.IsXRef, self.IsDynamicBlock = name, 0, False, False, dynamic


class Ref:
    def __init__(self, name, effective):
        self.Name, self.EffectiveName, self.ObjectName = name, effective, "AcDbBlockReference"


class Blocks:
    def __init__(self, items):
        self.items, self.Count = items, len(items)

    def Item(self, i):
        return self.items[i]


class Doc:
    Blocks = Blocks([
        Definition("*Model_Space"),
        Definition(""),
        Definition("Hex Nut - Metric", dynamic=True),
        Definition("Valve - Metric"),
        Definition("Unused"),
    ])


REFS = [Ref("Hex Nut - Metric", "Hex Nut - Metric"), Ref("*U44", "Hex Nut - Metric"), Ref("Valve - Metric", "Valve - Metric")]


@pytest.fixture
def blocks(monkeypatch):
    async def run(fn):
        return fn()

    monkeypatch.setattr(layers, "run", run)
    monkeypatch.setattr(layers, "get_doc", lambda: Doc())
    monkeypatch.setattr(layers, "select_filtered", lambda *a, **k: REFS)
    monkeypatch.setattr(layers, "iter_selection", lambda sel: iter(sel))
    monkeypatch.setattr(layers, "discard_selection_set", lambda *a, **k: None)

    def call(**kw):
        return {b["name"]: b for b in json.loads(asyncio.run(layers.autocad_list_blocks(**kw)))["blocks"]}

    return call


def test_dynamic_copies_count_under_their_real_name(blocks):
    listed = blocks()
    assert listed["Hex Nut - Metric"]["instances"] == 2
    assert listed["Hex Nut - Metric"]["dynamic"] is True
    assert listed["Valve - Metric"]["instances"] == 1 and listed["Valve - Metric"]["dynamic"] is False


def test_blank_names_and_unused_are_left_out(blocks):
    assert set(blocks()) == {"Hex Nut - Metric", "Valve - Metric"}
    assert set(blocks(include_unused=True)) == {"Hex Nut - Metric", "Valve - Metric", "Unused"}
