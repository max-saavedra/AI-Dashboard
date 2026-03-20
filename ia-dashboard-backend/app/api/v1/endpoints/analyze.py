"""
app/api/v1/endpoints/analyze.py

POST /api/v1/analyze

Main pipeline endpoint (RF-01, RF-02, RF-05, UC-01, UC-02):
  1. Validate and read uploaded file
  2. Clean and normalise with the ETL engine
  3. Profile columns with heuristics
  4. Enrich schema via AI Schema Agent
  5. Extract KPIs
  6. Build chart configurations
  7. Persist to DB:
     - If user authenticated: save to dashboards table (permanent)
     - If user not authenticated: save to temporary_dashboards table (TTL 24h)
  8. Return full AnalysisResult
"""

import json
import time
import uuid
import secrets
from typing import Optional
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import optional_current_user
from app.core.exceptions import (
    EmptyFileError,
    FileTooLargeError,
    UnsupportedFileFormatError,
)
from app.core.logging import get_logger
from app.core.security import TokenPayload
from app.models.database import Chat, Dashboard
from app.models.session import get_db
from app.schemas.analysis import AnalysisResult, ColumnMeta
from app.services.ai.orchestrator import AIOrchestrator
from app.services.ai.schema_agent import enrich_schema
from app.services.dashboard.chart_builder import build_chart_configs
from app.services.etl.cleaner import clean_file
from app.services.etl.kpi_extractor import extract_kpis
from app.services.etl.profiler import profile_dataframe
from app.services.etl.validator import validate_upload

router = APIRouter()
logger = get_logger(__name__)

# Singleton orchestrator reused across requests (stateless, RNF-09)
_orchestrator = AIOrchestrator()


@router.post(
    "/analyze",
    response_model=AnalysisResult,
    summary="Upload and analyse an Excel/CSV file",
    status_code=status.HTTP_200_OK,
)
async def analyze_file(
    file: UploadFile = File(...,
                            description="Excel (.xlsx) or CSV file to analyse"),
    user_objective: Optional[str] = Form(
        default=None,
        description="Optional analysis goal entered by the user",
    ),
    tags: Optional[str] = Form(
        default=None,
        description="Comma-separated focus tags (e.g. 'sales,revenue')",
    ),
    chat_id: Optional[str] = Form(
        default=None,
        description="Existing chat ID to append the analysis to",
    ),
    current_user: Optional[TokenPayload] = Depends(optional_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalysisResult:
    """
    Main ETL + AI pipeline.

    Accepts a multipart form with the file and optional context fields.
    Returns a complete dashboard payload ready for frontend rendering.
    """
    start_time = time.perf_counter()

    # ------------------------------------------------------------------ #
    # 1. Read and validate the uploaded file
    # ------------------------------------------------------------------ #
    content = await file.read()
    filename = file.filename or "upload"

    try:
        validate_upload(filename, content)
    except FileTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc))
    except UnsupportedFileFormatError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    # ------------------------------------------------------------------ #
    # 2. ETL: clean and normalise
    # ------------------------------------------------------------------ #
    try:
        df = clean_file(filename, content)
    except EmptyFileError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.error("etl_unexpected_error", filename=filename, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="File processing failed.")

    etl_duration = time.perf_counter() - start_time
    logger.info("etl_completed", filename=filename,
                rows=len(df),
                columns=df.shape[1],
                duration_s=round(etl_duration, 3))

    # ------------------------------------------------------------------ #
    # 3. Heuristic column profiling (LOCAL, NO AI)
    # ------------------------------------------------------------------ #
    profile = profile_dataframe(df)

    # ------------------------------------------------------------------ #
    # 4. AI schema enrichment (with automatic fallback, RNF-04)
    # If AI fails (rate limit, quota, timeout), continues with heuristic profile
    # ------------------------------------------------------------------ #
    schema_ai_start = time.perf_counter()
    enriched_profile = await enrich_schema(profile, _orchestrator)
    schema_ai_duration = time.perf_counter() - schema_ai_start

    # Check if schema was enriched or using heuristic-only fallback
    ai_enriched = len(enriched_profile.columns) > 0 and any(
        col.alias for col in enriched_profile.columns
    )
    logger.info(
        "schema_enrichment_completed",
        ai_enriched=ai_enriched,
        columns_count=len(enriched_profile.columns),
        duration_s=round(schema_ai_duration, 3),
    )

    # ------------------------------------------------------------------ #
    # 5. KPI extraction
    # ------------------------------------------------------------------ #
    parsed_tags = [t.strip() for t in (tags or "").split(",") if t.strip()]
    kpi_payload = extract_kpis(df, enriched_profile, user_objective)

    # ------------------------------------------------------------------ #
    # 6. Chart configuration
    # ------------------------------------------------------------------ #
    chart_configs = build_chart_configs(enriched_profile, kpi_payload)

    # ------------------------------------------------------------------ #
    # 7. Persist (authenticated users permanently, anon users temporarily)
    # ------------------------------------------------------------------ #
    dashboard_id = str(uuid.uuid4())
    resolved_chat_id: Optional[str] = None
    session_id: Optional[str] = None
    is_temporary: bool = False

    if current_user and current_user.sub:
        # Authenticated user: save permanently to dashboards
        resolved_chat_id = await _persist_analysis(
            db=db,
            user_id=current_user.sub,
            chat_id=chat_id,
            filename=filename,
            df_records=df.to_dict(orient="records"),
            kpi_payload=kpi_payload,
            chart_configs=chart_configs,
            enriched_profile=enriched_profile,
            tags=parsed_tags,
            user_objective=user_objective,
            dashboard_id=dashboard_id,
        )
    else:
        # Anonymous user: save temporarily (will expire in 24h)
        session_id = secrets.token_urlsafe(32)
        is_temporary = True

        logger.info("DEBUG: Persisting temporary analysis for anonymous user",
                    session_id=session_id, dashboard_id=dashboard_id)

        try:
            await _persist_temporary_analysis(
                db=db,
                session_id=session_id,
                filename=filename,
                df_records=df.to_dict(orient="records"),
                kpi_payload=kpi_payload,
                chart_configs=chart_configs,
                enriched_profile=enriched_profile,
                tags=parsed_tags,
                user_objective=user_objective,
                dashboard_id=dashboard_id,
            )
        except Exception as exc:
            logger.error("DEBUG: Failed to persist temporary analysis",
                         session_id=session_id, error=str(exc))
            # Continue anyway - data was processed successfully

    # ------------------------------------------------------------------ #
    # 8. Build and return response
    # ------------------------------------------------------------------ #
    column_metas = [
        ColumnMeta(
            name=col.name,
            alias=col.alias or col.name,
            inferred_type=col.inferred_type,
            suggested_role=col.suggested_role,
            null_rate=col.null_rate,
            unique_count=col.unique_count,
            stats=col.stats,
        )
        for col in enriched_profile.columns
    ]

    filter_columns = [
        col.name
        for col in enriched_profile.columns
        if col.suggested_role in ("dimension", "datetime")
    ]

    total_duration = time.perf_counter() - start_time
    logger.info(
        "analysis_complete",
        filename=filename,
        dashboard_id=dashboard_id,
        total_duration_s=round(total_duration, 3),
    )

    return AnalysisResult(
        dashboard_id=dashboard_id,
        chat_id=resolved_chat_id,
        session_id=session_id,
        is_temporary=is_temporary,
        dataset_summary=getattr(enriched_profile, "dataset_summary", ""),
        row_count=len(df),
        columns=column_metas,
        kpis=kpi_payload,
        chart_configs=chart_configs,
        filter_columns=filter_columns,
    )


# ------------------------------------------------------------------ #
# Persistence helpers
# ------------------------------------------------------------------ #


async def _persist_temporary_analysis(
    db: AsyncSession,
    session_id: str,
    filename: str,
    df_records: list[dict],
    kpi_payload: dict,
    chart_configs: list[dict],
    enriched_profile,
    tags: list[str],
    user_objective: Optional[str],
    dashboard_id: str,
) -> None:
    """
    Save analysis data to dashboards table with an anonymous Chat.
    For unauthenticated users without a persistent chat.
    """
    import uuid as _uuid

    # Create an anonymous chat for this temporary analysis
    chat = Chat(
        id=_uuid.uuid4(),
        user_id=None,  # Anonymous
        name=filename.rsplit(".", 1)[0][:60],
    )
    db.add(chat)
    await db.flush()

    # Save dashboard linked to the anonymous chat
    dashboard = Dashboard(
        id=_uuid.UUID(dashboard_id),
        chat_id=chat.id,
        cleaned_data={"records": df_records},
        kpi_data=kpi_payload,
        ai_insights={
            "dataset_summary": getattr(enriched_profile, "dataset_summary", ""),
        },
        chart_config=chart_configs,
        analysis_metadata={
            "filename": filename,
            "tags": tags,
            "user_objective": user_objective,
            "session_id": session_id,
            "columns": [
                {"name": c.name, "alias": c.alias, "type": c.inferred_type}
                for c in enriched_profile.columns
            ],
        },
    )
    db.add(dashboard)
    await db.flush()

    logger.info(
        "temporary_analysis_persisted",
        dashboard_id=dashboard_id,
        session_id=session_id,
        chat_id=str(chat.id),
    )


# ------------------------------------------------------------------ #
# Persistence helper
# ------------------------------------------------------------------ #


async def _persist_analysis(
    db: AsyncSession,
    user_id: str,
    chat_id: Optional[str],
    filename: str,
    df_records: list[dict],
    kpi_payload: dict,
    chart_configs: list[dict],
    enriched_profile,
    tags: list[str],
    user_objective: Optional[str],
    dashboard_id: str,
) -> str:
    """
    Create or reuse a Chat and persist a Dashboard row.
    Returns the chat_id used.
    """
    import uuid as _uuid

    # Resolve or create chat session
    if chat_id:
        chat = await db.get(Chat, uuid.UUID(chat_id))
        if chat is None or str(chat.user_id) != user_id:
            chat = None  # invalid chat_id – create a new one

    if not chat_id or chat is None:
        chat = Chat(
            id=_uuid.uuid4(),
            user_id=_uuid.UUID(user_id),
            name=filename.rsplit(".", 1)[0][:60],
        )
        db.add(chat)
        await db.flush()

    dashboard = Dashboard(
        id=_uuid.UUID(dashboard_id),
        chat_id=chat.id,
        cleaned_data={"records": df_records},
        kpi_data=kpi_payload,
        ai_insights={
            "dataset_summary": getattr(enriched_profile, "dataset_summary", ""),
        },
        chart_config=chart_configs,
        metadata={
            "filename": filename,
            "tags": tags,
            "user_objective": user_objective,
            "columns": [
                {"name": c.name, "alias": c.alias, "type": c.inferred_type}
                for c in enriched_profile.columns
            ],
        },
    )
    db.add(dashboard)
    await db.flush()

    logger.info("analysis_persisted",
                dashboard_id=dashboard_id, chat_id=str(chat.id))
    return str(chat.id)
