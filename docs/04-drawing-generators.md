# 04 - Drawing generators

A generator is a set of Python scripts in [`generators/`](../generators/README.md) that builds a whole
drawing package and sends it to AutoCAD through this server over MCP stdio, the same way Claude
does. The scripts import each other by plain module name, so they all live in one folder.

Run every command **from the repository folder** with AutoCAD open:

```bash
python generators/cctv_run.py status
```

The server path and every output folder come from [`generators/paths.py`](../generators/paths.py).

## How a generator is built

| Piece | Job | AHU example | CCTV example |
|---|---|---|---|
| Drawing model | Collects lines, text, polylines in Python before anything is sent | `ahu_gen.Drawing` | `cctv_lib.View`, `Sheet` |
| Data | Every number, once. Sheets read from it | inside `ahu_gen.py`, `ahu_bms.py` | `cctv_data.py` (cameras, IDFs, ports, IPs, storage, UPS) |
| Sheets | One function per sheet | `ahu_iso.py`, `ahu_bms.py`, `ahu_extra1/2.py` | `cctv_plans.py`, `cctv_schem.py`, `cctv_power.py`, ... |
| Register | Which sheets exist and where they sit | `ahu_extra1.SPACING` | `cctv_sheets.REGISTRY` |
| Runner | Talks to the server: setup, draw, clear, save, plot | `ahu_run.py`, `sheet_run.py` | `cctv_run.py` |
| Preview | PNG without AutoCAD, pure Python | `preview.py` | `cctv_preview.py` |

Sheets sit **side by side in model space**, each in its own x-range, so one sheet can be cleared and
redrawn without touching the others.

## AHU-01 package (11 sheets, A1 @ 1:30)

Frames are 25230 wide at 25630 spacing: M-AHU-001 at x = -3200, 002 at x = 22430, then 003 to 011
from x = 48060.

| Command | Does |
|---|---|
| `python generators/ahu_run.py [setup draw post view]` | Sheet 1, GA and control schematic |
| `python generators/sheet_run.py MODULE clear XMIN XMAX draw` | Clear one x-range and draw a module's `build()` |
| `python generators/pdf_plot.py` | Plot sheets 2 to 4 to PDF (**runs on import**) |
| `python generators/pdf_plot2.py` | Plot sheets 5 to 11 to PDF (**runs on import**) |
| `python generators/png_plot.py` | Plot a window to PNG for checking (**runs on import**) |
| `python generators/preview.py out.png` | Pure-Python preview, no AutoCAD |

Output: `drawings/AHU/`. The runners check the active drawing is `AHU-01_GA_and_Control_Schematic.dwg`.

## CCTV package (42 sheets, MOI SSD Qatar)

Sample building B1+G+4+roof, office and retail, Doha; IP + PoE + VMS. Every sheet uses sheet factor
k = 100 (site plan k = 200), so one `LTSCALE = 25` works; text heights are paper millimetres.

| Command | Does |
|---|---|
| `python generators/cctv_run.py new` | Create `CCTV_Package.dwg` from acadiso.dwt and set it up |
| `python generators/cctv_run.py setup` | Layers, text style, dim style, system variables |
| `python generators/cctv_run.py draw all` or `draw 000 001 102` | Draw sheets |
| `python generators/cctv_run.py redraw 102` | Clear and draw again |
| `python generators/cctv_run.py pdf all` | Plot to `drawings/CCTV/PDF/` (A1) |
| `python generators/cctv_run.py png 102` | Plot to PNG for checking |
| `python generators/cctv_preview.py 102` | Pure-Python preview, no AutoCAD (`PREVIEW_DIR` sets the folder) |

MOI SSD values used: 120 days storage, UPS at least 1 h, hot standby, at most 9 cameras per screen,
identification 120 % / recognition 50 % / detection 10 % / monitoring 5 % of screen height,
number plate 50 %.

## CCTV pole enclosure detail (1 sheet)

Real site submission: 400 x 400 x 120 pole enclosure, PLANET IGTP-805AT media converter and MEAN WELL
NDR-75-48 PSU per camera, 13 A fused spur, fibre splice box. Type A = 1 camera, Type B = 2.

| Command | Does |
|---|---|
| `python generators/encl_run.py draw` | Draw into the **active** drawing, then Save As |
| `python generators/encl_run.py redraw` | Clear and draw again |
| `python generators/encl_run.py pdf` | Plot to `drawings/CCTV/ENCLOSURE/PDF/` |

**Open items:** the fibre type is marked TBC (single-mode was asked for, the site photos show aqua
OM3). Client, project and location in the title block are `TBC` at the top of `encl_detail.py`.

## Rules for any new generator

1. Data in one module; sheets never type a number the data module owns.
2. Batches through `autocad_batch_draw`; AutoLISP chunks under about 700 characters.
3. Generated text must never be empty, or batch handles misalign when filtered.
4. Every output path from `paths.py`.
5. Check every sheet from a PNG before calling it done.
6. Put a `if __name__ == "__main__":` guard on anything that talks to AutoCAD.
