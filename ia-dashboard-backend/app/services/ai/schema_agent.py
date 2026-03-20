"""
app/services/ai/schema_agent.py

Uses the AI Orchestrator to enrich the heuristic DatasetProfile
with human-readable aliases, confirmed types, and chart suggestions (RF-02).

Falls back to heuristic-only results when the AI provider is unavailable.
OPTIMIZED: Checks payload size before sending to prevent rate limits.
"""

from __future__ import annotations

from typing import Any

from app.core.exceptions import AIProviderError
from app.core.logging import get_logger
from app.services.ai.orchestrator import AIOrchestrator
from app.services.ai.prompts import build_schema_detection_prompt
from app.services.ai.token_optimizer import check_payload_size
from app.services.etl.profiler import ColumnProfile, DatasetProfile

logger = get_logger(__name__)


async def enrich_schema(
    profile: DatasetProfile,
    orchestrator: AIOrchestrator,
) -> DatasetProfile:
    """
    Send the heuristic profile to the AI Schema Agent and merge the
    returned metadata back into the profile.

    If the AI call fails (rate limit, timeout, quota exceeded), the original 
    heuristic profile is returned unchanged (graceful degradation, RNF-04).
    Analysis continues without AI enrichment but completes successfully.
    """
    payload = profile.to_ai_payload(sample_rows=2, max_columns=30)

    # Check payload size before sending (helps avoid rate limits)
    size_check = check_payload_size(
        payload, max_tokens=8000, warn_threshold=0.75)
    if size_check["warning"]:
        logger.info(
            "schema_payload_large",
            estimated_tokens=size_check["estimated_tokens"],
            size_bytes=size_check["size_bytes"],
            columns_sent=payload.get(
                "columns_sent", len(payload.get("columns", []))),
        )

    prompt = build_schema_detection_prompt(payload)

    try:
        ai_result = await orchestrator.complete_json(prompt)
    except AIProviderError as exc:
        # Log as INFO not WARNING - this is expected behavior when fallback exhausted
        error_lower = str(exc).lower()
        if "rate" in error_lower or "429" in str(exc) or "quota" in error_lower:
            logger.info(
                "schema_agent_fallback_rate_limit",
                reason="API rate limit or quota exceeded",
                details=str(exc),
            )
        else:
            logger.info(
                "schema_agent_fallback",
                reason="AI unavailable",
                details=str(exc),
            )
        return profile  # Return heuristic-only profile, analysis continues

    return _merge_ai_result(profile, ai_result)


def _merge_ai_result(
    profile: DatasetProfile, ai_result: dict[str, Any]
) -> DatasetProfile:
    """
    Overlay AI-confirmed types and aliases on top of the heuristic profile.
    Unknown columns returned by the AI are ignored.

    Also enrich the dataset_summary with AI-generated description if available,
    but preserve the heuristic summary if AI doesn't provide one.
    """
    ai_columns: dict[str, dict[str, Any]] = {
        col["name"]: col for col in ai_result.get("columns", [])
    }

    enriched_columns: list[ColumnProfile] = []
    for col in profile.columns:
        ai_col = ai_columns.get(col.name, {})
        enriched_columns.append(
            ColumnProfile(
                name=col.name,
                alias=ai_col.get("alias", col.name),
                inferred_type=ai_col.get("type", col.inferred_type),
                suggested_role=ai_col.get("role", col.suggested_role),
                null_rate=col.null_rate,
                unique_count=col.unique_count,
                stats=col.stats,
                sample_values=col.sample_values,
            )
        )

    # Update columns
    profile.columns = enriched_columns

    # Preserve heuristic dataset_summary but enrich with AI version if available
    ai_summary = ai_result.get("dataset_summary", "").strip()
    if ai_summary:
        profile.dataset_summary = ai_summary
    # else: keep the heuristic summary already in profile.dataset_summary

    # Store suggested charts for later use
    profile.suggested_charts = ai_result.get(
        "suggested_charts", [])  # type: ignore[attr-defined]

    logger.info(
        "schema_enriched",
        columns=len(enriched_columns),
        has_ai_summary=bool(ai_summary),
        # type: ignore[attr-defined]
        suggested_charts=len(profile.suggested_charts),
    )
    return profile
