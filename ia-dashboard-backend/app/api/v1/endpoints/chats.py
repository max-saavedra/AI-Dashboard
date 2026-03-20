"""
app/api/v1/endpoints/chats.py

GET    /api/v1/chats              – list user's analysis sessions (UC-03)
DELETE /api/v1/chats/{chat_id}   – delete a chat and all its dashboards
PATCH  /api/v1/chats/{chat_id}   – rename a chat

Persistence requires authentication (RF-04, RNF-08).
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import require_current_user
from app.core.logging import get_logger
from app.core.security import TokenPayload
from app.models.database import Chat
from app.models.session import get_db
from app.schemas.analysis import ChatSessionSummary, RenameChatRequest

router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "/chats",
    response_model=list[ChatSessionSummary],
    summary="List all analysis sessions for the authenticated user",
)
async def list_chats(
    current_user: TokenPayload = Depends(require_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ChatSessionSummary]:
    """
    Return all chat sessions for the current user, ordered newest first (UC-03).
    """
    logger.info('DEBUG: list_chats endpoint accessed \n', user_id=current_user.sub, email=current_user.email)

    result = await db.execute(
        select(Chat)
        .options(selectinload(Chat.dashboards))
        .where(Chat.user_id == uuid.UUID(current_user.sub))
        .order_by(Chat.created_at.desc())
    )
    chats = result.scalars().all()

    logger.info('DEBUG: Retrieved chats from database\n', count=len(chats), user_id=current_user.sub)

    return [
        ChatSessionSummary(
            chat_id=str(chat.id),
            name=chat.name,
            created_at=chat.created_at.isoformat(),
            dashboard_count=len(chat.dashboards),
        )
        for chat in chats
    ]


@router.patch(
    "/chats/{chat_id}",
    response_model=ChatSessionSummary,
    summary="Rename an analysis session",
)
async def rename_chat(
    chat_id: str,
    body: RenameChatRequest,
    current_user: TokenPayload = Depends(require_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatSessionSummary:
    """Rename a chat session. Only the owner may rename it (RNF-08)."""
    chat = await _get_owned_chat(db, chat_id, current_user.sub)
    chat.name = body.name
    await db.flush()

    return ChatSessionSummary(
        chat_id=str(chat.id),
        name=chat.name,
        created_at=chat.created_at.isoformat(),
        dashboard_count=len(chat.dashboards),
    )


@router.delete(
    "/chats/{chat_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a chat session and all its dashboards",
)
async def delete_chat(
    chat_id: str,
    current_user: TokenPayload = Depends(require_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Permanently delete a chat and cascade-delete all associated dashboards.
    Only the owner may delete it (RNF-08, US-04 AC3 – full CRUD).
    """
    chat = await _get_owned_chat(db, chat_id, current_user.sub)
    await db.delete(chat)
    await db.flush()
    logger.info("chat_deleted", chat_id=chat_id, user_id=current_user.sub)


# ------------------------------------------------------------------ #
# Shared helper
# ------------------------------------------------------------------ #


async def _get_owned_chat(
    db: AsyncSession, chat_id: str, user_id: str
) -> Chat:
    """Load a chat and verify ownership. Raises 404 or 403 as appropriate."""
    try:
        parsed_id = uuid.UUID(chat_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid chat ID format.",
        )

    chat = await db.get(Chat, parsed_id, options=[selectinload(Chat.dashboards)])
    if chat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found.")

    if str(chat.user_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return chat
