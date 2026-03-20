"""
app/services/ai/summary_service.py

Generates AI executive summaries and handles Q&A chat queries (RF-03, RF-06).

Both functions are thin wrappers that build the appropriate prompt and
delegate to the AIOrchestrator for provider-agnostic completion.
"""

from __future__ import annotations

from typing import Any, Optional

from app.core.logging import get_logger
from app.services.ai.orchestrator import AIOrchestrator
from app.services.ai.prompts import (
    build_chat_qa_prompt,
    build_executive_summary_prompt,
)

logger = get_logger(__name__)


async def generate_executive_summary(
    kpi_payload: dict[str, Any],
    dataset_summary: str,
    orchestrator: AIOrchestrator,
    user_objective: Optional[str] = None,
    user_structure: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> str:
    """
    Generate a professional executive summary from KPI data (RF-03, US-03).

    Args:
        kpi_payload: aggregated metrics from the ETL layer.
        dataset_summary: one-paragraph context from the schema agent.
        orchestrator: AI provider dispatcher.
        user_objective: free-text goal provided by the user.
        user_structure: optional custom outline for the summary.
        tags: user-selected focus tags (UC-02).

    Returns:
        Plain-text executive summary.

    Raises:
        ValueError: if required inputs are empty.
    """
    # Validate required inputs
    if not kpi_payload:
        raise ValueError("kpi_payload cannot be empty")
    if not dataset_summary or not dataset_summary.strip():
        raise ValueError("dataset_summary cannot be empty")

    prompt = build_executive_summary_prompt(
        kpi_payload=kpi_payload,
        schema_summary=dataset_summary,
        user_objective=user_objective,
        user_structure=user_structure,
        tags=tags,
    )

    logger.info(
        "summary_generation_start",
        tags=tags,
        has_objective=bool(user_objective),
        provider="orchestrator",
    )
    summary = await orchestrator.complete(prompt)
    logger.info(
        "summary_generation_success",
        length=len(summary),
        provider=getattr(orchestrator, "_selected_provider", "unknown"),
    )
    return summary


async def answer_data_question(
    question: str,
    kpi_payload: dict[str, Any],
    dataset_summary: str,
    orchestrator: AIOrchestrator,
    conversation_history: Optional[list[dict[str, str]]] = None,
) -> str:
    """
    Answer a natural language question grounded strictly in the dataset (RF-06).

    Args:
        question: the user's question.
        kpi_payload: current KPI context.
        dataset_summary: one-paragraph dataset description.
        orchestrator: AI provider dispatcher.
        conversation_history: previous Q&A turns for multi-turn context.

    Returns:
        Plain-text answer.
    """
    prompt = build_chat_qa_prompt(
        question=question,
        kpi_payload=kpi_payload,
        schema_summary=dataset_summary,
        conversation_history=conversation_history,
    )

    logger.info("qa_question_start", question_preview=question[:80])
    answer = await orchestrator.complete(prompt)
    logger.info("qa_answer_done", length=len(answer))
    return answer
