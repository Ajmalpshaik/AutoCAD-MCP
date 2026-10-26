# Needs checking - what is built but not yet proven in a real AutoCAD

> A build is not a proof, and a passing offline test is not a proof. A row is **PASS** only after it
> was run in the named AutoCAD and gave the result in the last column. Four states, kept apart:
> **PASS**, **FAIL** (with what happened), **NOT RUN**, **NO MACHINE** (no PC with that version yet).
> Put the date and the AutoCAD version in the result.

**Set-up for every row:** build and install the plug-in (`tools/build_plugin.py`, close AutoCAD,
`tools/install_plugin.py`), start AutoCAD, open a scratch drawing, and connect Claude Code in this
folder.

## Group A - AutoCAD 2027 (this PC)

| Row | Do | Pass looks like | Result |
|---|---|---|---|
| A1 | Start AutoCAD | Tab **Heron**, panel **AI Bridge**, dark heron, four blue padlocks; command line shows nothing alarming; log file written | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): tab, panel, dark heron, four padlocks off |
| A2 | Ask Claude "check the AutoCAD connection" before pressing Heron | Status answers, with `"heron": {"connected": false, ...}` and the press-Heron sentence | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): after Disconnect, status returned only `heron: connected false` + press-Heron sentence, no drawing data |
| A3 | Press **Heron** | Icon lights; command line `Heron: connected...`; `%LOCALAPPDATA%\Heron\autocad\bridges\<pid>.json` exists | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): icon lit/dark follows each click; address file written and removed |
| A4 | "List the layers" | READING banner (blue) appears, then DONE; the layers come back; `Heron: List Layers. Done in ...` | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): reads accepted; begin/end logged |
| A5 | "Draw a line from 0,0 to 1000,0" with Changes **off** | Refused naming **Changes** and HERONCHANGES; nothing drawn; no banner | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): draw and LISP refused naming Changes; drawing still empty; audit `refused` |
| A6 | Click **Changes**, answer Yes, repeat A5 | Red padlock; CHANGING banner (amber); line drawn; one Ctrl+Z removes it | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): asks before turning on; CHANGING banner seen; one U removed the rectangle |
| A7 | Click **Changes** again | Off with no question | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): turned off with no question |
| A8 | Ask to Keep on, Changes on, draw a circle, click **Discard it** | Circle selected and zoomed before the box; after Discard it is gone; chat says `Discarded: nothing was kept.` | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): box with circle selected and zoomed; Keep kept it; Discard removed it |
| A9 | Same, click **Keep, and keep the rest...**, then draw twice more | No more boxes; ribbon reads **Keep: rest of job** (within 15 s) | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): after 'keep the rest', next two draws had no box (61 / 78 ms). Ribbon label not confirmed |
| A8b | Ask to Keep on: draw, Keep; then draw again and Discard | Only the second drawing goes; the first stays; the view returns to where it was | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): earlier kept circle stayed; VIEWSIZE 2080 before and after Discard (view went back) |
| A8c | Ask to Keep on: `autocad_batch_draw` with a new layer, Discard | Objects and the new layer both gone | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): batch objects and its new layer both gone after Discard. See A21 |
| A8d | Ask to Keep on: delete with `confirm=false` (preview) | No Keep box; nothing undone | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): `confirm=false` preview gave no box and undid nothing |
| A8e | Ask to Keep on: draw, then leave the mouse still | The Keep box appears at once, without moving the mouse | **Likely PASS** 2026-10-26: answered 8 s after the draw; not confirmed in words |
| A23 | Keep box: press Enter, and another time Esc | Enter keeps, Esc discards, arrows move between choices | **FAIL then PASS** 2026-10-26: first only the mouse worked and nothing showed the keyboard's place; now the box takes focus, a thick blue border follows the arrow keys, and Enter chose the bordered choice (Discard, removed the circle) |
| A10 | Open a second drawing in the same AutoCAD, make it active, ask to draw | Refused: active drawing changed from A to B; after "check status" the draw works | **FAIL then PASS** 2026-10-26, AutoCAD 2027 (26.0s): a fresh server let the first change through unchecked; fixed (D-19: units checked first); re-run refused before status and after switching, Drawing2 = millimetres, Drawing1 = inches |
| A11 | "Export to PDF" with Publish off, then on | Off: refused naming Publish. On: PDF written | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): on wrote an A3 PDF; off refused naming Publish, no file |
| A12 | "Run the LISP (+ 1 2)" with Admin off, then on | Off: refused naming Admin. On: 3 | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): on returned 3; off refused naming Admin |
| A13 | "Show me the drawing" | `autocad_preview` returns a PNG the chat can see; page setup unchanged (PAGESETUP) | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): PNG received by the chat. Note: portrait, drawing at the left edge (ROADMAP) |
| A14 | Press **Heron** to disconnect, ask anything | Icon dark; address file gone; every tool refused with the press-Heron sentence | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): icon dark, address file gone, tools refused with press-Heron |
| A15 | Two AutoCAD 2027 windows, connect only the second | Claude reaches the one COM attaches to; if that one is not connected, it is refused (no cross-talk) | **PASS** 2026-10-26: COM attached to the first (pid 16068); with the first connected it worked on CCTV_Package.dwg; with only the second (pid 40440) connected, every call was refused 'not connected' and nothing reached either AutoCAD. Limit: the second cannot be chosen yet (ROADMAP) |
| A16 | Second Claude session asks while the first is working | Second refused: in use by another chat; works after 3 quiet minutes | **PASS** 2026-10-26: second chat refused ('in use by another chat', no drawing data) at 1.4 min; let in after 3 quiet minutes (status + layers of CCTV_Package.dwg) |
| A17 | Switch workspace (WSCURRENT) | Heron tab comes back | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): tab still there after a workspace switch |
| A18 | Bridge Status in each state | Wording and buttons as in [06 §2](06-heron-plugin.md#2-bridge-status); Enter = Close | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): wording, padlock cards and versions correct; Disconnect works; Enter closed the window and stayed connected |
| A20 | Double-click a padlock | Acts once (the second click is ignored) | **FAIL then PASS** 2026-10-26: 0.86 s between clicks beat the 0.7 s window; with 1.5 s, a double-click on Ask to Keep acted once (no box) and rapid Admin clicks logged 'second click ... ignored' |
| A22 | `autocad_batch_draw` with the plug-in connected, then F2 | Only `Command:` prompts and `Heron: Batch Draw Geometry. Done in ...`; no LISP text, no coordinates | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): 41 objects in 0.16-0.19 s (was 1.4 s over COM), history clean after two fixes (polyline list, helper name) |
| A21 | `autocad_batch_draw` with SECURELOAD on (default) | No security box | **FAIL then PASS** 2026-10-26, AutoCAD 2027 (26.0s): the old .lsp in %TEMP% raised 'Unsigned Executable File'; after D-21, 40 circles + a 150-point polyline drew in 1.4 s with no box. Command history fills with the LISP text (ROADMAP) |
| A24 | `autocad_add_label`, 13 labels, shape angled, on the roof pipe-support detail | Real LEADERs with arrows under MTEXT, on the text's layer | **FAIL then PASS** 2026-10-26: first drawn as splines without arrows (leader type 1); type 2 gives straight leaders with arrows under the text |
| A25 | `autocad_make_block` on a detail's parts, then insert and mirror copies | Parts become named blocks in place; copies insert; mirror makes the opposite hand | **PASS** 2026-10-26: roof pipe-support detail redrawn with 18 named blocks (anchor plan block x4, gussets mirrored), right-aligned label column, plan under elevation |
| A26 | `autocad_count_blocks` and `autocad_total_length` on valves, nuts, pipe lines, a room and a circle | Counts by name, layer and property values; lengths per layer; area only for closed shapes | **PASS** 2026-10-26 after one fix: an open polyline had reported an area (COM gives one), now closed shapes only |
| A27 | `autocad_get_dynamic_properties` / `autocad_set_dynamic_properties` on the sample "Hex Nut - Metric" | Sizes M3-M14 listed; "m6" sets M6 and the nut redraws; read-only and unknown names reported, not fatal | **PASS** 2026-10-26: count by properties then split M10 / M6 |
| A28 | `autocad_insert_block` with a C:/ forward-slash .dwg path; `autocad_list_blocks` after a dynamic nut is changed to M6 | File inserts; nut still counted 2, marked dynamic, no blank names | **PASS** 2026-10-26 |
| A29 | Every Lee Mac study tool on a test layout: import blocks from a closed DWG, place along, place from CSV, number tags, set attributes, count / total / polyline info / connected, segment and field labels, count / clean / find-replace / align text, break at block, double offset, overlapping dims, layouts | Results match hand checks | **PASS** 2026-10-26 after one fix (total length counted a leader). The field label updated itself from 22.00 m to 18.31 m after the break; the ellipse measured 9688.4 = its perimeter |
| A19 | Run a CCTV generator sheet (`python generators/cctv_run.py png 102`) with Changes on | Draws and plots as before the folder move | **PASS** 2026-10-26: CCTV_Package.dwg (23,303 objects) opened, sheet 102 plotted to PNG correctly. Found: generators started their server without the user's environment; now passed through |

## Group D - Sheets, coordinates and shop drawings (AutoCAD 2027, this PC)

The 14 tools added on 2026-10-26 ([09](09-sheets-and-coordinates.md)). Their arithmetic and their
planning are covered by the offline suites (`tests/test_coords.py`, `test_sheets.py`,
`test_settings.py`, `test_convert.py`, `test_sequence.py`); **everything COM touches is NOT RUN.**
Nothing below may be called working until its row says PASS with a date and a version.

**Set-up:** a scratch drawing in millimetres, Changes on, one piece of geometry in model space.

| Row | Do | Pass looks like | Result |
|---|---|---|---|
| D1 | Set a UCS by hand in AutoCAD (`UCS` > 3 point, turned about 23 degrees), then `autocad_status` | Reports `ucs.rotated` true, the rotation in degrees, and a `ucs_advice` sentence | NOT RUN |
| D2 | `autocad_get_ucs` with that UCS set | Origin, axes and rotation match what AutoCAD's `UCSORG` / `UCSXDIR` show; `saved` lists any named UCS | NOT RUN |
| D3 | `autocad_convert_points(points=[[100,0]], into="world")`, then draw a line to that world point | The line lands where 100,0 reads on the modeller's own screen | NOT RUN |
| D4 | `autocad_batch_draw(coords="ucs")` with a rectangle on that turned UCS | The rectangle is square to the UCS grid, not to the world; the drawing's UCS is unchanged | NOT RUN |
| D5 | `autocad_set_ucs(mode="world")`, then `mode="3point"`, then `mode="named"` back | The UCS icon moves and turns each time; one Ctrl+Z per call; `HERON-UCS` is reused, not duplicated | NOT RUN |
| D6 | `autocad_set_ucs(mode="entity")` on a rotated block, and on a block on a tilted plane | Lines up with the block; the tilted one is refused in plain words, not guessed | NOT RUN |
| D7 | Tilt the UCS out of the XY plane, then `autocad_batch_draw(coords="ucs")` | Refused, naming `autocad_convert_points`; nothing drawn | NOT RUN |
| D8 | `autocad_create_layout(name="D-101", paper_size="A1", plot_style_table="monochrome.ctb")` | New tab; Page Setup shows A1, DWG To PDF, monochrome; the returned `sheet` frame matches what PAGESETUP shows | NOT RUN |
| D9 | `autocad_create_layout(copy_from="D-101")` | The copy carries the page setup | NOT RUN |
| D10 | `autocad_page_setup(all_layouts=true, paper_size="A1", plotter="DWG To PDF.pc3", scale="1:1")` | Every tab changes; only the options passed are different afterwards | NOT RUN |
| D11 | `autocad_page_setup` with a plotter and a sheet size AutoCAD does not have | Named in the error, with the sizes that plotter does offer; the sheet is unchanged | NOT RUN |
| D12 | `autocad_place_title_block` with a real A1 title block, `all_layouts=true`, `per_layout_attributes` | One per sheet, bottom-right inside the ISO frame, right attributes per sheet; `replace_existing` does not stack a second | NOT RUN |
| D13 | `autocad_add_viewport(scale="1:100", view_name=...)` | Viewport fills the frame clear of the title block; **measure a known 10 m wall on the plot: 100 mm**; the viewport is locked | NOT RUN |
| D14 | `autocad_add_viewport` with no `scale` and a window | The reported scale is a standard one, the area fits, and the measurement matches that scale | NOT RUN |
| D15 | `autocad_add_viewport(align_to_ucs=true)` on the 23 degree UCS | The plan reads upright on the sheet; nothing falls outside the frame; the reported twist matches. **If it comes out turned the wrong way, the sign of the twist in `_aim` (sheets.py) is inverted — flip it and re-run.** The twist follows VIEWTWIST, which is +23 for a plan view of a UCS turned +23, but that has only been reasoned, not measured | NOT RUN |
| D16 | `autocad_add_viewport(paper_centre=..., paper_width=..., paper_height=...)` | The viewport is where those numbers say, in paper units | NOT RUN |
| D17 | After D13, zoom inside the viewport | Refused / no change: the lock held and the scale is still true | NOT RUN |
| D18 | `autocad_save_view` from a window, then `autocad_list_views` | The corners come back the same; `zoom_to` showed the area | NOT RUN |
| D19 | `autocad_export(area="view", view_name=...)` then `autocad_add_viewport(view_name=...)` | The PDF and the viewport show the **same** area | NOT RUN |
| D20 | `autocad_export(area="layout", scale="1:1")` on the D-101 sheet | The PDF is the sheet, title block and all, at full size; the layout's page setup is put back | NOT RUN |
| D21 | `autocad_drawing_setup(units="millimeters", scale="1:50", paper_text_height=2.5, osnaps=[...])` with `dry_run=true`, then false | The dry run writes nothing; the real run sets INSUNITS, DIMSCALE 50, LTSCALE 50, CANNOSCALE 1:50, TEXTSIZE 125, OSMODE; each `from`/`to` matches what SETVAR reports | NOT RUN |
| D22 | `autocad_drawing_setup` on a drawing where one variable is read-only for that release | That one is in `failed`; the rest still land | NOT RUN |
| D23 | `autocad_create_styles` with a text style and a dim style, then dimension something | The dim uses the new style at the right size; **the drawing's own DIM variables are back where they were** (check DIMSCALE and DIMTXT with SETVAR) | NOT RUN |
| D24 | `autocad_remap_layers(preset="ifc", dry_run=true)` on a real IFC or Revit export | `counts` and `by_rule` match a hand count of 3 sampled layers; nothing changed | NOT RUN |
| D25 | The same with `dry_run=false, set_bylayer=true` | Objects moved, the layers exist with the right colours, the drawing now plots in those colours; a locked layer appears in `failed` and the rest still land | NOT RUN |
| D26 | `autocad_tidy_entities(flatten_z=0, off_layer_0=..., dry_run=false)` on that import | Z is 0 throughout (check with LIST), layer 0 is empty of geometry, the plan now hatches and trims | NOT RUN |
| D27 | `autocad_sequence` of layout + title block + viewport | All three land in order; each step's own answer comes back; Ctrl+Z backs them out one at a time | NOT RUN |
| D28 | `autocad_sequence` with a bad argument in step 3 | Refused before step 1 runs; **the drawing is untouched** | NOT RUN |
| D29 | `autocad_sequence` with a step that fails at run time (a locked layer) | Steps 1-2 are in the drawing, that step reports the refusal, the rest are skipped, and the hint names the step | NOT RUN |
| D30 | `autocad_sequence` containing `autocad_save_drawing`, and one containing `autocad_run_lisp` | Both refused, naming the level; nothing ran. **This is the padlock ceiling (D-29) and must be re-run whenever a tool is added** | NOT RUN |
| D31 | After the whole set, `autocad_preview` and `autocad_check_standards` | The sheet looks right and the standard passes | NOT RUN |

## Group E - Geometry, annotation and 3D (AutoCAD 2027, this PC)

The 12 tools added on 2026-10-26 ([10](10-geometry-annotation-3d.md)). The
geometry and the layout arithmetic are covered offline (`tests/test_shapes.py`,
`test_dimension_run.py`, `test_annotate.py`, `test_solids.py` - 400 tests);
**every COM call below is NOT RUN.** Four of these methods were matched to
Autodesk's reference but have never been called from this server, and they are
marked.

**Set-up:** a scratch drawing in millimetres, Changes on, DIMSCALE set with
`autocad_drawing_setup(scale="1:10")`.

| Row | Do | Pass looks like | Result |
|---|---|---|---|
| E1 | `autocad_make_shape(shape="slot", settings={"length":120,"width":40})` then LIST it | **One** LWPOLYLINE, not a pile of arcs; measure it: 120 long, 40 wide, round both ends | NOT RUN |
| E2 | `shape="rounded_rectangle"` 2400 x 1200 r50 | One polyline, overall size exactly 2400 x 1200, corners truly tangent | NOT RUN |
| E3 | `shape="flange"` 200 OD, 8 holes, 160 PCD, bore 100, with `centreline_layer` | 11 circles; every hole centre 80 from the middle; the pitch circle on its own layer | NOT RUN |
| E4 | `shape="cone_development"` 200 to 100 over 150 | **Measure the two arcs.** Outer must be 628.3 (pi x 200), inner 314.2 (pi x 100). This is the one row that proves a flat pattern | NOT RUN |
| E5 | `shape="stair"` 14 risers at 175, going 280, both `view="section"` and `view="plan"` | Section climbs to 3920 x 2450; plan is 3920 x 1200 with 13 tread lines | NOT RUN |
| E6 | `shape="steel_section"` for i, c, l, t, shs, chs | Each outline is the right depth and width, corners square | NOT RUN |
| E7 | `shape="detail_bubble"` with a sheet, and `shape="revision_tag"` | **The text sits centred on its point, both ways** - this is the DXF 72/73/11 justification working | NOT RUN |
| E8 | `shape="scale_bar"` scale 1:50, length 100 | Bar 100 long on the paper; labels read 0 to 5000 | NOT RUN |
| E9 | `autocad_make_shape(..., coords="ucs")` on a 23 degree UCS | The shape comes out square to the UCS grid, not to the world | NOT RUN |
| E10 | `autocad_make_shape(..., dry_run=true)` | Operations come back, nothing is drawn | NOT RUN |
| E11 | `autocad_dimension_run` chain along 4 grid points, offset 500, `include_overall=true` | 4 dimensions; the three gaps on one line, the overall above; **each "measured" equals its "expected"** | NOT RUN |
| E12 | The same as `mode="baseline"` | Each dimension back to the first point, each on its own line stepped 500 clear | NOT RUN |
| E13 | `mode="ordinate"` with a datum | **AddDimOrdinate: never called from here before.** Ordinate dimensions with leaders, reading the distance from the datum | NOT RUN |
| E14 | `axis="aligned"` on a sloping run | The true length, text offset perpendicular to the run | NOT RUN |
| E15 | `autocad_add_centre_marks(layer_filter=..., extend=...)` | A cross on every circle, centre lines running past, all on the layer asked for; `min_radius` skips the small ones | NOT RUN |
| E16 | `autocad_add_multileader` with **three** arrow points | One MULTILEADER, three leader lines, one note. **AddLeader / AddLeaderLine: never called from here before** | NOT RUN |
| E17 | `autocad_add_multileader(block=...)` | The block is carried at the end of the leader | NOT RUN |
| E18 | `autocad_add_table` with a title, headers and 5 rows | A real TABLE object, editable, title and header rows filled, column widths as asked. **AddTable / SetText / SetColumnWidth: never called from here before** | NOT RUN |
| E19 | `autocad_extract_attributes` then `autocad_add_table` with those rows | The schedule appears as a table with one row per block | NOT RUN |
| E20 | `autocad_add_revision_cloud(handle=...)` with a margin | One polyline round the object, arcs bulging **outward**, even size, no stub arc | NOT RUN |
| E21 | The same on a boundary traced clockwise | Arcs still bulge outward, not inward | NOT RUN |
| E22 | `autocad_add_solid` box 2400 x 1200 x 200 at the origin | **The base sits on z=0**, not z=-100. Check with LIST | NOT RUN |
| E23 | `autocad_add_solid` for wedge, cylinder, cone, sphere, torus | Each the right size, base on z=0 where it has one | NOT RUN |
| E24 | `autocad_extrude_profile` on a closed polyline, height 200 | A 3D solid; the intermediate REGION is **gone**; the original polyline is **still there** | NOT RUN |
| E25 | The same with a taper | The sides draw in as it rises | NOT RUN |
| E26 | `autocad_extrude_profile` with `revolve_angle=360` and an axis | A solid of revolution. **AddRevolvedSolid: never called from here before** | NOT RUN |
| E27 | `autocad_extrude_profile` on curves with a gap in them | Refused in plain words, naming what to check; nothing left behind | NOT RUN |
| E28 | `autocad_solid_boolean` subtract: 4 cylinders out of a plate | Holes through the plate; the cylinders gone; **volume_after is less than volume_before** | NOT RUN |
| E29 | `autocad_solid_boolean` with a handle that is a line | Refused **before anything is consumed** - the other solids must all still be there | NOT RUN |
| E30 | `autocad_solid_boolean` subtract two solids that do not touch | The warning about the volume not changing appears | NOT RUN |
| E31 | `autocad_solid_properties` on that plate | Volume matches 2400x1200x200 less the holes; centroid sensible; bounding box right | NOT RUN |
| E32 | `autocad_draw_3d_path` with helix r100, 3 turns, rise 600 | One 3D polyline; starts at (100,0,0), ends at (100,0,600) | NOT RUN |
| E33 | `autocad_draw_3d_path` with points through a building | One 3D polyline following them | NOT RUN |
| E34 | `autocad_set_3d_view(direction="sw_iso", visual_style="hidden")` then `autocad_preview` | The model is shown from the south-west with hidden lines; **no padlock was needed** | NOT RUN |
| E35 | `autocad_set_3d_view(direction="top", visual_style="2dwireframe")` | Back to plan and normal drafting | NOT RUN |
| E36 | `autocad_batch_draw` with `bulges` on a polyline and `align` on a text | The arc is part of the polyline; the text is justified. These two are what every shape depends on | NOT RUN |

## Group B - AutoCAD 2025 / 2026 (.NET 8 build)

Rows B1-B19 = A1-A19 on AutoCAD 2025 and on 2026. **NO MACHINE.**

## Group C - AutoCAD 2021 to 2024 (.NET Framework 4.8 build)

Rows C1-C19 = A1-A19 on each of 2021, 2022, 2023, 2024. **NO MACHINE.** Look first at C1 and C3:
the .NET Framework build loads System.Text.Json and its helpers from the bundle folder (an
AssemblyResolve fallback), so a missing-DLL error would show there, in the add-in log.

## Server items not provable offline

| Row | Do | Pass looks like | Result |
|---|---|---|---|
| S1 | Make AutoCAD busy mid-batch (open a dialog during a large `autocad_batch_draw`) | `Outcome unknown...` and no duplicate geometry | NOT RUN |
| S2 | `autocad_check_standards` on a real project drawing with a rules file | Findings match a manual check of 5 random layers | NOT RUN |
| S3 | `autocad_extract_attributes` on the CCTV package (CAM blocks), CSV | One row per camera, tags as columns | NOT RUN |
