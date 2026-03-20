"""
tests/integration/test_summary_chat_endpoints.py

Integration tests for:
  POST /api/v1/summary
  GET  /api/v1/summary/{id}/pdf
  POST /api/v1/chat

These tests inject a pre-built Dashboard directly into the database
to isolate the summary and chat logic from the ETL pipeline.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Chat, Dashboard


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #


async def _insert_dashboard(db: AsyncSession, with_summary: bool = False) -> str:
    """Insert a Chat + Dashboard row and return the dashboard_id as a string."""
    chat = Chat(id=uuid.uuid4(), user_id=None, name="Test Chat")
    db.add(chat)
    await db.flush()

    ai_insights: dict = {"dataset_summary": "A test sales dataset."}
    if with_summary:
        ai_insights["executive_summary"] = "Revenue grew 20% YoY."

    dashboard = Dashboard(
        id=uuid.uuid4(),
        chat_id=chat.id,
        cleaned_data={"records": []},
        kpi_data={
            "row_count": 10,
            "measures": ["revenue"],
            "dimensions": ["region"],
            "datetimes": [],
            "kpis": {"revenue": {"sum": 5000.0, "mean": 500.0, "max": 1000.0, "min": 100.0}},
            "breakdowns": [],
            "trends": [],
        },
        ai_insights=ai_insights,
        chart_config=[],
        metadata={"filename": "test.xlsx", "tags": []},
    )
    db.add(dashboard)
    await db.flush()
    return str(dashboard.id)


# ------------------------------------------------------------------ #
# Summary endpoint
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
class TestSummaryEndpoint:
    async def test_generates_summary_for_existing_dashboard(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        dashboard_id = await _insert_dashboard(db_session)

        with patch("app.api.v1.endpoints.summary._orchestrator") as mock_orc:
            mock_orc.complete = AsyncMock(return_value="Revenue grew 15% in Q4.")

            response = await async_client.post(
                "/api/v1/summary",
                json={"dashboard_id": dashboard_id},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["summary"] == "Revenue grew 15% in Q4."
        assert body["dashboard_id"] == dashboard_id

    async def test_includes_tags_in_request(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        dashboard_id = await _insert_dashboard(db_session)

        with patch("app.api.v1.endpoints.summary._orchestrator") as mock_orc:
            mock_orc.complete = AsyncMock(return_value="Focused summary.")

            response = await async_client.post(
                "/api/v1/summary",
                json={
                    "dashboard_id": dashboard_id,
                    "tags": ["revenue", "growth"],
                    "user_objective": "Understand Q4 performance",
                },
            )

        assert response.status_code == 200
        mock_orc.complete.assert_called_once()
        # Verify the prompt passed to the AI contains the tags
        prompt_used = mock_orc.complete.call_args[0][0]
        assert "revenue" in prompt_used
        assert "growth" in prompt_used

    async def test_returns_404_for_unknown_dashboard(self, async_client: AsyncClient):
        response = await async_client.post(
            "/api/v1/summary",
            json={"dashboard_id": str(uuid.uuid4())},
        )
        assert response.status_code == 404

    async def test_returns_422_for_invalid_uuid(self, async_client: AsyncClient):
        response = await async_client.post(
            "/api/v1/summary",
            json={"dashboard_id": "not-a-uuid"},
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestSummaryPDFEndpoint:
    async def test_returns_pdf_bytes(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        dashboard_id = await _insert_dashboard(db_session, with_summary=True)

        response = await async_client.get(f"/api/v1/summary/{dashboard_id}/pdf")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content[:4] == b"%PDF"

    async def test_returns_404_when_no_summary_generated(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        dashboard_id = await _insert_dashboard(db_session, with_summary=False)

        response = await async_client.get(f"/api/v1/summary/{dashboard_id}/pdf")
        assert response.status_code == 404


# ------------------------------------------------------------------ #
# Chat Q&A endpoint
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
class TestChatEndpoint:
    async def test_answers_question_about_dataset(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        dashboard_id = await _insert_dashboard(db_session)

        with patch("app.api.v1.endpoints.chat._orchestrator") as mock_orc:
            mock_orc.complete = AsyncMock(return_value="The total revenue is 5000.")

            response = await async_client.post(
                "/api/v1/chat",
                json={
                    "dashboard_id": dashboard_id,
                    "question": "What is the total revenue?",
                    "history": [],
                },
            )

        assert response.status_code == 200
        body = response.json()
        assert body["answer"] == "The total revenue is 5000."
        assert body["question"] == "What is the total revenue?"

    async def test_accepts_conversation_history(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        dashboard_id = await _insert_dashboard(db_session)

        history = [
            {"role": "user", "content": "What is the max?"},
            {"role": "assistant", "content": "The max revenue is 1000."},
        ]

        with patch("app.api.v1.endpoints.chat._orchestrator") as mock_orc:
            mock_orc.complete = AsyncMock(return_value="The min is 100.")

            response = await async_client.post(
                "/api/v1/chat",
                json={
                    "dashboard_id": dashboard_id,
                    "question": "And the minimum?",
                    "history": history,
                },
            )

        assert response.status_code == 200

    async def test_rejects_empty_question(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        dashboard_id = await _insert_dashboard(db_session)

        response = await async_client.post(
            "/api/v1/chat",
            json={"dashboard_id": dashboard_id, "question": "", "history": []},
        )
        assert response.status_code == 422

    async def test_returns_404_for_unknown_dashboard(self, async_client: AsyncClient):
        response = await async_client.post(
            "/api/v1/chat",
            json={
                "dashboard_id": str(uuid.uuid4()),
                "question": "What is the total?",
                "history": [],
            },
        )
        assert response.status_code == 404
