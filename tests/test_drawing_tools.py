"""Import from a standards drawing and layout tools (Lee Mac's Steal, Import Block,
TabSort, Renumber Layouts and Copy to Layouts ideas; Heron's own code)."""

from __future__ import annotations

import pytest

from autocad_mcp.tools import drawing_tools as dt


def test_pick_names_by_wildcards_case_insensitive():
    available = ["VALVE-GATE", "Valve-Ball", "PUMP", "*Model_Space", "A$C123"]
    assert dt.pick_names(available, ["valve*"]) == ["Valve-Ball", "VALVE-GATE"]
    assert dt.pick_names(available, ["*"]) == ["PUMP", "Valve-Ball", "VALVE-GATE"]


def test_renumber_plan_keeps_tab_order():
    plan = dt.renumber_plan(["Layout2", "Layout1", "Cover"], prefix="E-", start=101, pad=0)
    assert plan == {"Layout2": "E-101", "Layout1": "E-102", "Cover": "E-103"}


def test_renumber_plan_refuses_duplicates_with_unchanged_tabs():
    with pytest.raises(ValueError, match="E-102"):
        dt.check_names(["A", "E-102"], {"A": "E-102"})


def test_order_plan_puts_named_first_and_keeps_the_rest():
    assert dt.order_plan(["A", "B", "C", "D"], ["C", "A"]) == ["C", "A", "B", "D"]
    with pytest.raises(ValueError, match="X"):
        dt.order_plan(["A"], ["X"])


def test_dbx_progid_from_version():
    assert dt.dbx_progid("26.0s (LMS Tech)") == "ObjectDBX.AxDbDocument.26"
    assert dt.dbx_progid("24.1s") == "ObjectDBX.AxDbDocument.24"


def test_levels():
    from autocad_mcp.core.risk import Risk, risk_of

    assert risk_of("autocad_list_layouts") is Risk.READ
    assert risk_of("autocad_import_from_drawing") is Risk.CHANGE
    assert risk_of("autocad_manage_layouts") is Risk.CHANGE
