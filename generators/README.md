# generators - drawing-package scripts

Python scripts that build whole drawing packages and send them to AutoCAD through the server. They
import each other by module name, so they stay together in this one folder. How to run each package:
[docs/04-drawing-generators.md](../docs/04-drawing-generators.md).

| File | Package | Job |
|---|---|---|
| `paths.py` | all | Server exe and every output folder, from this file's location |
| `ahu_gen.py` | AHU-01 | `Drawing` model, sheet 1 (GA + control schematic) |
| `ahu_iso.py` | AHU-01 | Sheet 2, isometric with hidden-line removal |
| `ahu_bms.py` | AHU-01 | Sheets 3 (P&ID) and 4 (BMS); shared table / sheet helpers |
| `ahu_extra1.py` | AHU-01 | Sheets 5 to 7 |
| `ahu_extra2.py` | AHU-01 | Sheets 8 to 11 |
| `ahu_run.py` | AHU-01 | Runner for sheet 1; `call()` helper used by the others |
| `sheet_run.py` | AHU-01 | Clear an x-range and draw any module's `build()` |
| `only_s7.py` | AHU-01 | One-off: sheet 7 duct details only, for `sheet_run.py` |
| `pdf_plot.py`, `pdf_plot2.py` | AHU-01 | Plot sheets 2-4 and 5-11 to PDF. **Run on import** |
| `png_plot.py` | AHU-01 | Plot to PNG for checking. **Runs on import** |
| `preview.py` | AHU-01 | Pure-Python PNG preview, no AutoCAD |
| `cctv_lib.py` | CCTV | `View`, `Sheet`, title strip, symbols |
| `cctv_data.py` | CCTV | **Single source of truth**: 109 cameras, IDFs, switches, ports, IPs, cable lengths, storage and UPS |
| `cctv_plans.py` | CCTV | Site and floor layouts (100-107) |
| `cctv_general.py` | CCTV | Cover, legend, notes, design criteria, calculations, schedules |
| `cctv_schem.py` | CCTV | Riser, topology, fibre, IP/VLAN, head-end, video wall (200-205) |
| `cctv_power.py` | CCTV | SLD, UPS, earthing, PoE (210-213) |
| `cctv_intf.py` | CCTV | Interfaces, lift / ANPR, cause and effect, field cabinet (215-218) |
| `cctv_rooms.py` | CCTV | Control room, MDF / IDF, racks (300-302) |
| `cctv_details.py` | CCTV | Installation details (400-407); `place()` picks the detail scale |
| `cctv_sheets.py` | CCTV | `REGISTRY` of the 42 sheets and their positions |
| `cctv_run.py` | CCTV | Runner: new, setup, draw, clear, redraw, save, pdf, png |
| `cctv_preview.py` | CCTV | Pure-Python PNG preview, no AutoCAD |
| `encl_detail.py` | Enclosure | The pole-enclosure sheet (reuses `cctv_lib`) |
| `encl_run.py` | Enclosure | Runner: draw, redraw, pdf |

**Check a script with `python -m py_compile FILE`, never by importing it** - three of them plot as soon
as they are imported. Never type a drive path: add it to `paths.py`.

These files are excluded from ruff ([D-06](../docs/DECISIONS.md)).
