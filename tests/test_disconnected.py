"""A COM pointer AutoCAD has disconnected is rebuilt and retried, not reported as a failure.

Seen 2026-10-26: Documents.Add raised RPC_E_DISCONNECTED ("The object invoked
has disconnected from its clients") in the full test suite; the same call on a
fresh dispatch works.
"""

from __future__ import annotations

import pythoncom

from autocad_mcp.core import connection
from autocad_mcp.core.errors import is_dispatch_failure, is_retryable

RPC_E_DISCONNECTED = -2147417848


def disconnected():
    return pythoncom.com_error(RPC_E_DISCONNECTED, "The object invoked has disconnected from its clients.", None, None)


def test_disconnected_counts_as_a_dead_pointer():
    assert is_dispatch_failure(disconnected())
    assert is_retryable(disconnected())


def test_retry_drops_the_cached_pointer_and_tries_again(monkeypatch):
    monkeypatch.setattr(connection, "RETRY_DELAY", 0)
    dropped = []
    monkeypatch.setattr(connection, "invalidate", lambda: dropped.append(True))
    calls = []

    def work():
        calls.append(1)
        if len(calls) == 1:
            raise disconnected()
        return "ok"

    assert connection._with_retry(work) == "ok"
    assert dropped and len(calls) == 2
