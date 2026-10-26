"""MCP resources and prompts.

A resource reads the drawing just as a tool does, so each one calls the
matching gated tool: it is refused the same way while AutoCAD is not
connected to Heron, and it is audited the same way.
"""

from __future__ import annotations

from ..core.registry import mcp
from . import document, layers

_JSON = "application/json"


@mcp.resource("autocad://drawing/status", name="drawing_status", description="Connection, active drawing, units.", mime_type=_JSON)
async def drawing_status() -> str:
    return await document.autocad_status(launch_if_needed=False)


@mcp.resource("autocad://drawing/layers", name="drawing_layers", description="Every layer and its state.", mime_type=_JSON)
async def drawing_layers() -> str:
    return await layers.autocad_list_layers(include_entity_counts=False)


@mcp.resource("autocad://drawing/blocks", name="drawing_blocks", description="Block definitions in the drawing.", mime_type=_JSON)
async def drawing_blocks() -> str:
    return await layers.autocad_list_blocks()


@mcp.resource("autocad://drawing/styles", name="drawing_styles", description="Text styles, dimension styles, linetypes.", mime_type=_JSON)
async def drawing_styles() -> str:
    return await layers.autocad_list_styles()


@mcp.prompt(name="check_standards", description="Check the open drawing against a layer standard and show the result.")
def check_standards(rules_path: str = "") -> str:
    where = f"the rules in {rules_path}" if rules_path else "the layer standard I describe"
    return (
        "Check the drawing that is open in AutoCAD against " + where + ".\n"
        "1. Call autocad_status and tell me the drawing name and units.\n"
        "2. Call autocad_check_standards with those rules.\n"
        "3. Summarise the findings by rule, worst first, with handles I can zoom to.\n"
        "4. Do not change anything: only report."
    )


@mcp.prompt(name="draw_from_spec", description="Draw something from a written spec, then show it.")
def draw_from_spec(spec: str) -> str:
    return (
        "Draw this in the AutoCAD drawing that is open:\n\n" + spec + "\n\n"
        "Work like this: call autocad_status first for the units; use autocad_batch_draw for more "
        "than about ten objects; put everything on named layers; then call autocad_preview and "
        "look at the picture before you tell me it is done. If Changes is off, tell me to turn it "
        "on with the Changes padlock on the Heron tab."
    )
