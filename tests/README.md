# tests

| File | Needs AutoCAD | Covers |
|---|---|---|
| `test_offline.py` | No | Tool registration, input checks, LISP generation, VARIANT and unit helpers |
| `test_export.py` | No (fake COM objects) | The PDF export order that works on AutoCAD 2027 ([D-04](../docs/DECISIONS.md)) |
| `test_live.py` | **Yes**, marked `live` | Real drawing round trips |

Offline only (what CI runs):

```bash
.venv\Scripts\python.exe -m pytest -m "not live"
```

Live, with AutoCAD open:

```bash
.venv\Scripts\python.exe -m pytest -m live
```

How many tests there are: `pytest --collect-only -q`. Never edit a test just to make it pass.
