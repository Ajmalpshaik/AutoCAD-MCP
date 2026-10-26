"""Bulk geometry creation through AutoLISP.

The per-entity tools in draw.py go through COM, which costs a round trip for
the create plus one for each property. That is the right trade for a handful of
entities — the inputs are validated per field and the result comes back typed.

For hundreds of entities it is the wrong trade. This tool sends one AutoLISP
script that runs inside AutoCAD and creates everything with ``entmake``, so a
batch of any size is a single round trip.
"""

from __future__ import annotations

import os
import tempfile
import time
import uuid
from typing import Annotated, Any

from pydantic import Field

from ..acad.lisp import (
    build_chunks,
    dotted,
    lisp_number,
    lisp_point,
    lisp_string,
    parse_output,
)
from ..acad.tables import ensure_layer
from ..acad.units import rad
from ..core.connection import get_doc, mark_writing, require_idle, run
from ..core.errors import AutocadError
from ..core.gate import quiet_sender
from ..core.registry import dumps, mcp, to_aci, tool_errors, tool_meta

MAX_OPERATIONS = 5000

# How long to wait for the script's output file to appear. SendCommand normally
# blocks until the load completes, so this only covers the versions where it
# does not.
OUTPUT_TIMEOUT = 60.0
OUTPUT_POLL = 0.02


def _require(op: dict[str, Any], key: str, index: int) -> Any:
    if key not in op or op[key] is None:
        raise AutocadError(
            f"Operation {index} ({op.get('type', 'unknown')}) is missing "
            f"required field '{key}'."
        )
    return op[key]


def _common_pairs(op: dict[str, Any], dxf_name: str) -> list[str]:
    """The group codes every entity shares: type, layer, colour."""
    pairs = [dotted(0, lisp_string(dxf_name))]
    if op.get("layer"):
        pairs.append(dotted(8, lisp_string(str(op["layer"]).strip())))
    aci = to_aci(op.get("color"))
    if aci is not None:
        pairs.append(dotted(62, str(aci)))
    return pairs


def _build_line(op: dict[str, Any], i: int) -> list[str]:
    pairs = _common_pairs(op, "LINE")
    pairs.append(dotted(10, lisp_point(_require(op, "start", i))))
    pairs.append(dotted(11, lisp_point(_require(op, "end", i))))
    return pairs


def _build_circle(op: dict[str, Any], i: int) -> list[str]:
    radius = op.get("radius")
    if radius is None and op.get("diameter") is not None:
        radius = float(op["diameter"]) / 2.0
    if radius is None:
        raise AutocadError(f"Operation {i} (circle) needs 'radius' or 'diameter'.")
    if float(radius) <= 0:
        raise AutocadError(
            f"Operation {i} (circle) has radius {radius}; it must be greater "
            "than zero."
        )
    pairs = _common_pairs(op, "CIRCLE")
    pairs.append(dotted(10, lisp_point(_require(op, "center", i))))
    pairs.append(dotted(40, lisp_number(radius)))
    return pairs


def _build_arc(op: dict[str, Any], i: int) -> list[str]:
    radius = _require(op, "radius", i)
    if float(radius) <= 0:
        raise AutocadError(f"Operation {i} (arc) has radius {radius}; must be > 0.")
    pairs = _common_pairs(op, "ARC")
    pairs.append(dotted(10, lisp_point(_require(op, "center", i))))
    pairs.append(dotted(40, lisp_number(radius)))
    pairs.append(dotted(50, lisp_number(rad(_require(op, "start_angle", i)))))
    pairs.append(dotted(51, lisp_number(rad(_require(op, "end_angle", i)))))
    return pairs


def _build_point(op: dict[str, Any], i: int) -> list[str]:
    pairs = _common_pairs(op, "POINT")
    pairs.append(dotted(10, lisp_point(_require(op, "position", i))))
    return pairs


def _build_text(op: dict[str, Any], i: int) -> list[str]:
    pairs = _common_pairs(op, "TEXT")
    pairs.append(dotted(10, lisp_point(_require(op, "position", i))))
    pairs.append(dotted(40, lisp_number(op.get("height", 2.5))))
    pairs.append(dotted(1, lisp_string(_require(op, "text", i))))
    if op.get("rotation"):
        pairs.append(dotted(50, lisp_number(rad(op["rotation"]))))
    return pairs


def _polyline_pairs(
    op: dict[str, Any], vertices: list[list[float]], closed: bool
) -> list[str]:
    """LWPOLYLINE needs its subclass markers, unlike the simpler entities.

    entmake validates against the DXF subclass structure here, so the
    AcDbEntity / AcDbPolyline markers and the vertex count are mandatory, and
    colour has to sit in the AcDbEntity section before the second marker.
    """
    pairs = [dotted(0, lisp_string("LWPOLYLINE")), dotted(100, lisp_string("AcDbEntity"))]
    if op.get("layer"):
        pairs.append(dotted(8, lisp_string(str(op["layer"]).strip())))
    aci = to_aci(op.get("color"))
    if aci is not None:
        pairs.append(dotted(62, str(aci)))
    pairs.append(dotted(100, lisp_string("AcDbPolyline")))
    pairs.append(dotted(90, str(len(vertices))))
    pairs.append(dotted(70, "1" if closed else "0"))
    for vertex in vertices:
        pairs.append(
            dotted(
                10,
                f"(list {lisp_number(vertex[0])} {lisp_number(vertex[1])})",
            )
        )
    return pairs


def _build_polyline(op: dict[str, Any], i: int) -> list[str]:
    points = _require(op, "points", i)
    if len(points) < 2:
        raise AutocadError(
            f"Operation {i} (polyline) has {len(points)} vertices; at least 2 "
            "are required."
        )
    for n, vertex in enumerate(points):
        if len(vertex) < 2:
            raise AutocadError(
                f"Operation {i} (polyline) vertex {n} is {vertex!r}; every "
                "vertex needs at least [x, y]."
            )
    return _polyline_pairs(op, points, bool(op.get("closed", False)))


def _build_rectangle(op: dict[str, Any], i: int) -> list[str]:
    c1 = _require(op, "corner1", i)
    c2 = _require(op, "corner2", i)
    if len(c1) < 2 or len(c2) < 2:
        raise AutocadError(f"Operation {i} (rectangle) needs [x, y] corners.")
    x1, y1, x2, y2 = float(c1[0]), float(c1[1]), float(c2[0]), float(c2[1])
    if x1 == x2 or y1 == y2:
        raise AutocadError(
            f"Operation {i} (rectangle) corners {c1} and {c2} share an X or Y "
            "value, giving a rectangle with no area."
        )
    corners = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
    return _polyline_pairs(op, corners, closed=True)


BUILDERS = {
    "line": _build_line,
    "circle": _build_circle,
    "arc": _build_arc,
    "point": _build_point,
    "text": _build_text,
    "polyline": _build_polyline,
    "rectangle": _build_rectangle,
}


@mcp.tool(
    name="autocad_batch_draw",
    **tool_meta("Batch Draw Geometry"),
)
@tool_errors
async def autocad_batch_draw(
    operations: Annotated[
        list[dict[str, Any]],
        Field(
            description=(
                "Entities to create, in order. Each is an object with a 'type' "
                "and that type's fields, plus optional 'layer' and 'color'. "
                "Angles are DEGREES; coordinates are in the drawing's units.\n\n"
                'line: {"type":"line","start":[0,0],"end":[100,0]}\n'
                'polyline: {"type":"polyline","points":[[0,0],[10,0],[10,5]],'
                '"closed":true}\n'
                'rectangle: {"type":"rectangle","corner1":[0,0],'
                '"corner2":[100,50]}\n'
                'circle: {"type":"circle","center":[0,0],"radius":25} '
                "(or \"diameter\")\n"
                'arc: {"type":"arc","center":[0,0],"radius":25,'
                '"start_angle":0,"end_angle":90}\n'
                'text: {"type":"text","position":[0,0],"text":"ROOM 1",'
                '"height":2.5,"rotation":0}\n'
                'point: {"type":"point","position":[0,0]}\n\n'
                'Example with styling: {"type":"line","start":[0,0],'
                '"end":[5000,0],"layer":"A-WALL","color":"red"}'
            ),
            min_length=1,
            max_length=MAX_OPERATIONS,
        ),
    ],
    return_handles: Annotated[
        bool,
        Field(
            default=True,
            description=(
                "Return the handle of every entity created, so the batch can "
                "be modified or hatched afterwards. Capturing handles roughly "
                "doubles the run time, so turn it off for large batches you "
                "will not need to touch again — the created and failed counts "
                "are reported either way."
            ),
        ),
    ] = True,
) -> str:
    """Create many entities at once, far faster than one call per entity.

    Use this whenever you are drawing more than about ten things — a floor
    plan, a grid, a hatch pattern of lines, a set of labels. It sends a single
    AutoLISP script that runs inside AutoCAD, instead of one COM round trip per
    entity, and the whole batch lands as one undo step.

    Measured on AutoCAD 2020, 200 lines: 20.3s one at a time through the
    autocad_draw_* tools, 2.2s through this one — about 9x, or 17x with
    return_handles=false.

    Every operation is validated in Python before anything is sent, so a
    malformed batch fails naming the offending operation index and changes
    nothing in the drawing.

    Layers named by any operation are created automatically if they do not
    exist.

    Args:
        operations (list[dict]): The entities to create. See the field
            description for the shape of each type.
        return_handles (bool): Return each new entity's handle. Roughly doubles
            the run time; turn off for large batches you will not modify.

    Returns:
        str: JSON: {
          "created": int,          # entities actually made
          "failed": int,           # operations AutoCAD rejected
          "requested": int,
          "handles": [str],        # in order; empty if return_handles=false
          "completed": bool,       # false if the script died partway
          "layers_created": [str],
          "elapsed_seconds": float,
          "entities_per_second": float
        }

    Examples:
        - Use when: "draw this 20 x 15 m grid at 1 m spacing" — 36 lines in one
          call rather than 36.
        - Use when: placing a room's worth of walls, doors and labels together.
        - Don't use when: creating one or two entities, or when you need the
          richer validation and per-entity feedback of autocad_draw_* tools.

    Error Handling:
        - An unknown operation type, or a missing required field, is reported
          with its index before the batch runs.
        - If AutoCAD rejects individual operations (locked layer, degenerate
          geometry), "failed" counts them and "created" reflects what did land.
    """
    # Validate and generate everything up front: a batch that cannot be fully
    # built should not half-draw itself.
    entities: list[list[str]] = []
    layers_needed: set[str] = set()

    for index, op in enumerate(operations):
        if not isinstance(op, dict):
            raise AutocadError(
                f"Operation {index} is {type(op).__name__}, but each operation "
                "must be an object with a 'type' field."
            )
        kind = str(op.get("type", "")).strip().lower()
        if kind not in BUILDERS:
            raise AutocadError(
                f"Operation {index} has type '{op.get('type')}', which this "
                "tool cannot create. Supported types: "
                + ", ".join(sorted(BUILDERS))
                + ". For blocks, dimensions or hatches use the dedicated "
                "autocad_insert_block, autocad_add_dimension or "
                "autocad_add_hatch tools."
            )
        entities.append(BUILDERS[kind](op, index))
        if op.get("layer"):
            layers_needed.add(str(op["layer"]).strip())

    token = uuid.uuid4().hex[:12]
    output_path = os.path.join(tempfile.gettempdir(), f"mcp_batch_{token}.txt")
    # Built before anything is sent, so an operation too long to send fails
    # with its index and nothing half-drawn.
    chunks = build_chunks(entities, return_handles, output_path)

    def work() -> dict[str, Any]:
        doc = get_doc()
        require_idle(doc)
        # From here the drawing changes (layers, then the LISP batch): a busy
        # signal must not re-run it, and the gate must know it wrote.
        mark_writing()

        # entmake will not create a layer, so any that are missing are made
        # over COM first. This is a handful of calls, not one per entity.
        created_layers = []
        for layer_name in sorted(layers_needed):
            _, was_created = ensure_layer(doc, layer_name)
            if was_created:
                created_layers.append(layer_name)

        started = time.monotonic()
        # Short expressions, never a loaded file: a .lsp loaded from %TEMP%
        # makes AutoCAD's SECURELOAD ask about an unsigned executable. The
        # Heron plug-in types them with echo off; without it (or an older
        # plug-in) they go over COM and show in the command history.
        sender = quiet_sender()
        if not (sender and sender(chunks)):
            for chunk in chunks:
                doc.SendCommand(chunk + "\n")

        text = ""
        while time.monotonic() - started < OUTPUT_TIMEOUT:
            if os.path.isfile(output_path):
                with open(output_path, encoding="utf-8", errors="replace") as handle:
                    text = handle.read()
                if "DONE" in text or "ERROR " in text:
                    break
            time.sleep(OUTPUT_POLL)
        elapsed = time.monotonic() - started

        if not text:
            raise AutocadError(
                "The batch produced no output within "
                f"{OUTPUT_TIMEOUT:.0f}s. Check AutoCAD's command line (F2) for a "
                "prompt or an error waiting there, press Esc, and read the drawing "
                "back before retrying: part of the batch may already be drawn."
            )

        result = parse_output(text, expected=len(entities))
        result["layers_created"] = created_layers
        result["elapsed_seconds"] = round(elapsed, 3)
        if elapsed > 0:
            result["entities_per_second"] = round(result["created"] / elapsed, 1)
        return result

    try:
        return dumps(await run(work))
    finally:
        try:
            os.remove(output_path)
        except OSError:
            pass
