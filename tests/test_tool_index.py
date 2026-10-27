"""The toolbox has to be findable, or 101 tools is worse than 20.

Two things are checked here. Every tool says **when** to use it, so an AI (or
Ajmal) can pick one without reading its arguments. And the index resource
lists every one of them, grouped by padlock, built from the live registry so
it cannot drift from the code.
"""

from __future__ import annotations

import asyncio
import json

import pytest

from autocad_mcp.core.registry import mcp
from autocad_mcp.core.risk import RISK, Risk
from autocad_mcp.tools import register_all, resources

register_all()

TOOLS = asyncio.run(mcp.list_tools())
INDEX = json.loads(asyncio.run(resources.tool_index()))


def listed() -> dict[str, dict]:
    """Every row in the index, by tool name."""
    rows = {}
    for group in INDEX["padlocks"].values():
        for row in group["tools"]:
            rows[row["tool"]] = row
    return rows


class TestEveryToolSaysWhenToUseIt:
    @pytest.mark.parametrize("tool", sorted(t.name for t in TOOLS))
    def test_it_has_a_use_when_line(self, tool):
        """A new tool must say when to use it, or it will not be found."""
        description = next(t.description or "" for t in TOOLS if t.name == tool)
        assert "Use when" in description, (
            f"{tool} does not say when to use it. Add an 'Examples:' section "
            "to its docstring with '- Use when: \"...\"' in the user's own words."
        )

    @pytest.mark.parametrize("tool", sorted(t.name for t in TOOLS))
    def test_the_index_can_read_its_use_when_lines(self, tool):
        row = listed()[tool]
        assert row["use_when"], f"{tool} has a Use when line the index cannot read"

    @pytest.mark.parametrize("tool", sorted(t.name for t in TOOLS))
    def test_it_has_a_summary_and_a_title(self, tool):
        row = listed()[tool]
        assert len(row["summary"].split()) >= 3, f"{tool}: {row['summary']!r}"
        assert row["title"], f"{tool} has no title"


class TestTheIndexMatchesTheRegistry:
    def test_it_lists_every_tool_once(self):
        assert sorted(listed()) == sorted(t.name for t in TOOLS)

    def test_its_count_is_the_truth(self):
        assert INDEX["count"] == len(TOOLS) == len(listed())

    def test_the_counts_add_up(self):
        total = sum(group["count"] for group in INDEX["padlocks"].values())
        assert total == len(TOOLS)
        for group in INDEX["padlocks"].values():
            assert group["count"] == len(group["tools"])

    def test_every_padlock_level_is_there_and_named(self):
        assert list(INDEX["padlocks"]) == [r.value for r in
                                           (Risk.READ, Risk.VIEW, Risk.CHANGE, Risk.PUBLISH, Risk.ADMIN)]
        for level, group in INDEX["padlocks"].items():
            assert group["needs"], level

    def test_each_tool_is_under_its_own_level(self):
        for level, group in INDEX["padlocks"].items():
            for row in group["tools"]:
                assert RISK[row["tool"]].value == level, row["tool"]

    def test_only_read_and_view_need_no_padlock(self):
        for level, group in INDEX["padlocks"].items():
            needs_none = group["needs"].startswith("none")
            assert needs_none == (level in ("read", "view")), level

    def test_it_says_a_padlock_cannot_be_talked_up(self):
        assert "property of the tool" in INDEX["note"]


class TestTheBulletsReadAsSentences:
    def test_a_wrapped_bullet_is_joined_back_up(self):
        """A bullet that wraps in the source must not be cut off in the index."""
        row = listed()["autocad_make_shape"]
        joined = [line for line in row["use_when"] if "cone_development" in line]
        assert joined, row["use_when"]
        assert joined[0].startswith("Use when:") and joined[0].endswith(".")

    @pytest.mark.parametrize("tool", sorted(t.name for t in TOOLS))
    def test_no_bullet_is_left_hanging(self, tool):
        """A bullet ending in a connector means a continuation was dropped."""
        for line in listed()[tool]["use_when"]:
            assert not line.rstrip().endswith(("->", "—", "-", ",", "and", "or")), f"{tool}: {line!r}"

    @pytest.mark.parametrize("tool", sorted(t.name for t in TOOLS))
    def test_no_bullet_swallowed_the_next_section(self, tool):
        for line in listed()[tool]["use_when"]:
            for header in ("Args:", "Returns:", "Error Handling:", "Examples:"):
                assert header not in line, f"{tool} ran into {header}: {line!r}"


def test_the_index_answers_with_no_autocad_running():
    """It is the one resource that touches no drawing, so it is not gated."""
    out = json.loads(asyncio.run(resources.tool_index()))
    assert out["count"] == len(TOOLS)
    assert "Error" not in out.get("note", "")
