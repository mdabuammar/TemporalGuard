"""Streamlit helper utilities."""

from __future__ import annotations

from typing import Any, Dict


def build_dashboard_state(context: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return dict(context or {})
