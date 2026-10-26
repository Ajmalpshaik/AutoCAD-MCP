# AutoCAD MCP - Documentation index

> **Status, 2026-10-26:** the server has 50 tools and passes its offline tests. It was used live on
> AutoCAD 2027 for every package below. PDF export works on 2027 since 2026-10-19. Three drawing packages have been
> produced with it (AHU-01, CCTV 42 sheets, CCTV pole enclosure). Where work stopped:
> [HANDOVER.md](HANDOVER.md).
>
> Counts typed on these pages go stale. Derive them instead:
> `.venv\Scripts\autocad-mcp.exe --list-tools` for tools, `pytest --collect-only -q` for tests.

## Which document do I read?

| You are | Start with | Then |
|---|---|---|
| **The owner** | [HANDOVER](HANDOVER.md) | [ROADMAP](ROADMAP.md) |
| **Setting it up on a PC** | [SETUP](SETUP.md) | [TROUBLESHOOTING](TROUBLESHOOTING.md) |
| **Making drawings** | [04 - Drawing generators](04-drawing-generators.md) | [05 - Known limits](05-known-limits.md) |
| **Changing the server** | [PROJECT-MAP](PROJECT-MAP.md) | [02 - Architecture](02-architecture.md), [CONTRIBUTING](../CONTRIBUTING.md) |
| **An AI agent** | [AGENTS.md](../AGENTS.md) | [PROJECT-MAP](PROJECT-MAP.md) |

## The numbered set

Read in order the first time. Each one owns its subject; the others link to it.

| No. | Document | Owns |
|---|---|---|
| 01 | [Overview and principles](01-overview.md) | What it is for, what it will never do |
| 02 | [Architecture](02-architecture.md) | How a request reaches AutoCAD; Python vs AutoLISP; the COM rules |
| 03 | [Tools reference](03-tools-reference.md) | Every `autocad_*` tool, grouped |
| 04 | [Drawing generators](04-drawing-generators.md) | How the AHU and CCTV packages are built and re-run |
| 05 | [Known limits and traps](05-known-limits.md) | What broke before, and the fix |

## Registers and working pages

| Page | What it is |
|---|---|
| [SETUP](SETUP.md) | From nothing to Claude drawing in AutoCAD |
| [TROUBLESHOOTING](TROUBLESHOOTING.md) | Every error message and what fixes it |
| [PROJECT-MAP](PROJECT-MAP.md) | Folders, entry points, which source wins |
| [DECISIONS](DECISIONS.md) | Every real choice made, with the reason. Append-only |
| [HANDOVER](HANDOVER.md) | Where the last session stopped and what is next |
| [ROADMAP](ROADMAP.md) | Ideas and known gaps, not yet started |
| [CHANGELOG](../CHANGELOG.md) | What changed, newest first |
