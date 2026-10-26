"""What each tool may do to a drawing, declared once, in code.

The Heron plug-in decides from this level which padlock a call needs. It is
never worked out from the request text: a tool's level is a property of the
tool, so nothing a caller writes can raise it or lower it.
"""

from __future__ import annotations

from enum import Enum


class Risk(str, Enum):
    READ = "read"  # looks at the drawing, changes nothing
    VIEW = "view"  # changes what is on screen or which drawing is active
    CHANGE = "change"  # changes drawing content: needs the Changes padlock
    PUBLISH = "publish"  # writes files: Changes + Publish
    ADMIN = "admin"  # escape hatches that can do anything: Changes + Admin


_LEVELS: dict[Risk, tuple[str, ...]] = {
    Risk.READ: (
        "status",
        "list_drawings",
        "list_entities",
        "get_entity",
        "get_selection",
        "find_text",
        "get_extents",
        "measure",
        "list_layers",
        "list_blocks",
        "list_styles",
        "get_variable",
    ),
    Risk.VIEW: (
        "zoom",
        "regen",
        "switch_drawing",
        "open_drawing",
        "create_drawing",
    ),
    Risk.CHANGE: (
        "draw_line",
        "draw_polyline",
        "draw_rectangle",
        "draw_circle",
        "draw_arc",
        "draw_ellipse",
        "draw_point",
        "add_text",
        "add_mtext",
        "add_dimension",
        "add_hatch",
        "insert_block",
        "batch_draw",
        "move_entities",
        "copy_entities",
        "rotate_entities",
        "scale_entities",
        "mirror_entities",
        "offset_entities",
        "array_entities",
        "modify_entity",
        "delete_entities",
        "create_layer",
        "set_layer_state",
        "set_current_layer",
        "delete_layer",
    ),
    Risk.PUBLISH: (
        "save_drawing",
        "export",
    ),
    Risk.ADMIN: (
        "send_command",
        "run_lisp",
        "set_variable",
        "purge",
        "audit",
    ),
}

RISK: dict[str, Risk] = {
    f"autocad_{name}": level for level, names in _LEVELS.items() for name in names
}


def risk_of(tool: str) -> Risk:
    """The level of a registered tool. Unknown tools raise KeyError, never a default."""
    return RISK[tool]
