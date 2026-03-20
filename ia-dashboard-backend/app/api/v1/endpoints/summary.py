"""
app/api/v1/endpoints/summary.py

POST /api/v1/summary         – generate AI executive summary
GET  /api/v1/summary/{id}/pdf – download summary as PDF

Implements RF-03 and US-03.
"""

import uuid
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import optional_current_user
from app.core.exceptions import AIProviderError
from app.core.logging import get_logger
from app.core.security import TokenPayload
from app.models.database import Dashboard, Chat
from app.models.session import get_db
from app.schemas.analysis import SummaryRequest, SummaryResponse
from app.services.ai.orchestrator import AIOrchestrator
from app.services.ai.summary_service import generate_executive_summary
from app.services.dashboard.pdf_exporter import export_summary_pdf

router = APIRouter()
logger = get_logger(__name__)
_orchestrator = AIOrchestrator()


@router.post(
    "/summary",
    response_model=SummaryResponse,
    summary="Generate an AI executive summary for a dashboard",
)
async def create_summary(
    request: SummaryRequest,
    current_user: Optional[TokenPayload] = Depends(optional_current_user),
    db: AsyncSession = Depends(get_db),
) -> SummaryResponse:
    """
    Build the executive summary prompt dynamically based on:
      - The stored KPI payload for the given dashboard
      - Optional user tags and custom structure (US-03)
      - Optional user objective

    Validates that required data (KPI and dataset summary) is available before
    attempting AI generation. Stores the generated summary back to the dashboard's
    ai_insights field.

    Returns 422 if required data is missing or empty.
    Returns 503 if AI providers fail after retries.
    """
    dashboard = await _get_dashboard(db, request.dashboard_id, current_user)

    # Copy data from ORM object while session is still active (prevents greenlet_spawn error)
    kpi_payload: dict = dict(dashboard.kpi_data or {})
    insights = dict(dashboard.ai_insights or {})
    dataset_summary: str = insights.get("dataset_summary", "").strip()

    # Validate required inputs
    if not kpi_payload:
        logger.warning(
            "summary_request_missing_kpi",
            dashboard_id=request.dashboard_id,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Dashboard has no KPI data. Run analysis first.",
        )

    if not dataset_summary:
        logger.warning(
            "summary_request_missing_dataset_summary",
            dashboard_id=request.dashboard_id,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Dataset summary not available. Run analysis first.",
        )

    logger.info(
        "summary_generation_request",
        dashboard_id=request.dashboard_id,
        has_tags=bool(request.tags),
        has_objective=bool(request.user_objective),
    )

    try:
        summary = await generate_executive_summary(
            kpi_payload=kpi_payload,
            dataset_summary=dataset_summary,
            orchestrator=_orchestrator,
            user_objective=request.user_objective,
            user_structure=request.user_structure,
            tags=request.tags,
        )
    except (AIProviderError, ValueError) as exc:
        logger.error("summary_generation_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI summary generation is currently unavailable. Please try again.",
        )

    # Persist the summary
    insights["executive_summary"] = summary
    dashboard.ai_insights = insights
    await db.commit()  # Commit instead of flush to ensure changes are persisted

    logger.info(
        "summary_generation_completed",
        dashboard_id=request.dashboard_id,
        summary_length=len(summary),
        provider=getattr(_orchestrator, "_selected_provider", "unknown"),
    )

    return SummaryResponse(dashboard_id=request.dashboard_id, summary=summary)


@router.get(
    "/summary/{dashboard_id}/pdf",
    summary="Download the executive summary as a PDF",
    response_class=StreamingResponse,
)
async def download_summary_pdf(
    dashboard_id: str,
    current_user: Optional[TokenPayload] = Depends(optional_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Export the previously generated executive summary as a formatted PDF.
    Raises 404 if no summary has been generated yet for this dashboard.
    """
    dashboard = await _get_dashboard(db, dashboard_id, current_user)

    summary_text = (dashboard.ai_insights or {}).get("executive_summary")
    if not summary_text:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No summary found. Generate a summary first via POST /summary.",
        )

    # filename_hint = (dashboard.metadata or {}).get("filename", "report")
    # Si en el modelo es analysis_metadata, cámbialo aquí:
    filename_hint = (dashboard.analysis_metadata or {}
                     ).get("filename", "report")
    title = filename_hint.rsplit(".", 1)[0].replace("_", " ").title()

    pdf_bytes = export_summary_pdf(
        summary_text=summary_text,
        kpi_payload=dashboard.kpi_data or {},
        dataset_title=title,
    )

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{title}_summary.pdf"'},
    )


# ------------------------------------------------------------------ #
# Shared helper
# ------------------------------------------------------------------ #


async def _get_dashboard(
    db: AsyncSession,
    dashboard_id: str,
    current_user: Optional[TokenPayload],
) -> Dashboard:
    try:
        parsed_id = uuid.UUID(dashboard_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid dashboard ID."
        )

    # 1. Traemos solo el Dashboard primero.
    # Quitamos selectinload para evitar que asyncpg genere sentencias preparadas complejas
    stmt = select(Dashboard).where(Dashboard.id == parsed_id)
    result = await db.execute(stmt)
    dashboard = result.scalar_one_or_none()

    if dashboard is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found."
        )

    # 2. VALIDACIÓN DE PROPIEDAD (Evitando el Greenlet Error)
    # En lugar de hacer 'dashboard.chat', lo buscamos explícitamente si existe chat_id
    if dashboard.chat_id:
        chat_stmt = select(Chat).where(Chat.id == dashboard.chat_id)
        chat_result = await db.execute(chat_stmt)
        chat = chat_result.scalar_one_or_none()

        if chat and chat.user_id:
            # Verificamos si el usuario actual es el dueño
            if current_user is None or str(chat.user_id) != current_user.sub:
                logger.warning(
                    "unauthorized_access_attempt",
                    dashboard_id=dashboard_id,
                    user_id=current_user.sub if current_user else "anonymous"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied."
                )

    return dashboard
