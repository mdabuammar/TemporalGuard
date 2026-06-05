import json

import pytest

from temporalguard.skills.outdated_answer_detector import detect_outdated_answer


@pytest.mark.parametrize(
    ("name", "question", "answer", "temporal_category", "claims_payload", "verification_payload", "expected_status"),
    [
        (
            "outdated latest Python answer",
            "What is the latest Python version?",
            "Python 3.10 is the latest stable version of Python.",
            "RECENT_ONLY",
            {
                "claims": [
                    {
                        "claim_id": "C1",
                        "claim_type": "software_version",
                        "temporal_sensitivity": "high",
                        "evidence_need": "fresh",
                    }
                ]
            },
            {
                "verification_results": [
                    {
                        "claim_id": "C1",
                        "verification_status": "OUTDATED",
                        "verification_confidence": 0.94,
                        "risk_level": "high",
                        "requires_correction": True,
                    }
                ]
            },
            "OUTDATED",
        ),
        (
            "partially outdated mixed answer",
            "What is the latest Python version and why is Python useful?",
            "Python 3.10 is the latest version. Python is widely used in data science.",
            "RECENT_ONLY",
            {
                "claims": [
                    {
                        "claim_id": "C1",
                        "claim_type": "software_version",
                        "temporal_sensitivity": "high",
                        "evidence_need": "fresh",
                    },
                    {
                        "claim_id": "C2",
                        "claim_type": "general_fact",
                        "temporal_sensitivity": "medium",
                        "evidence_need": "optional",
                    },
                ]
            },
            {
                "verification_results": [
                    {
                        "claim_id": "C1",
                        "verification_status": "OUTDATED",
                        "verification_confidence": 0.92,
                        "risk_level": "high",
                        "requires_correction": True,
                    },
                    {
                        "claim_id": "C2",
                        "verification_status": "SUPPORTED",
                        "verification_confidence": 0.86,
                        "risk_level": "low",
                        "requires_correction": False,
                    },
                ]
            },
            "PARTIALLY_OUTDATED",
        ),
        (
            "contradicted world cup answer",
            "Who won the 2014 FIFA World Cup?",
            "France won the 2014 FIFA World Cup.",
            "HISTORICAL",
            {
                "claims": [
                    {
                        "claim_id": "C1",
                        "claim_type": "event_result",
                        "temporal_sensitivity": "low",
                        "evidence_need": "historical",
                    }
                ]
            },
            {
                "verification_results": [
                    {
                        "claim_id": "C1",
                        "verification_status": "CONTRADICTED",
                        "verification_confidence": 0.93,
                        "risk_level": "high",
                        "requires_correction": True,
                    }
                ]
            },
            "CONTRADICTED",
        ),
        (
            "high risk unverified visa answer",
            "Is this visa rule still active?",
            "Yes, this visa rule is still active.",
            "RECENT_ONLY",
            {
                "claims": [
                    {
                        "claim_id": "C1",
                        "claim_type": "law_or_policy",
                        "temporal_sensitivity": "high",
                        "evidence_need": "fresh",
                    }
                ]
            },
            {
                "verification_results": [
                    {
                        "claim_id": "C1",
                        "verification_status": "INSUFFICIENT_EVIDENCE",
                        "verification_confidence": 0.75,
                        "risk_level": "critical",
                        "requires_correction": True,
                    }
                ]
            },
            "UNVERIFIED_RISKY",
        ),
        (
            "supported static answer",
            "What is binary search?",
            "Binary search divides a sorted search space in half.",
            "STATIC",
            {
                "claims": [
                    {
                        "claim_id": "C1",
                        "claim_type": "definition",
                        "temporal_sensitivity": "low",
                        "evidence_need": "optional",
                    }
                ]
            },
            {
                "verification_results": [
                    {
                        "claim_id": "C1",
                        "verification_status": "SUPPORTED",
                        "verification_confidence": 0.88,
                        "risk_level": "low",
                        "requires_correction": False,
                    }
                ]
            },
            "NOT_OUTDATED",
        ),
        (
            "no factual claims creative answer",
            "Write a poem about rain.",
            "Rain falls softly on the silent street.",
            "STATIC",
            {"claims": []},
            {"verification_results": []},
            "NOT_APPLICABLE",
        ),
        (
            "factual question no claims",
            "Who is the CEO of OpenAI?",
            "I am not sure.",
            "TIME_SENSITIVE",
            {"claims": []},
            {"verification_results": []},
            "NOT_ENOUGH_INFORMATION",
        ),
    ],
)
def test_detect_outdated_answer_minimum_cases(
    name: str,
    question: str,
    answer: str,
    temporal_category: str,
    claims_payload: dict,
    verification_payload: dict,
    expected_status: str,
) -> None:
    del name
    result = detect_outdated_answer(question, answer, verification_payload, claims_payload, temporal_category)

    assert isinstance(result, dict)
    assert result["outdatedness_status"] == expected_status
    json.dumps(result)


def test_outdated_answer_schema_fields() -> None:
    result = detect_outdated_answer(
        "What is the latest Python version?",
        "Python 3.10 is the latest stable version of Python.",
        {
            "verification_results": [
                {
                    "claim_id": "C1",
                    "verification_status": "OUTDATED",
                    "verification_confidence": 0.94,
                    "risk_level": "high",
                    "requires_correction": True,
                }
            ]
        },
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_type": "software_version",
                    "temporal_sensitivity": "high",
                    "evidence_need": "fresh",
                }
            ]
        },
        "RECENT_ONLY",
    )

    assert result["outdatedness_status"] == "OUTDATED"
    assert result["is_outdated"] is True
    assert result["requires_correction"] is True
    assert result["answer_temporal_risk"] == "high"
    assert result["outdated_claim_ids"] == ["C1"]
    assert result["contradicted_claim_ids"] == []
    assert result["unsupported_claim_ids"] == []
    assert result["supported_claim_ids"] == []
    assert result["critical_claim_ids"] == []
    assert result["confidence"] == 0.94
    assert result["recommended_next_action"] == "generate_correction"
    assert result["answer_level_summary"] == {
        "total_claims": 1,
        "supported_count": 0,
        "outdated_count": 1,
        "contradicted_count": 0,
        "partially_supported_count": 0,
        "insufficient_evidence_count": 0,
        "not_verifiable_count": 0,
    }
    assert result["warnings"] == []


def test_high_risk_unsupported_sets_critical_and_request_more_evidence() -> None:
    result = detect_outdated_answer(
        "Is this visa rule still active?",
        "Yes, this visa rule is still active.",
        {
            "verification_results": [
                {
                    "claim_id": "C1",
                    "verification_status": "INSUFFICIENT_EVIDENCE",
                    "verification_confidence": 0.75,
                    "risk_level": "critical",
                    "requires_correction": True,
                }
            ]
        },
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_type": "law_or_policy",
                    "temporal_sensitivity": "high",
                    "evidence_need": "fresh",
                }
            ]
        },
        "RECENT_ONLY",
    )

    assert result["outdatedness_status"] == "UNVERIFIED_RISKY"
    assert result["is_outdated"] is False
    assert result["requires_correction"] is True
    assert result["answer_temporal_risk"] == "critical"
    assert result["unsupported_claim_ids"] == ["C1"]
    assert result["critical_claim_ids"] == ["C1"]
    assert result["recommended_next_action"] == "request_more_evidence"


def test_not_applicable_for_all_not_verifiable_results() -> None:
    result = detect_outdated_answer(
        "Which language is best?",
        "Python is the best language.",
        {
            "verification_results": [
                {
                    "claim_id": "C1",
                    "verification_status": "NOT_VERIFIABLE",
                    "verification_confidence": 0.60,
                    "risk_level": "unknown",
                    "requires_correction": False,
                }
            ]
        },
        {"claims": [{"claim_id": "C1", "claim_type": "other"}]},
        "STATIC",
    )

    assert result["outdatedness_status"] == "NOT_APPLICABLE"
    assert result["requires_correction"] is False
    assert result["recommended_next_action"] == "no_action"


def test_missing_verification_for_time_sensitive_question_needs_information() -> None:
    result = detect_outdated_answer(
        "Who is the CEO of OpenAI?",
        "I am not sure.",
        {"verification_results": []},
        {"claims": []},
        "TIME_SENSITIVE",
    )

    assert result["outdatedness_status"] == "NOT_ENOUGH_INFORMATION"
    assert result["requires_correction"] is True
    assert result["recommended_next_action"] == "request_more_evidence"
    assert result["warnings"] == ["No verification results supplied."]


def test_backward_compatible_boolean_call() -> None:
    assert detect_outdated_answer("answer", []) is False
