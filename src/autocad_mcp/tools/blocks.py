"""Make a named block from drawn objects.

Ajmal (2026-10-26): parts must be blocks, "otherwise the manual drawing person
cannot do anything". Draw the part's geometry, then turn it into a block: the
objects are copied into a new block definition (their world positions kept,
relative to ``base_point``), removed, and one insert of the block takes their
place, so the drawing looks the same but the part now moves, copies and counts
as one piece. One undo step.
"""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from ..acad.entities import resolve_handles
from ..acad.tables import apply_properties
from ..core.connection import get_doc, get_space, require_idle, run
from ..core.errors import AutocadError
from ..core.registry import dumps, mcp, tool_errors, tool_meta, undo_mark
from ..core.variants import object_array
from ._shared import LAYER_OPT, point


@mcp.tool(name="autocad_make_block", **tool_meta("Make Block from Objects"))
@tool_errors
async def autocad_make_block(
    name: Annotated[str, Field(min_length=1, description="New block name, e.g. 'SHS 100x100x5 POST'.")],
    handles: Annotated[list[str], Field(min_length=1, description="Handles of the objects that make up the part.")],
    base_point: Annotated[list[float], Field(description="Block base point [x, y]: the point you insert it by.")],
    layer: Annotated[str | None, LAYER_OPT] = None,
    keep_originals: Annotated[
        bool, Field(description="True: only define the block; leave the objects and insert nothing.")
    ] = False,
) -> str:
    """Turn drawn objects into a named block, and put the block where they were.

    Use for every separate part (fitting, elbow, clamp, plate, anchor, support
    piece) so it can be moved, copied, swapped and counted as one. Draw the part,
    then call this with its handles. Insert more copies with autocad_insert_block.
    Pipes and runs can stay as lines or polylines.

    Returns:
        JSON: {"created": true, "block": name, "handle": insert handle (null when keep_originals)}
    """

    def work() -> dict[str, Any]:
        doc = get_doc()
        require_idle(doc)
        try:
            doc.Blocks.Item(name)
        except Exception:  # noqa: BLE001 - not found is what we want
            pass
        else:
            raise AutocadError(
                f"A block named '{name}' already exists in this drawing. Insert it with "
                "autocad_insert_block, or choose another name."
            )
        objects = resolve_handles(doc, handles)
        with undo_mark(doc):
            definition = doc.Blocks.Add(point(base_point, "base_point"), name)
            doc.CopyObjects(object_array(objects), definition)
            if keep_originals:
                return {"created": True, "block": name, "handle": None, "objects": len(objects)}
            for obj in objects:
                obj.Delete()
            ref = get_space(doc, "model").InsertBlock(point(base_point, "base_point"), name, 1.0, 1.0, 1.0, 0.0)
            notes = apply_properties(doc, ref, layer, None, None)
        return {"created": True, "block": name, "handle": str(ref.Handle), "objects": len(objects), **notes}

    return dumps(await run(work))
