"""Shared test settings.

The Heron bridge is switched off for every test unless a test turns it back
on: the offline suites exercise tools against fake COM objects and have no
plug-in to ask. tests/test_gate.py turns it on with a fake bridge.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _bridge_off_by_default(monkeypatch, tmp_path):
    monkeypatch.setenv("HERON_AUTOCAD_BRIDGE", "off")
    # Keep audit lines and address files out of the real user profile.
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
