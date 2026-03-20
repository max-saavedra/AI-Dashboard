"""
app/services/dashboard/pdf_exporter.py

Generates a downloadable PDF executive summary using ReportLab (RF-03, US-03).

The PDF includes:
  - Title and metadata header
  - Dataset overview (row count, column list)
  - Key KPI table
  - Full executive summary text
"""

from __future__ import annotations

import io
from datetime import date
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core.logging import get_logger

logger = get_logger(__name__)

# Brand colours (neutral palette – replace for white-label deployments)
COLOR_PRIMARY = colors.HexColor("#1E3A5F")
COLOR_ACCENT = colors.HexColor("#2E86AB")
COLOR_LIGHT = colors.HexColor("#F4F6F8")


def export_summary_pdf(
    summary_text: str,
    kpi_payload: dict[str, Any],
    dataset_title: str = "Dataset Analysis",
) -> bytes:
    """
    Build a PDF document from the executive summary and KPI payload.

    Returns raw PDF bytes suitable for a FastAPI StreamingResponse.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2 * cm,
    )

    styles = _build_styles()
    story = []

    # Title block
    story.append(Paragraph(dataset_title, styles["report_title"]))
    story.append(
        Paragraph(f"Generated: {date.today().isoformat()}", styles["subtitle"])
    )
    story.append(Spacer(1, 0.5 * cm))

    # Dataset overview
    story.append(Paragraph("Dataset Overview", styles["section_heading"]))
    overview_data = _build_overview_table(kpi_payload)
    if overview_data:
        table = Table(overview_data, colWidths=[6 * cm, 10 * cm])
        table.setStyle(_overview_table_style())
        story.append(table)
    story.append(Spacer(1, 0.4 * cm))

    # KPI highlights
    story.append(Paragraph("Key Performance Indicators", styles["section_heading"]))
    kpi_data = _build_kpi_table(kpi_payload)
    if kpi_data:
        kpi_table = Table(kpi_data, colWidths=[5 * cm, 3 * cm, 3 * cm, 3 * cm, 3 * cm])
        kpi_table.setStyle(_kpi_table_style())
        story.append(kpi_table)
    story.append(Spacer(1, 0.4 * cm))

    # Executive summary body
    story.append(Paragraph("Executive Summary", styles["section_heading"]))
    for paragraph in summary_text.split("\n"):
        stripped = paragraph.strip()
        if stripped:
            story.append(Paragraph(stripped, styles["body_text"]))
            story.append(Spacer(1, 0.2 * cm))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    logger.info("pdf_exported", size_bytes=len(pdf_bytes))
    return pdf_bytes


# ------------------------------------------------------------------ #
# Internal helpers
# ------------------------------------------------------------------ #


def _build_styles() -> dict[str, ParagraphStyle]:
    """Define all paragraph styles used in the report."""
    base = getSampleStyleSheet()
    return {
        "report_title": ParagraphStyle(
            "report_title",
            parent=base["Title"],
            fontSize=20,
            textColor=COLOR_PRIMARY,
            spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            parent=base["Normal"],
            fontSize=9,
            textColor=colors.grey,
            spaceAfter=8,
        ),
        "section_heading": ParagraphStyle(
            "section_heading",
            parent=base["Heading2"],
            fontSize=12,
            textColor=COLOR_PRIMARY,
            spaceBefore=10,
            spaceAfter=4,
            borderPad=2,
        ),
        "body_text": ParagraphStyle(
            "body_text",
            parent=base["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.black,
        ),
    }


def _build_overview_table(kpi_payload: dict[str, Any]) -> list[list[str]]:
    """Build [label, value] rows for the dataset overview section."""
    rows = [["Metric", "Value"]]
    rows.append(["Total rows", str(kpi_payload.get("row_count", "—"))])
    measures = kpi_payload.get("measures", [])
    dimensions = kpi_payload.get("dimensions", [])
    rows.append(["Measure columns", ", ".join(measures) or "—"])
    rows.append(["Dimension columns", ", ".join(dimensions) or "—"])
    return rows


def _build_kpi_table(kpi_payload: dict[str, Any]) -> list[list[str]]:
    """Build a table of scalar KPIs: column | sum | mean | max | min."""
    rows = [["Column", "Sum", "Mean", "Max", "Min"]]
    for col_name, stats in kpi_payload.get("kpis", {}).items():
        rows.append(
            [
                col_name,
                _fmt(stats.get("sum")),
                _fmt(stats.get("mean")),
                _fmt(stats.get("max")),
                _fmt(stats.get("min")),
            ]
        )
    return rows if len(rows) > 1 else []


def _fmt(value: object) -> str:
    """Format a numeric value for display in the PDF table."""
    if value is None:
        return "—"
    try:
        f = float(value)  # type: ignore[arg-type]
        # Use integer display when there are no decimals
        return f"{f:,.0f}" if f == int(f) else f"{f:,.2f}"
    except (TypeError, ValueError):
        return str(value)


def _overview_table_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_LIGHT, colors.white]),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
    )


def _kpi_table_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_LIGHT, colors.white]),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
    )
