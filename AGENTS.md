# AGENTS.md - for an AI agent working on AutoCAD MCP

**Read this first. It is short on purpose.** It points at the file that owns each detail instead of
repeating it.

> **Asked to draw something in AutoCAD, rather than change this server? Stop reading here.** Use the
> `autocad_*` MCP tools. Call `autocad_status` first: it gives the drawing units every coordinate
> depends on. If no `autocad_` tool is listed, the server is not connected: say so in one line, point
> at [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md), and stop.

---

## What this project is

An MCP server (Python) that drives a running full AutoCAD through COM, plus the generator scripts that
used it to produce real drawing packages. The owner is a BIM / MEP modeller, not a developer: explain
in plain words and confirm before anything that changes GitHub.

This repository is **separate from Heron AI** (`D:\06_Development\03_Heron\Heron Ai`). Never edit
Heron from here, and never route AutoCAD work through Heron or Revit work through this server.

## Reading order

1. This file.
2. [README.md](README.md): what it is and what it can do.
3. [docs/PROJECT-MAP.md](docs/PROJECT-MAP.md): folders, entry points, which source wins.
4. The **README of the folder you are changing**.
5. [docs/05-known-limits.md](docs/05-known-limits.md): the traps already found the hard way.
6. [docs/HANDOVER.md](docs/HANDOVER.md), only if you are continuing unfinished work.

## Never

- **Never run `pip install -e .` while an `autocad-mcp` server is running.** The locked exe makes pip
  abort half-way and the next start fails to import. Fix and detail in
  [05 §1](docs/05-known-limits.md#1-reinstalling-while-the-server-runs).
- **Never import a generator to "check" it.** `pdf_plot.py`, `pdf_plot2.py` and `png_plot.py` run on
  import and talk to AutoCAD. Use `python -m py_compile` instead.
- **Never type a drive path into a generator.** Use [`generators/paths.py`](generators/paths.py).
- **Never drive AutoCAD from two sessions at once.** One switching the active drawing breaks the
  other's batch. Check the active drawing name before each batch.
- **Never send an AutoLISP expression near 3,600 characters.** It fails silently; keep chunks under
  about 700.
- **Never claim a drawing is right without looking at it.** Plot a PNG and check it
  ([04](docs/04-drawing-generators.md)).
- **Never edit a test until it passes.** A red test is a claim about the code.

## How to work

**Inspect before you edit.** Read the file and find what references it.
**Make the smallest safe change.** Something you notice on the way is written into
[docs/ROADMAP.md](docs/ROADMAP.md), not fixed in the same change.
**Run the gates before you claim anything:**

```bash
.venv\Scripts\python.exe -m ruff check .
```

```bash
.venv\Scripts\python.exe -m pytest -m "not live"
```

With AutoCAD open, also `tools/smoke_test.py` and `pytest -m live`.

**Record a decision** in [docs/DECISIONS.md](docs/DECISIONS.md) when you choose between two real
options. **Update [docs/HANDOVER.md](docs/HANDOVER.md)** before you stop.
