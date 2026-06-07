"""Structured report generation for TemporalGuard pipeline outputs."""

from __future__ import annotations

from typing import Any


EXPECTED_SECTIONS = (
    "temporal_detection",
    "claims",
    "evidence",
    "freshness",
    "verification",
    "outdatedness",
    "correction",
    "risk_label",
)
REPORT_TYPES = {"dashboard", "technical", "thesis", "debug"}


def generate_report(
    pipeline_output: dict[str, Any],
    report_type: str = "dashboard",
    max_evidence_items: int = 5,
) -> dict[str, Any]:
    """
    Generate a structured TemporalGuard report from pipeline outputs.

    This formatter only uses provided pipeline output. It does not retrieve,
    verify, correct, or invent facts.
    """
    data = pipeline_output if isinstance(pipeline_output, dict) else {}
    warnings: list[str] = []
    safe_report_type = report_type if report_type in REPORT_TYPES else "dashboard"
    if safe_report_type != report_type:
        warnings.append(f"Unknown report type '{report_type}' defaulted to dashboard.")

    example_id = data.get("example_id") if data.get("example_id") is not None else None
    missing_sections = _find_missing_sections(data)
    debug_warnings = warnings + _collect_warnings(data)

    return {
        "report_id": f"RPT_{example_id}" if example_id else "RPT_UNKNOWN",
        "example_id": example_id,
        "report_type": safe_report_type,
        "title": f"TemporalGuard Report for {example_id}" if example_id else "Temporal Reliability Report",
        "executive_summary": _build_executive_summary(data, safe_report_type),
        "final_answer": _final_answer(data),
        "dashboard_summary": _build_dashboard_summary(data),
        "pipeline_summary": _build_pipeline_summary(data),
        "claim_report": _build_claim_report(data),
        "evidence_report": _build_evidence_report(data, max_evidence_items),
        "correction_report": _build_correction_report(data),
        "thesis_summary": _build_thesis_summary(data),
        "debug_info": {
            "missing_sections": missing_sections,
            "warnings": debug_warnings,
            "raw_statuses": _get_raw_statuses(data),
            "evidence_inspection": _build_evidence_inspection(data),
        },
    }


def _safe_get(data: dict[str, Any], path: list[str], default: Any = None) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def _find_missing_sections(pipeline_output: dict[str, Any]) -> list[str]:
    return [section for section in EXPECTED_SECTIONS if not isinstance(pipeline_output.get(section), dict)]


def _get_raw_statuses(pipeline_output: dict[str, Any]) -> dict[str, Any]:
    return {
        "temporal_category": _safe_get(pipeline_output, ["temporal_detection", "temporal_category"]),
        "overall_verification_status": _safe_get(pipeline_output, ["verification", "overall_verification_status"]),
        "outdatedness_status": _safe_get(pipeline_output, ["outdatedness", "outdatedness_status"]),
        "correction_status": _safe_get(pipeline_output, ["correction", "correction_status"]),
        "final_risk_label": _safe_get(pipeline_output, ["risk_label", "final_risk_label"]),
    }


def _build_dashboard_summary(pipeline_output: dict[str, Any]) -> dict[str, Any]:
    risk = pipeline_output.get("risk_label") if isinstance(pipeline_output.get("risk_label"), dict) else {}
    return {
        "badge": risk.get("dashboard_badge", "UNKNOWN"),
        "risk_label": risk.get("final_risk_label", "unknown_risk"),
        "uncertainty_label": risk.get("uncertainty_label", "unknown"),
        "trust_score": _number_or_default(risk.get("trust_score"), 0.0),
        "temporal_safety_status": risk.get("temporal_safety_status", "needs_more_evidence"),
        "user_warning": risk.get("user_warning"),
    }


def _build_pipeline_summary(pipeline_output: dict[str, Any]) -> dict[str, Any]:
    return {
        "temporal_category": _safe_get(pipeline_output, ["temporal_detection", "temporal_category"]),
        "needs_fresh_evidence": bool(_safe_get(pipeline_output, ["temporal_detection", "needs_fresh_evidence"], False)),
        "total_claims": int(_safe_get(pipeline_output, ["claims", "total_claims"], len(_claim_items(pipeline_output))) or 0),
        "verification_status": _safe_get(pipeline_output, ["verification", "overall_verification_status"]),
        "outdatedness_status": _safe_get(pipeline_output, ["outdatedness", "outdatedness_status"]),
        "correction_status": _safe_get(pipeline_output, ["correction", "correction_status"]),
        "final_risk_label": _safe_get(pipeline_output, ["risk_label", "final_risk_label"]),
    }


def _build_claim_report(pipeline_output: dict[str, Any]) -> list[dict[str, Any]]:
    claims_by_id = {str(claim.get("claim_id")): claim for claim in _claim_items(pipeline_output) if claim.get("claim_id")}
    verification_by_id = {
        str(result.get("claim_id")): result
        for result in _verification_items(pipeline_output)
        if result.get("claim_id")
    }
    all_ids = list(dict.fromkeys(list(claims_by_id) + list(verification_by_id)))
    reports: list[dict[str, Any]] = []
    for claim_id in all_ids:
        claim = claims_by_id.get(claim_id, {})
        verification = verification_by_id.get(claim_id, {})
        claim_text = claim.get("claim_text") or verification.get("claim_text") or ""
        status = verification.get("verification_status")
        reports.append(
            {
                "claim_id": claim_id,
                "claim_text": claim_text,
                "claim_type": claim.get("claim_type"),
                "verification_status": status,
                "risk_level": verification.get("risk_level"),
                "requires_correction": bool(verification.get("requires_correction", False)),
                "claim_value": verification.get("claim_value"),
                "evidence_value": verification.get("evidence_value"),
                "short_explanation": _claim_explanation(status, verification),
            }
        )
    return reports


def _build_evidence_report(pipeline_output: dict[str, Any], max_items: int) -> list[dict[str, Any]]:
    freshness_scores = _freshness_scores_by_key(pipeline_output)
    reports: list[dict[str, Any]] = []
    limit = max(0, int(max_items or 0))
    for evidence_result in _evidence_results(pipeline_output):
        claim_id = str(evidence_result.get("claim_id") or "")
        items = evidence_result.get("evidence_items")
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict) or len(reports) >= limit:
                continue
            evidence_id = str(item.get("evidence_id") or "")
            score = freshness_scores.get((claim_id, evidence_id), {})
            reports.append(
                {
                    "claim_id": claim_id,
                    "evidence_id": evidence_id,
                    "title": str(item.get("title") or ""),
                    "publisher": str(item.get("publisher") or "unknown"),
                    "source_type": str(item.get("source_type") or "other"),
                    "url": str(item.get("url") or ""),
                    "date_used": score.get("date_used") or item.get("updated_date") or item.get("published_date"),
                    "freshness_label": score.get("freshness_label"),
                    "combined_score": _number_or_default(score.get("combined_score"), 0.0),
                    "evidence_summary": _shorten(str(item.get("evidence_summary") or "")),
                }
            )
    return reports


def _build_evidence_inspection(pipeline_output: dict[str, Any]) -> list[dict[str, Any]]:
    freshness_scores = _freshness_scores_by_key(pipeline_output)
    inspections: list[dict[str, Any]] = []
    for evidence_result in _evidence_results(pipeline_output):
        claim_id = str(evidence_result.get("claim_id") or "")
        items = evidence_result.get("evidence_items")
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            evidence_id = str(item.get("evidence_id") or "")
            score = freshness_scores.get((claim_id, evidence_id), {})
            inspections.append(
                {
                    "claim_id": claim_id,
                    "evidence_id": evidence_id,
                    "title": str(item.get("title") or ""),
                    "url": str(item.get("url") or ""),
                    "snippet": _shorten(str(item.get("snippet") or item.get("content") or item.get("evidence_summary") or ""), 320),
                    "evidence_value": item.get("evidence_value"),
                    "freshness_score": _number_or_default(score.get("freshness_score"), 0.0),
                    "combined_score": _number_or_default(score.get("combined_score"), 0.0),
                }
            )
    return inspections


def _build_correction_report(pipeline_output: dict[str, Any]) -> dict[str, Any]:
    correction = pipeline_output.get("correction") if isinstance(pipeline_output.get("correction"), dict) else {}
    original = str(pipeline_output.get("original_answer") or "")
    corrected = str(correction.get("corrected_answer") or original)
    return {
        "original_answer": original,
        "corrected_answer": corrected,
        "changed_claim_ids": list(correction.get("changed_claim_ids") or []),
        "unsupported_claim_ids": list(correction.get("unsupported_claim_ids") or []),
        "freshness_note": correction.get("freshness_note"),
        "uncertainty_note": correction.get("uncertainty_note"),
        "safety_note": correction.get("safety_note"),
        "user_visible_explanation": correction.get("user_visible_explanation"),
    }


def _infer_temporal_failure_type(pipeline_output: dict[str, Any]) -> str:
    outdatedness = _safe_get(pipeline_output, ["outdatedness", "outdatedness_status"])
    temporal_category = _safe_get(pipeline_output, ["temporal_detection", "temporal_category"])
    claim_types = {str(claim.get("claim_type")) for claim in _claim_items(pipeline_output)}
    if outdatedness == "OUTDATED":
        return "version_mismatch" if "software_version" in claim_types else "outdated_current_fact"
    if outdatedness == "CONTRADICTED":
        return "contradicted_historical_fact" if temporal_category == "HISTORICAL" else "outdated_current_fact"
    if outdatedness == "UNVERIFIED_RISKY":
        return "policy_status_uncertainty" if "law_or_policy" in claim_types else "insufficient_evidence_for_current_claim"
    if outdatedness == "NOT_APPLICABLE":
        return "not_applicable"
    if outdatedness == "NOT_OUTDATED":
        return "no_failure_detected"
    return "unknown"


def _build_thesis_summary(pipeline_output: dict[str, Any]) -> dict[str, str]:
    failure_type = _infer_temporal_failure_type(pipeline_output)
    outdatedness = _safe_get(pipeline_output, ["outdatedness", "outdatedness_status"], "unknown")
    correction = _safe_get(pipeline_output, ["correction", "correction_status"], "unknown")
    return {
        "problem_observed": _problem_observed(failure_type),
        "temporal_failure_type": failure_type,
        "evidence_quality": _evidence_quality(pipeline_output),
        "system_decision": f"TemporalGuard marked the answer as {outdatedness} and correction status was {correction}.",
        "research_value": _research_value(failure_type),
    }


def _build_executive_summary(pipeline_output: dict[str, Any], report_type: str) -> str:
    del report_type
    temporal = _safe_get(pipeline_output, ["temporal_detection", "temporal_category"], "unknown")
    outdatedness = _safe_get(pipeline_output, ["outdatedness", "outdatedness_status"], "unknown")
    correction = _safe_get(pipeline_output, ["correction", "correction_status"], "unknown")
    badge = _safe_get(pipeline_output, ["risk_label", "dashboard_badge"], "UNKNOWN")
    if outdatedness == "OUTDATED":
        return "The original answer was time-sensitive and contained an outdated claim. TemporalGuard compared it with the checked evidence and generated a corrected response. The result remains time-sensitive and should be interpreted with the displayed risk label."
    if outdatedness == "UNVERIFIED_RISKY":
        return "The original answer involved a current or high-risk claim that could not be verified with reliable evidence. TemporalGuard avoided unsupported correction and marked the answer as risky. More authoritative evidence is needed before relying on it."
    if outdatedness == "NOT_OUTDATED":
        return "The extracted factual claims were supported by the available verification result. TemporalGuard did not detect an outdated answer. No correction was required."
    if outdatedness == "NOT_APPLICABLE":
        return "Temporal outdatedness was not applicable because no checkable factual claim required verification. The report records the result for completeness."
    return f"TemporalGuard generated a {badge} report. Temporal category is {temporal}, outdatedness status is {outdatedness}, and correction status is {correction}."


def _final_answer(pipeline_output: dict[str, Any]) -> str:
    corrected = _safe_get(pipeline_output, ["correction", "corrected_answer"])
    return str(corrected if corrected is not None else pipeline_output.get("original_answer", ""))


def _claim_items(pipeline_output: dict[str, Any]) -> list[dict[str, Any]]:
    claims = _safe_get(pipeline_output, ["claims", "claims"], [])
    return [claim for claim in claims if isinstance(claim, dict)] if isinstance(claims, list) else []


def _verification_items(pipeline_output: dict[str, Any]) -> list[dict[str, Any]]:
    items = _safe_get(pipeline_output, ["verification", "verification_results"], [])
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def _evidence_results(pipeline_output: dict[str, Any]) -> list[dict[str, Any]]:
    items = _safe_get(pipeline_output, ["evidence", "evidence_results"], [])
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def _freshness_scores_by_key(pipeline_output: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    scores: dict[tuple[str, str], dict[str, Any]] = {}
    freshness_results = _safe_get(pipeline_output, ["freshness", "freshness_results"], [])
    if not isinstance(freshness_results, list):
        return scores
    for result in freshness_results:
        if not isinstance(result, dict):
            continue
        claim_id = str(result.get("claim_id") or "")
        evidence_scores = result.get("evidence_scores")
        if not isinstance(evidence_scores, list):
            continue
        for score in evidence_scores:
            if isinstance(score, dict):
                scores[(claim_id, str(score.get("evidence_id") or ""))] = score
    return scores


def _claim_explanation(status: Any, verification: dict[str, Any]) -> str:
    if not status:
        return "This claim was extracted but not verified."
    if verification.get("reason"):
        return str(verification["reason"])
    if status == "SUPPORTED":
        return "The claim was supported by the available evidence."
    if status == "OUTDATED":
        return "The claim was marked OUTDATED because the evidence value differs from the claim value."
    if status == "CONTRADICTED":
        return "The claim was contradicted by the checked evidence."
    if status == "INSUFFICIENT_EVIDENCE":
        return "The claim could not be verified with enough reliable evidence."
    return f"The claim verification status was {status}."


def _evidence_quality(pipeline_output: dict[str, Any]) -> str:
    score = _safe_get(pipeline_output, ["freshness", "overall_freshness_score"])
    if isinstance(score, int | float):
        if score >= 0.85:
            return "The evidence was fresh and authoritative."
        if score >= 0.60:
            return "The evidence was acceptable but not ideal."
        return "The evidence quality was weak or stale."
    if _evidence_results(pipeline_output):
        return "Evidence was available, but freshness scoring was missing."
    return "The evidence was insufficient or missing."


def _problem_observed(failure_type: str) -> str:
    if failure_type == "version_mismatch":
        return "The base LLM produced an answer that depended on current software-version information but used an outdated value."
    if failure_type == "contradicted_historical_fact":
        return "The base LLM produced a historical claim that conflicted with the checked evidence."
    if failure_type == "insufficient_evidence_for_current_claim":
        return "The base LLM produced a current claim that could not be verified with sufficient evidence."
    if failure_type == "policy_status_uncertainty":
        return "The base LLM produced a policy-status claim that required stronger current evidence."
    if failure_type == "no_failure_detected":
        return "No temporal failure was detected in the verified answer."
    if failure_type == "not_applicable":
        return "Temporal verification was not applicable to this response."
    return "The temporal reliability outcome could not be fully classified."


def _research_value(failure_type: str) -> str:
    if failure_type == "version_mismatch":
        return "This example shows how TemporalGuard can reduce outdated answers in current software-version questions."
    if failure_type == "contradicted_historical_fact":
        return "This example shows how TemporalGuard can detect conflicts in historically anchored claims."
    if failure_type in {"insufficient_evidence_for_current_claim", "policy_status_uncertainty"}:
        return "This example shows that the system avoids overclaiming when fresh evidence is not available."
    if failure_type == "no_failure_detected":
        return "This example shows the system can preserve answers when no temporal failure is detected."
    return "This example documents how the pipeline handles non-temporal or incomplete cases."


def _collect_warnings(pipeline_output: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    for section in ("verification", "outdatedness", "correction", "risk_label", "freshness", "evidence"):
        value = pipeline_output.get(section)
        if isinstance(value, dict) and isinstance(value.get("warnings"), list):
            warnings.extend(str(item) for item in value["warnings"])
        if isinstance(value, dict) and isinstance(value.get("verification_warnings"), list):
            warnings.extend(str(item) for item in value["verification_warnings"])
        if isinstance(value, dict) and isinstance(value.get("scoring_warnings"), list):
            warnings.extend(str(item) for item in value["scoring_warnings"])
        if isinstance(value, dict) and isinstance(value.get("retrieval_warnings"), list):
            warnings.extend(str(item) for item in value["retrieval_warnings"])
    return warnings


def _number_or_default(value: Any, default: float) -> float:
    return float(value) if isinstance(value, int | float) else default


def _shorten(text: str, limit: int = 240) -> str:
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."
