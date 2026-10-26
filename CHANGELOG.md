# Changelog

Newest first. Dates are when the change was made.

## 1.2.0 - 2026-10-26 - Sheets, coordinates and shop drawings

Server only; the plug-in is unchanged at 1.1.0. 14 new tools, 89 in all. Everything COM touches is
**NOT RUN**: see [NEEDS-CHECKING group D](docs/NEEDS-CHECKING.md). Detail:
[docs/09](docs/09-sheets-and-coordinates.md).

- **The UCS, at last.** Every coordinate here is a world coordinate and the modeller's are not, so
  `autocad_status` now reports the drawing's UCS and warns in plain words when it is not the world
  one; `autocad_get_ucs`, `autocad_set_ucs` and `autocad_convert_points` (AutoLISP's `trans`) make
  it workable; and `autocad_batch_draw` takes `coords="ucs"`, converting every point and angle
  before anything is sent — a rectangle square to a turned grid comes out turned. A tilted UCS is
  refused for a flat request rather than guessed ([D-27](docs/DECISIONS.md)).
- **Sheets.** `autocad_create_layout`, `autocad_page_setup` (one sheet or all of them),
  `autocad_place_title_block` (one sheet or all of them, with per-sheet attributes) and
  `autocad_add_viewport`. The viewport's model window is worked out to the viewport's own
  proportions, so 1:50 comes out 1:50; leave the scale out and the largest standard scale that fits
  is chosen; `twist` / `align_to_ucs` makes a rotated plan read upright; and viewports lock by
  default, because an unlocked one gets scrolled and the scale on the title block stops being true.
  Frame to ISO 5457 (20 mm binding edge, 10 elsewhere, title block bottom-right).
- **One location, used everywhere.** `autocad_save_view` and `autocad_list_views` name an area once;
  `autocad_export` gained `area` (`layout`, `window`, `view`, ...) and `scale`, and
  `autocad_add_viewport` takes the same `view_name` — so the area plotted and the area in the
  viewport are the same area.
- **Drawing settings.** `autocad_drawing_setup` takes the scale once and sets DIMSCALE, the
  annotation scale and LTSCALE from it, plus units, precision, snaps, point style and limits;
  `autocad_create_styles` makes text and dimension styles, putting the drawing's own DIM variables
  back afterwards. Both write only from a fixed list in code, which is why they need Changes and not
  Admin ([D-28](docs/DECISIONS.md)), and both report every old value beside its new one.
- **An import into a shop drawing.** `autocad_remap_layers` puts everything on the right layers and
  makes those layers properly (rules match the old layer name *or* the block name, the type, the
  colour or the text; `preset="ifc"` is a starting point, `rules_path` takes an office standard);
  `autocad_tidy_entities` clears the per-object colour / linetype / lineweight overrides that make a
  layer change look like it did nothing, flattens Z, moves geometry off layer 0 and deletes the
  zero-length leftovers. Both default to `dry_run=true`.
- **`autocad_sequence`:** AutoLISP's `progn` as a tool. Several tools in one call, every step's
  arguments checked against that tool's own schema before the first one runs. It refuses Publish and
  Admin steps and a sequence inside a sequence, so it can never spend more than the Changes padlock
  ([D-29](docs/DECISIONS.md)); a test asserts that against every registered Publish and Admin tool
  by name.
- Drafting rules 9-15 added to [docs/07](docs/07-drafting-rules.md) and to the server's own
  instructions, so every AI that connects follows them.
- 286 more offline tests (`tests/test_coords.py`, `test_sheets.py`, `test_settings.py`,
  `test_convert.py`, `test_sequence.py`): all the UCS arithmetic, the sheet arithmetic, the
  plain-words-to-system-variables mapping, the layer and tidy plans, and the sequence's ceiling.

## 1.1.0 - 2026-10-26 - Heron AI for AutoCAD

- The whole Lee Mac study built (D-26): 16 more tools (attributes, numbering, text count / clean /
  replace / align, polyline info, field labels, connected runs, segment labels, place along, place
  from CSV, break at blocks, import from drawing, layouts) and 6 add-ons; 75 tools in all. Live A29.
- Take-off tools from the Lee Mac study (ideas only, our own code, D-26): `autocad_count_blocks`,
  `autocad_total_length`, `autocad_get_dynamic_properties`, `autocad_set_dynamic_properties`.
- Fixes from live check A28: `autocad_list_blocks` counts dynamic copies by real name and skips
  blank names; `.dwg` paths with forward slashes insert; a disconnected COM pointer is retried.
- Drafting rules built in: server instructions + `draw_detail` prompt + docs/07 (D-25).
- New `autocad_make_block`: parts become named blocks in place (D-24). Labels can hang right-aligned.
- New `autocad_add_label`: MTEXT + LEADER in Ajmal's TLD style (L or angled), or a MULTILEADER;
  arrows and dimensions now take DIMSCALE (D-24).

- Removed the `generators/` folder (AHU, CCTV, pole-enclosure scripts); the drawings stay on the PC,
  the scripts in git history at `a443df4` ([D-23](docs/DECISIONS.md)).

- **Live checks on AutoCAD 2027:** 18 rows PASS. From them: units must be checked before any change
  (D-19); a double-click on a padlock counts once (D-20); "press Heron" is said before the units rule;
  `HERON_CONVERSATION_ID` for scripts. Batch drawing no longer loads a file, so AutoCAD's security box is gone (D-21), and its input goes
  through the plug-in with echo off: clean command history and about 8x faster (D-22). The Keep box
  works from the keyboard (focus, blue border, Enter, Esc), and a double-click within 1.5 s counts once.

- **Renamed Heron AI for AutoCAD** ([D-12](docs/DECISIONS.md)); repository `Ajmalpshaik/Heron-AutoCAD`.
- **New plug-in** `autocad/`: ribbon tab Heron / AI Bridge, connect button (lit / dark heron),
  Changes, Publish, Admin and Ask to Keep padlocks, Bridge Status window, READING / CHANGING / DONE /
  STOPPED banner, Keep or Discard, commands `HERON*`. Builds for AutoCAD 2021-2027 ([D-13](docs/DECISIONS.md)).
  **Not yet run live** ([NEEDS-CHECKING](docs/NEEDS-CHECKING.md)).
- **Every tool is gated** by the plug-in: risk level per tool, padlocks, one chat at a time,
  wrong-drawing guard, Keep or Discard, audit log ([D-14](docs/DECISIONS.md)).
- A write AutoCAD interrupts is never re-run: "outcome unknown" instead ([D-15](docs/DECISIONS.md)).
- Created objects are read back by handle (`verified`).
- New tools: `autocad_preview` (PNG back to the AI), `autocad_check_standards`,
  `autocad_extract_attributes`. New resources `autocad://drawing/{status,layers,blocks,styles}` and
  prompts `check_standards`, `draw_from_spec`. New start options `--read-only`, `--no-bridge`.
- `tools/build_plugin.py`, `tools/install_plugin.py`, `tools/check_structure.py`; CI builds the
  plug-in three ways and runs the bridge tests.
- `pyproject.toml` now says `mcp>=2.0` (the code needs 2.x).

## 2026-10-26 - Repository and documentation

- Made the repository public ([D-10](docs/DECISIONS.md)).
- Took the generated drawings out of git, including from all past commits; they stay on the PC only
  ([D-11](docs/DECISIONS.md)).

- Put the project under git and pushed it to a private GitHub repository, `Ajmalpshaik/AutoCAD-MCP`.
- Re-arranged the folders into parts, the way Heron AI is laid out ([D-05](docs/DECISIONS.md)):
  `drawings/source/` -> `generators/`, the AHU outputs -> `drawings/AHU/`, `scripts/` -> `tools/`,
  the stopped Revit enclosure experiment -> `archive/revit_encl/`.
- Generators no longer carry a typed `D:\...` path; all folders come from `generators/paths.py`.
- Wrote the documentation set: AGENTS, CONTRIBUTING, SECURITY, a README per folder, and `docs/`
  (index, project map, overview, architecture, tools reference, generators, known limits, decisions,
  handover, roadmap).
- Added GitHub CI (ruff + offline tests on Windows), issue and pull-request templates.
- Fixed `.codex/config.toml`, which still pointed at the old `D:\Ajmal\AutoCAD APP\...` folder.

## 2026-10-22 - CCTV pole enclosure detail

- `generators/encl_detail.py` and `encl_run.py`: A1 installation detail of the 400x400x120 pole
  enclosure, Type A (1 camera) and Type B (2 cameras). Fibre type still TBC.

## 2026-10-21 - CCTV drawing package

- 42-sheet CCTV package for a sample B1+G+4 building to MOI SSD (Qatar) rules, `generators/cctv_*.py`.

## 2026-10-19 - Local setup repaired, PDF export fixed

- Rebuilt the broken `.venv`; pointed `.mcp.json` at it.
- `autocad_export` PDF works on AutoCAD 2027: configure the layout for the pc3, then plot with the
  path only. Accepts `paper_size` (`A3`, `A1 portrait`). Pinned by `tests/test_export.py`.
- AHU-01 11-sheet package generated, `generators/ahu_*.py`.

## 1.0.0 - 2026-08-25

- First version: 50 tools, COM worker thread, AutoLISP batch drawing, offline and live tests.
