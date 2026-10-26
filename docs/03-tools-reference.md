# 03 - Tools reference

The live list, always right: `.venv\Scripts\autocad-mcp.exe --list-tools`. This page groups them and
adds what the one-line descriptions leave out.

**Levels.** Every tool has a level ([`core/risk.py`](../src/autocad_mcp/core/risk.py)) that decides
which padlock it needs in AutoCAD: Read and View need only the connection; Change needs **Changes**;
Publish needs Changes + **Publish**; Admin needs Changes + **Admin** ([06](06-heron-plugin.md)).
The group headings below give the level.

**Rules for every tool**

- Coordinates are in the drawing's own units. Call `autocad_status` first to learn them.
- Angles are **degrees**.
- Entities are identified by their **handle**. Creation and query tools return it; modify tools take it.
- Drawing tools share `layer`, `color`, `linetype` and `space` options. A missing layer is created
  and reported.
- **Coordinates are WORLD coordinates.** `autocad_status` reports the drawing's UCS and warns when
  it is not the world one. `autocad_batch_draw`, `autocad_make_shape` and the other tools built on
  that engine take `coords="ucs"`; for the rest convert first with `autocad_convert_points`
  ([09](09-sheets-and-coordinates.md)).
- `autocad_batch_draw` polylines take **`bulges`** (one per vertex, `tan(sweep/4)`, positive
  anticlockwise) so arcs stay part of the object, and text takes **`align`** and `style`.

## Session and files (Read / View; save and export are Publish)

| Tool | Purpose |
|---|---|
| `autocad_status` | Connection check, units, current layer, entity counts |
| `autocad_list_drawings` | Every drawing currently open |
| `autocad_create_drawing` | New drawing, optionally from a template |
| `autocad_open_drawing` | Open a .dwg or .dxf |
| `autocad_save_drawing` | Save, or Save As to a new path |
| `autocad_switch_drawing` | Make another open drawing active |
| `autocad_export` | PDF, DXF, WMF, SAT, BMP, EPS, STL. PDF takes `paper_size` (`A3`, `A1 portrait`), `area` (`extents` default, `layout`, `limits`, `display`, `window`, `view`), `corner1`/`corner2`, `view_name` and `scale` |
| `autocad_zoom` | Extents, all, or a window |
| `autocad_get_variable` | Read a system variable |
| `autocad_set_variable` | Write a system variable |

## Drawing (Change)

`autocad_draw_line`, `autocad_draw_polyline`, `autocad_draw_rectangle`, `autocad_draw_circle`,
`autocad_draw_arc`, `autocad_draw_ellipse`, `autocad_draw_point`, `autocad_add_text`,
`autocad_add_mtext`, `autocad_add_dimension`, `autocad_insert_block`, `autocad_add_hatch`

## Labels (Change)

`autocad_add_label` puts a label on something: MTEXT plus a leader with an arrow. Use it for every label.

| Option | Meaning |
|---|---|
| `kind="leader"` (default) | Ajmal's TLD style (TextLeader_V4.lsp): MTEXT and a LEADER on the text's layer, ending under the text between line 1 and line 2, full width + `extension` x text height each side |
| `shape="L"` / `"angled"` | Square leg from the arrow, or straight to the near end of the text. Use `angled` for a column of labels |
| `kind="mleader"` | One MULTILEADER with the text as its content |

The arrow is sized from DIMSCALE (a leader made over COM ignores the override). Dimensions made by
`autocad_add_dimension` get DIMSCALE the same way.

## Blocks from parts (Change)

`autocad_make_block` turns drawn objects into a named block and puts one insert in their place
(`keep_originals=true` only defines it). Use it for every separate part (fitting, elbow, clamp, plate,
anchor); pipes and runs can stay as lines. More copies: `autocad_insert_block`; mirrored copies:
`autocad_mirror_entities` on the insert. Labels: `text_align="right"` hangs a label from its
top-right corner, for a tidy column left of a detail.

## Bulk drawing (Change)

`autocad_batch_draw` sends one AutoLISP script that creates many entities inside AutoCAD. Use it for
anything above about ten entities. Every operation is checked in Python first, so a bad batch fails
naming the operation index without touching the drawing. Supports line, polyline, rectangle, circle,
arc, text and point. Speeds are in [02](02-architecture.md#why-python-and-autolisp).

## Querying (Read)

| Tool | Purpose |
|---|---|
| `autocad_list_entities` | Filter by type, layer, block or colour; paginated; summary mode |
| `autocad_get_entity` | All properties and bounding box of one entity |
| `autocad_get_selection` | What you have selected in AutoCAD right now |
| `autocad_find_text` | Search text, mtext and block attributes |
| `autocad_get_extents` | Bounding box of the drawing or one layer |
| `autocad_measure` | Point-to-point distance, or total length / area of entities or a layer |

## Modifying (Change)

`autocad_move_entities`, `autocad_copy_entities`, `autocad_rotate_entities`,
`autocad_scale_entities`, `autocad_mirror_entities`, `autocad_offset_entities`,
`autocad_array_entities`, `autocad_modify_entity`, `autocad_delete_entities`

`autocad_delete_entities` needs `confirm=true`. Without it the tool returns a preview and changes
nothing.

## Layers and blocks (lists Read, the rest Change)

`autocad_list_layers`, `autocad_create_layer`, `autocad_set_layer_state`,
`autocad_set_current_layer`, `autocad_delete_layer` (needs `confirm=true`), `autocad_list_blocks`,
`autocad_list_styles`

## Escape hatches (Admin; regen is View)

| Tool | Purpose |
|---|---|
| `autocad_send_command` | Any AutoCAD command: TRIM, FILLET, add-in commands |
| `autocad_run_lisp` | Evaluate AutoLISP **and get the result back**. Keep expressions under about 700 characters ([05](05-known-limits.md)) |
| `autocad_purge` | Remove unused blocks, layers, linetypes, styles |
| `autocad_regen` | Regenerate the display |
| `autocad_audit` | Check and repair the drawing database |

`autocad_send_command` refuses commands known to open a modal dialog and names the command-line
alternative, because a dialog blocks COM until a person closes it.

## Take-off, text and placement (from the [Lee Mac study](08-lee-mac-study.md); our own code)

| Tool | Level | Purpose |
|---|---|---|
| `autocad_count_blocks` | Read | Count blocks by real name (dynamic too); group by name, layer, visibility or properties; `include_nested` |
| `autocad_total_length` | Read | Total length per layer or type, area of closed shapes; splines and ellipses measured |
| `autocad_get_dynamic_properties` | Read | A dynamic block's properties: value, allowed choices, read-only |
| `autocad_count_text` | Read | Count text / tag values (`source`, `tag`, `pattern`), optional `sum_numeric` |
| `autocad_polyline_info` | Read | Vertices, segments (arcs: centre, radius, sweep), total, area, centroid |
| `autocad_select_connected` | Read | A whole run joined end to end: handles, total length, open ends |
| `autocad_list_layouts` | Read | Layouts in tab order with plotter, paper, object count |
| `autocad_set_dynamic_properties` | Change | Set visibility, size, distance, flip; typed and checked; failures listed |
| `autocad_set_attributes` | Change | Attributes from `values`, `rows` or `csv_path`, matched by `key` (a tag or `layout`); `dry_run` |
| `autocad_number_tags` | Change | Prefix + padded number + suffix on blocks (`tag`), texts or new text; sort rows / columns / path |
| `autocad_text_clean` | Change | Strip MText formatting codes; `dry_run` |
| `autocad_find_replace_text` | Change | Find / replace (plain or regex) in text, mtext, attributes, mleaders, dim overrides, tables; `dry_run` |
| `autocad_align_text` | Change | Line up (left, right, centre, top, bottom, middle) or space evenly; the first object stays put |
| `autocad_add_field_label` | Change | Live Length / Area field (sum of several) in new text or an attribute; `factor` for m / m2 |
| `autocad_label_segment_lengths` | Change | Length at each segment's middle; `split_at_layer` splits at crossings |
| `autocad_place_along` | Change | Blocks along a run by `spacing` (equal ends) or `count`; `align` turns them to the run |
| `autocad_place_from_csv` | Change | Blocks at x, y (rotation, block) from a CSV; other columns fill attributes |
| `autocad_break_at_blocks` | Change | Cut lines / straight polylines through block extents + `gap` |
| `autocad_import_from_drawing` | Change | Blocks, layers, linetypes, text / dim styles from a closed DWG; existing names skipped |
| `autocad_manage_layouts` | Change | Order, renumber, rename layouts; copy paper-space objects to other layouts |

## Coordinates and the UCS (Read; setting it is Change)

A rotated or moved UCS is why a line lands somewhere nobody meant. Detail:
[09 §1](09-sheets-and-coordinates.md#1-the-ucs-why-a-line-lands-in-the-wrong-place).

| Tool | Level | Purpose |
|---|---|---|
| `autocad_get_ucs` | Read | Is a UCS set? Origin, axes, rotation in degrees, moved / rotated / tilted / flipped, the saved ones, and what to do about it |
| `autocad_convert_points` | Read | AutoLISP's `trans`: points and angles between the UCS and the world. Changes nothing |
| `autocad_set_ucs` | Change | `world`, `named`, `origin` + angle, `3point`, `entity`, `view`; `save_as` keeps it by name |

## Sheets, title blocks and viewports (Change)

A sheet from nothing in four calls, or one `autocad_sequence`. Detail:
[09 §3](09-sheets-and-coordinates.md#3-laying-out-a-sheet).

| Tool | Purpose |
|---|---|
| `autocad_create_layout` | New sheet: paper size, orientation, plotter, plot style table, optionally copied from another layout. Returns the frame, the drawing space and where the title block goes |
| `autocad_page_setup` | Page Setup on one sheet or `all_layouts`: plotter, paper, `plot_area`, scale, `monochrome.ctb`, lineweights. Only what you pass is written |
| `autocad_place_title_block` | The title block in the sheet's corner (ISO 5457 bottom-right by default) with its attributes filled; `all_layouts` and `per_layout_attributes` do a whole set |
| `autocad_add_viewport` | A viewport at a real scale (`"1:50"`, or omitted to fit) looking at a point, a window, a saved view or a set of objects; `twist` / `align_to_ucs` for a rotated plan; locked by default |

## Saved locations (Read; saving is Change)

One named area, used for a plot, a viewport and a measurement. Detail:
[09 §2](09-sheets-and-coordinates.md#2-one-location-used-everywhere).

| Tool | Level | Purpose |
|---|---|---|
| `autocad_list_views` | Read | Every saved view with its centre, size and both corners |
| `autocad_save_view` | Change | Name an area, from two corners or from the objects' own extents + `pad` |

## Drawing settings and styles (Change)

| Tool | Purpose |
|---|---|
| `autocad_drawing_setup` | Units, precision, the drawing `scale` (which sets DIMSCALE, the annotation scale and LTSCALE), `paper_text_height`, object snaps, point style, linetype scaling, limits. `dry_run` shows the plan; writes only from a fixed list ([D-28](DECISIONS.md)) |
| `autocad_create_styles` | Text styles (font, height, width factor, oblique) and dimension styles (scale, text height, arrows, precision, or raw `DIM...` variables). The drawing's own DIM variables are put back |

## An import into a shop drawing (Change)

Both default to `dry_run=true`: read the counts, then run it. Detail:
[09 §5](09-sheets-and-coordinates.md#5-an-ifc-or-revit-export-into-a-shop-drawing).

| Tool | Purpose |
|---|---|
| `autocad_remap_layers` | Rules match `name_like` (layer **or** block name), `source_layer`, `block_name`, `entity_type`, `source_color`, `text_contains`; the target layer is created with its colour, linetype, lineweight, description and plot setting. `preset="ifc"` is a starting point; `rules_path` takes an office standard |
| `autocad_tidy_entities` | Colour / linetype / lineweight back to ByLayer, `flatten_z`, `zero_thickness`, `off_layer_0`, `delete_empty` |

## Several tools in one call (Change)

`autocad_sequence` runs a list of steps in order. Every step's arguments are checked against that
tool's own schema **before the first one runs**, so a sequence with a mistake in step four changes
nothing. Steps at the Publish or Admin level, and a sequence inside a sequence, are refused: a
sequence holds the **Changes** padlock only ([D-29](DECISIONS.md)). `stop_on_error` (default true)
and `dry_run`.

## Shapes from a few numbers (Change)

`autocad_make_shape` draws a named shape from its dimensions — 24 of them, from
a slot to a reducer's flat pattern. Detail: [10 §1](10-geometry-annotation-3d.md#1-simple-words-complex-geometry).

| Group | Shapes |
|---|---|
| Plain | polygon, hexagon (across flats), star, slot, rounded_rectangle, spiral, zigzag |
| Fabrication | flange, bolt_circle, steel_section (i/h/c/l/t/shs/rhs/chs), gear, **cone_development** (the flat pattern for a reducer) |
| MEP | elbow (with centreline), duct_transition, grating |
| Building | stair (section or plan), ladder, truss |
| Furniture | detail_bubble, section_mark, north_arrow, scale_bar, level_mark, revision_tag |

Arcs come out as polyline bulges, so a slot or an elbow stays **one object**.
`dry_run=true` returns the geometry instead of drawing it.

## Dimensioning and annotation (Change)

| Tool | Purpose |
|---|---|
| `autocad_dimension_run` | A whole run in one call: `chain`, `baseline` (stepped clear of each other), `overall`, `ordinate`. Horizontal, vertical or aligned; the points are put in order first; `include_overall` adds the overall above. Reports both its own arithmetic and AutoCAD's measurement |
| `autocad_add_centre_marks` | The cross on every circle and arc, by handle or by layer; `extend` makes full centre lines |
| `autocad_add_multileader` | One note with **as many arrows as it needs**; text or block content |
| `autocad_add_table` | A schedule as a real AutoCAD table, with title and headings |
| `autocad_add_revision_cloud` | A cloud round a boundary, a rectangle, or an object's own extents. One polyline with bulges, like REVCLOUD |

## 3D (Change; reading is Read, the view is View)

| Tool | Level | Purpose |
|---|---|---|
| `autocad_add_solid` | Change | box, wedge, cylinder, cone, sphere, torus — placed by the centre of its **base**, not its bounding box |
| `autocad_extrude_profile` | Change | A closed 2D profile into a solid: extrude along Z (with taper) or revolve about an axis. The intermediate region is cleaned up |
| `autocad_solid_boolean` | Change | union / subtract / intersect. The others are **consumed**, as AutoCAD's own commands do; every handle is checked first |
| `autocad_solid_properties` | Read | Volume, centroid, bounding box, moments — for a weight take-off |
| `autocad_draw_3d_path` | Change | A pipe or cable route as one 3D polyline, or a helix |
| `autocad_set_3d_view` | View | A named direction (top, front, sw_iso …) and a visual style. Changes only what is on screen ([D-31](DECISIONS.md)) |

## Seeing and checking (Read)

| Tool | Purpose |
|---|---|
| `autocad_preview` | Plot the extents, the current view or a window to PNG and return the **picture** to the AI. Use after drawing, before saying it is done. Page setup put back |
| `autocad_check_standards` | Check layers and objects against rules: `layer_name_pattern`, `layers {name: {color, linetype}}`, `forbid_entities_on_layer_0`, `require_bylayer_color`, `require_bylayer_linetype`, `max_findings`. Inline or a JSON file |
| `autocad_extract_attributes` | Every block reference with attributes as rows (block, handle, layer, insertion, tags), JSON or CSV - for schedules |

## Resources and prompts

| Resource | Same as |
|---|---|
| `autocad://drawing/status` | `autocad_status` |
| `autocad://drawing/layers` | `autocad_list_layers` |
| `autocad://drawing/blocks` | `autocad_list_blocks` |
| `autocad://drawing/styles` | `autocad_list_styles` |
| `autocad://tools` | **the toolbox index** — not a drawing read, so it needs no AutoCAD |

The four drawing resources call the gated tools, so they are refused the same way while AutoCAD is
not connected.

`autocad://tools` is the one that is not about the drawing: every tool grouped by the padlock it
needs, with its one-line summary and its **`Use when`** lines. It is built from the live registry,
so it cannot drift from the code, and it answers before Heron is pressed. Each tool's own
`Use when:` / `Don't use when:` bullets name the better tool when there is one — which is how 101
tools stay findable. A tool without them fails `tests/test_tool_index.py`.

A prompt is a whole job written out in the right order, so the AI does not have to work out which
of the tools to reach for or what to check afterwards. Pick one in your client and fill in its
arguments.

| Prompt | Arguments | What it walks through |
|---|---|---|
| `check_standards` | `rules_path` | Checks the drawing against a layer standard and reports. Changes nothing |
| `draw_from_spec` | `spec` | Draws from a written spec on named layers, then previews it |
| `draw_detail` | `subject`, `scale` | The full drafting checklist: sheet plan, layers, parts as blocks, hatching, labels, dimensions, titles, notes, then look at it |
| `make_sheet` | `sheet_name`, `paper_size`, `scale` | Layout, page setup, title block, viewport at a scale, and a saved view so the same location comes back |
| `import_to_shop_drawing` | `discipline`, `scale` | An IFC or CAD import into a shop drawing: layer audit, remap and tidy (dry run first), styles, details, dimensions, annotation, sheet, PDF |
| `model_part` | `part`, `material` | Profile, extrude or revolve, cut the holes, take the volume and weight off the solid, and the flat pattern if it is rolled |
| `shape_from_words` | `description`, `scale` | Picks the shape from the catalogue, dry-runs it, draws it, then measures it back |

Every tool a prompt names is checked against the registry by `tests/test_drafting_rules.py`, so a
prompt cannot send the AI after a tool that was renamed or never built.

## Start options

| Option | Effect |
|---|---|
| `--read-only` | Only Read and View tools are offered; nothing can change a drawing |
| `--no-bridge` | Developers only: skip the plug-in (no padlocks, banner, Keep or Discard) |
| `--transport http --host --port` | Serve over HTTP (no authentication: trusted networks only) |
