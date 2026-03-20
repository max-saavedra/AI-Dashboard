"""
app/services/dashboard/chart_builder.py

Generates a dynamic, frontend-ready chart configuration from the enriched
DatasetProfile and KPI payload (RF-05, UC-02).

The output is a list of ChartConfig objects that the Vue frontend can render
directly with ApexCharts / Chart.js without additional transformation.

Design principles:
  - Charts are fully determined by data shape, not hardcoded assumptions.
  - Each chart includes filter metadata so the frontend can build dynamic
    filter controls automatically (US-02).
  - All aggregation happens here; the frontend only renders.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from app.core.logging import get_logger
from app.services.etl.profiler import DatasetProfile

logger = get_logger(__name__)


@dataclass
class ChartSeries:
    """A single data series within a chart."""

    name: str
    data: list[Any]


@dataclass
class ChartConfig:
    """Frontend-ready chart specification."""

    id: str
    chart_type: str           # bar | line | pie | area | scatter | table
    title: str
    x_column: str
    y_column: str
    series: list[ChartSeries]
    categories: list[str]     # x-axis labels (for bar/line/area)
    filter_columns: list[str] # dimension columns usable as filters
    description: str = ""
    color_scheme: str = "default"
    is_time_series: bool = False
    aggregation: str = "sum"  # sum | mean | count

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_chart_configs(
    profile: DatasetProfile,
    kpi_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Generate a complete set of chart configurations for the dashboard.

    Combines:
      - AI-suggested charts (if schema agent ran successfully)
      - Heuristic fallback charts derived from column roles
      - Always includes a KPI summary card

    Returns a list of dicts ready to be stored as JSONB and served to
    the frontend.
    """
    charts: list[ChartConfig] = []
    filter_columns = _get_filter_columns(profile)

    # AI-suggested charts (added first as they are highest quality)
    ai_charts = getattr(profile, "suggested_charts", [])
    for suggestion in ai_charts:
        chart = _build_from_suggestion(
            suggestion, kpi_payload, filter_columns, profile
        )
        if chart:
            charts.append(chart)

    # Heuristic fallback charts for columns not yet covered
    covered_pairs = {(c.x_column, c.y_column) for c in charts}
    heuristic = _build_heuristic_charts(
        profile, kpi_payload, filter_columns, covered_pairs
    )
    charts.extend(heuristic)

    logger.info("charts_built", total=len(charts))
    return [c.to_dict() for c in charts]


# ------------------------------------------------------------------ #
# Internal helpers
# ------------------------------------------------------------------ #


def _get_filter_columns(profile: DatasetProfile) -> list[str]:
    """Return categorical / dimension column names suitable for filters."""
    return [
        col.name
        for col in profile.columns
        if col.suggested_role in ("dimension", "datetime")
    ]


def _build_from_suggestion(
    suggestion: dict[str, Any],
    kpi_payload: dict[str, Any],
    filter_columns: list[str],
    profile: DatasetProfile,
) -> Optional[ChartConfig]:
    """
    Convert an AI suggestion dict into a concrete ChartConfig with real data.
    Returns None when the referenced columns are not present in KPI data.
    """
    chart_type = suggestion.get("chart_type", "bar")
    x_col = suggestion.get("x_column", "")
    y_col = suggestion.get("y_column", "")
    title = suggestion.get("title", f"{y_col} by {x_col}")

    series, categories = _extract_series(kpi_payload, x_col, y_col, chart_type)
    if not series:
        return None

    is_time = _is_time_column(x_col, profile)
    chart_id = _make_id(chart_type, x_col, y_col)

    return ChartConfig(
        id=chart_id,
        chart_type=chart_type,
        title=title,
        x_column=x_col,
        y_column=y_col,
        series=series,
        categories=categories,
        filter_columns=filter_columns,
        description=suggestion.get("rationale", ""),
        is_time_series=is_time,
        aggregation="sum",
    )


def _build_heuristic_charts(
    profile: DatasetProfile,
    kpi_payload: dict[str, Any],
    filter_columns: list[str],
    covered_pairs: set[tuple[str, str]],
) -> list[ChartConfig]:
    """
    Generate sensible default charts for column combinations not yet covered.
    Priority order: time-series lines, dimension bars, category pies.
    """
    charts: list[ChartConfig] = []
    measures = [c.name for c in profile.columns if c.suggested_role == "measure"]
    datetimes = [c.name for c in profile.columns if c.suggested_role == "datetime"]
    dimensions = [c.name for c in profile.columns if c.suggested_role == "dimension"]

    # Line charts for time-series combinations
    for date_col in datetimes[:2]:
        for measure_col in measures[:3]:
            if (date_col, measure_col) in covered_pairs:
                continue
            series, categories = _extract_series(
                kpi_payload, date_col, measure_col, "line"
            )
            if series:
                charts.append(
                    ChartConfig(
                        id=_make_id("line", date_col, measure_col),
                        chart_type="line",
                        title=f"{_humanize(measure_col)} over Time",
                        x_column=date_col,
                        y_column=measure_col,
                        series=series,
                        categories=categories,
                        filter_columns=filter_columns,
                        is_time_series=True,
                        aggregation="sum",
                    )
                )
                covered_pairs.add((date_col, measure_col))

    # Bar charts for dimension × measure breakdowns
    for dim_col in dimensions[:3]:
        for measure_col in measures[:3]:
            if (dim_col, measure_col) in covered_pairs:
                continue
            series, categories = _extract_series(
                kpi_payload, dim_col, measure_col, "bar"
            )
            if series:
                charts.append(
                    ChartConfig(
                        id=_make_id("bar", dim_col, measure_col),
                        chart_type="bar",
                        title=f"{_humanize(measure_col)} by {_humanize(dim_col)}",
                        x_column=dim_col,
                        y_column=measure_col,
                        series=series,
                        categories=categories,
                        filter_columns=filter_columns,
                        aggregation="sum",
                    )
                )
                covered_pairs.add((dim_col, measure_col))

    # Pie chart for top dimension by first measure
    if dimensions and measures:
        dim_col, measure_col = dimensions[0], measures[0]
        if (dim_col, measure_col) not in covered_pairs:
            series, categories = _extract_series(
                kpi_payload, dim_col, measure_col, "pie"
            )
            if series:
                charts.append(
                    ChartConfig(
                        id=_make_id("pie", dim_col, measure_col),
                        chart_type="pie",
                        title=f"{_humanize(measure_col)} Distribution",
                        x_column=dim_col,
                        y_column=measure_col,
                        series=series,
                        categories=categories,
                        filter_columns=filter_columns,
                        aggregation="sum",
                    )
                )

    return charts


def _extract_series(
    kpi_payload: dict[str, Any],
    x_col: str,
    y_col: str,
    chart_type: str,
) -> tuple[list[ChartSeries], list[str]]:
    """
    Pull the matching breakdown or trend data from the KPI payload
    and format it as series + categories lists.
    Returns empty lists when no matching data is found.
    """
    # Check breakdowns (dimension × measure)
    for breakdown in kpi_payload.get("breakdowns", []):
        if breakdown["dimension"] == x_col and breakdown["measure"] == y_col:
            data_points = breakdown["data"]
            categories = [d["label"] for d in data_points]
            values = [d["value"] for d in data_points]
            series_name = _humanize(y_col)

            if chart_type == "pie":
                # Pie expects flat series of values
                return [ChartSeries(name=series_name, data=values)], categories
            return [ChartSeries(name=series_name, data=values)], categories

    # Check trends (datetime × measure)
    for trend in kpi_payload.get("trends", []):
        if trend["date_column"] == x_col and trend["measure"] == y_col:
            data_points = trend["data"]
            categories = [d["period"] for d in data_points]
            values = [d["value"] for d in data_points]
            return (
                [ChartSeries(name=_humanize(y_col), data=values)],
                categories,
            )

    return [], []


def _is_time_column(col_name: str, profile: DatasetProfile) -> bool:
    """Check whether a column is a datetime in the profile."""
    return any(
        c.name == col_name and c.suggested_role == "datetime"
        for c in profile.columns
    )


def _make_id(chart_type: str, x_col: str, y_col: str) -> str:
    """Generate a deterministic chart identifier."""
    return f"{chart_type}__{x_col}__{y_col}"


def _humanize(snake: str) -> str:
    """Convert snake_case to Title Case for display."""
    return snake.replace("_", " ").title()
