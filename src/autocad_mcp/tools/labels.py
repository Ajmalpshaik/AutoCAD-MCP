"""Labels: MTEXT with a leader, the way Ajmal's TLD command makes them.

Two kinds:

* ``leader`` (default) follows TextLeader_V4.lsp ("TLD"): an MTEXT label and a
  classic LEADER on the text's layer, using the current dimension style for the
  arrow. The leader ends under the text, in the gap between line 1 and line 2
  (just under a one-line text), running the full text width plus an extension
  each side. Shape "L": a square leg from the arrow point, then along under the
  text. Shape "angled": straight to the near end of the text, then along it.
* ``mleader``: one MULTILEADER with the text as its content.

Both are one undo step. The arrow is sized from DIMSCALE: a leader made over COM
does not pick up the DIMSCALE override on its own (seen on dimensions, 2026-10-26).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any, Literal

from pydantic import Field, StrictInt

from ..acad.tables import apply_properties
from ..core.connection import get_doc, get_space, require_idle, run
from ..core.errors import AutocadError
from ..core.registry import dumps, mcp, to_aci, tool_errors, tool_meta, undo_mark
from ..core.variants import double_array
from ._shared import COLOR_OPT, LAYER_OPT, point

AC_LINE_WITH_ARROW = 2  # AcLeaderType: 0 line, 1 spline, 2 line + arrow, 3 spline + arrow
AC_MTEXT_CONTENT = 2  # AcMLeaderContentType
AC_ATTACH_TOP_RIGHT = 3  # AcAttachmentPoint


@dataclass(frozen=True)
class Frame:
    """An MTEXT's extent (world X/Y, unrotated text)."""

    left: float
    right: float
    top: float
    height: float
    spacing: float = 1.0


def underline_level(frame: Frame) -> float:
    """Where the leader runs under the text: between line 1 and line 2 (TLD rule)."""
    pitch = frame.height * frame.spacing * 5.0 / 3.0
    return frame.top - frame.height - (pitch - frame.height) / 2.0


def leader_points(
    frame: Frame, arrow: tuple[float, float], shape: str, extension: float
) -> list[tuple[float, float]]:
    """TLD leader vertices, from the arrow point to the far end under the text."""
    if shape not in ("L", "angled"):
        raise AutocadError(f"shape must be 'L' or 'angled', got {shape!r}.")
    ext = extension * frame.height
    yu = underline_level(frame)
    ends = (frame.left - ext, frame.right + ext)
    ax, ay = float(arrow[0]), float(arrow[1])
    near, far = sorted(ends, key=lambda x: abs(x - ax))
    if shape == "angled":
        return [(ax, ay), (near, yu), (far, yu)]
    if abs(ay - yu) < 1e-6:
        return [(ax, ay), (far, yu)]
    return [(ax, ay), (ax, yu), (far, yu)]


def _flat(points: list[tuple[float, float]]) -> list[float]:
    return [c for x, y in points for c in (x, y, 0.0)]


@mcp.tool(name="autocad_add_label", **tool_meta("Add Label with Leader"))
@tool_errors
async def autocad_add_label(
    text: Annotated[str, Field(description="Label text. Use \\P for a new line (MTEXT).")],
    arrow: Annotated[list[float], Field(description="Arrow point [x, y]: what the label points at.")],
    position: Annotated[list[float], Field(description="Top-left corner of the text [x, y].")],
    height: Annotated[float, Field(gt=0, description="Text height in drawing units.")],
    kind: Annotated[
        Literal["leader", "mleader"],
        Field(description="'leader' = MTEXT + LEADER, Ajmal's TLD style (default); 'mleader' = one MULTILEADER."),
    ] = "leader",
    shape: Annotated[
        Literal["L", "angled"],
        Field(description="For kind='leader': 'L' square leg then under the text (default), 'angled' straight to the text."),
    ] = "L",
    extension: Annotated[
        float, Field(ge=0, le=10, description="How far the line runs past the text each side, x text height (TLD: 0.5).")
    ] = 0.5,
    width: Annotated[float, Field(ge=0, description="MTEXT wrap width; 0 = no wrapping.")] = 0.0,
    text_align: Annotated[
        Literal["left", "right"],
        Field(description="'left': position is the text's top-left (default). 'right': its top-right, for a label column left of the detail."),
    ] = "left",
    mask: Annotated[
        bool, Field(description="Background mask behind the text, so it reads over hatching and lines.")
    ] = False,
    layer: Annotated[str | None, LAYER_OPT] = None,
    color: Annotated[str | StrictInt | None, COLOR_OPT] = None,
) -> str:
    """Place a label that points at something: text plus a leader with an arrow.

    Use for every label on a drawing. Default is Ajmal's TLD style: MTEXT, and a
    LEADER that ends under the text. 'L' gives a square leg, 'angled' a straight
    one; pick 'angled' when several labels sit in a column. kind='mleader' gives
    one MULTILEADER instead. Put the text where it is easy to read, clear of the
    drawing; the arrow goes on the object.

    Returns:
        JSON: {"created": true, "kind", "handle" (text or mleader), "handles", "points"}
    """
    aci = to_aci(color)

    def work() -> dict[str, Any]:
        doc = get_doc()
        require_idle(doc)
        space = get_space(doc, "model")
        scale = float(doc.GetVariable("DIMSCALE") or 1.0) or 1.0
        with undo_mark(doc):
            if kind == "mleader":
                pts = [(float(arrow[0]), float(arrow[1])), (float(position[0]), float(position[1]))]
                made = space.AddMLeader(double_array(_flat(pts)), 0)
                mleader = made[0] if isinstance(made, tuple) else made
                mleader.ContentType = AC_MTEXT_CONTENT
                mleader.TextString = text
                notes = apply_properties(doc, mleader, layer, aci, None)
                for prop, value in (("TextHeight", height), ("ArrowheadSize", height), ("DoglegLength", height)):
                    try:
                        setattr(mleader, prop, float(value))
                    except Exception:  # noqa: BLE001 - a style that locks it keeps its own
                        notes.setdefault("not_set", []).append(prop)
                return {"created": True, "kind": "mleader", "handle": str(mleader.Handle),
                        "handles": [str(mleader.Handle)], "points": [list(p) for p in pts], **notes}

            label = space.AddMText(point(position, "position"), float(width), text)
            label.Height = float(height)
            if mask:
                label.BackgroundFill = True
            if text_align == "right":
                label.AttachmentPoint = AC_ATTACH_TOP_RIGHT
                label.InsertionPoint = point(position, "position")
            notes = apply_properties(doc, label, layer, aci, None)
            low, high = label.GetBoundingBox()
            frame = Frame(
                left=float(low[0]), right=float(high[0]), top=float(high[1]),
                height=float(height), spacing=float(getattr(label, "LineSpacingFactor", 1.0) or 1.0),
            )
            pts = leader_points(frame, (float(arrow[0]), float(arrow[1])), shape, extension)
            lead = space.AddLeader(double_array(_flat(pts)), None, AC_LINE_WITH_ARROW)
            lead.Layer = label.Layer  # TLD: the leader lives on the text's layer
            lead.ScaleFactor = scale
        return {"created": True, "kind": "leader", "shape": shape,
                "handle": str(label.Handle), "text_handle": str(label.Handle),
                "leader_handle": str(lead.Handle), "handles": [str(label.Handle), str(lead.Handle)],
                "points": [list(p) for p in pts], "arrow_scale": scale, **notes}

    return dumps(await run(work))
