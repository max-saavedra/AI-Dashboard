"""
tests/unit/test_kpi_extractor.py

Unit tests for app/services/etl/kpi_extractor.py.
Verifies scalar KPI computation, dimension breakdowns, and trend detection.
"""

import pandas as pd
import pytest

from app.services.etl.kpi_extractor import (
    _compute_scalar_kpis,
    _compute_dimension_breakdowns,
    _compute_trends,
    _detect_trend,
    extract_kpis,
)
from app.services.etl.profiler import profile_dataframe


class TestScalarKPIs:
    def test_computes_sum_mean_max_min(self):
        df = pd.DataFrame({"revenue": ["100", "200", "300"]})
        result = _compute_scalar_kpis(df, ["revenue"])
        assert result["revenue"]["sum"] == pytest.approx(600.0)
        assert result["revenue"]["mean"] == pytest.approx(200.0)
        assert result["revenue"]["max"] == pytest.approx(300.0)
        assert result["revenue"]["min"] == pytest.approx(100.0)

    def test_skips_non_numeric_column(self):
        df = pd.DataFrame({"name": ["Alice", "Bob", "Charlie"]})
        result = _compute_scalar_kpis(df, ["name"])
        assert result == {}

    def test_handles_column_with_some_nulls(self):
        df = pd.DataFrame({"value": ["10", None, "20", None, "30"]})
        result = _compute_scalar_kpis(df, ["value"])
        assert result["value"]["sum"] == pytest.approx(60.0)
        assert result["value"]["count"] == 3


class TestDimensionBreakdowns:
    def test_groups_by_dimension(self):
        df = pd.DataFrame(
            {
                "region": ["North", "North", "South"],
                "sales": ["100", "150", "200"],
            }
        )
        result = _compute_dimension_breakdowns(df, ["region"], ["sales"])
        assert len(result) == 1
        north_sum = next(
            (d["value"] for d in result[0]["data"] if d["label"] == "North"), None
        )
        assert north_sum == pytest.approx(250.0)

    def test_limits_to_top_n(self):
        categories = [str(i) for i in range(20)]
        df = pd.DataFrame({"cat": categories, "val": ["1"] * 20})
        result = _compute_dimension_breakdowns(df, ["cat"], ["val"], top_n=5)
        assert len(result[0]["data"]) == 5

    def test_returns_empty_for_all_null_measure(self):
        df = pd.DataFrame({"region": ["A", "B"], "sales": [None, None]})
        result = _compute_dimension_breakdowns(df, ["region"], ["sales"])
        assert result == []


class TestTrendDetection:
    def test_detects_increasing_trend(self):
        series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        assert _detect_trend(series) == "increasing"

    def test_detects_decreasing_trend(self):
        series = pd.Series([5.0, 4.0, 3.0, 2.0, 1.0])
        assert _detect_trend(series) == "decreasing"

    def test_detects_stable_trend(self):
        series = pd.Series([10.0, 10.0, 10.0, 10.0, 10.0])
        assert _detect_trend(series) == "stable"

    def test_single_value_is_stable(self):
        series = pd.Series([42.0])
        assert _detect_trend(series) == "stable"


class TestExtractKPIs:
    def test_full_extraction_on_simple_dataframe(self, simple_dataframe: pd.DataFrame):
        profile = profile_dataframe(simple_dataframe)
        result = extract_kpis(simple_dataframe, profile, user_objective="Maximise sales")

        assert result["row_count"] == len(simple_dataframe)
        assert "sales" in result["kpis"]
        assert result["kpis"]["sales"]["sum"] == pytest.approx(6500.0)
        assert len(result["breakdowns"]) > 0
        assert result["user_objective"] == "Maximise sales"

    def test_extraction_without_objective(self, simple_dataframe: pd.DataFrame):
        profile = profile_dataframe(simple_dataframe)
        result = extract_kpis(simple_dataframe, profile)
        assert "user_objective" not in result

    def test_trends_built_for_date_columns(self, simple_dataframe: pd.DataFrame):
        profile = profile_dataframe(simple_dataframe)
        result = extract_kpis(simple_dataframe, profile)
        # The 'date' column should produce at least one trend entry
        assert len(result["trends"]) >= 1
