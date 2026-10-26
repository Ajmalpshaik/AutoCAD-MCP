"""Draw the CCTV pole-enclosure detail sheet (encl_detail.py) into the active AutoCAD drawing.

Usage:
  python encl_run.py draw      setup layers/styles + draw into the ACTIVE drawing, then Save As OUT_DWG
  python encl_run.py redraw    erase the sheet area and draw again, save
  python encl_run.py pdf       plot the sheet to PDF (A1)
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import cctv_lib
import cctv_run
import encl_detail
from paths import ENCL_OUT as OUT

OUT_DWG = os.path.join(OUT, "CCTV_Pole_Enclosure_Details.dwg")

# point the CCTV-package runner at this single sheet
cctv_run.cctv_sheets = encl_detail
cctv_run.OUT = OUT
cctv_run.LSP_DIR = os.path.join(OUT, "_lsp")
for lay in encl_detail.EXTRA_LAYERS:
    if lay[0] not in [x[0] for x in cctv_lib.LAYERS]:
        cctv_lib.LAYERS.append(lay)
NO = "DT-001"


async def main(cmd):
    params = StdioServerParameters(command=cctv_run.SERVER, args=[], env=dict(os.environ))
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            call, lisp = cctv_run.call, cctv_run.lisp
            st = json.loads(await call(s, "autocad_status", {}))
            print("active:", st["active_drawing"]["name"])
            if cmd == "draw":
                await call(s, "autocad_set_variable", {"name": "MEASUREMENT", "value": "1"})
                await cctv_run.setup(s)
                await cctv_run.draw_sheet(s, NO)
            elif cmd == "redraw":
                await cctv_run.clear_sheet(s, NO)
                await cctv_run.draw_sheet(s, NO)
            elif cmd == "pdf":
                print(await cctv_run.plot(s, NO, "pdf"))
                return
            await call(s, "autocad_zoom", {"mode": "extents"})
            os.makedirs(OUT, exist_ok=True)
            print(await call(s, "autocad_save_drawing", {"path": OUT_DWG}, quiet=False))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "draw"))
