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
| Server tools | **107 tools**, every one gated by the plug-in; 5 resources, a tool search and **7 job prompts** | `pytest -m "not live"` green (1812 tests); `tools/check_structure.py` OK |
| Sheets, UCS, shop drawings | **14 tools, server 1.2.0** (2026-10-26): the UCS, layouts, page setup, title blocks, viewports, saved locations, drawing settings and styles, remap layers, tidy an import, `autocad_sequence`. All the arithmetic and planning is tested offline; **everything COM touches is NOT RUN** | [09](09-sheets-and-coordinates.md), D-27 / D-28 / D-29, [NEEDS-CHECKING group D](NEEDS-CHECKING.md) |
| Geometry, annotation, 3D | **12 tools, server 1.3.0** (2026-10-26): 24 named shapes, dimension runs, centre marks, multileaders, tables, revision clouds, solids, extrude / revolve, booleans, mass properties, 3D paths, 3D views. Plus polyline bulges and text justification in the batch. Geometry tested offline (402 tests); **everything COM touches is NOT RUN** | [10](10-geometry-annotation-3d.md), D-30 / D-31, [NEEDS-CHECKING group E](NEEDS-CHECKING.md) |
| Proving it in AutoCAD | **`tools/live_check.py`** (2026-10-26): one command measures 65 of the 90 live rows in a scratch drawing it makes itself and writes the results here. The other 25 need an eye or depend on the machine and say so. **Not yet run on a real AutoCAD** | `tools/README.md`, [NEEDS-CHECKING](NEEDS-CHECKING.md) header |
| Findability | **Measured, not assumed** (2026-10-26): every tool carries a `Use when` line, `autocad://tools` indexes them and `autocad://tools/find/{phrase}` searches them. 67 real phrases: 55 put the right tool first, all 67 in the top three | `tests/test_find_tool.py`, D-32 |
| The rest of 3D | **6 tools, server 1.6.0** (2026-10-26): oval primitives, sweep along a path, slice, clash detection, 3D move/rotate/mirror/array, materials, render. The plane arithmetic is tested offline; **everything COM touches is NOT RUN** | [NEEDS-CHECKING group F](NEEDS-CHECKING.md), D-33 |
| Plug-in (C#) | Ribbon, padlocks, banner, Bridge Status, Keep or Discard, 6 commands. Builds for net48 / net8 / net10 with 0 warnings | `dotnet build`; bridge tests green incl. real Python <-> C# |
| Plug-in live in AutoCAD | **2027: 18 rows PASS on 2026-10-26**, A21 fixed and PASS (D-21), 6 rows still NOT RUN. 2021-2026: no machine | [NEEDS-CHECKING](NEEDS-CHECKING.md) group A |
| Bundle and installer | `tools/build_plugin.py` -> `dist/HeronAutoCAD.bundle`; `tools/install_plugin.py` (refuses while AutoCAD runs) | `tests/test_plugin_bundle.py` |
| CI | Two jobs on Windows: Python (ruff, tests, structure) and plug-in (3 builds + bridge tests) | `.github/workflows/ci.yml` |
| Drawing packages | AHU-01, CCTV 42 sheets, pole enclosure: on this PC only. Their generator scripts were removed ([D-23](DECISIONS.md)) | `drawings/` |

## Next, in order

1. **Run NEEDS-CHECKING groups D, E and F** (90 rows) on AutoCAD 2027. **This is one command
   now, not a day of clicking** — with the Changes padlock on:

   ```bash
   .venv\Scripts\python.exe tools/live_check.py --group all --write
   ```

   It works in a scratch drawing it makes and closes itself, measures 65 of the 90 rows, and
   writes each result and its evidence straight into NEEDS-CHECKING.md. Read the FAIL list
   first: a FAIL there is a defect in a tool, not in the runner, until shown otherwise. The 25
   it cannot measure are written NOT RUN with the reason; `--list` names them.

   From group F, the newest and least proven, start with:
   - **F1** — a 400 x 200 oval duct must measure 400 x 200. If it comes out 800 x 400, the
     half-axis conversion in `tools/solids.py` is inverted.
   - **F5 / F11** — a slice's two halves must add up to the original, and a clash check with
     `create_solids=false` must leave the entity count unchanged.
   - **F15** — a 1000 tall column tipped 90 degrees about X must lie down to 100.

   From group E, five rows matter most:
   - **E4** — measure the two arcs of a cone development. Outer 628.3, inner 314.2. That one
     measurement proves every flat pattern the server will ever draw.
   - **E1 / E36** — a slot must come out as **one** polyline, not a pile of arcs, and a batch text
     must justify. Both rest on the DXF group codes added for the shape library (42, and 72/73/11).
   - **E22** — a box's base must sit on z=0, not half a height below it.
   - **E29** — a boolean with a bad handle must refuse **before** consuming anything.
   - **E13 / E16 / E18 / E26** — `AddDimOrdinate`, `AddLeader`/`AddLeaderLine`, `AddTable` and
     `AddRevolvedSolid` have never been called from this server. Their signatures came from
     Autodesk's reference, not from a run.
   And from group D, these four:
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
   **Do this with one command, not by hand:** with Changes on,
   `.venv\Scripts\python.exe tools/live_check.py --group all --write`. It measures 46 of the 67
   rows and writes the evidence into NEEDS-CHECKING itself. Read the FAIL list first - a FAIL
   there is a real defect in a tool, not in the runner, until you have shown otherwise.
2. Choose-which-AutoCAD when several are open ([ROADMAP](ROADMAP.md)).
3. Run the remaining 2027 group A rows (A8e, A15, A16, A19, A20); restart AutoCAD first so the
   double-click fix (D-20) is loaded. Live checks are driven with one server for several calls
   (`HERON_CONVERSATION_ID` keeps one chat id across scripts).
4. Tag `v1.6.0` once groups A, D, E and F pass.
5. Pick from [ROADMAP](ROADMAP.md) — `coords="ucs"` on the single-entity draw tools is the natural
   next step, now the transform and its tests exist; after that, hatch and mtext operations in
   `autocad_batch_draw`, which would give the furniture shapes real filled arrowheads.

## Before you stop

Update the table above, add decisions to [DECISIONS.md](DECISIONS.md), a line to
[CHANGELOG.md](../CHANGELOG.md), run the gates, commit and push.
