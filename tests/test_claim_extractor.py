import json

import pytest

from temporalguard.skills.claim_extractor import extract_claims


@pytest.mark.parametrize(
    ("question", "answer", "temporal_category", "expected_claim_type", "expected_evidence_need"),
    [
        (
            "What is the latest Python version?",
            "Python 3.10 is the latest stable version of Python.",
            "RECENT_ONLY",
            "software_version",
            "fresh",
        ),
        (
            "Who was the president of the USA in 2016?",
            "Barack Obama was the president of the United States in 2016.",
            "HISTORICAL",
            "historical_fact",
            "historical",
        ),
        (
            "What is binary search?",
            "Binary search is an algorithm that repeatedly divides a sorted search space in half to find a target value.",
            "STATIC",
            "definition",
            "optional",
        ),
        (
            "Is the Canada student visa SDS program still active?",
            "No, the Canada student visa SDS program is no longer active.",
            "RECENT_ONLY",
            "law_or_policy",
            "fresh",
        ),
        (
            "How do I use the OpenAI API in Python?",
            "The OpenAI Python SDK lets developers call OpenAI models from Python applications.",
            "VERSION_DEPENDENT",
            "api_or_library_behavior",
            "version_specific",
        ),
        (
            "What is the model result?",
            "The model achieved 92% accuracy and 0.89 F1-score on the test set.",
            "STATIC",
            "statistical_claim",
            "optional",
        ),
    ],
)
def test_extract_claims_minimum_cases(
    question: str,
    answer: str,
    temporal_category: str,
    expected_claim_type: str,
    expected_evidence_need: str,
) -> None:
    result = extract_claims(question, answer, temporal_category)

    assert result["total_claims"] >= 1
    assert result["claims"][0]["claim_type"] == expected_claim_type
    assert result["claims"][0]["evidence_need"] == expected_evidence_need
    assert result["claims"][0]["requires_verification"] is True
    json.dumps(result)


def test_no_factual_claims_returns_empty_schema() -> None:
    result = extract_claims(
        "Tell me something nice.",
        "Sure, I hope you have a wonderful day.",
        "STATIC",
    )

    assert result == {
        "claims": [],
        "total_claims": 0,
        "needs_verification": False,
        "notes": "No checkable factual claims extracted.",
    }


def test_latest_python_example_schema_fields() -> None:
    result = extract_claims(
        "What is the latest Python version?",
        "Python 3.10 is the latest stable version of Python.",
        "RECENT_ONLY",
    )
    claim = result["claims"][0]

    assert claim["claim_id"] == "C1"
    assert claim["claim_text"] == "Python 3.10 is the latest stable version of Python."
    assert claim["normalized_claim"] == "Python 3.10 is the latest stable Python version."
    assert claim["entities"] == ["Python", "Python 3.10"]
    assert claim["temporal_sensitivity"] == "high"
    assert claim["temporal_anchor"] == "latest"
    assert result["needs_verification"] is True


def test_static_definition_makes_verification_optional() -> None:
    result = extract_claims(
        "What is binary search?",
        "Binary search is an algorithm that repeatedly divides a sorted search space in half to find a target value.",
        "STATIC",
    )

    assert result["total_claims"] == 1
    assert result["claims"][0]["temporal_sensitivity"] == "low"
    assert result["claims"][0]["evidence_need"] == "optional"
    assert result["needs_verification"] is False


def test_compound_reason_sentence_splits_into_atomic_claims() -> None:
    result = extract_claims(
        "Explain why Python is useful.",
        "Python is popular because it has simple syntax, many libraries, and strong support for data science.",
        "STATIC",
    )

    assert result["total_claims"] == 3
    assert [claim["claim_text"] for claim in result["claims"]] == [
        "Python has simple syntax.",
        "Python has many libraries.",
        "Python has strong support for data science.",
    ]


def test_duplicate_claims_are_extracted_once() -> None:
    result = extract_claims(
        "Who is the CEO of OpenAI?",
        "Sam Altman is the CEO of OpenAI. Sam Altman is the CEO of OpenAI.",
        "TIME_SENSITIVE",
    )

    assert result["total_claims"] == 1
    assert result["claims"][0]["claim_id"] == "C1"


def test_max_claims_is_limited_and_renumbered() -> None:
    result = extract_claims(
        "What changed?",
        (
            "Python 3.10 is the latest stable version of Python. "
            "Sam Altman is the CEO of OpenAI. "
            "The policy is still active."
        ),
        "RECENT_ONLY",
        max_claims=2,
    )

    assert result["total_claims"] == 2
    assert [claim["claim_id"] for claim in result["claims"]] == ["C1", "C2"]


def test_invalid_input_is_safe() -> None:
    result = extract_claims("Question", None)

    assert result["claims"] == []
    assert result["needs_verification"] is False
