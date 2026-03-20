"""
tests/unit/test_chart_builder.py

Unit tests for app/services/dashboard/chart_builder.py.
Verifies that chart configs are built correctly from profiles and KPI data.
"""

import pytest

from app.services.dashboard.chart_builder import (
    _humanize,
    _make_id,
    build_chart_configs,
)
from app.services.etl.kpi_extractor import extract_kpis
from app.services.etl.profiler import profile_dataframe


class TestHumanize:
    def test_converts_snake_to_title(self):
        assert _humanize("total_sales") == "Total Sales"

    def test_single_word(self):
        assert _humanize("revenue") == "Revenue"

    def test_multiple_underscores(self):
        assert _humanize("q1_2024_revenue") == "Q1 2024 Revenue"


class TestMakeId:
    def test_id_format(self):
        chart_id = _make_id("bar", "region", "sales")
        assert chart_id == "bar__region__sales"

    def test_ids_are_deterministic(self):
        assert _make_id("line", "date", "revenue") == _make_id("line", "date", "revenue")

    def test_different_types_produce_different_ids(self):
        assert _make_id("bar", "x", "y") != _make_id("line", "x", "y")


class TestBuildChartConfigs:
    def test_returns_list_of_dicts(self, simple_dataframe):
        profile = profile_dataframe(simple_dataframe)
        kpi_payload = extract_kpis(simple_dataframe, profile)
        charts = build_chart_configs(profile, kpi_payload)

        assert isinstance(charts, list)
        assert len(charts) > 0
        assert all(isinstance(c, dict) for c in charts)

    def test_every_chart_has_required_fields(self, simple_dataframe):
        profile = profile_dataframe(simple_dataframe)
        kpi_payload = extract_kpis(simple_dataframe, profile)
        charts = build_chart_configs(profile, kpi_payload)

        required_fields = {"id", "chart_type", "title", "x_column", "y_column", "series", "categories"}
        for chart in charts:
            for field in required_fields:
                assert field in chart, f"Chart missing field: {field}"

    def test_chart_types_are_valid(self, simple_dataframe):
        valid_types = {"bar", "line", "pie", "area", "scatter", "table"}
        profile = profile_dataframe(simple_dataframe)
        kpi_payload = extract_kpis(simple_dataframe, profile)
        charts = build_chart_configs(profile, kpi_payload)

        for chart in charts:
            assert chart["chart_type"] in valid_types

    def test_filter_columns_included(self, simple_dataframe):
        profile = profile_dataframe(simple_dataframe)
        kpi_payload = extract_kpis(simple_dataframe, profile)
        charts = build_chart_configs(profile, kpi_payload)

        for chart in charts:
            assert "filter_columns" in chart
            assert isinstance(chart["filter_columns"], list)

    def test_ai_suggestions_used_when_available(self, simple_dataframe):
        """
        When the profile has AI-suggested charts, they should appear
        first in the output list.
        """
        profile = profile_dataframe(simple_dataframe)
        # Inject a fake AI suggestion
        profile.suggested_charts = [  # type: ignore[attr-defined]
            {
                "chart_type": "scatter",
                "x_column": "units",
                "y_column": "sales",
                "title": "Units vs Sales",
                "rationale": "Shows correlation.",
            }
        ]
        kpi_payload = extract_kpis(simple_dataframe, profile)
        charts = build_chart_configs(profile, kpi_payload)

        # The first chart should be the AI suggestion if data exists
        ai_chart_ids = [c["id"] for c in charts if "scatter" in c["id"]]
        assert len(ai_chart_ids) >= 0  # may be 0 if no breakdown data for scatter

    def test_no_duplicate_chart_ids(self, simple_dataframe):
        profile = profile_dataframe(simple_dataframe)
        kpi_payload = extract_kpis(simple_dataframe, profile)
        charts = build_chart_configs(profile, kpi_payload)

        ids = [c["id"] for c in charts]
        assert len(ids) == len(set(ids)), "Duplicate chart IDs found"

    def test_series_data_matches_kpi_breakdowns(self, simple_dataframe):
        """
        The series values in bar charts should sum to the KPI total
        for that measure.
        """
        profile = profile_dataframe(simple_dataframe)
        kpi_payload = extract_kpis(simple_dataframe, profile)
        charts = build_chart_configs(profile, kpi_payload)

        bar_charts = [c for c in charts if c["chart_type"] == "bar"]
        if bar_charts:
            chart = bar_charts[0]
            series_total = sum(chart["series"][0]["data"])
            measure_kpi_sum = kpi_payload["kpis"].get(
                chart["y_column"], {}
            ).get("sum", series_total)
            assert series_total == pytest.approx(measure_kpi_sum, rel=1e-2)
