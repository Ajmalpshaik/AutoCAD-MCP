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
