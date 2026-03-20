"""
app/services/ai/providers.py

Thin async wrappers around the Gemini and OpenAI SDKs.
Each provider exposes a single `complete(prompt)` coroutine so the
orchestrator can swap between them without knowing SDK internals.

Implements retry logic with exponential backoff for rate limiting (429).
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

import google.generativeai as genai
from openai import AsyncOpenAI, RateLimitError

from app.core.config import get_settings
from app.core.exceptions import AIProviderError
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Retry configuration
MAX_RETRIES = 3
BASE_WAIT_SECONDS = 1

# Request throttling: max 2 concurrent AI requests to prevent rate limits
_ai_semaphore = asyncio.Semaphore(2)


class BaseAIProvider(ABC):
    """Common interface for all AI provider wrappers."""

    name: str = "base"

    @abstractmethod
    async def complete(self, prompt: str) -> str:
        """Send a prompt and return the text response."""


class GeminiProvider(BaseAIProvider):
    """
    Wraps Google Gemini 1.5 Flash.
    Gemini's Python SDK is synchronous; we run it in an executor
    to avoid blocking the FastAPI event loop.
    """

    name = "gemini"

    def __init__(self) -> None:
        if not settings.gemini_api_key:
            logger.warning("gemini_api_key_missing", provider="gemini")
        genai.configure(api_key=settings.gemini_api_key)
        self._model = genai.GenerativeModel("gemini-2.5-flash")

    async def complete(self, prompt: str) -> str:
        """
        Execute a Gemini completion in a thread pool executor
        to preserve async compatibility.
        Implements retry with exponential backoff for rate limiting.
        """
        if not prompt or not prompt.strip():
            raise AIProviderError("Prompt cannot be empty")

        loop = asyncio.get_running_loop()

        for attempt in range(MAX_RETRIES):
            try:
                response = await loop.run_in_executor(
                    None,
                    lambda: self._model.generate_content(prompt),
                )
                return response.text.strip()
            except Exception as exc:
                error_str = str(exc).lower()

                # Handle rate limiting with exponential backoff
                if "429" in str(exc) or "rate_limit" in error_str or "quota" in error_str:
                    if attempt < MAX_RETRIES - 1:
                        wait_seconds = BASE_WAIT_SECONDS * (2 ** attempt)
                        logger.warning(
                            "gemini_rate_limited",
                            attempt=attempt + 1,
                            max_retries=MAX_RETRIES,
                            wait_seconds=wait_seconds,
                        )
                        await asyncio.sleep(wait_seconds)
                        continue

                # Log final error
                logger.error(
                    "gemini_completion_failed",
                    error=str(exc),
                    attempt=attempt + 1,
                )
                raise AIProviderError(f"Gemini failed: {exc}") from exc

        raise AIProviderError("Gemini: max retries exceeded")


class OpenAIProvider(BaseAIProvider):
    """
    Wraps OpenAI GPT-4o as the fallback provider.
    The openai SDK is natively async.
    """

    name = "openai"

    def __init__(self) -> None:
        if not settings.openai_api_key:
            logger.warning("openai_api_key_missing", provider="openai")
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def complete(self, prompt: str) -> str:
        """
        Run a chat completion against GPT-4o.
        Implements retry with exponential backoff for rate limiting.
        Uses semaphore to throttle concurrent requests and avoid rate limits.
        Reduced max_tokens to 800 (sufficient for summaries, saves ~60% token cost).
        """
        if not prompt or not prompt.strip():
            raise AIProviderError("Prompt cannot be empty")

        async with _ai_semaphore:  # Throttle: max 2 concurrent requests
            for attempt in range(MAX_RETRIES):
                try:
                    response = await self._client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=800,  # Reduced from 2048: sufficient for summaries, saves tokens
                        temperature=0.2,
                    )
                    content = response.choices[0].message.content
                    return (content or "").strip()
                except RateLimitError as exc:
                    # Handle rate limiting with exponential backoff
                    if attempt < MAX_RETRIES - 1:
                        wait_seconds = BASE_WAIT_SECONDS * (2 ** attempt)

                        # Respect Retry-After header if present
                        retry_after = getattr(exc, "retry_after", None)
                        if retry_after:
                            try:
                                wait_seconds = float(retry_after)
                            except (TypeError, ValueError):
                                pass

                        logger.warning(
                            "openai_rate_limited",
                            attempt=attempt + 1,
                            max_retries=MAX_RETRIES,
                            wait_seconds=wait_seconds,
                        )
                        await asyncio.sleep(wait_seconds)
                        continue

                    logger.error(
                        "openai_rate_limit_exceeded",
                        attempts=attempt + 1,
                        error=str(exc),
                    )
                    raise AIProviderError(
                        "OpenAI rate limit exceeded after retries"
                    ) from exc
                except Exception as exc:
                    logger.error(
                        "openai_completion_failed",
                        error=str(exc),
                        attempt=attempt + 1,
                    )
                    raise AIProviderError(f"OpenAI failed: {exc}") from exc

        raise AIProviderError("OpenAI: max retries exceeded")
