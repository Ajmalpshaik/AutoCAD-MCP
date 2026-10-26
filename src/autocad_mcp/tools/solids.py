"""3D: solids, profiles turned into solids, booleans, and looking at the result.

What a modeller needs to go from a flat drawing to a model and back:

* **Primitives** - box, wedge, cylinder, cone, sphere, torus. A duct, a pad, a
  bollard, a tank.
* **A profile into a solid** - draw the section flat, then extrude it along Z
  or revolve it about an axis. Every real part starts this way.
* **Booleans** - union, subtract, intersect. A plate with holes in it is a box
  minus some cylinders.
* **Mass properties** - volume, centroid, bounding box. What a weight takes-off
  needs.
* **Looking at it** - a named 3D direction and a visual style, so the modeller
  (and ``autocad_preview``) can actually see the model.
* **3D paths** - a pipe route or a helix as one 3D polyline.

A note on where the geometry lands: AutoCAD's primitive calls place a solid by
the **centre of its bounding box**, with the base on the current XY plane. That
is not where a drafter expects a box to go, so these tools take the base centre
and work the rest out, and report both.
"""

from __future__ import annotations

import math
from typing import Annotated, Any, Literal

from pydantic import Field, StrictInt

from ..acad.entities import describe, resolve_handle, resolve_handles, short_type
from ..acad.tables import apply_properties, ensure_layer
from ..acad.units import rad
from ..core.connection import get_doc, get_space, require_idle, run
from ..core.errors import AutocadError, com_message
from ..core.registry import dumps, mcp, to_aci, tool_errors, tool_meta, undo_mark
from ..core.variants import apoint, double_array, object_array, point_to_list
from ._shared import (
    COLOR_OPT,
    COORDS_OPT,
    LAYER_OPT,
    created_payload,
    ucs_for,
    world_coords,
)

# AcBooleanType: the Boolean method's operation. The first object is the one
# that changes; the second is consumed.
BOOLEAN_OPS = {"union": 0, "intersect": 1, "subtract": 2}

# AcRegenType: acActiveViewport = 0, acAllViewports = 1.
AC_ALL_VIEWPORTS = 1

# Where a named view looks from, as a direction vector. Same names AutoCAD's
# own View panel uses.
VIEW_DIRECTIONS: dict[str, tuple[float, float, float]] = {
    "top": (0.0, 0.0, 1.0),
    "plan": (0.0, 0.0, 1.0),
    "bottom": (0.0, 0.0, -1.0),
    "front": (0.0, -1.0, 0.0),
    "back": (0.0, 1.0, 0.0),
    "left": (-1.0, 0.0, 0.0),
    "right": (1.0, 0.0, 0.0),
    "sw_iso": (-1.0, -1.0, 1.0),
    "se_iso": (1.0, -1.0, 1.0),
    "ne_iso": (1.0, 1.0, 1.0),
    "nw_iso": (-1.0, 1.0, 1.0),
}

# VSCURRENT takes the style's name. These are the ones AutoCAD ships.
VISUAL_STYLES = (
    "2dwireframe", "wireframe", "hidden", "realistic", "conceptual",
    "shaded", "shaded with edges", "shades of gray", "sketchy", "x-ray",
)

Primitive = Literal["box", "wedge", "cylinder", "cone", "sphere", "torus"]


def _try(getter, default=None):
    try:
        return getter()
    except BaseException:  # noqa: BLE001 - absent properties are expected here
        return default


def _write(target: Any, name: str, value: Any) -> bool:
    try:
        setattr(target, name, value)
        return True
    except BaseException:  # noqa: BLE001 - a refusal is the answer, not a crash
        return False


def helix_points(
    radius: float,
    turns: float,
    height: float,
    top_radius: float | None = None,
    centre: tuple[float, float, float] = (0.0, 0.0, 0.0),
    per_turn: int = 36,
) -> list[list[float]]:
    """The points of a helix, as a 3D path. Pure, so it is tested without AutoCAD.

    ``top_radius`` different from ``radius`` gives a conical coil. A negative
    height winds downward. The last point closes the final turn exactly, so a
    whole number of turns comes back round to its starting angle.
    """
    if radius <= 0.0:
        raise ValueError(f"a helix needs a radius above zero, got {radius:g}")
    if turns <= 0.0:
        raise ValueError(f"a helix needs more than zero turns, got {turns:g}")
    if top_radius is not None and top_radius <= 0.0:
        raise ValueError(f"top_radius must be above zero, got {top_radius:g}")
    steps = max(8, int(round(per_turn * turns)))
    cx, cy, cz = centre
    r1 = radius if top_radius is None else float(top_radius)
    out = []
    for i in range(steps + 1):
        t = i / steps
        angle = 2.0 * math.pi * turns * t
        r = radius + (r1 - radius) * t
        out.append(
            [
                round(cx + r * math.cos(angle), 9),
                round(cy + r * math.sin(angle), 9),
                round(cz + height * t, 9),
            ]
        )
    return out


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------


@mcp.tool(name="autocad_add_solid", **tool_meta("Add A 3D Solid"))
@tool_errors
async def autocad_add_solid(
    shape: Annotated[
        Primitive,
        Field(
            description=(
                "'box' and 'wedge' need length, width and height. 'cylinder' and 'cone' "
                "need radius (or diameter) and height. 'sphere' needs radius. 'torus' "
                "needs radius and tube_radius."
            )
        ),
    ],
    base: Annotated[
        list[float],
        Field(
            description=(
                "The centre of the solid's **base**, as [x, y] or [x, y, z] — where a "
                "drafter would put it. For a sphere and a torus this is the centre of the "
                "shape itself, since neither has a flat base."
            )
        ),
    ],
    length: Annotated[float | None, Field(default=None, gt=0, description="Box and wedge: size along X.")] = None,
    width: Annotated[float | None, Field(default=None, gt=0, description="Box and wedge: size along Y.")] = None,
    height: Annotated[float | None, Field(default=None, gt=0, description="Box, wedge, cylinder and cone: size along Z.")] = None,
    radius: Annotated[float | None, Field(default=None, gt=0, description="Cylinder, cone, sphere: the radius. Torus: the radius of the ring itself.")] = None,
    diameter: Annotated[float | None, Field(default=None, gt=0, description="Instead of radius — how a pipe or a bollard is normally called out.")] = None,
    tube_radius: Annotated[float | None, Field(default=None, gt=0, description="Torus: the radius of the tube going round the ring.")] = None,
    layer: Annotated[str | None, LAYER_OPT] = None,
    color: Annotated[str | StrictInt | None, COLOR_OPT] = None,
    coords: Annotated[str, COORDS_OPT] = "world",
) -> str:
    """Make a 3D solid primitive, placed by the centre of its base.

    AutoCAD's own calls place a solid by the centre of its bounding box, which
    is halfway up it. That is never where you mean, so these take the **base
    centre** and work the rest out — a 300 high cylinder at z=0 sits on z=0.
    Both points come back in the result.

    One undo step.

    Args:
        shape (str): box, wedge, cylinder, cone, sphere or torus.
        base (list[float]): centre of the base ([x, y] or [x, y, z]).
        length / width / height (Optional[float]): as the shape needs.
        radius / diameter (Optional[float]): as the shape needs.
        tube_radius (Optional[float]): torus only.
        layer (Optional[str]): target layer, created if missing.
        color (Optional[str | int]): colour.
        coords (str): 'world' or 'ucs'.

    Returns:
        str: JSON: {"created": true, "handle": str, "type": str, "shape": str,
             "base": [x, y, z], "centre": [x, y, z], "volume": float,
             "bounding_box": {"min", "max"}}

    Examples:
        - Use when: "a 2400 x 1200 x 200 concrete pad at the origin" —
          shape='box'.
        - Use when: "a 300 diameter column 3000 high" — shape='cylinder',
          diameter=300, height=3000.
        - Don't use when: the part is really a 2D section to be extruded —
          draw the profile and use autocad_extrude_profile, which gets the real
          shape rather than a box that is nearly it.

    Error Handling:
        - Each shape names exactly the sizes it needs and which were missing.
        - radius and diameter together are refused rather than one quietly winning.
    """
    if radius is not None and diameter is not None:
        raise AutocadError("Give radius or diameter, not both.")
    r = float(radius) if radius is not None else (float(diameter) / 2.0 if diameter else None)

    needs: dict[str, tuple[str, ...]] = {
        "box": ("length", "width", "height"),
        "wedge": ("length", "width", "height"),
        "cylinder": ("radius", "height"),
        "cone": ("radius", "height"),
        "sphere": ("radius",),
        "torus": ("radius", "tube_radius"),
    }
    have = {"length": length, "width": width, "height": height, "radius": r,
            "tube_radius": tube_radius}
    missing = [n for n in needs[shape] if have.get(n) is None]
    if missing:
        raise AutocadError(
            f"'{shape}' needs {', '.join(needs[shape])}; missing {', '.join(missing)}."
            + (" radius can be given as diameter instead." if "radius" in missing else "")
        )
    if shape == "torus" and float(tube_radius) >= r:
        raise AutocadError(
            f"the tube radius ({float(tube_radius):g}) must be smaller than the ring radius "
            f"({r:g}), or the torus closes on itself"
        )
    aci = to_aci(color)

    def work() -> dict[str, Any]:
        doc = get_doc()
        require_idle(doc)
        ucs = ucs_for(doc, coords)
        target = get_space(doc, "model")
        bx, by, bz = world_coords(base, ucs)

        # AutoCAD places these by the centre of the bounding box. A sphere and a
        # torus have no base, so their centre is the point given; everything
        # else rises from its base, so the centre is half a height up.
        lift = 0.0 if shape in ("sphere", "torus") else float(height) / 2.0
        cx, cy, cz = bx, by, bz + lift
        centre = apoint(cx, cy, cz)

        with undo_mark(doc):
            try:
                if shape == "box":
                    solid = target.AddBox(centre, float(length), float(width), float(height))
                elif shape == "wedge":
                    solid = target.AddWedge(centre, float(length), float(width), float(height))
                elif shape == "cylinder":
                    solid = target.AddCylinder(centre, r, float(height))
                elif shape == "cone":
                    solid = target.AddCone(centre, r, float(height))
                elif shape == "sphere":
                    solid = target.AddSphere(centre, r)
                else:
                    solid = target.AddTorus(centre, r, float(tube_radius))
            except BaseException as exc:  # noqa: BLE001
                raise AutocadError(
                    f"AutoCAD would not make that {shape} ({com_message(exc)}). Check the sizes "
                    "are above zero and that this drawing is not AutoCAD LT, which has no solids."
                ) from exc
            notes = apply_properties(doc, solid, layer, aci, None)

        payload = created_payload(
            solid,
            notes,
            shape=shape,
            base=[round(bx, 6), round(by, 6), round(bz, 6)],
            centre=[round(cx, 6), round(cy, 6), round(cz, 6)],
            volume=_try(lambda: round(float(solid.Volume), 6)),
        )
        low, high = _try(lambda: solid.GetBoundingBox(), (None, None))
        if low is not None:
            payload["bounding_box"] = {"min": point_to_list(low), "max": point_to_list(high)}
        return payload

    return dumps(await run(work))


# ---------------------------------------------------------------------------
# A profile into a solid
# ---------------------------------------------------------------------------


@mcp.tool(name="autocad_extrude_profile", **tool_meta("Extrude Or Revolve A Profile"))
@tool_errors
async def autocad_extrude_profile(
    handles: Annotated[
        list[str],
        Field(
            min_length=1,
            description=(
                "The curves making the closed profile: lines, arcs, circles, polylines, "
                "ellipses or splines, all on one plane and joined end to end. One closed "
                "polyline or circle is the easy case — give just that."
            ),
        ),
    ],
    height: Annotated[
        float | None,
        Field(default=None, description="Extrude: how far along Z, in drawing units. Negative goes the other way. Give this or revolve_angle."),
    ] = None,
    taper: Annotated[
        float,
        Field(default=0.0, description="Extrude: taper angle in degrees. A positive angle draws the sides in as it rises, as a plinth or a footing does."),
    ] = 0.0,
    revolve_angle: Annotated[
        float | None,
        Field(default=None, description="Revolve: the angle in degrees to sweep the profile about the axis. 360 for a full turn. Give this or height."),
    ] = None,
    axis_point: Annotated[
        list[float] | None,
        Field(default=None, description="Revolve: a point on the axis, as [x, y] or [x, y, z]."),
    ] = None,
    axis_direction: Annotated[
        list[float] | None,
        Field(default=None, description="Revolve: which way the axis runs, e.g. [0,1,0] for the Y axis. Rotation follows the right-hand rule about it."),
    ] = None,
    keep_profile: Annotated[
        bool,
        Field(default=True, description="Keep the original curves. They are kept by default, because they are usually the 2D section you still want on the drawing."),
    ] = True,
    layer: Annotated[str | None, LAYER_OPT] = None,
    color: Annotated[str | StrictInt | None, COLOR_OPT] = None,
    coords: Annotated[str, COORDS_OPT] = "world",
) -> str:
    """Turn a closed 2D profile into a solid: extrude it along Z, or revolve it about an axis.

    This is how every real part gets modelled — draw the section flat, then
    give it depth. A flange is a profile revolved 360 degrees; a bracket is a
    profile extruded; a footing is a profile extruded with a taper.

    The curves are joined into a region first (AutoCAD's own step), the solid
    is made from it, and that intermediate region is then removed — it is
    scaffolding, not something you asked for. Your original curves stay unless
    you say otherwise.

    One undo step.

    Args:
        handles (list[str]): the curves forming the closed profile.
        height (Optional[float]): extrude this far along Z.
        taper (float): extrude taper angle, degrees.
        revolve_angle (Optional[float]): revolve this many degrees instead.
        axis_point / axis_direction (Optional[list[float]]): the axis to revolve about.
        keep_profile (bool): keep the original curves (default true).
        layer (Optional[str]): target layer, created if missing.
        color (Optional[str | int]): colour.
        coords (str): 'world' or 'ucs'.

    Returns:
        str: JSON: {"created": true, "handle": str, "operation": "extrude" |
             "revolve", "regions_found": int, "volume": float,
             "bounding_box": {...}, "profile_kept": bool}

    Examples:
        - Use when: "extrude this outline 200 up" — handles the polyline,
          height=200.
        - Use when: "revolve this section round the Y axis to make the flange"
          — revolve_angle=360, axis_point and axis_direction.
        - Use when: "a tapered footing" — height plus taper.
        - Don't use when: a plain box or cylinder will do (autocad_add_solid).

    Error Handling:
        - Curves that do not close, or are not all on one plane, come back as
          AutoCAD's own refusal with what to check.
        - A revolve without an axis, or with an angle of zero, is refused before
          anything is made.
        - More than one region from the curves is reported, with the count: that
          means the profile closed more than one loop, which is rarely meant.
    """
    if (height is None) == (revolve_angle is None):
        raise AutocadError(
            "Give 'height' to extrude, or 'revolve_angle' with an axis to revolve — one or "
            "the other."
        )
    if height is not None and abs(float(height)) < 1e-9:
        raise AutocadError("A height of zero extrudes nothing.")
    if revolve_angle is not None:
        if abs(float(revolve_angle)) < 1e-9:
            raise AutocadError("A revolve angle of zero sweeps nothing.")
        if not axis_point or not axis_direction:
            raise AutocadError(
                "A revolve needs axis_point (a point on the axis) and axis_direction "
                "(which way it runs, e.g. [0,1,0])."
            )
        if len(axis_direction) < 3 or all(abs(float(v)) < 1e-12 for v in axis_direction[:3]):
            raise AutocadError("axis_direction needs [x, y, z] and cannot be all zeros.")
    aci = to_aci(color)

    def work() -> dict[str, Any]:
        doc = get_doc()
        require_idle(doc)
        ucs = ucs_for(doc, coords)
        target = get_space(doc, "model")
        curves = resolve_handles(doc, handles)
        kinds = {short_type(c) for c in curves}

        with undo_mark(doc):
            try:
                made = target.AddRegion(object_array(curves))
            except BaseException as exc:  # noqa: BLE001
                raise AutocadError(
                    f"Those curves would not make a region ({com_message(exc)}). A profile has "
                    "to be closed, flat (all on one plane) and joined end to end, and the "
                    f"curves given are: {', '.join(sorted(kinds))}. Check for gaps with "
                    "autocad_select_connected."
                ) from exc
            regions = list(made) if isinstance(made, tuple) else [made]
            regions = [r for r in regions if r is not None]
            if not regions:
                raise AutocadError(
                    "Those curves closed no region. Check the profile is closed and flat."
                )
            region = regions[0]

            try:
                if height is not None:
                    solid = target.AddExtrudedSolid(region, float(height), rad(taper) or 0.0)
                    operation = "extrude"
                else:
                    solid = target.AddRevolvedSolid(
                        region,
                        apoint(*world_coords(axis_point, ucs)),
                        apoint(*(float(v) for v in axis_direction[:3])),
                        rad(revolve_angle),
                    )
                    operation = "revolve"
            except BaseException as exc:  # noqa: BLE001
                # The region was ours, so it goes whatever happens next.
                _try(lambda: region.Delete())
                raise AutocadError(
                    f"AutoCAD would not {'extrude' if height is not None else 'revolve'} that "
                    f"profile ({com_message(exc)}). For a taper, check the sides do not meet "
                    "before the top; for a revolve, check the axis does not cut through the "
                    "profile."
                ) from exc

            # Tidy up the scaffolding: the region the solid was built from, and
            # any extra regions the curves closed that nothing was built from.
            # Delete returns nothing either way, so there is nothing to count -
            # a region that will not go is harmless, and the warning below
            # already tells the caller when there was more than one.
            for extra in regions:
                _try(lambda e=extra: e.Delete())
            if not keep_profile:
                for curve in curves:
                    _try(lambda c=curve: c.Delete())

            notes = apply_properties(doc, solid, layer, aci, None)

        payload = created_payload(
            solid,
            notes,
            operation=operation,
            regions_found=len(regions),
            volume=_try(lambda: round(float(solid.Volume), 6)),
            profile_kept=bool(keep_profile),
        )
        low, high = _try(lambda: solid.GetBoundingBox(), (None, None))
        if low is not None:
            payload["bounding_box"] = {"min": point_to_list(low), "max": point_to_list(high)}
        if len(regions) > 1:
            payload["warning"] = (
                f"Those curves closed {len(regions)} separate loops; the solid was made from "
                "the first. If you meant one profile, check for a stray curve."
            )
        return payload

    return dumps(await run(work))


# ---------------------------------------------------------------------------
# Booleans
# ---------------------------------------------------------------------------


@mcp.tool(name="autocad_solid_boolean", **tool_meta("Join, Cut Or Intersect Solids", destructive=True))
@tool_errors
async def autocad_solid_boolean(
    operation: Annotated[
        Literal["union", "subtract", "intersect"],
        Field(
            description=(
                "'union' joins them into one. 'subtract' cuts the others out of the first "
                "— a plate with holes is a box minus some cylinders. 'intersect' keeps only "
                "the part they share."
            )
        ),
    ],
    handle: Annotated[
        str,
        Field(description="The solid that stays and is changed. For 'subtract' this is the one being cut."),
    ],
    others: Annotated[
        list[str],
        Field(min_length=1, description="The other solids. **These are consumed** — AutoCAD removes them as it applies the operation."),
    ],
) -> str:
    """Join, cut or intersect 3D solids — the real modelling step.

    The first solid is the one that remains and is modified; the others are
    **consumed by AutoCAD**, which is how its own UNION, SUBTRACT and INTERSECT
    behave. The result's handle is the first solid's, unchanged.

    One undo step, so one Ctrl+Z puts them all back.

    Args:
        operation (str): union, subtract or intersect.
        handle (str): the solid that stays (for subtract, the one being cut).
        others (list[str]): the solids consumed by the operation.

    Returns:
        str: JSON: {"operation", "handle", "consumed": [str], "failed": [...],
             "volume_before": float, "volume_after": float,
             "bounding_box": {...}}

    Examples:
        - Use when: "cut these four bolt holes out of the plate" —
          operation='subtract', handle the plate, others the cylinders.
        - Use when: "join the base and the upstand".
        - Don't use when: the objects are 2D (regions boolean the same way, but
          a 2D outline is usually better edited directly).

    Error Handling:
        - A handle that is not a 3D solid or a region is named before anything
          is changed, so nothing is consumed by mistake.
        - The volume before and after is reported: a subtract that removed
          nothing shows up as an unchanged volume.
    """
    if handle in others:
        raise AutocadError(
            "The first solid is also in 'others'. A solid cannot be combined with itself."
        )

    def work() -> dict[str, Any]:
        doc = get_doc()
        require_idle(doc)
        first = resolve_handle(doc, handle)
        rest = resolve_handles(doc, others)

        # Check every one of them before touching any: the others are consumed,
        # so a failure halfway would leave a mess that cannot be reasoned about.
        for entity, label in [(first, handle)] + list(zip(rest, others, strict=False)):
            kind = short_type(entity)
            if kind not in ("3dsolid", "region") and "Solid3d" not in str(
                _try(lambda e=entity: e.ObjectName, "")
            ):
                raise AutocadError(
                    f"{label} is a {kind}, not a 3D solid or a region, so it cannot take part "
                    "in a boolean. Make it a solid first with autocad_add_solid or "
                    "autocad_extrude_profile."
                )

        before = _try(lambda: round(float(first.Volume), 6))
        code = BOOLEAN_OPS[operation]
        consumed: list[str] = []
        failed: list[dict[str, Any]] = []

        with undo_mark(doc):
            for label, other in zip(others, rest, strict=False):
                try:
                    first.Boolean(code, other)
                    consumed.append(label)
                except BaseException as exc:  # noqa: BLE001 - report, keep going
                    failed.append({"handle": label, "reason": com_message(exc)})

        after = _try(lambda: round(float(first.Volume), 6))
        result: dict[str, Any] = {
            "operation": operation,
            "handle": str(_try(lambda: first.Handle, handle)),
            "consumed": consumed,
            "failed": failed,
            "volume_before": before,
            "volume_after": after,
        }
        low, high = _try(lambda: first.GetBoundingBox(), (None, None))
        if low is not None:
            result["bounding_box"] = {"min": point_to_list(low), "max": point_to_list(high)}
        if before is not None and after is not None and abs(after - before) < 1e-9 and consumed:
            result["warning"] = (
                "The volume did not change, so the operation did nothing useful — for a "
                "subtract that usually means the solids were not actually overlapping."
            )
        return result

    return dumps(await run(work))


# ---------------------------------------------------------------------------
# Mass properties
# ---------------------------------------------------------------------------


@mcp.tool(
    name="autocad_solid_properties",
    **tool_meta("Read A Solid's Volume And Centroid", read_only=True, idempotent=True),
)
@tool_errors
async def autocad_solid_properties(
    handles: Annotated[
        list[str],
        Field(min_length=1, description="The solids or regions to measure, by handle."),
    ],
) -> str:
    """Volume, centroid, bounding box and moments for 3D solids — what a take-off needs.

    Give a density and the volume becomes a weight: that is the number a
    fabricator and a lifting plan both want. Regions report their area and
    perimeter instead of a volume.

    Args:
        handles (list[str]): the solids or regions to measure.

    Returns:
        str: JSON: {
          "count": int, "total_volume": float, "total_area": float,
          "items": [{"handle", "type", "volume", "area", "perimeter",
                     "centroid", "bounding_box", "size",
                     "moment_of_inertia", "radii_of_gyration"}],
          "unreadable": [{"handle", "type"}]
        }

    Examples:
        - Use when: "how much concrete is in these pads" — total_volume, then
          multiply by the density yourself.
        - Use when: "where is the centre of gravity of this frame" — centroid.
        - Don't use when: you want a length or an area of 2D linework
          (autocad_measure, autocad_total_length).

    Error Handling:
        - Anything that reports no volume or area is listed in "unreadable"
          with its type, rather than failing the call.
    """

    def work() -> dict[str, Any]:
        doc = get_doc()
        items: list[dict[str, Any]] = []
        unreadable: list[dict[str, Any]] = []

        for handle, entity in zip(handles, resolve_handles(doc, handles), strict=False):
            row: dict[str, Any] = {"handle": handle, "type": short_type(entity)}
            volume = _try(lambda e=entity: round(float(e.Volume), 6))
            area = _try(lambda e=entity: round(float(e.Area), 6))
            if volume is None and area is None:
                unreadable.append(row)
                continue
            if volume is not None:
                row["volume"] = volume
            if area is not None:
                row["area"] = area
            for key, prop in (
                ("perimeter", "Perimeter"),
                ("centroid", "Centroid"),
                ("moment_of_inertia", "MomentOfInertia"),
                ("radii_of_gyration", "RadiiOfGyration"),
                ("principal_moments", "PrincipalMoments"),
            ):
                value = _try(lambda e=entity, p=prop: getattr(e, p))
                if value is None:
                    continue
                row[key] = (
                    round(float(value), 6)
                    if isinstance(value, (int, float))
                    else point_to_list(value)
                )
            low, high = _try(lambda e=entity: e.GetBoundingBox(), (None, None))
            if low is not None:
                lo, hi = point_to_list(low), point_to_list(high)
                row["bounding_box"] = {"min": lo, "max": hi}
                row["size"] = [round(h - lo_v, 6) for h, lo_v in zip(hi, lo, strict=False)]
            items.append(row)

        return {
            "count": len(items),
            "total_volume": round(sum(i.get("volume") or 0.0 for i in items), 6),
            "total_area": round(sum(i.get("area") or 0.0 for i in items), 6),
            "items": items,
            "unreadable": unreadable,
        }

    return dumps(await run(work))


# ---------------------------------------------------------------------------
# 3D paths
# ---------------------------------------------------------------------------


@mcp.tool(name="autocad_draw_3d_path", **tool_meta("Draw A 3D Path Or Helix"))
@tool_errors
async def autocad_draw_3d_path(
    points: Annotated[
        list[list[float]] | None,
        Field(default=None, description="The path, each [x, y, z] — a pipe or cable route through a building. Give this, or the helix settings below."),
    ] = None,
    helix_radius: Annotated[float | None, Field(default=None, gt=0, description="Helix: the radius. Give with helix_turns and helix_height.")] = None,
    helix_turns: Annotated[float | None, Field(default=None, gt=0, description="Helix: how many turns.")] = None,
    helix_height: Annotated[float | None, Field(default=None, description="Helix: the rise over all the turns. Negative winds the other way down.")] = None,
    helix_top_radius: Annotated[float | None, Field(default=None, gt=0, description="Helix: a different radius at the top, for a conical coil.")] = None,
    helix_centre: Annotated[list[float] | None, Field(default=None, description="Helix: the centre of its base, as [x, y] or [x, y, z]. Default the origin.")] = None,
    per_turn: Annotated[int, Field(default=36, ge=8, le=360, description="Helix: points per turn. More is smoother and heavier.")] = 36,
    closed: Annotated[bool, Field(default=False, description="Close the path back to its start.")] = False,
    layer: Annotated[str | None, LAYER_OPT] = None,
    color: Annotated[str | StrictInt | None, COLOR_OPT] = None,
    coords: Annotated[str, COORDS_OPT] = "world",
) -> str:
    """Draw a 3D polyline: a pipe or cable route through a building, or a helix.

    One object, so it moves and selects as one thing, and it can be used as a
    path later. A helix is generated from its radius, turns and rise —
    a spiral stair's handrail, a coil, a spiral duct, a thread line.

    One undo step.

    Args:
        points (Optional[list[list[float]]]): the path, each [x, y, z].
        helix_radius / helix_turns / helix_height (Optional[float]): a helix instead.
        helix_top_radius (Optional[float]): a different radius at the top.
        helix_centre (Optional[list[float]]): centre of the helix's base.
        per_turn (int): points per turn of the helix.
        closed (bool): close the path.
        layer (Optional[str]): target layer, created if missing.
        color (Optional[str | int]): colour.
        coords (str): 'world' or 'ucs'.

    Returns:
        str: JSON: {"created": true, "handle": str, "type": "polyline3d",
             "vertex_count": int, "length": float, "shape": "path" | "helix"}

    Examples:
        - Use when: "route this drain from the gully up to the stack" — the
          points it passes through.
        - Use when: "a handrail up the spiral stair" — helix_radius,
          helix_turns, helix_height.
        - Don't use when: the route is flat (autocad_draw_polyline, which can
          carry arcs for the bends).

    Error Handling:
        - Needs either points or the three helix settings, and says which are
          missing.
        - A path of fewer than two points is refused.
    """
    helix = helix_radius is not None or helix_turns is not None or helix_height is not None
    if points is not None and helix:
        raise AutocadError("Give 'points' for a path, or the helix settings — not both.")
    if helix:
        missing = [
            name
            for name, value in (("helix_radius", helix_radius), ("helix_turns", helix_turns),
                                ("helix_height", helix_height))
            if value is None
        ]
        if missing:
            raise AutocadError(f"A helix needs {', '.join(missing)} as well.")
        base = (list(helix_centre or []) + [0.0, 0.0, 0.0])[:3]
        try:
            path = helix_points(
                float(helix_radius), float(helix_turns), float(helix_height),
                float(helix_top_radius) if helix_top_radius else None,
                (float(base[0]), float(base[1]), float(base[2])), per_turn,
            )
        except ValueError as exc:
            raise AutocadError(str(exc)) from exc
        shape = "helix"
    else:
        if not points or len(points) < 2:
            raise AutocadError("A 3D path needs at least two points, each [x, y, z].")
        path = [list((list(p) + [0.0, 0.0, 0.0])[:3]) for p in points]
        shape = "path"
    aci = to_aci(color)

    def work() -> dict[str, Any]:
        doc = get_doc()
        require_idle(doc)
        ucs = ucs_for(doc, coords)
        target = get_space(doc, "model")
        world = [world_coords(p, ucs) for p in path]
        flat = [c for p in world for c in p]

        with undo_mark(doc):
            if layer:
                ensure_layer(doc, layer)
            try:
                entity = target.Add3DPoly(double_array(flat))
            except BaseException as exc:  # noqa: BLE001
                raise AutocadError(
                    f"AutoCAD would not make the 3D polyline ({com_message(exc)})."
                ) from exc
            if closed:
                _write(entity, "Closed", True)
            notes = apply_properties(doc, entity, layer, aci, None)

        info = describe(entity)
        return created_payload(
            entity,
            notes,
            shape=shape,
            vertex_count=len(world),
            length=info.get("length"),
            start=[round(v, 6) for v in world[0]],
            end=[round(v, 6) for v in world[-1]],
        )

    return dumps(await run(work))


# ---------------------------------------------------------------------------
# Looking at it
# ---------------------------------------------------------------------------


@mcp.tool(name="autocad_set_3d_view", **tool_meta("Set The 3D View And Visual Style", idempotent=True))
@tool_errors
async def autocad_set_3d_view(
    direction: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Where to look from: top (or plan), bottom, front, back, left, right, "
                "sw_iso, se_iso, ne_iso, nw_iso. Omit to leave the direction alone."
            ),
        ),
    ] = None,
    vector: Annotated[
        list[float] | None,
        Field(default=None, description="Instead of a name: the direction to look from, as [x, y, z]."),
    ] = None,
    visual_style: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "2dwireframe, wireframe, hidden, realistic, conceptual, shaded, "
                "'shaded with edges', 'shades of gray', sketchy, x-ray. 'hidden' is the "
                "one a shop drawing wants; 'realistic' is for showing someone."
            ),
        ),
    ] = None,
    zoom_extents: Annotated[
        bool,
        Field(default=True, description="Fit the drawing on screen afterwards, so the new view actually shows the model."),
    ] = True,
) -> str:
    """Look at the model from a named direction, in a chosen visual style.

    What you need before ``autocad_preview`` can show a 3D model usefully: a
    south-west isometric in the hidden style reads like a shop drawing, while
    plan plus 2D wireframe is back to normal drafting.

    This only changes what is on screen, so it needs no padlock — the same
    level as autocad_zoom. It does not move or change a single object.

    Args:
        direction (Optional[str]): a named direction, e.g. 'sw_iso'.
        vector (Optional[list[float]]): or an explicit [x, y, z].
        visual_style (Optional[str]): the visual style to switch to.
        zoom_extents (bool): fit the drawing afterwards.

    Returns:
        str: JSON: {"direction": [x, y, z], "named": str | null,
             "visual_style": str | null, "zoomed": bool, "not_set": [str]}

    Examples:
        - Use when: "show me the model in 3D" — direction='sw_iso',
          visual_style='hidden', then autocad_preview.
        - Use when: "back to plan" — direction='top',
          visual_style='2dwireframe'.
        - Don't use when: you want a viewport on a sheet
          (autocad_add_viewport).

    Error Handling:
        - An unknown direction or visual style is named, with the list of real
          ones, before anything changes.
        - A visual style this AutoCAD does not have comes back in "not_set".
    """
    if direction and vector:
        raise AutocadError("Give a named 'direction' or a 'vector', not both.")
    if not direction and not vector and not visual_style:
        raise AutocadError(
            "Nothing to do. Give a direction, a vector, or a visual_style."
        )

    aim: tuple[float, float, float] | None = None
    named: str | None = None
    if direction:
        key = str(direction).strip().lower().replace("-", "_").replace(" ", "_")
        if key not in VIEW_DIRECTIONS:
            raise AutocadError(
                f"'{direction}' is not a view direction. Use one of: "
                + ", ".join(sorted(VIEW_DIRECTIONS))
            )
        aim, named = VIEW_DIRECTIONS[key], key
    elif vector:
        if len(vector) < 3 or all(abs(float(v)) < 1e-12 for v in vector[:3]):
            raise AutocadError("vector needs [x, y, z] and cannot be all zeros.")
        aim = (float(vector[0]), float(vector[1]), float(vector[2]))

    style: str | None = None
    if visual_style:
        wanted = str(visual_style).strip().lower()
        if wanted not in VISUAL_STYLES:
            raise AutocadError(
                f"'{visual_style}' is not a visual style this server knows. Use one of: "
                + ", ".join(VISUAL_STYLES)
            )
        style = wanted

    def work() -> dict[str, Any]:
        doc = get_doc()
        require_idle(doc)
        not_set: list[str] = []
        result: dict[str, Any] = {"named": named, "visual_style": style, "zoomed": False}

        if aim is not None:
            viewport = doc.ActiveViewport
            if not _write(viewport, "Direction", apoint(*aim)):
                not_set.append("direction")
            else:
                # A viewport's changes only take once it is made active again;
                # this reassignment is what applies them.
                if not _write(doc, "ActiveViewport", viewport):
                    not_set.append("direction (the viewport would not reactivate)")
            result["direction"] = [round(v, 6) for v in aim]

        if style is not None:
            try:
                doc.SetVariable("VSCURRENT", style)
            except BaseException as exc:  # noqa: BLE001 - say so, change nothing else
                not_set.append(f"visual_style ({com_message(exc)})")

        if zoom_extents:
            try:
                doc.Application.ZoomExtents()
                result["zoomed"] = True
            except BaseException:  # noqa: BLE001 - the view is still set
                not_set.append("zoom_extents")

        _try(lambda: doc.Regen(AC_ALL_VIEWPORTS))
        result["current_visual_style"] = _try(lambda: str(doc.GetVariable("VSCURRENT")))
        if not_set:
            result["not_set"] = not_set
        return result

    return dumps(await run(work))
