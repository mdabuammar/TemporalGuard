"""Validation helpers for human TemporalGuard benchmark annotations."""

from __future__ import annotations

from typing import Any


REQUIRED_FIELDS = {
    "example_id",
    "question",
    "original_answer",
    "gold_temporal_category",
    "gold_outdatedness_status",
    "gold_requires_correction",
    "gold_final_risk_label",
    "domain",
    "difficulty",
    "high_risk_domain",
    "annotation_status",
}
ALLOWED_TEMPORAL_CATEGORIES = {
    "STATIC",
    "TIME_SENSITIVE",
    "RECENT_ONLY",
    "HISTORICAL",
    "VERSION_DEPENDENT",
    "UNKNOWN",
}
ALLOWED_OUTDATEDNESS_STATUSES = {
    "NOT_OUTDATED",
    "OUTDATED",
    "PARTIALLY_OUTDATED",
    "CONTRADICTED",
    "UNVERIFIED_RISKY",
    "NOT_ENOUGH_INFORMATION",
    "NOT_APPLICABLE",
}
ALLOWED_RISK_LABELS = {
    "safe",
    "low_risk",
    "medium_risk",
    "high_risk",
    "critical_risk",
    "unknown_risk",
}
ALLOWED_DOMAINS = {
    "software",
    "company_leadership",
    "law_policy",
    "medical_science",
    "finance_market",
    "sports_events",
    "academic_research",
    "historical",
    "static_education",
    "other",
}
ALLOWED_DIFFICULTIES = {"easy", "medium", "hard", "adversarial"}
ALLOWED_ANNOTATION_STATUSES = {"draft", "verified", "needs_review", "rejected"}
EVIDENCE_REQUIRED_STATUSES = {"OUTDATED", "PARTIALLY_OUTDATED", "CONTRADICTED"}
CORRECTION_REQUIRED_STATUSES = {"OUTDATED", "PARTIALLY_OUTDATED", "CONTRADICTED", "UNVERIFIED_RISKY"}
HIGH_RISK_DOMAINS = {"law_policy", "medical_science", "finance_market"}
HIGH_RISK_ALLOWED_LABELS = {"high_risk", "critical_risk", "unknown_risk"}
HIGH_RISK_INSUFFICIENT_ALLOWED_LABELS = {"critical_risk", "unknown_risk"}


def validate_annotation(example: dict[str, Any]) -> dict[str, Any]:
    """Validate one benchmark annotation and return JSON-compatible results."""
    normalized = _normalize_example(example)
    errors: list[str] = []
    warnings: list[str] = []

    for field in sorted(REQUIRED_FIELDS):
        if normalized.get(field) in (None, ""):
            errors.append(f"missing required field: {field}")

    _check_allowed(
        normalized,
        errors,
        "gold_temporal_category",
        ALLOWED_TEMPORAL_CATEGORIES,
    )
    _check_allowed(
        normalized,
        errors,
        "gold_outdatedness_status",
        ALLOWED_OUTDATEDNESS_STATUSES,
    )
    _check_allowed(normalized, errors, "gold_final_risk_label", ALLOWED_RISK_LABELS)
    _check_allowed(normalized, errors, "domain", ALLOWED_DOMAINS)
    _check_allowed(normalized, errors, "difficulty", ALLOWED_DIFFICULTIES)
    _check_allowed(normalized, errors, "annotation_status", ALLOWED_ANNOTATION_STATUSES)

    if not isinstance(normalized.get("gold_requires_correction"), bool):
        errors.append("gold_requires_correction must be boolean")
    if not isinstance(normalized.get("high_risk_domain"), bool):
        errors.append("high_risk_domain must be boolean")

    _check_evidence_fields(normalized, errors, warnings)
    _check_correction_consistency(normalized, warnings)
    _check_high_risk_consistency(normalized, errors, warnings)

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "example_id": normalized.get("example_id"),
        "annotation_status": normalized.get("annotation_status"),
    }


def annotation_checklist(example: dict[str, Any]) -> list[str]:
    """Return human-readable checklist items for annotation review."""
    normalized = _normalize_example(example)
    checklist = [
        "Confirm the question context before assigning temporal category.",
        "Confirm the original answer contains the annotated claim.",
        "Verify gold labels use the allowed TemporalGuard label set.",
        "Record authoritative evidence for any outdated or contradicted example.",
        "Set gold_requires_correction consistently with outdatedness status.",
        "Review final risk label, especially for high-risk domains.",
        "Set annotation_status to verified only after evidence and labels are reviewed.",
    ]
    if normalized.get("gold_outdatedness_status") in EVIDENCE_REQUIRED_STATUSES:
        checklist.append("Check gold_evidence_value, gold_source_url, and gold_source_date are filled.")
    if normalized.get("high_risk_domain") is True or normalized.get("domain") in HIGH_RISK_DOMAINS:
        checklist.append("High-risk example: confirm risk label is high_risk or critical_risk.")
    return checklist


def _normalize_example(example: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(example or {})
    for key, value in list(normalized.items()):
        if isinstance(value, str):
            normalized[key] = value.strip()

    if "gold_temporal_category" in normalized:
        normalized["gold_temporal_category"] = str(normalized["gold_temporal_category"]).upper()
    if "gold_outdatedness_status" in normalized:
        normalized["gold_outdatedness_status"] = str(normalized["gold_outdatedness_status"]).upper()
    if "gold_final_risk_label" in normalized:
        normalized["gold_final_risk_label"] = str(normalized["gold_final_risk_label"]).lower()
    if "domain" in normalized:
        normalized["domain"] = str(normalized["domain"]).lower()
    if "difficulty" in normalized:
        normalized["difficulty"] = str(normalized["difficulty"]).lower()
    if "annotation_status" in normalized:
        normalized["annotation_status"] = str(normalized["annotation_status"]).lower()
    if "gold_requires_correction" in normalized:
        normalized["gold_requires_correction"] = _parse_bool(normalized["gold_requires_correction"])
    if "high_risk_domain" in normalized:
        normalized["high_risk_domain"] = _parse_bool(normalized["high_risk_domain"])
    return normalized


def _check_allowed(example: dict[str, Any], errors: list[str], field: str, allowed: set[str]) -> None:
    value = example.get(field)
    if value not in (None, "") and value not in allowed:
        errors.append(f"invalid {field}")


def _check_evidence_fields(example: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    status = example.get("gold_outdatedness_status")
    if status not in EVIDENCE_REQUIRED_STATUSES:
        return
    for field in ("gold_evidence_value", "gold_source_url", "gold_source_date"):
        if example.get(field) in (None, ""):
            errors.append(f"missing {field} for {status} example")
    if example.get("gold_source_url") and not str(example["gold_source_url"]).startswith(("http://", "https://")):
        warnings.append("gold_source_url should be an http or https URL")


def _check_correction_consistency(example: dict[str, Any], warnings: list[str]) -> None:
    status = example.get("gold_outdatedness_status")
    requires = example.get("gold_requires_correction")
    if status in CORRECTION_REQUIRED_STATUSES and requires is False:
        warnings.append(f"{status} examples usually require correction or uncertainty injection")
    if status in {"NOT_OUTDATED", "NOT_APPLICABLE"} and requires is True:
        warnings.append(f"{status} examples usually should not require correction")


def _check_high_risk_consistency(example: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    high_risk = example.get("high_risk_domain") is True or example.get("domain") in HIGH_RISK_DOMAINS
    risk = example.get("gold_final_risk_label")
    status = example.get("gold_outdatedness_status")
    if not high_risk or risk in (None, ""):
        return
    if status in {"UNVERIFIED_RISKY", "NOT_ENOUGH_INFORMATION"} and risk not in HIGH_RISK_INSUFFICIENT_ALLOWED_LABELS:
        errors.append("high-risk insufficient-evidence examples must use critical_risk or unknown_risk")
    elif status in {"OUTDATED", "PARTIALLY_OUTDATED", "CONTRADICTED"} and risk not in HIGH_RISK_ALLOWED_LABELS:
        errors.append("high-risk outdated or contradicted examples need high_risk or critical_risk label")
    elif risk in {"safe", "low_risk"}:
        warnings.append("high-risk examples should not use safe or low_risk without strong justification")


def _parse_bool(value: Any) -> bool | Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"true", "1", "yes", "y"}:
            return True
        if text in {"false", "0", "no", "n"}:
            return False
    return value
