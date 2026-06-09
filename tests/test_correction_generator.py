import json

import pytest

from temporalguard.skills.correction_generator import generate_correction


@pytest.mark.parametrize(
    (
        "name",
        "question",
        "answer",
        "temporal_category",
        "verification_payload",
        "outdatedness_payload",
        "expected_correction_status",
        "expected_correction_type",
    ),
    [
        (
            "correct outdated Python version",
            "What is the latest Python version?",
            "Python 3.10 is the latest stable version of Python.",
            "RECENT_ONLY",
            {
                "verification_results": [
                    {
                        "claim_id": "C1",
                        "claim_text": "Python 3.10 is the latest stable version of Python.",
                        "verification_status": "OUTDATED",
                        "claim_value": "Python 3.10",
                        "evidence_value": "Python 3.13.5",
                        "risk_level": "high",
                        "verification_confidence": 0.94,
                        "requires_correction": True,
                    }
                ]
            },
            {"outdatedness_status": "OUTDATED", "requires_correction": True, "answer_temporal_risk": "high"},
            "corrected",
            "update_outdated_fact",
        ),
        (
            "correct contradicted world cup winner",
            "Who won the 2014 FIFA World Cup?",
            "France won the 2014 FIFA World Cup.",
            "HISTORICAL",
            {
                "verification_results": [
                    {
                        "claim_id": "C1",
                        "claim_text": "France won the 2014 FIFA World Cup.",
                        "verification_status": "CONTRADICTED",
                        "claim_value": "France",
                        "evidence_value": "Germany",
                        "risk_level": "high",
                        "verification_confidence": 0.93,
                        "requires_correction": True,
                    }
                ]
            },
            {"outdatedness_status": "CONTRADICTED", "requires_correction": True, "answer_temporal_risk": "high"},
            "corrected",
            "fix_contradiction",
        ),
        (
            "unable to correct high risk visa claim",
            "Is this visa rule still active?",
            "Yes, this visa rule is still active.",
            "RECENT_ONLY",
            {
                "verification_results": [
                    {
                        "claim_id": "C1",
                        "claim_text": "This visa rule is still active.",
                        "verification_status": "INSUFFICIENT_EVIDENCE",
                        "risk_level": "critical",
                        "verification_confidence": 0.75,
                        "requires_correction": True,
                    }
                ]
            },
            {"outdatedness_status": "UNVERIFIED_RISKY", "requires_correction": True, "answer_temporal_risk": "critical"},
            "unable_to_correct",
            "add_uncertainty",
        ),
        (
            "no correction needed static answer",
            "What is binary search?",
            "Binary search divides a sorted search space in half.",
            "STATIC",
            {
                "verification_results": [
                    {
                        "claim_id": "C1",
                        "claim_text": "Binary search divides a sorted search space in half.",
                        "verification_status": "SUPPORTED",
                        "risk_level": "low",
                        "verification_confidence": 0.88,
                        "requires_correction": False,
                    }
                ]
            },
            {"outdatedness_status": "NOT_OUTDATED", "requires_correction": False, "answer_temporal_risk": "low"},
            "no_correction_needed",
            "no_change",
        ),
        (
            "partially corrected mixed answer",
            "What is the latest Python version and why is Python useful?",
            "Python 3.10 is the latest version. Python is widely used in data science.",
            "RECENT_ONLY",
            {
                "verification_results": [
                    {
                        "claim_id": "C1",
                        "claim_text": "Python 3.10 is the latest version.",
                        "verification_status": "OUTDATED",
                        "claim_value": "Python 3.10",
                        "evidence_value": "Python 3.13.5",
                        "risk_level": "high",
                        "verification_confidence": 0.92,
                        "requires_correction": True,
                    },
                    {
                        "claim_id": "C2",
                        "claim_text": "Python is widely used in data science.",
                        "verification_status": "SUPPORTED",
                        "risk_level": "low",
                        "verification_confidence": 0.86,
                        "requires_correction": False,
                    },
                ]
            },
            {"outdatedness_status": "PARTIALLY_OUTDATED", "requires_correction": True, "answer_temporal_risk": "high"},
            "partially_corrected",
            "partial_revision",
        ),
    ],
)
def test_generate_correction_minimum_cases(
    name: str,
    question: str,
    answer: str,
    temporal_category: str,
    verification_payload: dict,
    outdatedness_payload: dict,
    expected_correction_status: str,
    expected_correction_type: str,
) -> None:
    del name
    result = generate_correction(
        question,
        answer,
        verification_payload,
        outdatedness_payload,
        temporal_category=temporal_category,
    )

    assert result["correction_status"] == expected_correction_status
    assert result["correction_type"] == expected_correction_type
    json.dumps(result)


def test_outdated_python_correction_uses_evidence_value_and_schema() -> None:
    result = generate_correction(
        "What is the latest Python version?",
        "Python 3.10 is the latest stable version of Python.",
        {
            "verification_results": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python 3.10 is the latest stable version of Python.",
                    "verification_status": "OUTDATED",
                    "claim_value": "Python 3.10",
                    "evidence_value": "Python 3.13.5",
                    "risk_level": "high",
                    "verification_confidence": 0.94,
                    "requires_correction": True,
                }
            ]
        },
        {"outdatedness_status": "OUTDATED", "requires_correction": True, "answer_temporal_risk": "high"},
        evidence_payload={
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "title": "Download Python",
                            "url": "https://www.python.org/downloads/",
                            "publisher": "Python Software Foundation",
                            "source_type": "official",
                            "updated_date": "2026-06-01",
                            "relevance_score": 0.95,
                        }
                    ],
                }
            ]
        },
        temporal_category="RECENT_ONLY",
    )

    assert "Python 3.13.5" in result["corrected_answer"]
    assert "Python 3.14" not in result["corrected_answer"]
    assert result["changed_claim_ids"] == ["C1"]
    assert result["unchanged_claim_ids"] == []
    assert result["unsupported_claim_ids"] == []
    assert result["evidence_used"] == [
        {
            "claim_id": "C1",
            "evidence_id": "E1",
            "title": "Download Python",
            "url": "https://www.python.org/downloads/",
            "publisher": "Python Software Foundation",
            "date_used": "2026-06-01",
            "source_type": "official",
        }
    ]
    assert result["uncertainty_note"] is None
    assert result["safety_note"] is None
    assert result["answer_temporal_risk"] == "medium"
    assert result["confidence"] == 0.94
    assert result["warnings"] == []


def test_high_risk_insufficient_evidence_adds_safety_note() -> None:
    result = generate_correction(
        "Is this visa rule still active?",
        "Yes, this visa rule is still active.",
        {
            "verification_results": [
                {
                    "claim_id": "C1",
                    "claim_text": "This visa rule is still active.",
                    "verification_status": "INSUFFICIENT_EVIDENCE",
                    "risk_level": "critical",
                    "verification_confidence": 0.75,
                    "requires_correction": True,
                }
            ]
        },
        {"outdatedness_status": "UNVERIFIED_RISKY", "requires_correction": True, "answer_temporal_risk": "critical"},
        temporal_category="RECENT_ONLY",
    )

    assert result["correction_status"] == "unable_to_correct"
    assert result["changed_claim_ids"] == []
    assert result["unsupported_claim_ids"] == ["C1"]
    assert result["uncertainty_note"] == "The claim could not be verified safely."
    assert result["safety_note"] is not None
    assert result["answer_temporal_risk"] == "critical"
    assert result["confidence"] == 0.35
    assert result["warnings"] == ["insufficient_evidence_for_high_risk_claim"]


def test_partial_correction_keeps_supported_claim() -> None:
    result = generate_correction(
        "What is the latest Python version and why is Python useful?",
        "Python 3.10 is the latest version. Python is widely used in data science.",
        {
            "verification_results": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python 3.10 is the latest version.",
                    "verification_status": "OUTDATED",
                    "claim_value": "Python 3.10",
                    "evidence_value": "Python 3.13.5",
                    "risk_level": "high",
                    "verification_confidence": 0.92,
                    "requires_correction": True,
                },
                {
                    "claim_id": "C2",
                    "claim_text": "Python is widely used in data science.",
                    "verification_status": "SUPPORTED",
                    "risk_level": "low",
                    "verification_confidence": 0.86,
                    "requires_correction": False,
                },
            ]
        },
        {"outdatedness_status": "PARTIALLY_OUTDATED", "requires_correction": True, "answer_temporal_risk": "high"},
        temporal_category="RECENT_ONLY",
    )

    assert "Python 3.13.5" in result["corrected_answer"]
    assert "Python is widely used in data science." in result["corrected_answer"]
    assert result["changed_claim_ids"] == ["C1"]
    assert result["unchanged_claim_ids"] == ["C2"]
    assert result["confidence"] == 0.74


def test_missing_evidence_value_does_not_invent_correction() -> None:
    result = generate_correction(
        "What is the latest package version?",
        "Package 1.0 is the latest version.",
        {
            "verification_results": [
                {
                    "claim_id": "C1",
                    "claim_text": "Package 1.0 is the latest version.",
                    "verification_status": "OUTDATED",
                    "claim_value": "Package 1.0",
                    "evidence_value": None,
                    "risk_level": "high",
                    "verification_confidence": 0.70,
                    "requires_correction": True,
                }
            ]
        },
        {"outdatedness_status": "OUTDATED", "requires_correction": True, "answer_temporal_risk": "high"},
        temporal_category="RECENT_ONLY",
    )

    assert result["correction_status"] == "unable_to_correct"
    assert "Package 2.0" not in result["corrected_answer"]
    assert result["warnings"] == ["missing_evidence_value_for_correction"]


def test_no_correction_needed_returns_original_answer() -> None:
    answer = "Binary search divides a sorted search space in half."
    result = generate_correction(
        "What is binary search?",
        answer,
        {
            "verification_results": [
                {
                    "claim_id": "C1",
                    "claim_text": answer,
                    "verification_status": "SUPPORTED",
                    "risk_level": "low",
                    "verification_confidence": 0.88,
                    "requires_correction": False,
                }
            ]
        },
        {"outdatedness_status": "NOT_OUTDATED", "requires_correction": False, "answer_temporal_risk": "low"},
        temporal_category="STATIC",
    )

    assert result["corrected_answer"] == answer
    assert result["correction_status"] == "no_correction_needed"
    assert result["unchanged_claim_ids"] == ["C1"]


def test_backward_compatible_call_preserves_answer() -> None:
    assert generate_correction("answer", []) == {"answer": "answer", "corrected": False}


def test_world_cup_correction_is_direct_final_answer() -> None:
    result = generate_correction(
        "Who won the 2014 FIFA World Cup?",
        "France won the 2014 FIFA World Cup.",
        {
            "verification_results": [
                {
                    "claim_id": "C1",
                    "claim_text": "France won the 2014 FIFA World Cup.",
                    "verification_status": "CONTRADICTED",
                    "claim_value": "France",
                    "evidence_value": "Germany",
                    "risk_level": "high",
                    "requires_correction": True,
                }
            ]
        },
        {"outdatedness_status": "CONTRADICTED", "requires_correction": True, "answer_temporal_risk": "high"},
        temporal_category="HISTORICAL",
    )

    assert result["corrected_answer"] == "Germany won the 2014 FIFA World Cup."


def test_who_pheic_correction_mentions_actual_date() -> None:
    result = generate_correction(
        "When did WHO end the COVID-19 public health emergency of international concern?",
        "WHO ended it in 2022.",
        {
            "verification_results": [
                {
                    "claim_id": "C1",
                    "claim_text": "WHO ended it in 2022.",
                    "verification_status": "CONTRADICTED",
                    "claim_value": "2022",
                    "evidence_value": "May 5, 2023",
                    "risk_level": "high",
                    "requires_correction": True,
                }
            ]
        },
        {"outdatedness_status": "CONTRADICTED", "requires_correction": True, "answer_temporal_risk": "high"},
        temporal_category="HISTORICAL",
    )

    assert result["corrected_answer"] == (
        "WHO ended the COVID-19 public health emergency of international concern on May 5, 2023."
    )


def test_node_lifecycle_correction_is_user_friendly() -> None:
    result = generate_correction(
        "Is Node.js 18 still actively supported?",
        "Yes, Node.js 18 is still active LTS.",
        {
            "verification_results": [
                {
                    "claim_id": "C1",
                    "claim_text": "Yes, Node.js 18 is still active LTS.",
                    "verification_status": "OUTDATED",
                    "claim_value": "active LTS",
                    "evidence_value": "end-of-life on April 30, 2025",
                    "risk_level": "high",
                    "requires_correction": True,
                }
            ]
        },
        {"outdatedness_status": "OUTDATED", "requires_correction": True, "answer_temporal_risk": "high"},
        temporal_category="RECENT_ONLY",
    )

    assert result["corrected_answer"] == (
        "Node.js 18 is no longer actively supported. It reached end-of-life on April 30, 2025."
    )


def test_pandas_append_correction_is_direct() -> None:
    result = generate_correction(
        "Does pandas 2.0 still support DataFrame.append?",
        "Yes, pandas 2.0 still supports DataFrame.append.",
        {
            "verification_results": [
                {
                    "claim_id": "C1",
                    "claim_text": "Yes, pandas 2.0 still supports DataFrame.append.",
                    "verification_status": "CONTRADICTED",
                    "claim_value": "DataFrame.append is supported",
                    "evidence_value": "DataFrame.append was removed in pandas 2.0; use pandas.concat",
                    "risk_level": "high",
                    "requires_correction": True,
                }
            ]
        },
        {"outdatedness_status": "CONTRADICTED", "requires_correction": True, "answer_temporal_risk": "high"},
        temporal_category="VERSION_DEPENDENT",
    )

    assert result["corrected_answer"] == "DataFrame.append was removed in pandas 2.0. Use pandas.concat instead."
