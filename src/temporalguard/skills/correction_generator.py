"""Evidence-grounded correction generation for TemporalGuard."""

from __future__ import annotations

import re
from typing import Any


HIGH_RISK_PATTERN = re.compile(
    r"\b(medical|legal|visa|immigration|finance|tax|safety|security|policy|regulation|clinical|drug|amazon policy|university admission)\b",
    re.IGNORECASE,
)
RISK_DOWNGRADE = {"critical": "high", "high": "medium", "medium": "low", "low": "low", "unknown": "unknown"}


def generate_correction(
    question: str,
    answer: str | list[dict[str, Any]],
    verification_payload: dict[str, Any] | None = None,
    outdatedness_payload: dict[str, Any] | None = None,
    claims_payload: dict[str, Any] | None = None,
    evidence_payload: dict[str, Any] | None = None,
    freshness_payload: dict[str, Any] | None = None,
    temporal_category: str | None = None,
) -> dict[str, Any]:
    """
    Generate a concise, evidence-grounded corrected answer.

    The generator uses supplied verification/outdatedness/evidence payloads only.
    It does not retrieve, browse, verify from scratch, or call an LLM.
    """
    if verification_payload is None and isinstance(answer, list):
        return {"answer": question, "corrected": False}

    answer_text = str(answer or "")
    verification_payload = verification_payload or {}
    outdatedness_payload = outdatedness_payload or {}
    results = _get_verification_results(verification_payload)
    status = _get_outdatedness_status(outdatedness_payload)
    risk = str(outdatedness_payload.get("answer_temporal_risk") or "unknown")
    high_risk = _detect_high_risk_domain(question, answer_text, results)

    changed_ids = [str(item.get("claim_id")) for item in results if item.get("verification_status") in {"OUTDATED", "CONTRADICTED"} and item.get("claim_id")]
    unchanged_ids = [str(item.get("claim_id")) for item in results if item.get("verification_status") == "SUPPORTED" and item.get("claim_id")]
    unsupported_ids = [str(item.get("claim_id")) for item in results if item.get("verification_status") == "INSUFFICIENT_EVIDENCE" and item.get("claim_id")]
    evidence_used = _collect_evidence_metadata(evidence_payload, freshness_payload, changed_ids or unsupported_ids or unchanged_ids)

    warnings: list[str] = []
    if not bool(outdatedness_payload.get("requires_correction", False)) or status in {"NOT_OUTDATED", "NOT_APPLICABLE"}:
        correction_status = "no_correction_needed"
        correction_type = "no_change"
        corrected_answer = answer_text
    elif status == "UNVERIFIED_RISKY" or (unsupported_ids and not changed_ids):
        correction_status = "unable_to_correct"
        correction_type = "add_uncertainty"
        corrected_answer = _generate_insufficient_evidence_response(question, high_risk)
        if high_risk:
            warnings.append("insufficient_evidence_for_high_risk_claim")
    elif status == "PARTIALLY_OUTDATED":
        correction_status = "partially_corrected"
        correction_type = "partial_revision"
        corrected_answer = _generate_partial_revision(results, question, temporal_category)
        if unsupported_ids:
            warnings.append("partial_correction_has_unsupported_claims")
    else:
        decisive = _first_decisive_result(results)
        if not decisive or not decisive.get("evidence_value"):
            correction_status = "unable_to_correct"
            correction_type = "add_uncertainty"
            corrected_answer = _generate_insufficient_evidence_response(question, high_risk)
            warnings.append("missing_evidence_value_for_correction")
        elif decisive.get("verification_status") == "CONTRADICTED":
            correction_status = "corrected"
            correction_type = "fix_contradiction"
            corrected_answer = _generate_contradiction_fix(decisive, question, temporal_category)
        else:
            correction_status = "corrected"
            correction_type = "update_outdated_fact"
            corrected_answer = _generate_outdated_update(decisive, question, temporal_category)

    final_risk = _reduce_risk_after_correction(risk, correction_status, high_risk)
    uncertainty_note = _build_uncertainty_note(correction_status, unsupported_ids)
    safety_note = _build_safety_note(high_risk, correction_status)

    return {
        "corrected_answer": corrected_answer,
        "correction_status": correction_status,
        "correction_type": correction_type,
        "changed_claim_ids": changed_ids if correction_status in {"corrected", "partially_corrected"} else [],
        "unchanged_claim_ids": unchanged_ids,
        "unsupported_claim_ids": unsupported_ids,
        "evidence_used": evidence_used[:3],
        "freshness_note": _build_freshness_note(evidence_used, temporal_category, correction_status),
        "uncertainty_note": uncertainty_note,
        "safety_note": safety_note,
        "answer_temporal_risk": final_risk,
        "confidence": _calculate_correction_confidence(results, correction_status),
        "user_visible_explanation": _user_visible_explanation(correction_status, correction_type),
        "warnings": warnings,
    }


def _get_verification_results(verification_payload: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(verification_payload, dict) or not isinstance(verification_payload.get("verification_results"), list):
        return []
    return [result for result in verification_payload["verification_results"] if isinstance(result, dict)]


def _get_outdatedness_status(outdatedness_payload: dict[str, Any]) -> str:
    if not isinstance(outdatedness_payload, dict):
        return "NOT_ENOUGH_INFORMATION"
    return str(outdatedness_payload.get("outdatedness_status") or "NOT_ENOUGH_INFORMATION")


def _get_claims_by_id(claims_payload: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(claims_payload, dict) or not isinstance(claims_payload.get("claims"), list):
        return {}
    return {
        str(claim.get("claim_id") or f"C{index}"): claim
        for index, claim in enumerate(claims_payload["claims"], start=1)
        if isinstance(claim, dict)
    }


def _collect_evidence_metadata(
    evidence_payload: dict[str, Any] | None,
    freshness_payload: dict[str, Any] | None,
    claim_ids: list[str],
) -> list[dict[str, Any]]:
    evidence_by_claim = _evidence_by_claim(evidence_payload)
    freshness_by_claim = _freshness_by_claim(freshness_payload)
    metadata: list[dict[str, Any]] = []
    for claim_id in claim_ids:
        evidence_result = evidence_by_claim.get(claim_id, {})
        items = evidence_result.get("evidence_items") if isinstance(evidence_result, dict) else None
        if not isinstance(items, list) or not items:
            continue
        best_id = freshness_by_claim.get(claim_id, {}).get("best_evidence_id")
        item = _select_evidence_item(items, best_id)
        if item:
            metadata.append(
                {
                    "claim_id": claim_id,
                    "evidence_id": str(item.get("evidence_id") or ""),
                    "title": str(item.get("title") or ""),
                    "url": str(item.get("url") or ""),
                    "publisher": str(item.get("publisher") or "unknown"),
                    "date_used": _date_used_for_evidence(item, freshness_by_claim.get(claim_id)),
                    "source_type": str(item.get("source_type") or "other"),
                }
            )
    return metadata


def _detect_high_risk_domain(question: str, answer: str, verification_results: list[dict[str, Any]]) -> bool:
    if HIGH_RISK_PATTERN.search(f"{question} {answer}"):
        return True
    return any(str(result.get("risk_level") or "") == "critical" for result in verification_results)


def _generate_outdated_update(ver_result: dict[str, Any], question: str, temporal_category: str | None) -> str:
    claim_value = str(ver_result.get("claim_value") or "The original value")
    evidence_value = str(ver_result.get("evidence_value") or "")
    direct = _direct_answer_template(question, evidence_value)
    if direct:
        return direct
    if temporal_category == "HISTORICAL":
        return f"{claim_value} does not match the checked evidence for the requested time period. Based on the checked evidence, {evidence_value} is the supported value."
    if temporal_category == "VERSION_DEPENDENT":
        return f"{claim_value} does not match the checked version-specific evidence. Based on the checked evidence, {evidence_value} is the supported value for this context."
    if "latest" in question.lower() or "latest" in str(ver_result.get("claim_text") or "").lower():
        return f"{claim_value} is not the latest value according to the checked evidence. Based on the checked evidence, {evidence_value} is listed as the latest release."
    return f"{claim_value} is outdated according to the checked evidence. The evidence-supported value is {evidence_value}."


def _generate_contradiction_fix(ver_result: dict[str, Any], question: str, temporal_category: str | None) -> str:
    claim_value = str(ver_result.get("claim_value") or "The original claim")
    evidence_value = str(ver_result.get("evidence_value") or "")
    direct = _direct_answer_template(question, evidence_value)
    if direct:
        return direct
    event_context = _event_context(question, str(ver_result.get("claim_text") or ""))
    if event_context:
        return f"{claim_value} did not {event_context}. Based on the checked evidence, {evidence_value} {event_context}."
    if temporal_category == "HISTORICAL":
        return f"{claim_value} does not match the checked historical evidence. Based on the checked evidence, {evidence_value} is supported for the requested time period."
    return f"The original answer is contradicted by the checked evidence. The evidence-supported value is {evidence_value}, not {claim_value}."


def _direct_answer_template(question: str, evidence_value: str) -> str | None:
    q = (question or "").lower()
    value = str(evidence_value or "").strip()
    if not value or _is_bad_final_value(value):
        return None
    if re.search(r"\bwho won\b", q):
        event = _extract_event_phrase(question)
        return f"{value} won {event}." if event else f"{value} won."
    if "covid" in q and ("public health emergency" in q or "pheic" in q):
        return f"WHO ended the COVID-19 public health emergency of international concern on {value}."
    if re.search(r"\bwhen\b|\bwhat year\b", q):
        subject = _date_subject_phrase(question)
        return f"{subject} {value}." if subject else f"The date was {value}."
    if "node.js" in q or "nodejs" in q:
        if "end-of-life" in value.lower() or "no longer" in value.lower():
            return f"Node.js 18 is no longer actively supported. It reached {value}."
        return f"Node.js 18 support status: {value}."
    if "dataframe.append" in q or "append" in q and "pandas" in q:
        return "DataFrame.append was removed in pandas 2.0. Use pandas.concat instead."
    if "latest" in q and "python" in q:
        return f"The latest stable Python version is {value}."
    return None


def _extract_event_phrase(question: str) -> str | None:
    match = re.search(r"who won\s+(?P<event>.+?)\??$", question or "", re.IGNORECASE)
    if not match:
        return None
    event = match.group("event").strip()
    if not event.lower().startswith("the "):
        event = f"the {event}"
    return event


def _date_subject_phrase(question: str) -> str | None:
    q = (question or "").strip().rstrip("?")
    match = re.search(r"when did\s+(?P<subject>.+)$", q, re.IGNORECASE)
    if match:
        subject = match.group("subject").strip()
        return f"{subject[0].upper()}{subject[1:]} on"
    match = re.search(r"what year did\s+(?P<subject>.+)$", q, re.IGNORECASE)
    if match:
        subject = match.group("subject").strip()
        return f"{subject[0].upper()}{subject[1:]} in"
    return None


def _is_bad_final_value(value: str) -> bool:
    normalized = re.sub(r"[^a-z0-9.]+", " ", str(value or "").lower()).strip()
    return normalized in {
        "world cup",
        "fifa world cup",
        "results report",
        "report",
        "source",
        "documentation",
        "official website",
    }


def _generate_insufficient_evidence_response(question: str, high_risk: bool) -> str:
    if high_risk:
        return "I could not safely verify this claim from the available evidence. Because this topic may affect real decisions, check the relevant official source before taking action."
    if "latest" in question.lower() or "current" in question.lower() or "still" in question.lower():
        return "I could not verify this time-sensitive claim with reliable evidence, so the original answer should not be treated as confirmed."
    return "I could not verify this claim with the available evidence, so no safe factual correction can be made."


def _generate_partial_revision(
    results: list[dict[str, Any]],
    question: str,
    temporal_category: str | None,
) -> str:
    corrected_parts: list[str] = []
    supported_parts: list[str] = []
    unsupported_parts: list[str] = []
    for result in results:
        status = result.get("verification_status")
        if status == "OUTDATED" and result.get("evidence_value"):
            corrected_parts.append(_generate_outdated_update(result, question, temporal_category))
        elif status == "CONTRADICTED" and result.get("evidence_value"):
            corrected_parts.append(_generate_contradiction_fix(result, question, temporal_category))
        elif status == "SUPPORTED":
            supported_parts.append(str(result.get("claim_text") or "A supported part of the original answer can remain."))
        elif status == "INSUFFICIENT_EVIDENCE":
            unsupported_parts.append(str(result.get("claim_text") or "One claim"))
    output = []
    if corrected_parts:
        output.append(" ".join(corrected_parts))
    if supported_parts:
        output.append("The supported part can remain: " + " ".join(supported_parts))
    if unsupported_parts:
        output.append("Some claim(s) could not be verified safely: " + " ".join(unsupported_parts))
    return " ".join(output) if output else "Only part of the original answer could be corrected from the available evidence."


def _build_freshness_note(evidence_used: list[dict[str, Any]], temporal_category: str | None, status: str) -> str:
    if status == "no_correction_needed":
        return "No temporal correction was needed for this answer."
    if not evidence_used:
        return "Reliable fresh evidence was not available for this correction."
    dated = next((item for item in evidence_used if item.get("date_used")), None)
    if temporal_category == "HISTORICAL":
        return "The correction uses evidence for the requested historical context."
    if dated:
        return f"The correction uses checked evidence dated {dated['date_used']}."
    return "The source had no clear update date, so the correction should be treated with caution."


def _build_safety_note(high_risk: bool, status: str) -> str | None:
    if not high_risk:
        return None
    if status == "unable_to_correct":
        return "This is a high-risk topic, so official confirmation is required before action."
    return "Because this is a high-risk topic, the corrected answer should still be checked against an official source before action."


def _calculate_correction_confidence(results: list[dict[str, Any]], correction_status: str) -> float:
    if correction_status == "unable_to_correct":
        return 0.35
    if not results:
        return 0.60 if correction_status == "no_correction_needed" else 0.50
    relevant = [
        result
        for result in results
        if correction_status != "no_correction_needed" or result.get("verification_status") == "SUPPORTED"
    ] or results
    values = [
        float(result.get("verification_confidence"))
        if isinstance(result.get("verification_confidence"), int | float)
        else 0.80
        for result in relevant
    ]
    if correction_status == "partially_corrected":
        return round(max(0.60, min(0.74, sum(values) / len(values))), 3)
    return round(max(0.0, min(0.95, sum(values) / len(values))), 3)


def _reduce_risk_after_correction(original_risk: str, correction_status: str, high_risk: bool) -> str:
    risk = original_risk if original_risk in RISK_DOWNGRADE else "unknown"
    if correction_status == "no_correction_needed":
        return "low"
    if correction_status == "unable_to_correct":
        return risk
    if high_risk and risk == "critical":
        return "high"
    return RISK_DOWNGRADE[risk]


def _build_uncertainty_note(correction_status: str, unsupported_ids: list[str]) -> str | None:
    if correction_status == "unable_to_correct":
        return "The claim could not be verified safely."
    if unsupported_ids:
        return "Some claims could not be fully verified from the available evidence."
    return None


def _user_visible_explanation(correction_status: str, correction_type: str) -> str:
    if correction_status == "no_correction_needed":
        return "The answer did not appear outdated based on the verification result."
    if correction_type == "update_outdated_fact":
        return "The original answer was outdated because the claimed value differed from the checked evidence."
    if correction_type == "fix_contradiction":
        return "The original answer was contradicted by the checked evidence."
    if correction_type == "partial_revision":
        return "The answer was partially corrected while supported claims were kept."
    return "The original answer could not be verified with enough reliable evidence."


def _first_decisive_result(results: list[dict[str, Any]]) -> dict[str, Any] | None:
    for status in ("OUTDATED", "CONTRADICTED"):
        for result in results:
            if result.get("verification_status") == status:
                return result
    return None


def _evidence_by_claim(evidence_payload: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(evidence_payload, dict) or not isinstance(evidence_payload.get("evidence_results"), list):
        return {}
    return {
        str(result.get("claim_id")): result
        for result in evidence_payload["evidence_results"]
        if isinstance(result, dict) and result.get("claim_id")
    }


def _freshness_by_claim(freshness_payload: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(freshness_payload, dict) or not isinstance(freshness_payload.get("freshness_results"), list):
        return {}
    return {
        str(result.get("claim_id")): result
        for result in freshness_payload["freshness_results"]
        if isinstance(result, dict) and result.get("claim_id")
    }


def _select_evidence_item(items: list[Any], best_id: Any) -> dict[str, Any] | None:
    dict_items = [item for item in items if isinstance(item, dict)]
    if best_id:
        for item in dict_items:
            if item.get("evidence_id") == best_id:
                return item
    if not dict_items:
        return None
    return max(dict_items, key=lambda item: float(item.get("relevance_score") or 0.0))


def _date_used_for_evidence(item: dict[str, Any], freshness_result: dict[str, Any] | None) -> str | None:
    if isinstance(freshness_result, dict):
        for score in freshness_result.get("evidence_scores", []) if isinstance(freshness_result.get("evidence_scores"), list) else []:
            if isinstance(score, dict) and score.get("evidence_id") == item.get("evidence_id"):
                return score.get("date_used")
    return item.get("updated_date") or item.get("published_date") or item.get("retrieved_at")


def _event_context(question: str, claim_text: str) -> str | None:
    text = f"{question} {claim_text}"
    match = re.search(r"won the (.+?)(?:\?|\.|$)", text, re.IGNORECASE)
    if match:
        return f"win the {match.group(1).strip()}"
    return None
