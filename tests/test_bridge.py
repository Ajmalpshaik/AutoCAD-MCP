"""The Python side of the Heron bridge, against a fake plug-in pipe.

The fake stands in for Heron.AutoCAD.Bridge: it serves one named pipe,
reads one JSON line and answers with whatever the test hands it.
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid

import pytest
import pywintypes
import win32file
import win32pipe

from autocad_mcp.core import bridge
from autocad_mcp.core.bridge import (
    NOT_CONNECTED,
    NOTHING_SENT,
    Bridge,
    BridgeRefused,
)


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    return tmp_path


class FakePlugin:
    """One-connection pipe server; records the request, sends ``reply``."""

    def __init__(self, reply: dict | None, *, answer: bool = True) -> None:
        self.name = f"heron.autocad.test.{uuid.uuid4().hex[:8]}"
        self.reply = reply
        self.answer = answer
        self.requests: list[dict] = []
        self._ready = threading.Event()
        self._release = threading.Event()
        self._thread = threading.Thread(target=self._serve, daemon=True)

    def __enter__(self) -> FakePlugin:
        self._thread.start()
        self._ready.wait(5)
        return self

    def __exit__(self, *exc) -> None:
        self._release.set()
        self._thread.join(5)

    def _serve(self) -> None:
        handle = win32pipe.CreateNamedPipe(
            rf"\\.\pipe\{self.name}",
            win32pipe.PIPE_ACCESS_DUPLEX,
            win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_WAIT,
            1,
            65536,
            65536,
            0,
            None,
        )
        self._ready.set()
        try:
            win32pipe.ConnectNamedPipe(handle, None)
            data = b""
            while not data.endswith(b"\n"):
                _, chunk = win32file.ReadFile(handle, 65536)
                data += chunk
            self.requests.append(json.loads(data))
            if self.answer:
                win32file.WriteFile(handle, (json.dumps(self.reply) + "\n").encode())
                win32file.FlushFileBuffers(handle)
            self._release.wait(10)
        except pywintypes.error:
            pass
        finally:
            win32file.CloseHandle(handle)


def write_address(home, pid: int, pipe_name: str, token: str = "tok") -> None:
    folder = home / "Heron" / "autocad" / "bridges"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{pid}.json").write_text(
        json.dumps(
            {
                "pid": pid,
                "pipeName": pipe_name,
                "acadVersion": "26.0",
                "addinVersion": "1.0.0",
                "protocolVersion": 1,
                "token": token,
                "startedAt": "2026-10-26T00:00:00Z",
            }
        )
    )


def test_no_address_file_means_not_connected(home):
    with pytest.raises(BridgeRefused) as err:
        Bridge(os.getpid()).begin("autocad_status", "read", "Checking", "a.dwg")
    assert str(err.value) == NOT_CONNECTED


def test_dead_pid_file_is_deleted(home):
    dead = 4_000_000  # far above any live Windows pid
    write_address(home, dead, "nobody")
    assert Bridge(dead).find() is None
    assert not (home / "Heron" / "autocad" / "bridges" / f"{dead}.json").exists()


def test_begin_sends_token_client_conversation(home):
    with FakePlugin({"ok": True}) as plugin:
        write_address(home, os.getpid(), plugin.name, token="secret")
        job = Bridge(os.getpid()).begin("autocad_draw_line", "change", "Drawing a line", "a.dwg")
    request = plugin.requests[0]
    assert request["op"] == "begin"
    assert request["token"] == "secret"
    assert request["client"] == bridge.CLIENT
    assert request["conversation"] == bridge.CONVERSATION
    assert request["tool"] == "autocad_draw_line"
    assert request["risk"] == "change"
    assert request["job"] == job


def test_refusal_message_passed_through(home):
    reply = {"ok": False, "refusedBy": "Changes", "message": "Changes is off. Turn it on with the Changes padlock."}
    with FakePlugin(reply) as plugin:
        write_address(home, os.getpid(), plugin.name)
        with pytest.raises(BridgeRefused) as err:
            Bridge(os.getpid()).begin("autocad_draw_line", "change", "Drawing", "a.dwg")
    assert str(err.value).startswith("Changes is off.")
    assert str(err.value).endswith(NOTHING_SENT)


def test_hung_pipe_times_out(home):
    with FakePlugin(None, answer=False) as plugin:
        write_address(home, os.getpid(), plugin.name)
        started = time.monotonic()
        with pytest.raises(BridgeRefused) as err:
            Bridge(os.getpid()).begin("autocad_status", "read", "Checking", "a.dwg", timeout=1.0)
        assert time.monotonic() - started < 6
    assert str(err.value).endswith(NOTHING_SENT)


def test_end_never_raises_when_not_connected(home):
    Bridge(os.getpid()).end("job", ok=True, outcome="done", summary="x", ms=1)


def test_ask_keep_falls_back_to_discard(home):
    # A plug-in that cannot be reached must never be read as "keep".
    assert Bridge(os.getpid()).ask_keep("job", "Drew a line", ["2A"]) == "discard"


def test_bridge_can_be_switched_off(monkeypatch):
    monkeypatch.setenv("HERON_AUTOCAD_BRIDGE", "off")
    assert bridge.bridge_enabled() is False
    monkeypatch.delenv("HERON_AUTOCAD_BRIDGE")
    assert bridge.bridge_enabled() is True
