"""Answer generation helpers for TemporalGuard."""

from __future__ import annotations

from typing import Any, Dict


def generate_answer(question: str, context: Dict[str, Any] | None = None) -> str:
    del context
    return f"Scaffold answer for: {question}"
