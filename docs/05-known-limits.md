# 05 - Known limits and traps

Each one was found the hard way. The fix is written beside it.

## 1. Reinstalling while the server runs

**Never run `pip install -e .` (or `.[dev]`) while any `autocad-mcp` server is running.** The locked
`.venv\Scripts\autocad-mcp.exe` makes pip abort half-way: it deletes `_editable_impl_autocad_mcp.pth`
and leaves a `~utocad_mcp-1.0.0.dist-info` folder, so `import autocad_mcp` fails on the next start.

**Fix:** recreate the `.pth` in `.venv\Lib\site-packages\` (its content is the full path of the `src`
folder, backslashes, no newline) and rename the dist-info folder back. To add another package, install
it by name instead.

## 2. A code change is not live until restart

A server started before an edit keeps running the old code. Restart the Claude session (or
reconnect the MCP server) after changing anything in `src/`.

## 3. Long AutoLISP fails silently

`autocad_run_lisp` expressions near 3,600 characters fail with no error. Keep chunks under about
700 characters.

## 4. Two sessions on one AutoCAD

Two Claude sessions driving the same AutoCAD collide: one switching the active drawing breaks the
other's batch. Agree who drives first, and check the active drawing name before each batch.

## 5. PDF on AutoCAD 2027

`Plot.PlotToFile(path, "DWG To PDF.pc3")` raises a bare "Exception occurred" on 2027. Configure the
layout for the pc3 first, then plot with the path only. Fixed in `autocad_export` on 2026-10-19 and
pinned by `tests/test_export.py`. The same route works for `PublishToWeb PNG.pc3`.

## 6. Plot styles on this PC

There is **no `monochrome.ctb`**. Only the custom `TRG *.ctb` tables (`TRG MECH.CTB` and others).

## 7. AutoCAD LT

Not supported at any version: LT ships no COM Automation server ([SETUP](SETUP.md)).

## 8. Run as the same user level

COM cannot connect from a normal process to an AutoCAD running as Administrator. Run both the same way.

## 9. A broken `.venv` after moving PCs or users

A `.venv` built under another Windows user or folder will not start. Rebuild it:
`python -m venv .venv` then `.venv\Scripts\python.exe -m pip install -e ".[dev]"`, and check the
path in `.mcp.json`, `.codex/config.toml` and the Claude Desktop config.

## 10. Live scripts need Heron connected

With the plug-in installed, `tools/smoke_test.py` and `tests/test_live.py` go through the gate like
Claude does: press **Heron** and turn on **Changes** (and **Publish** for PDF
plots) first, or start the server with `--no-bridge` for developer runs.

## 11. COM is still open to other programs

The padlocks stop Heron; they do not stop another program that drives AutoCAD over COM.

## 12. Escape hatches can still be re-run when busy

`send_command` and `run_lisp` paths that manage their own undo do not mark "write started", so a busy
retry could repeat them ([D-15](DECISIONS.md)).

## 13. Proven live on AutoCAD 2027 only

The plug-in passed every live check on AutoCAD 2027 (2026-10-26). The 2021-2024 and 2025-2026
builds compile and pass their offline tests, but have not run in those AutoCADs
([NEEDS-CHECKING](NEEDS-CHECKING.md) groups B and C).

## 14. A read's undo pause is not yet proven live

Reads should leave no undo step: the plug-in turns undo recording off for the length of a Read job
([D-34](DECISIONS.md)). Until row A31 passes, a plug-in built before 2026-10-27, or a read that ran
while AutoCAD was mid-command (the pause waits 2 s for AutoCAD to be idle, then goes ahead without
it), can still leave steps: the U then undoes the look, not the change. Press U again, or check the
object count.

## 15. A visual style cannot be read back

`autocad_set_3d_view` types the VSCURRENT command ([D-35](DECISIONS.md)); there is no VSCURRENT
system variable and COM has no visual style on a model viewport, so the tool cannot report which
style is current. `autocad_preview` shows it. The answers for 'shaded with edges' and 'shades of
gray' are from the prompt's capital letters and are not yet proven (row E34): if one is not taken,
the tool cancels the command and says so in `not_set`.

## 16. A scale is written as on the sheet

`scale=10` is refused: it could be 1:10 or 10:1 ([D-36](DECISIONS.md)). Write `'1:10'`, or `'10:1'`
for an enlargement. A plain ratio of 1 or less (0.02 for 1:50) still works.

## 17. Ordinates measure from the UCS origin

`autocad_dimension_run(mode="ordinate")` needs the datum at the UCS origin, because that is where
AutoCAD measures ordinates from ([D-37](DECISIONS.md)). A datum elsewhere is refused with the
`autocad_set_ucs(mode="origin", ...)` call that moves it.
