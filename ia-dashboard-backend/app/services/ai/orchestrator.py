"""
app/services/ai/orchestrator.py

AI Orchestrator implementing the Strategy + Fallback pattern (SA section 3.2).

Flow:
  1. Call primary provider (Gemini) with a configurable timeout.
  2. If the primary exceeds the timeout or raises an error, automatically
     fall back to the secondary provider (OpenAI).
  3. If both providers fail, raise AIProviderError.

This design ensures continuity of AI features (RNF-04) while keeping
vendor independence.
"""

import asyncio
import json
import re
from typing import Any, Optional

from app.core.config import get_settings
from app.core.exceptions import AIProviderError, AITimeoutError
from app.core.logging import get_logger
from app.services.ai.providers import BaseAIProvider, GeminiProvider, OpenAIProvider

logger = get_logger(__name__)
settings = get_settings()


class AIOrchestrator:
    """
    Manages prompt dispatch and provider fallback logic.
    Instantiate once and reuse across requests (stateless, RNF-09).
    """

    def __init__(
        self,
        primary: Optional[BaseAIProvider] = None,
        fallback: Optional[BaseAIProvider] = None,
    ) -> None:
        self._primary = primary or GeminiProvider()
        self._fallback = fallback or OpenAIProvider()
        self._timeout = settings.ai_timeout_seconds
        self._fallback_enabled = settings.ai_fallback_enabled
        # Track which provider succeeded
        self._selected_provider: Optional[str] = None

    async def complete(self, prompt: str) -> str:
        """
        Send a prompt through the primary provider with a timeout.
        Falls back to the secondary provider when needed (RNF-04).

        Returns the raw text response from whichever provider responded.
        Sets _selected_provider to track which provider was used.
        """
        try:
            logger.info("ai_request_start", provider=self._primary.name)
            result = await asyncio.wait_for(
                self._primary.complete(prompt),
                timeout=float(self._timeout),
            )
            self._selected_provider = self._primary.name
            logger.info("ai_request_success", provider=self._primary.name)
            return result

        except asyncio.TimeoutError:
            logger.warning(
                "ai_primary_timeout",
                provider=self._primary.name,
                timeout_seconds=self._timeout,
            )
            if not self._fallback_enabled:
                raise AITimeoutError(
                    f"Primary AI provider timed out after {self._timeout}s."
                )

        except AIProviderError as exc:
            # Detect rate limiting early (429 or "rate" in error) → go to fallback
            error_lower = str(exc).lower()
            if "rate" in error_lower or "429" in str(exc):
                logger.warning(
                    "ai_primary_rate_limit_detected",
                    provider=self._primary.name,
                    trigger_fallback=True,
                )
            else:
                logger.warning(
                    "ai_primary_error",
                    provider=self._primary.name,
                    error=str(exc),
                )
            if not self._fallback_enabled:
                raise

        # --- Fallback path ---
        logger.info("ai_fallback_start", provider=self._fallback.name)
        try:
            result = await self._fallback.complete(prompt)
            self._selected_provider = self._fallback.name
            logger.info("ai_fallback_success", provider=self._fallback.name)
            return result
        except Exception as exc:
            logger.error(
                "ai_fallback_failed",
                provider=self._fallback.name,
                error=str(exc),
            )
            raise AIProviderError(
                "All AI providers failed. Please try again later."
            ) from exc

    async def complete_json(self, prompt: str) -> dict[str, Any]:
        """
        Run a completion and parse the response as JSON.
        Strips markdown code fences if the model includes them.
        """
        raw = await self.complete(prompt)
        cleaned = _strip_markdown_fences(raw)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error("ai_json_parse_failed", raw_response=raw[:500])
            raise AIProviderError(
                "AI returned a non-JSON response."
            ) from exc


def _strip_markdown_fences(text: str) -> str:
    """Remove ```json ... ``` wrappers that models often include."""
    pattern = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
    match = pattern.search(text)
    return match.group(1).strip() if match else text.strip()
