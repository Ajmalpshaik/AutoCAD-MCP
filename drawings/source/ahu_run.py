"""Draw AHU-01 into the active AutoCAD drawing through the autocad-mcp server.

Usage: python ahu_run.py [phase ...]   phases: setup draw post view (default: all)
"""

import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import ahu_gen

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = r"D:\06_Development\09_Autocad MCP\Autocad MCP\.venv\Scripts\autocad-mcp.exe"
HANDLES = os.path.join(HERE, "handles.json")


async def call(session, tool, args, quiet=False):
    res = await session.call_tool(tool, args)
    text = res.content[0].text if res.content else ""
    if text.startswith("Error") or not quiet:
        print(f"[{tool}] {text[:400]}")
    return text


def lisp_chunks(stmts, limit=700):
    chunk, size = [], 0
    for s in stmts:
        if size + len(s) > limit and chunk:
            yield "(progn " + " ".join(chunk) + " T)"
            chunk, size = [], 0
        chunk.append(s)
        size += len(s) + 1
    if chunk:
        yield "(progn " + " ".join(chunk) + " T)"


def pt(p):
    return f"'({p[0]} {p[1]} 0.0)"


async def main(phases):
    d = ahu_gen.build()
    params = StdioServerParameters(command=SERVER, args=[])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as s:
            await s.initialize()

            if "setup" in phases:
                for name, value in (("INSUNITS", "4"), ("LTSCALE", "15"), ("LWDISPLAY", "1"),
                                    ("FILLMODE", "1"), ("PDMODE", "0")):
                    await call(s, "autocad_set_variable", {"name": name, "value": value}, quiet=True)
                for name, aci, lt, lw in ahu_gen.LAYERS:
                    args = {"name": name, "color": aci, "lineweight": lw}
                    if lt:
                        args["linetype"] = lt
                    await call(s, "autocad_create_layer", args, quiet=True)
                dimvars = " ".join(f'(setvar "{k}" {v})' for k, v in (
                    ("DIMSCALE", 30), ("DIMTXT", 2.5), ("DIMASZ", 2.0), ("DIMEXO", 1.5), ("DIMEXE", 1.5),
                    ("DIMGAP", 1.0), ("DIMDEC", 0), ("DIMTAD", 1), ("DIMTIH", 0), ("DIMTOH", 0),
                    ("DIMLUNIT", 2), ("DIMZIN", 8), ("DIMTSZ", 0), ("DIMCLRD", 2), ("DIMCLRE", 2),
                    ("DIMCLRT", 7), ("DIMATFIT", 3), ("DIMTMOVE", 1)))
                await call(s, "autocad_run_lisp", {"expression":
                    f'(progn {dimvars} (if (tblsearch "DIMSTYLE" "AHU-30") '
                    f'(command "_.-DIMSTYLE" "_R" "AHU-30") (command "_.-DIMSTYLE" "_S" "AHU-30")) '
                    f'(getvar "DIMSTYLE"))'})
                await call(s, "autocad_run_lisp", {"expression":
                    "(progn (defun _s (l a b c) (entmake (list '(0 . \"SOLID\") (cons 8 l) (cons 10 a) "
                    "(cons 11 b) (cons 12 c) (cons 13 c)))) (defun _d (l x y) (entmake (list "
                    "'(0 . \"LWPOLYLINE\") '(100 . \"AcDbEntity\") (cons 8 l) '(100 . \"AcDbPolyline\") "
                    "'(90 . 2) '(70 . 1) '(43 . 14.0) (list 10 (- x 7.0) y) '(42 . 1.0) "
                    "(list 10 (+ x 7.0) y) '(42 . 1.0)))) \"helpers-ok\")"})

            if "draw" in phases:
                out = await call(s, "autocad_batch_draw", {"operations": d.ops, "return_handles": True}, quiet=True)
                res = json.loads(out)
                print({k: res.get(k) for k in ("created", "failed", "requested", "completed", "elapsed_seconds")})
                with open(HANDLES, "w") as fh:
                    json.dump(res.get("handles", []), fh)

            if "post" in phases:
                with open(HANDLES) as fh:
                    handles = json.load(fh)
                assert len(handles) == len(d.ops), (len(handles), len(d.ops))
                ok = 0
                for h in d.hatches:
                    t = await call(s, "autocad_add_hatch", {"boundary_handles": [handles[h["op"]]],
                                   "pattern": h["pattern"], "scale": h["scale"], "angle": h["angle"],
                                   "layer": h["layer"], "associative": True}, quiet=True)
                    ok += not t.startswith("Error")
                print("hatches ok", ok, "/", len(d.hatches))
                ok = 0
                for dm in d.dims:
                    t = await call(s, "autocad_add_dimension", dm, quiet=True)
                    ok += not t.startswith("Error")
                print("dims ok", ok, "/", len(d.dims))
                for m in d.mtexts:
                    await call(s, "autocad_add_mtext", m, quiet=True)
                stmts = [f'(_s "{l}" {pt(a)} {pt(b)} {pt(c)})' for l, a, b, c in d.solids]
                stmts += [f'(_d "{l}" {x} {y})' for l, x, y in d.dots]
                for expr in lisp_chunks(stmts):
                    await call(s, "autocad_run_lisp", {"expression": expr})

            if "view" in phases:
                await call(s, "autocad_zoom", {"mode": "extents"})
                await call(s, "autocad_regen", {})
                await call(s, "autocad_status", {})


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:] or ["setup", "draw", "post", "view"]))
