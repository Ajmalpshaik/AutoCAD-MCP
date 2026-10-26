"""Draw a sheet module (build() -> Drawing) into AHU-01 through autocad-mcp.

Usage: python sheet_run.py MODULE [clear XMIN XMAX] [draw]
  clear XMIN XMAX - erase entities whose bounding-box min X lies in [XMIN, XMAX]
"""

import asyncio
import importlib
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import ahu_run

DWG = "AHU-01_GA_and_Control_Schematic.dwg"


def clear_expr(xa, xb):
    return ('(progn (vl-load-com) (setq n 0 ms (vla-get-ModelSpace (vla-get-ActiveDocument (vlax-get-acad-object)))) '
            '(vlax-for o ms (if (not (vl-catch-all-error-p (vl-catch-all-apply (quote vla-GetBoundingBox) '
            '(list o (quote mn) (quote mx))))) (progn (setq x (car (vlax-safearray->list mn))) '
            f'(if (and (>= x {xa}) (<= x {xb})) (progn (vla-Delete o) (setq n (1+ n))))))) n)')


async def main(argv):
    mod = importlib.import_module(argv[0])
    rest = argv[1:]
    params = StdioServerParameters(command=ahu_run.SERVER, args=[])
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            st = json.loads(await ahu_run.call(s, "autocad_status", {}, quiet=True))
            if st["active_drawing"]["name"] != DWG:
                print("switching from", st["active_drawing"]["name"])
                await ahu_run.call(s, "autocad_switch_drawing", {"name": DWG})
            if "clear" in rest:
                i = rest.index("clear")
                xa, xb = float(rest[i + 1]), float(rest[i + 2])
                t = json.loads(await ahu_run.call(s, "autocad_run_lisp", {"expression": clear_expr(xa, xb)}, quiet=True))
                print("cleared", t.get("result"))
            if "draw" in rest:
                d = mod.build()
                ops = d.ops
                assert all(op.get("type") != "text" or op["text"].strip() for op in ops), "empty text op"
                want = bool(d.hatches)
                out = json.loads(await ahu_run.call(s, "autocad_batch_draw", {"operations": ops, "return_handles": want}, quiet=True))
                print({k: out.get(k) for k in ("created", "failed", "requested", "completed")})
                if want:
                    handles = out.get("handles", [])
                    assert len(handles) == len(ops), (len(handles), len(ops))
                    ok = 0
                    for h in d.hatches:
                        t = await ahu_run.call(s, "autocad_add_hatch", {"boundary_handles": [handles[h["op"]]],
                                               "pattern": h["pattern"], "scale": h["scale"], "angle": h["angle"],
                                               "layer": h["layer"], "associative": True}, quiet=True)
                        ok += not t.startswith("Error")
                    print("hatches", ok, "/", len(d.hatches))
                ok = 0
                for dm in d.dims:
                    t = await ahu_run.call(s, "autocad_add_dimension", dm, quiet=True)
                    ok += not t.startswith("Error")
                print("dims", ok, "/", len(d.dims))
                for m in d.mtexts:
                    await ahu_run.call(s, "autocad_add_mtext", m, quiet=True)
                stmts = [f'(_s "{l}" {ahu_run.pt(a)} {ahu_run.pt(b)} {ahu_run.pt(c)})' for l, a, b, c in d.solids]
                stmts += [f'(_d "{l}" {x} {y})' for l, x, y in d.dots]
                for expr in ahu_run.lisp_chunks(stmts, limit=700):
                    t = json.loads(await ahu_run.call(s, "autocad_run_lisp", {"expression": expr}, quiet=True))
                    if t.get("timed_out"):
                        print("LISP chunk timed out")
            st = json.loads(await ahu_run.call(s, "autocad_status", {}, quiet=True))
            print("active", st["active_drawing"]["name"], "entities", st["active_drawing"]["model_space_entities"])


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
