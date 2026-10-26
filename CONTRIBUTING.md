# Contributing

This is a public, single-owner repository. Ideas and corrections are welcome through an Issue. These
are the house rules for any change, by a person or an AI agent.

## Before you change anything

1. Read [AGENTS.md](AGENTS.md) and [docs/PROJECT-MAP.md](docs/PROJECT-MAP.md).
2. Read the README of the folder you are changing.
3. Check [docs/05-known-limits.md](docs/05-known-limits.md) for the trap you are about to step in.

## Branches and commits

- `main` is always working. Do larger work on a branch: `feature/<name>`, `fix/<name>`, `docs/<name>`.
- One subject per commit. Write the message as what the change does: *"Fit PDF export to A1 paper"*.
- Never commit `.venv/`, AutoCAD `.bak` / `.dwl` files, or anything with a password or key in it.
  [.gitignore](.gitignore) covers the usual ones.

## The gates

Run both before every push:

```bash
.venv\Scripts\python.exe -m ruff check .
```

```bash
.venv\Scripts\python.exe -m pytest -m "not live"
```

The same two run on GitHub for every push ([.github/workflows/ci.yml](.github/workflows/ci.yml)).
GitHub has no AutoCAD, so **live tests run only on your PC**, with AutoCAD open:

```bash
.venv\Scripts\python.exe -m pytest -m live
```

```bash
.venv\Scripts\python.exe tools/smoke_test.py
```

## Adding a tool

1. Put it in the matching file in [`src/autocad_mcp/tools/`](src/autocad_mcp/tools/).
2. Keep the layer rule: `tools` -> `acad` -> `core`, never upward.
3. Add an offline test in [`tests/test_offline.py`](tests/test_offline.py) and, if it changes the
   drawing, a live one in [`tests/test_live.py`](tests/test_live.py).
4. Add it to [docs/03-tools-reference.md](docs/03-tools-reference.md) and the count in the README.
5. Add a line to [CHANGELOG.md](CHANGELOG.md).

## Adding a drawing package

Follow [docs/04-drawing-generators.md](docs/04-drawing-generators.md): one data module as the single
source of truth, one sheet module per group, one runner. Outputs go in `drawings/<PACKAGE>/`.
