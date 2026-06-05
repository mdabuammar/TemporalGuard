"""Uncertainty and risk labeling scaffold."""

from __future__ import annotations

from typing import Any, Dict


def label_uncertainty_and_risk(answer: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
    del answer, context
    return {"uncertainty": "low", "risk": "low"}
