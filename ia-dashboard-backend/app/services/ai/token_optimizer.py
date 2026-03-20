"""
app/services/ai/token_optimizer.py

Utilities to estimate and optimize token usage before sending to AI models.
Prevents hitting rate limits and quota errors.
"""

import json
from typing import Any


# Rough token estimation: 1 token ≈ 4 characters for English
# This is a heuristic - actual token count depends on the tokenizer
CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """
    Quick token estimate for a text string.
    Useful to check if payload might exceed limits before sending.

    Note: This is an estimate. Actual token count from OpenAI's tokenizer
    could differ by ±10-20%.
    """
    return len(text) // CHARS_PER_TOKEN


def estimate_dict_tokens(data: dict[str, Any]) -> int:
    """Estimate tokens for a dictionary (typically JSON payload)."""
    json_str = json.dumps(data, ensure_ascii=False)
    return estimate_tokens(json_str)


def check_payload_size(
    data: dict[str, Any],
    max_tokens: int = 8000,
    warn_threshold: float = 0.75,
) -> dict[str, Any]:
    """
    Check payload size before sending to AI.

    Returns:
        dict with keys:
        - estimated_tokens: predicted token count
        - size_bytes: JSON byte size
        - exceeds_limit: bool, true if estimated_tokens > max_tokens
        - warning: bool, true if estimated_tokens > max_tokens * warn_threshold
    """
    estimated = estimate_dict_tokens(data)
    size_bytes = len(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    return {
        "estimated_tokens": estimated,
        "size_bytes": size_bytes,
        "exceeds_limit": estimated > max_tokens,
        "warning": estimated > int(max_tokens * warn_threshold),
        "max_tokens": max_tokens,
    }
