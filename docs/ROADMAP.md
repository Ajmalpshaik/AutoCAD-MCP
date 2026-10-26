# Roadmap

Ideas and known gaps, **not started**. Move an item to [HANDOVER](HANDOVER.md) when work begins and
to [CHANGELOG](../CHANGELOG.md) when it lands. Proving what is built comes first:
[NEEDS-CHECKING](NEEDS-CHECKING.md).

## Plug-in

- [ ] A Companion page like Heron's in Revit (drawing, view, selection, activity list).
- [ ] Emergency stop: a ribbon button that refuses every job until pressed again.
- [ ] Sign the add-in DLLs, so AutoCAD's SECURELOAD never asks.
- [ ] An installer `.exe` / `.msi` for modellers (today: two Python scripts).
- [ ] Move tools into the plug-in one at a time where it pays off (speed, true transactions), keeping COM as the fallback.

## Found in the first live checks (2026-10-26)

- [ ] A batch still leaves one `Command:` prompt per piece in the history (about 27 for 41 objects).
  Harmless; fewer, larger pieces may be possible through the plug-in (the 600-character limit was
  measured for COM SendCommand).
- [ ] `autocad_preview`: the picture comes out portrait with the drawing at the left edge; fit and
  centre it, landscape when the drawing is wide.
- [ ] **Choose which AutoCAD** when several are open (like Heron's `revit_use_session`): today the server always takes the one COM hands it, usually the first started (A15).
- [ ] Remaining live rows: A9 ribbon label, A8e confirmation.
- [x] `autocad_list_blocks` listed blank names and lost changed dynamic copies (`*U` names): now
  counted by real name, blank names skipped, `dynamic` flag added (A28).
- [x] `autocad_insert_block` with a forward-slash .dwg path failed "Key not found": paths are now
  normalised to backslashes (A28).
- [x] "Object invoked has disconnected" (RPC_E_DISCONNECTED) is now treated as a dead pointer:
  re-dispatch and retry. The live export test no longer fails in the full suite.

## Server

- [x] Dynamic blocks: read and set properties (`autocad_get/set_dynamic_properties`). Authoring
  parameters and actions has no API; it stays a Block Editor job.
- [ ] The next Lee Mac ideas, in the order listed in [08](08-lee-mac-study.md).

- [ ] `autocad_batch_draw`: hatch, mtext and dimension operations.
- [ ] Draw an attribute schedule as an AutoCAD table (a CHANGE tool beside `autocad_extract_attributes`).
- [ ] Standards check against a reference DWG / DWS, not only a rules file.
- [ ] Read DXF / DWG files without AutoCAD (ezdxf, plus the ODA converter for DWG), read only.
- [ ] Paper-space layouts and viewports.
- [ ] Split long `autocad_run_lisp` expressions instead of failing silently.
- [ ] `send_command` / `run_lisp` that manage their own undo do not mark "write started", so a busy retry can still re-run them ([D-15](DECISIONS.md)).

## Repository

- [ ] Tag `v1.1.0` after NEEDS-CHECKING group A passes.
- [ ] Later: offer this repository to Heron AI as its AutoCAD adapter when Heron's capability registry is ready ([D-12](DECISIONS.md)).
