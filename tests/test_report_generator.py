import json

import pytest

from temporalguard.reporting.report_generator import generate_report


def _outdated_python_pipeline() -> dict:
    return {
        "example_id": "EX001",
        "question": "What is the latest Python version?",
        "original_answer": "Python 3.10 is the latest stable version of Python.",
        "temporal_detection": {"temporal_category": "RECENT_ONLY", "needs_fresh_evidence": True},
        "claims": {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python 3.10 is the latest stable version of Python.",
                    "claim_type": "software_version",
                }
            ],
            "total_claims": 1,
        },
        "evidence": {
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
                            "evidence_summary": "The official Python downloads page lists Python 3.13.5 as the latest release.",
                        }
                    ],
                }
            ]
        },
        "freshness": {
            "freshness_results": [
                {
                    "claim_id": "C1",
                    "evidence_scores": [
                        {
                            "evidence_id": "E1",
                            "date_used": "2026-06-01",
                            "freshness_label": "very_fresh",
                            "combined_score": 0.98,
                        }
                    ],
                }
            ],
            "overall_freshness_score": 0.98,
        },
        "verification": {
            "verification_results": [
                {
                    "claim_id": "C1",
                    "verification_status": "OUTDATED",
                    "risk_level": "high",
                    "requires_correction": True,
                    "claim_value": "Python 3.10",
                    "evidence_value": "Python 3.13.5",
                    "reason": "The claim says Python 3.10 is latest, but official evidence lists Python 3.13.5 as latest.",
                }
            ],
            "overall_verification_status": "NEEDS_CORRECTION",
            "overall_confidence": 0.94,
        },
        "outdatedness": {
            "outdatedness_status": "OUTDATED",
            "is_outdated": True,
            "requires_correction": True,
            "answer_temporal_risk": "high",
        },
        "correction": {
            "corrected_answer": (
                "Python 3.10 is not the latest stable Python version. "
                "Based on the checked official evidence, Python 3.13.5 is listed as the latest release."
            ),
            "correction_status": "corrected",
            "changed_claim_ids": ["C1"],
            "unsupported_claim_ids": [],
            "freshness_note": "The correction uses checked evidence for a current software-version claim.",
            "uncertainty_note": None,
            "safety_note": None,
            "user_visible_explanation": "The original answer was outdated because the claimed latest version differed from the checked evidence.",
        },
        "risk_label": {
            "final_risk_label": "medium_risk",
            "uncertainty_label": "low",
            "trust_score": 0.93,
            "temporal_safety_status": "show_with_caution",
            "user_warning": "This answer was updated using checked evidence, but software versions can change again.",
            "dashboard_badge": "OUTDATED - CORRECTED",
        },
    }


def _safe_static_pipeline() -> dict:
    return {
        "example_id": "EX002",
        "question": "What is binary search?",
        "original_answer": "Binary search divides a sorted search space in half.",
        "temporal_detection": {"temporal_category": "STATIC", "needs_fresh_evidence": False},
        "claims": {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Binary search divides a sorted search space in half.",
                    "claim_type": "definition",
                }
            ],
            "total_claims": 1,
        },
        "verification": {
            "verification_results": [
                {
                    "claim_id": "C1",
                    "verification_status": "SUPPORTED",
                    "risk_level": "low",
                    "requires_correction": False,
                }
            ],
            "overall_verification_status": "SUPPORTED",
            "overall_confidence": 0.90,
        },
        "outdatedness": {
            "outdatedness_status": "NOT_OUTDATED",
            "is_outdated": False,
            "requires_correction": False,
            "answer_temporal_risk": "low",
        },
        "correction": {
            "corrected_answer": "Binary search divides a sorted search space in half.",
            "correction_status": "no_correction_needed",
            "changed_claim_ids": [],
            "unsupported_claim_ids": [],
            "freshness_note": "No temporal correction was needed for this stable concept.",
            "uncertainty_note": None,
            "safety_note": None,
            "user_visible_explanation": "The answer did not appear outdated based on the verification result.",
        },
        "risk_label": {
            "final_risk_label": "safe",
            "uncertainty_label": "very_low",
            "trust_score": 0.91,
            "temporal_safety_status": "safe_to_show",
            "user_warning": None,
            "dashboard_badge": "SAFE",
        },
    }


@pytest.mark.parametrize(
    ("name", "pipeline_output", "report_type", "expected_badge"),
    [
        ("outdated corrected python report", _outdated_python_pipeline(), "dashboard", "OUTDATED - CORRECTED"),
        ("safe static report", _safe_static_pipeline(), "thesis", "SAFE"),
    ],
)
def test_generate_report_minimum_cases(name: str, pipeline_output: dict, report_type: str, expected_badge: str) -> None:
    del name
    result = generate_report(pipeline_output, report_type)

    assert result["dashboard_summary"]["badge"] == expected_badge
    assert result["report_type"] == report_type
    json.dumps(result)


def test_missing_sections_debug_report() -> None:
    result = generate_report(
        {
            "example_id": "EX003",
            "question": "Who is the CEO of OpenAI?",
            "original_answer": "Sam Altman is the CEO of OpenAI.",
        },
        "debug",
    )

    assert result["report_id"] == "RPT_EX003"
    assert result["report_type"] == "debug"
    assert result["debug_info"]["missing_sections"] == [
        "temporal_detection",
        "claims",
        "evidence",
        "freshness",
        "verification",
        "outdatedness",
        "correction",
        "risk_label",
    ]
    assert result["dashboard_summary"]["badge"] == "UNKNOWN"


def test_outdated_python_report_schema_content() -> None:
    pipeline = _outdated_python_pipeline()
    result = generate_report(pipeline, "dashboard")

    assert result["report_id"] == "RPT_EX001"
    assert result["example_id"] == "EX001"
    assert result["title"] == "TemporalGuard Report for EX001"
    assert result["final_answer"] == pipeline["correction"]["corrected_answer"]
    assert result["pipeline_summary"] == {
        "temporal_category": "RECENT_ONLY",
        "needs_fresh_evidence": True,
        "total_claims": 1,
        "verification_status": "NEEDS_CORRECTION",
        "outdatedness_status": "OUTDATED",
        "correction_status": "corrected",
        "final_risk_label": "medium_risk",
    }
    assert result["claim_report"][0]["verification_status"] == "OUTDATED"
    assert result["claim_report"][0]["claim_value"] == "Python 3.10"
    assert result["claim_report"][0]["evidence_value"] == "Python 3.13.5"
    assert result["evidence_report"][0]["date_used"] == "2026-06-01"
    assert result["evidence_report"][0]["freshness_label"] == "very_fresh"
    assert result["correction_report"]["changed_claim_ids"] == ["C1"]
    assert result["thesis_summary"]["temporal_failure_type"] == "version_mismatch"
    assert result["debug_info"]["raw_statuses"]["final_risk_label"] == "medium_risk"


def test_safe_static_thesis_summary() -> None:
    result = generate_report(_safe_static_pipeline(), "thesis")

    assert result["thesis_summary"]["temporal_failure_type"] == "no_failure_detected"
    assert "No temporal failure" in result["thesis_summary"]["problem_observed"]
    assert result["final_answer"] == "Binary search divides a sorted search space in half."


def test_unknown_report_type_defaults_to_dashboard_with_warning() -> None:
    result = generate_report(_safe_static_pipeline(), "unknown_type")

    assert result["report_type"] == "dashboard"
    assert result["debug_info"]["warnings"] == ["Unknown report type 'unknown_type' defaulted to dashboard."]


def test_claim_report_handles_missing_verification() -> None:
    result = generate_report(
        {
            "question": "What is Python?",
            "original_answer": "Python is a programming language.",
            "claims": {
                "claims": [
                    {
                        "claim_id": "C1",
                        "claim_text": "Python is a programming language.",
                        "claim_type": "definition",
                    }
                ],
                "total_claims": 1,
            },
        }
    )

    assert result["claim_report"][0]["verification_status"] is None
    assert result["claim_report"][0]["short_explanation"] == "This claim was extracted but not verified."


def test_evidence_report_limit() -> None:
    pipeline = _outdated_python_pipeline()
    pipeline["evidence"]["evidence_results"][0]["evidence_items"] = [
        {
            "evidence_id": f"E{index}",
            "title": f"Evidence {index}",
            "url": f"https://example.com/{index}",
            "publisher": "Example",
            "source_type": "other",
            "evidence_summary": "short",
        }
        for index in range(1, 8)
    ]

    result = generate_report(pipeline, "technical", max_evidence_items=3)

    assert len(result["evidence_report"]) == 3
    assert [item["evidence_id"] for item in result["evidence_report"]] == ["E1", "E2", "E3"]


def test_malformed_input_returns_valid_unknown_report() -> None:
    result = generate_report("not a dict")  # type: ignore[arg-type]

    assert result["report_id"] == "RPT_UNKNOWN"
    assert result["final_answer"] == ""
    assert result["debug_info"]["missing_sections"] == [
        "temporal_detection",
        "claims",
        "evidence",
        "freshness",
        "verification",
        "outdatedness",
        "correction",
        "risk_label",
    ]
