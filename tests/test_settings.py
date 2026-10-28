"""Plain words to system variables, and dimension-style plans (no AutoCAD)."""

from __future__ import annotations

import pytest

from autocad_mcp.core.risk import Risk, risk_of
from autocad_mcp.tools.settings import (
    DIM_OPTIONS,
    DRAWING_VARIABLES,
    OSNAP_SUPPRESS,
    OSNAPS,
    osnap_bits,
    osnap_names,
    plan_dim_style,
    plan_settings,
    point_mode,
    unit_code,
)


class TestOsnaps:
    def test_names_add_up_to_the_osmode_value(self):
        assert osnap_bits(["endpoint", "midpoint"]) == 3
        assert osnap_bits(["endpoint", "center", "intersection"]) == 37
        assert osnap_bits(["perpendicular", "endpoint"]) == 129

    def test_spelling_is_forgiving(self):
        assert osnap_bits(["END POINT".lower().replace(" ", "")]) == 1
        assert osnap_bits(["centre"]) == osnap_bits(["center"])
        assert osnap_bits(["geometric-center"]) == 1024
        assert osnap_bits(["Geometric Center"]) == 1024

    def test_none_and_all(self):
        assert osnap_bits(["none"]) == 0
        assert osnap_bits([]) == 0
        assert osnap_bits(["all"]) == sum(set(OSNAPS.values()))

    def test_an_unknown_snap_lists_the_real_ones(self):
        with pytest.raises(ValueError) as exc:
            osnap_bits(["elbow", "midpoint"])
        message = str(exc.value)
        assert "elbow" in message and "perpendicular" in message

    def test_names_come_back_in_bit_order(self):
        assert osnap_names(37) == ["endpoint", "center", "intersection"]
        assert osnap_names(0) == []

    def test_the_suppress_bit_is_reported_as_suppressed(self):
        assert osnap_names(OSNAP_SUPPRESS | 37) == ["suppressed"]

    @pytest.mark.parametrize("name", [n for n in OSNAPS if n != "centre"])
    def test_every_snap_round_trips(self, name):
        assert osnap_names(osnap_bits([name])) == [name]


class TestPointStyle:
    def test_known_styles(self):
        assert point_mode("x") == 3
        assert point_mode("circle_x") == 35
        assert point_mode("square_circle_x") == 99
        assert point_mode("Circle X") == 35

    def test_an_unknown_style_lists_the_real_ones(self):
        with pytest.raises(ValueError, match="circle_x"):
            point_mode("sparkle")


class TestUnitCode:
    @pytest.mark.parametrize(
        ("given", "expected"),
        [("mm", 4), ("millimeters", 4), ("meters", 6), ("m", 6), ("inches", 1), ("feet", 2), (4, 4)],
    )
    def test_names_and_codes(self, given, expected):
        assert unit_code(given) == expected

    def test_nonsense_is_refused(self):
        with pytest.raises(ValueError, match="millimeters"):
            unit_code("cubits")
        with pytest.raises(ValueError, match="0 to 20"):
            unit_code(99)


class TestPlanSettings:
    def test_everything_written_is_on_the_allowed_list(self):
        plan = plan_settings(
            {
                "units": "mm", "scale": "1:50", "paper_text_height": 2.5,
                "osnaps": ["endpoint"], "point_style": "x", "linear_precision": 0,
                "angle_format": "dms", "limits": [[0, 0], [100, 100]],
                "psltscale": True, "lineweight_display": True, "mirror_text": False,
            }
        )
        assert set(plan) <= set(DRAWING_VARIABLES)

    def test_the_scale_drives_dimscale_ltscale_and_the_annotation_scale(self):
        plan = plan_settings({"scale": "1:50"})
        assert plan["DIMSCALE"] == pytest.approx(50.0)
        assert plan["LTSCALE"] == pytest.approx(50.0)
        assert plan["CANNOSCALE"] == "1:50"

    def test_ltscale_can_be_left_out_of_the_scale(self):
        plan = plan_settings({"scale": "1:50", "ltscale_from_scale": False})
        assert "LTSCALE" not in plan
        assert plan["DIMSCALE"] == pytest.approx(50.0)

    def test_paper_text_height_becomes_the_model_height(self):
        assert plan_settings({"scale": "1:50", "paper_text_height": 2.5})["TEXTSIZE"] == pytest.approx(125.0)

    def test_paper_text_height_without_a_scale_is_refused(self):
        with pytest.raises(ValueError, match="scale"):
            plan_settings({"paper_text_height": 2.5})

    def test_metric_units_select_the_metric_definition_files(self):
        assert plan_settings({"units": "mm"})["MEASUREMENT"] == 1
        assert plan_settings({"units": "inches"})["MEASUREMENT"] == 0

    def test_an_explicit_metric_flag_wins_over_the_units(self):
        assert plan_settings({"units": "mm", "metric": False})["MEASUREMENT"] == 0

    def test_booleans_become_the_zero_or_one_autocad_wants(self):
        plan = plan_settings({"psltscale": True, "lineweight_display": False, "mirror_text": False})
        assert plan == {"PSLTSCALE": 1, "LWDISPLAY": 0, "MIRRTEXT": 0}

    def test_associative_dimensions_is_two_or_one(self):
        assert plan_settings({"associative_dimensions": True})["DIMASSOC"] == 2
        assert plan_settings({"associative_dimensions": False})["DIMASSOC"] == 1

    def test_limits_become_two_points(self):
        plan = plan_settings({"limits": [[0, 0], [420, 297]]})
        assert plan["LIMMIN"] == (0.0, 0.0)
        assert plan["LIMMAX"] == (420.0, 297.0)

    def test_malformed_limits_are_refused(self):
        with pytest.raises(ValueError, match="min x"):
            plan_settings({"limits": [[0, 0]]})

    def test_precision_outside_range_is_refused(self):
        with pytest.raises(ValueError, match="between 0 and 8"):
            plan_settings({"linear_precision": 12})

    def test_nothing_asked_for_is_nothing_written(self):
        assert plan_settings({}) == {}

    def test_an_unknown_format_lists_the_real_ones(self):
        with pytest.raises(ValueError, match="architectural"):
            plan_settings({"linear_format": "metric-ish"})
        with pytest.raises(ValueError, match="surveyor"):
            plan_settings({"angle_format": "compass"})


class TestPlanDimStyle:
    def test_friendly_names_become_dim_variables(self):
        plan = plan_dim_style(
            {"name": "M-50", "scale": 50, "text_height": 2.5, "arrow_size": 2.5, "precision": 0}
        )
        assert plan == {"DIMSCALE": 50.0, "DIMTXT": 2.5, "DIMASZ": 2.5, "DIMDEC": 0.0}

    def test_flags_become_zero_or_one(self):
        plan = plan_dim_style({"text_above_line": True, "text_inside": False, "force_line_inside": True})
        assert plan == {"DIMTAD": 1, "DIMTIX": 0, "DIMTOFL": 1}

    def test_names_stay_text(self):
        plan = plan_dim_style({"text_style": "ROMANS", "arrow_block": "_ArchTick"})
        assert plan == {"DIMTXSTY": "ROMANS", "DIMBLK": "_ArchTick"}

    def test_the_decimal_separator_is_one_character(self):
        assert plan_dim_style({"decimal_separator": ","}) == {"DIMDSEP": ","}
        with pytest.raises(ValueError, match="single character"):
            plan_dim_style({"decimal_separator": "--"})

    def test_raw_dim_variables_are_allowed_through(self):
        assert plan_dim_style({"variables": {"dimtih": 0, "DIMJUST": 0}}) == {"DIMTIH": 0, "DIMJUST": 0}

    def test_anything_outside_the_dim_family_is_refused(self):
        with pytest.raises(ValueError) as exc:
            plan_dim_style({"variables": {"LTSCALE": 1}})
        assert "autocad_drawing_setup" in str(exc.value)

    def test_nothing_asked_for_is_nothing_written(self):
        assert plan_dim_style({"name": "EMPTY"}) == {}

    @pytest.mark.parametrize("variable", DIM_OPTIONS.values())
    def test_every_mapped_variable_is_a_dim_variable(self, variable):
        assert variable.startswith("DIM")


def test_levels():
    assert risk_of("autocad_drawing_setup") is Risk.CHANGE
    assert risk_of("autocad_create_styles") is Risk.CHANGE


def test_the_allowed_list_holds_no_duplicates():
    assert len(DRAWING_VARIABLES) == len(set(DRAWING_VARIABLES))


# ---------------------------------------------------------------------------
# Against a fake drawing: the 2026-10-28 failures in AutoCAD 2027
# ---------------------------------------------------------------------------


class FakeDimStyle:
    def __init__(self, name):
        self.Name = name
        self.copied = None

    def CopyFrom(self, doc):
        self.copied = dict(doc.variables)


class FakeDimStyles:
    def __init__(self):
        self.items = [FakeDimStyle("Standard")]

    @property
    def Count(self):
        return len(self.items)

    def Item(self, index):
        return self.items[index]

    def Add(self, name):
        style = FakeDimStyle(name)
        self.items.append(style)
        return style


class FakeDrawing:
    """The variables a fresh metric drawing holds, as AutoCAD's COM hands them back."""

    def __init__(self, **variables):
        self.variables = {
            "CANNOSCALE": "1:1", "DIMSCALE": 1.0, "LTSCALE": 1.0, "TEXTSIZE": 2.5,
            "DIMTXSTY": "Standard", "DIMTXT": 2.5, "DIMDEC": 4, "DIMBLK": "",
            "OSMODE": 4133, "LIMMIN": (0.0, 0.0),
        }
        self.variables.update(variables)
        self.written: list[tuple[str, object]] = []
        self.DimStyles = FakeDimStyles()

    def GetVariable(self, name):
        return self.variables[name]

    def SetVariable(self, name, value):
        self.written.append((name, value))
        self.variables[name] = value

    def StartUndoMark(self):
        pass

    def EndUndoMark(self):
        pass


@pytest.fixture
def drawing(monkeypatch):
    from autocad_mcp.tools import settings

    doc = FakeDrawing()

    async def run(fn):
        return fn()

    monkeypatch.setattr(settings, "run", run)
    monkeypatch.setattr(settings, "get_doc", lambda: doc)
    monkeypatch.setattr(settings, "require_idle", lambda d: None)
    return doc


class TestReadVariable:
    """A variable's value comes back as AutoCAD holds it: text stays text."""

    @pytest.mark.parametrize(
        ("held", "expected"),
        [("1:10", "1:10"), ("Standard", "Standard"), ("12", "12"), ("", ""),
         (2.5, 2.5), (4, 4), ((0.0, 0.0), [0.0, 0.0])],
    )
    def test_each_kind_of_value(self, held, expected):
        from autocad_mcp.tools.settings import _read_variable

        assert _read_variable(FakeDrawing(X=held), "X") == expected


class TestDrawingSetupLive:
    def test_scale_1_to_10_lands(self, drawing):
        """2026-10-28: 'could not convert string to float: ':'' — the old CANNOSCALE was split into letters."""
        import asyncio
        import json

        from autocad_mcp.tools import settings

        answer = asyncio.run(settings.autocad_drawing_setup(scale="1:10"))
        assert not answer.startswith("Error"), answer
        result = json.loads(answer)
        assert {"variable": "CANNOSCALE", "from": "1:1", "to": "1:10"} in result["changed"]
        assert drawing.variables["DIMSCALE"] == 10.0
        assert result["scale"] == "1:10"

    @pytest.mark.parametrize("given", [10, 10.0, "10", 2])
    def test_a_bare_number_above_one_is_refused_not_guessed(self, drawing, given):
        """scale=10 meant 1:10, but a bare number is a ratio, so it read as 10:1 (DIMSCALE 0.1)."""
        import asyncio

        from autocad_mcp.tools import settings

        answer = asyncio.run(settings.autocad_drawing_setup(scale=given))
        assert answer.startswith("Error"), answer
        assert "1:10" in answer or "1:2" in answer
        assert drawing.written == []


class TestCreateStylesLive:
    def test_a_dim_style_with_a_text_style(self, drawing):
        """2026-10-28: 'could not convert string to float: 'S'' — DIMTXSTY 'Standard' was split into letters."""
        import asyncio
        import json

        from autocad_mcp.tools import settings

        answer = asyncio.run(settings.autocad_create_styles(
            dim_styles=[{"name": "MEP-10", "scale": 10, "text_height": 2.5, "text_style": "ROMANS"}]
        ))
        assert not answer.startswith("Error"), answer
        row = json.loads(answer)["dim_styles"][0]
        assert row["created"] is True and "notes" not in row, row
        made = drawing.DimStyles.items[-1]
        assert made.copied["DIMTXSTY"] == "ROMANS"
        # The drawing's own settings are put back afterwards.
        assert drawing.variables["DIMTXSTY"] == "Standard"
        assert drawing.variables["DIMSCALE"] == 1.0

    def test_an_arrow_block_is_put_back_to_the_default_arrow(self, drawing):
        """DIMBLK reads back empty for the default arrow; AutoCAD's way to set that back is '.'."""
        import asyncio
        import json

        from autocad_mcp.tools import settings

        answer = asyncio.run(settings.autocad_create_styles(
            dim_styles=[{"name": "TICKS", "arrow_block": "_ArchTick"}]
        ))
        row = json.loads(answer)["dim_styles"][0]
        assert "notes" not in row, row
        assert drawing.DimStyles.items[-1].copied["DIMBLK"] == "_ArchTick"
        assert drawing.written[-1] == ("DIMBLK", ".")


class TestWholeNumberDimVariables:
    """AutoCAD refuses a decimal for a whole-number variable, so these go as whole numbers."""

    @pytest.mark.parametrize(
        ("option", "variable"),
        [("precision", "DIMDEC"), ("angle_precision", "DIMADEC"), ("unit_format", "DIMLUNIT"),
         ("suppress_zeros", "DIMZIN"), ("text_colour", "DIMCLRT"), ("line_colour", "DIMCLRD"),
         ("extension_colour", "DIMCLRE")],
    )
    def test_they_are_whole_numbers(self, option, variable):
        value = plan_dim_style({option: 2})[variable]
        assert value == 2 and type(value) is int

    @pytest.mark.parametrize("option", ["scale", "text_height", "arrow_size", "text_gap"])
    def test_lengths_stay_decimals(self, option):
        value = next(iter(plan_dim_style({option: 2}).values()))
        assert type(value) is float
