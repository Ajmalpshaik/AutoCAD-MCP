# src/autocad_mcp - the server

The MCP server. Installed as the `autocad-mcp` command (`pyproject.toml` -> `server:main`).

| Folder / file | Owns | Knows about |
|---|---|---|
| `server.py` | Command line: `--transport stdio/http`, `--host`, `--port`, `--list-tools` | everything below |
| `tools/` | The 50 MCP tools, one file per subject | MCP, `acad`, `core` |
| `acad/` | AutoCAD domain: entities, selections, tables, AutoLISP, units | `core` only |
| `core/` | COM worker thread, VARIANTs, errors, the FastMCP instance, undo groups | pywin32 only |

**The one rule:** imports point down only, `tools` -> `acad` -> `core`.

| Tool file | Tools |
|---|---|
| `tools/document.py` | status, drawings, open, save, switch, export, zoom, variables |
| `tools/draw.py` | the 12 single-entity drawing tools |
| `tools/batch.py` | `autocad_batch_draw` |
| `tools/query.py` | list, get, selection, find text, extents, measure |
| `tools/modify.py` | move, copy, rotate, scale, mirror, offset, array, modify, delete |
| `tools/layers.py` | layers, blocks, styles |
| `tools/advanced.py` | send command, run LISP, purge, regen, audit |
| `tools/_shared.py` | option types and helpers shared by the tool files |

After changing anything here: run the gates ([CONTRIBUTING](../../CONTRIBUTING.md)), then **restart the
server** - a running one keeps the old code. Never reinstall while it runs
([05 §1](../../docs/05-known-limits.md#1-reinstalling-while-the-server-runs)).

Design detail: [docs/02-architecture.md](../../docs/02-architecture.md).
