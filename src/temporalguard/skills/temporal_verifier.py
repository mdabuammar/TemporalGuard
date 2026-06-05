"""Deterministic temporal claim verification for TemporalGuard."""

from __future__ import annotations

import re
from typing import Any


VERIFICATION_STATUSES = {
    "SUPPORTED",
    "OUTDATED",
    "CONTRADICTED",
    "PARTIALLY_SUPPORTED",
    "INSUFFICIENT_EVIDENCE",
    "NOT_VERIFIABLE",
}
CORRECTION_STATUSES = {"OUTDATED", "CONTRADICTED", "PARTIALLY_SUPPORTED"}
STRICT_TEMPORAL_CATEGORIES = {"RECENT_ONLY", "TIME_SENSITIVE", "VERSION_DEPENDENT"}
HIGH_RISK_PATTERN = re.compile(
    r"\b(visa|immigration|law|legal|policy|regulation|medical|medicine|finance|price|tax|safety|security)\b",
    re.IGNORECASE,
)
SUBJECTIVE_PATTERN = re.compile(r"\b(best|amazing|wonderful|nice|beautiful|better|favorite)\b", re.IGNORECASE)
STATUS_GROUPS = {
    "active": {"active", "available", "supported", "current", "open"},
    "inactive": {"inactive", "ended", "closed", "expired", "no longer active", "not active", "unavailable"},
    "deprecated": {"deprecated"},
    "not_deprecated": {"not deprecated"},
    "released": {"released"},
    "not_released": {"not released"},
}


def verify_temporal_claims(
    question: str,
    claims_payload: dict[str, Any],
    evidence_payload: dict[str, Any],
    freshness_payload: dict[str, Any] | None = None,
    temporal_category: str | None = None,
) -> dict[str, Any]:
    """
    Verify extracted claims against retrieved and freshness-scored evidence.

    The verifier only uses supplied payloads. It does not retrieve, browse, correct,
    or call an LLM.
    """
    del question
    warnings: list[str] = []
    claims_by_id = _get_claims_by_id(claims_payload)
    evidence_by_id = _get_evidence_by_claim_id(evidence_payload)
    freshness_by_id = _get_freshness_by_claim_id(freshness_payload)

    if not claims_by_id:
        return {
            "verification_results": [],
            "overall_verification_status": "NOT_VERIFIABLE",
            "overall_confidence": 0.0,
            "verification_warnings": ["No claims supplied for verification."],
        }

    results = []
    for claim_id, claim in claims_by_id.items():
        evidence_result = evidence_by_id.get(claim_id, {})
        freshness_result = freshness_by_id.get(claim_id)
        evidence_item = _select_best_evidence(evidence_result, freshness_result)
        evidence_text = _build_evidence_text(evidence_item) if evidence_item else ""
        comparison = _compare_claim_and_evidence_values(claim, evidence_text, temporal_category)
        status = _infer_verification_status(claim, evidence_item, freshness_result, comparison, temporal_category)
        risk_level = _risk_level(status, claim, freshness_result)
        confidence = _verification_confidence(status, freshness_result, comparison, evidence_item)
        best_evidence_id = str(evidence_item.get("evidence_id")) if evidence_item else None

        results.append(
            {
                "claim_id": claim_id,
                "claim_text": str(claim.get("claim_text") or ""),
                "verification_status": status,
                "temporal_validity": _infer_temporal_validity(status, claim, temporal_category),
                "verification_confidence": confidence,
                "evidence_used": [best_evidence_id] if best_evidence_id else [],
                "best_evidence_id": best_evidence_id,
                "reason": _reason(status, claim, comparison, evidence_item),
                "detected_conflict": comparison["detected_conflict"] if status in CORRECTION_STATUSES else None,
                "claim_value": comparison["claim_value"],
                "evidence_value": comparison["evidence_value"],
                "requires_correction": _infer_requires_correction(status, risk_level),
                "risk_level": risk_level,
                "notes": _notes(status, risk_level),
            }
        )

    return {
        "verification_results": results,
        "overall_verification_status": _infer_overall_status(results),
        "overall_confidence": _overall_confidence(results),
        "verification_warnings": warnings,
    }


def verify_temporal_claim(claim: str, evidence: list[dict[str, Any]]) -> dict[str, Any]:
    """Backward-compatible wrapper for the old scaffold API."""
    result = verify_temporal_claims(
        "",
        {"claims": [{"claim_id": "C1", "claim_text": claim, "claim_type": "other"}]},
        {"evidence_results": [{"claim_id": "C1", "evidence_items": evidence, "retrieval_status": "success"}]},
        None,
        None,
    )
    first = result["verification_results"][0]
    return {"verified": first["verification_status"] == "SUPPORTED", "reason": first["reason"]}


def _get_claims_by_id(claims_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if not isinstance(claims_payload, dict) or not isinstance(claims_payload.get("claims"), list):
        return {}
    claims: dict[str, dict[str, Any]] = {}
    for index, claim in enumerate(claims_payload["claims"], start=1):
        if isinstance(claim, dict):
            claim_id = str(claim.get("claim_id") or f"C{index}")
            claims[claim_id] = claim
    return claims


def _get_evidence_by_claim_id(evidence_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if not isinstance(evidence_payload, dict) or not isinstance(evidence_payload.get("evidence_results"), list):
        return {}
    return {
        str(result.get("claim_id")): result
        for result in evidence_payload["evidence_results"]
        if isinstance(result, dict) and result.get("claim_id")
    }


def _get_freshness_by_claim_id(freshness_payload: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(freshness_payload, dict) or not isinstance(freshness_payload.get("freshness_results"), list):
        return {}
    return {
        str(result.get("claim_id")): result
        for result in freshness_payload["freshness_results"]
        if isinstance(result, dict) and result.get("claim_id")
    }


def _select_best_evidence(
    evidence_result: dict[str, Any],
    freshness_result: dict[str, Any] | None,
) -> dict[str, Any] | None:
    items = evidence_result.get("evidence_items") if isinstance(evidence_result, dict) else None
    if not isinstance(items, list) or not items:
        return None
    best_id = freshness_result.get("best_evidence_id") if isinstance(freshness_result, dict) else None
    if best_id:
        for item in items:
            if isinstance(item, dict) and item.get("evidence_id") == best_id:
                return item
    valid_items = [item for item in items if isinstance(item, dict)]
    if not valid_items:
        return None
    return max(valid_items, key=lambda item: float(item.get("relevance_score") or 0.0))


def _build_evidence_text(evidence_item: dict[str, Any]) -> str:
    parts = [
        str(evidence_item.get("title") or ""),
        str(evidence_item.get("publisher") or ""),
        str(evidence_item.get("evidence_summary") or ""),
        str(evidence_item.get("quote") or ""),
    ]
    return " ".join(part for part in parts if part).strip()


def _extract_versions(text: str) -> list[str]:
    return _unique(re.findall(r"\b(?:[A-Z][A-Za-z]+(?:\s+)?|v)?\d+(?:\.\d+){1,3}\b", text))


def _extract_years(text: str) -> list[str]:
    return _unique(re.findall(r"\b(?:19|20)\d{2}\b", text))


def _extract_numbers(text: str) -> list[str]:
    values = re.findall(r"\$\d+(?:\.\d+)?|\b\d+(?:\.\d+)?%|\b\d+\.\d+\b", text)
    return _unique(values)


def _extract_status_words(text: str) -> list[str]:
    lower = text.lower()
    statuses: list[str] = []
    for group, variants in STATUS_GROUPS.items():
        if any(re.search(rf"\b{re.escape(variant)}\b", lower) for variant in variants):
            statuses.append(group)
    return _unique(statuses)


def _extract_candidate_entities(text: str) -> list[str]:
    entities = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\b", text)
    return [entity for entity in _unique(entities) if entity.lower() not in {"the", "president"}]


def _compare_claim_and_evidence_values(
    claim: dict[str, Any],
    evidence_text: str,
    temporal_category: str | None,
) -> dict[str, Any]:
    claim_text = str(claim.get("claim_text") or "")
    claim_versions = _extract_versions(claim_text)
    evidence_versions = _extract_versions(evidence_text)
    claim_years = _extract_years(claim_text)
    evidence_years = _extract_years(evidence_text)
    claim_numbers = _extract_numbers(claim_text)
    evidence_numbers = _extract_numbers(evidence_text)
    claim_statuses = _extract_status_words(claim_text)
    evidence_statuses = _extract_status_words(evidence_text)
    claim_entities = [str(entity) for entity in claim.get("entities", []) if str(entity).strip()]
    if not claim_entities:
        claim_entities = _extract_candidate_entities(claim_text)
    evidence_entities = _extract_candidate_entities(evidence_text)

    comparison = {
        "supports": _overlap_score(claim_text, evidence_text) >= 0.45,
        "partial": _overlap_score(claim_text, evidence_text) >= 0.25,
        "conflict_type": None,
        "claim_value": None,
        "evidence_value": None,
        "detected_conflict": None,
    }

    if claim_versions and evidence_versions:
        claim_value = claim_versions[0]
        evidence_value = evidence_versions[0]
        comparison.update(_value_comparison(claim_value, evidence_value, "version"))
        if claim_value != evidence_value and _is_current_or_latest(claim, temporal_category):
            comparison["conflict_type"] = "outdated"
        return comparison

    if claim_statuses and evidence_statuses:
        claim_value = claim_statuses[0]
        evidence_value = evidence_statuses[0]
        comparison.update(_value_comparison(claim_value, evidence_value, "status"))
        if claim_value != evidence_value:
            comparison["conflict_type"] = "outdated" if _is_current_or_latest(claim, temporal_category) else "contradicted"
        return comparison

    if claim_numbers and evidence_numbers:
        comparison.update(_value_comparison(claim_numbers[0], evidence_numbers[0], "number"))
        return comparison

    winner_claim = _winner_entity(claim_text)
    winner_evidence = _winner_entity(evidence_text)
    if winner_claim and winner_evidence:
        comparison.update(_value_comparison(winner_claim, winner_evidence, "entity"))
        if winner_claim != winner_evidence:
            comparison["conflict_type"] = "contradicted"
        return comparison

    if temporal_category == "HISTORICAL" and claim_years:
        comparison["claim_value"] = _best_entity_value(claim_entities, claim_text)
        comparison["evidence_value"] = comparison["claim_value"] if _historical_year_supported(claim_years[0], evidence_text) else None
        comparison["supports"] = bool(comparison["evidence_value"])
        comparison["partial"] = comparison["supports"] or any(year in evidence_years for year in claim_years)
        return comparison

    if claim_entities:
        value = _best_entity_value(claim_entities, claim_text)
        comparison["claim_value"] = value
        comparison["evidence_value"] = value if value and value.lower() in evidence_text.lower() else None
        if comparison["evidence_value"]:
            comparison["supports"] = True
    return comparison


def _infer_verification_status(
    claim: dict[str, Any],
    evidence_item: dict[str, Any] | None,
    freshness_result: dict[str, Any] | None,
    comparison: dict[str, Any],
    temporal_category: str | None,
) -> str:
    claim_text = str(claim.get("claim_text") or "")
    if _is_not_verifiable(claim_text):
        return "NOT_VERIFIABLE"
    if evidence_item is None:
        return "INSUFFICIENT_EVIDENCE"

    reliability = _freshness_value(freshness_result, "claim_reliability_score", default=0.60)
    freshness = _freshness_value(freshness_result, "claim_freshness_score", default=0.60)
    weak_evidence = reliability < 0.45 or (temporal_category in STRICT_TEMPORAL_CATEGORIES and freshness < 0.40)

    if comparison["conflict_type"] == "outdated":
        return "OUTDATED"
    if comparison["conflict_type"] == "contradicted" or comparison["detected_conflict"]:
        return "CONTRADICTED"
    if weak_evidence:
        return "INSUFFICIENT_EVIDENCE"
    if comparison["supports"]:
        return "SUPPORTED"
    if comparison["partial"]:
        return "PARTIALLY_SUPPORTED"
    return "INSUFFICIENT_EVIDENCE"


def _infer_temporal_validity(status: str, claim: dict[str, Any], temporal_category: str | None) -> str:
    if status == "OUTDATED":
        return "expired"
    if status in {"INSUFFICIENT_EVIDENCE", "NOT_VERIFIABLE"}:
        return "uncertain" if status == "INSUFFICIENT_EVIDENCE" else "not_applicable"
    if temporal_category == "HISTORICAL" or claim.get("evidence_need") == "historical":
        return "historical"
    if temporal_category == "VERSION_DEPENDENT" or claim.get("evidence_need") == "version_specific":
        return "version_specific"
    if temporal_category in {"RECENT_ONLY", "TIME_SENSITIVE"} or _is_current_or_latest(claim, temporal_category):
        return "current"
    return "not_applicable"


def _infer_requires_correction(status: str, risk_level: str) -> bool:
    if status in CORRECTION_STATUSES:
        return True
    return status == "INSUFFICIENT_EVIDENCE" and risk_level in {"high", "critical"}


def _infer_overall_status(results: list[dict[str, Any]]) -> str:
    statuses = [str(result["verification_status"]) for result in results]
    if not statuses:
        return "NOT_VERIFIABLE"
    if all(status == "SUPPORTED" for status in statuses):
        return "SUPPORTED"
    if any(status in CORRECTION_STATUSES for status in statuses):
        return "NEEDS_CORRECTION"
    if all(status == "INSUFFICIENT_EVIDENCE" for status in statuses):
        return "INSUFFICIENT_EVIDENCE"
    if all(status == "NOT_VERIFIABLE" for status in statuses):
        return "NOT_VERIFIABLE"
    return "MIXED"


def _risk_level(status: str, claim: dict[str, Any], freshness_result: dict[str, Any] | None) -> str:
    if isinstance(freshness_result, dict) and freshness_result.get("claim_temporal_risk"):
        base = str(freshness_result["claim_temporal_risk"])
        if status in {"CONTRADICTED", "OUTDATED"} and base == "low":
            return "high"
        return base
    if status == "SUPPORTED":
        return "low"
    if status == "PARTIALLY_SUPPORTED":
        return "medium"
    if status in {"OUTDATED", "CONTRADICTED"}:
        return "critical" if _high_risk_claim(claim) else "high"
    if status == "INSUFFICIENT_EVIDENCE":
        return "critical" if _high_risk_claim(claim) else "high"
    return "unknown"


def _verification_confidence(
    status: str,
    freshness_result: dict[str, Any] | None,
    comparison: dict[str, Any],
    evidence_item: dict[str, Any] | None,
) -> float:
    if status == "NOT_VERIFIABLE":
        return 0.70
    if evidence_item is None:
        return 0.80
    reliability = _freshness_value(freshness_result, "claim_reliability_score", default=0.70)
    if status in {"OUTDATED", "CONTRADICTED"} and comparison["detected_conflict"]:
        return round(min(0.95, max(0.75, reliability)), 3)
    if status == "SUPPORTED":
        return round(min(0.95, max(0.70, reliability)), 3)
    if status == "PARTIALLY_SUPPORTED":
        return round(min(0.80, max(0.60, reliability)), 3)
    return round(min(0.85, max(0.50, reliability)), 3)


def _reason(
    status: str,
    claim: dict[str, Any],
    comparison: dict[str, Any],
    evidence_item: dict[str, Any] | None,
) -> str:
    claim_text = str(claim.get("claim_text") or "The claim")
    if status == "INSUFFICIENT_EVIDENCE":
        return "No reliable evidence was available to verify the claim." if evidence_item is None else "Evidence was too weak or unclear to verify the claim."
    if status == "NOT_VERIFIABLE":
        return "The claim is subjective or too vague for factual verification."
    if status == "OUTDATED":
        return f"The claim value {comparison['claim_value']} appears replaced by evidence value {comparison['evidence_value']}."
    if status == "CONTRADICTED":
        return f"The evidence directly conflicts with the claim value {comparison['claim_value']}."
    if status == "PARTIALLY_SUPPORTED":
        return "The evidence supports part of the claim but not all important details."
    return f"Reliable evidence supports the claim: {claim_text}"


def _notes(status: str, risk_level: str) -> str:
    return f"Verification status is {status} with {risk_level} risk."


def _overall_confidence(results: list[dict[str, Any]]) -> float:
    if not results:
        return 0.0
    return round(sum(float(result["verification_confidence"]) for result in results) / len(results), 3)


def _value_comparison(claim_value: str, evidence_value: str, value_type: str) -> dict[str, Any]:
    if claim_value == evidence_value:
        return {
            "supports": True,
            "partial": True,
            "conflict_type": None,
            "claim_value": claim_value,
            "evidence_value": evidence_value,
            "detected_conflict": None,
        }
    return {
        "supports": False,
        "partial": False,
        "conflict_type": "contradicted",
        "claim_value": claim_value,
        "evidence_value": evidence_value,
        "detected_conflict": f"Claim value: {claim_value}; Evidence value: {evidence_value}.",
    }


def _winner_entity(text: str) -> str | None:
    match = re.search(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+won\b", text)
    return match.group(1) if match else None


def _historical_year_supported(year: str, evidence_text: str) -> bool:
    if year in evidence_text:
        return True
    target = int(year)
    for start, end in re.findall(r"\b((?:19|20)\d{2})\s+to\s+((?:19|20)\d{2})\b", evidence_text):
        if int(start) <= target <= int(end):
            return True
    return False


def _overlap_score(claim_text: str, evidence_text: str) -> float:
    claim_terms = _terms(claim_text)
    if not claim_terms:
        return 0.0
    evidence_terms = set(_terms(evidence_text))
    return sum(1 for term in claim_terms if term in evidence_terms) / len(claim_terms)


def _terms(text: str) -> list[str]:
    stop = {"the", "is", "are", "was", "were", "a", "an", "of", "and", "to", "in", "as", "from"}
    return [word.lower() for word in re.findall(r"[A-Za-z0-9]+", text) if len(word) > 2 and word.lower() not in stop]


def _is_current_or_latest(claim: dict[str, Any], temporal_category: str | None) -> bool:
    text = f"{claim.get('claim_text') or ''} {claim.get('temporal_anchor') or ''} {claim.get('evidence_need') or ''}"
    return temporal_category in STRICT_TEMPORAL_CATEGORIES or re.search(r"\b(latest|current|newest|still|active|fresh)\b", text, re.I) is not None


def _is_not_verifiable(claim_text: str) -> bool:
    return bool(SUBJECTIVE_PATTERN.search(claim_text))


def _high_risk_claim(claim: dict[str, Any]) -> bool:
    return HIGH_RISK_PATTERN.search(str(claim.get("claim_text") or "")) is not None


def _freshness_value(freshness_result: dict[str, Any] | None, key: str, default: float) -> float:
    if isinstance(freshness_result, dict) and isinstance(freshness_result.get(key), int | float):
        return float(freshness_result[key])
    return default


def _best_entity_value(entities: list[str], claim_text: str) -> str | None:
    for entity in entities:
        if entity and entity.lower() in claim_text.lower() and entity.lower() not in {"united states", "president"}:
            return entity
    return entities[0] if entities else None


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        clean = value.strip()
        key = clean.lower()
        if clean and key not in seen:
            seen.add(key)
            unique_values.append(clean)
    return unique_values
