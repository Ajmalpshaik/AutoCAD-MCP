# Decision log

> **Append-only.** A decision that is later reversed gets a **new** entry that supersedes the old one;
> the old one stays, so the reasoning is never lost. Number new entries one above the highest here.

---

## D-01 - Python server, AutoLISP for bulk work

**Decided:** 2026-08-25. **Status:** in force.
MCP must be served by an outside process, which AutoLISP cannot be. Python hosts the protocol and
typed single operations over COM; AutoLISP is generated for bulk creation and for what COM cannot
reach. Detail: [02](02-architecture.md#why-python-and-autolisp).

## D-02 - One COM worker thread, retry on busy for 10 s

**Decided:** 2026-08-25. **Status:** in force.
COM is apartment-threaded and AutoCAD rejects calls while busy. All COM work runs on one
`CoInitialize`d thread; `RPC_E_CALL_REJECTED` is retried for 10 s, then reported with "press Esc".

## D-03 - One tool call is one undo group; deletes need `confirm=true`

**Decided:** 2026-08-25. **Status:** in force.
Anything Claude does must be reversible with one Ctrl+Z, and nothing is deleted on a guess.

## D-04 - PDF export configures the layout, then plots with the path only

**Decided:** 2026-10-19. **Status:** in force.
The two-argument `PlotToFile(path, pc3)` fails on AutoCAD 2027. Set the layout to the pc3, extents,
fit and centre, plot with the path alone, restore the page setup. Pinned by `tests/test_export.py`.

## D-05 - Repository laid out in parts, like Heron AI

**Decided:** 2026-10-26, on Ajmal's instruction to "rearrange everything like Heron AI" without
changing Heron itself. **Status:** in force.
Folders: `src/autocad_mcp/` (server), `generators/` (was `drawings/source/`), `drawings/<PACKAGE>/`
(outputs only), `tools/` (was `scripts/`), `tests/`, `docs/`, `archive/`. Root carries README,
AGENTS, CONTRIBUTING, SECURITY, CHANGELOG, LICENSE, as Heron does. `src/` was **not** moved: the
editable install and three MCP configs point at it, and moving it means a reinstall
([05 §1](05-known-limits.md#1-reinstalling-while-the-server-runs)).
Heron AI was read for its structure only; nothing in it was changed.

## D-06 - Ruff checks the server, not the generators

**Decided:** 2026-10-26. **Status:** in force.
`generators/` and `archive/` are dense one-project drawing scripts with long data lines; they had 126
style findings and no functional ones. Ruff now excludes them (`pyproject.toml`) so CI guards the
server. Tidying the generators is on the [ROADMAP](ROADMAP.md).

## D-07 - Generator paths come from `generators/paths.py`

**Decided:** 2026-10-26. **Status:** in force.
Five scripts carried a typed `D:\06_Development\...` path. They now import `SERVER`, `AHU_OUT`,
`CCTV_OUT`, `ENCL_OUT` from `paths.py`, worked out from the file's own location, so the repository
runs from any folder or PC.

## D-08 - Revit enclosure experiment archived, not deleted

**Decided:** 2026-10-26. **Status:** in force.
`drawings/revit_encl/` sent raw C# to Revit through Heron's bridge pipe. Ajmal stopped that task on
2026-10-22 and said Heron must be used through its own capabilities. Kept in `archive/revit_encl/`
for reference; never build on it.

## D-09 - Private GitHub repository, generated drawings included

**Decided:** 2026-10-26. **Status:** in force.
`Ajmalpshaik/AutoCAD-MCP`, private. DWG, PDF and PNG outputs are committed (about 10 MB) so the
packages are kept with the code that made them. AutoCAD `.bak` / `.dwl` files and the `.venv` are not.
Visibility superseded by [D-10](#d-10---repository-made-public); keeping drawings in git superseded
by [D-11](#d-11---generated-drawings-are-not-kept-in-git).

## D-10 - Repository made public

**Decided:** 2026-10-26, on Ajmal's instruction "make it public". **Status:** in force. Supersedes the
*private* part of D-09.
Checked before switching: no keys, passwords or e-mail addresses in the files or history; the CCTV
package uses a sample client; the pole-enclosure sheet's client, location and consultant are still
`TBC`. **When those TBCs are filled with a real client's details, think before committing them here:
the repository is public.**

## D-11 - Generated drawings are not kept in git

**Decided:** 2026-10-26, on Ajmal's instruction ("why you keep drawings on this repo?? ... remove
this"). **Status:** in force. Supersedes the *drawings included* part of D-09.
The DWG, PDF, PNG and LISP output can be made again from `generators/`, it was about 10 MB against a
small code base, and the pole-enclosure sheet is real site work that should not be public. Everything
under `drawings/` except its README is ignored, and the files were **removed from the whole git history**
(rewritten and force-pushed the same day, while the repository was one day old with no other copies).
The files themselves stay on Ajmal's PC.
