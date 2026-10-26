# Session handover

> **What this file is:** where the last session stopped and what comes next. It is a work note. Where
> it disagrees with the code, the tests, [NEEDS-CHECKING](NEEDS-CHECKING.md) or
> [DECISIONS.md](DECISIONS.md), those win.

## If you are the owner, starting work - say this

> **"Read docs/HANDOVER.md in Heron-AutoCAD and carry on."**

## Where things stand - 2026-10-26

| Area | State | Evidence |
|---|---|---|
| Name and repository | **Heron AI for AutoCAD**, public, `Ajmalpshaik/Heron-AutoCAD` | [D-12](DECISIONS.md) |
| Server tools | **89 tools**, every one gated by the plug-in; resources and prompts | `pytest -m "not live"` green; `tools/check_structure.py` OK |
| Sheets, UCS, shop drawings | **14 new tools, server 1.2.0** (2026-10-26): the UCS, layouts, page setup, title blocks, viewports, saved locations, drawing settings and styles, remap layers, tidy an import, `autocad_sequence`. All the arithmetic and planning is tested offline; **everything COM touches is NOT RUN** | [09](09-sheets-and-coordinates.md), D-27 / D-28 / D-29, [NEEDS-CHECKING group D](NEEDS-CHECKING.md) |
| Plug-in (C#) | Ribbon, padlocks, banner, Bridge Status, Keep or Discard, 6 commands. Builds for net48 / net8 / net10 with 0 warnings | `dotnet build`; bridge tests green incl. real Python <-> C# |
| Plug-in live in AutoCAD | **2027: 18 rows PASS on 2026-10-26**, A21 fixed and PASS (D-21), 6 rows still NOT RUN. 2021-2026: no machine | [NEEDS-CHECKING](NEEDS-CHECKING.md) group A |
| Bundle and installer | `tools/build_plugin.py` -> `dist/HeronAutoCAD.bundle`; `tools/install_plugin.py` (refuses while AutoCAD runs) | `tests/test_plugin_bundle.py` |
| CI | Two jobs on Windows: Python (ruff, tests, structure) and plug-in (3 builds + bridge tests) | `.github/workflows/ci.yml` |
| Drawing packages | AHU-01, CCTV 42 sheets, pole enclosure: on this PC only. Their generator scripts were removed ([D-23](DECISIONS.md)) | `drawings/` |

## Next, in order

1. **Run NEEDS-CHECKING group D** (31 rows) on AutoCAD 2027. These 14 tools have never touched a
   real AutoCAD, and four rows matter more than the rest:
   - **D13** — measure a known 10 m wall on the plot of a 1:100 viewport. It must be 100 mm. This is
     the one thing that proves the viewport maths and the `CustomScale` pin.
   - **D23** — after `autocad_create_styles`, check `DIMSCALE` and `DIMTXT` with SETVAR. The
     drawing's own DIM variables must be back where they were.
   - **D30** — `autocad_sequence` containing `autocad_save_drawing`, and one containing
     `autocad_run_lisp`. Both must be refused. This is the padlock ceiling (D-29) and it must be
     re-run every time a tool is added.
   - **D4 / D15** — the UCS rows: a rotated UCS is the whole reason D-27 exists, and it has only
     been proved by arithmetic so far.
   Fix what fails before building anything else on top.
2. Choose-which-AutoCAD when several are open ([ROADMAP](ROADMAP.md)).
3. Run the remaining 2027 group A rows (A8e, A15, A16, A19, A20); restart AutoCAD first so the
   double-click fix (D-20) is loaded. Live checks are driven with one server for several calls
   (`HERON_CONVERSATION_ID` keeps one chat id across scripts).
4. Tag `v1.2.0` once groups A and D pass.
5. Pick from [ROADMAP](ROADMAP.md) — `coords="ucs"` on the single-entity draw tools is the natural
   next step, now the transform and its tests exist.

## Before you stop

Update the table above, add decisions to [DECISIONS.md](DECISIONS.md), a line to
[CHANGELOG.md](../CHANGELOG.md), run the gates, commit and push.
