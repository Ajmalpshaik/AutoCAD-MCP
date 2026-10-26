# autocad-mcp

An MCP server that connects Claude to AutoCAD.

It drives the copy of AutoCAD **already open on your machine** through AutoCAD's
COM Automation interface. Claude reads the drawing you have open and draws into
it live — geometry appears on screen as it is created, and every tool call lands
as a single undo step, so anything Claude does can be reversed with one Ctrl+Z.

50 tools across seven areas: session and files, drawing, bulk drawing,
querying, modifying, layers and blocks, and raw command/AutoLISP escape
hatches.

---

## Requirements

| | |
|---|---|
| OS | Windows (COM Automation is Windows-only) |
| AutoCAD | 2015 or newer, full AutoCAD — **not** AutoCAD LT |
| Python | 3.10 or newer |

**On AutoCAD LT:** LT 2024+ for Windows *does* run AutoLISP internally — that
part of LT's reputation is out of date. But this server drives AutoCAD from an
*external* process through ActiveX/COM Automation, and
[Autodesk's own documentation](https://help.autodesk.com/view/OARX/2024/ENU/?guid=GUID-2090E4E8-9AE0-4E01-B5EB-0843A30EB0E9)
states that ActiveX is not supported in AutoCAD LT. There is no
`AutoCAD.Application` COM server for a client to attach to, so this server
cannot reach LT regardless of version. Full AutoCAD is required.

AutoCAD must also have been launched at least once normally, so it registers
its COM interface.

---

## Install

```bash
uv venv --python 3.11
```

```bash
uv pip install -e .
```

Verify the tools registered, without touching AutoCAD (expect 50):

```bash
.venv\Scripts\autocad-mcp.exe --list-tools
```

Then check it can actually reach AutoCAD (open AutoCAD with any drawing first):

```bash
.venv\Scripts\python.exe scripts/smoke_test.py
```

And check it over the real MCP protocol, exactly as Claude launches it:

```bash
.venv\Scripts\python.exe scripts/protocol_check.py
```

---

## Connect it to Claude

### Claude Code

```bash
claude mcp add autocad -- "D:\06_Development\09_Autocad MCP\Autocad MCP\.venv\Scripts\autocad-mcp.exe"
```

### Claude Desktop

Edit `%APPDATA%\Claude\claude_desktop_config.json` and add the server, then
restart Claude Desktop completely (quit from the tray, not just close the
window):

```json
{
  "mcpServers": {
    "autocad": {
      "command": "D:\\06_Development\\09_Autocad MCP\\Autocad MCP\\.venv\\Scripts\\autocad-mcp.exe"
    }
  }
}
```

A ready-to-copy version is in [`examples/claude_desktop_config.json`](examples/claude_desktop_config.json).

### Over the network

To drive AutoCAD on this machine from Claude running on another one:

```bash
.venv\Scripts\autocad-mcp.exe --transport http --host 0.0.0.0 --port 8000
```

There is no authentication, and the tools can modify and delete drawing
content. Only do this on a network you trust.

---

## Using it

Start every session by asking Claude to check the connection — that returns the
drawing's units, which every coordinate afterwards depends on:

> Check the AutoCAD connection and tell me what's open.

Then work in plain language:

> What's in this drawing? Give me a summary by layer.

> Draw a 5000 x 3000 rectangle at the origin on a new layer called A-WALL, in red.

> Find every text that says FFL and tell me where it is.

> Total the length of everything on layer M-PIPE-CWS.

> I've selected some objects in AutoCAD — move them 1200 to the right.

Coordinates are always in the drawing's own units. In a millimetre drawing,
`5000` means 5 metres.

---

## The tools

### Session and files (10)

| Tool | Purpose |
|---|---|
| `autocad_status` | Connection check, units, current layer, entity counts |
| `autocad_list_drawings` | Every drawing currently open |
| `autocad_create_drawing` | New drawing, optionally from a template |
| `autocad_open_drawing` | Open a .dwg or .dxf |
| `autocad_save_drawing` | Save, or Save As to a new path |
| `autocad_switch_drawing` | Change which open drawing is active |
| `autocad_export` | Export to PDF (extents fitted to the sheet, optional `paper_size` such as `A3`), DXF, WMF, SAT, BMP, EPS or STL |
| `autocad_zoom` | Zoom extents, all, or to a window |
| `autocad_get_variable` | Read a system variable |
| `autocad_set_variable` | Write a system variable |

### Drawing (12)

`autocad_draw_line`, `autocad_draw_polyline`, `autocad_draw_rectangle`,
`autocad_draw_circle`, `autocad_draw_arc`, `autocad_draw_ellipse`,
`autocad_draw_point`, `autocad_add_text`, `autocad_add_mtext`,
`autocad_add_dimension`, `autocad_insert_block`, `autocad_add_hatch`

All of them take the same `layer`, `color`, `linetype` and `space` options, and
all return the handle of what they created. A layer that does not exist is
created and reported.

### Bulk drawing (1)

`autocad_batch_draw` creates many entities in one call by sending a single
**AutoLISP** script that runs inside AutoCAD, instead of one COM round trip per
entity.

Measured on AutoCAD 2020, 200 lines:

| Method | Time | Rate |
|---|---:|---:|
| One at a time via `autocad_draw_*` (COM) | 20.3 s | 10/s |
| `autocad_batch_draw` | 2.2 s | 93/s |
| `autocad_batch_draw`, `return_handles=false` | 1.2 s | 173/s |

Use it for anything above roughly ten entities — floor plans, grids, label
sets. Every operation is validated in Python first, so a malformed batch fails
naming the offending operation index without touching the drawing. Supports
line, polyline, rectangle, circle, arc, text and point.

### Querying (6)

| Tool | Purpose |
|---|---|
| `autocad_list_entities` | Filter by type, layer, block or colour; paginated, with a summary mode |
| `autocad_get_entity` | Full properties and bounding box of one entity |
| `autocad_get_selection` | What the user has selected in AutoCAD right now |
| `autocad_find_text` | Search text, mtext and block attributes |
| `autocad_get_extents` | Bounding box of the drawing, or of one layer |
| `autocad_measure` | Point-to-point distance, or total length/area of entities or a layer |

### Modifying (9)

`autocad_move_entities`, `autocad_copy_entities`, `autocad_rotate_entities`,
`autocad_scale_entities`, `autocad_mirror_entities`, `autocad_offset_entities`,
`autocad_array_entities`, `autocad_modify_entity`, `autocad_delete_entities`

Deletion requires an explicit `confirm=true`; without it the tool returns a
preview of what it *would* delete and changes nothing.

### Layers and blocks (7)

`autocad_list_layers`, `autocad_create_layer`, `autocad_set_layer_state`,
`autocad_set_current_layer`, `autocad_delete_layer`, `autocad_list_blocks`,
`autocad_list_styles`

### Escape hatches (5)

| Tool | Purpose |
|---|---|
| `autocad_send_command` | Any AutoCAD command — TRIM, FILLET, custom add-in commands |
| `autocad_run_lisp` | Evaluate an AutoLISP expression **and get the result back** |
| `autocad_purge` | Remove unused blocks, layers, linetypes, styles |
| `autocad_regen` | Regenerate the display |
| `autocad_audit` | Check and repair the drawing database |

`autocad_send_command` refuses commands known to open a modal dialog and names
the command-line alternative, because a dialog blocks AutoCAD's COM interface
until a human dismisses it.

---

## How it works

```
Claude  ──stdio/http──▶  MCP server (Python)
                              │
                              │  every call marshalled onto one
                              │  CoInitialize'd worker thread
                              ▼
                         pywin32 COM
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
      typed COM operations            AutoLISP scripts
      (one round trip each)           (one round trip total)
              └───────────────┬───────────────┘
                              ▼
                    AutoCAD  ──▶  your open drawing
```

### Why Python *and* AutoLISP

AutoLISP is AutoCAD's native language and is genuinely faster for bulk work —
it runs inside AutoCAD instead of across a process boundary. But it cannot be
the MCP server: MCP is a protocol spoken over stdio or HTTP to an *external*
process, and AutoLISP only runs inside AutoCAD, with no way to open a socket or
answer a client. So the protocol layer has to live outside, in Python.

That makes the right design a hybrid, and this server uses each language where
it wins:

| Job | Uses | Why |
|---|---|---|
| MCP protocol | Python | AutoLISP cannot host it |
| Typed single operations | COM | Returns real objects and values, with per-field validation |
| Bulk creation | **AutoLISP** `entmake` | One round trip instead of hundreds — ~9x faster |
| Reaching what COM cannot | **AutoLISP** | Xdata, dictionaries, xrecords, custom object properties |

The catch with AutoLISP is the return path: AutoCAD's COM interface has no
"evaluate this and give me the answer" call — `SendCommand` is fire-and-forget.
Two ways around it are used here. Small results come back through the `USERS1`
system variable (`autocad_run_lisp`); large ones are written to a temp file by
the LISP and read from Python (`autocad_batch_draw`).

### Two facts that drive the COM layer

**It is apartment-threaded.** Every COM call must happen on one thread that has
called `CoInitialize`. FastMCP tools run on asyncio's event loop, so all COM
work is marshalled onto a single dedicated worker thread
([`core/connection.py`](src/autocad_mcp/core/connection.py)).

**It rejects calls while AutoCAD is busy.** A modal dialog, a command waiting
for input, or a regen in progress all produce `RPC_E_CALL_REJECTED`. That is
transient, so it is retried for 10 seconds before being reported — and when it
is reported, the message says to press Esc in AutoCAD, which is what actually
fixes it.

---

## Layout

```
Autocad MCP/
├── README.md
├── pyproject.toml
├── src/autocad_mcp/
│   ├── server.py            entry point and CLI
│   ├── core/                COM link, VARIANTs, errors, MCP plumbing
│   │   ├── connection.py    worker thread, retry, app/document access
│   │   ├── variants.py      SAFEARRAY marshalling
│   │   ├── errors.py        COM error interpretation
│   │   └── registry.py      shared FastMCP instance, undo grouping
│   ├── acad/                AutoCAD domain layer — no MCP knowledge
│   │   ├── entities.py      entity serialization, handle lookup
│   │   ├── selection.py     DXF filters and selection sets
│   │   ├── tables.py        layers, linetypes, property application
│   │   ├── lisp.py          AutoLISP generation and result retrieval
│   │   └── units.py         INSUNITS, degree/radian conversion
│   └── tools/               the MCP tools, grouped by subject
│       ├── document.py  draw.py    batch.py  query.py
│       └── modify.py    layers.py  advanced.py
├── docs/
│   ├── SETUP.md
│   └── TROUBLESHOOTING.md
├── scripts/
│   ├── smoke_test.py        55 live checks against a scratch drawing
│   └── protocol_check.py    MCP handshake over stdio
├── tests/test_offline.py    85 tests, no AutoCAD needed
└── examples/
```

The layers only depend downward: `tools` → `acad` → `core`. Nothing in `acad`
or `core` imports a tool, so the AutoCAD logic can be tested and reused
independently of MCP.

---

## Troubleshooting

**"No running AutoCAD instance was found"** — Start AutoCAD and open a drawing.
If it is already open, check whether it is running as Administrator: COM cannot
connect from a non-elevated process to an elevated one. Run both the same way.

**"AutoCAD stayed busy and never accepted the request"** — A dialog is open or a
command is waiting for input. Switch to AutoCAD, press Esc, close any dialog.

**"AutoCAD is in the middle of a command"** — Same fix: press Esc in AutoCAD.

**Claude does not see the tools** — Restart Claude Desktop completely (quit from
the system tray). Verify the path in the config points at
`.venv\Scripts\autocad-mcp.exe` and that running it directly prints nothing and
waits — that is correct for a stdio server.

More detail in [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

---

## Development

```bash
uv pip install -e ".[dev]"
```

```bash
.venv\Scripts\python.exe -m pytest -m "not live"
```

The default test run needs no AutoCAD. Tests marked `live` drive a real
instance:

```bash
.venv\Scripts\python.exe -m pytest -m live
```

## License

MIT
