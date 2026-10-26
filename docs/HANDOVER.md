# Session handover

> **What this file is:** where the last session stopped and what comes next. It is a work note. Where
> it disagrees with the code, the tests or [DECISIONS.md](DECISIONS.md), those win.

## If you are the owner, starting work - say this

> **"Read docs/HANDOVER.md in AutoCAD-MCP and carry on."**

## Where things stand - 2026-10-26

| Area | State | Evidence |
|---|---|---|
| Server, 50 tools | Working | `--list-tools`; offline tests pass 2026-10-26; used live on AutoCAD 2027 for all three packages (2026-10-19 to 22) |
| PDF export on 2027 | Fixed 2026-10-19 | `tests/test_export.py` |
| AHU-01 package, 11 sheets | Done | `drawings/AHU/` |
| CCTV package, 42 sheets | Done | `drawings/CCTV/PDF/` |
| CCTV pole enclosure detail | Drawn; **fibre type and title-block fields TBC** | `drawings/CCTV/ENCLOSURE/PDF/` |
| Drawings | On this PC only, not in git ([D-11](DECISIONS.md)); paths in the table above are local | |
| Git and GitHub | **Public** repo `Ajmalpshaik/AutoCAD-MCP` since 2026-10-26, branch `main` ([D-10](DECISIONS.md)) | |
| Documentation | Full set written 2026-10-26 | [docs/README.md](README.md) |
| CI | ruff + offline tests on `windows-latest`, **green** since the repository went public on 2026-10-26 (while private it was blocked by the account's Actions billing) | `.github/workflows/ci.yml` |

## What changed last session (2026-10-26)

- Repository created and pushed; folders re-arranged into parts ([D-05](DECISIONS.md)).
- Generator paths made relative ([D-07](DECISIONS.md)). The generators were compiled and their
  imports checked after the move; **no package has been redrawn in AutoCAD since the move.** Run one
  `cctv_run.py png 102` (or similar) to confirm before relying on them.

## Next, in order

1. Confirm a generator still draws after the move (above).
2. Enclosure detail: settle the fibre type (single-mode or OM3) and fill the title-block TBCs.
3. Pick from [ROADMAP.md](ROADMAP.md).

## Before you stop

Update the table above, add any decision to [DECISIONS.md](DECISIONS.md), add a line to
[CHANGELOG.md](../CHANGELOG.md), run the gates, commit and push.
