# src/autocad_mcp - the server

The MCP server. Installed as the `autocad-mcp` command (`pyproject.toml` -> `server:main`).

| Folder / file | Owns | Knows about |
|---|---|---|
| `server.py` | Command line: `--transport stdio/http`, `--host`, `--port`, `--list-tools`, `--read-only`, `--no-bridge` | everything below |
| `tools/` | The MCP tools, resources and prompts, one file per subject (`--list-tools` counts them) | MCP, `acad`, `core` |
| `acad/` | AutoCAD domain: entities, selections, tables, AutoLISP, units, the UCS transform, sheet arithmetic | `core` only |
| `core/` | COM worker thread, VARIANTs, errors, the FastMCP instance, undo groups, and the Heron gate (`gate.py`, `bridge.py`, `risk.py`, `audit.py`) | pywin32 only |

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
| `tools/standards.py` | standards check, attribute extraction |
| `tools/coordinates.py` | the UCS: read it, set it, convert points through it |
| `tools/sheets.py` | layouts, page setup, title blocks, viewports |
| `tools/views.py` | saved views: one named location, plotted and viewported |
| `tools/settings.py` | drawing settings, text and dimension styles |
| `tools/convert.py` | an import into a shop drawing: remap layers, tidy overrides |
| `tools/sequence.py` | `autocad_sequence`: several tools in one call |
| `tools/resources.py` | MCP resources and prompts |
| `tools/_shared.py` | option types and helpers shared by the tool files, including the UCS funnel |

After changing anything here: run the gates ([CONTRIBUTING](../../CONTRIBUTING.md)), then **restart the
server** - a running one keeps the old code. Never reinstall while it runs
([05 §1](../../docs/05-known-limits.md#1-reinstalling-while-the-server-runs)).

Design detail: [docs/02-architecture.md](../../docs/02-architecture.md).
