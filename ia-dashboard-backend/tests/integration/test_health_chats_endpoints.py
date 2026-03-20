"""
tests/integration/test_health_chats_endpoints.py

Integration tests for:
  GET  /api/v1/health
  GET  /api/v1/chats
  PATCH /api/v1/chats/{chat_id}
  DELETE /api/v1/chats/{chat_id}
"""

import uuid
from unittest.mock import MagicMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TokenPayload
from app.models.database import Chat
from app.core.dependencies import optional_current_user, require_current_user
from app.main import app


# ------------------------------------------------------------------ #
# Health endpoint
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
class TestHealthEndpoint:
    async def test_returns_200(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200

    async def test_returns_status_ok(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/health")
        assert response.json()["status"] == "ok"

    async def test_returns_version(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/health")
        assert "version" in response.json()


# ------------------------------------------------------------------ #
# Chats endpoints (require authentication)
# ------------------------------------------------------------------ #


def _inject_user(user_id: str) -> None:
    """Override the auth dependency to simulate an authenticated user."""
    mock_user = TokenPayload(sub=user_id, email="test@example.com")
    app.dependency_overrides[optional_current_user] = lambda: mock_user
    app.dependency_overrides[require_current_user] = lambda: mock_user


def _clear_auth_overrides() -> None:
    app.dependency_overrides.pop(optional_current_user, None)
    app.dependency_overrides.pop(require_current_user, None)


async def _insert_chat(db: AsyncSession, user_id: str, name: str = "Test Chat") -> Chat:
    chat = Chat(id=uuid.uuid4(), user_id=uuid.UUID(user_id), name=name)
    db.add(chat)
    await db.flush()
    return chat


@pytest.mark.asyncio
class TestListChats:
    async def test_returns_empty_list_for_new_user(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        user_id = str(uuid.uuid4())
        _inject_user(user_id)
        try:
            response = await async_client.get("/api/v1/chats")
            assert response.status_code == 200
            assert response.json() == []
        finally:
            _clear_auth_overrides()

    async def test_returns_user_chats(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        user_id = str(uuid.uuid4())
        await _insert_chat(db_session, user_id, "Sales Analysis")
        await _insert_chat(db_session, user_id, "HR Report")
        _inject_user(user_id)
        try:
            response = await async_client.get("/api/v1/chats")
            assert response.status_code == 200
            names = [c["name"] for c in response.json()]
            assert "Sales Analysis" in names
            assert "HR Report" in names
        finally:
            _clear_auth_overrides()

    async def test_requires_authentication(self, async_client: AsyncClient):
        # No auth override → anonymous request → 401
        response = await async_client.get("/api/v1/chats")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestRenameChat:
    async def test_renames_own_chat(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        user_id = str(uuid.uuid4())
        chat = await _insert_chat(db_session, user_id, "Old Name")
        _inject_user(user_id)
        try:
            response = await async_client.patch(
                f"/api/v1/chats/{chat.id}",
                json={"name": "New Name"},
            )
            assert response.status_code == 200
            assert response.json()["name"] == "New Name"
        finally:
            _clear_auth_overrides()

    async def test_cannot_rename_another_users_chat(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        owner_id = str(uuid.uuid4())
        attacker_id = str(uuid.uuid4())
        chat = await _insert_chat(db_session, owner_id, "Private Chat")
        _inject_user(attacker_id)
        try:
            response = await async_client.patch(
                f"/api/v1/chats/{chat.id}",
                json={"name": "Hacked"},
            )
            assert response.status_code == 403
        finally:
            _clear_auth_overrides()


@pytest.mark.asyncio
class TestDeleteChat:
    async def test_deletes_own_chat(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        user_id = str(uuid.uuid4())
        chat = await _insert_chat(db_session, user_id)
        _inject_user(user_id)
        try:
            response = await async_client.delete(f"/api/v1/chats/{chat.id}")
            assert response.status_code == 204
        finally:
            _clear_auth_overrides()

    async def test_returns_404_for_nonexistent_chat(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        user_id = str(uuid.uuid4())
        _inject_user(user_id)
        try:
            response = await async_client.delete(f"/api/v1/chats/{uuid.uuid4()}")
            assert response.status_code == 404
        finally:
            _clear_auth_overrides()
