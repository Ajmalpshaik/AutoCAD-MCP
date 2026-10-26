# tools - checks you run by hand

| Script | Needs AutoCAD | Does |
|---|---|---|
| `smoke_test.py` | Yes, with a drawing open | Runs live checks against a scratch drawing and cleans up |
| `protocol_check.py` | Yes | Starts the server exactly as Claude does and does the MCP handshake over stdio |

```bash
.venv\Scripts\python.exe tools/smoke_test.py
```

```bash
.venv\Scripts\python.exe tools/protocol_check.py
```

Both find the server at `.venv\Scripts\autocad-mcp.exe` beside this folder.
