"""Take-off: count blocks, total lengths and areas, read and set dynamic block properties.

The ideas come from Lee Mac's Block Counter, Total Length & Area and Dynamic
Block Functions (lee-mac.com). This is Heron's own code, written from the
AutoCAD ActiveX reference: none of Lee Mac's code is used or copied (his terms
do not allow redistribution, D-26).

Grouping and type matching are plain functions over plain data, tested
without AutoCAD; the tools only gather that data over COM.
"""

from __future__ import annotations

import fnmatch
from typing import Annotated, Any, Literal

from pydantic import Field

from ..acad.curves import curve_length
from ..acad.entities import resolve_handle
from ..acad.selection import discard_selection_set, iter_selection, select_filtered
from ..core.connection import get_doc, require_idle, run
from ..core.errors import AutocadError
from ..core.registry import dumps, mcp, tool_errors, tool_meta, undo_mark

BlockGroup = Literal["name", "name_layer", "name_visibility", "name_properties"]
LengthGroup = Literal["layer", "type", "none"]


def count_blocks(refs: list[dict], group_by: BlockGroup) -> dict[str, Any]:
    """Count block references. Pure: refs are {block, layer, visibility, properties}."""
    keys = {
        "name": ("block",),
        "name_layer": ("block", "layer"),
        "name_visibility": ("block", "visibility"),
        "name_properties": ("block", "properties"),
    }[group_by]
    counts: dict[tuple, dict[str, Any]] = {}
    for ref in refs:
        row = {key: ref.get(key) for key in keys}
        marker = tuple(repr(sorted(v.items())) if isinstance(v, dict) else repr(v) for v in row.values())
        counts.setdefault(marker, {**row, "count": 0})["count"] += 1
    rows = sorted(counts.values(), key=lambda r: tuple(str(r.get(k)) for k in keys))
    return {"total": len(refs), "rows": rows}


def total_lengths(items: list[dict], group_by: LengthGroup) -> dict[str, Any]:
    """Sum length and area. Pure: items are {type, layer, length, area}, None when not measurable."""
    groups: dict[str, dict[str, Any]] = {}
    for item in items:
        key = "all" if group_by == "none" else str(item.get(group_by))
        row = groups.setdefault(key, {group_by if group_by != "none" else "group": key, "count": 0, "length": 0.0, "area": 0.0, "unmeasured": 0})
        row["count"] += 1
        if item.get("length") is None:
            row["unmeasured"] += 1
        else:
            row["length"] += float(item["length"])
        if item.get("area"):
            row["area"] += float(item["area"])
    rows = [groups[k] for k in sorted(groups)]
    return {
        "total_length": sum(r["length"] for r in rows),
        "total_area": sum(r["area"] for r in rows),
        "rows": rows,
    }


def coerce_value(current: Any, new: Any, allowed: list | None = None) -> Any:
    """Turn a requested value into the type the property already holds.

    A dynamic property refuses a value of the wrong COM type (a string for a
    distance), and agents often send numbers as text, so the current value's
    type decides. A list of allowed values, when the block has one, is enforced.
    """
    if isinstance(current, bool):
        value: Any = str(new).strip().lower() in {"1", "true", "yes", "on"}
    elif isinstance(current, int):
        value = int(float(new))
    elif isinstance(current, float):
        value = float(new)
    else:
        value = str(new)
    if allowed:
        matches = [a for a in allowed if a == value or (isinstance(a, str) and str(a).lower() == str(value).lower())]
        if not matches:
            raise ValueError(f"{new!r} is not one of the allowed values: {list(allowed)}")
        value = matches[0]
    return value


def _length(entity: Any) -> float | None:
    return curve_length(entity)


def expand_nested(refs: list[dict], children: dict[str, list[tuple[str, str]]], limit: int = 20) -> list[dict]:
    """Top-level refs plus every block nested inside them, once per placed copy.

    children: block name -> [(nested block name, layer)] as defined. A block
    that contains itself stops at 'limit' levels instead of looping forever.
    """
    out = list(refs)

    def walk(name: str, depth: int) -> None:
        if depth >= limit:
            return
        for child, layer in children.get(name, []):
            out.append({"block": child, "layer": layer, "visibility": None, "properties": {}, "nested": True})
            walk(child, depth + 1)

    for ref in refs:
        walk(ref["block"], 1)
    return out


def _children(doc: Any) -> dict[str, list[tuple[str, str]]]:
    out: dict[str, list[tuple[str, str]]] = {}
    for i in range(doc.Blocks.Count):
        block = doc.Blocks.Item(i)
        try:
            if block.IsLayout or block.IsXRef:
                continue
            name = str(block.Name)
            for j in range(int(block.Count)):
                item = block.Item(j)
                if str(item.ObjectName) == "AcDbBlockReference":
                    out.setdefault(name, []).append((str(getattr(item, "EffectiveName", None) or item.Name), str(item.Layer)))
        except BaseException:  # noqa: BLE001
            continue
    return out


_ALWAYS_CLOSED = {"AcDbCircle", "AcDbRegion"}


def _area(entity: Any) -> float | None:
    """Area of a closed shape only: COM also gives open polylines and arcs an area."""
    try:
        if str(entity.ObjectName) not in _ALWAYS_CLOSED and not bool(getattr(entity, "Closed", False)):
            return None
        return float(entity.Area)
    except BaseException:  # noqa: BLE001
        return None


def _dynamic_properties(ref: Any) -> list[Any]:
    try:
        if not ref.IsDynamicBlock:
            return []
        return list(ref.GetDynamicBlockProperties())
    except BaseException:  # noqa: BLE001 - not a block reference
        return []


def _plain(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def _describe_ref(ref: Any) -> dict[str, Any]:
    visibility = None
    properties: dict[str, Any] = {}
    for prop in _dynamic_properties(ref):
        name = str(prop.PropertyName)
        if name.lower().startswith("visibility"):
            visibility = _plain(prop.Value)
        elif not prop.ReadOnly and name.lower() != "origin":
            properties[name] = _plain(prop.Value)
    return {
        "block": str(getattr(ref, "EffectiveName", None) or ref.Name),
        "layer": str(ref.Layer),
        "visibility": visibility,
        "properties": properties,
    }


@mcp.tool(name="autocad_count_blocks", **tool_meta("Count Blocks", read_only=True, idempotent=True))
@tool_errors
async def autocad_count_blocks(
    block_name: Annotated[str | None, Field(description="Only blocks whose real name matches, wildcards allowed: 'VALVE*'.")] = None,
    layer: Annotated[str | None, Field(description="Only blocks on this layer (wildcards allowed).")] = None,
    group_by: Annotated[BlockGroup, Field(description=(
        "name; name_layer; name_visibility (dynamic block visibility state); "
        "name_properties (dynamic property values such as size)."
    ))] = "name",
    include_nested: Annotated[bool, Field(description="Also count blocks inside blocks (e.g. fixtures inside a room block).")] = False,
) -> str:
    """Count block references for a quantity take-off: fittings, valves, devices.

    Dynamic blocks are counted by their real name, not the *U names AutoCAD
    gives their copies. Group by visibility state or property values to count
    each size or type separately.

    Returns:
        JSON: {"total": n, "rows": [{"block", ..., "count"}]}
    """

    def work() -> list[dict[str, Any]]:
        doc = get_doc()
        sel = select_filtered(doc, entity_type="insert", layer=layer)
        refs: list[dict[str, Any]] = []
        try:
            for ref in iter_selection(sel):
                try:
                    row = _describe_ref(ref)
                except BaseException:  # noqa: BLE001 - not a block reference after all
                    continue
                refs.append(row)
        finally:
            discard_selection_set(doc)
        if include_nested:  # walk every top-level block: a DESK can sit inside a ROOM
            refs = expand_nested(refs, _children(doc))
        if block_name:
            refs = [r for r in refs if fnmatch.fnmatch(r["block"].lower(), block_name.lower())]
        return refs

    return dumps(count_blocks(await run(work), group_by))


@mcp.tool(name="autocad_total_length", **tool_meta("Total Length and Area", read_only=True, idempotent=True))
@tool_errors
async def autocad_total_length(
    entity_type: Annotated[str | None, Field(description="Only this type: line, polyline, arc, circle...")] = None,
    layer: Annotated[str | None, Field(description="Only this layer (wildcards allowed: 'P-*').")] = None,
    group_by: Annotated[LengthGroup, Field(description="layer, type, or none for one total.")] = "layer",
) -> str:
    """Total length (and area of closed shapes) for a run take-off: pipe, duct, cable.

    Lengths are in drawing units (check autocad_status). Splines and ellipses
    are measured from their definition.

    Returns:
        JSON: {"total_length", "total_area", "rows": [{layer|type, count, length, area, unmeasured}]}
    """

    def work() -> list[dict[str, Any]]:
        doc = get_doc()
        sel = select_filtered(doc, entity_type=entity_type, layer=layer)
        items: list[dict[str, Any]] = []
        try:
            for entity in iter_selection(sel):
                kind = str(entity.ObjectName)
                if kind in {"AcDbBlockReference", "AcDbText", "AcDbMText", "AcDbHatch"} or "Dimension" in kind:
                    continue
                items.append({"type": kind, "layer": str(entity.Layer), "length": _length(entity), "area": _area(entity)})
        finally:
            discard_selection_set(doc)
        return items

    return dumps(total_lengths(await run(work), group_by))


@mcp.tool(name="autocad_get_dynamic_properties", **tool_meta("Get Dynamic Block Properties", read_only=True, idempotent=True))
@tool_errors
async def autocad_get_dynamic_properties(
    handle: Annotated[str, Field(min_length=1, description="Handle of a dynamic block reference.")],
) -> str:
    """List a dynamic block's properties: value, allowed choices, read-only.

    Use before autocad_set_dynamic_properties to see the names and choices
    (visibility states, lookup sizes, stretch distances).

    Returns:
        JSON: {"handle", "block", "properties": [{name, value, allowed, read_only, description}]}
    """

    def work() -> dict[str, Any]:
        doc = get_doc()
        ref = resolve_handle(doc, handle)
        props = _dynamic_properties(ref)
        if not props:
            raise AutocadError(f"'{handle}' is not a dynamic block reference.")
        return {
            "handle": str(ref.Handle),
            "block": str(getattr(ref, "EffectiveName", None) or ref.Name),
            "properties": [
                {
                    "name": str(p.PropertyName),
                    "value": _plain(p.Value),
                    "allowed": _plain(list(p.AllowedValues or ())),
                    "read_only": bool(p.ReadOnly),
                    "description": str(p.Description),
                }
                for p in props
            ],
        }

    return dumps(await run(work))


@mcp.tool(name="autocad_set_dynamic_properties", **tool_meta("Set Dynamic Block Properties"))
@tool_errors
async def autocad_set_dynamic_properties(
    handle: Annotated[str, Field(min_length=1, description="Handle of a dynamic block reference.")],
    values: Annotated[dict[str, Any], Field(description="{property name: new value}, e.g. {'Visibility1': 'GATE', 'Size': 80}.")],
) -> str:
    """Change a dynamic block's properties: visibility state, size, distance, flip.

    Names are matched without regard to case. Each value is converted to the
    property's own type and checked against its allowed values; the ones that
    cannot be set are listed in 'failed' with the reason. One undo step.

    Returns:
        JSON: {"handle", "changed": {name: value}, "failed": {name: reason}}
    """

    def work() -> dict[str, Any]:
        doc = get_doc()
        require_idle(doc)
        ref = resolve_handle(doc, handle)
        props = {str(p.PropertyName).lower(): p for p in _dynamic_properties(ref)}
        if not props:
            raise AutocadError(f"'{handle}' is not a dynamic block reference.")
        changed: dict[str, Any] = {}
        failed: dict[str, str] = {}
        with undo_mark(doc):
            for name, new in values.items():
                prop = props.get(str(name).lower())
                if prop is None:
                    failed[name] = "no such property; see autocad_get_dynamic_properties"
                    continue
                label = str(prop.PropertyName)
                if prop.ReadOnly:
                    failed[label] = "read-only"
                    continue
                try:
                    value = coerce_value(prop.Value, new, _plain(list(prop.AllowedValues or ())))
                    prop.Value = value
                    changed[label] = value
                except BaseException as exc:  # noqa: BLE001 - report and carry on
                    failed[label] = str(exc)
        return {"handle": str(ref.Handle), "changed": changed, "failed": failed}

    return dumps(await run(work))
