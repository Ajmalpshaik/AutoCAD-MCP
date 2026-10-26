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
| Plug-in live in AutoCAD | **Not run yet, on any version** | [NEEDS-CHECKING](NEEDS-CHECKING.md) group A |
| Bundle and installer | `tools/build_plugin.py` -> `dist/HeronAutoCAD.bundle`; `tools/install_plugin.py` (refuses while AutoCAD runs) | `tests/test_plugin_bundle.py` |
| CI | Two jobs on Windows: Python (ruff, tests, structure) and plug-in (3 builds + bridge tests) | `.github/workflows/ci.yml` |
| Drawing packages | AHU-01, CCTV 42 sheets, pole enclosure: on this PC only, not in git ([D-11](DECISIONS.md)) | `drawings/` |
| Enclosure detail | Fibre type and title-block fields still TBC | `generators/encl_detail.py` |

## Next, in order

1. **Live checks on AutoCAD 2027**, rows A1-A19 of [NEEDS-CHECKING](NEEDS-CHECKING.md), with the
   owner at the PC: close AutoCAD, `tools/install_plugin.py`, start AutoCAD, press Heron, then work
   down the rows. Record PASS / FAIL with the date.
2. Fix whatever A1-A19 finds (each fix with a test first).
3. Tag `v1.1.0` once group A passes.
4. Pick from [ROADMAP](ROADMAP.md).

## Before you stop

Update the table above, add decisions to [DECISIONS.md](DECISIONS.md), a line to
[CHANGELOG.md](../CHANGELOG.md), run the gates, commit and push.
