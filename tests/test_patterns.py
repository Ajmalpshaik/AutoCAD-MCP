"""Hatch pattern (.pat) and linetype (.lin) files, written from plain words (no AutoCAD).

The file text is what AutoCAD reads, so it is checked line by line: one wrong
comma and AutoCAD says only "bad pattern".
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from autocad_mcp.acad import patterns as p
from autocad_mcp.core.risk import Risk, risk_of
from autocad_mcp.tools import patterns as tools


class TestPatText:
    def test_one_family_of_lines(self):
        text = p.pat_text("CHW-INS", "Chilled water insulation", p.hatch_families("lines", 45, 3))
        assert text == "*CHW-INS, Chilled water insulation\n45, 0,0, 0,3\n"

    def test_a_cross_is_two_families_square_to_each_other(self):
        text = p.pat_text("GRID5", "", p.hatch_families("cross", 0, 5))
        assert text.splitlines()[1:] == ["0, 0,0, 0,5", "90, 0,0, 0,5"]
        assert text.splitlines()[0] == "*GRID5"

    def test_dashes_follow_the_offsets(self):
        text = p.pat_text("DASH", "", p.hatch_families("lines", 0, 4, dashes=[3, -1.5]))
        assert text.splitlines()[1] == "0, 0,0, 0,4, 3,-1.5"

    def test_a_custom_family_is_written_as_given(self):
        fams = p.hatch_families("custom", families=[{"angle": 30, "origin": [1, 2], "offset": [0.5, 6], "dashes": [2, -1, 0, -1]}])
        assert p.pat_text("C", "", fams).splitlines()[1] == "30, 1,2, 0.5,6, 2,-1,0,-1"

    @pytest.mark.parametrize(
        ("kwargs", "match"),
        [
            ({"preset": "lines", "angle": 45, "spacing": 0}, "spacing"),
            ({"preset": "lines", "angle": 45, "spacing": 3, "dashes": [1, -1, 1, -1, 1, -1, 1]}, "six"),
            ({"preset": "custom", "families": []}, "at least one"),
            ({"preset": "custom", "families": [{"angle": 0, "offset": [0, 0]}]}, "on top of each other"),
            ({"preset": "spiral"}, "preset"),
        ],
    )
    def test_refusals(self, kwargs, match):
        with pytest.raises(ValueError, match=match):
            p.hatch_families(**kwargs)

    @pytest.mark.parametrize("name", ["", "has space", "x" * 32, "bad*name"])
    def test_a_name_autocad_or_a_file_cannot_hold_is_refused(self, name):
        with pytest.raises(ValueError):
            p.check_name(name)


class TestLinText:
    def test_a_simple_dashed_line(self):
        assert p.lin_text("DASH-12", "Dash 12 gap 3", [12, -3]) == "*DASH-12,Dash 12 gap 3\nA,12,-3\n"

    def test_an_mep_service_line_carries_its_text_in_the_gap(self):
        """CHWS: a 12 dash, then the text centred on the line in a gap that clears it."""
        elements, description = p.text_linetype("CHWS", "CHWS", dash=12, pad=1.5, height=2.5)
        text = p.lin_text("CHWS", description, elements)
        name_line, pattern = text.splitlines()
        assert name_line.startswith("*CHWS,") and "CHWS" in name_line[6:]
        assert pattern == 'A,12,-1.5,["CHWS",STANDARD,S=2.5,R=0,X=0,Y=-1.25],-10.5'

    def test_the_gap_can_be_set_when_the_estimate_is_off(self):
        elements, _ = p.text_linetype("HW", "HW", dash=10, pad=1, height=2, text_width=5)
        assert elements[-1] == -6.0

    @pytest.mark.parametrize(
        ("elements", "match"),
        [
            ([-3, 12], "start with a dash"),
            ([], "at least one"),
            ([12] * 13, "12"),
        ],
    )
    def test_refusals(self, elements, match):
        with pytest.raises(ValueError, match=match):
            p.lin_text("BAD", "", elements)

    def test_a_quote_in_the_text_is_refused(self):
        with pytest.raises(ValueError, match="quote"):
            p.text_linetype("Q", 'SAY "HI"')

    def test_a_long_description_is_refused(self):
        with pytest.raises(ValueError, match="47"):
            p.lin_text("D", "x" * 48, [12, -3])


# ---------------------------------------------------------------------------
# The tools, against a fake AutoCAD
# ---------------------------------------------------------------------------


class Files:
    def __init__(self, support):
        self.SupportPath = support


class Prefs:
    def __init__(self, support):
        self.Files = Files(support)


class App:
    def __init__(self, support):
        self.Preferences = Prefs(support)


class Named:
    def __init__(self, name):
        self.Name = name


class Linetypes:
    def __init__(self, *names):
        self.items = [Named(n) for n in names]
        self.loaded = []

    @property
    def Count(self):
        return len(self.items)

    def Item(self, i):
        return self.items[i]

    def Load(self, name, path):
        self.loaded.append((name, path))
        self.items.append(Named(name))


class Doc:
    def __init__(self, support="C:\\AutoCAD\\Support"):
        self.Application = App(support)
        self.Linetypes = Linetypes("ByLayer", "ByBlock", "Continuous")
        self.TextStyles = Linetypes("Standard")


@pytest.fixture
def doc(monkeypatch):
    fake = Doc()

    async def run(fn):
        return fn()

    monkeypatch.setattr(tools, "run", run)
    monkeypatch.setattr(tools, "get_doc", lambda: fake)
    return fake


def call(coro):
    answer = asyncio.run(coro)
    assert not answer.startswith("Error"), answer
    return json.loads(answer)


def test_a_hatch_pattern_is_written_and_its_folder_put_on_the_support_path(doc, tmp_path):
    out = call(tools.autocad_create_hatch_pattern(name="CHW-INS", angle=45, spacing=3, folder=str(tmp_path)))
    written = Path(out["file"])
    assert written.name == "CHW-INS.pat"
    assert written.read_text() == "*CHW-INS\n45, 0,0, 0,3\n"
    assert doc.Application.Preferences.Files.SupportPath == "C:\\AutoCAD\\Support;" + str(tmp_path)
    assert out["support_path_added"] is True and "autocad_add_hatch" in out["hint"]


def test_the_support_path_is_not_doubled(doc, tmp_path):
    doc.Application.Preferences.Files.SupportPath = "C:\\AutoCAD\\Support;" + str(tmp_path).upper()
    out = call(tools.autocad_create_hatch_pattern(name="P1", spacing=2, folder=str(tmp_path)))
    assert out["support_path_added"] is False


def test_an_existing_pattern_file_is_not_overwritten_without_replace(doc, tmp_path):
    (tmp_path / "P1.pat").write_text("*P1\n0, 0,0, 0,1\n")
    answer = asyncio.run(tools.autocad_create_hatch_pattern(name="P1", spacing=2, folder=str(tmp_path)))
    assert answer.startswith("Error") and "replace" in answer
    assert (tmp_path / "P1.pat").read_text() == "*P1\n0, 0,0, 0,1\n"


def test_a_dry_run_writes_nothing(doc, tmp_path):
    out = call(tools.autocad_create_hatch_pattern(name="P2", spacing=2, folder=str(tmp_path), dry_run=True))
    assert out["file_text"] == "*P2\n45, 0,0, 0,2\n" and not (tmp_path / "P2.pat").exists()


def test_the_default_folder_is_herons_own(doc, monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    out = call(tools.autocad_create_hatch_pattern(name="P3", spacing=2))
    assert Path(out["file"]) == tmp_path / "Heron" / "autocad" / "support" / "P3.pat"


def test_a_service_linetype_is_written_and_loaded(doc, tmp_path):
    out = call(tools.autocad_create_linetype(name="CHWS", text="CHWS", folder=str(tmp_path)))
    assert Path(out["file"]).read_text().startswith("*CHWS,")
    assert doc.Linetypes.loaded == [("CHWS", out["file"])]
    assert out["loaded"] is True


def test_a_linetype_already_in_the_drawing_is_refused_before_writing(doc, tmp_path):
    doc.Linetypes.items.append(Named("CHWS"))
    answer = asyncio.run(tools.autocad_create_linetype(name="chws", text="CHWS", folder=str(tmp_path)))
    assert answer.startswith("Error") and "already" in answer
    assert not (tmp_path / "chws.lin").exists() and doc.Linetypes.loaded == []


def test_a_text_style_the_drawing_lacks_is_refused(doc, tmp_path):
    answer = asyncio.run(tools.autocad_create_linetype(name="HWS", text="HWS", text_style="ROMANS", folder=str(tmp_path)))
    assert answer.startswith("Error") and "ROMANS" in answer


def test_give_text_or_dashes_not_both(doc, tmp_path):
    answer = asyncio.run(tools.autocad_create_linetype(name="X", text="X", dashes=[1, -1], folder=str(tmp_path)))
    assert answer.startswith("Error")


def test_levels():
    assert risk_of("autocad_create_hatch_pattern") is Risk.PUBLISH
    assert risk_of("autocad_create_linetype") is Risk.PUBLISH
