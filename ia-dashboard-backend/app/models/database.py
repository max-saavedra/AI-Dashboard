"""
app/models/database.py

SQLAlchemy ORM models mirroring the PostgreSQL schema defined in DA.md.
JSONB columns use the postgresql dialect for flexible semi-structured storage.

Tables:
  - users   (managed by Supabase Auth, referenced here for FK integrity)
  - chats   (analysis session threads, RF-04)
  - dashboards (core analytical entity with JSONB payloads)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    """
    Mirrors the Supabase Auth users table.
    Not created by the application – managed externally.
    Declared here only for FK relationships.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False)

    chats: Mapped[list["Chat"]] = relationship(
        "Chat", back_populates="user", cascade="all, delete-orphan"
    )


class Chat(Base):
    """
    An analysis session thread (RF-04).
    user_id is nullable to support anonymous sessions (RNF-05).
    """

    __tablename__ = "chats"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(120), nullable=False, default="New Analysis")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=_utcnow,
        nullable=False,
    )

    user: Mapped["User | None"] = relationship("User", back_populates="chats")
    dashboards: Mapped[list["Dashboard"]] = relationship(
        "Dashboard", back_populates="chat", cascade="all, delete-orphan"
    )


class Dashboard(Base):
    """
    Core analytical entity (DA section 3).
    All dynamic payloads (cleaned data, AI insights, chart config) are stored
    as JSONB for schema flexibility.
    """

    __tablename__ = "dashboards"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    chat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Cleaned dataset serialised as JSON records (orient="records")
    cleaned_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # KPI payload from kpi_extractor
    kpi_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # AI-generated insights and executive summary
    ai_insights: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict)

    # Chart configurations from chart_builder
    chart_config: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list)

    # File metadata, enriched schema, tags
    # metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    analysis_metadata: Mapped[dict] = mapped_column(
        JSONB, name="metadata", nullable=False, default=dict
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    chat: Mapped["Chat"] = relationship("Chat", back_populates="dashboards")


class TemporaryDashboard(Base):
    """
    Temporary storage for dashboards created by unauthenticated users.
    These are ephemeral and auto-deleted after TTL expires.
    When user authenticates, data can be migrated to permanent storage.
    """

    __tablename__ = "temporary_dashboards"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )

    # Cleaned dataset serialised as JSON records (orient="records")
    cleaned_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # KPI payload from kpi_extractor
    kpi_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # AI-generated insights and executive summary
    ai_insights: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict)

    # Chart configurations from chart_builder
    chart_config: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list)

    # File metadata, enriched schema, tags
    analysis_metadata: Mapped[dict] = mapped_column(
        JSONB, name="metadata", nullable=False, default=dict
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
