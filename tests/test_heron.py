"""Heron AI for AutoCAD: risk levels and server start-up options."""

from __future__ import annotations

import asyncio

from autocad_mcp.core.registry import mcp
from autocad_mcp.core.risk import RISK, Risk, risk_of
from autocad_mcp.tools import register_all

register_all()


def _registered() -> set[str]:
    return {tool.name for tool in asyncio.run(mcp.list_tools())}


def test_every_registered_tool_has_a_level():
    # A tool with no level would slip past the padlocks, so this fails first.
    assert _registered() == set(RISK)


def test_levels_match_spec():
    assert risk_of("autocad_status") is Risk.READ
    assert risk_of("autocad_zoom") is Risk.VIEW
    assert risk_of("autocad_open_drawing") is Risk.VIEW
    assert risk_of("autocad_draw_line") is Risk.CHANGE
    assert risk_of("autocad_delete_entities") is Risk.CHANGE
    assert risk_of("autocad_create_layer") is Risk.CHANGE
    assert risk_of("autocad_save_drawing") is Risk.PUBLISH
    assert risk_of("autocad_export") is Risk.PUBLISH
    assert risk_of("autocad_run_lisp") is Risk.ADMIN
    assert risk_of("autocad_send_command") is Risk.ADMIN
    assert risk_of("autocad_set_variable") is Risk.ADMIN
    if "autocad_preview" in RISK:
        assert risk_of("autocad_preview") is Risk.READ


def test_unknown_tool_has_no_level():
    try:
        risk_of("autocad_not_a_tool")
    except KeyError:
        return
    raise AssertionError("an unknown tool must not get a default level")
