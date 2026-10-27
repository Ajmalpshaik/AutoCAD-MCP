"""Materials and rendering: how a model looks, as opposed to what shape it is.

What AutoCAD's automation interface actually allows here is narrower than the
Materials Browser suggests, and the difference matters enough to state up
front:

* **Every entity has a ``Material`` property**, a string naming a material in
  the drawing. Setting it is how a material gets applied, and that works.
* **A material has to already be in the drawing.** There is no automation route
  into Autodesk's material library, so a name that is not in the drawing cannot
  be created from here. These tools say so and list what *is* there, rather
  than failing with a shrug.
* **A material carries no density.** It is appearance only. MASSPROP and this
  server's ``autocad_solid_properties`` both work as if density were 1, so a
  weight is volume times a density *you* supply. Assigning "Steel" to a solid
  does not make it weigh anything.
* **Rendering has no automation call at all.** The only route is the ``-render``
  command, so ``autocad_render`` drives that — which is why it needs the Admin
  padlock, and why it reports what it sent rather than pretending to more
  certainty than it has.

The honest summary: materials can be listed and applied; a render can be asked
for; neither can be invented from nothing.
"""

from __future__ import annotations

import os
from typing import Annotated, Any, Literal

from pydantic import Field

from ..acad.entities import resolve_handles, short_type
from ..acad.selection import select_filtered
from ..core.connection import get_doc, require_idle, run
from ..core.errors import AutocadError, com_message
from ..core.registry import dumps, mcp, tool_errors, tool_meta, undo_mark

# AutoCAD's built-in render presets, in the order its own prompt lists them.
RENDER_PRESETS = ("Low", "Medium", "High", "Coffee-Break", "Lunch", "Overnight")

# Common image sizes for a render, so a sensible one can be named.
RENDER_SIZES: dict[str, tuple[int, int]] = {
    "small": (800, 600),
    "medium": (1280, 960),
    "large": (1920, 1440),
    "print": (3300, 2550),
}


def _try(getter, default=None):
    try:
        return getter()
    except BaseException:  # noqa: BLE001 - absent properties are expected here
        return default


def material_names(doc: Any) -> list[str]:
    """Every material in the drawing, by name.

    The Materials collection is iterated by index rather than with ``for``,
    because the COM collection does not always present a Python iterator.
    """
    found: list[str] = []
    table = _try(lambda: doc.Materials)
    if table is None:
        return found
    count = _try(lambda: int(table.Count), 0) or 0
    for i in range(count):
        item = _try(lambda i=i: table.Item(i))
        if item is None:
            continue
        name = _try(lambda it=item: str(it.Name))
        if name:
            found.append(name)
    return found


def match_name(wanted: str, available: list[str]) -> str | None:
    """The material in the drawing that the caller meant, ignoring case."""
    lowered = {name.lower(): name for name in available}
    return lowered.get(wanted.strip().lower())


@mcp.tool(name="autocad_list_materials", **tool_meta("List Materials"))
@tool_errors
async def autocad_list_materials() -> str:
    """List the materials in this drawing, and which objects are using them.

    Worth running before you try to apply one: only a material already in the
    drawing can be applied, and this is the list of those. If what you want is
    not here, it has to be brought in through AutoCAD's own Materials Browser
    first — there is no automation route into Autodesk's library.

    Reads only.

    Returns:
        str: JSON: {"count": int, "materials": [{"name", "description",
             "in_use": int}], "note": str}

    Examples:
        - Use when: "what materials does this drawing have" before applying one.
        - Use when: a material name was refused and you need the real spelling.
        - Don't use when: you want the weight of something — a material carries
          no density. Use autocad_solid_properties for the volume and multiply
          by a density you state.
    """

    def work() -> dict[str, Any]:
        doc = get_doc()
        names = material_names(doc)
        used: dict[str, int] = {}
        space = _try(lambda: doc.ModelSpace)
        if space is not None:
            count = _try(lambda: int(space.Count), 0) or 0
            for i in range(count):
                item = _try(lambda i=i: space.Item(i))
                name = _try(lambda it=item: str(it.Material)) if item is not None else None
                if name:
                    used[name] = used.get(name, 0) + 1

        table = _try(lambda: doc.Materials)
        rows = []
        for name in names:
            entry = _try(lambda n=name: table.Item(n)) if table is not None else None
            rows.append({
                "name": name,
                "description": _try(lambda e=entry: str(e.Description)) if entry else None,
                "in_use": used.get(name, 0),
            })
        return {
            "count": len(rows),
            "materials": rows,
            "note": (
                "Only a material listed here can be applied. Bring others in through "
                "AutoCAD's Materials Browser first: automation cannot reach the library. "
                "A material is appearance only and carries no density."
            ),
        }

    return dumps(await run(work))


@mcp.tool(name="autocad_apply_material", **tool_meta("Apply A Material"))
@tool_errors
async def autocad_apply_material(
    material: Annotated[
        str,
        Field(
            min_length=1,
            description=(
                "The material's name, exactly as it is in the drawing — "
                "autocad_list_materials gives the spellings. Pass 'ByLayer' to hand the "
                "objects back to their layer's material."
            ),
        ),
    ],
    handles: Annotated[list[str] | None, Field(default=None, description="The objects to apply it to. Give this or layer_filter.")] = None,
    layer_filter: Annotated[str | None, Field(default=None, description="Apply it to everything on this layer instead, e.g. 'S-BEAM'. Wildcards allowed, as in 'A-WALL*'.")] = None,
    solids_only: Annotated[bool, Field(default=True, description="Only apply it to 3D solids. On by default: a material on a line does nothing but clutter the drawing.")] = True,
) -> str:
    """Apply a material to objects, for rendering and shaded views.

    Materials change how a model *looks* — in a shaded or realistic visual
    style, and in a render. They do not change its geometry and they do not
    give it a weight.

    The material must already be in the drawing. If it is not, this says so and
    lists what is, rather than silently doing nothing.

    One undo step.

    Args:
        material (str): the material's name, or 'ByLayer'.
        handles (Optional[list[str]]): the objects. Give this or layer_filter.
        layer_filter (Optional[str]): apply to everything on this layer.
        solids_only (bool): skip anything that is not a 3D solid. Default true.

    Returns:
        str: JSON: {"material", "applied": int, "skipped": int,
             "handles": [str], "failed": [{"handle", "reason"}]}

    Examples:
        - Use when: "make those beams look like steel" — material='Steel',
          layer_filter='S-BEAM'.
        - Use when: "put the concrete material on the slab" before a render or
          a shaded view.
        - Don't use when: the material is not in the drawing yet — bring it in
          with AutoCAD's Materials Browser first; autocad_list_materials shows
          what is available.
    """
    if bool(handles) == bool(layer_filter):
        raise AutocadError("Give either 'handles' or 'layer_filter' — one of the two.")
    wanted = material.strip()

    def work() -> dict[str, Any]:
        doc = get_doc()
        require_idle(doc)
        available = material_names(doc)
        by_layer = wanted.lower() == "bylayer"
        real = "ByLayer" if by_layer else match_name(wanted, available)
        if real is None:
            raise AutocadError(
                f"There is no material called '{wanted}' in this drawing. "
                + (f"It has: {', '.join(sorted(available))}. " if available else "It has none. ")
                + "A material has to be brought in through AutoCAD's Materials Browser "
                "first — automation cannot reach Autodesk's library."
            )

        if handles:
            targets = list(resolve_handles(doc, handles))
        else:
            targets = list(select_filtered(doc, layer=layer_filter))

        applied: list[str] = []
        failed: list[dict[str, Any]] = []
        skipped = 0
        with undo_mark(doc):
            for entity in targets:
                handle = _try(lambda e=entity: str(e.Handle), "?")
                if solids_only and short_type(entity) != "3dsolid":
                    skipped += 1
                    continue
                try:
                    entity.Material = real
                except BaseException as exc:  # noqa: BLE001
                    failed.append({"handle": handle, "reason": com_message(exc)})
                    continue
                applied.append(handle)

        payload: dict[str, Any] = {
            "material": real,
            "applied": len(applied),
            "handles": applied,
        }
        if skipped:
            payload["skipped"] = skipped
            payload["skipped_note"] = (
                "Not 3D solids, so a material would not show. Pass solids_only=false to "
                "apply it anyway."
            )
        if failed:
            payload["failed"] = failed
        if not applied:
            raise AutocadError(
                f"'{real}' was applied to nothing. "
                + (f"{skipped} object(s) were not 3D solids. " if skipped else "")
                + "; ".join(f"{f['handle']}: {f['reason']}" for f in failed)
            )
        payload["note"] = (
            "Set a shaded or realistic visual style to see it: "
            "autocad_set_3d_view(visual_style='realistic')."
        )
        return payload

    return dumps(await run(work))


@mcp.tool(name="autocad_render", **tool_meta("Render The Model"))
@tool_errors
async def autocad_render(
    output_path: Annotated[
        str,
        Field(
            min_length=1,
            description=(
                "Where to write the image, with its extension — .png, .jpg or .tif. An "
                "absolute Windows path, e.g. 'C:/Jobs/A-101/view.png'."
            ),
        ),
    ],
    preset: Annotated[
        Literal["Low", "Medium", "High", "Coffee-Break", "Lunch", "Overnight"],
        Field(
            default="Medium",
            description=(
                "Render quality, as AutoCAD names it. Low and Medium are quick looks; "
                "Coffee-Break, Lunch and Overnight are named for how long they take, "
                "and they mean it."
            ),
        ),
    ] = "Medium",
    size: Annotated[
        Literal["small", "medium", "large", "print"],
        Field(default="medium", description="Image size: small 800x600, medium 1280x960, large 1920x1440, print 3300x2550."),
    ] = "medium",
    width: Annotated[int | None, Field(default=None, ge=16, le=10000, description="An exact width in pixels instead of 'size'.")] = None,
    height: Annotated[int | None, Field(default=None, ge=16, le=10000, description="An exact height in pixels instead of 'size'.")] = None,
) -> str:
    """Render the current view to an image file.

    **Read this before using it.** Rendering has no automation call in AutoCAD;
    the only route is the ``-render`` command, so this sends that command and
    its answers. Three consequences, all of them real:

    * It needs the **Admin** padlock, because it drives the command line.
    * The prompt wording differs between releases, so the command can stall
      part-way waiting for an answer this tool did not anticipate. If the image
      does not appear, press Esc in AutoCAD and render by hand.
    * Rendering from a script has been reported to drop objects that render
      correctly when done by hand. Check the image before you send it to anyone.

    What is reliable: set the view with ``autocad_set_3d_view`` and apply
    materials with ``autocad_apply_material`` first — those do work — and for a
    picture to put on a drawing, ``autocad_preview`` or ``autocad_export`` is
    the dependable route.

    Args:
        output_path (str): where to write the image, with its extension.
        preset (str): Low, Medium, High, Coffee-Break, Lunch or Overnight.
        size (str): small, medium, large or print.
        width / height (Optional[int]): exact pixels instead of 'size'.

    Returns:
        str: JSON: {"sent": str, "output_path", "preset", "width", "height",
             "exists": bool, "size_bytes": int | null, "note": str}

    Examples:
        - Use when: "render this view for the client" — after setting the view
          and applying materials.
        - Don't use when: you want to see what you drew — autocad_preview is
          instant, needs no padlock and always works.
        - Don't use when: the picture goes on a drawing sheet — that is
          autocad_export to PDF.
    """
    if (width is None) != (height is None):
        raise AutocadError("Give both width and height, or neither and use 'size'.")
    px = (int(width), int(height)) if width is not None else RENDER_SIZES[size]
    target = output_path.strip().replace("/", "\\")
    if "." not in target.rsplit("\\", 1)[-1]:
        raise AutocadError(
            f"'{output_path}' has no file extension. Render output needs one: .png, .jpg or .tif."
        )

    def work() -> dict[str, Any]:
        doc = get_doc()
        require_idle(doc)
        # -render asks, in order: preset, destination, width, height, file name.
        line = f'-render\n{preset}\nFile\n{px[0]}\n{px[1]}\n{target}\n'
        try:
            doc.SendCommand(line)
        except BaseException as exc:  # noqa: BLE001
            raise AutocadError(
                f"AutoCAD would not take the render command ({com_message(exc)}). "
                "Render by hand instead: set the view, then RENDER."
            ) from exc

        exists = os.path.isfile(target)
        return {
            "sent": line.replace("\n", " | ").strip(),
            "output_path": target,
            "preset": preset,
            "width": px[0],
            "height": px[1],
            "exists": exists,
            "size_bytes": os.path.getsize(target) if exists else None,
            "note": (
                "The image was found." if exists else
                "The file is not there yet. A render at this preset can take minutes, and "
                "the command may be waiting for an answer on AutoCAD's command line — look "
                "at it. If it is stuck, press Esc and render by hand."
            ),
        }

    return dumps(await run(work))
