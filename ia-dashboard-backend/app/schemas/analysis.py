"""
app/schemas/analysis.py

Pydantic v2 schemas for all API request bodies and response envelopes.
These are the contracts between the backend and the Vue frontend.
"""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ------------------------------------------------------------------ #
# Shared / base
# ------------------------------------------------------------------ #


class APIResponse(BaseModel):
    """Standard response envelope used by all endpoints."""

    success: bool = True
    message: str = "OK"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    success: bool = False
    error_code: str
    message: str
    detail: Optional[str] = None


# ------------------------------------------------------------------ #
# Analysis (upload + process)
# ------------------------------------------------------------------ #


class AnalysisRequest(BaseModel):
    """
    Optional JSON body that can accompany the file upload (multipart).
    All fields are optional so the endpoint degrades gracefully.
    """

    user_objective: Optional[str] = Field(
        default=None,
        max_length=500,
        description="The user's goal or context for the analysis (UC-02).",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="User-selected focus topics for the AI summary (US-03).",
    )

    @field_validator("tags")
    @classmethod
    def limit_tags(cls, v: list[str]) -> list[str]:
        # Prevent unreasonably large tag lists
        return v[:10]


class ColumnMeta(BaseModel):
    """Metadata for a single column returned after processing."""

    name: str
    alias: str
    inferred_type: str
    suggested_role: str
    null_rate: float
    unique_count: int
    stats: dict[str, Any] = Field(default_factory=dict)


class AnalysisResult(BaseModel):
    """
    Full result returned by POST /analyze.
    Contains everything the frontend needs to render the dashboard.
    """

    dashboard_id: str
    chat_id: Optional[str] = None
    # For unauthenticated users' temporary data
    session_id: Optional[str] = None
    is_temporary: bool = False  # True if data is stored temporarily (no auth)
    dataset_summary: str
    row_count: int
    columns: list[ColumnMeta]
    kpis: dict[str, Any]
    chart_configs: list[dict[str, Any]]
    filter_columns: list[str]


# ------------------------------------------------------------------ #
# Summary generation
# ------------------------------------------------------------------ #


class SummaryRequest(BaseModel):
    """Body for POST /summary."""

    dashboard_id: str
    tags: list[str] = Field(default_factory=list)
    user_objective: Optional[str] = Field(default=None, max_length=500)
    user_structure: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Custom outline / template the user wants the summary to follow.",
    )


class SummaryResponse(BaseModel):
    """Response from POST /summary."""

    dashboard_id: str
    summary: str


# ------------------------------------------------------------------ #
# Q&A chat
# ------------------------------------------------------------------ #


class ChatMessage(BaseModel):
    """A single turn in the conversation history."""

    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(max_length=4000)


class ChatRequest(BaseModel):
    """Body for POST /chat."""

    dashboard_id: str
    question: str = Field(min_length=1, max_length=1000)
    history: list[ChatMessage] = Field(
        default_factory=list,
        description="Previous conversation turns for multi-turn context (RF-06).",
    )

    @field_validator("history")
    @classmethod
    def limit_history(cls, v: list[ChatMessage]) -> list[ChatMessage]:
        # Keep only the last 10 turns to control token usage
        return v[-10:]


class ChatResponse(BaseModel):
    """Response from POST /chat."""

    dashboard_id: str
    answer: str
    question: str


# ------------------------------------------------------------------ #
# Session / history
# ------------------------------------------------------------------ #


class ChatSessionSummary(BaseModel):
    """Summary item in the user's analysis history list (UC-03)."""

    chat_id: str
    name: str
    created_at: str
    dashboard_count: int


class RenameChatRequest(BaseModel):
    """Body for PATCH /chats/{chat_id}."""

    name: str = Field(min_length=1, max_length=120)
