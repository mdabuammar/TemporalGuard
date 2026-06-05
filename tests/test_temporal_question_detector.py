import json

import pytest

from temporalguard.skills.temporal_question_detector import (
    detect_temporal_category,
    detect_temporal_question,
)


@pytest.mark.parametrize(
    ("question", "expected_category"),
    [
        ("What is machine learning?", "STATIC"),
        ("Explain binary search in easy words.", "STATIC"),
        ("Who is the CEO of Microsoft?", "TIME_SENSITIVE"),
        ("What is the latest Python version?", "RECENT_ONLY"),
        ("What happened in AI today?", "RECENT_ONLY"),
        ("What was the latest Python version in 2020?", "HISTORICAL"),
        ("Who was the president of USA in 2016?", "HISTORICAL"),
        ("How do I use the OpenAI API in Python?", "VERSION_DEPENDENT"),
        ("Is this pandas function deprecated?", "VERSION_DEPENDENT"),
        ("Is this visa rule still active?", "RECENT_ONLY"),
        ("What is the current inflation rate?", "RECENT_ONLY"),
        ("Tell me about Apple.", "UNKNOWN"),
    ],
)
def test_detect_temporal_category_minimum_cases(question: str, expected_category: str) -> None:
    result = detect_temporal_category(question)

    assert result["temporal_category"] == expected_category


def test_static_question_schema_and_action() -> None:
    result = detect_temporal_category("What is binary search?")

    assert result == {
        "temporal_category": "STATIC",
        "needs_fresh_evidence": False,
        "confidence": 0.95,
        "reason": "This is a stable educational concept.",
        "temporal_signals": [],
        "temporal_anchor": None,
        "recommended_next_action": "answer_directly",
    }
    json.dumps(result)


def test_historical_anchor_is_preserved() -> None:
    result = detect_temporal_category("What did the policy say during 2021?")

    assert result["temporal_category"] == "HISTORICAL"
    assert result["needs_fresh_evidence"] is True
    assert result["temporal_anchor"] == "2021"
    assert result["recommended_next_action"] == "retrieve_historical_evidence"


def test_version_anchor_is_preserved() -> None:
    result = detect_temporal_category("What is the syntax for TensorFlow 2.15?")

    assert result["temporal_category"] == "VERSION_DEPENDENT"
    assert result["temporal_anchor"] == "TensorFlow 2.15"
    assert "TensorFlow" in result["temporal_signals"]


def test_high_risk_domain_is_time_sensitive_without_current_word() -> None:
    result = detect_temporal_category("What visa requirements apply for Canada?")

    assert result["temporal_category"] == "TIME_SENSITIVE"
    assert result["needs_fresh_evidence"] is True
    assert "visa" in result["temporal_signals"]


def test_empty_and_invalid_questions_are_unknown() -> None:
    for question in ("", "   ", None):
        result = detect_temporal_category(question)  # type: ignore[arg-type]

        assert result["temporal_category"] == "UNKNOWN"
        assert result["recommended_next_action"] == "ask_clarifying_question"
        assert result["needs_fresh_evidence"] is True


def test_ambiguous_short_questions_are_unknown() -> None:
    for question in ("Apple", "What about Java?", "Tell me about Mercury."):
        result = detect_temporal_category(question)

        assert result["temporal_category"] == "UNKNOWN"
        assert result["confidence"] < 0.70


def test_backward_compatible_wrapper_returns_category_string() -> None:
    assert detect_temporal_question("What is the latest Python version?") == "RECENT_ONLY"
