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
small code base, and the pole-enclosure sheet is real site work that should not be public. The whole
`drawings/` folder is ignored (its README too, since 2026-10-26: an empty-looking folder on GitHub
helped nobody), and the files were **removed from the whole git history**
(rewritten and force-pushed the same day, while the repository was one day old with no other copies).
The files themselves stay on Ajmal's PC.

## D-12 - Heron AI for AutoCAD: same family, separate repository

**Decided:** 2026-10-26, with Ajmal ("Heron AI for AutoCAD", repository renamed `Heron-AutoCAD`).
**Status:** in force.
Heron AI's own decisions defer every non-Revit platform "until Revit works properly", and an AutoCAD
plug-in needs its own C# builds, so it lives here, separate. It carries Heron's name, ribbon, padlocks,
banner and wording so a modeller sees one product. When Heron's capability registry is ready, this
repository is offered as its AutoCAD adapter. Heron AI itself is not changed (its icon PNGs were
copied once, read only).

## D-13 - AutoCAD 2021 to 2027, three builds

**Decided:** 2026-10-26, Ajmal chose "2021 to 2027". **Status:** in force.
`net48` for 2021-2024 (R24), `net8.0-windows` for 2025-2026 (R25), `net10.0-windows` for 2027 (R26),
against Autodesk's `AutoCAD.NET` NuGet packages 24.0.0 / 25.0.1 / 26.0.0, in one `HeronAutoCAD.bundle`.
Only 2027 is on this PC: the other versions stay NO MACHINE in [NEEDS-CHECKING](NEEDS-CHECKING.md)
until someone runs them; the docs never claim them as working before that.

## D-14 - The plug-in guards, COM draws

**Decided:** 2026-10-26, Ajmal chose this over rewriting every tool in C#. **Status:** in force.
The plug-in owns connection, padlocks, banner and Keep or Discard; the Python server keeps its COM
tools and asks the plug-in `begin` / `end` / `ask_keep` around every call, from one place
(`tool_errors` -> `core/gate.py`). Tools can move into the plug-in later, one at a time.
Known limit: COM stays reachable by other programs; the guard binds Heron, not the whole PC.

## D-15 - A write AutoCAD interrupted is never re-run

**Decided:** 2026-10-26. **Status:** in force.
The busy-retry loop re-ran a whole tool. Once `undo_mark` has started a write, a busy signal now
raises `OutcomeUnknown` ("read the drawing back before retrying") instead, so nothing is drawn twice.
Gap: `send_command` / `run_lisp` paths that manage their own undo do not mark the write; on the
[ROADMAP](ROADMAP.md).

## D-16 - A broken padlock file means padlocks off, banner on

**Decided:** 2026-10-26. **Status:** in force.
An unreadable `heron-autocad.config` turns every padlock off (fail closed) but keeps the activity
banner on, because the banner is what shows the modeller that Heron is working.

## D-22 - Batch input goes through the plug-in with echo off

**Decided:** 2026-10-26, from the live F2 check. **Status:** in force.
Sent over COM, every batch piece was echoed into the command history. The plug-in now takes the
pieces (`send_quiet`) and types them with `SendStringToExecute(..., echoCommand: false)`. It accepts
them only inside this chat's running CHANGE / PUBLISH / ADMIN job, so it adds no new way in: the
padlock check at `begin` already covered the job. Without the plug-in (or an older one) the server
falls back to COM SendCommand. Each piece also returns nothing printable (`(princ)`). Side effect:
batches run inside AutoCAD and are about 8x faster (0.17 s against 1.4 s for 41 objects).

## D-21 - Batch drawing sends expressions; it never loads a file

**Decided:** 2026-10-26, from live check A21. **Status:** in force.
Loading the batch `.lsp` from `%TEMP%` made AutoCAD's SECURELOAD ask "Unsigned Executable File" on
every batch. The batch is now sent as short expressions (under 600 characters each, `build_chunks`),
like typed input, so no file is loaded. Rejected: adding `%TEMP%` to TRUSTEDPATHS or setting SECURELOAD
to 0 (weakens the modeller's security), writing the file into the trusted plug-in folder (generated
code in a trusted place), and reading the file back with `eval` (sidesteps the security check rather
than respecting it). The old error text that advised setting SECURELOAD to 0 is gone.

## D-20 - A double-click on a ribbon switch counts once

**Decided:** 2026-10-26, from the first live checks. **Status:** in force (built; live row A20 NOT RUN).
The live log showed padlocks flipping on and straight back off within 0.4 s: modellers double-click.
A second click on the same switch within 0.7 s is ignored (`RepeatClickFilter`).

## D-19 - Units are checked before anything is changed in a drawing

**Decided:** 2026-10-26, on Ajmal's instruction during the live checks: *"Whenever you are in one
drawing for the first time, at that time you have to understand the unit."* **Status:** in force.
A CHANGE, PUBLISH or ADMIN call is refused until `autocad_status` (or `autocad_create_drawing`) has run
on that very drawing in this server; switching or opening a drawing does not count, and reading does
not count. The live check showed why: Drawing1 was in inches, Drawing2 in millimetres.
Replaces the looser D-17 re-arming rule.

## D-18 - Discard goes back to an UNDO mark, and only on a clear answer

**Decided:** 2026-10-26, after the final review. **Status:** in force. Supersedes the "UNDO 1" design.
`UNDO 1` undid the plug-in's own zoom, missed layers a batch made, fired on delete previews that wrote
nothing, and fired when the pipe broke. Now: the plug-in says at `begin` whether it will ask; only then
the server puts `UNDO _Mark` down before the work; it asks only when the call really wrote (a write
counter in `core/connection.py`); Discard is `UNDO _Back`, then the created handles must be gone; a
failed question keeps the change and says so; UNDO off (UNDOCTL) means "cannot discard", said plainly.
The Keep box closes itself as Discard after 9 minutes, before the server's 10, and a question the
plug-in gave up on can never pop up later (`OneShotWork`).

## D-17 - Status always answers; resources go through the gate

**Decided:** 2026-10-26. **Status:** in force.
`autocad_status` always answers with `"heron": {connected, message}`, so a chat can always tell the
modeller how to connect. While AutoCAD is not connected it returns only that block, never the
drawing's name, path or contents (changed after the final review); under `--no-bridge` it says
Heron is off. MCP resources call the matching gated tools,
so a resource read is refused and audited exactly like a tool call.
