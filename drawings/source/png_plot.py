"""Plot extents or a window of model space to PNG through autocad-mcp run_lisp."""
import asyncio, json, os, sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import ahu_run

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")

def pt(x, y):
    return f"(vlax-make-variant (vlax-safearray-fill (vlax-make-safearray vlax-vbDouble '(0 . 1)) (list {x} {y})))"

async def plot(s, name, media, window=None, style="monochrome.ctb"):
    parts = ['(setq lay (vla-get-ActiveLayout (vla-get-ActiveDocument (vlax-get-acad-object))))',
             '(vla-put-ConfigName lay "PublishToWeb PNG.pc3")', '(vla-RefreshPlotDeviceInfo lay)',
             f'(vla-put-CanonicalMediaName lay "{media}")', '(vla-put-PlotRotation lay ac0degrees)',
             '(vla-put-UseStandardScale lay :vlax-true)', '(vla-put-StandardScale lay acScaleToFit)',
             '(vla-put-CenterPlot lay :vlax-true)', '(vla-put-PlotWithLineweights lay :vlax-true)',
             f'(vl-catch-all-apply (quote vla-put-StyleSheet) (list lay "{style}"))',
             '(vla-put-PlotWithPlotStyles lay :vlax-true)']
    if window:
        (x1, y1), (x2, y2) = window
        parts += [f'(vla-SetWindowToPlot lay {pt(x1, y1)} {pt(x2, y2)})', '(vla-put-PlotType lay acWindow)']
    else:
        parts += ['(vla-put-PlotType lay acExtents)']
    parts += ['(setvar "BACKGROUNDPLOT" 0)',
              f'(setq r (vl-catch-all-apply (quote vla-PlotToFile) (list (vla-get-Plot (vla-get-ActiveDocument (vlax-get-acad-object))) "{HERE}/{name}.png")))',
              '(if (vl-catch-all-error-p r) (vl-catch-all-error-message r) (list (vla-get-StyleSheet lay) r))']
    expr = "(progn " + " ".join(parts) + ")"
    t = json.loads(await ahu_run.call(s, "autocad_run_lisp", {"expression": expr}, quiet=True))
    print(name, t.get("result"), t.get("timed_out"))

async def main():
    jobs = json.loads(sys.argv[1])
    async with stdio_client(StdioServerParameters(command=ahu_run.SERVER, args=[])) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            for j in jobs:
                await plot(s, j["name"], j.get("media", "5K_(5120.00_x_2880.00_Pixels)"), j.get("window"), j.get("style", "monochrome.ctb"))

asyncio.run(main())
