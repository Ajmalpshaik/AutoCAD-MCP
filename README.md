# AutoCAD MCP

> **Private repository.** This is Ajmal's working copy of the AutoCAD MCP server and the drawing
> packages made with it. It is not published and not ready for anyone else to install.

**An MCP server that lets Claude drive the AutoCAD already open on your machine.**

> You describe the drawing. AutoCAD MCP does the AutoCAD work behind it.

---

## What it is

AutoCAD MCP connects Claude to a running copy of full AutoCAD through AutoCAD's COM Automation
interface. Claude reads the drawing you have open and draws into it live. Geometry appears on screen
as it is created, and every tool call lands as **one undo step**, so anything Claude does can be
reversed with one Ctrl+Z.

```
"Check the AutoCAD connection and tell me what's open."
"Draw a 5000 x 3000 rectangle at the origin on a new layer A-WALL, in red."
"Find every text that says FFL and tell me where it is."
"Total the length of everything on layer M-PIPE-CWS."
"I've selected some objects - move them 1200 to the right."
```

It is **not** an AutoCAD plug-in. Nothing is installed inside AutoCAD. It is an outside program that
attaches to AutoCAD the same way a VBA macro would.

## Four parts

| Part | Responsibility | Folder |
|---|---|---|
| **The server** | The MCP server: 50 `autocad_*` tools, the COM link, AutoLISP helpers | [`src/autocad_mcp/`](src/autocad_mcp/README.md) |
| **Generators** | Python scripts that build whole drawing packages through the server (AHU, CCTV) | [`generators/`](generators/README.md) |
| **Drawings** | What the generators produced: DWG, PDF, PNG previews | [`drawings/`](drawings/README.md) |
| **Tools & tests** | Live smoke test, protocol check, offline and live test suites | [`tools/`](tools/README.md), [`tests/`](tests/README.md) |

Everything else is documentation ([`docs/`](docs/README.md)), configuration examples
([`examples/`](examples/README.md)) and stopped experiments kept for reference
([`archive/`](archive/README.md)).

---

## What you need

| | |
|---|---|
| OS | Windows (COM Automation is Windows-only) |
| AutoCAD | 2015 or newer, **full AutoCAD, not LT** (LT has no COM Automation) |
| Python | 3.10 or newer |

AutoCAD must have been started normally at least once so it registers its COM interface.

## Quick start

```bash
python -m venv .venv
```

```bash
.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Check the 50 tools register (AutoCAD not needed):

```bash
.venv\Scripts\autocad-mcp.exe --list-tools
```

Check it reaches AutoCAD (open AutoCAD with any drawing first):

```bash
.venv\Scripts\python.exe tools/smoke_test.py
```

Connect it to Claude Code (this repository's [`.mcp.json`](.mcp.json) already does this when Claude
Code is opened in this folder):

```bash
claude mcp add autocad -- "D:\06_Development\09_Autocad MCP\Autocad MCP\.venv\Scripts\autocad-mcp.exe"
```

Full steps, Claude Desktop and network use: [docs/SETUP.md](docs/SETUP.md).

---

## What it can do today

| Group | Tools | Detail |
|---|---|---|
| Session and files | 10 | status, open, save, switch, export PDF/DXF, zoom, system variables |
| Drawing | 12 | line, polyline, rectangle, circle, arc, ellipse, point, text, mtext, dimension, block, hatch |
| Bulk drawing | 1 | `autocad_batch_draw`: hundreds of entities in one AutoLISP round trip (about 9x faster) |
| Querying | 6 | list and filter entities, selection, find text, extents, measure |
| Modifying | 9 | move, copy, rotate, scale, mirror, offset, array, modify, delete (delete needs `confirm=true`) |
| Layers and blocks | 7 | list, create, state, current, delete, blocks, styles |
| Escape hatches | 5 | any command, AutoLISP with a result, purge, regen, audit |

Every tool with its options: [docs/03-tools-reference.md](docs/03-tools-reference.md).

**Drawing packages made with it so far** (outputs in [`drawings/`](drawings/README.md)):

| Package | Sheets | Generator |
|---|---|---|
| AHU-01 GA, isometric, P&ID, BMS, plant room, details, SLD, TAB | 11 (A1) | `generators/ahu_*.py` |
| CCTV full package, sample building B1+G+4, MOI SSD Qatar | 42 (A1) | `generators/cctv_*.py` |
| CCTV pole enclosure installation detail, Type A / B | 1 (A1) | `generators/encl_*.py` |

How to run them: [docs/04-drawing-generators.md](docs/04-drawing-generators.md).

---

## Where to read next

| You are | Read |
|---|---|
| **The owner** | [docs/HANDOVER.md](docs/HANDOVER.md): where work stopped and what is next |
| **Setting it up** | [docs/SETUP.md](docs/SETUP.md), then [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |
| **Changing the code** | [docs/PROJECT-MAP.md](docs/PROJECT-MAP.md), [CONTRIBUTING.md](CONTRIBUTING.md) |
| **An AI agent** | [AGENTS.md](AGENTS.md) |

The full documentation index is [docs/README.md](docs/README.md).

## Safety in one paragraph

Each tool call is one undo group. Deleting needs an explicit `confirm=true`, and without it the tool
only shows what it would delete. Commands that open a modal dialog are refused, because a dialog
blocks AutoCAD until a person closes it. The HTTP transport has **no authentication**; use it only on
a network you trust. More in [SECURITY.md](SECURITY.md).

## Licence

MIT. See [LICENSE](LICENSE).
