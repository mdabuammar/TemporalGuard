"""Correction generation scaffold."""

from __future__ import annotations

from typing import Any, Dict


def generate_correction(answer: str, evidence: list[dict[str, Any]]) -> Dict[str, Any]:
    del evidence
    return {"answer": answer, "corrected": False}
