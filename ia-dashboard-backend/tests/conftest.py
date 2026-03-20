"""
tests/conftest.py

Shared pytest fixtures used across unit and integration tests.
Uses an in-memory SQLite database for integration tests so no external
services are required to run the test suite.
"""

import io
import uuid
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.main import app
from app.models.database import Base
from app.models.session import get_db

# ------------------------------------------------------------------ #
# In-memory test database (no external Postgres required)
# ------------------------------------------------------------------ #

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_tables():
    """Create all tables once per test session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional test session that rolls back after each test."""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client with the test DB injected.
    All requests hit the real FastAPI app but use the in-memory database.
    """
    app.dependency_overrides[get_db] = lambda: db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


# ------------------------------------------------------------------ #
# Reusable data fixtures
# ------------------------------------------------------------------ #


@pytest.fixture
def simple_dataframe() -> pd.DataFrame:
    """A clean, well-typed DataFrame for tests that skip file I/O."""
    return pd.DataFrame(
        {
            "region": ["North", "South", "East", "West", "North"],
            "product": ["A", "B", "A", "C", "B"],
            "sales": [1000.0, 1500.0, 800.0, 2000.0, 1200.0],
            "units": [10, 15, 8, 20, 12],
            "date": ["2024-01-01", "2024-02-01", "2024-03-01", "2024-04-01", "2024-05-01"],
        }
    )


@pytest.fixture
def excel_bytes_clean() -> bytes:
    """Minimal valid .xlsx bytes built with openpyxl via pandas."""
    df = pd.DataFrame(
        {
            "Category": ["A", "B", "C"],
            "Revenue": [100, 200, 300],
            "Month": ["2024-01", "2024-02", "2024-03"],
        }
    )
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()


@pytest.fixture
def excel_bytes_with_offset() -> bytes:
    """
    .xlsx bytes that include 3 empty header rows (offset) before the real table.
    Tests the offset-detection heuristic in the cleaner.
    """
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    # 3 empty rows (offset)
    for _ in range(3):
        ws.append([None, None, None])
    # Actual header
    ws.append(["Product", "Sales", "Year"])
    # Data rows
    ws.append(["Widget", 500, 2024])
    ws.append(["Gadget", 750, 2024])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.fixture
def csv_bytes_clean() -> bytes:
    """Simple UTF-8 CSV bytes."""
    return b"name,score,category\nAlice,90,A\nBob,75,B\nCharlie,85,A\n"


@pytest.fixture
def mock_orchestrator() -> MagicMock:
    """
    A mock AIOrchestrator that returns predictable JSON responses
    without making real API calls.
    """
    orchestrator = MagicMock()
    orchestrator.complete = AsyncMock(return_value="Mocked AI response.")
    orchestrator.complete_json = AsyncMock(
        return_value={
            "columns": [],
            "suggested_charts": [
                {
                    "chart_type": "bar",
                    "x_column": "category",
                    "y_column": "score",
                    "title": "Score by Category",
                    "rationale": "Shows distribution across categories.",
                }
            ],
            "dataset_summary": "A test dataset with names and scores.",
        }
    )
    return orchestrator
