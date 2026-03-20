"""
app/api/v1/endpoints/chat.py

POST /api/v1/chat

Mini-chat Q&A endpoint (RF-06, US not numbered but described in project spec).
Answers natural language questions grounded strictly in the dashboard's data.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import optional_current_user
from app.core.exceptions import AIProviderError
from app.core.logging import get_logger
from app.core.security import TokenPayload
from app.models.session import get_db
from app.schemas.analysis import ChatRequest, ChatResponse
from app.services.ai.orchestrator import AIOrchestrator
from app.services.ai.summary_service import answer_data_question
from app.api.v1.endpoints.summary import _get_dashboard

router = APIRouter()
logger = get_logger(__name__)
_orchestrator = AIOrchestrator()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Ask a natural language question about a dashboard dataset",
)
async def chat_with_data(
    request: ChatRequest,
    current_user: Optional[TokenPayload] = Depends(optional_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """
    Q&A endpoint grounded exclusively in the stored KPI data (RF-06).

    Accepts optional conversation history for multi-turn context.
    Responses must not reference information outside the dataset.
    """
    dashboard = await _get_dashboard(db, request.dashboard_id, current_user)

    kpi_payload: dict = dashboard.kpi_data or {}
    dataset_summary: str = (dashboard.ai_insights or {}).get("dataset_summary", "")

    # Convert Pydantic ChatMessage objects to plain dicts for the prompt builder
    history = [{"role": msg.role, "content": msg.content} for msg in request.history]

    try:
        answer = await answer_data_question(
            question=request.question,
            kpi_payload=kpi_payload,
            dataset_summary=dataset_summary,
            orchestrator=_orchestrator,
            conversation_history=history,
        )
    except AIProviderError as exc:
        logger.error("chat_qa_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI assistant is temporarily unavailable. Please try again.",
        )

    return ChatResponse(
        dashboard_id=request.dashboard_id,
        question=request.question,
        answer=answer,
    )
