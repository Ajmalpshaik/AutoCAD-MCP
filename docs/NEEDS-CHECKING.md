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
| A1 | Start AutoCAD | Tab **Heron**, panel **AI Bridge**, dark heron, four blue padlocks; command line shows nothing alarming; log file written | NOT RUN |
| A2 | Ask Claude "check the AutoCAD connection" before pressing Heron | Status answers, with `"heron": {"connected": false, ...}` and the press-Heron sentence | NOT RUN |
| A3 | Press **Heron** | Icon lights; command line `Heron: connected...`; `%LOCALAPPDATA%\Heron\autocad\bridges\<pid>.json` exists | NOT RUN |
| A4 | "List the layers" | READING banner (blue) appears, then DONE; the layers come back; `Heron: List Layers. Done in ...` | NOT RUN |
| A5 | "Draw a line from 0,0 to 1000,0" with Changes **off** | Refused naming **Changes** and HERONCHANGES; nothing drawn; no banner | NOT RUN |
| A6 | Click **Changes**, answer Yes, repeat A5 | Red padlock; CHANGING banner (amber); line drawn; one Ctrl+Z removes it | NOT RUN |
| A7 | Click **Changes** again | Off with no question | NOT RUN |
| A8 | Ask to Keep on, Changes on, draw a circle, click **Discard it** | Circle selected and zoomed before the box; after Discard it is gone; chat says `Discarded: nothing was kept.` | NOT RUN |
| A9 | Same, click **Keep, and keep the rest...**, then draw twice more | No more boxes; ribbon reads **Keep: rest of job** (within 15 s) | NOT RUN |
| A10 | Open a second drawing in the same AutoCAD, make it active, ask to draw | Refused: active drawing changed from A to B; after "check status" the draw works | NOT RUN |
| A11 | "Export to PDF" with Publish off, then on | Off: refused naming Publish. On: PDF written | NOT RUN |
| A12 | "Run the LISP (+ 1 2)" with Admin off, then on | Off: refused naming Admin. On: 3 | NOT RUN |
| A13 | "Show me the drawing" | `autocad_preview` returns a PNG the chat can see; page setup unchanged (PAGESETUP) | NOT RUN |
| A14 | Press **Heron** to disconnect, ask anything | Icon dark; address file gone; every tool refused with the press-Heron sentence | NOT RUN |
| A15 | Two AutoCAD 2027 windows, connect only the second | Claude reaches the one COM attaches to; if that one is not connected, it is refused (no cross-talk) | NOT RUN |
| A16 | Second Claude session asks while the first is working | Second refused: in use by another chat; works after 3 quiet minutes | NOT RUN |
| A17 | Switch workspace (WSCURRENT) | Heron tab comes back | NOT RUN |
| A18 | Bridge Status in each state | Wording and buttons as in [06 §2](06-heron-plugin.md#2-bridge-status); Enter = Close | NOT RUN |
| A19 | Run a CCTV generator sheet (`python generators/cctv_run.py png 102`) with Changes on | Draws and plots as before the folder move | NOT RUN |

## Group B - AutoCAD 2025 / 2026 (.NET 8 build)

Rows B1-B19 = A1-A19 on AutoCAD 2025 and on 2026. **NO MACHINE.**

## Group C - AutoCAD 2021 to 2024 (.NET Framework 4.8 build)

Rows C1-C19 = A1-A19 on each of 2021, 2022, 2023, 2024. **NO MACHINE.**

## Server items not provable offline

| Row | Do | Pass looks like | Result |
|---|---|---|---|
| S1 | Make AutoCAD busy mid-batch (open a dialog during a large `autocad_batch_draw`) | `Outcome unknown...` and no duplicate geometry | NOT RUN |
| S2 | `autocad_check_standards` on a real project drawing with a rules file | Findings match a manual check of 5 random layers | NOT RUN |
| S3 | `autocad_extract_attributes` on the CCTV package (CAM blocks), CSV | One row per camera, tags as columns | NOT RUN |
