# Changelog

Newest first. Dates are when the change was made.

## 1.1.0 - 2026-10-26 - Heron AI for AutoCAD

- **Live checks on AutoCAD 2027:** 18 rows PASS. From them: units must be checked before any change
  (D-19); a double-click on a padlock counts once (D-20); "press Heron" is said before the units rule;
  `HERON_CONVERSATION_ID` for scripts. Batch drawing no longer loads a file, so AutoCAD's security box is gone (D-21), and its input goes
  through the plug-in with echo off: clean command history and about 8x faster (D-22).

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
