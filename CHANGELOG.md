# Changelog

Newest first. Dates are when the change was made.

## 2026-10-26 - Repository and documentation

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
