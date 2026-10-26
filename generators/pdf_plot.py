"""Save AHU-01 DWG and plot each sheet window to an A1 PDF through autocad-mcp."""
import asyncio, json, os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import ahu_run
from paths import AHU_OUT


def pt(x, y):
    return f"(vlax-make-variant (vlax-safearray-fill (vlax-make-safearray vlax-vbDouble '(0 . 1)) (list {x} {y})))"

OUT = AHU_OUT.replace("\\", "/")
SHEETS = [("AHU-01_M-AHU-002_Isometric", (22430, -11000), (47660, 6820)),
          ("AHU-01_M-AHU-003_PID", (48060, -11000), (73290, 6820)),
          ("AHU-01_M-AHU-004_BMS_Details", (73690, -11000), (98920, 6820))]

async def main():
    async with stdio_client(StdioServerParameters(command=ahu_run.SERVER, args=[])) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            st = json.loads(await ahu_run.call(s, "autocad_status", {}, quiet=True))
            assert st["active_drawing"]["name"] == "AHU-01_GA_and_Control_Schematic.dwg", st["active_drawing"]["name"]
            await ahu_run.call(s, "autocad_zoom", {"mode": "extents"}, quiet=True)
            print(await ahu_run.call(s, "autocad_save_drawing", {}, quiet=True))
            for name, (x1, y1), (x2, y2) in SHEETS:
                expr = ("(progn (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)) lay (vla-get-ActiveLayout doc)) "
                        '(vla-put-ConfigName lay "DWG To PDF.pc3") (vla-RefreshPlotDeviceInfo lay) '
                        '(vla-put-CanonicalMediaName lay "ISO_full_bleed_A1_(841.00_x_594.00_MM)") '
                        "(vla-put-PaperUnits lay acMillimeters) (vla-put-PlotRotation lay ac0degrees) "
                        f"(vla-SetWindowToPlot lay {pt(x1, y1)} {pt(x2, y2)}) (vla-put-PlotType lay acWindow) "
                        "(vla-put-UseStandardScale lay :vlax-true) (vla-put-StandardScale lay acScaleToFit) "
                        "(vla-put-CenterPlot lay :vlax-true) (vla-put-PlotWithLineweights lay :vlax-true) "
                        '(setvar "BACKGROUNDPLOT" 0) '
                        f'(setq r (vl-catch-all-apply (quote vla-PlotToFile) (list (vla-get-Plot doc) "{OUT}/{name}.pdf"))) '
                        "(if (vl-catch-all-error-p r) (vl-catch-all-error-message r) r))")
                t = json.loads(await ahu_run.call(s, "autocad_run_lisp", {"expression": expr}, quiet=True))
                p = f"{OUT}/{name}.pdf"
                print(name, t.get("result"), os.path.getsize(p) if os.path.exists(p) else "MISSING")
            print(await ahu_run.call(s, "autocad_save_drawing", {}, quiet=True))

asyncio.run(main())
