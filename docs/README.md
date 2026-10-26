# Heron AI for AutoCAD - Documentation index

> **Status, 2026-10-26:** the server (tools gated by the Heron plug-in) passes its offline tests;
> the plug-in builds for AutoCAD 2021-2027 and its bridge passes its offline tests, including the
> real Python client against the real C# server. **The plug-in has not yet run inside a real
> AutoCAD**: every live row in [NEEDS-CHECKING](NEEDS-CHECKING.md) is NOT RUN. Where work stopped:
> [HANDOVER](HANDOVER.md).
>
> Counts typed on these pages go stale. Derive them: `.venv\Scripts\autocad-mcp.exe --list-tools`
> for tools, `pytest --collect-only -q` and `dotnet test --list-tests` for tests.

## Which document do I read?

| You are | Start with | Then |
|---|---|---|
| **The owner** | [HANDOVER](HANDOVER.md) | [NEEDS-CHECKING](NEEDS-CHECKING.md), [ROADMAP](ROADMAP.md) |
| **A modeller** | [06 - The Heron plug-in](06-heron-plugin.md) | [SETUP](SETUP.md) |
| **Changing the code** | [PROJECT-MAP](PROJECT-MAP.md) | [02 - Architecture](02-architecture.md), [CONTRIBUTING](../CONTRIBUTING.md) |
| **An AI agent** | [AGENTS.md](../AGENTS.md) | [PROJECT-MAP](PROJECT-MAP.md) |

## The numbered set

| No. | Document | Owns |
|---|---|---|
| 01 | [Overview and principles](01-overview.md) | What it is for, what it will never do |
| 02 | [Architecture](02-architecture.md) | How a request reaches AutoCAD; the gate; Python vs AutoLISP; COM rules |
| 03 | [Tools reference](03-tools-reference.md) | Every `autocad_*` tool and its level; resources; prompts; start options |
| 05 | [Known limits and traps](05-known-limits.md) | What broke before, and the fix |
| 06 | [The Heron plug-in](06-heron-plugin.md) | Ribbon, padlocks, banner, Keep or Discard, the bridge protocol |
| 07 | [Drafting rules](07-drafting-rules.md) | How every drawing is set out: blocks, TLD labels, aligned views, preview check |

## Registers and working pages

| Page | What it is |
|---|---|
| [NEEDS-CHECKING](NEEDS-CHECKING.md) | Every live check, PASS / FAIL / NOT RUN / NO MACHINE per AutoCAD version |
| [DECISIONS](DECISIONS.md) | Every real choice, with the reason. Append-only |
| [HANDOVER](HANDOVER.md) | Where the last session stopped and what is next |
| [ROADMAP](ROADMAP.md) | Ideas and known gaps, not yet started |
| [SETUP](SETUP.md), [TROUBLESHOOTING](TROUBLESHOOTING.md) | Install, and every error with its fix |
| [PROJECT-MAP](PROJECT-MAP.md) | Folders, entry points, which source wins |
| [Design spec](superpowers/specs/2026-10-26-heron-autocad-design.md), [plan](superpowers/plans/2026-10-26-heron-autocad.md) | How Heron for AutoCAD was designed and built |
| [CHANGELOG](../CHANGELOG.md) | What changed, newest first |
