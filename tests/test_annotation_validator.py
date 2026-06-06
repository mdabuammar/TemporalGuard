import json

from temporalguard.data.annotation_validator import annotation_checklist, validate_annotation


def _example(**overrides):
    data = {
        "example_id": "EX001",
        "question": "What is the latest Python version?",
        "original_answer": "Python 3.10 is the latest stable version.",
        "gold_temporal_category": "RECENT_ONLY",
        "gold_outdatedness_status": "OUTDATED",
        "gold_requires_correction": True,
        "gold_evidence_value": "Python 3.13.5",
        "gold_source_url": "https://www.python.org/downloads/",
        "gold_source_date": "2026-06-06",
        "gold_final_risk_label": "medium_risk",
        "domain": "software",
        "difficulty": "easy",
        "high_risk_domain": False,
        "source_notes": "Official Python download page checked manually.",
        "annotation_status": "verified",
    }
    data.update(overrides)
    return data


def test_validate_annotation_accepts_valid_example() -> None:
    result = validate_annotation(_example())

    assert result == {
        "valid": True,
        "errors": [],
        "warnings": [],
        "example_id": "EX001",
        "annotation_status": "verified",
    }
    json.dumps(result)


def test_validate_annotation_reports_missing_required_fields() -> None:
    result = validate_annotation({})

    assert result["valid"] is False
    assert "missing required field: example_id" in result["errors"]
    assert "missing required field: question" in result["errors"]
    assert "gold_requires_correction must be boolean" in result["errors"]
    assert "high_risk_domain must be boolean" in result["errors"]


def test_validate_annotation_checks_allowed_labels() -> None:
    result = validate_annotation(
        _example(
            gold_temporal_category="CURRENT",
            gold_outdatedness_status="STALE",
            gold_final_risk_label="danger",
            domain="software_docs",
            difficulty="simple",
            annotation_status="done",
        )
    )

    assert "invalid gold_temporal_category" in result["errors"]
    assert "invalid gold_outdatedness_status" in result["errors"]
    assert "invalid gold_final_risk_label" in result["errors"]
    assert "invalid domain" in result["errors"]
    assert "invalid difficulty" in result["errors"]
    assert "invalid annotation_status" in result["errors"]


def test_validate_annotation_requires_gold_evidence_for_outdated_examples() -> None:
    result = validate_annotation(
        _example(
            gold_outdatedness_status="CONTRADICTED",
            gold_evidence_value="",
            gold_source_url="",
            gold_source_date="",
        )
    )

    assert "missing gold_evidence_value for CONTRADICTED example" in result["errors"]
    assert "missing gold_source_url for CONTRADICTED example" in result["errors"]
    assert "missing gold_source_date for CONTRADICTED example" in result["errors"]


def test_validate_annotation_warns_for_non_http_source_url() -> None:
    result = validate_annotation(_example(gold_source_url="python.org/downloads"))

    assert result["valid"] is True
    assert "gold_source_url should be an http or https URL" in result["warnings"]


def test_validate_annotation_detects_high_risk_with_too_low_risk_label() -> None:
    result = validate_annotation(
        _example(
            question="Is this visa rule still active?",
            gold_outdatedness_status="UNVERIFIED_RISKY",
            gold_evidence_value="insufficient official evidence",
            gold_source_url="https://example.gov/visa",
            gold_source_date="2026-06-06",
            gold_final_risk_label="medium_risk",
            domain="law_policy",
            high_risk_domain=True,
        )
    )

    assert result["valid"] is False
    assert "high-risk insufficient-evidence examples must use critical_risk or unknown_risk" in result["errors"]


def test_validate_annotation_detects_high_risk_outdated_with_low_risk_label() -> None:
    result = validate_annotation(
        _example(
            gold_outdatedness_status="OUTDATED",
            gold_final_risk_label="low_risk",
            domain="medical_science",
            high_risk_domain=True,
        )
    )

    assert "high-risk outdated or contradicted examples need high_risk or critical_risk label" in result["errors"]


def test_validate_annotation_warns_for_correction_inconsistency() -> None:
    no_correction_needed = validate_annotation(_example(gold_requires_correction=False))
    unnecessary_correction = validate_annotation(
        _example(
            gold_outdatedness_status="NOT_OUTDATED",
            gold_requires_correction=True,
            gold_evidence_value="Python explanation is supported.",
            gold_final_risk_label="safe",
        )
    )

    assert "OUTDATED examples usually require correction or uncertainty injection" in no_correction_needed["warnings"]
    assert "NOT_OUTDATED examples usually should not require correction" in unnecessary_correction["warnings"]


def test_validate_annotation_normalizes_case_and_boolean_strings() -> None:
    result = validate_annotation(
        _example(
            gold_temporal_category="recent_only",
            gold_outdatedness_status="outdated",
            gold_requires_correction="true",
            gold_final_risk_label="MEDIUM_RISK",
            domain="SOFTWARE",
            difficulty="EASY",
            high_risk_domain="false",
            annotation_status="VERIFIED",
        )
    )

    assert result["valid"] is True
    assert result["annotation_status"] == "verified"


def test_annotation_checklist_includes_evidence_and_high_risk_items() -> None:
    checklist = annotation_checklist(
        _example(
            gold_outdatedness_status="OUTDATED",
            high_risk_domain=True,
            domain="law_policy",
        )
    )

    assert any("gold_evidence_value" in item for item in checklist)
    assert any("High-risk example" in item for item in checklist)
