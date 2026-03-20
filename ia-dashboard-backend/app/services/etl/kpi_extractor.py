"""
app/services/etl/kpi_extractor.py

Extracts KPIs and aggregated metrics from a profiled DataFrame.

These aggregations are sent to the AI summary generator instead of raw data,
reducing token usage while preserving analytical value (DA section 2.3).

Supports:
  - Totals, averages, min/max for numeric columns
  - Period-over-period trend detection on date+numeric pairs
  - Top-N breakdown for categorical dimensions
  - Optional user-defined objective for context tagging
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np
import pandas as pd

from app.core.logging import get_logger
from app.services.etl.profiler import DatasetProfile

logger = get_logger(__name__)


def extract_kpis(
    df: pd.DataFrame,
    profile: DatasetProfile,
    user_objective: Optional[str] = None,
) -> dict[str, Any]:
    """
    Compute a structured KPI payload from the DataFrame.

    Args:
        df: cleaned DataFrame.
        profile: output of profiler.profile_dataframe.
        user_objective: optional plain-text goal entered by the user (UC-02).

    Returns:
        A dict that can be embedded into AI prompts and chart configurations.
    """
    measures = [c.name for c in profile.columns if c.suggested_role == "measure"]
    dimensions = [c.name for c in profile.columns if c.suggested_role == "dimension"]
    datetimes = [c.name for c in profile.columns if c.suggested_role == "datetime"]

    kpis = _compute_scalar_kpis(df, measures)
    breakdowns = _compute_dimension_breakdowns(df, dimensions, measures)
    trends = _compute_trends(df, datetimes, measures)

    payload: dict[str, Any] = {
        "row_count": len(df),
        "measures": measures,
        "dimensions": dimensions,
        "datetimes": datetimes,
        "kpis": kpis,
        "breakdowns": breakdowns,
        "trends": trends,
    }

    if user_objective:
        payload["user_objective"] = user_objective

    logger.info(
        "kpis_extracted",
        measures=len(measures),
        dimensions=len(dimensions),
        trends=len(trends),
    )
    return payload


# ------------------------------------------------------------------ #
# Internal helpers
# ------------------------------------------------------------------ #


def _compute_scalar_kpis(
    df: pd.DataFrame, measure_columns: list[str]
) -> dict[str, dict[str, float]]:
    """
    Compute sum, mean, max, min for each measure column.
    """
    result: dict[str, dict[str, float]] = {}
    for col in measure_columns:
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        if series.empty:
            continue
        result[col] = {
            "sum": round(float(series.sum()), 4),
            "mean": round(float(series.mean()), 4),
            "max": round(float(series.max()), 4),
            "min": round(float(series.min()), 4),
            "count": int(series.count()),
        }
    return result


def _compute_dimension_breakdowns(
    df: pd.DataFrame,
    dimension_columns: list[str],
    measure_columns: list[str],
    top_n: int = 10,
) -> list[dict[str, Any]]:
    """
    For each (dimension, measure) pair compute a top-N grouped aggregation.
    Useful for bar charts and pie charts.
    """
    breakdowns = []
    for dim in dimension_columns:
        for measure in measure_columns:
            try:
                numeric_series = pd.to_numeric(df[measure], errors="coerce")
                grouped = (
                    df.assign(**{measure: numeric_series})
                    .groupby(dim, dropna=True)[measure]
                    .sum()
                    .nlargest(top_n)
                )
                if grouped.empty:
                    continue
                breakdowns.append(
                    {
                        "dimension": dim,
                        "measure": measure,
                        "aggregation": "sum",
                        "data": [
                            {"label": str(k), "value": round(float(v), 4)}
                            for k, v in grouped.items()
                        ],
                    }
                )
            except Exception as exc:
                logger.warning(
                    "breakdown_failed", dim=dim, measure=measure, error=str(exc)
                )
    return breakdowns


def _compute_trends(
    df: pd.DataFrame,
    datetime_columns: list[str],
    measure_columns: list[str],
) -> list[dict[str, Any]]:
    """
    Build time-series aggregations for each (datetime, measure) pair.
    Automatically chooses monthly or daily resolution based on date range.
    """
    trends = []
    for date_col in datetime_columns:
        dates = pd.to_datetime(df[date_col], errors="coerce")
        if dates.isna().all():
            continue

        # Choose aggregation frequency
        date_range_days = (dates.max() - dates.min()).days
        freq = "ME" if date_range_days > 60 else "D"

        for measure in measure_columns:
            try:
                numeric = pd.to_numeric(df[measure], errors="coerce")
                ts = (
                    pd.DataFrame({"date": dates, "value": numeric})
                    .dropna()
                    .set_index("date")
                    .resample(freq)["value"]
                    .sum()
                )
                if ts.empty:
                    continue

                trend_direction = _detect_trend(ts)
                trends.append(
                    {
                        "date_column": date_col,
                        "measure": measure,
                        "frequency": freq,
                        "trend_direction": trend_direction,
                        "data": [
                            {
                                "period": str(k.date()),
                                "value": round(float(v), 4),
                            }
                            for k, v in ts.items()
                        ],
                    }
                )
            except Exception as exc:
                logger.warning(
                    "trend_failed",
                    date_col=date_col,
                    measure=measure,
                    error=str(exc),
                )
    return trends


def _detect_trend(series: pd.Series) -> str:
    """
    Use a simple linear regression slope to classify the trend.
    Returns "increasing", "decreasing", or "stable".
    """
    if len(series) < 2:
        return "stable"

    x = np.arange(len(series), dtype=float)
    y = series.values.astype(float)
    slope = float(np.polyfit(x, y, 1)[0])

    mean_abs = abs(y).mean()
    if mean_abs == 0:
        return "stable"

    relative_slope = slope / mean_abs
    if relative_slope > 0.01:
        return "increasing"
    if relative_slope < -0.01:
        return "decreasing"
    return "stable"
