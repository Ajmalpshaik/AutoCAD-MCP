# Needs checking - what is built but not yet proven in a real AutoCAD

> A build is not a proof, and a passing offline test is not a proof. A row is **PASS** only after it
> was run in the named AutoCAD and gave the result in the last column. Four states, kept apart:
> **PASS**, **FAIL** (with what happened), **NOT RUN**, **NO MACHINE** (no PC with that version yet).
> Put the date and the AutoCAD version in the result.

**Set-up for every row:** build and install the plug-in (`tools/build_plugin.py`, close AutoCAD,
`tools/install_plugin.py`), start AutoCAD, open a scratch drawing, and connect Claude Code in this
folder.

## Group A - AutoCAD 2027 (this PC)

| Row | Do | Pass looks like | Result |
|---|---|---|---|
| A1 | Start AutoCAD | Tab **Heron**, panel **AI Bridge**, dark heron, four blue padlocks; command line shows nothing alarming; log file written | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): tab, panel, dark heron, four padlocks off |
| A2 | Ask Claude "check the AutoCAD connection" before pressing Heron | Status answers, with `"heron": {"connected": false, ...}` and the press-Heron sentence | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): after Disconnect, status returned only `heron: connected false` + press-Heron sentence, no drawing data |
| A3 | Press **Heron** | Icon lights; command line `Heron: connected...`; `%LOCALAPPDATA%\Heron\autocad\bridges\<pid>.json` exists | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): icon lit/dark follows each click; address file written and removed |
| A4 | "List the layers" | READING banner (blue) appears, then DONE; the layers come back; `Heron: List Layers. Done in ...` | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): reads accepted; begin/end logged |
| A5 | "Draw a line from 0,0 to 1000,0" with Changes **off** | Refused naming **Changes** and HERONCHANGES; nothing drawn; no banner | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): draw and LISP refused naming Changes; drawing still empty; audit `refused` |
| A6 | Click **Changes**, answer Yes, repeat A5 | Red padlock; CHANGING banner (amber); line drawn; one Ctrl+Z removes it | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): asks before turning on; CHANGING banner seen; one U removed the rectangle |
| A7 | Click **Changes** again | Off with no question | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): turned off with no question |
| A8 | Ask to Keep on, Changes on, draw a circle, click **Discard it** | Circle selected and zoomed before the box; after Discard it is gone; chat says `Discarded: nothing was kept.` | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): box with circle selected and zoomed; Keep kept it; Discard removed it |
| A9 | Same, click **Keep, and keep the rest...**, then draw twice more | No more boxes; ribbon reads **Keep: rest of job** (within 15 s) | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): after 'keep the rest', next two draws had no box (61 / 78 ms). Ribbon label not confirmed |
| A8b | Ask to Keep on: draw, Keep; then draw again and Discard | Only the second drawing goes; the first stays; the view returns to where it was | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): earlier kept circle stayed; VIEWSIZE 2080 before and after Discard (view went back) |
| A8c | Ask to Keep on: `autocad_batch_draw` with a new layer, Discard | Objects and the new layer both gone | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): batch objects and its new layer both gone after Discard. See A21 |
| A8d | Ask to Keep on: delete with `confirm=false` (preview) | No Keep box; nothing undone | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): `confirm=false` preview gave no box and undid nothing |
| A8e | Ask to Keep on: draw, then leave the mouse still | The Keep box appears at once, without moving the mouse | **Likely PASS** 2026-10-26: answered 8 s after the draw; not confirmed in words |
| A23 | Keep box: press Enter, and another time Esc | Enter keeps, Esc discards, arrows move between choices | **FAIL then PASS** 2026-10-26: first only the mouse worked and nothing showed the keyboard's place; now the box takes focus, a thick blue border follows the arrow keys, and Enter chose the bordered choice (Discard, removed the circle) |
| A10 | Open a second drawing in the same AutoCAD, make it active, ask to draw | Refused: active drawing changed from A to B; after "check status" the draw works | **FAIL then PASS** 2026-10-26, AutoCAD 2027 (26.0s): a fresh server let the first change through unchecked; fixed (D-19: units checked first); re-run refused before status and after switching, Drawing2 = millimetres, Drawing1 = inches |
| A11 | "Export to PDF" with Publish off, then on | Off: refused naming Publish. On: PDF written | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): on wrote an A3 PDF; off refused naming Publish, no file |
| A12 | "Run the LISP (+ 1 2)" with Admin off, then on | Off: refused naming Admin. On: 3 | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): on returned 3; off refused naming Admin |
| A13 | "Show me the drawing" | `autocad_preview` returns a PNG the chat can see; page setup unchanged (PAGESETUP) | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): PNG received by the chat. Note: portrait, drawing at the left edge (ROADMAP) |
| A14 | Press **Heron** to disconnect, ask anything | Icon dark; address file gone; every tool refused with the press-Heron sentence | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): icon dark, address file gone, tools refused with press-Heron |
| A15 | Two AutoCAD 2027 windows, connect only the second | Claude reaches the one COM attaches to; if that one is not connected, it is refused (no cross-talk) | **PASS** 2026-10-26: COM attached to the first (pid 16068); with the first connected it worked on CCTV_Package.dwg; with only the second (pid 40440) connected, every call was refused 'not connected' and nothing reached either AutoCAD. Limit: the second cannot be chosen yet (ROADMAP) |
| A16 | Second Claude session asks while the first is working | Second refused: in use by another chat; works after 3 quiet minutes | **PASS** 2026-10-26: second chat refused ('in use by another chat', no drawing data) at 1.4 min; let in after 3 quiet minutes (status + layers of CCTV_Package.dwg) |
| A17 | Switch workspace (WSCURRENT) | Heron tab comes back | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): tab still there after a workspace switch |
| A18 | Bridge Status in each state | Wording and buttons as in [06 §2](06-heron-plugin.md#2-bridge-status); Enter = Close | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): wording, padlock cards and versions correct; Disconnect works; Enter closed the window and stayed connected |
| A20 | Double-click a padlock | Acts once (the second click is ignored) | **FAIL then PASS** 2026-10-26: 0.86 s between clicks beat the 0.7 s window; with 1.5 s, a double-click on Ask to Keep acted once (no box) and rapid Admin clicks logged 'second click ... ignored' |
| A22 | `autocad_batch_draw` with the plug-in connected, then F2 | Only `Command:` prompts and `Heron: Batch Draw Geometry. Done in ...`; no LISP text, no coordinates | **PASS** 2026-10-26, AutoCAD 2027 (26.0s): 41 objects in 0.16-0.19 s (was 1.4 s over COM), history clean after two fixes (polyline list, helper name) |
| A21 | `autocad_batch_draw` with SECURELOAD on (default) | No security box | **FAIL then PASS** 2026-10-26, AutoCAD 2027 (26.0s): the old .lsp in %TEMP% raised 'Unsigned Executable File'; after D-21, 40 circles + a 150-point polyline drew in 1.4 s with no box. Command history fills with the LISP text (ROADMAP) |
| A24 | `autocad_add_label`, 13 labels, shape angled, on the roof pipe-support detail | Real LEADERs with arrows under MTEXT, on the text's layer | **FAIL then PASS** 2026-10-26: first drawn as splines without arrows (leader type 1); type 2 gives straight leaders with arrows under the text |
| A25 | `autocad_make_block` on a detail's parts, then insert and mirror copies | Parts become named blocks in place; copies insert; mirror makes the opposite hand | **PASS** 2026-10-26: roof pipe-support detail redrawn with 18 named blocks (anchor plan block x4, gussets mirrored), right-aligned label column, plan under elevation |
| A19 | Run a CCTV generator sheet (`python generators/cctv_run.py png 102`) with Changes on | Draws and plots as before the folder move | **PASS** 2026-10-26: CCTV_Package.dwg (23,303 objects) opened, sheet 102 plotted to PNG correctly. Found: generators started their server without the user's environment; now passed through |

## Group B - AutoCAD 2025 / 2026 (.NET 8 build)

Rows B1-B19 = A1-A19 on AutoCAD 2025 and on 2026. **NO MACHINE.**

## Group C - AutoCAD 2021 to 2024 (.NET Framework 4.8 build)

Rows C1-C19 = A1-A19 on each of 2021, 2022, 2023, 2024. **NO MACHINE.** Look first at C1 and C3:
the .NET Framework build loads System.Text.Json and its helpers from the bundle folder (an
AssemblyResolve fallback), so a missing-DLL error would show there, in the add-in log.

## Server items not provable offline

| Row | Do | Pass looks like | Result |
|---|---|---|---|
| S1 | Make AutoCAD busy mid-batch (open a dialog during a large `autocad_batch_draw`) | `Outcome unknown...` and no duplicate geometry | NOT RUN |
| S2 | `autocad_check_standards` on a real project drawing with a rules file | Findings match a manual check of 5 random layers | NOT RUN |
| S3 | `autocad_extract_attributes` on the CCTV package (CAM blocks), CSV | One row per camera, tags as columns | NOT RUN |
