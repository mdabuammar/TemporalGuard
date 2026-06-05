from temporalguard.frontend.streamlit_helpers import (
    build_dashboard_state,
    build_demo_output,
    build_metric_cards,
    claims_to_table_rows,
    evidence_to_table_rows,
    format_badge,
    get_dashboard_summary,
    get_final_answer,
    get_pipeline_summary,
    risk_to_css_class,
    safe_get,
)


def test_safe_get_nested_and_default() -> None:
    data = {"a": {"b": {"c": 3}}}

    assert safe_get(data, ["a", "b", "c"]) == 3
    assert safe_get(data, ["a", "x"], "missing") == "missing"
    assert safe_get(None, ["a"], "fallback") == "fallback"


def test_risk_to_css_class_and_format_badge() -> None:
    assert risk_to_css_class("safe") == "badge-safe"
    assert risk_to_css_class("low_risk") == "badge-low"
    assert risk_to_css_class("medium_risk") == "badge-medium"
    assert risk_to_css_class("high_risk") == "badge-high"
    assert risk_to_css_class("critical_risk") == "badge-critical"
    assert risk_to_css_class(None) == "badge-unknown"
    assert format_badge("medium_risk") == "MEDIUM RISK"
    assert format_badge(None) == "UNKNOWN"


def test_get_final_answer_prefers_correction() -> None:
    output = {
        "original_answer": "Original",
        "correction": {"corrected_answer": "Corrected"},
        "report": {"final_answer": "Report answer"},
    }

    assert get_final_answer(output) == "Corrected"
    assert get_final_answer({"original_answer": "Original"}) == "Original"


def test_get_dashboard_and_pipeline_summary_defaults() -> None:
    output = {
        "temporal_detection": {"temporal_category": "RECENT_ONLY", "needs_fresh_evidence": True},
        "claims": {"total_claims": 2},
        "verification": {"overall_verification_status": "NEEDS_CORRECTION"},
        "outdatedness": {"outdatedness_status": "OUTDATED"},
        "correction": {"correction_status": "corrected"},
        "risk_label": {
            "dashboard_badge": "OUTDATED - CORRECTED",
            "final_risk_label": "medium_risk",
            "uncertainty_label": "low",
            "trust_score": 0.93,
            "temporal_safety_status": "show_with_caution",
        },
        "freshness": {"overall_freshness_score": 0.98},
    }

    dashboard = get_dashboard_summary(output)
    pipeline = get_pipeline_summary(output)

    assert dashboard["badge"] == "OUTDATED - CORRECTED"
    assert dashboard["trust_score"] == 0.93
    assert pipeline["temporal_category"] == "RECENT_ONLY"
    assert pipeline["total_claims"] == 2
    assert pipeline["freshness_score"] == 0.98


def test_build_metric_cards() -> None:
    output = build_demo_output("What is the latest Python version?")
    cards = build_metric_cards(output)

    assert len(cards) == 6
    assert cards[0]["label"] == "Temporal Category"
    assert any(card["label"] == "Trust Score" for card in cards)


def test_claims_to_table_rows_from_pipeline() -> None:
    output = {
        "claims": {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python 3.10 is latest.",
                    "claim_type": "software_version",
                }
            ]
        },
        "verification": {
            "verification_results": [
                {
                    "claim_id": "C1",
                    "verification_status": "OUTDATED",
                    "risk_level": "high",
                    "claim_value": "Python 3.10",
                    "evidence_value": "Python 3.13.5",
                    "requires_correction": True,
                }
            ]
        },
    }

    rows = claims_to_table_rows(output)

    assert rows == [
        {
            "Claim ID": "C1",
            "Claim Text": "Python 3.10 is latest.",
            "Claim Type": "software_version",
            "Verification Status": "OUTDATED",
            "Risk Level": "high",
            "Claim Value": "Python 3.10",
            "Evidence Value": "Python 3.13.5",
            "Requires Correction": True,
        }
    ]


def test_evidence_to_table_rows_from_pipeline() -> None:
    output = {
        "evidence": {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "title": "Download Python",
                            "publisher": "Python Software Foundation",
                            "source_type": "official",
                            "url": "https://www.python.org/downloads/",
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
                            "freshness_label": "very_fresh",
                            "combined_score": 0.98,
                        }
                    ],
                }
            ]
        },
    }

    rows = evidence_to_table_rows(output)

    assert rows[0]["Evidence ID"] == "E1"
    assert rows[0]["Claim ID"] == "C1"
    assert rows[0]["Freshness Label"] == "very_fresh"
    assert rows[0]["Combined Score"] == 0.98


def test_build_demo_output_latest_python() -> None:
    output = build_demo_output("What is the latest Python version?")

    assert output["risk_label"]["dashboard_badge"] == "OUTDATED - CORRECTED"
    assert "Python 3.13.5" in output["correction"]["corrected_answer"]
    assert output["claims"]["total_claims"] == 1


def test_build_demo_output_static_and_high_risk() -> None:
    static_output = build_demo_output("What is binary search?")
    visa_output = build_demo_output("Is this visa rule still active?")

    assert static_output["risk_label"]["dashboard_badge"] == "SAFE"
    assert visa_output["risk_label"]["final_risk_label"] == "critical_risk"
    assert visa_output["correction"]["unsupported_claim_ids"] == ["C1"]


def test_build_dashboard_state_returns_mapping() -> None:
    assert build_dashboard_state({"mode": "demo"}) == {"mode": "demo"}
