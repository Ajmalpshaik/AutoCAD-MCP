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

- [ ] **`autocad_batch_draw` triggers AutoCAD's "Unsigned Executable File" warning** (SECURELOAD) because
  it loads a temporary `.lsp` from `%TEMP%`. Send the LISP without a file, or have the plug-in run it;
  never weaken the modeller's security settings ([NEEDS-CHECKING](NEEDS-CHECKING.md) A21).
- [ ] `autocad_preview`: the picture comes out portrait with the drawing at the left edge; fit and
  centre it, landscape when the drawing is wide.
- [ ] Remaining live rows: A8e, A9 ribbon label, A15, A16, A18 Enter, A19, A20.

## Server

- [ ] `autocad_batch_draw`: hatch, mtext and dimension operations.
- [ ] Draw an attribute schedule as an AutoCAD table (a CHANGE tool beside `autocad_extract_attributes`).
- [ ] Standards check against a reference DWG / DWS, not only a rules file.
- [ ] Read DXF / DWG files without AutoCAD (ezdxf, plus the ODA converter for DWG), read only.
- [ ] Paper-space layouts and viewports.
- [ ] Split long `autocad_run_lisp` expressions instead of failing silently.
- [ ] `send_command` / `run_lisp` that manage their own undo do not mark "write started", so a busy retry can still re-run them ([D-15](DECISIONS.md)).

## Generators

- [ ] `if __name__ == "__main__":` guards on `pdf_plot.py`, `pdf_plot2.py`, `png_plot.py`.
- [ ] Tidy the ruff findings and bring `generators/` back under ruff ([D-06](DECISIONS.md)).
- [ ] Merge `pdf_plot.py` and `pdf_plot2.py`; remove `only_s7.py`.
- [ ] Offline tests for `cctv_data.py` calculations.

## Repository

- [ ] Tag `v1.1.0` after NEEDS-CHECKING group A passes.
- [ ] Later: offer this repository to Heron AI as its AutoCAD adapter when Heron's capability registry is ready ([D-12](DECISIONS.md)).
