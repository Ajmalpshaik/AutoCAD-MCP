# drawings - generated output (local only)

Everything here is produced by a script in [`generators/`](../generators/README.md). **Do not edit it
by hand**: change the generator and run it again, or the next run overwrites your edit.

**None of it is in git.** This README is the only tracked file in the folder ([D-11](../docs/DECISIONS.md)).
The drawings stay on the PC that made them; on a fresh clone the folders below fill up when you run
the generators.

| Folder | Package | Made by |
|---|---|---|
| `AHU/` | AHU-01: DWG + 11 A1 PDFs (M-AHU-001 to 011) | `ahu_*.py`, `sheet_run.py`, `pdf_plot*.py` |
| `CCTV/` | CCTV package: `CCTV_Package.dwg` | `cctv_run.py` |
| `CCTV/PDF/` | The 42 A1 PDFs (ELV-CCTV-000 to 503) | `cctv_run.py pdf all` |
| `CCTV/PNG/` | AutoCAD PNG plots used for checking | `cctv_run.py png ...` |
| `CCTV/preview/` | Pure-Python previews, no AutoCAD | `cctv_preview.py` |
| `CCTV/_lsp/` | AutoLISP written for solid fills, one per sheet | `cctv_run.py` |
| `CCTV/ENCLOSURE/` | Pole enclosure detail DWG, PDF and its LISP | `encl_run.py` |

Ignored by `drawings/*` with `!drawings/README.md` in [.gitignore](../.gitignore).
