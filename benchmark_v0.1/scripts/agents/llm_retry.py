"""Shared HTTP retry backoff for benchmark LLM adapters."""

from __future__ import annotations

import re


def retry_sleep_seconds(code: int, detail: str, attempt: int, *, base: float = 2.0) -> float:
    """Seconds to wait before retrying a rate-limited or transient API error."""
    if code == 429:
        match = re.search(r"try again in ([0-9.]+)\s*s", detail, re.IGNORECASE)
        if match:
            return float(match.group(1)) + 0.5
        return max(base ** attempt, 5.0)
    return base ** attempt
