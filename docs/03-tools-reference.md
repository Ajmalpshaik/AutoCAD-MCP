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

## Session and files (Read / View; save and export are Publish)

| Tool | Purpose |
|---|---|
| `autocad_status` | Connection check, units, current layer, entity counts |
| `autocad_list_drawings` | Every drawing currently open |
| `autocad_create_drawing` | New drawing, optionally from a template |
| `autocad_open_drawing` | Open a .dwg or .dxf |
| `autocad_save_drawing` | Save, or Save As to a new path |
| `autocad_switch_drawing` | Make another open drawing active |
| `autocad_export` | PDF (extents fitted, optional `paper_size` such as `A3`, `A1 portrait`), DXF, WMF, SAT, BMP, EPS, STL |
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

## Take-off and dynamic blocks (get Read, set Change)

From the [Lee Mac study](08-lee-mac-study.md); our own code.

| Tool | Purpose |
|---|---|
| `autocad_count_blocks` | Count blocks by real name (dynamic blocks too); `group_by` name, name_layer, name_visibility, name_properties; name and layer wildcards |
| `autocad_total_length` | Total length and closed area by layer, type or one total; splines and ellipses counted as unmeasured |
| `autocad_get_dynamic_properties` | A dynamic block's properties: value, allowed choices, read-only |
| `autocad_set_dynamic_properties` | Set visibility, size, distance, flip: `{name: value}`, typed and checked; failures listed |

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

They call the gated tools, so they are refused the same way while AutoCAD is not connected.
Prompts: `check_standards` (report only), `draw_from_spec` (draw, then preview).

## Start options

| Option | Effect |
|---|---|
| `--read-only` | Only Read and View tools are offered; nothing can change a drawing |
| `--no-bridge` | Developers only: skip the plug-in (no padlocks, banner, Keep or Discard) |
| `--transport http --host --port` | Serve over HTTP (no authentication: trusted networks only) |
