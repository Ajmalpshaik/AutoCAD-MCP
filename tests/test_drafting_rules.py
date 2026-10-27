"""Ajmal's drafting rules ship inside Heron, so every AI that connects follows them."""

from __future__ import annotations

import asyncio

from autocad_mcp.core.registry import mcp
from autocad_mcp.tools import register_all, resources

register_all()


def test_every_connecting_ai_is_told_the_drafting_rules():
    text = mcp.instructions
    for rule in ("autocad_make_block", "autocad_add_label", "autocad_status", "autocad_preview", "crossing"):
        assert rule in text, rule


def test_draw_detail_prompt_carries_the_full_checklist():
    names = {p.name for p in asyncio.run(mcp.list_prompts())}
    assert "draw_detail" in names
    text = resources.draw_detail("roof pipe support")
    for rule in ("block", "TLD", "units", "plan", "whole", "preview", "column", "title"):
        assert rule.lower() in text.lower(), rule


def _prompt_texts() -> dict[str, str]:
    """Every prompt's words, as the AI reading it will get them."""
    return {
        "check_standards": resources.check_standards(),
        "draw_from_spec": resources.draw_from_spec("a 2400 x 1200 plate"),
        "draw_detail": resources.draw_detail("roof pipe support"),
        "make_sheet": resources.make_sheet("E-101"),
        "import_to_shop_drawing": resources.import_to_shop_drawing("steelwork"),
        "model_part": resources.model_part("a 200 x 100 x 10 angle bracket"),
        "shape_from_words": resources.shape_from_words("a 120 long slot 40 wide"),
    }


def test_every_prompt_is_registered():
    names = {p.name for p in asyncio.run(mcp.list_prompts())}
    assert set(_prompt_texts()) <= names, sorted(set(_prompt_texts()) - names)


def test_no_prompt_tells_the_ai_to_call_a_tool_that_does_not_exist():
    """A prompt naming a tool that was renamed or never built sends the AI nowhere."""
    import re

    from autocad_mcp.core.risk import RISK

    wrong: list[str] = []
    for name, text in _prompt_texts().items():
        for tool in sorted(set(re.findall(r"\bautocad_[a-z0-9_]+", text))):
            if tool not in RISK:
                wrong.append(f"{name} names {tool}")
    assert wrong == [], wrong


def test_the_sheet_prompt_covers_the_whole_sheet():
    text = resources.make_sheet("E-101", "A1", "1:100").lower()
    for step in ("autocad_create_layout", "autocad_page_setup", "autocad_place_title_block",
                 "autocad_add_viewport", "autocad_save_view", "scale_set", "drawing_space",
                 "attributes_not_found", "ucs", "preview"):
        assert step in text, step


def test_the_shop_drawing_prompt_insists_on_the_dry_run():
    text = resources.import_to_shop_drawing("steelwork").lower()
    for step in ("dry_run", "autocad_remap_layers", "autocad_tidy_entities",
                 "autocad_dimension_run", "measured", "autocad_check_standards",
                 "autocad_sequence", "progn"):
        assert step in text, step


def test_the_part_prompt_will_not_guess_a_density():
    text = resources.model_part("a bracket", "stainless").lower()
    assert "do not guess a density" in text
    for step in ("autocad_extrude_profile", "autocad_solid_boolean", "autocad_solid_properties",
                 "volume_after", "coords='ucs'", "pi x diameter"):
        assert step in text, step


def test_the_shape_prompt_checks_its_own_work():
    text = resources.shape_from_words("a slot").lower()
    for step in ("dry_run", "autocad_polyline_info", "bulges", "do not report it as done"):
        assert step in text, step
