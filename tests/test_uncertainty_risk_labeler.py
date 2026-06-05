import json

import pytest

from temporalguard.skills.uncertainty_risk_labeler import label_uncertainty_and_risk


@pytest.mark.parametrize(
    (
        "name",
        "question",
        "answer",
        "temporal_category",
        "freshness_payload",
        "verification_payload",
        "outdatedness_payload",
        "correction_payload",
        "expected_final_risk_label",
        "expected_dashboard_badge",
    ),
    [
        (
            "outdated corrected software version",
            "What is the latest Python version?",
            "Python 3.10 is the latest stable version.",
            "RECENT_ONLY",
            {"overall_freshness_score": 0.98, "overall_temporal_risk": "low"},
            {"overall_verification_status": "NEEDS_CORRECTION", "overall_confidence": 0.94},
            {
                "outdatedness_status": "OUTDATED",
                "is_outdated": True,
                "requires_correction": True,
                "answer_temporal_risk": "high",
            },
            {
                "correction_status": "corrected",
                "correction_type": "update_outdated_fact",
                "answer_temporal_risk": "medium",
                "confidence": 0.92,
                "warnings": [],
            },
            "medium_risk",
            "OUTDATED - CORRECTED",
        ),
        (
            "supported static answer",
            "What is binary search?",
            "Binary search divides a sorted search space in half.",
            "STATIC",
            {"overall_freshness_score": 0.85, "overall_temporal_risk": "low"},
            {"overall_verification_status": "SUPPORTED", "overall_confidence": 0.90},
            {
                "outdatedness_status": "NOT_OUTDATED",
                "is_outdated": False,
                "requires_correction": False,
                "answer_temporal_risk": "low",
            },
            {
                "correction_status": "no_correction_needed",
                "correction_type": "no_change",
                "answer_temporal_risk": "low",
                "confidence": 0.88,
                "warnings": [],
            },
            "safe",
            "SAFE",
        ),
        (
            "critical unverified visa claim",
            "Is this visa rule still active?",
            "Yes, this visa rule is still active.",
            "RECENT_ONLY",
            {"overall_freshness_score": 0.20, "overall_temporal_risk": "critical"},
            {"overall_verification_status": "INSUFFICIENT_EVIDENCE", "overall_confidence": 0.70},
            {
                "outdatedness_status": "UNVERIFIED_RISKY",
                "is_outdated": False,
                "requires_correction": True,
                "answer_temporal_risk": "critical",
            },
            {
                "correction_status": "unable_to_correct",
                "correction_type": "add_uncertainty",
                "answer_temporal_risk": "critical",
                "confidence": 0.30,
                "warnings": ["insufficient_evidence_for_high_risk_claim"],
            },
            "critical_risk",
            "CRITICAL - VERIFY OFFICIAL SOURCE",
        ),
        (
            "contradicted but corrected historical claim",
            "Who won the 2014 FIFA World Cup?",
            "France won the 2014 FIFA World Cup.",
            "HISTORICAL",
            {"overall_freshness_score": 0.90, "overall_temporal_risk": "low"},
            {"overall_verification_status": "NEEDS_CORRECTION", "overall_confidence": 0.93},
            {
                "outdatedness_status": "CONTRADICTED",
                "is_outdated": False,
                "requires_correction": True,
                "answer_temporal_risk": "high",
            },
            {
                "correction_status": "corrected",
                "correction_type": "fix_contradiction",
                "answer_temporal_risk": "medium",
                "confidence": 0.92,
                "warnings": [],
            },
            "medium_risk",
            "CONTRADICTION - CORRECTED",
        ),
        (
            "no factual claims",
            "Write a poem about rain.",
            "Rain falls softly on the silent street.",
            "STATIC",
            None,
            {"overall_verification_status": "NOT_VERIFIABLE", "overall_confidence": 0.90},
            {
                "outdatedness_status": "NOT_APPLICABLE",
                "is_outdated": False,
                "requires_correction": False,
                "answer_temporal_risk": "low",
            },
            {
                "correction_status": "no_correction_needed",
                "correction_type": "no_change",
                "answer_temporal_risk": "low",
                "confidence": 1.0,
                "warnings": [],
            },
            "safe",
            "NO FACTUAL CLAIMS",
        ),
        (
            "missing inputs unknown risk",
            "Who is the CEO of OpenAI?",
            "Sam Altman is the CEO of OpenAI.",
            "TIME_SENSITIVE",
            None,
            None,
            None,
            None,
            "unknown_risk",
            "UNKNOWN",
        ),
    ],
)
def test_label_uncertainty_and_risk_minimum_cases(
    name: str,
    question: str,
    answer: str,
    temporal_category: str,
    freshness_payload: dict | None,
    verification_payload: dict | None,
    outdatedness_payload: dict | None,
    correction_payload: dict | None,
    expected_final_risk_label: str,
    expected_dashboard_badge: str,
) -> None:
    del name
    result = label_uncertainty_and_risk(
        question,
        answer,
        temporal_category,
        freshness_payload,
        verification_payload,
        outdatedness_payload,
        correction_payload,
    )

    assert result["final_risk_label"] == expected_final_risk_label
    assert result["dashboard_badge"] == expected_dashboard_badge
    json.dumps(result)


def test_outdated_corrected_software_schema_values() -> None:
    result = label_uncertainty_and_risk(
        "What is the latest Python version?",
        "Python 3.10 is the latest stable version.",
        "RECENT_ONLY",
        {"overall_freshness_score": 0.98, "overall_temporal_risk": "low"},
        {"overall_verification_status": "NEEDS_CORRECTION", "overall_confidence": 0.94},
        {"outdatedness_status": "OUTDATED", "is_outdated": True, "requires_correction": True, "answer_temporal_risk": "high"},
        {"correction_status": "corrected", "correction_type": "update_outdated_fact", "answer_temporal_risk": "medium", "confidence": 0.92, "warnings": []},
    )

    assert result["final_risk_label"] == "medium_risk"
    assert result["uncertainty_label"] == "very_low"
    assert result["trust_score"] == 0.944
    assert result["temporal_safety_status"] == "show_with_caution"
    assert result["user_warning"] == "This answer was updated using checked evidence, but it may change again in the future."
    assert result["risk_reasons"] == [
        "original_answer_outdated",
        "correction_successful",
        "time_sensitive_question",
        "freshness_dependent",
    ]
    assert result["uncertainty_reasons"] == ["fresh_evidence_available"]
    assert result["recommended_user_action"] == "verify_official_source"
    assert result["high_risk_domain"] is False
    assert result["freshness_dependency"] == "high"
    assert result["label_confidence"] == 0.82


def test_supported_static_answer_is_safe() -> None:
    result = label_uncertainty_and_risk(
        "What is binary search?",
        "Binary search divides a sorted search space in half.",
        "STATIC",
        {"overall_freshness_score": 0.85, "overall_temporal_risk": "low"},
        {"overall_verification_status": "SUPPORTED", "overall_confidence": 0.90},
        {"outdatedness_status": "NOT_OUTDATED", "is_outdated": False, "requires_correction": False, "answer_temporal_risk": "low"},
        {"correction_status": "no_correction_needed", "correction_type": "no_change", "answer_temporal_risk": "low", "confidence": 0.88, "warnings": []},
    )

    assert result["final_risk_label"] == "safe"
    assert result["temporal_safety_status"] == "safe_to_show"
    assert result["user_warning"] is None
    assert result["recommended_user_action"] == "none"
    assert result["freshness_dependency"] == "none"


def test_critical_unverified_high_risk_warning_and_action() -> None:
    result = label_uncertainty_and_risk(
        "Is this visa rule still active?",
        "Yes, this visa rule is still active.",
        "RECENT_ONLY",
        {"overall_freshness_score": 0.20, "overall_temporal_risk": "critical"},
        {"overall_verification_status": "INSUFFICIENT_EVIDENCE", "overall_confidence": 0.70},
        {"outdatedness_status": "UNVERIFIED_RISKY", "is_outdated": False, "requires_correction": True, "answer_temporal_risk": "critical"},
        {"correction_status": "unable_to_correct", "correction_type": "add_uncertainty", "answer_temporal_risk": "critical", "confidence": 0.30, "warnings": ["insufficient_evidence_for_high_risk_claim"]},
    )

    assert result["final_risk_label"] == "critical_risk"
    assert result["uncertainty_label"] == "very_high"
    assert result["trust_score"] <= 0.49
    assert result["temporal_safety_status"] == "do_not_use_as_final"
    assert result["recommended_user_action"] == "consult_expert"
    assert result["high_risk_domain"] is True
    assert result["freshness_dependency"] == "critical"
    assert "high-risk topic" in result["user_warning"]


def test_no_factual_claims_not_applicable_output() -> None:
    result = label_uncertainty_and_risk(
        "Write a poem about rain.",
        "Rain falls softly on the silent street.",
        "STATIC",
        None,
        {"overall_verification_status": "NOT_VERIFIABLE", "overall_confidence": 0.90},
        {"outdatedness_status": "NOT_APPLICABLE", "is_outdated": False, "requires_correction": False, "answer_temporal_risk": "low"},
        {"correction_status": "no_correction_needed", "correction_type": "no_change", "answer_temporal_risk": "low", "confidence": 1.0, "warnings": []},
    )

    assert result["final_risk_label"] == "safe"
    assert result["uncertainty_label"] == "very_low"
    assert result["temporal_safety_status"] == "not_applicable"
    assert result["dashboard_badge"] == "NO FACTUAL CLAIMS"
    assert result["risk_reasons"] == ["not_applicable"]


def test_missing_time_sensitive_inputs_are_unknown() -> None:
    result = label_uncertainty_and_risk(
        "Who is the CEO of OpenAI?",
        "Sam Altman is the CEO of OpenAI.",
        "TIME_SENSITIVE",
        None,
        None,
        None,
        None,
    )

    assert result["final_risk_label"] == "unknown_risk"
    assert result["uncertainty_label"] == "unknown"
    assert result["trust_score"] == 0.0
    assert result["temporal_safety_status"] == "needs_more_evidence"
    assert result["dashboard_badge"] == "UNKNOWN"
    assert result["recommended_user_action"] == "retrieve_more_evidence"


def test_backward_compatible_default_call() -> None:
    assert label_uncertainty_and_risk("answer") == {"uncertainty": "low", "risk": "low"}
