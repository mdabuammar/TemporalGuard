"""Temporal verification scaffold."""

from __future__ import annotations

from typing import Any, Dict


def verify_temporal_claim(claim: str, evidence: list[dict[str, Any]]) -> Dict[str, Any]:
    del claim, evidence
    return {"verified": False, "reason": "scaffold"}
