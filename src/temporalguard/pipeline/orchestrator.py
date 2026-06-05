"""End-to-end TemporalGuard pipeline orchestration."""

from __future__ import annotations

from datetime import UTC, datetime
import time
from typing import Any, Callable

from temporalguard.llm.answer_generator import generate_base_answer
from temporalguard.reporting.report_generator import generate_report
from temporalguard.skills.claim_extractor import extract_claims
from temporalguard.skills.correction_generator import generate_correction
from temporalguard.skills.fresh_evidence_retriever import retrieve_fresh_evidence
from temporalguard.skills.outdated_answer_detector import detect_outdated_answer
from temporalguard.skills.source_freshness_scorer import score_source_freshness
from temporalguard.skills.temporal_question_detector import detect_temporal_category
from temporalguard.skills.temporal_verifier import verify_temporal_claims
from temporalguard.skills.uncertainty_risk_labeler import label_uncertainty_and_risk


def run_temporalguard_pipeline(
    question: str,
    base_answer: str | None = None,
    llm_provider: Any = None,
    search_provider: Any = None,
    config: dict[str, Any] | None = None,
    report_type: str = "dashboard",
) -> dict[str, Any]:
    """
    Run the full TemporalGuard pipeline for one question.

    The orchestrator delegates work to existing skill modules. It does not
    retrieve, verify, correct, browse, or call external services on its own.
    """
    started = time.perf_counter()
    started_at = _now_utc_iso()
    cfg = config or {}
    warnings: list[str] = []
    errors: list[dict[str, str]] = []

    original_answer = _obtain_answer(question, base_answer, llm_provider, cfg, warnings, errors)
    temporal_detection = _run_step("temporal_detection", errors, lambda: detect_temporal_category(question), _fallback_temporal())
    temporal_category = temporal_detection.get("temporal_category") if isinstance(temporal_detection, dict) else None
    claims = _run_step(
        "claims",
        errors,
        lambda: extract_claims(question, original_answer, temporal_category),
        _fallback_claims(),
    )
    evidence = _run_step(
        "evidence",
        errors,
        lambda: retrieve_fresh_evidence(
            question=question,
            claims_payload=claims,
            temporal_category=temporal_category,
            search_provider=search_provider,
            max_sources_per_claim=int(cfg.get("max_sources_per_claim", 3)),
            max_claims=int(cfg.get("max_claims", 5)),
        ),
        _fallback_evidence(claims),
    )
    warnings.extend(_payload_warnings(evidence, "retrieval_warnings"))

    freshness = _run_step(
        "freshness",
        errors,
        lambda: score_source_freshness(evidence, temporal_category, cfg.get("scoring_datetime")),
        _fallback_freshness(evidence),
    )
    warnings.extend(_payload_warnings(freshness, "scoring_warnings"))

    verification = _run_step(
        "verification",
        errors,
        lambda: verify_temporal_claims(question, claims, evidence, freshness, temporal_category),
        _fallback_verification(claims),
    )
    warnings.extend(_payload_warnings(verification, "verification_warnings"))

    outdatedness = _run_step(
        "outdatedness",
        errors,
        lambda: detect_outdated_answer(question, original_answer, verification, claims, temporal_category, freshness),
        _fallback_outdatedness(),
    )

    correction = _run_step(
        "correction",
        errors,
        lambda: generate_correction(
            question,
            original_answer,
            verification,
            outdatedness,
            claims,
            evidence,
            freshness,
            temporal_category,
        ),
        _fallback_correction(original_answer),
    )
    warnings.extend(_payload_warnings(correction, "warnings"))

    risk_label = _run_step(
        "risk_label",
        errors,
        lambda: label_uncertainty_and_risk(
            question,
            original_answer,
            temporal_category,
            freshness,
            verification,
            outdatedness,
            correction,
        ),
        _fallback_risk_label(),
    )

    output: dict[str, Any] = {
        "run_id": _run_id(started_at),
        "question": question,
        "original_answer": original_answer,
        "temporal_detection": temporal_detection,
        "claims": claims,
        "evidence": evidence,
        "freshness": freshness,
        "verification": verification,
        "outdatedness": outdatedness,
        "correction": correction,
        "risk_label": risk_label,
        "report": {},
        "runtime": {
            "started_at": started_at,
            "finished_at": "",
            "duration_ms": 0,
        },
        "pipeline_status": "success",
        "errors": errors,
        "warnings": _unique(warnings),
    }

    report = _run_step("report", errors, lambda: generate_report(output, report_type), {})
    output["report"] = report
    output["runtime"]["finished_at"] = _now_utc_iso()
    output["runtime"]["duration_ms"] = int((time.perf_counter() - started) * 1000)
    output["pipeline_status"] = _pipeline_status(errors, output["warnings"])
    return output


def run_pipeline(question: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Backward-compatible wrapper around the full TemporalGuard pipeline."""
    cfg = config or {}
    return run_temporalguard_pipeline(
        question=question,
        base_answer=cfg.get("base_answer"),
        llm_provider=cfg.get("llm_provider"),
        search_provider=cfg.get("search_provider"),
        config=cfg,
        report_type=str(cfg.get("report_type", "dashboard")),
    )


def _obtain_answer(
    question: str,
    base_answer: str | None,
    llm_provider: Any,
    config: dict[str, Any],
    warnings: list[str],
    errors: list[dict[str, str]],
) -> str:
    if isinstance(base_answer, str) and base_answer.strip():
        return base_answer
    if llm_provider is not None:
        result = generate_base_answer(question, llm_provider, max_tokens=int(config.get("max_tokens", 512)))
        warnings.extend(str(item) for item in result.get("warnings", []))
        for error in result.get("errors", []):
            errors.append({"step": "answer_generation", "message": str(error)})
        answer = str(result.get("answer") or "").strip()
        if result.get("status") == "success" and answer:
            return answer
    warnings.append("No base answer available; using safe fallback answer.")
    return "I could not generate a base answer safely."


def _run_step(step: str, errors: list[dict[str, str]], func: Callable[[], Any], fallback: Any) -> Any:
    try:
        return func()
    except Exception as exc:  # pragma: no cover - exercised via monkeypatch in tests
        errors.append({"step": step, "message": str(exc)})
        return fallback


def _fallback_temporal() -> dict[str, Any]:
    return {
        "temporal_category": "UNKNOWN",
        "needs_fresh_evidence": True,
        "confidence": 0.0,
        "reason": "Temporal detection failed.",
        "temporal_signals": [],
        "temporal_anchor": None,
        "recommended_next_action": "ask_clarifying_question",
    }


def _fallback_claims() -> dict[str, Any]:
    return {"claims": [], "total_claims": 0, "needs_verification": False, "notes": "Claim extraction failed."}


def _fallback_evidence(claims: dict[str, Any]) -> dict[str, Any]:
    evidence_results = []
    for claim in claims.get("claims", []) if isinstance(claims, dict) else []:
        evidence_results.append(
            {
                "claim_id": claim.get("claim_id"),
                "claim_text": claim.get("claim_text", ""),
                "query_used": "",
                "evidence_items": [],
                "evidence_count": 0,
                "retrieval_status": "failed",
                "notes": "Evidence retrieval failed.",
            }
        )
    return {
        "evidence_results": evidence_results,
        "total_claims_processed": len(evidence_results),
        "total_evidence_items": 0,
        "retrieval_warnings": ["Evidence retrieval failed."],
    }


def _fallback_freshness(evidence: dict[str, Any]) -> dict[str, Any]:
    del evidence
    return {
        "freshness_results": [],
        "overall_freshness_score": 0.0,
        "overall_temporal_risk": "unknown",
        "scoring_warnings": ["Freshness scoring failed."],
    }


def _fallback_verification(claims: dict[str, Any]) -> dict[str, Any]:
    results = []
    for claim in claims.get("claims", []) if isinstance(claims, dict) else []:
        results.append(
            {
                "claim_id": claim.get("claim_id"),
                "claim_text": claim.get("claim_text", ""),
                "verification_status": "INSUFFICIENT_EVIDENCE",
                "temporal_validity": "uncertain",
                "verification_confidence": 0.0,
                "evidence_used": [],
                "best_evidence_id": None,
                "reason": "Verification failed.",
                "detected_conflict": None,
                "claim_value": None,
                "evidence_value": None,
                "requires_correction": False,
                "risk_level": "unknown",
                "notes": "Fallback verification result.",
            }
        )
    return {
        "verification_results": results,
        "overall_verification_status": "INSUFFICIENT_EVIDENCE",
        "overall_confidence": 0.0,
        "verification_warnings": ["Verification failed."],
    }


def _fallback_outdatedness() -> dict[str, Any]:
    return {
        "outdatedness_status": "NOT_ENOUGH_INFORMATION",
        "is_outdated": False,
        "requires_correction": True,
        "answer_temporal_risk": "unknown",
        "outdated_claim_ids": [],
        "contradicted_claim_ids": [],
        "unsupported_claim_ids": [],
        "supported_claim_ids": [],
        "critical_claim_ids": [],
        "main_issue": "Outdatedness detection failed.",
        "decision_reason": "The pipeline could not determine answer outdatedness.",
        "confidence": 0.0,
        "recommended_next_action": "request_more_evidence",
        "answer_level_summary": {
            "total_claims": 0,
            "supported_count": 0,
            "outdated_count": 0,
            "contradicted_count": 0,
            "partially_supported_count": 0,
            "insufficient_evidence_count": 0,
            "not_verifiable_count": 0,
        },
        "warnings": ["Outdatedness detection failed."],
    }


def _fallback_correction(original_answer: str) -> dict[str, Any]:
    return {
        "corrected_answer": original_answer,
        "correction_status": "unable_to_correct",
        "correction_type": "add_uncertainty",
        "changed_claim_ids": [],
        "unchanged_claim_ids": [],
        "unsupported_claim_ids": [],
        "evidence_used": [],
        "freshness_note": "Correction generation failed.",
        "uncertainty_note": "The answer could not be corrected safely.",
        "safety_note": None,
        "answer_temporal_risk": "unknown",
        "confidence": 0.0,
        "user_visible_explanation": "Correction generation failed.",
        "warnings": ["Correction generation failed."],
    }


def _fallback_risk_label() -> dict[str, Any]:
    return {
        "final_risk_label": "unknown_risk",
        "uncertainty_label": "unknown",
        "trust_score": 0.0,
        "temporal_safety_status": "needs_more_evidence",
        "user_warning": "Risk labeling failed.",
        "dashboard_badge": "UNKNOWN",
        "risk_reasons": ["risk_labeling_failed"],
        "uncertainty_reasons": ["pipeline_error"],
        "recommended_user_action": "retrieve_more_evidence",
        "high_risk_domain": False,
        "freshness_dependency": "low",
        "label_confidence": 0.0,
        "notes": "Risk labeling failed.",
    }


def _payload_warnings(payload: Any, key: str) -> list[str]:
    if isinstance(payload, dict) and isinstance(payload.get(key), list):
        return [str(item) for item in payload[key]]
    return []


def _pipeline_status(errors: list[dict[str, str]], warnings: list[str]) -> str:
    if errors:
        return "partial_success"
    if warnings:
        return "partial_success"
    return "success"


def _run_id(started_at: str) -> str:
    compact = started_at.replace("-", "").replace(":", "").replace("T", "_").replace("Z", "")
    return f"TG_{compact}"


def _now_utc_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_items: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique_items.append(item)
    return unique_items
