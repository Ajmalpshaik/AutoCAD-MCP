"""Draw the CCTV drawing package into AutoCAD through the autocad-mcp server.

Usage:
  python cctv_run.py status
  python cctv_run.py new                 create CCTV_Package.dwg (acadiso.dwt) + setup
  python cctv_run.py setup               layers, text style, dim style, system variables
  python cctv_run.py draw all | NO ...   draw sheets (e.g. draw 000 001 102)
  python cctv_run.py clear NO ...        erase everything inside those sheet frames
  python cctv_run.py redraw NO ...       clear + draw
  python cctv_run.py save
  python cctv_run.py pdf all | NO ...    plot sheets to drawings/CCTV/PDF/*.pdf (A1)
  python cctv_run.py png NO ...          plot sheets to PNG for checking
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import cctv_lib
import cctv_sheets

SERVER = r"D:\06_Development\09_Autocad MCP\Autocad MCP\.venv\Scripts\autocad-mcp.exe"
OUT = r"D:\06_Development\09_Autocad MCP\Autocad MCP\drawings\CCTV"
DWG = "CCTV_Package.dwg"
LSP_DIR = os.path.join(OUT, "_lsp")
CTB = os.environ.get("CCTV_CTB", "")  # e.g. "monochrome.ctb" if available


async def call(s, tool, args, quiet=True):
    res = await s.call_tool(tool, args)
    text = res.content[0].text if res.content else ""
    if text.startswith("Error") or not quiet:
        print(f"[{tool}] {text[:500]}")
    return text


async def lisp(s, expr):
    t = await call(s, "autocad_run_lisp", {"expression": expr})
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        return {"result": t}


def lpath(p):
    return p.replace("\\", "/")


async def ensure_active(s):
    st = json.loads(await call(s, "autocad_status", {}))
    name = st.get("active_drawing", {}).get("name")
    if name != DWG:
        t = await call(s, "autocad_switch_drawing", {"name": DWG})
        st = json.loads(await call(s, "autocad_status", {}))
        name = st.get("active_drawing", {}).get("name")
        if name != DWG:
            raise SystemExit(f"Active drawing is {name!r}, expected {DWG}. Open it first (python cctv_run.py new).")
    return st


# ------------------------------------------------------------------ setup
async def setup(s):
    for name, value in (("INSUNITS", "4"), ("LTSCALE", "25"), ("PSLTSCALE", "0"), ("LWDISPLAY", "1"),
                        ("FILLMODE", "1"), ("PDMODE", "0"), ("TEXTFILL", "1"), ("MIRRTEXT", "0")):
        await call(s, "autocad_set_variable", {"name": name, "value": value})
    for name, aci, lt, lw in cctv_lib.LAYERS:
        args = {"name": name, "color": aci, "lineweight": lw}
        if lt:
            args["linetype"] = lt
        await call(s, "autocad_create_layer", args)
    print(await lisp(s, '(progn (vl-load-com) (setq st (vla-item (vla-get-textstyles (vla-get-ActiveDocument '
                        '(vlax-get-acad-object))) "Standard")) (vla-setfont st "Arial" :vlax-false :vlax-false 0 34) '
                        '(setvar "TEXTSTYLE" "Standard") "style-ok")'))
    dimvars = " ".join(f'(setvar "{k}" {v})' for k, v in (
        ("DIMSCALE", 100), ("DIMTXT", 2.2), ("DIMASZ", 2.0), ("DIMEXO", 1.5), ("DIMEXE", 1.5), ("DIMGAP", 1.0),
        ("DIMDEC", 0), ("DIMTAD", 1), ("DIMTIH", 0), ("DIMTOH", 0), ("DIMLUNIT", 2), ("DIMZIN", 8), ("DIMTSZ", 0),
        ("DIMCLRD", 2), ("DIMCLRE", 2), ("DIMCLRT", 7), ("DIMATFIT", 3), ("DIMTMOVE", 1)))
    print(await lisp(s, f'(progn {dimvars} (if (tblsearch "DIMSTYLE" "CCTV") (command "_.-DIMSTYLE" "_S" "CCTV" "_Y") '
                        f'(command "_.-DIMSTYLE" "_S" "CCTV")) (getvar "DIMSTYLE"))'))
    print("setup done")


# ------------------------------------------------------------------ drawing
def write_quads_lsp(no, d):
    os.makedirs(LSP_DIR, exist_ok=True)
    path = os.path.join(LSP_DIR, f"solids_{no}.lsp")

    with open(path, "w", encoding="ascii") as fh:
        fh.write("(progn\n")
        for lay, a, b, c, e in d.quads:
            q = " ".join(f"'({code} {pt_[0]:.3f} {pt_[1]:.3f} 0.0)" for code, pt_ in ((10, a), (11, b), (12, c), (13, e)))
            fh.write(f"(entmake (list '(0 . \"SOLID\") '(8 . \"{lay}\") {q}))\n")
        fh.write(f'(princ "solids-{no}-ok"))\n')
    return path


async def draw_sheet(s, no):
    t0 = time.time()
    d, sh = cctv_sheets.build_one(no)
    ops = d.ops
    for op in ops:
        if op["type"] == "text":
            assert op["text"].strip(), "empty text op"
    want = bool(d.hatches)
    handles = []
    created = failed = 0
    CH = 4000
    for i in range(0, len(ops), CH):
        chunk = ops[i:i + CH]
        out = json.loads(await call(s, "autocad_batch_draw", {"operations": chunk, "return_handles": want}))
        created += out.get("created", 0)
        failed += out.get("failed", 0)
        if want:
            hs = out.get("handles", [])
            assert len(hs) == len(chunk), (len(hs), len(chunk))
            handles += hs
    ok_h = 0
    for h in d.hatches:
        t = await call(s, "autocad_add_hatch", {"boundary_handles": [handles[h["op"]]], "pattern": h["pattern"],
                                               "scale": h["scale"], "angle": h["angle"], "layer": h["layer"],
                                               "associative": True})
        ok_h += not t.startswith("Error")
    ok_d = 0
    if d.dims:
        await call(s, "autocad_set_variable", {"name": "DIMSCALE", "value": str(sh.k)})
        for dm in d.dims:
            args = {k: v for k, v in dm.items() if k != "k"}
            t = await call(s, "autocad_add_dimension", args)
            ok_d += not t.startswith("Error")
    for m in d.mtexts:
        await call(s, "autocad_add_mtext", m)
    if d.quads:
        path = write_quads_lsp(no, d)
        r = await lisp(s, f'(load "{lpath(path)}")')
        if "ok" not in str(r.get("result", "")) and not r.get("result"):
            print("  solids load result:", r)
    print(f"{no}: ops {created}/{len(ops)} (failed {failed}), hatches {ok_h}/{len(d.hatches)}, dims {ok_d}/{len(d.dims)}, "
          f"solids {len(d.quads)}, {time.time() - t0:.1f}s")


def clear_expr(xa, xb):
    return ('(progn (vl-load-com) (setq n 0 ms (vla-get-ModelSpace (vla-get-ActiveDocument (vlax-get-acad-object)))) '
            '(vlax-for o ms (if (not (vl-catch-all-error-p (vl-catch-all-apply (quote vla-GetBoundingBox) '
            '(list o (quote mn) (quote mx))))) (progn (setq x (car (vlax-safearray->list mn))) '
            f'(if (and (>= x {xa}) (< x {xb})) (progn (vla-Delete o) (setq n (1+ n))))))) n)')


async def clear_sheet(s, no):
    pos = cctv_sheets.positions()
    k = cctv_sheets.sheet_k(no)
    xa = pos[no] - 1.0
    xb = pos[no] + cctv_lib.A1W * k + 1.0
    r = await lisp(s, clear_expr(xa, xb))
    print(no, "cleared", r.get("result"))


# ------------------------------------------------------------------ plotting
def pt(x, y):
    return f"(vlax-make-variant (vlax-safearray-fill (vlax-make-safearray vlax-vbDouble '(0 . 1)) (list {x} {y})))"


async def plot(s, no, kind="pdf"):
    pos = cctv_sheets.positions()
    k = cctv_sheets.sheet_k(no)
    x1, y1, x2, y2 = pos[no], 0.0, pos[no] + cctv_lib.A1W * k, cctv_lib.A1H * k
    title = cctv_sheets.BY_NO[no][5].replace(" ", "_").replace("&", "and").replace("/", "-").replace(",", "")
    folder = os.path.join(OUT, "PDF" if kind == "pdf" else "PNG")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"ELV-CCTV-{no}_{title}.{kind}")
    if kind == "pdf":
        dev, media = "DWG To PDF.pc3", "ISO_full_bleed_A1_(841.00_x_594.00_MM)"
    else:
        dev, media = "PublishToWeb PNG.pc3", "5K_(5120.00_x_2880.00_Pixels)"
    media_expr = f'(vla-put-CanonicalMediaName lay "{media}") ' if media else ""
    ctb = f'(vla-put-StyleSheet lay "{CTB}") (vla-put-PlotWithPlotStyles lay :vlax-true) ' if CTB else ""
    expr = ("(progn (vl-load-com) (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)) lay (vla-get-ActiveLayout doc)) "
            f'(vla-put-ConfigName lay "{dev}") (vla-RefreshPlotDeviceInfo lay) {media_expr}'
            f"{'(vla-put-PaperUnits lay acMillimeters) ' if kind == 'pdf' else ''}(vla-put-PlotRotation lay ac0degrees) "
            f"(vla-SetWindowToPlot lay {pt(x1, y1)} {pt(x2, y2)}) (vla-put-PlotType lay acWindow) "
            "(vla-put-UseStandardScale lay :vlax-true) (vla-put-StandardScale lay acScaleToFit) "
            f"(vla-put-CenterPlot lay :vlax-true) (vla-put-PlotWithLineweights lay :vlax-true) {ctb}"
            '(setvar "BACKGROUNDPLOT" 0) '
            f'(setq r (vl-catch-all-apply (quote vla-PlotToFile) (list (vla-get-Plot doc) "{lpath(path)}"))) '
            "(if (vl-catch-all-error-p r) (vl-catch-all-error-message r) r))")
    r = await lisp(s, expr)
    size = os.path.getsize(path) if os.path.exists(path) else "MISSING"
    print(no, kind, r.get("result"), size)
    return path


# ------------------------------------------------------------------ main
def sheet_list(args):
    if not args or args == ["all"]:
        return [r[0] for r in cctv_sheets.REGISTRY]
    return args


async def main(argv):
    cmd, rest = argv[0], argv[1:]
    params = StdioServerParameters(command=SERVER, args=[])
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            if cmd == "status":
                print(await call(s, "autocad_status", {}, quiet=False))
                return
            if cmd == "new":
                print(await call(s, "autocad_create_drawing", {"template": "acadiso.dwt"}, quiet=False))
                os.makedirs(OUT, exist_ok=True)
                print(await call(s, "autocad_save_drawing", {"path": os.path.join(OUT, DWG)}, quiet=False))
                await setup(s)
                print(await call(s, "autocad_save_drawing", {}, quiet=False))
                return
            await ensure_active(s)
            if cmd == "setup":
                await setup(s)
            elif cmd in ("draw", "redraw", "clear"):
                for no in sheet_list(rest):
                    if cmd in ("redraw", "clear"):
                        await clear_sheet(s, no)
                    if cmd in ("draw", "redraw"):
                        await draw_sheet(s, no)
                await call(s, "autocad_zoom", {"mode": "extents"})
                print(await call(s, "autocad_save_drawing", {}, quiet=False))
            elif cmd == "save":
                print(await call(s, "autocad_save_drawing", {}, quiet=False))
            elif cmd in ("pdf", "png"):
                for no in sheet_list(rest):
                    await plot(s, no, cmd)
            st = json.loads(await call(s, "autocad_status", {}))
            print("active", st["active_drawing"]["name"], "entities", st["active_drawing"].get("model_space_entities"))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:] or ["status"]))
