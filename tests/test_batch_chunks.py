"""batch_draw sends its AutoLISP as short expressions and never loads a file.

Loading a .lsp from %TEMP% makes AutoCAD's SECURELOAD ask "Unsigned Executable
File" (live check A21, 2026-10-26). Expressions sent to the command line are
not loaded files, so SECURELOAD never applies to them.
"""

from __future__ import annotations

import asyncio
import json
import re

import pytest

from autocad_mcp.acad.lisp import CHUNK_LIMIT, build_chunks, dotted, lisp_string
from autocad_mcp.core.errors import AutocadError
from autocad_mcp.tools import batch

OUT = r"C:\temp\out.txt"


def point(i: float) -> list[str]:
    return [dotted(0, lisp_string("POINT")), dotted(10, f"(list {i}.0 0.0 0.0)")]


def balanced(text: str) -> bool:
    depth = 0
    for ch in re.sub(r'"(?:[^"\\]|\\.)*"', '""', text):
        depth += (ch == "(") - (ch == ")")
        if depth < 0:
            return False
    return depth == 0


def test_every_chunk_is_short_and_balanced():
    chunks = build_chunks([point(i) for i in range(200)], True, OUT)
    assert all(len(c) <= CHUNK_LIMIT for c in chunks)
    assert all(balanced(c) for c in chunks)


def test_no_file_is_ever_loaded():
    chunks = build_chunks([point(i) for i in range(5)], True, OUT)
    assert not any("(load" in c for c in chunks)


def test_setup_opens_the_output_and_one_undo_group_first():
    chunks = build_chunks([point(1)], True, OUT)
    start = chunks[1]
    assert start.index("(vl-load-com)") < start.index("vla-get-activedocument")
    assert "(vla-startundomark" in start
    assert '"C:/temp/out.txt"' in start
    assert "(defun heron-run" in chunks[0]


def test_last_chunk_closes_every_undo_group_and_writes_done():
    last = build_chunks([point(1)], True, OUT)[-1]
    assert "(while (= 8 (logand 8 (getvar 'undoctl)))" in last
    assert '"DONE"' in last


def test_errors_are_caught_recorded_and_stop_the_rest():
    helper = build_chunks([point(1)], True, OUT)[0]
    assert "vl-catch-all-apply" in helper
    assert '"ERROR "' in helper
    assert "(close *heron-f*)" in helper


def test_every_entity_is_made_once_in_order():
    chunks = build_chunks([point(i) for i in range(30)], True, OUT)
    body = " ".join(chunks)
    found = [int(m) for m in re.findall(r"\(list (\d+)\.0 0\.0 0\.0\)", body)]
    assert found == list(range(30))
    assert body.count("(entmake") == 30


def test_a_long_polyline_is_built_up_in_pieces():
    pairs = [dotted(0, lisp_string("LWPOLYLINE"))] + [dotted(10, f"(list {i}.0 {i}.0)") for i in range(300)]
    chunks = build_chunks([pairs], True, OUT)
    assert all(len(c) <= CHUNK_LIMIT for c in chunks)
    body = " ".join(chunks)
    assert body.count("(entmake") == 1
    assert "(entmake *heron-p*)" in body
    assert len(re.findall(r"\(list \d+\.0 \d+\.0\)", body)) == 300


def test_a_single_value_too_long_is_refused_by_index():
    huge = [dotted(0, lisp_string("TEXT")), dotted(1, lisp_string("x" * 3000))]
    with pytest.raises(AutocadError, match="Operation 0"):
        build_chunks([huge], True, OUT)


class FakeDoc:
    """Answers the chunks the way AutoCAD would, by writing the output file."""

    def __init__(self):
        self.sent: list[str] = []
        self.out = None

    def GetVariable(self, name):
        return 0

    def SendCommand(self, text):
        self.sent.append(text)
        found = re.search(r'\(open "([^"]+)" "w"\)', text)
        if found:
            self.out = found.group(1)
        if '"DONE"' in text and self.out:
            with open(self.out, "w") as fh:
                fh.write("2A\n2B\nDONE\n")


def test_batch_tool_sends_chunks_and_reads_results(monkeypatch):
    doc = FakeDoc()

    async def run(fn):
        return fn()

    monkeypatch.setattr(batch, "run", run)
    monkeypatch.setattr(batch, "get_doc", lambda: doc)
    monkeypatch.setattr(batch, "require_idle", lambda d: None)
    monkeypatch.setattr(batch, "ensure_layer", lambda d, name: (None, False))
    result = json.loads(asyncio.run(batch.autocad_batch_draw(operations=[
        {"type": "point", "position": [0, 0]},
        {"type": "point", "position": [1, 0]},
    ])))
    assert result["handles"] == ["2A", "2B"]
    assert not any("(load" in s for s in doc.sent)
    assert len(doc.sent) >= 3
    assert all(len(s) <= CHUNK_LIMIT + 1 for s in doc.sent)


def _run_batch(monkeypatch, sender):
    doc = FakeDoc()

    async def run(fn):
        return fn()

    monkeypatch.setattr(batch, "run", run)
    monkeypatch.setattr(batch, "get_doc", lambda: doc)
    monkeypatch.setattr(batch, "require_idle", lambda d: None)
    monkeypatch.setattr(batch, "ensure_layer", lambda d, name: (None, False))
    monkeypatch.setattr(batch, "quiet_sender", lambda: sender)
    result = json.loads(asyncio.run(batch.autocad_batch_draw(operations=[{"type": "point", "position": [0, 0]}])))
    return doc, result


def test_batch_goes_through_the_plugin_quietly_when_it_can(monkeypatch):
    delivered = []

    def sender(lines):
        delivered.extend(lines)
        doc_holder[0].SendCommand("\n".join(lines))  # stand-in for AutoCAD running them
        return True

    doc_holder = [None]
    original = FakeDoc.__init__

    def init(self):
        original(self)
        doc_holder[0] = self

    monkeypatch.setattr(FakeDoc, "__init__", init)
    doc, result = _run_batch(monkeypatch, sender)
    assert delivered and '"DONE"' in delivered[-1]
    assert len(doc.sent) == 1  # only the stand-in above, no echoing SendCommand per chunk
    assert result["completed"] is True


def test_batch_falls_back_to_send_command_when_the_plugin_says_no(monkeypatch):
    doc, result = _run_batch(monkeypatch, lambda lines: False)
    assert len(doc.sent) >= 3
    assert result["completed"] is True


def test_every_chunk_returns_nothing_to_print():
    # The command line prints whatever an expression returns. A bare
    # (setq *heron-p* ...) printed the whole polyline (live, 2026-10-26).
    pairs = [dotted(0, lisp_string("LWPOLYLINE"))] + [dotted(10, f"(list {i}.0 {i}.0)") for i in range(300)]
    for chunk in build_chunks([pairs, point(1)], True, OUT):
        # The top-level form itself must return nothing printable: a progn
        # ending in (princ), or heron-run (which ends in (princ)). A defun at
        # top level printed "HERON-RUN" (live, 2026-10-26).
        assert chunk.startswith("(progn ") and chunk.endswith("(princ))") or chunk.startswith("(heron-run "), chunk[:60]
