"""Final uncertainty and risk labeling for TemporalGuard outputs."""

from __future__ import annotations

import re
from typing import Any


HIGH_RISK_PATTERN = re.compile(
    r"\b("
    r"medical|medicine|clinical|drug|diagnosis|treatment|law|legal|visa|immigration|tax|"
    r"finance|interest rate|stock|crypto|policy|regulation|safety|security|vulnerability|"
    r"government rule|university admission|amazon fba policy|insurance|employment law"
    r")\b",
    re.IGNORECASE,
)
FACTUAL_PATTERN = re.compile(
    r"\b(who|what|when|where|which|latest|current|still|active|ceo|version|price|law|visa|policy|won)\b",
    re.IGNORECASE,
)
RISK_TO_CONFIDENCE = {
    "safe": 0.95,
    "low_risk": 0.88,
    "medium_risk": 0.82,
    "high_risk": 0.88,
    "critical_risk": 0.93,
    "unknown_risk": 0.35,
}


def label_uncertainty_and_risk(
    question: str,
    answer: str | dict[str, Any] | None = None,
    temporal_category: str | None = None,
    freshness_payload: dict[str, Any] | None = None,
    verification_payload: dict[str, Any] | None = None,
    outdatedness_payload: dict[str, Any] | None = None,
    correction_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Assign final uncertainty, risk, trust, and safety labels.

    This function uses previous pipeline outputs only. It does not retrieve,
    verify, correct, browse, or call an LLM.
    """
    if answer is None and all(payload is None for payload in (freshness_payload, verification_payload, outdatedness_payload, correction_payload)):
        return {"uncertainty": "low", "risk": "low"}
    if isinstance(answer, dict) and temporal_category is None and all(
        payload is None for payload in (freshness_payload, verification_payload, outdatedness_payload, correction_payload)
    ):
        return {"uncertainty": "low", "risk": "low"}

    answer_text = "" if answer is None or isinstance(answer, dict) else str(answer)
    high_risk = _detect_high_risk_domain(
        question,
        answer_text,
        freshness_payload,
        verification_payload,
        outdatedness_payload,
        correction_payload,
    )
    freshness_dependency = _infer_freshness_dependency(temporal_category, high_risk, question)
    confidences = _get_confidence_values(freshness_payload, verification_payload, correction_payload)
    final_risk = _infer_final_risk_label(outdatedness_payload, correction_payload, high_risk, temporal_category, question)
    correction_status = _correction_status(correction_payload)
    outdatedness_status = _outdatedness_status(outdatedness_payload)
    trust_score = _calculate_trust_score(confidences, final_risk, high_risk)
    uncertainty_label = "unknown" if final_risk == "unknown_risk" else _confidence_to_uncertainty_label(trust_score)

    return {
        "final_risk_label": final_risk,
        "uncertainty_label": uncertainty_label,
        "trust_score": trust_score,
        "temporal_safety_status": _infer_safety_status(final_risk, correction_status, outdatedness_status),
        "user_warning": _build_user_warning(final_risk, high_risk, freshness_dependency, correction_status),
        "dashboard_badge": _build_dashboard_badge(outdatedness_status, correction_status, final_risk),
        "risk_reasons": _build_risk_reasons(
            final_risk,
            outdatedness_status,
            correction_status,
            high_risk,
            temporal_category,
            freshness_dependency,
        ),
        "uncertainty_reasons": _build_uncertainty_reasons(
            confidences,
            correction_status,
            freshness_payload,
            verification_payload,
            correction_payload,
        ),
        "recommended_user_action": _infer_recommended_action(final_risk, high_risk, freshness_dependency, correction_status),
        "high_risk_domain": high_risk,
        "freshness_dependency": freshness_dependency,
        "label_confidence": _label_confidence(final_risk, outdatedness_payload, correction_payload),
        "notes": _notes(final_risk, outdatedness_status, correction_status),
    }


def _detect_high_risk_domain(question: str, answer: str, *payloads: dict[str, Any] | None) -> bool:
    text_parts = [question, answer]
    for payload in payloads:
        text_parts.append(_payload_text(payload))
    return HIGH_RISK_PATTERN.search(" ".join(text_parts)) is not None


def _infer_freshness_dependency(temporal_category: str | None, high_risk: bool, question: str) -> str:
    text = question.lower()
    if high_risk and re.search(r"\b(current|still|active|latest|now|today)\b", text):
        return "critical"
    if temporal_category in {"RECENT_ONLY", "TIME_SENSITIVE"}:
        if re.search(r"\b(latest|current|still|active|now|today|ceo|version)\b", text):
            return "high"
        return "medium"
    if temporal_category == "VERSION_DEPENDENT":
        return "medium"
    if temporal_category == "HISTORICAL":
        return "none"
    if temporal_category == "STATIC":
        return "none"
    return "low" if _is_factual_question(question) else "none"


def _get_confidence_values(
    freshness_payload: dict[str, Any] | None,
    verification_payload: dict[str, Any] | None,
    correction_payload: dict[str, Any] | None,
) -> dict[str, float | None]:
    return {
        "freshness_score": _number(freshness_payload, "overall_freshness_score"),
        "source_reliability": _number(freshness_payload, "overall_freshness_score"),
        "verification_confidence": _number(verification_payload, "overall_confidence"),
        "correction_confidence": _number(correction_payload, "confidence"),
    }


def _calculate_trust_score(confidences: dict[str, float | None], status: str, high_risk: bool) -> float:
    correction = confidences.get("correction_confidence")
    verification = confidences.get("verification_confidence")
    freshness = confidences.get("freshness_score")
    reliability = confidences.get("source_reliability")

    if status == "unknown_risk":
        return 0.0
    if status == "critical_risk":
        base = _average_available([correction, verification, freshness], default=0.25)
        return _round(min(base, 0.39 if high_risk else 0.49))
    if correction is not None:
        score = (0.40 * correction) + (0.30 * (verification if verification is not None else correction)) + (
            0.30 * (freshness if freshness is not None else correction)
        )
    else:
        score = (0.50 * (verification if verification is not None else 0.60)) + (
            0.30 * (freshness if freshness is not None else 0.60)
        ) + (0.20 * (reliability if reliability is not None else 0.60))
    if high_risk and status in {"high_risk", "critical_risk"}:
        score -= 0.10
    return _round(_clamp(score))


def _confidence_to_uncertainty_label(confidence: float | None) -> str:
    if confidence is None:
        return "unknown"
    if confidence >= 0.90:
        return "very_low"
    if confidence >= 0.75:
        return "low"
    if confidence >= 0.60:
        return "medium"
    if confidence >= 0.40:
        return "high"
    return "very_high"


def _infer_final_risk_label(
    outdatedness_payload: dict[str, Any] | None,
    correction_payload: dict[str, Any] | None,
    high_risk: bool,
    temporal_category: str | None,
    question: str,
) -> str:
    if not isinstance(outdatedness_payload, dict) or not isinstance(correction_payload, dict):
        return "unknown_risk" if temporal_category in {"RECENT_ONLY", "TIME_SENSITIVE", "VERSION_DEPENDENT"} or _is_factual_question(question) else "safe"

    outdatedness = _outdatedness_status(outdatedness_payload)
    correction = _correction_status(correction_payload)
    if outdatedness == "NOT_APPLICABLE":
        return "safe"
    if high_risk and (correction == "unable_to_correct" or outdatedness in {"UNVERIFIED_RISKY", "CONTRADICTED"}):
        return "critical_risk"
    if correction == "unable_to_correct":
        return "high_risk"
    if correction == "partially_corrected":
        return "high_risk" if high_risk else "high_risk"
    if correction == "corrected":
        if outdatedness == "CONTRADICTED":
            return "high_risk" if high_risk else "medium_risk"
        return "medium_risk"
    if outdatedness == "NOT_OUTDATED" and correction == "no_correction_needed":
        return "low_risk" if high_risk else "safe"
    if outdatedness == "NOT_ENOUGH_INFORMATION":
        return "high_risk" if temporal_category in {"RECENT_ONLY", "TIME_SENSITIVE", "VERSION_DEPENDENT"} else "unknown_risk"
    if outdatedness == "UNVERIFIED_RISKY":
        return "critical_risk" if high_risk else "high_risk"
    return "unknown_risk"


def _infer_safety_status(final_risk_label: str, correction_status: str | None, outdatedness_status: str | None) -> str:
    if outdatedness_status == "NOT_APPLICABLE":
        return "not_applicable"
    if final_risk_label in {"safe", "low_risk"}:
        return "safe_to_show"
    if final_risk_label == "medium_risk":
        return "show_with_caution"
    if final_risk_label == "high_risk":
        return "needs_more_evidence" if correction_status == "unable_to_correct" else "show_with_caution"
    if final_risk_label == "critical_risk":
        return "do_not_use_as_final"
    return "needs_more_evidence"


def _build_dashboard_badge(outdatedness_status: str | None, correction_status: str | None, final_risk_label: str) -> str:
    if final_risk_label == "unknown_risk":
        return "UNKNOWN"
    if outdatedness_status == "NOT_APPLICABLE":
        return "NO FACTUAL CLAIMS"
    if outdatedness_status == "OUTDATED" and correction_status == "corrected":
        return "OUTDATED - CORRECTED"
    if outdatedness_status == "CONTRADICTED" and correction_status == "corrected":
        return "CONTRADICTION - CORRECTED"
    if correction_status == "partially_corrected":
        return "PARTIALLY CORRECTED"
    if correction_status == "unable_to_correct":
        return "CRITICAL - VERIFY OFFICIAL SOURCE" if final_risk_label == "critical_risk" else "UNVERIFIED"
    if final_risk_label == "safe":
        return "SAFE"
    if final_risk_label == "low_risk":
        return "LOW RISK"
    if final_risk_label == "medium_risk":
        return "TIME-SENSITIVE"
    if final_risk_label == "high_risk":
        return "HIGH RISK"
    if final_risk_label == "critical_risk":
        return "CRITICAL - VERIFY OFFICIAL SOURCE"
    return "UNKNOWN"


def _build_user_warning(
    final_risk_label: str,
    high_risk: bool,
    freshness_dependency: str,
    correction_status: str | None,
) -> str | None:
    if final_risk_label in {"safe", "low_risk"}:
        return None
    if final_risk_label == "critical_risk":
        return "This is a high-risk topic. Do not rely on this answer without checking an official source or qualified expert."
    if correction_status == "unable_to_correct":
        return "Reliable evidence was insufficient, so this answer should not be treated as confirmed."
    if final_risk_label == "high_risk":
        return "This answer has important uncertainty and should be verified before use."
    if freshness_dependency in {"high", "critical"}:
        return "This answer was updated using checked evidence, but it may change again in the future."
    return "This answer has some remaining uncertainty."


def _infer_recommended_action(
    final_risk_label: str,
    high_risk: bool,
    freshness_dependency: str,
    correction_status: str | None,
) -> str:
    if final_risk_label == "unknown_risk":
        return "retrieve_more_evidence"
    if final_risk_label in {"safe", "low_risk"}:
        return "none"
    if high_risk and final_risk_label == "critical_risk":
        return "consult_expert"
    if correction_status == "unable_to_correct":
        return "retrieve_more_evidence"
    if freshness_dependency in {"high", "critical"}:
        return "verify_official_source"
    return "verify_official_source"


def _build_risk_reasons(
    final_risk_label: str,
    outdatedness_status: str | None,
    correction_status: str | None,
    high_risk: bool,
    temporal_category: str | None,
    freshness_dependency: str,
) -> list[str]:
    reasons: list[str] = []
    if outdatedness_status == "NOT_APPLICABLE":
        return ["not_applicable"]
    if outdatedness_status == "OUTDATED":
        reasons.append("original_answer_outdated")
    if outdatedness_status == "CONTRADICTED":
        reasons.append("contradicted_claim_detected")
    if correction_status == "corrected":
        reasons.append("correction_successful")
    if correction_status == "partially_corrected":
        reasons.append("partial_correction")
    if correction_status == "unable_to_correct":
        reasons.append("insufficient_evidence")
    if high_risk:
        reasons.append("high_risk_domain")
    if temporal_category in {"RECENT_ONLY", "TIME_SENSITIVE", "VERSION_DEPENDENT"}:
        reasons.append("time_sensitive_question")
    if freshness_dependency in {"high", "critical"}:
        reasons.append("freshness_dependent")
    if final_risk_label == "safe" and not reasons:
        reasons.append("supported_static_answer")
    if final_risk_label == "unknown_risk":
        reasons.append("missing_pipeline_inputs")
    return _unique(reasons)


def _build_uncertainty_reasons(
    confidences: dict[str, float | None],
    correction_status: str | None,
    freshness_payload: dict[str, Any] | None,
    verification_payload: dict[str, Any] | None,
    correction_payload: dict[str, Any] | None,
) -> list[str]:
    reasons: list[str] = []
    if correction_status == "no_correction_needed":
        reasons.append("stable_knowledge")
    if correction_status == "corrected":
        reasons.append("fresh_evidence_available")
    if correction_status == "partially_corrected":
        reasons.append("partial_correction")
    if correction_status == "unable_to_correct":
        reasons.extend(["evidence_missing", "correction_failed"])
    if confidences.get("verification_confidence") is not None and float(confidences["verification_confidence"] or 0.0) < 0.75:
        reasons.append("low_verification_confidence")
    if not isinstance(freshness_payload, dict) and correction_status not in {"no_correction_needed", None}:
        reasons.append("freshness_score_missing")
    if not isinstance(verification_payload, dict) or not isinstance(correction_payload, dict):
        reasons.append("pipeline_input_missing")
    return _unique(reasons)


def _label_confidence(
    final_risk_label: str,
    outdatedness_payload: dict[str, Any] | None,
    correction_payload: dict[str, Any] | None,
) -> float:
    if final_risk_label == "unknown_risk":
        return 0.35
    base = RISK_TO_CONFIDENCE.get(final_risk_label, 0.60)
    if not isinstance(outdatedness_payload, dict) or not isinstance(correction_payload, dict):
        base -= 0.25
    return _round(_clamp(base))


def _notes(final_risk_label: str, outdatedness_status: str | None, correction_status: str | None) -> str:
    if final_risk_label == "safe" and outdatedness_status == "NOT_APPLICABLE":
        return "Temporal risk labeling is not applicable to this response."
    if final_risk_label == "safe":
        return "The answer is supported and does not require temporal correction."
    if correction_status == "corrected":
        return "The answer was corrected using previous pipeline evidence."
    if correction_status == "unable_to_correct":
        return "The answer is not safe to use as final because reliable evidence was insufficient."
    if final_risk_label == "unknown_risk":
        return "Risk could not be labeled because required pipeline inputs were missing."
    return "The answer has remaining temporal risk or uncertainty."


def _outdatedness_status(payload: dict[str, Any] | None) -> str | None:
    return str(payload.get("outdatedness_status")) if isinstance(payload, dict) and payload.get("outdatedness_status") else None


def _correction_status(payload: dict[str, Any] | None) -> str | None:
    return str(payload.get("correction_status")) if isinstance(payload, dict) and payload.get("correction_status") else None


def _payload_text(payload: dict[str, Any] | None) -> str:
    if not isinstance(payload, dict):
        return ""
    parts: list[str] = []
    for key, value in payload.items():
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            parts.extend(_payload_text(item) for item in value if isinstance(item, dict))
        elif isinstance(value, dict):
            parts.append(_payload_text(value))
        elif key in {"risk_level", "answer_temporal_risk"}:
            parts.append(str(value))
    return " ".join(parts)


def _number(payload: dict[str, Any] | None, key: str) -> float | None:
    if isinstance(payload, dict) and isinstance(payload.get(key), int | float):
        return _clamp(float(payload[key]))
    return None


def _average_available(values: list[float | None], default: float) -> float:
    available = [value for value in values if value is not None]
    if not available:
        return default
    return sum(available) / len(available)


def _is_factual_question(question: str) -> bool:
    return FACTUAL_PATTERN.search(question) is not None


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_items: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique_items.append(item)
    return unique_items


def _round(value: float) -> float:
    return round(_clamp(value), 3)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
