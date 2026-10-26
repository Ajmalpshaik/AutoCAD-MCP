"""One JSON line per tool call, kept for good.

The audit is the record of what Heron did to which drawing and when. It sits
apart from any log that gets rotated, it is never pruned, and failing to write
it never fails the tool: the work has already happened by then.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_lock = threading.Lock()


def audit_dir() -> Path:
    return Path(os.environ.get("LOCALAPPDATA", "")) / "Heron" / "autocad" / "audit"


def record(**fields: Any) -> None:
    """Append one line: at, conversation, tool, risk, drawing, ok, outcome, ms."""
    now = datetime.now(timezone.utc)
    line = json.dumps({"at": now.isoformat(timespec="milliseconds"), **fields}, default=str)
    try:
        folder = Path(audit_dir())
        folder.mkdir(parents=True, exist_ok=True)
        with _lock, open(folder / f"audit-{now:%Y%m}.jsonl", "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass
