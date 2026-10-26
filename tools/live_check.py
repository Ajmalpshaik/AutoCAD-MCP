#!/usr/bin/env python3
"""Drive the NEEDS-CHECKING live rows against a real AutoCAD, and measure them.

The register holds 67 rows that can only be proved inside AutoCAD. Most of them
are a measurement, not an opinion: a cone development's arcs must be exactly as
long as the girths they roll onto; a 1:100 viewport must report a scale of 0.01;
a box's base must sit on z=0. This runs those rows, **measures** them, and
writes the answer back into the register with its evidence.

    .venv\\Scripts\\python.exe tools/live_check.py --list
    .venv\\Scripts\\python.exe tools/live_check.py --group E
    .venv\\Scripts\\python.exe tools/live_check.py --group all --write

Everything happens in a **new drawing it creates for itself**, so the drawing
you have open is never touched. It is closed without saving at the end.

Press **Heron** in AutoCAD first and turn the **Changes** padlock on. A row the
padlocks refuse is reported NOT RUN with that reason, not FAIL - a refusal is
the gate working, not a bug.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import sys
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from live_results import Outcome, apply_results, summarise  # noqa: E402

from autocad_mcp.core.connection import get_app, run  # noqa: E402
from autocad_mcp.tools import (  # noqa: E402
    annotate,
    batch,
    blocks,
    convert,
    coordinates,
    dimensions,
    document,
    draw,
    geometry_tools,
    layers,
    query,
    sequence,
    settings,
    shapes,
    sheets,
    solids,
    views,
)

REGISTER = ROOT / "docs" / "NEEDS-CHECKING.md"
TOLERANCE = 1e-4


class Failed(Exception):
    """A row that did not measure up. The message is the evidence."""


class Refused(Exception):
    """A row the padlocks or the machine would not let run."""


def parse(raw: str) -> dict[str, Any]:
    """A tool result as data. An 'Error: ...' reply becomes the right exception."""
    if not isinstance(raw, str):
        return raw
    if raw.startswith("Error:"):
        low = raw.lower()
        if any(word in low for word in ("padlock", "press heron", "not connected", "admin", "publish")):
            raise Refused(raw[7:].strip())
        raise Failed(raw[7:].strip())
    try:
        return json.loads(raw)
    except ValueError:
        return {"text": raw}


def expect(condition: Any, message: str) -> None:
    if not condition:
        raise Failed(message)


def near(got: float | None, want: float, tol: float = TOLERANCE) -> bool:
    return got is not None and abs(float(got) - float(want)) <= tol


def refusal(raw: str) -> str:
    """The message from a reply that must be a refusal; raises if it was allowed."""
    expect(isinstance(raw, str) and raw.startswith("Error:"), f"expected a refusal, got: {str(raw)[:120]}")
    return raw[7:].strip()


# ---------------------------------------------------------------------------
# The scratch drawing
# ---------------------------------------------------------------------------


@dataclass
class Context:
    """What the checks share: the version, and a few things they pass along."""

    version: str = "unknown"
    store: dict[str, Any] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.store is None:
            self.store = {}


async def entity_count() -> int:
    """Model-space entities, read from status so it costs no undo step."""
    status = parse(await document.autocad_status())
    return int((status.get("active_drawing") or {}).get("model_space_entities") or 0)


async def variable(name: str) -> Any:
    return parse(await document.autocad_get_variable(name=name)).get("value")


# ---------------------------------------------------------------------------
# The checks
# ---------------------------------------------------------------------------


async def d1_status_reports_a_rotated_ucs(ctx: Context) -> str:
    parse(await coordinates.autocad_set_ucs(mode="origin", origin=[1000, 500], rotation=23))
    status = parse(await document.autocad_status())
    drawing = status["active_drawing"]
    ucs = drawing["ucs"]
    expect(ucs["rotated"] and ucs["moved"], f"status says rotated={ucs['rotated']} moved={ucs['moved']}")
    expect(near(ucs["rotation_degrees"], 23.0, 1e-6), f"rotation reads {ucs['rotation_degrees']}")
    expect("ucs_advice" in drawing, "status gave no ucs_advice for a rotated UCS")
    return f"rotation {ucs['rotation_degrees']}, moved, advice present"


async def d2_get_ucs_matches_the_system_variables(ctx: Context) -> str:
    got = parse(await coordinates.autocad_get_ucs())["current"]
    org = await variable("UCSORG")
    xdir = await variable("UCSXDIR")
    expect(near(got["origin"][0], org[0], 1e-6) and near(got["origin"][1], org[1], 1e-6),
           f"origin {got['origin']} vs UCSORG {org}")
    expect(near(got["x_axis"][0], xdir[0], 1e-6), f"x_axis {got['x_axis']} vs UCSXDIR {xdir}")
    return f"origin {got['origin'][:2]} matches UCSORG; x_axis matches UCSXDIR"


async def d3_convert_points_round_trips(ctx: Context) -> str:
    out = parse(await coordinates.autocad_convert_points(points=[[100, 0]], into="world"))
    world = out["points"][0]
    back = parse(await coordinates.autocad_convert_points(points=[world], into="ucs"))["points"][0]
    expect(near(back[0], 100.0, 1e-6) and near(back[1], 0.0, 1e-6), f"round trip gave {back}")
    # 100 along a UCS turned 23 degrees from (1000, 500).
    want = (1000 + 100 * math.cos(math.radians(23)), 500 + 100 * math.sin(math.radians(23)))
    expect(near(world[0], want[0], 1e-6) and near(world[1], want[1], 1e-6),
           f"world {world[:2]} but the UCS says {want}")
    return f"ucs [100,0] -> world [{world[0]:.3f}, {world[1]:.3f}], round trip exact"


async def d4_batch_draws_square_to_the_ucs(ctx: Context) -> str:
    made = parse(await batch.autocad_batch_draw(
        operations=[{"type": "rectangle", "corner1": [0, 0], "corner2": [1000, 500], "layer": "LC-UCS"}],
        coords="ucs",
    ))
    expect(made["created"] == 1, f"created {made['created']}")
    info = parse(await geometry_tools.autocad_polyline_info(handle=made["handles"][0]))
    first = info["segments"][0]
    angle = math.degrees(math.atan2(first["end"][1] - first["start"][1],
                                    first["end"][0] - first["start"][0])) % 360.0
    expect(near(angle, 23.0, 1e-3), f"the first side runs at {angle:.4f} degrees, not 23")
    expect(near(first["length"], 1000.0, 1e-6), f"the first side is {first['length']}, not 1000")
    return f"rectangle came out at {angle:.4f} degrees, side 1000.0 - square to the UCS, not the world"


async def d7_a_tilted_ucs_is_refused(ctx: Context) -> str:
    parse(await coordinates.autocad_set_ucs(
        mode="3point", origin=[0, 0, 0], point_on_x=[1, 0, 0], point_on_y=[0, 0, 1]
    ))
    got = parse(await coordinates.autocad_get_ucs())["current"]
    expect(got["tilted"], "the UCS did not come out tilted, so this proves nothing")
    message = refusal(await batch.autocad_batch_draw(
        operations=[{"type": "line", "start": [0, 0], "end": [100, 0]}], coords="ucs"
    ))
    expect("autocad_convert_points" in message, f"the refusal did not point anywhere useful: {message[:120]}")
    parse(await coordinates.autocad_set_ucs(mode="world"))
    return "tilted UCS refused and pointed at convert_points; back to world"


async def d6_the_ucs_lines_up_with_a_block(ctx: Context) -> str:
    """mode='entity' must read the block's own rotation, not guess at it."""
    made = parse(await batch.autocad_batch_draw(operations=[
        {"type": "line", "start": [0, 0], "end": [500, 0], "layer": "LC-BLOCK"},
        {"type": "line", "start": [0, 0], "end": [0, 300], "layer": "LC-BLOCK"},
    ]))
    parse(await blocks.autocad_make_block(
        name="LC-MARK", handles=made["handles"], base_point=[0, 0]
    ))
    placed = parse(await draw.autocad_insert_block(
        block_name="LC-MARK", position=[2000, 70000], rotation=30, layer="LC-BLOCK"
    ))
    parse(await coordinates.autocad_set_ucs(mode="entity", handle=placed["handle"]))
    got = parse(await coordinates.autocad_get_ucs())["current"]
    expect(near(got["rotation_degrees"], 30.0, 1e-6),
           f"the UCS came out at {got['rotation_degrees']} degrees, not the block's 30")
    expect(near(got["origin"][0], 2000.0, 1e-6) and near(got["origin"][1], 70000.0, 1e-6),
           f"the UCS origin is {got['origin'][:2]}, not the block's insertion point")
    parse(await coordinates.autocad_set_ucs(mode="world"))
    return "the UCS took the block's own 30 degrees and its insertion point"


async def d5_the_ucs_goes_back_to_world(ctx: Context) -> str:
    parse(await coordinates.autocad_set_ucs(mode="origin", origin=[50, 50], rotation=10, save_as="LC-UCS-1"))
    parse(await coordinates.autocad_set_ucs(mode="world"))
    now = parse(await coordinates.autocad_get_ucs())
    expect(now["current"]["is_world"], f"mode='world' left {now['current']}")
    saved = [row["name"] for row in now["saved"]]
    expect("LC-UCS-1" in saved, f"save_as did not keep it; saved: {saved}")
    parse(await coordinates.autocad_set_ucs(mode="named", name="LC-UCS-1"))
    back = parse(await coordinates.autocad_get_ucs())["current"]
    expect(near(back["rotation_degrees"], 10.0, 1e-6), f"the saved UCS came back as {back['rotation_degrees']}")
    parse(await coordinates.autocad_set_ucs(mode="world"))
    return "world -> saved -> named -> world all held"


async def d8_a_sheet_is_made_with_its_paper(ctx: Context) -> str:
    made = parse(await sheets.autocad_create_layout(name="LC-A1", paper_size="A1", orientation="landscape"))
    ctx.store["layout"] = made["layout"]
    paper = made["paper"]["paper"]
    expect(paper[0] > paper[1], f"an A1 landscape sheet came back as {paper}")
    expect(near(paper[0], 841.0, 1.0) or near(paper[0], 594.0, 1.0),
           f"the sheet is {paper}, which is not an A1")
    sheet = made["sheet"]
    expect("frame" in sheet and "drawing_space" in sheet, f"no sheet arithmetic came back: {sheet}")
    ctx.store["a1_paper"] = paper
    return f"{made['layout']}: paper {paper}, frame {sheet.get('frame')}"


async def d9_a_copied_sheet_carries_its_setup(ctx: Context) -> str:
    source = ctx.store.get("layout")
    expect(source, "D8 did not leave a sheet to copy")
    want = ctx.store["a1_paper"]
    made = parse(await sheets.autocad_create_layout(name="LC-A1-COPY", copy_from=source))
    expect(made["created"], f"the copy was not made: {made}")
    got = made["paper"]["paper"]
    expect(near(got[0], want[0], 1.0) and near(got[1], want[1], 1.0),
           f"the copy's paper is {got}, but its template's A1 is {want}")
    return f"LC-A1-COPY came off {source} carrying its paper {got}, not a default"


async def d10_page_setup_reaches_every_sheet(ctx: Context) -> str:
    out = parse(await sheets.autocad_page_setup(all_layouts=True, paper_size="A3", plot_area="layout", scale="1:1"))
    expect(out["count"] >= 2, f"only {out['count']} sheet(s) were set up")
    for row in out["layouts"]:
        expect("A3" in str(row["written"].get("paper_size", "")),
               f"{row['name']} came back as {row['written'].get('paper_size')}")
    return f"{out['count']} sheets set to A3, plot_area=layout, 1:1"


async def d13_a_viewport_comes_out_at_the_scale_asked_for(ctx: Context) -> str:
    """The row that proves the viewport maths: a 1:100 viewport must report 0.01."""
    made = parse(await sheets.autocad_add_viewport(
        layout=ctx.store.get("layout"), scale="1:100", centre=[0, 0], locked=True
    ))
    expect(made["scale"] == "1:100", f"it reports {made['scale']}")
    expect(near(made["scale_ratio"], 0.01, 1e-9), f"the ratio is {made['scale_ratio']}")
    expect(near(made.get("scale_set"), 0.01, 1e-6),
           f"AutoCAD kept CustomScale at {made.get('scale_set')}, not 0.01")
    paper = made["paper_rect"]
    model = made["model_window"]
    paper_w, model_w = paper[2] - paper[0], model[2] - model[0]
    expect(near(model_w * 0.01, paper_w, 1e-3),
           f"{model_w:g} of drawing at 1:100 is {model_w * 0.01:g} of paper, but the viewport is {paper_w:g}")
    expect(made["locked"], "the viewport did not lock")
    for note in ("twist_note", "aim_note", "lock_note"):
        expect(note not in made, f"AutoCAD refused part of it: {made.get(note)}")
    ctx.store["viewport"] = made["handle"]
    return (f"CustomScale {made.get('scale_set')}; {model_w:g} drawing units across "
            f"{paper_w:g} paper units = 1:100 exactly; locked")


async def d14_a_fitted_viewport_picks_a_standard_scale(ctx: Context) -> str:
    made = parse(await sheets.autocad_add_viewport(
        layout=ctx.store.get("layout"), corner1=[0, 0], corner2=[9000, 6000],
        paper_centre=[150, 150], paper_width=180, paper_height=120,
    ))
    expect(made["fitted"], "it did not report a fitted scale")
    expect(":" in made["scale"], f"the fitted scale reads {made['scale']}")
    model = made["model_window"]
    expect((model[2] - model[0]) >= 9000 - 1e-6, "the area asked for does not fit in the window chosen")
    return f"fitted to {made['scale']}, window {[round(v) for v in model]}"


async def d16_a_viewport_sits_where_the_paper_numbers_say(ctx: Context) -> str:
    made = parse(await sheets.autocad_add_viewport(
        layout=ctx.store.get("layout"), scale="1:200", centre=[0, 0],
        paper_centre=[260, 180], paper_width=200, paper_height=140,
    ))
    rect = made["paper_rect"]
    width, height = rect[2] - rect[0], rect[3] - rect[1]
    mid = ((rect[0] + rect[2]) / 2.0, (rect[1] + rect[3]) / 2.0)
    expect(near(width, 200.0, 1e-6) and near(height, 140.0, 1e-6),
           f"the viewport is {width} x {height} on paper, not 200 x 140")
    expect(near(mid[0], 260.0, 1e-6) and near(mid[1], 180.0, 1e-6),
           f"its middle is at {mid} on paper, not [260, 180]")
    expect(near(made.get("centre_set", mid[0]), 260.0, 1e-3) if "centre_set" in made else True,
           f"AutoCAD put it at {made.get('centre_set')}")
    return "200 x 140 of paper centred on [260, 180] - exactly the numbers asked for"


async def d18_a_saved_view_gives_its_corners_back(ctx: Context) -> str:
    parse(await views.autocad_save_view(name="LC-AREA", corner1=[0, 0], corner2=[4000, 3000], replace=True))
    listed = parse(await views.autocad_list_views())
    found = next((v for v in listed["views"] if v["name"].upper() == "LC-AREA"), None)
    expect(found is not None, f"the view was not saved; views: {[v['name'] for v in listed['views']]}")
    expect(near(found["width"], 4000.0, 1e-3) and near(found["height"], 3000.0, 1e-3),
           f"it came back {found['width']} x {found['height']}")
    expect(near(found["corner1"][0], 0.0, 1e-3) and near(found["corner2"][0], 4000.0, 1e-3),
           f"corners came back {found['corner1']} {found['corner2']}")
    return f"LC-AREA saved and read back as {found['width']} x {found['height']}, corners exact"


async def d21_the_scale_sets_everything_that_hangs_off_it(ctx: Context) -> str:
    before = await variable("DIMSCALE")
    dry = parse(await settings.autocad_drawing_setup(
        units="millimeters", scale="1:50", paper_text_height=2.5, dry_run=True
    ))
    expect(dry["dry_run"] and await variable("DIMSCALE") == before,
           "the dry run changed DIMSCALE")
    parse(await settings.autocad_drawing_setup(
        units="millimeters", scale="1:50", paper_text_height=2.5,
        osnaps=["endpoint", "midpoint", "intersection"],
    ))
    got = {name: await variable(name) for name in ("DIMSCALE", "LTSCALE", "TEXTSIZE", "INSUNITS", "OSMODE")}
    canno = await variable("CANNOSCALE")
    expect(near(got["DIMSCALE"], 50.0, 1e-6), f"DIMSCALE is {got['DIMSCALE']}")
    expect(near(got["LTSCALE"], 50.0, 1e-6), f"LTSCALE is {got['LTSCALE']}")
    expect(near(got["TEXTSIZE"], 125.0, 1e-6), f"TEXTSIZE is {got['TEXTSIZE']}, not 2.5 x 50")
    expect(int(got["INSUNITS"]) == 4, f"INSUNITS is {got['INSUNITS']}")
    expect(int(got["OSMODE"]) == 35, f"OSMODE is {got['OSMODE']}, not endpoint+midpoint+intersection")
    return (f"dry run wrote nothing; then DIMSCALE 50, LTSCALE 50, TEXTSIZE 125, "
            f"CANNOSCALE {canno}, OSMODE 35")


async def d23_a_dim_style_leaves_the_drawing_as_it_found_it(ctx: Context) -> str:
    """The row that proves CopyFrom: the style holds the settings, the drawing does not."""
    before = {name: await variable(name) for name in ("DIMSCALE", "DIMTXT", "DIMASZ")}
    out = parse(await settings.autocad_create_styles(dim_styles=[{
        "name": "LC-DIM", "scale": 25, "text_height": 1.8, "arrow_size": 1.8, "replace": True,
    }], replace=True))
    row = out["dim_styles"][0]
    expect(row.get("created") or row.get("variables"), f"the style was not made: {row}")
    after = {name: await variable(name) for name in ("DIMSCALE", "DIMTXT", "DIMASZ")}
    expect(all(near(after[k], before[k], 1e-6) for k in before),
           f"the drawing's own DIM variables changed: {before} -> {after}")
    styles = parse(await layers.autocad_list_styles())
    names = [str(n).upper() for n in styles.get("dimension_styles", styles.get("dim_styles", []))]
    expect(any("LC-DIM" in n for n in names), f"LC-DIM is not in the drawing's styles: {names}")
    return f"LC-DIM made; the drawing's DIMSCALE/DIMTXT/DIMASZ are back at {before}"


async def d24_the_remap_plan_shows_the_work_first(ctx: Context) -> str:
    """The dry run has to be worth trusting: it must change nothing and plan right."""
    parse(await batch.autocad_batch_draw(operations=[
        {"type": "line", "start": [0, 20000], "end": [5000, 20000], "layer": "IfcWallStandardCase"},
        {"type": "line", "start": [0, 20500], "end": [5000, 20500], "layer": "IfcDuctSegment"},
        {"type": "line", "start": [0, 21000], "end": [5000, 21000], "layer": "IfcDoor"},
        {"type": "line", "start": [0, 21500], "end": [5000, 21500], "layer": "Mystery-Layer"},
    ]))
    before = parse(await query.autocad_list_entities(layer="IfcWallStandardCase", summary_only=True))
    plan = parse(await convert.autocad_remap_layers(preset="ifc", layer="Ifc*", dry_run=True))
    expect(plan["dry_run"], "it did not report itself as a dry run")
    expect(plan["counts"]["to_move"] >= 3, f"it planned {plan['counts']}")
    wanted = plan["counts"].get("layers_wanted") or 0
    expect(wanted >= 1, f"it planned no layers to create: {plan['counts']}")
    after = parse(await query.autocad_list_entities(layer="IfcWallStandardCase", summary_only=True))
    expect(after["total_matching"] == before["total_matching"],
           f"the dry run moved something: {before['total_matching']} -> {after['total_matching']}")
    ctx.store["planned"] = plan["counts"]["to_move"]
    return (f"planned {plan['counts']['to_move']} moves and {wanted} new layers, "
            f"and moved nothing")


async def d25_the_remap_lands_with_colours_and_reports_what_it_could_not(ctx: Context) -> str:
    """A locked layer must come back in `failed` while everything else lands."""
    parse(await batch.autocad_batch_draw(operations=[
        {"type": "line", "start": [0, 21800], "end": [5000, 21800], "layer": "IfcBeam"},
    ]))
    parse(await layers.autocad_set_layer_state(name="IfcBeam", locked=True))
    out = parse(await convert.autocad_remap_layers(
        preset="ifc", layer="Ifc*", dry_run=False, set_bylayer=True
    ))
    expect(out["moved"] >= 3, f"only {out.get('moved')} moved; failed: {out.get('failed')}")
    walls = parse(await query.autocad_list_entities(layer="A-WALL", summary_only=True))
    ducts = parse(await query.autocad_list_entities(layer="M-HVAC-DUCT", summary_only=True))
    expect(walls["total_matching"] >= 1 and ducts["total_matching"] >= 1,
           f"A-WALL has {walls['total_matching']}, M-HVAC-DUCT has {ducts['total_matching']}")
    listed = parse(await layers.autocad_list_layers(include_entity_counts=False))
    by_name = {row["name"].upper(): row for row in listed["layers"]}
    wall = by_name.get("A-WALL")
    expect(wall and wall["color"] not in (None, 7),
           f"A-WALL came out colour {wall and wall['color']}, so it will plot black")
    failed = out.get("failed") or []
    expect(failed, "the object on the locked layer did not come back in failed")
    reason = str(failed[0].get("reason", ""))[:70]
    parse(await layers.autocad_set_layer_state(name="IfcBeam", locked=False))
    return (f"moved {out['moved']}, A-WALL is colour {wall['color']} (so it plots in colour), "
            f"and the locked one is in failed: {reason}")


async def d26_an_import_is_tidied(ctx: Context) -> str:
    made = parse(await batch.autocad_batch_draw(operations=[
        {"type": "line", "start": [0, 22000], "end": [1000, 22000], "layer": "0", "color": 1},
    ]))
    handle = made["handles"][0]
    dry = parse(await convert.autocad_tidy_entities(
        handles=[handle], color_bylayer=True, off_layer_0="LC-REVIEW", dry_run=True
    ))
    expect(dry["counts"], f"the dry run found nothing to do: {dry}")
    parse(await convert.autocad_tidy_entities(
        handles=[handle], color_bylayer=True, off_layer_0="LC-REVIEW", dry_run=False
    ))
    got = parse(await query.autocad_get_entity(handle=handle))
    expect(got["layer"] == "LC-REVIEW", f"it is still on layer {got['layer']}")
    expect(got["color"] == 256, f"its colour is {got['color']}, not ByLayer")
    return f"moved off layer 0 to LC-REVIEW and set ByLayer (colour {got['color']})"


async def d27_a_sequence_runs_its_steps_in_order(ctx: Context) -> str:
    out = parse(await sequence.autocad_sequence(steps=[
        {"tool": "autocad_draw_line", "args": {"start": [0, 24000], "end": [1000, 24000]}, "label": "one"},
        {"tool": "autocad_draw_line", "args": {"start": [1000, 24000], "end": [1000, 25000]}, "label": "two"},
        {"tool": "autocad_draw_circle", "args": {"center": [500, 24500], "radius": 200}, "label": "three"},
    ]))
    expect(out["ran"] == 3 and out["failed"] == 0, f"ran {out['ran']}, failed {out['failed']}")
    expect(all(s["result"].get("handle") for s in out["steps"]), "a step gave no handle back")
    return "3 steps ran in order, each handing back its own handle"


async def d28_a_bad_step_changes_nothing(ctx: Context) -> str:
    """The row that proves the pre-flight: step 3 is wrong, so nothing runs."""
    before = await entity_count()
    message = refusal(await sequence.autocad_sequence(steps=[
        {"tool": "autocad_draw_line", "args": {"start": [0, 26000], "end": [1000, 26000]}},
        {"tool": "autocad_draw_line", "args": {"start": [0, 26100], "end": [1000, 26100]}},
        {"tool": "autocad_draw_circle", "args": {"center": [0, 0], "radius": -5}},
    ]))
    after = await entity_count()
    expect("Step 3" in message, f"the refusal did not name the step: {message[:120]}")
    expect(after == before, f"the drawing changed: {before} -> {after} entities")
    return f"step 3 refused before step 1 ran; entity count unchanged at {before}"


async def d29_a_step_that_fails_at_run_time_stops_the_rest(ctx: Context) -> str:
    """Steps 1-2 stay, the bad one reports, the rest are skipped."""
    parse(await batch.autocad_batch_draw(operations=[
        {"type": "line", "start": [0, 28000], "end": [10, 28000], "layer": "LC-LOCKED"},
    ]))
    parse(await layers.autocad_set_layer_state(name="LC-LOCKED", locked=True))
    before = await entity_count()
    out = parse(await sequence.autocad_sequence(steps=[
        {"tool": "autocad_draw_line", "args": {"start": [0, 28100], "end": [1000, 28100]}},
        {"tool": "autocad_draw_line", "args": {"start": [0, 28200], "end": [1000, 28200]}},
        {"tool": "autocad_draw_line",
         "args": {"start": [0, 28300], "end": [1000, 28300], "layer": "LC-LOCKED"}},
        {"tool": "autocad_draw_circle", "args": {"center": [500, 28400], "radius": 100}},
    ], stop_on_error=True))
    expect(out["ran"] == 2, f"it ran {out['ran']} steps; the first two should have gone in")
    expect(out["failed"] == 1, f"it reports {out['failed']} failures, not 1")
    expect(out.get("skipped") == 1, f"it skipped {out.get('skipped')}, not the 1 step after the failure")
    after = await entity_count()
    expect(after == before + 2, f"the drawing gained {after - before} objects, not the 2 that worked")
    hint = str(out.get("hint") or out.get("stopped_at") or "")
    expect("3" in hint, f"nothing named the step that stopped it: {hint[:120]}")
    parse(await layers.autocad_set_layer_state(name="LC-LOCKED", locked=False))
    return ("steps 1-2 are in the drawing (+2 objects), step 3 reported the locked layer, "
            "step 4 skipped, and the hint names step 3")


async def d30_a_sequence_cannot_spend_more_than_changes(ctx: Context) -> str:
    """The padlock ceiling. Re-run this whenever a tool is added."""
    saved = refusal(await sequence.autocad_sequence(
        steps=[{"tool": "autocad_save_drawing", "args": {}}]
    ))
    lisped = refusal(await sequence.autocad_sequence(
        steps=[{"tool": "autocad_run_lisp", "args": {"expression": "(princ)"}}]
    ))
    nested = refusal(await sequence.autocad_sequence(
        steps=[{"tool": "autocad_sequence", "args": {"steps": []}}]
    ))
    expect("publish" in saved.lower(), f"save_drawing was refused for the wrong reason: {saved[:100]}")
    expect("admin" in lisped.lower(), f"run_lisp was refused for the wrong reason: {lisped[:100]}")
    expect("sequence" in nested.lower(), f"a nested sequence was refused for the wrong reason: {nested[:100]}")
    return "save_drawing refused (publish), run_lisp refused (admin), nested sequence refused"


async def e1_a_slot_is_one_object(ctx: Context) -> str:
    made = parse(await shapes.autocad_make_shape(
        shape="slot", settings={"length": 120, "width": 40, "origin": [0, 30000]}, layer="LC-SHAPE"
    ))
    expect(made["created"] == 1, f"it made {made['created']} objects, not one")
    info = parse(await geometry_tools.autocad_polyline_info(handle=made["handles"][0]))
    arcs = [s for s in info["segments"] if s["kind"] == "arc"]
    expect(len(arcs) == 2, f"it has {len(arcs)} arcs, not 2")
    want = 2 * 80 + math.pi * 40
    expect(near(info["total_length"], want, 1e-3),
           f"perimeter {info['total_length']:.4f}, expected {want:.4f}")
    for a in arcs:
        expect(near(a["radius"], 20.0, 1e-6), f"an end radius is {a['radius']}, not 20")
    return (f"one polyline, 2 arcs of r20, perimeter {info['total_length']:.4f} "
            f"= 2x80 + pi x 40 ({want:.4f})")


async def e2_a_rounded_rectangle_keeps_its_size(ctx: Context) -> str:
    made = parse(await shapes.autocad_make_shape(
        shape="rounded_rectangle",
        settings={"width": 2400, "height": 1200, "radius": 50, "origin": [0, 32000]},
        layer="LC-SHAPE",
    ))
    got = parse(await query.autocad_get_entity(handle=made["handles"][0]))
    size = got["size"]
    expect(near(size["width"], 2400.0, 1e-3) and near(size["height"], 1200.0, 1e-3),
           f"it measures {size['width']} x {size['height']}")
    info = parse(await geometry_tools.autocad_polyline_info(handle=made["handles"][0]))
    arcs = [s for s in info["segments"] if s["kind"] == "arc"]
    expect(len(arcs) == 4, f"it has {len(arcs)} corner arcs, not 4")
    expect(all(near(a["radius"], 50.0, 1e-6) for a in arcs), f"corner radii: {[a['radius'] for a in arcs]}")
    return "2400.0 x 1200.0 overall, 4 corner arcs of r50, one object"


async def e4_the_flat_pattern_rolls_onto_its_cone(ctx: Context) -> str:
    """The row that proves every flat pattern: the arcs must equal the girths."""
    made = parse(await shapes.autocad_make_shape(
        shape="cone_development",
        settings={"bottom_diameter": 200, "top_diameter": 100, "height": 150, "origin": [0, 34000]},
        layer="LC-SHAPE",
    ))
    outline = made["handles"][0]
    info = parse(await geometry_tools.autocad_polyline_info(handle=outline))
    arcs = sorted((s for s in info["segments"] if s["kind"] == "arc"), key=lambda s: s["radius"])
    expect(len(arcs) == 2, f"the pattern has {len(arcs)} arcs, not 2")
    inner, outer = arcs[0], arcs[1]
    want_outer, want_inner = math.pi * 200, math.pi * 100
    expect(near(outer["length"], want_outer, 1e-2),
           f"the outer arc is {outer['length']:.4f}, but the bottom girth is {want_outer:.4f}")
    expect(near(inner["length"], want_inner, 1e-2),
           f"the inner arc is {inner['length']:.4f}, but the top girth is {want_inner:.4f}")
    return (f"outer arc {outer['length']:.4f} = pi x 200 ({want_outer:.4f}); "
            f"inner arc {inner['length']:.4f} = pi x 100 ({want_inner:.4f})")


async def e3_a_flange_puts_its_holes_on_the_pitch_circle(ctx: Context) -> str:
    made = parse(await shapes.autocad_make_shape(
        shape="flange",
        settings={"outer_diameter": 200, "bolt_count": 8, "pitch_diameter": 160,
                  "hole_diameter": 18, "bore": 100, "origin": [0, 36000]},
        layer="LC-SHAPE",
    ))
    expect(made["created"] == 11, f"it made {made['created']} objects, not 11")
    holes = []
    for handle in made["handles"]:
        got = parse(await query.autocad_get_entity(handle=handle))
        if near(got.get("radius"), 9.0, 1e-6):
            holes.append(got["center"])
    expect(len(holes) == 8, f"found {len(holes)} holes of r9, not 8")
    for centre in holes:
        reach = math.dist((centre[0], centre[1]), (0, 36000))
        expect(near(reach, 80.0, 1e-4), f"a hole sits {reach:.4f} from the middle, not 80")
    return "11 objects; all 8 holes of r9 exactly 80 from the centre (160 PCD)"


async def e7_bubble_text_sits_on_its_point(ctx: Context) -> str:
    """Proves the DXF 72/73/11 justification: the text's box is centred on the point."""
    centre = [0, 38000]
    made = parse(await shapes.autocad_make_shape(
        shape="detail_bubble", settings={"number": "3", "radius": 300, "origin": centre},
        layer="LC-SHAPE",
    ))
    texts = []
    for handle in made["handles"]:
        got = parse(await query.autocad_get_entity(handle=handle))
        if got["type"] == "text":
            texts.append(got)
    expect(len(texts) == 1, f"the bubble has {len(texts)} texts, not 1")
    box = texts[0]["bounding_box"]
    mid = ((box["min"][0] + box["max"][0]) / 2.0, (box["min"][1] + box["max"][1]) / 2.0)
    off = math.dist(mid, (centre[0], centre[1]))
    expect(off < 1.0, f"the text's middle is {off:.3f} from the bubble's centre, so it is not justified")
    return f"the text's box is centred {off:.4f} from the bubble centre - justification took"


async def e9_a_shape_can_be_drawn_in_the_ucs(ctx: Context) -> str:
    parse(await coordinates.autocad_set_ucs(mode="origin", origin=[0, 40000], rotation=23))
    made = parse(await shapes.autocad_make_shape(
        shape="rounded_rectangle", settings={"width": 1000, "height": 500, "radius": 50},
        layer="LC-SHAPE", coords="ucs",
    ))
    info = parse(await geometry_tools.autocad_polyline_info(handle=made["handles"][0]))
    straight = next(s for s in info["segments"] if s["kind"] == "line")
    angle = math.degrees(math.atan2(straight["end"][1] - straight["start"][1],
                                    straight["end"][0] - straight["start"][0])) % 180.0
    expect(near(angle, 23.0, 1e-2) or near(angle, 113.0, 1e-2),
           f"a side runs at {angle:.4f} degrees; the UCS is at 23")
    parse(await coordinates.autocad_set_ucs(mode="world"))
    return f"the shape came out square to the 23 degree UCS (a side at {angle:.3f} degrees)"


async def e10_a_dry_run_draws_nothing(ctx: Context) -> str:
    before = await entity_count()
    out = parse(await shapes.autocad_make_shape(
        shape="flange",
        settings={"outer_diameter": 200, "bolt_count": 8, "pitch_diameter": 160, "hole_diameter": 18},
        dry_run=True,
    ))
    after = await entity_count()
    expect(out["dry_run"] and out["entity_count"] == 11, f"the dry run reported {out}")
    expect(after == before, f"the drawing changed: {before} -> {after}")
    return f"11 operations reported, entity count unchanged at {before}"


async def e11_a_dimension_run_measures_what_it_says(ctx: Context) -> str:
    """Proves the run layout: every dimension's own measurement must match."""
    out = parse(await dimensions.autocad_dimension_run(
        points=[[0, 42000], [3000, 42000], [7500, 42000], [12000, 42000]],
        mode="chain", axis="horizontal", offset=-500, include_overall=True, layer="LC-DIMS",
    ))
    expect(out["count"] == 4, f"it made {out['count']} dimensions, not 4")
    expect(not out.get("failed"), f"some failed: {out.get('failed')}")
    for row in out["dimensions"]:
        expect(near(row["measured"], row["expected"], 1e-6),
               f"a {row['kind']} dimension measured {row['measured']} but spans {row['expected']}")
    chain = [r["expected"] for r in out["dimensions"] if r["kind"] == "chain"]
    overall = next(r["expected"] for r in out["dimensions"] if r["kind"] == "overall")
    expect(near(sum(chain), overall, 1e-6), f"the chain {chain} does not add up to {overall}")
    return f"chain {chain} adds up to the overall {overall}; every measured value matches"


async def e13_ordinate_dimensions_work(ctx: Context) -> str:
    """AddDimOrdinate: never called from this server before today."""
    out = parse(await dimensions.autocad_dimension_run(
        points=[[0, 44000], [1200, 44000], [3600, 44000]],
        mode="ordinate", axis="horizontal", offset=800, datum=[0, 44000], layer="LC-DIMS",
    ))
    expect(out["count"] == 3, f"it made {out['count']} ordinates, not 3")
    expect(not out.get("failed"), f"AddDimOrdinate was refused: {out.get('failed')}")
    for handle in out["handles"]:
        got = parse(await query.autocad_get_entity(handle=handle))
        expect(got["type"] == "dimension", f"an ordinate came out as {got['type']}")
    return "3 ordinate dimensions made - AddDimOrdinate works from here"


async def e15_centre_marks_land_on_every_circle(ctx: Context) -> str:
    parse(await batch.autocad_batch_draw(operations=[
        {"type": "circle", "center": [i * 500, 46000], "radius": 100, "layer": "LC-HOLES"}
        for i in range(4)
    ]))
    out = parse(await dimensions.autocad_add_centre_marks(
        layer_filter="LC-HOLES", size=30, extend=40, layer="LC-CNTR"
    ))
    expect(out["marked"] == 4, f"it marked {out['marked']} circles, not 4")
    expect(out["created"] == 4 * 6, f"it drew {out['created']} lines; 4 circles x 6 = 24")
    got = parse(await query.autocad_get_entity(handle=out["handles"][0]))
    expect(got["layer"] == "LC-CNTR", f"a mark landed on layer {got['layer']}")
    return f"4 circles marked, {out['created']} lines, all on LC-CNTR"


async def e16_a_multileader_takes_several_arrows(ctx: Context) -> str:
    """AddLeader / AddLeaderLine: never called from this server before today."""
    out = parse(await annotate.autocad_add_multileader(
        landing=[6000, 48000], arrows=[[0, 48000], [1000, 48500], [2000, 48000]],
        text="4 No. M16 BOLTS", height=200, layer="LC-ANNO",
    ))
    expect(out["leader_lines"] == 3, f"it has {out['leader_lines']} leader lines, not 3")
    expect(not out.get("not_set"), f"some properties were refused: {out.get('not_set')}")
    got = parse(await query.autocad_get_entity(handle=out["handle"]))
    expect(got["type"] == "mleader", f"it came out as {got['type']}")
    return "one MULTILEADER with 3 leader lines - AddLeader and AddLeaderLine work from here"


async def e18_a_schedule_becomes_a_table(ctx: Context) -> str:
    """AddTable / SetText: never called from this server before today."""
    rows = [["CAM-01", "Dome", "Level 1"], ["CAM-02", "Bullet", "Level 1"], ["CAM-03", "Dome", "Level 2"]]
    out = parse(await annotate.autocad_add_table(
        position=[0, 50000], rows=rows, headers=["TAG", "TYPE", "LOCATION"],
        title="CAMERA SCHEDULE", text_height=100, column_widths=[800, 800, 1200], layer="LC-ANNO",
    ))
    expect(out["rows"] == 5, f"the table has {out['rows']} rows; 1 title + 1 header + 3 data = 5")
    expect(out["columns"] == 3, f"it has {out['columns']} columns, not 3")
    expect(out["cells_written"] == 1 + 3 + 9, f"only {out['cells_written']} cells were written of 13")
    got = parse(await query.autocad_get_entity(handle=out["handle"]))
    expect(got["type"] == "table", f"it came out as {got['type']}")
    return f"a TABLE of {out['rows']} x {out['columns']}, {out['cells_written']} cells filled"


async def e20_a_revision_cloud_is_one_object_of_even_arcs(ctx: Context) -> str:
    made = parse(await batch.autocad_batch_draw(operations=[
        {"type": "rectangle", "corner1": [0, 52000], "corner2": [2000, 53000], "layer": "LC-SHAPE"}
    ]))
    out = parse(await annotate.autocad_add_revision_cloud(
        handle=made["handles"][0], margin=100, layer="LC-REVS", color="red"
    ))
    expect(out["created"] == 1, f"it made {out['created']} objects, not one")
    info = parse(await geometry_tools.autocad_polyline_info(handle=out["handles"][0]))
    arcs = [s for s in info["segments"] if s["kind"] == "arc"]
    expect(len(arcs) == info["segment_count"],
           f"only {len(arcs)} of {info['segment_count']} segments are arcs")
    expect(out["arcs"] == len(arcs), f"it reported {out['arcs']} arcs but drew {len(arcs)}")
    lengths = [a["length"] for a in arcs]
    spread = max(lengths) - min(lengths)
    expect(spread < 1e-6, f"the arcs vary in length by {spread:.6f}; there should be no stub arc")
    return f"one polyline of {len(arcs)} arcs, all {lengths[0]:.4f} long - no stub"


async def e22_a_solid_sits_on_its_base(ctx: Context) -> str:
    """AutoCAD places a primitive by its bounding-box centre; this must not."""
    made = parse(await solids.autocad_add_solid(
        shape="box", base=[0, 54000, 0], length=2400, width=1200, height=200, layer="LC-3D"
    ))
    box = made["bounding_box"]
    expect(near(box["min"][2], 0.0, 1e-6), f"the base sits at z={box['min'][2]}, not 0")
    expect(near(box["max"][2], 200.0, 1e-6), f"the top is at z={box['max'][2]}, not 200")
    expect(near(made["volume"], 2400 * 1200 * 200, 1.0), f"the volume is {made['volume']}")
    expect(near(made["centre"][2], 100.0, 1e-6), f"it reported the centre at z={made['centre'][2]}")
    ctx.store["box"] = made["handle"]
    return (f"base at z={box['min'][2]}, top at z={box['max'][2]}, volume {made['volume']:g} "
            f"= 2400 x 1200 x 200")


async def e23_every_primitive_comes_out(ctx: Context) -> str:
    cases = [
        ("cylinder", {"base": [4000, 54000, 0], "diameter": 300, "height": 3000}),
        ("cone", {"base": [5000, 54000, 0], "radius": 200, "height": 600}),
        ("sphere", {"base": [6000, 54000, 0], "radius": 250}),
        ("wedge", {"base": [7000, 54000, 0], "length": 500, "width": 400, "height": 300}),
        ("torus", {"base": [8000, 54000, 0], "radius": 300, "tube_radius": 60}),
    ]
    out = []
    for shape, kwargs in cases:
        made = parse(await solids.autocad_add_solid(shape=shape, layer="LC-3D", **kwargs))
        expect(made["created"], f"{shape} was not made")
        out.append(f"{shape} {made['volume']:g}")
    return "volumes: " + ", ".join(out)


async def e24_a_profile_becomes_a_solid(ctx: Context) -> str:
    made = parse(await batch.autocad_batch_draw(operations=[
        {"type": "rectangle", "corner1": [0, 56000], "corner2": [1000, 600 + 56000],
         "layer": "LC-3D"}
    ]))
    profile = made["handles"][0]
    before = await entity_count()
    out = parse(await solids.autocad_extrude_profile(handles=[profile], height=200, layer="LC-3D"))
    expect(out["created"], "no solid came back")
    expect(out["regions_found"] == 1, f"the curves closed {out['regions_found']} regions")
    expect(near(out["volume"], 1000 * 600 * 200, 1.0), f"the volume is {out['volume']}")
    still = parse(await query.autocad_get_entity(handle=profile))
    expect(still["type"] == "polyline", "the original profile is gone")
    after = await entity_count()
    expect(after == before + 1, f"entity count went {before} -> {after}; the region was left behind")
    ctx.store["extruded"] = out["handle"]
    return (f"volume {out['volume']:g} = 1000 x 600 x 200; the profile is still there and the "
            f"region was cleaned up ({before} -> {after} entities)")


async def e26_a_profile_revolves(ctx: Context) -> str:
    """AddRevolvedSolid: never called from this server before today."""
    made = parse(await batch.autocad_batch_draw(operations=[
        {"type": "rectangle", "corner1": [1000, 58000], "corner2": [1200, 58400], "layer": "LC-3D"}
    ]))
    out = parse(await solids.autocad_extrude_profile(
        handles=[made["handles"][0]], revolve_angle=360,
        axis_point=[0, 58000, 0], axis_direction=[0, 1, 0], layer="LC-3D",
    ))
    expect(out["operation"] == "revolve", f"it reported {out['operation']}")
    expect(out["volume"] and out["volume"] > 0, f"the volume is {out.get('volume')}")
    return f"revolved 360 degrees about the Y axis; volume {out['volume']:g}"


async def e28_a_boolean_takes_material_away(ctx: Context) -> str:
    plate = parse(await solids.autocad_add_solid(
        shape="box", base=[0, 60000, 0], length=1000, width=600, height=20, layer="LC-3D"
    ))
    holes = []
    for x in (200, 800):
        hole = parse(await solids.autocad_add_solid(
            shape="cylinder", base=[x - 500, 60000, -10], diameter=50, height=40, layer="LC-3D"
        ))
        holes.append(hole["handle"])
    out = parse(await solids.autocad_solid_boolean(
        operation="subtract", handle=plate["handle"], others=holes
    ))
    expect(len(out["consumed"]) == 2, f"it consumed {out['consumed']}, failed {out.get('failed')}")
    expect(out["volume_after"] < out["volume_before"],
           f"the volume did not drop: {out['volume_before']} -> {out['volume_after']}")
    expect("warning" not in out, f"it warned: {out.get('warning')}")
    removed = out["volume_before"] - out["volume_after"]
    want = 2 * math.pi * 25 ** 2 * 20
    expect(near(removed, want, 50.0), f"it removed {removed:.1f}; two 50 dia holes in 20 plate is {want:.1f}")
    ctx.store["plate"] = out["handle"]
    return (f"volume {out['volume_before']:g} -> {out['volume_after']:g}; removed {removed:.1f} "
            f"for two 50 dia holes (expected {want:.1f})")


async def e29_a_boolean_refuses_before_consuming(ctx: Context) -> str:
    """The row that matters most in 3D: a bad handle must not cost you a solid."""
    solid = parse(await solids.autocad_add_solid(
        shape="box", base=[0, 62000, 0], length=200, width=200, height=200, layer="LC-3D"
    ))
    good = parse(await solids.autocad_add_solid(
        shape="box", base=[100, 62000, 0], length=200, width=200, height=200, layer="LC-3D"
    ))
    line = parse(await draw.autocad_draw_line(start=[0, 63000], end=[100, 63000], layer="LC-3D"))
    message = refusal(await solids.autocad_solid_boolean(
        operation="union", handle=solid["handle"], others=[good["handle"], line["handle"]]
    ))
    expect("not a 3D solid" in message, f"it was refused for the wrong reason: {message[:140]}")
    for handle, label in ((solid["handle"], "the first solid"), (good["handle"], "the good solid")):
        still = parse(await query.autocad_get_entity(handle=handle))
        expect(still is not None, f"{label} was consumed by a call that failed")
    return "a line among the solids was refused by name, and neither solid was consumed"


async def e31_a_solid_reports_its_volume(ctx: Context) -> str:
    handle = ctx.store.get("plate") or ctx.store.get("box")
    expect(handle, "no solid from an earlier row to measure")
    out = parse(await solids.autocad_solid_properties(handles=[handle]))
    item = out["items"][0]
    expect(item.get("volume"), f"no volume came back: {item}")
    expect(item.get("centroid"), f"no centroid came back: {item}")
    expect(item.get("bounding_box"), f"no bounding box came back: {item}")
    return (f"volume {item['volume']:g}, centroid {[round(v, 1) for v in item['centroid']]}, "
            f"size {item.get('size')}")


async def e32_a_helix_comes_out(ctx: Context) -> str:
    out = parse(await solids.autocad_draw_3d_path(
        helix_radius=100, helix_turns=3, helix_height=600,
        helix_centre=[0, 64000, 0], layer="LC-3D",
    ))
    expect(out["shape"] == "helix", f"it reported {out['shape']}")
    want = math.hypot(2 * math.pi * 100 * 3, 600)
    expect(out["length"] and abs(out["length"] - want) / want < 0.01,
           f"its length is {out.get('length')}, but a 3-turn r100 helix rising 600 is about {want:.1f}")
    got = parse(await query.autocad_get_entity(handle=out["handle"]))
    box = got["bounding_box"]
    rise = box["max"][2] - box["min"][2]
    expect(near(rise, 600.0, 1e-3), f"the helix rises {rise}, not 600")
    return (f"3D polyline of {out['vertex_count']} points, length {out['length']:.1f} "
            f"(expected about {want:.1f}), rising {rise:.1f}")


async def e34_the_3d_view_and_style_take(ctx: Context) -> str:
    out = parse(await solids.autocad_set_3d_view(direction="sw_iso", visual_style="hidden"))
    expect(out.get("direction") == [-1.0, -1.0, 1.0], f"the direction reads {out.get('direction')}")
    expect(not out.get("not_set"), f"something was refused: {out.get('not_set')}")
    vscurrent = str(await variable("VSCURRENT") or "")
    expect("hidden" in vscurrent.lower(), f"VSCURRENT reads {vscurrent!r}, not Hidden")
    back = parse(await solids.autocad_set_3d_view(direction="top", visual_style="2dwireframe"))
    expect(back.get("direction") == [0.0, 0.0, 1.0], f"going back gave {back.get('direction')}")
    return f"sw_iso + hidden took (VSCURRENT={vscurrent}), then back to plan"


async def e36_bulges_and_text_alignment_round_trip(ctx: Context) -> str:
    """Everything the shape library rests on: DXF 42, and 72/73/11."""
    made = parse(await batch.autocad_batch_draw(operations=[
        {"type": "polyline", "points": [[0, 66000], [1000, 66000], [1000, 67000]],
         "bulges": [0, 0.4142135624, 0], "layer": "LC-SHAPE"},
        {"type": "text", "position": [500, 68000], "text": "CENTRED", "height": 100,
         "align": "center", "layer": "LC-SHAPE"},
    ]))
    expect(made["created"] == 2, f"it made {made['created']} of 2")
    info = parse(await geometry_tools.autocad_polyline_info(handle=made["handles"][0]))
    arcs = [s for s in info["segments"] if s["kind"] == "arc"]
    expect(len(arcs) == 1, f"the polyline has {len(arcs)} arcs; the bulge did not take")
    expect(near(arcs[0]["sweep_degrees"], 90.0, 1e-3),
           f"the arc sweeps {arcs[0]['sweep_degrees']} degrees, not 90")
    text = parse(await query.autocad_get_entity(handle=made["handles"][1]))
    box = text["bounding_box"]
    mid_x = (box["min"][0] + box["max"][0]) / 2.0
    expect(abs(mid_x - 500.0) < 1.0, f"the text's middle is at x={mid_x:.2f}, not 500 - not justified")
    return (f"bulge 0.4142 became a {arcs[0]['sweep_degrees']:.3f} degree arc inside the polyline; "
            f"centred text's box middle at x={mid_x:.2f}")


# ---------------------------------------------------------------------------
# The register
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Check:
    row: str
    group: str
    title: str
    run: Callable[[Context], Awaitable[str]]


CHECKS: tuple[Check, ...] = (
    Check("D1", "D", "status reports a rotated UCS", d1_status_reports_a_rotated_ucs),
    Check("D2", "D", "get_ucs matches UCSORG / UCSXDIR", d2_get_ucs_matches_the_system_variables),
    Check("D3", "D", "convert_points round trips", d3_convert_points_round_trips),
    Check("D4", "D", "batch draws square to the UCS", d4_batch_draws_square_to_the_ucs),
    Check("D7", "D", "a tilted UCS is refused", d7_a_tilted_ucs_is_refused),
    Check("D6", "D", "the UCS lines up with a block", d6_the_ucs_lines_up_with_a_block),
    Check("D5", "D", "the UCS goes back to world", d5_the_ucs_goes_back_to_world),
    Check("D8", "D", "a sheet is made with its paper", d8_a_sheet_is_made_with_its_paper),
    Check("D9", "D", "a copied sheet carries its setup", d9_a_copied_sheet_carries_its_setup),
    Check("D10", "D", "page setup reaches every sheet", d10_page_setup_reaches_every_sheet),
    Check("D13", "D", "a viewport comes out at its scale", d13_a_viewport_comes_out_at_the_scale_asked_for),
    Check("D14", "D", "a fitted viewport picks a standard scale", d14_a_fitted_viewport_picks_a_standard_scale),
    Check("D16", "D", "a viewport sits where the paper numbers say",
          d16_a_viewport_sits_where_the_paper_numbers_say),
    Check("D18", "D", "a saved view gives its corners back", d18_a_saved_view_gives_its_corners_back),
    Check("D21", "D", "the scale sets DIMSCALE, LTSCALE, TEXTSIZE", d21_the_scale_sets_everything_that_hangs_off_it),
    Check("D23", "D", "a dim style leaves the drawing alone", d23_a_dim_style_leaves_the_drawing_as_it_found_it),
    Check("D24", "D", "the remap plan shows the work first", d24_the_remap_plan_shows_the_work_first),
    Check("D25", "D", "the remap lands, with colours",
          d25_the_remap_lands_with_colours_and_reports_what_it_could_not),
    Check("D26", "D", "an import is tidied", d26_an_import_is_tidied),
    Check("D27", "D", "a sequence runs its steps in order", d27_a_sequence_runs_its_steps_in_order),
    Check("D28", "D", "a bad step changes nothing", d28_a_bad_step_changes_nothing),
    Check("D29", "D", "a step that fails at run time stops the rest",
          d29_a_step_that_fails_at_run_time_stops_the_rest),
    Check("D30", "D", "a sequence cannot spend more than Changes", d30_a_sequence_cannot_spend_more_than_changes),
    Check("E1", "E", "a slot is one object", e1_a_slot_is_one_object),
    Check("E2", "E", "a rounded rectangle keeps its size", e2_a_rounded_rectangle_keeps_its_size),
    Check("E3", "E", "a flange puts its holes on the PCD", e3_a_flange_puts_its_holes_on_the_pitch_circle),
    Check("E4", "E", "the flat pattern rolls onto its cone", e4_the_flat_pattern_rolls_onto_its_cone),
    Check("E7", "E", "bubble text sits on its point", e7_bubble_text_sits_on_its_point),
    Check("E9", "E", "a shape can be drawn in the UCS", e9_a_shape_can_be_drawn_in_the_ucs),
    Check("E10", "E", "a dry run draws nothing", e10_a_dry_run_draws_nothing),
    Check("E11", "E", "a dimension run measures what it says", e11_a_dimension_run_measures_what_it_says),
    Check("E13", "E", "ordinate dimensions work", e13_ordinate_dimensions_work),
    Check("E15", "E", "centre marks land on every circle", e15_centre_marks_land_on_every_circle),
    Check("E16", "E", "a multileader takes several arrows", e16_a_multileader_takes_several_arrows),
    Check("E18", "E", "a schedule becomes a table", e18_a_schedule_becomes_a_table),
    Check("E20", "E", "a revision cloud is one object of even arcs", e20_a_revision_cloud_is_one_object_of_even_arcs),
    Check("E22", "E", "a solid sits on its base", e22_a_solid_sits_on_its_base),
    Check("E23", "E", "every primitive comes out", e23_every_primitive_comes_out),
    Check("E24", "E", "a profile becomes a solid", e24_a_profile_becomes_a_solid),
    Check("E26", "E", "a profile revolves", e26_a_profile_revolves),
    Check("E28", "E", "a boolean takes material away", e28_a_boolean_takes_material_away),
    Check("E29", "E", "a boolean refuses before consuming", e29_a_boolean_refuses_before_consuming),
    Check("E31", "E", "a solid reports its volume", e31_a_solid_reports_its_volume),
    Check("E32", "E", "a helix comes out", e32_a_helix_comes_out),
    Check("E34", "E", "the 3D view and style take", e34_the_3d_view_and_style_take),
    Check("E36", "E", "bulges and text alignment round trip", e36_bulges_and_text_alignment_round_trip),
)

# Rows the register holds that only an eye can answer, said plainly rather than
# left looking un-run for no reason.
BY_EYE: dict[str, str] = {
    "D11": "which sheet sizes a plotter offers depends on the plotter installed",
    "D12": "needs your own title block .dwg, and the corner has to be looked at",
    "D15": "the twist direction has to be looked at, not measured",
    "D22": "which variables are read-only depends on the AutoCAD release",
    "D17": "zooming inside a locked viewport is a thing you do with the mouse",
    "D19": "needs the Publish padlock and a look at the PDF",
    "D20": "needs a look at the plotted sheet",
    "D31": "'the sheet looks right' is a judgement, not a measurement",
    "E5": "the stair profile is better judged by eye",
    "E6": "the steel section outlines are better judged by eye",
    "E8": "the scale bar's look is a judgement",
    "E12": "the baseline spacing is clearest by eye once E11 passes",
    "E14": "an aligned run is clearest by eye once E11 passes",
    "E17": "needs a block of your own to carry",
    "E19": "needs a drawing with real attribute blocks in it",
    "E21": "a clockwise boundary is easiest to make by picking points",
    "E25": "the taper is better judged by eye",
    "E27": "needs curves with a deliberate gap, easiest drawn by hand",
    "E30": "two solids that do not touch, easiest placed by hand",
    "E33": "a route through a building needs a building",
    "E35": "going back to plan is clearest by eye",
}


async def scratch_drawing() -> tuple[str, str | None]:
    """A new drawing to work in. Returns (its name, the one that was active)."""

    def make() -> tuple[str, str | None]:
        app = get_app()
        was = str(app.ActiveDocument.Name) if int(app.Documents.Count) else None
        doc = app.Documents.Add()
        return str(doc.Name), was

    return await run(make)


async def close_scratch(name: str, restore: str | None) -> None:
    def close() -> None:
        app = get_app()
        for i in range(int(app.Documents.Count)):
            if str(app.Documents.Item(i).Name) == name:
                app.Documents.Item(i).Close(False)
                break
        if restore:
            for i in range(int(app.Documents.Count)):
                if str(app.Documents.Item(i).Name) == restore:
                    app.Documents.Item(i).Activate()
                    break

    await run(close)


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--group", default="all", help="D, E or all (default all)")
    parser.add_argument("--row", action="append", help="run only these rows, e.g. --row E4 --row D13")
    parser.add_argument("--list", action="store_true", help="list the rows and exit, without AutoCAD")
    parser.add_argument("--write", action="store_true", help="write the results into docs/NEEDS-CHECKING.md")
    parser.add_argument("--keep", action="store_true", help="leave the scratch drawing open to look at")
    args = parser.parse_args()

    wanted = list(CHECKS)
    if args.row:
        rows = {r.upper() for r in args.row}
        wanted = [c for c in wanted if c.row in rows]
    elif args.group.lower() != "all":
        group = args.group.upper()
        wanted = [c for c in wanted if c.group == group]

    if args.list:
        print(f"{len(CHECKS)} measured rows, {len(BY_EYE)} that need an eye\n")
        for check in CHECKS:
            print(f"  {check.row:5} {check.title}")
        print("\nNeed an eye (reported NOT RUN with the reason):")
        for row, why in sorted(BY_EYE.items()):
            print(f"  {row:5} {why}")
        return 0

    if not wanted:
        print(f"No rows match {args.row or args.group}. Try --list.")
        return 1

    print(f"Heron live check: {len(wanted)} row(s)\n" + "=" * 72)
    ctx = Context()
    try:
        status = parse(await document.autocad_status())
        ctx.version = str(status.get("version", "unknown"))
        print(f"AutoCAD {ctx.version} | {status.get('application', '')}")
    except (Failed, Refused) as exc:
        print(f"Cannot reach AutoCAD: {exc}")
        print("Start AutoCAD, open a drawing, and press Heron on the Heron tab.")
        return 1

    name, restore = await scratch_drawing()
    print(f"Working in a scratch drawing: {name}\n")
    # The gate wants units checked in the drawing it is about to change.
    parse(await document.autocad_status())

    outcomes: list[Outcome] = []
    try:
        for check in wanted:
            try:
                detail = await check.run(ctx)
                outcomes.append(Outcome(check.row, True, detail))
                print(f"  PASS  {check.row:5} {check.title}\n          {detail}")
            except Refused as exc:
                outcomes.append(Outcome(check.row, False, "", skipped=True, reason=f"refused: {exc}"))
                print(f"  ----  {check.row:5} {check.title}\n          refused: {exc}")
            except Failed as exc:
                outcomes.append(Outcome(check.row, False, str(exc)))
                print(f"  FAIL  {check.row:5} {check.title}\n          {exc}")
            except Exception as exc:  # noqa: BLE001 - one row, not the run
                outcomes.append(Outcome(check.row, False, f"{type(exc).__name__}: {exc}"))
                print(f"  FAIL  {check.row:5} {check.title}\n          {type(exc).__name__}: {exc}")
    finally:
        if args.keep:
            print(f"\nThe scratch drawing {name} is still open; close it without saving.")
        else:
            await close_scratch(name, restore)

    for row, why in BY_EYE.items():
        if args.group.lower() in ("all", row[0].lower()) and not args.row:
            outcomes.append(Outcome(row, False, "", skipped=True, reason=why))

    counts = summarise(outcomes)
    print("=" * 72)
    print(f"{counts['passed']}/{counts['checked']} measured rows passed, {counts['skipped']} need an eye")
    if counts["failed"]:
        print("\nFailed:")
        for outcome in outcomes:
            if not outcome.ok and not outcome.skipped:
                print(f"  {outcome.row}: {outcome.detail}")

    if args.write:
        register = REGISTER.read_text(encoding="utf-8")
        new, written, missing = apply_results(register, outcomes, date.today().isoformat(), ctx.version)
        REGISTER.write_text(new, encoding="utf-8")
        print(f"\nWrote {len(written)} row(s) into {REGISTER.relative_to(ROOT)}")
        if missing:
            print(f"  not in the register: {', '.join(missing)}")
    else:
        print("\nNothing was written. Add --write to put these results in the register.")

    return 1 if counts["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
