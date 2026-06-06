"""Answer-level outdatedness detection for TemporalGuard."""

from __future__ import annotations

import re
from typing import Any


STATUS_DEFAULT_CONFIDENCE = {
    "SUPPORTED": 0.85,
    "OUTDATED": 0.90,
    "CONTRADICTED": 0.90,
    "PARTIALLY_SUPPORTED": 0.75,
    "INSUFFICIENT_EVIDENCE": 0.70,
    "NOT_VERIFIABLE": 0.60,
}
IMPORTANT_CLAIM_TYPES = {
    "software_version",
    "current_status",
    "company_leadership",
    "law_or_policy",
    "medical_or_scientific_guideline",
    "price_or_market_data",
    "event_result",
    "date_or_deadline",
    "api_or_library_behavior",
}
HIGH_RISK_TYPES = {
    "law_or_policy",
    "medical_or_scientific_guideline",
    "price_or_market_data",
}
HIGH_RISK_PATTERN = re.compile(
    r"\b("
    r"medical|medicine|clinical|drug|diagnosis|treatment|law|legal|visa|immigration|tax|"
    r"finance|interest rate|stock|crypto|policy|regulation|safety|security|vulnerability|"
    r"government rule|university admission|amazon fba policy"
    r")\b",
    re.IGNORECASE,
)
FACTUAL_PATTERN = re.compile(
    r"\b(who|what|when|where|which|latest|current|still|active|ceo|version|price|law|visa|policy|won)\b",
    re.IGNORECASE,
)
CREATIVE_PATTERN = re.compile(r"\b(write|poem|story|joke|creative|imagine|song|haiku)\b", re.IGNORECASE)
RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3, "unknown": 4}


def detect_outdated_answer(
    question: str,
    answer: str | list[dict[str, Any]],
    verification_payload: dict[str, Any] | None = None,
    claims_payload: dict[str, Any] | None = None,
    temporal_category: str | None = None,
    freshness_payload: dict[str, Any] | None = None,
) -> dict[str, Any] | bool:
    """
    Detect whether the full LLM answer is outdated, contradicted, risky, or safe.

    The function uses Skill 05 verification results only. It does not retrieve,
    verify, correct, browse, or call an LLM.
    """
    if verification_payload is None and isinstance(answer, list):
        return False

    del freshness_payload
    answer_text = str(answer or "")
    verification_payload = verification_payload or {}
    results = _get_verification_results(verification_payload)
    claims_by_id = _get_claims_by_id(claims_payload)
    warnings: list[str] = []

    if not results:
        status = _status_for_no_results(question, answer_text, temporal_category)
        risk = "unknown" if status == "NOT_ENOUGH_INFORMATION" else "low"
        return _build_output(
            status=status,
            results=[],
            claims_by_id=claims_by_id,
            question=question,
            answer=answer_text,
            temporal_category=temporal_category,
            high_risk=_detect_high_risk_domain(question, answer_text, list(claims_by_id.values())),
            risk=risk,
            warnings=["No verification results supplied."],
        )

    high_risk = _detect_high_risk_domain(question, answer_text, list(claims_by_id.values()))
    status = _infer_answer_status(results, claims_by_id, question, answer_text, temporal_category)
    risk = _infer_answer_risk(status, results, high_risk)

    return _build_output(
        status=status,
        results=results,
        claims_by_id=claims_by_id,
        question=question,
        answer=answer_text,
        temporal_category=temporal_category,
        high_risk=high_risk,
        risk=risk,
        warnings=warnings,
    )


def _build_output(
    status: str,
    results: list[dict[str, Any]],
    claims_by_id: dict[str, dict[str, Any]],
    question: str,
    answer: str,
    temporal_category: str | None,
    high_risk: bool,
    risk: str,
    warnings: list[str],
) -> dict[str, Any]:
    ids = _collect_claim_ids_by_status(results)
    summary = _count_statuses(results)
    decisive = _decisive_results(status, results, claims_by_id, question)
    return {
        "outdatedness_status": status,
        "is_outdated": status in {"OUTDATED", "PARTIALLY_OUTDATED"},
        "requires_correction": _infer_requires_correction(status, risk, question, temporal_category),
        "answer_temporal_risk": risk,
        "outdated_claim_ids": ids["OUTDATED"],
        "contradicted_claim_ids": ids["CONTRADICTED"],
        "unsupported_claim_ids": ids["INSUFFICIENT_EVIDENCE"],
        "supported_claim_ids": ids["SUPPORTED"],
        "critical_claim_ids": _critical_claim_ids(results),
        "main_issue": _build_main_issue(status, decisive, high_risk),
        "decision_reason": _decision_reason(status, decisive, temporal_category),
        "confidence": _calculate_confidence(status, decisive or results),
        "recommended_next_action": _infer_recommended_action(status),
        "answer_level_summary": summary,
        "warnings": warnings,
    }


def _get_verification_results(verification_payload: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(verification_payload, dict):
        return []
    results = verification_payload.get("verification_results")
    if not isinstance(results, list):
        return []
    return [result for result in results if isinstance(result, dict)]


def _get_claims_by_id(claims_payload: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(claims_payload, dict) or not isinstance(claims_payload.get("claims"), list):
        return {}
    claims: dict[str, dict[str, Any]] = {}
    for index, claim in enumerate(claims_payload["claims"], start=1):
        if isinstance(claim, dict):
            claims[str(claim.get("claim_id") or f"C{index}")] = claim
    return claims


def _count_statuses(results: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "total_claims": len(results),
        "supported_count": 0,
        "outdated_count": 0,
        "contradicted_count": 0,
        "partially_supported_count": 0,
        "insufficient_evidence_count": 0,
        "not_verifiable_count": 0,
    }
    for result in results:
        status = str(result.get("verification_status") or "")
        if status == "SUPPORTED":
            counts["supported_count"] += 1
        elif status == "OUTDATED":
            counts["outdated_count"] += 1
        elif status == "CONTRADICTED":
            counts["contradicted_count"] += 1
        elif status == "PARTIALLY_SUPPORTED":
            counts["partially_supported_count"] += 1
        elif status == "INSUFFICIENT_EVIDENCE":
            counts["insufficient_evidence_count"] += 1
        elif status == "NOT_VERIFIABLE":
            counts["not_verifiable_count"] += 1
    return counts


def _detect_high_risk_domain(question: str, answer: str, claims: list[dict[str, Any]]) -> bool:
    if HIGH_RISK_PATTERN.search(f"{question} {answer}"):
        return True
    return any(str(claim.get("claim_type") or "") in HIGH_RISK_TYPES for claim in claims)


def _is_central_claim(claim_id: str, claim: dict[str, Any] | None, question: str) -> bool:
    if not claim:
        return True
    claim_type = str(claim.get("claim_type") or "")
    sensitivity = str(claim.get("temporal_sensitivity") or "")
    evidence_need = str(claim.get("evidence_need") or "")
    if claim_type in IMPORTANT_CLAIM_TYPES:
        return True
    if sensitivity == "high" or evidence_need in {"fresh", "version_specific", "historical"}:
        return True
    question_terms = _terms(question)
    claim_text = str(claim.get("claim_text") or claim_id)
    if not question_terms:
        return False
    claim_terms = set(_terms(claim_text))
    return bool(claim_terms) and (len(question_terms & claim_terms) / len(question_terms)) >= 0.35


def _collect_claim_ids_by_status(results: list[dict[str, Any]]) -> dict[str, list[str]]:
    ids = {
        "SUPPORTED": [],
        "OUTDATED": [],
        "CONTRADICTED": [],
        "PARTIALLY_SUPPORTED": [],
        "INSUFFICIENT_EVIDENCE": [],
        "NOT_VERIFIABLE": [],
    }
    for result in results:
        status = str(result.get("verification_status") or "")
        claim_id = str(result.get("claim_id") or "")
        if status in ids and claim_id:
            ids[status].append(claim_id)
    return ids


def _infer_answer_status(
    results: list[dict[str, Any]],
    claims_by_id: dict[str, dict[str, Any]],
    question: str,
    answer: str,
    temporal_category: str | None,
) -> str:
    del answer
    central_results = [
        result
        for result in results
        if _is_central_claim(str(result.get("claim_id") or ""), claims_by_id.get(str(result.get("claim_id") or "")), question)
    ] or results
    statuses = [str(result.get("verification_status") or "") for result in results]
    central_statuses = [str(result.get("verification_status") or "") for result in central_results]
    high_risk = _detect_high_risk_domain(question, "", list(claims_by_id.values()))

    if "CONTRADICTED" in central_statuses:
        return "CONTRADICTED"
    if "CONTRADICTED" in statuses:
        return "PARTIALLY_OUTDATED"
    if "OUTDATED" in central_statuses:
        return "OUTDATED" if len(results) == 1 or all(status in {"OUTDATED", "NOT_VERIFIABLE"} for status in statuses) else "PARTIALLY_OUTDATED"
    if "OUTDATED" in statuses or "PARTIALLY_SUPPORTED" in statuses:
        return "PARTIALLY_OUTDATED"
    if temporal_category == "STATIC" and all(
        status in {"SUPPORTED", "INSUFFICIENT_EVIDENCE", "NOT_VERIFIABLE"} for status in statuses
    ):
        if all(
            str(claims_by_id.get(str(result.get("claim_id") or ""), {}).get("evidence_need") or "") == "optional"
            or str(result.get("verification_status") or "") == "SUPPORTED"
            for result in results
        ):
            return "NOT_OUTDATED"
    if any(status == "INSUFFICIENT_EVIDENCE" for status in central_statuses):
        central_missing_evidence = [
            result
            for result in central_results
            if str(result.get("verification_status") or "") == "INSUFFICIENT_EVIDENCE"
            and not result.get("evidence_used")
        ]
        if high_risk and central_missing_evidence:
            return "UNVERIFIED_RISKY"
        return "NOT_ENOUGH_INFORMATION"
    if all(status == "SUPPORTED" for status in statuses):
        return "NOT_OUTDATED"
    if all(status == "NOT_VERIFIABLE" for status in statuses):
        return "NOT_APPLICABLE"
    if "INSUFFICIENT_EVIDENCE" in statuses:
        missing_evidence = any(
            str(result.get("verification_status") or "") == "INSUFFICIENT_EVIDENCE" and not result.get("evidence_used")
            for result in results
        )
        return "UNVERIFIED_RISKY" if high_risk and missing_evidence else "NOT_ENOUGH_INFORMATION"
    return "NOT_ENOUGH_INFORMATION"


def _infer_answer_risk(status: str, results: list[dict[str, Any]], high_risk: bool) -> str:
    if high_risk and status in {"CONTRADICTED", "OUTDATED", "PARTIALLY_OUTDATED", "UNVERIFIED_RISKY"}:
        return "critical"
    if status == "NOT_OUTDATED" or status == "NOT_APPLICABLE":
        return "low"
    if status == "NOT_ENOUGH_INFORMATION":
        return "unknown"
    if status in {"OUTDATED", "CONTRADICTED", "UNVERIFIED_RISKY"}:
        return _worst_risk([str(result.get("risk_level") or "high") for result in results], default="high")
    if status == "PARTIALLY_OUTDATED":
        return _worst_risk([str(result.get("risk_level") or "medium") for result in results], default="medium")
    return "unknown"


def _infer_requires_correction(status: str, risk: str, question: str, temporal_category: str | None) -> bool:
    if status in {"OUTDATED", "PARTIALLY_OUTDATED", "CONTRADICTED"}:
        return True
    if status == "UNVERIFIED_RISKY":
        return risk in {"high", "critical"}
    if status == "NOT_ENOUGH_INFORMATION":
        return temporal_category in {"RECENT_ONLY", "TIME_SENSITIVE", "VERSION_DEPENDENT"} or _is_factual_question(question)
    return False


def _infer_recommended_action(status: str) -> str:
    if status in {"OUTDATED", "PARTIALLY_OUTDATED", "CONTRADICTED"}:
        return "generate_correction"
    if status in {"UNVERIFIED_RISKY", "NOT_ENOUGH_INFORMATION"}:
        return "request_more_evidence"
    return "no_action"


def _calculate_confidence(status: str, results: list[dict[str, Any]]) -> float:
    decisive_statuses = _decisive_statuses_for(status)
    decisive = [
        result
        for result in results
        if not decisive_statuses or str(result.get("verification_status") or "") in decisive_statuses
    ]
    selected = decisive or results
    if not selected:
        return 0.60 if status == "NOT_APPLICABLE" else 0.50
    values = [
        float(result.get("verification_confidence"))
        if isinstance(result.get("verification_confidence"), int | float)
        else STATUS_DEFAULT_CONFIDENCE.get(str(result.get("verification_status") or ""), 0.60)
        for result in selected
    ]
    return round(max(0.0, min(1.0, sum(values) / len(values))), 3)


def _build_main_issue(status: str, decisive_results: list[dict[str, Any]], high_risk: bool) -> str:
    if status == "OUTDATED":
        return "The answer contains a central outdated claim."
    if status == "PARTIALLY_OUTDATED":
        return "Some important claims are outdated or only partially supported."
    if status == "CONTRADICTED":
        return "The main claim is contradicted by evidence."
    if status == "UNVERIFIED_RISKY":
        return "A high-risk or current claim could not be verified with reliable evidence." if high_risk else "An important current claim could not be verified."
    if status == "NOT_ENOUGH_INFORMATION":
        return "There is not enough verified factual information to judge the answer."
    if status == "NOT_APPLICABLE":
        return "Outdatedness is not applicable to this answer."
    if decisive_results:
        return "All important factual claims are supported."
    return "No outdatedness issue detected."


def _decision_reason(status: str, decisive_results: list[dict[str, Any]], temporal_category: str | None) -> str:
    if status == "OUTDATED":
        return "The main high-sensitivity claim is marked OUTDATED, so the answer requires correction."
    if status == "PARTIALLY_OUTDATED":
        return "At least one claim needs correction while other claims are supported or less central."
    if status == "CONTRADICTED":
        return "A central claim is marked CONTRADICTED by verification evidence."
    if status == "UNVERIFIED_RISKY":
        return "Important evidence is insufficient for a high-risk or time-sensitive answer."
    if status == "NOT_ENOUGH_INFORMATION":
        return "No reliable verification result is available for a factual answer."
    if status == "NOT_APPLICABLE":
        return "No checkable factual claims require outdatedness detection."
    if temporal_category == "STATIC":
        return "Stable factual claims are supported, so no temporal correction is needed."
    return "All important claims are supported by verification results."


def _status_for_no_results(question: str, answer: str, temporal_category: str | None) -> str:
    if _is_creative_or_subjective(question, answer):
        return "NOT_APPLICABLE"
    if temporal_category in {"RECENT_ONLY", "TIME_SENSITIVE", "VERSION_DEPENDENT", "HISTORICAL"} or _is_factual_question(question):
        return "NOT_ENOUGH_INFORMATION"
    return "NOT_APPLICABLE"


def _decisive_results(
    status: str,
    results: list[dict[str, Any]],
    claims_by_id: dict[str, dict[str, Any]],
    question: str,
) -> list[dict[str, Any]]:
    statuses = _decisive_statuses_for(status)
    selected = [result for result in results if str(result.get("verification_status") or "") in statuses]
    central = [
        result
        for result in selected
        if _is_central_claim(str(result.get("claim_id") or ""), claims_by_id.get(str(result.get("claim_id") or "")), question)
    ]
    return central or selected


def _decisive_statuses_for(status: str) -> set[str]:
    if status == "OUTDATED":
        return {"OUTDATED"}
    if status == "PARTIALLY_OUTDATED":
        return {"OUTDATED", "PARTIALLY_SUPPORTED", "CONTRADICTED"}
    if status == "CONTRADICTED":
        return {"CONTRADICTED"}
    if status == "UNVERIFIED_RISKY":
        return {"INSUFFICIENT_EVIDENCE"}
    if status == "NOT_OUTDATED":
        return {"SUPPORTED"}
    if status == "NOT_APPLICABLE":
        return {"NOT_VERIFIABLE"}
    return {"INSUFFICIENT_EVIDENCE"}


def _critical_claim_ids(results: list[dict[str, Any]]) -> list[str]:
    return [
        str(result.get("claim_id"))
        for result in results
        if result.get("claim_id") and str(result.get("risk_level") or "") == "critical"
    ]


def _is_creative_or_subjective(question: str, answer: str) -> bool:
    text = f"{question} {answer}"
    if CREATIVE_PATTERN.search(text):
        return True
    return bool(re.search(r"\b(greeting|hello|thanks|opinion|feel|prefer)\b", text, re.IGNORECASE))


def _is_factual_question(question: str) -> bool:
    return bool(FACTUAL_PATTERN.search(question))


def _terms(text: str) -> set[str]:
    stop = {"the", "is", "are", "was", "were", "and", "or", "what", "who", "why", "how", "for", "with"}
    return {word.lower() for word in re.findall(r"[A-Za-z0-9]+", text) if len(word) > 2 and word.lower() not in stop}


def _worst_risk(risks: list[str], default: str) -> str:
    if not risks:
        return default
    valid = [risk if risk in RISK_ORDER else default for risk in risks]
    worst = max(valid, key=lambda risk: RISK_ORDER[risk])
    return default if worst == "unknown" and default != "unknown" else worst
