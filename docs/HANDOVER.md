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
| Server tools | Every tool gated by the plug-in; 3 new READ tools (preview, standards, attributes); resources and prompts | `pytest -m "not live"` green; `tools/check_structure.py` OK |
| Plug-in (C#) | Ribbon, padlocks, banner, Bridge Status, Keep or Discard, 6 commands. Builds for net48 / net8 / net10 with 0 warnings | `dotnet build`; bridge tests green incl. real Python <-> C# |
| Plug-in live in AutoCAD | **2027: 18 rows PASS on 2026-10-26**, A21 fixed and PASS (D-21), 6 rows still NOT RUN. 2021-2026: no machine | [NEEDS-CHECKING](NEEDS-CHECKING.md) group A |
| Bundle and installer | `tools/build_plugin.py` -> `dist/HeronAutoCAD.bundle`; `tools/install_plugin.py` (refuses while AutoCAD runs) | `tests/test_plugin_bundle.py` |
| CI | Two jobs on Windows: Python (ruff, tests, structure) and plug-in (3 builds + bridge tests) | `.github/workflows/ci.yml` |
| Drawing packages | AHU-01, CCTV 42 sheets, pole enclosure: on this PC only. Their generator scripts were removed ([D-23](DECISIONS.md)) | `drawings/` |

## Next, in order

0. **2026-10-27: `autocad_batch_labels` built** (one call + one undo step for a label column,
   `arrow_scale`, `crossing` report); offline gates green. Live row A30 is NOT RUN: merge to main,
   restart the server, then draw a 15-label column. Why: a CCTV pole test sheet took ~120 tool calls,
   mostly one label / block / dimension at a time; batch blocks and dimensions are the next candidates.
1. Choose-which-AutoCAD when several are open ([ROADMAP](ROADMAP.md)).
2. Run the remaining 2027 rows (A8e, A15, A16, A19, A20); restart AutoCAD first so the
   double-click fix (D-20) is loaded. Live checks are driven with one server for several calls
   (`HERON_CONVERSATION_ID` keeps one chat id across scripts).
3. Tag `v1.1.0` once group A passes.
4. Pick from [ROADMAP](ROADMAP.md).

## Before you stop

Update the table above, add decisions to [DECISIONS.md](DECISIONS.md), a line to
[CHANGELOG.md](../CHANGELOG.md), run the gates, commit and push.
