"""Evaluation metrics scaffold."""

from __future__ import annotations

from typing import Any, Dict


def compute_metrics(predictions: list[Any], references: list[Any]) -> Dict[str, float]:
    del predictions, references
    return {}
