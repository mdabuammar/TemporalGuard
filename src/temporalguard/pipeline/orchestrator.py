"""Pipeline orchestration entry points."""

from __future__ import annotations

from typing import Any, Dict


def run_pipeline(question: str, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    del config
    return {
        "question": question,
        "status": "scaffold",
        "answer": "TemporalGuard scaffold is ready.",
    }
