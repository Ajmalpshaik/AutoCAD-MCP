"""The shared MCPServer instance plus the plumbing every tool reuses.

Tool modules import ``mcp`` from here and register onto it with decorators, so
the server keeps one registry while the tools stay grouped by subject.
"""

from __future__ import annotations

import functools
import json
from collections.abc import Callable
from enum import Enum
from typing import Any

import pythoncom
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from .connection import mark_writing
from .errors import AutocadError, com_message

mcp = MCPServer(
    "autocad_mcp",
    title="AutoCAD",
    version="1.0.0",
    instructions=(
        "Controls the AutoCAD instance running on this machine through its COM "
        "Automation interface. Changes appear live in the user's open drawing.\n\n"
        "Call autocad_status first: coordinates are in the drawing's own units, "
        "and that tool reports whether the drawing is in millimetres, metres or "
        "inches. All angles in this server are DEGREES.\n\n"
        "Entities are identified by their drawing 'handle', which every creation "
        "and query tool returns and every modify tool accepts.\n\n"
        "If a tool reports AutoCAD is busy or mid-command, the user needs to "
        "press Esc in AutoCAD — no retry will clear it."
    ),
)


def tool_meta(
    title: str,
    *,
    read_only: bool = False,
    destructive: bool = False,
    idempotent: bool = False,
    open_world: bool = False,
) -> dict[str, Any]:
    """Build the title and annotations kwargs for ``@mcp.tool``.

    Keeping this in one place means every tool declares its hints the same way,
    and the SDK's annotation type is named once rather than 49 times.
    """
    return {
        "title": title,
        "annotations": ToolAnnotations(
            read_only_hint=read_only,
            destructive_hint=destructive,
            idempotent_hint=idempotent,
            open_world_hint=open_world,
        ),
    }


# AutoCAD Color Index values that have common names.
ACI_COLORS = {
    "byblock": 0,
    "red": 1,
    "yellow": 2,
    "green": 3,
    "cyan": 4,
    "blue": 5,
    "magenta": 6,
    "white": 7,
    "black": 7,
    "grey": 8,
    "gray": 8,
    "bylayer": 256,
}


class ResponseFormat(str, Enum):
    """Output format for tools that can render either way."""

    MARKDOWN = "markdown"
    JSON = "json"


def to_aci(color: str | int | None) -> int | None:
    """Resolve a colour name or an AutoCAD Color Index number to an ACI int.

    Agents phrase colours both ways; rejecting one of them only produces a
    retry loop, so both are accepted here. Some clients send a number as a
    JSON-quoted string ('"7"'), so stray quotes around the value are removed.
    """
    if color is None or color == "":
        return None
    if isinstance(color, int) and not isinstance(color, bool):
        value = color
    else:
        text = str(color).strip().strip("\"'").strip().lower()
        if not text:
            return None
        if text in ACI_COLORS:
            return ACI_COLORS[text]
        try:
            value = int(text)
        except ValueError:
            raise AutocadError(
                f"'{color}' is not a colour this server understands. Use an "
                "AutoCAD Color Index number from 0-256, or one of: "
                + ", ".join(sorted(set(ACI_COLORS)))
                + "."
            ) from None
    if not 0 <= value <= 256:
        raise AutocadError(
            f"AutoCAD Color Index must be between 0 and 256, got {value}. "
            "256 means ByLayer, 0 means ByBlock."
        )
    return value


def dumps(payload: Any) -> str:
    """Serialize a tool result as JSON."""
    return json.dumps(payload, indent=2, default=str)


def tool_errors(func: Callable) -> Callable:
    """Turn COM and connection failures into actionable text.

    Every tool wears this, so a busy AutoCAD, a closed drawing or a stale
    handle reads as an instruction to the agent rather than a traceback.
    """

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> str:
        # Every call goes through the Heron gate: connection, padlocks,
        # wrong-drawing guard, Keep or Discard, audit (core/gate.py).
        from .gate import guarded

        return await guarded(func.__name__, lambda: _run(*args, **kwargs))

    async def _run(*args: Any, **kwargs: Any) -> str:
        try:
            return await func(*args, **kwargs)
        except AutocadError as exc:
            return f"Error: {exc}"
        except pythoncom.com_error as exc:
            return (
                f"Error: AutoCAD rejected the operation — {com_message(exc)}. "
                "Check that the drawing is not read-only, the target layer is "
                "not locked or frozen, and no command is waiting for input."
            )
        except (ValueError, TypeError) as exc:
            return f"Error: Invalid input — {exc}"
        except Exception as exc:  # noqa: BLE001 - last resort, still actionable
            return f"Error: Unexpected {type(exc).__name__} — {exc}"

    return wrapper


class undo_mark:
    """Group everything a write tool does into one AutoCAD undo step.

    Without this, each primitive lands as its own undo record and the user has
    to press Ctrl+Z once per entity to back out a single tool call.
    """

    def __init__(self, doc: Any) -> None:
        self.doc = doc

    def __enter__(self) -> Any:
        # From here on the drawing may change, so a busy signal must not
        # re-run the work (see connection._with_retry).
        mark_writing()
        try:
            self.doc.StartUndoMark()
        except BaseException:  # noqa: BLE001 - grouping is a nicety, not a gate
            pass
        return self.doc

    def __exit__(self, *exc_info: Any) -> None:
        try:
            self.doc.EndUndoMark()
        except BaseException:  # noqa: BLE001
            pass
