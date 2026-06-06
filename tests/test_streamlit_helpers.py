from temporalguard.frontend.streamlit_helpers import (
    LLM_PROVIDER_OPTIONS,
    SAMPLE_QUESTIONS,
    badge_to_css_class,
    build_analyze_payload,
    build_dashboard_state,
    build_demo_output,
    build_metric_cards,
    claims_to_table_rows,
    evidence_to_table_rows,
    format_badge,
    get_dashboard_summary,
    get_final_answer,
    get_pipeline_summary,
    normalize_llm_provider,
    risk_to_css_class,
    safe_get,
)


def test_safe_get_nested_and_default() -> None:
    data = {"a": {"b": {"c": 3}}}

    assert safe_get(data, ["a", "b", "c"]) == 3
    assert safe_get(data, ["a", "x"], "missing") == "missing"
    assert safe_get(None, ["a"], "fallback") == "fallback"
    assert safe_get({"a": None}, ["a", "b"], "fallback") == "fallback"


def test_risk_to_css_class() -> None:
    assert risk_to_css_class("safe") == "tg-badge-safe"
    assert risk_to_css_class("low_risk") == "tg-badge-low"
    assert risk_to_css_class("medium_risk") == "tg-badge-medium"
    assert risk_to_css_class("high_risk") == "tg-badge-high"
    assert risk_to_css_class("critical_risk") == "tg-badge-critical"
    assert risk_to_css_class(None) == "tg-badge-unknown"


def test_badge_to_css_class_and_format_badge() -> None:
    assert badge_to_css_class("SAFE - STATIC KNOWLEDGE") == "tg-badge-safe"
    assert badge_to_css_class("OUTDATED - CORRECTED") == "tg-badge-medium"
    assert badge_to_css_class("HIGH - VERIFY") == "tg-badge-high"
    assert badge_to_css_class("CRITICAL - VERIFY OFFICIAL SOURCE") == "tg-badge-critical"
    assert badge_to_css_class(None) == "tg-badge-unknown"
    assert format_badge("medium_risk") == "MEDIUM RISK"
    assert format_badge(None) == "UNKNOWN"


def test_get_final_answer_prefers_correction() -> None:
    output = {
        "original_answer": "Original",
        "correction": {"corrected_answer": "Corrected"},
        "report": {"final_answer": "Report answer"},
    }

    assert get_final_answer(output) == "Corrected"
    assert get_final_answer({"report": {"final_answer": "Report answer"}}) == "Report answer"
    assert get_final_answer({"original_answer": "Original"}) == "Original"
    assert get_final_answer({}) == ""


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
    assert dashboard["badge_class"] == "tg-badge-medium"
    assert dashboard["risk_class"] == "tg-badge-medium"
    assert dashboard["trust_score"] == 0.93
    assert pipeline["temporal_category"] == "RECENT_ONLY"
    assert pipeline["total_claims"] == 2
    assert pipeline["freshness_score"] == 0.98


def test_missing_fields_do_not_crash() -> None:
    assert get_dashboard_summary({})["badge"] == "UNKNOWN"
    assert get_pipeline_summary({})["temporal_category"] == "UNKNOWN"
    assert len(build_metric_cards({})) == 6
    assert claims_to_table_rows({}) == []
    assert evidence_to_table_rows({}) == []
    assert normalize_llm_provider(None) == "mock"
    assert build_analyze_payload("Q") == {
        "question": "Q",
        "base_answer": None,
        "llm_provider": "mock",
        "model_name": None,
        "report_type": "dashboard",
    }


def test_llm_provider_payload_helpers() -> None:
    assert LLM_PROVIDER_OPTIONS["Claude/Anthropic"] == "anthropic"
    assert normalize_llm_provider("OpenAI") == "openai"
    assert normalize_llm_provider("Gemini") == "gemini"

    payload = build_analyze_payload(
        question="What is current?",
        base_answer="Existing answer",
        report_type="technical",
        llm_provider="Claude/Anthropic",
        model_name=" claude-test ",
    )

    assert payload["base_answer"] == "Existing answer"
    assert payload["llm_provider"] == "anthropic"
    assert payload["model_name"] == "claude-test"
    assert payload["report_type"] == "technical"


def test_build_metric_cards() -> None:
    output = build_demo_output("What is the latest Python version?")
    cards = build_metric_cards(output)

    assert len(cards) == 6
    assert [card["label"] for card in cards] == [
        "Temporal Category",
        "Outdatedness",
        "Verification",
        "Correction",
        "Trust Score",
        "Freshness Score",
    ]
    assert any(card["value"] == "0.93" for card in cards)


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
            "Verification": "OUTDATED",
            "Risk": "high",
            "Claim Value": "Python 3.10",
            "Evidence Value": "Python 3.13.5",
            "Correction": True,
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
    assert rows[0]["Freshness"] == "very_fresh"
    assert rows[0]["Score"] == 0.98


def test_build_demo_output_for_all_sample_questions() -> None:
    for question in SAMPLE_QUESTIONS:
        output = build_demo_output(question)

        assert output["question"] == question
        assert output["pipeline_status"] == "success"
        assert output["temporal_detection"]["temporal_category"]
        assert output["claims"]["total_claims"] >= 1
        assert claims_to_table_rows(output)
        assert evidence_to_table_rows(output)
        assert get_final_answer(output)
        assert get_dashboard_summary(output)["badge"] != "UNKNOWN"
        assert "problem_observed" in output["report"]["thesis_summary"]


def test_build_demo_output_respects_base_answer() -> None:
    output = build_demo_output("Who is the CEO of OpenAI?", "An older base answer.")

    assert output["original_answer"] == "An older base answer."
    assert claims_to_table_rows(output)[0]["Claim Text"] == "An older base answer."


def test_build_dashboard_state_returns_mapping() -> None:
    assert build_dashboard_state({"mode": "demo"}) == {"mode": "demo"}
