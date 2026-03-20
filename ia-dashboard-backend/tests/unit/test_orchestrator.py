"""
tests/unit/test_orchestrator.py

Unit tests for app/services/ai/orchestrator.py.
Uses mocks so no real API calls are made.
Tests the timeout, fallback logic, and JSON parsing.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.core.exceptions import AIProviderError, AITimeoutError
from app.services.ai.orchestrator import AIOrchestrator, _strip_markdown_fences
from app.services.ai.providers import BaseAIProvider


def _make_provider(name: str, response: str = "response") -> MagicMock:
    """Build a mock AI provider that returns a canned response."""
    provider = MagicMock(spec=BaseAIProvider)
    provider.name = name
    provider.complete = AsyncMock(return_value=response)
    return provider


def _make_slow_provider(name: str, delay: float = 10.0) -> MagicMock:
    """Build a mock AI provider that sleeps to simulate a timeout."""

    async def _slow_complete(_: str) -> str:
        await asyncio.sleep(delay)
        return "too late"

    provider = MagicMock(spec=BaseAIProvider)
    provider.name = name
    provider.complete = _slow_complete
    return provider


def _make_failing_provider(name: str) -> MagicMock:
    """Build a mock AI provider that always raises AIProviderError."""
    provider = MagicMock(spec=BaseAIProvider)
    provider.name = name
    provider.complete = AsyncMock(side_effect=AIProviderError("provider down"))
    return provider


class TestOrchestratorFallback:
    @pytest.mark.asyncio
    async def test_primary_success_no_fallback(self):
        primary = _make_provider("gemini", "primary response")
        fallback = _make_provider("openai", "fallback response")
        orchestrator = AIOrchestrator(primary=primary, fallback=fallback)

        result = await orchestrator.complete("test prompt")

        assert result == "primary response"
        fallback.complete.assert_not_called()

    @pytest.mark.asyncio
    async def test_falls_back_on_timeout(self):
        primary = _make_slow_provider("gemini", delay=10.0)
        fallback = _make_provider("openai", "fallback response")
        orchestrator = AIOrchestrator(primary=primary, fallback=fallback)
        orchestrator._timeout = 0.01  # very short timeout for the test

        result = await orchestrator.complete("test prompt")

        assert result == "fallback response"

    @pytest.mark.asyncio
    async def test_falls_back_on_provider_error(self):
        primary = _make_failing_provider("gemini")
        fallback = _make_provider("openai", "fallback ok")
        orchestrator = AIOrchestrator(primary=primary, fallback=fallback)

        result = await orchestrator.complete("test prompt")
        assert result == "fallback ok"

    @pytest.mark.asyncio
    async def test_raises_when_both_providers_fail(self):
        primary = _make_failing_provider("gemini")
        fallback = _make_failing_provider("openai")
        orchestrator = AIOrchestrator(primary=primary, fallback=fallback)

        with pytest.raises(AIProviderError):
            await orchestrator.complete("test prompt")

    @pytest.mark.asyncio
    async def test_raises_timeout_error_when_fallback_disabled(self):
        primary = _make_slow_provider("gemini", delay=10.0)
        fallback = _make_provider("openai")
        orchestrator = AIOrchestrator(primary=primary, fallback=fallback)
        orchestrator._timeout = 0.01
        orchestrator._fallback_enabled = False

        with pytest.raises(AITimeoutError):
            await orchestrator.complete("test prompt")


class TestCompleteJSON:
    @pytest.mark.asyncio
    async def test_parses_clean_json(self):
        primary = _make_provider("gemini", '{"key": "value"}')
        orchestrator = AIOrchestrator(primary=primary, fallback=_make_provider("openai"))

        result = await orchestrator.complete_json("prompt")
        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_strips_markdown_fences_before_parsing(self):
        raw = "```json\n{\"answer\": 42}\n```"
        primary = _make_provider("gemini", raw)
        orchestrator = AIOrchestrator(primary=primary, fallback=_make_provider("openai"))

        result = await orchestrator.complete_json("prompt")
        assert result == {"answer": 42}

    @pytest.mark.asyncio
    async def test_raises_on_invalid_json(self):
        primary = _make_provider("gemini", "this is not json")
        orchestrator = AIOrchestrator(primary=primary, fallback=_make_provider("openai"))

        with pytest.raises(AIProviderError, match="non-JSON"):
            await orchestrator.complete_json("prompt")


class TestStripMarkdownFences:
    def test_removes_json_fence(self):
        text = "```json\n{\"a\": 1}\n```"
        assert _strip_markdown_fences(text) == '{"a": 1}'

    def test_removes_plain_fence(self):
        text = "```\n{\"a\": 1}\n```"
        assert _strip_markdown_fences(text) == '{"a": 1}'

    def test_passes_through_clean_json(self):
        text = '{"a": 1}'
        assert _strip_markdown_fences(text) == '{"a": 1}'
