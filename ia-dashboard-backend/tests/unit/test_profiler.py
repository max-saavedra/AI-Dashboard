"""
tests/unit/test_profiler.py

Unit tests for app/services/etl/profiler.py.
Verifies type inference, role assignment, and stats computation.
"""

import pandas as pd
import pytest

from app.services.etl.profiler import (
    _infer_type,
    _suggest_role,
    profile_dataframe,
)


class TestTypeInference:
    def test_numeric_column(self):
        series = pd.Series(["100", "200.5", "300", "400"])
        assert _infer_type(series, 4, 4) == "numeric"

    def test_date_column(self):
        series = pd.Series(["2024-01-01", "2024-02-01", "2024-03-01"])
        assert _infer_type(series, 3, 3) == "date"

    def test_categorical_column(self):
        # Low cardinality relative to row count → categorical
        series = pd.Series(["A", "B", "A", "B", "A", "B", "A", "B", "A", "B"])
        assert _infer_type(series, 2, 10) == "categorical"

    def test_text_column(self):
        # High cardinality text
        series = pd.Series([f"unique_value_{i}" for i in range(100)])
        assert _infer_type(series, 100, 100) == "text"

    def test_empty_series_returns_text(self):
        series = pd.Series([], dtype=str)
        assert _infer_type(series, 0, 0) == "text"

    def test_mixed_column_with_few_nulls_stays_numeric(self):
        # 80% parseable → still numeric
        series = pd.Series(["10", "20", "30", "40", "not_a_number"])
        assert _infer_type(series, 5, 5) == "numeric"


class TestRoleAssignment:
    def test_numeric_becomes_measure(self):
        assert _suggest_role("numeric", 100, 100) == "measure"

    def test_date_becomes_datetime(self):
        assert _suggest_role("date", 12, 100) == "datetime"

    def test_categorical_becomes_dimension(self):
        assert _suggest_role("categorical", 5, 100) == "dimension"

    def test_high_cardinality_text_becomes_label(self):
        # unique_count / total > 0.5 → label
        assert _suggest_role("text", 90, 100) == "label"

    def test_low_cardinality_text_becomes_dimension(self):
        assert _suggest_role("text", 3, 100) == "dimension"


class TestProfileDataframe:
    def test_profiles_all_columns(self, simple_dataframe: pd.DataFrame):
        profile = profile_dataframe(simple_dataframe)
        assert profile.column_count == len(simple_dataframe.columns)
        assert profile.row_count == len(simple_dataframe)

    def test_correct_type_for_numeric_column(self, simple_dataframe: pd.DataFrame):
        profile = profile_dataframe(simple_dataframe)
        sales_col = next(c for c in profile.columns if c.name == "sales")
        assert sales_col.inferred_type == "numeric"
        assert sales_col.suggested_role == "measure"

    def test_correct_type_for_categorical_column(self, simple_dataframe: pd.DataFrame):
        profile = profile_dataframe(simple_dataframe)
        region_col = next(c for c in profile.columns if c.name == "region")
        assert region_col.inferred_type == "categorical"
        assert region_col.suggested_role == "dimension"

    def test_null_rate_is_zero_for_complete_column(self, simple_dataframe: pd.DataFrame):
        profile = profile_dataframe(simple_dataframe)
        for col in profile.columns:
            assert col.null_rate == 0.0

    def test_stats_populated_for_numeric_column(self, simple_dataframe: pd.DataFrame):
        profile = profile_dataframe(simple_dataframe)
        sales_col = next(c for c in profile.columns if c.name == "sales")
        assert "sum" in sales_col.stats
        assert "mean" in sales_col.stats
        assert sales_col.stats["sum"] == pytest.approx(6500.0)

    def test_to_ai_payload_limits_sample_rows(self, simple_dataframe: pd.DataFrame):
        profile = profile_dataframe(simple_dataframe)
        payload = profile.to_ai_payload(sample_rows=3)
        for col_meta in payload["columns"]:
            assert len(col_meta["sample_values"]) <= 3
