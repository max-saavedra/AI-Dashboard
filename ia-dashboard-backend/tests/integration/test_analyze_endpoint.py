"""
tests/integration/test_analyze_endpoint.py

Integration tests for POST /api/v1/analyze.
Uses the real FastAPI app with an in-memory SQLite database and
a mocked AI orchestrator to avoid external API calls.
"""

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest
import pytest_asyncio
from httpx import AsyncClient


ANALYZE_URL = "/api/v1/analyze"


def _make_excel_bytes(rows: int = 5) -> bytes:
    """Build a minimal valid .xlsx file in memory."""
    df = pd.DataFrame(
        {
            "Region": ["North", "South", "East", "West", "Central"][:rows],
            "Revenue": [1000, 1500, 800, 2000, 1200][:rows],
            "Units": [10, 15, 8, 20, 12][:rows],
            "Month": ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05"][:rows],
        }
    )
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()


def _mock_schema_response() -> dict:
    """Canned AI schema response so tests don't call Gemini/OpenAI."""
    return {
        "columns": [
            {"name": "region", "alias": "Region", "type": "categorical", "role": "dimension", "format_hint": "text"},
            {"name": "revenue", "alias": "Revenue", "type": "numeric", "role": "measure", "format_hint": "currency"},
            {"name": "units", "alias": "Units", "type": "numeric", "role": "measure", "format_hint": "integer"},
            {"name": "month", "alias": "Month", "type": "date", "role": "datetime", "format_hint": "date"},
        ],
        "suggested_charts": [
            {
                "chart_type": "bar",
                "x_column": "region",
                "y_column": "revenue",
                "title": "Revenue by Region",
                "rationale": "Compare revenue across regions.",
            },
            {
                "chart_type": "line",
                "x_column": "month",
                "y_column": "revenue",
                "title": "Revenue over Time",
                "rationale": "Show monthly trend.",
            },
            {
                "chart_type": "pie",
                "x_column": "region",
                "y_column": "units",
                "title": "Units Distribution",
                "rationale": "Show proportion of units per region.",
            },
        ],
        "dataset_summary": "A sales dataset with regional revenue and unit data.",
    }


@pytest.mark.asyncio
class TestAnalyzeEndpointHappyPath:
    async def test_returns_200_for_valid_excel(self, async_client: AsyncClient):
        with patch(
            "app.api.v1.endpoints.analyze._orchestrator"
        ) as mock_orc:
            mock_orc.complete_json = AsyncMock(return_value=_mock_schema_response())

            files = {"file": ("sales.xlsx", _make_excel_bytes(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            response = await async_client.post(ANALYZE_URL, files=files)

        assert response.status_code == 200

    async def test_response_contains_required_fields(self, async_client: AsyncClient):
        with patch("app.api.v1.endpoints.analyze._orchestrator") as mock_orc:
            mock_orc.complete_json = AsyncMock(return_value=_mock_schema_response())

            files = {"file": ("data.xlsx", _make_excel_bytes(), "application/octet-stream")}
            response = await async_client.post(ANALYZE_URL, files=files)

        body = response.json()
        assert "dashboard_id" in body
        assert "columns" in body
        assert "kpis" in body
        assert "chart_configs" in body
        assert "row_count" in body

    async def test_row_count_matches_file(self, async_client: AsyncClient):
        with patch("app.api.v1.endpoints.analyze._orchestrator") as mock_orc:
            mock_orc.complete_json = AsyncMock(return_value=_mock_schema_response())

            files = {"file": ("data.xlsx", _make_excel_bytes(rows=5), "application/octet-stream")}
            response = await async_client.post(ANALYZE_URL, files=files)

        assert response.json()["row_count"] == 5

    async def test_user_objective_is_accepted(self, async_client: AsyncClient):
        with patch("app.api.v1.endpoints.analyze._orchestrator") as mock_orc:
            mock_orc.complete_json = AsyncMock(return_value=_mock_schema_response())

            files = {"file": ("data.xlsx", _make_excel_bytes(), "application/octet-stream")}
            data = {"user_objective": "Increase Q4 revenue"}
            response = await async_client.post(ANALYZE_URL, files=files, data=data)

        assert response.status_code == 200

    async def test_valid_csv_is_accepted(self, async_client: AsyncClient, csv_bytes_clean: bytes):
        with patch("app.api.v1.endpoints.analyze._orchestrator") as mock_orc:
            mock_orc.complete_json = AsyncMock(return_value={
                "columns": [], "suggested_charts": [], "dataset_summary": "CSV dataset."
            })

            files = {"file": ("data.csv", csv_bytes_clean, "text/csv")}
            response = await async_client.post(ANALYZE_URL, files=files)

        assert response.status_code == 200


@pytest.mark.asyncio
class TestAnalyzeEndpointValidation:
    async def test_rejects_unsupported_file_format(self, async_client: AsyncClient):
        files = {"file": ("report.pdf", b"%PDF-1.4", "application/pdf")}
        response = await async_client.post(ANALYZE_URL, files=files)
        assert response.status_code == 422

    async def test_rejects_oversized_file(self, async_client: AsyncClient):
        oversized = b"\x00" * (11 * 1024 * 1024)
        files = {"file": ("big.csv", oversized, "text/csv")}
        response = await async_client.post(ANALYZE_URL, files=files)
        assert response.status_code == 413

    async def test_rejects_empty_csv(self, async_client: AsyncClient):
        files = {"file": ("empty.csv", b"col1,col2\n", "text/csv")}
        response = await async_client.post(ANALYZE_URL, files=files)
        assert response.status_code == 422

    async def test_chart_configs_are_list(self, async_client: AsyncClient):
        with patch("app.api.v1.endpoints.analyze._orchestrator") as mock_orc:
            mock_orc.complete_json = AsyncMock(return_value=_mock_schema_response())

            files = {"file": ("data.xlsx", _make_excel_bytes(), "application/octet-stream")}
            response = await async_client.post(ANALYZE_URL, files=files)

        assert isinstance(response.json()["chart_configs"], list)
