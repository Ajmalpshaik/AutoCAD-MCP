"""Tests that need a running AutoCAD with at least one drawing open.

Run them explicitly:

    .venv\\Scripts\\python.exe -m pytest -m live

Each test works in a throwaway drawing that it closes without saving, so the
drawing the user has open is never plotted or changed.

AutoCAD rejects calls for a moment while it opens or closes a drawing. The
retry loop absorbs that, but pytest's faulthandler still prints each rejection
as "Windows fatal exception: code 0x80010001"; add -p no:faulthandler to
silence it.
"""

from __future__ import annotations

import json

import pytest

from autocad_mcp.core.connection import get_app, run
from autocad_mcp.core.variants import apoint
from autocad_mcp.tools.document import autocad_export

pytestmark = pytest.mark.live


@pytest.fixture
async def scratch():
    """A new drawing with some geometry, made active for the test."""
    held = {}

    def open_scratch():
        app = get_app()
        held["original"] = app.ActiveDocument if app.Documents.Count else None
        doc = app.Documents.Add()
        doc.ModelSpace.AddLine(apoint(0, 0), apoint(4200, 2970))
        doc.ModelSpace.AddCircle(apoint(2100, 1485), 500)
        held["doc"] = doc

    def close_scratch():
        held["doc"].Close(False)
        if held["original"] is not None:
            held["original"].Activate()

    await run(open_scratch)
    yield held["doc"]
    await run(close_scratch)


def _page_setup(doc):
    layout = doc.ActiveLayout
    return (
        str(layout.Name),
        str(layout.ConfigName),
        str(layout.CanonicalMediaName),
        int(layout.PlotType),
    )


async def _export(path, **kwargs):
    raw = await autocad_export(path=str(path), **kwargs)
    assert not raw.startswith("Error"), raw
    return json.loads(raw)


async def test_model_space_exports_to_pdf(scratch, tmp_path):
    target = tmp_path / "model.pdf"
    before = await run(lambda: _page_setup(scratch))

    result = await _export(target)

    assert target.read_bytes().startswith(b"%PDF")
    assert result["size_bytes"] == target.stat().st_size
    assert result["layout"] == "Model"
    # The export must not leave the layout set up for the PDF plotter.
    after = await run(lambda: _page_setup(scratch))
    assert after == before


async def test_paper_size_is_used(scratch, tmp_path):
    target = tmp_path / "a3.pdf"
    result = await _export(target, paper_size="A3")
    assert target.read_bytes().startswith(b"%PDF")
    assert result["paper"] == "ISO full bleed A3 (420.00 x 297.00 MM)"


async def test_paper_space_layout_exports_to_pdf(scratch, tmp_path):
    def to_layout():
        scratch.ActiveLayout = scratch.Layouts.Item("Layout1")
        return _page_setup(scratch)

    before = await run(to_layout)
    target = tmp_path / "layout1.pdf"

    result = await _export(target, paper_size="A1")

    assert target.read_bytes().startswith(b"%PDF")
    assert result["layout"] == "Layout1"
    assert await run(lambda: _page_setup(scratch)) == before


async def test_overwrites_an_earlier_export(scratch, tmp_path):
    target = tmp_path / "again.pdf"
    target.write_bytes(b"%PDF old")
    await _export(target)
    assert target.read_bytes() != b"%PDF old"
