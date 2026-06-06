"""Manual smoke test for a running TemporalGuard API backend.

Usage:
    python scripts/smoke_test_live_api.py --provider mock
"""

from __future__ import annotations

import argparse
import os
from typing import Any

import requests


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test TemporalGuard /analyze.")
    parser.add_argument("--api-url", default=os.getenv("TEMPORALGUARD_API_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--provider", default=os.getenv("DEFAULT_LLM_PROVIDER", "mock"))
    parser.add_argument("--model-name", default=os.getenv("DEFAULT_MODEL_NAME", ""))
    parser.add_argument("--question", default="What is the latest Python version?")
    args = parser.parse_args()

    payload = {
        "question": args.question,
        "base_answer": None,
        "llm_provider": args.provider,
        "model_name": args.model_name or None,
        "report_type": "dashboard",
    }
    response = requests.post(f"{args.api_url.rstrip('/')}/analyze", json=payload, timeout=30)
    response.raise_for_status()
    result: dict[str, Any] = response.json()

    print(f"provider: {args.provider}")
    print(f"generated answer: {result.get('original_answer', '')}")
    print(f"TemporalGuard badge: {_get(result, ['risk_label', 'dashboard_badge'], 'UNKNOWN')}")
    print(f"corrected answer: {_get(result, ['correction', 'corrected_answer'], '')}")
    print(f"pipeline status: {result.get('pipeline_status', 'unknown')}")


def _get(data: dict[str, Any], path: list[str], default: Any = None) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return default if current is None else current


if __name__ == "__main__":
    main()
