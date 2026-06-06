"""Helper utilities for the TemporalGuard Streamlit dashboard."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


SAMPLE_QUESTIONS = [
    "What is the latest Python version?",
    "What is binary search?",
    "Is this visa rule still active?",
    "Who won the 2014 FIFA World Cup?",
    "Who is the CEO of OpenAI?",
    "How do I use the OpenAI API in Python?",
]

LLM_PROVIDER_OPTIONS = {
    "Demo/mock": "mock",
    "OpenAI": "openai",
    "Gemini": "gemini",
    "Claude/Anthropic": "anthropic",
}


def safe_get(data: dict[str, Any] | None, path: list[str], default: Any = None) -> Any:
    """Safely read a nested dictionary value."""
    current: Any = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def normalize_llm_provider(value: Any) -> str:
    text = str(value or "Demo/mock").strip()
    if text in LLM_PROVIDER_OPTIONS:
        return LLM_PROVIDER_OPTIONS[text]
    lowered = text.lower()
    aliases = {
        "demo": "mock",
        "demo/mock": "mock",
        "mock": "mock",
        "openai": "openai",
        "gpt": "openai",
        "gemini": "gemini",
        "google": "gemini",
        "anthropic": "anthropic",
        "claude": "anthropic",
        "claude/anthropic": "anthropic",
    }
    return aliases.get(lowered, "mock")


def build_analyze_payload(
    question: str,
    base_answer: str | None = None,
    report_type: str = "dashboard",
    llm_provider: Any = None,
    model_name: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "question": str(question or ""),
        "base_answer": base_answer if isinstance(base_answer, str) and base_answer.strip() else None,
        "llm_provider": normalize_llm_provider(llm_provider),
        "model_name": model_name.strip() if isinstance(model_name, str) and model_name.strip() else None,
        "report_type": str(report_type or "dashboard"),
    }
    return payload


def risk_to_css_class(risk_label: str | None) -> str:
    label = str(risk_label or "").lower()
    if label in {"safe", "safe_to_show"}:
        return "tg-badge-safe"
    if "critical" in label:
        return "tg-badge-critical"
    if "high" in label:
        return "tg-badge-high"
    if "medium" in label:
        return "tg-badge-medium"
    if "low" in label:
        return "tg-badge-low"
    return "tg-badge-unknown"


def badge_to_css_class(badge: str | None) -> str:
    label = str(badge or "").lower()
    if any(token in label for token in ("critical", "official", "blocked")):
        return "tg-badge-critical"
    if any(token in label for token in ("high", "verify")):
        return "tg-badge-high"
    if any(token in label for token in ("outdated", "corrected", "caution", "medium")):
        return "tg-badge-medium"
    if any(token in label for token in ("low", "review")):
        return "tg-badge-low"
    if any(token in label for token in ("safe", "supported", "current")):
        return "tg-badge-safe"
    return "tg-badge-unknown"


def format_label(label: Any, fallback: str = "Unknown") -> str:
    text = str(label if label not in (None, "") else fallback).replace("_", " ").replace("-", " ")
    return " ".join(text.split()).title()


def format_badge(label: Any) -> str:
    text = str(label if label not in (None, "") else "UNKNOWN").replace("_", " ").strip()
    return text.upper() if text else "UNKNOWN"


def get_final_answer(pipeline_output: dict[str, Any] | None) -> str:
    return str(
        safe_get(pipeline_output, ["correction", "corrected_answer"])
        or safe_get(pipeline_output, ["report", "final_answer"])
        or safe_get(pipeline_output, ["final_answer"])
        or safe_get(pipeline_output, ["original_answer"])
        or ""
    )


def get_dashboard_summary(pipeline_output: dict[str, Any] | None) -> dict[str, Any]:
    risk_label = safe_get(pipeline_output, ["risk_label"], {}) or {}
    dashboard = safe_get(pipeline_output, ["report", "dashboard_summary"], {}) or {}
    correction = safe_get(pipeline_output, ["correction"], {}) or {}
    badge = risk_label.get("dashboard_badge") or dashboard.get("badge") or "UNKNOWN"
    risk = risk_label.get("final_risk_label") or dashboard.get("risk_label") or "unknown_risk"
    warning = risk_label.get("user_warning") or dashboard.get("user_warning") or correction.get("safety_note")
    return {
        "badge": badge,
        "badge_class": badge_to_css_class(badge),
        "risk_label": risk,
        "risk_class": risk_to_css_class(risk),
        "uncertainty_label": risk_label.get("uncertainty_label") or dashboard.get("uncertainty_label") or "unknown",
        "trust_score": _as_float(risk_label.get("trust_score", dashboard.get("trust_score", 0.0))),
        "temporal_safety_status": risk_label.get("temporal_safety_status")
        or dashboard.get("temporal_safety_status")
        or "needs_more_evidence",
        "user_warning": warning,
    }


def get_pipeline_summary(pipeline_output: dict[str, Any] | None) -> dict[str, Any]:
    report_summary = safe_get(pipeline_output, ["report", "pipeline_summary"], {}) or {}
    return {
        "temporal_category": safe_get(pipeline_output, ["temporal_detection", "temporal_category"])
        or report_summary.get("temporal_category")
        or "UNKNOWN",
        "needs_fresh_evidence": bool(
            safe_get(
                pipeline_output,
                ["temporal_detection", "needs_fresh_evidence"],
                report_summary.get("needs_fresh_evidence", False),
            )
        ),
        "total_claims": _as_int(safe_get(pipeline_output, ["claims", "total_claims"], report_summary.get("total_claims", 0))),
        "verification_status": safe_get(pipeline_output, ["verification", "overall_verification_status"])
        or report_summary.get("verification_status")
        or "UNKNOWN",
        "outdatedness_status": safe_get(pipeline_output, ["outdatedness", "outdatedness_status"])
        or report_summary.get("outdatedness_status")
        or "UNKNOWN",
        "correction_status": safe_get(pipeline_output, ["correction", "correction_status"])
        or report_summary.get("correction_status")
        or "UNKNOWN",
        "final_risk_label": safe_get(pipeline_output, ["risk_label", "final_risk_label"])
        or report_summary.get("final_risk_label")
        or "unknown_risk",
        "freshness_score": _as_float(safe_get(pipeline_output, ["freshness", "overall_freshness_score"], 0.0)),
    }


def build_metric_cards(pipeline_output: dict[str, Any] | None) -> list[dict[str, str]]:
    summary = get_pipeline_summary(pipeline_output)
    dashboard = get_dashboard_summary(pipeline_output)
    return [
        {
            "label": "Temporal Category",
            "value": format_label(summary["temporal_category"]),
            "caption": "Fresh evidence required" if summary["needs_fresh_evidence"] else "Stable knowledge",
        },
        {
            "label": "Outdatedness",
            "value": format_label(summary["outdatedness_status"]),
            "caption": "Answer-level temporal decision",
        },
        {
            "label": "Verification",
            "value": format_label(summary["verification_status"]),
            "caption": f"{summary['total_claims']} extracted claim(s)",
        },
        {
            "label": "Correction",
            "value": format_label(summary["correction_status"]),
            "caption": "Final response handling",
        },
        {
            "label": "Trust Score",
            "value": f"{dashboard['trust_score']:.2f}",
            "caption": "Reliability signal after checks",
        },
        {
            "label": "Freshness Score",
            "value": f"{summary['freshness_score']:.2f}",
            "caption": "Temporal quality of evidence",
        },
    ]


def claims_to_table_rows(pipeline_output: dict[str, Any] | None) -> list[dict[str, Any]]:
    report_rows = safe_get(pipeline_output, ["report", "claim_report"])
    if isinstance(report_rows, list) and report_rows:
        return [_claim_row(row) for row in report_rows if isinstance(row, dict)]

    claims = safe_get(pipeline_output, ["claims", "claims"], [])
    verification = {
        str(item.get("claim_id")): item
        for item in safe_get(pipeline_output, ["verification", "verification_results"], [])
        if isinstance(item, dict) and item.get("claim_id") is not None
    }
    rows: list[dict[str, Any]] = []
    for claim in claims if isinstance(claims, list) else []:
        if isinstance(claim, dict):
            rows.append(_claim_row({**claim, **verification.get(str(claim.get("claim_id")), {})}))
    return rows


def evidence_to_table_rows(pipeline_output: dict[str, Any] | None) -> list[dict[str, Any]]:
    report_rows = safe_get(pipeline_output, ["report", "evidence_report"])
    if isinstance(report_rows, list) and report_rows:
        return [_evidence_row(row) for row in report_rows if isinstance(row, dict)]

    score_map = _freshness_score_map(pipeline_output)
    rows: list[dict[str, Any]] = []
    evidence_results = safe_get(pipeline_output, ["evidence", "evidence_results"], [])
    for result in evidence_results if isinstance(evidence_results, list) else []:
        if not isinstance(result, dict):
            continue
        claim_id = str(result.get("claim_id") or "")
        items = result.get("evidence_items", [])
        for item in items if isinstance(items, list) else []:
            if isinstance(item, dict):
                score = score_map.get((claim_id, str(item.get("evidence_id") or "")), {})
                rows.append(_evidence_row({**item, **score, "claim_id": claim_id}))
    return rows


def build_demo_output(question: str, base_answer: str | None = None) -> dict[str, Any]:
    q = (question or "").strip() or SAMPLE_QUESTIONS[0]
    lower = q.lower()
    if "binary search" in lower:
        demo = _demo_binary_search()
    elif "visa" in lower:
        demo = _demo_visa_rule()
    elif "2014" in lower or "world cup" in lower:
        demo = _demo_world_cup()
    elif "ceo of openai" in lower or ("openai" in lower and "ceo" in lower):
        demo = _demo_openai_ceo()
    elif "openai api" in lower:
        demo = _demo_openai_api()
    else:
        demo = _demo_latest_python()

    demo = deepcopy(demo)
    demo["question"] = q
    if base_answer:
        demo["original_answer"] = base_answer
        first_claim = safe_get(demo, ["claims", "claims"], [{}])
        if isinstance(first_claim, list) and first_claim and isinstance(first_claim[0], dict):
            first_claim[0]["claim_text"] = base_answer
        claim_report = safe_get(demo, ["report", "claim_report"], [])
        if isinstance(claim_report, list) and claim_report and isinstance(claim_report[0], dict):
            claim_report[0]["Claim Text"] = base_answer
    return demo


def build_dashboard_state(context: dict[str, Any] | None = None) -> dict[str, Any]:
    return dict(context or {})


def _claim_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "Claim ID": row.get("claim_id", row.get("Claim ID", "")),
        "Claim Text": row.get("claim_text", row.get("Claim Text", "")),
        "Claim Type": row.get("claim_type", row.get("Claim Type", "")),
        "Verification": row.get("verification_status", row.get("verification", row.get("Verification", ""))),
        "Risk": row.get("risk_level", row.get("risk", row.get("Risk", ""))),
        "Claim Value": row.get("claim_value", row.get("Claim Value", "")),
        "Evidence Value": row.get("evidence_value", row.get("Evidence Value", "")),
        "Correction": row.get("correction", row.get("requires_correction", row.get("Correction", ""))),
    }


def _evidence_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "Evidence ID": row.get("evidence_id", row.get("Evidence ID", "")),
        "Claim ID": row.get("claim_id", row.get("Claim ID", "")),
        "Title": row.get("title", row.get("Title", "")),
        "Publisher": row.get("publisher", row.get("Publisher", "Unknown")),
        "Source Type": row.get("source_type", row.get("type", row.get("Source Type", "other"))),
        "Freshness": row.get("freshness_label", row.get("freshness", row.get("Freshness", ""))),
        "Score": _as_float(row.get("combined_score", row.get("score", row.get("Score", 0.0)))),
        "URL": row.get("url", row.get("URL", "")),
    }


def _freshness_score_map(pipeline_output: dict[str, Any] | None) -> dict[tuple[str, str], dict[str, Any]]:
    score_map: dict[tuple[str, str], dict[str, Any]] = {}
    freshness_results = safe_get(pipeline_output, ["freshness", "freshness_results"], [])
    for result in freshness_results if isinstance(freshness_results, list) else []:
        if not isinstance(result, dict):
            continue
        claim_id = str(result.get("claim_id") or "")
        scores = result.get("evidence_scores", [])
        for score in scores if isinstance(scores, list) else []:
            if isinstance(score, dict):
                score_map[(claim_id, str(score.get("evidence_id") or ""))] = score
    return score_map


def _demo_latest_python() -> dict[str, Any]:
    return _demo_payload(
        question="What is the latest Python version?",
        original_answer="Python 3.10 is the latest stable version of Python.",
        corrected_answer=(
            "Python 3.10 is outdated as a latest-version answer. Based on the checked release evidence, "
            "Python 3.13.5 is the current stable Python release in this demo snapshot."
        ),
        badge="OUTDATED - CORRECTED",
        risk="medium_risk",
        trust=0.93,
        temporal_category="RECENT_ONLY",
        outdatedness="OUTDATED",
        verification_status="OUTDATED",
        correction_status="corrected",
        warning="Software release answers change over time; verify the release page before publishing.",
        claims=[
            _claim("C1", "Python 3.10 is the latest stable version of Python.", "software_version", "OUTDATED", "medium", "Python 3.10", "Python 3.13.5", True)
        ],
        evidence=[
            _evidence("E1", "C1", "Python Downloads", "Python Software Foundation", "official", "very_fresh", 0.98, "https://www.python.org/downloads/"),
            _evidence("E2", "C1", "Python 3.13 Release Schedule", "Python Developer's Guide", "official", "fresh", 0.91, "https://peps.python.org/pep-0719/"),
        ],
        thesis={
            "problem_observed": "The base answer presents an old software version as current.",
            "temporal_failure_type": "Outdated latest-version claim.",
            "evidence_quality": "Official release sources with high freshness.",
            "system_decision": "Correct the answer and show with caution.",
            "research_value": "Demonstrates temporal drift in software-version answers.",
        },
    )


def _demo_binary_search() -> dict[str, Any]:
    return _demo_payload(
        question="What is binary search?",
        original_answer="Binary search divides a sorted search space in half until the target is found or ruled out.",
        corrected_answer="Binary search is a static algorithmic concept: it repeatedly halves a sorted search space to find a target in O(log n) time.",
        badge="SAFE - STATIC KNOWLEDGE",
        risk="safe",
        trust=0.91,
        temporal_category="STATIC",
        outdatedness="NOT_OUTDATED",
        verification_status="SUPPORTED",
        correction_status="no_correction_needed",
        warning=None,
        claims=[
            _claim("C1", "Binary search requires a sorted search space.", "definition", "SUPPORTED", "low", "sorted search space", "sorted input requirement", False),
            _claim("C2", "Binary search runs in O(log n) time.", "algorithmic_complexity", "SUPPORTED", "low", "O(log n)", "O(log n)", False),
        ],
        evidence=[
            _evidence("E1", "C1", "Binary Search", "CP-Algorithms", "reference", "stable", 0.86, "https://cp-algorithms.com/num_methods/binary_search.html"),
            _evidence("E2", "C2", "Introduction to Algorithms: Search", "MIT OpenCourseWare", "academic", "stable", 0.84, "https://ocw.mit.edu/"),
        ],
        thesis={
            "problem_observed": "No temporal failure detected.",
            "temporal_failure_type": "Static knowledge.",
            "evidence_quality": "Stable educational and reference sources.",
            "system_decision": "Keep the answer with minor clarity improvement.",
            "research_value": "Shows the system avoids unnecessary correction for non-temporal claims.",
        },
    )


def _demo_visa_rule() -> dict[str, Any]:
    return _demo_payload(
        question="Is this visa rule still active?",
        original_answer="Yes, this visa rule is still active.",
        corrected_answer=(
            "I cannot safely confirm that this visa rule is still active from the available evidence. "
            "Visa and immigration rules are high-impact and can change without notice, so use the official government source before making a decision."
        ),
        badge="CRITICAL - VERIFY OFFICIAL SOURCE",
        risk="critical_risk",
        trust=0.24,
        temporal_category="RECENT_ONLY",
        outdatedness="UNVERIFIED_RISKY",
        verification_status="INSUFFICIENT_EVIDENCE",
        correction_status="unable_to_correct",
        warning="High-impact policy question: verify with an official immigration authority before action.",
        claims=[
            _claim("C1", "This visa rule is still active.", "law_or_policy", "INSUFFICIENT_EVIDENCE", "critical", "active", "not verified", True)
        ],
        evidence=[
            _evidence("E1", "C1", "Official Immigration Rule Index", "Government Portal", "official", "unknown", 0.42, "https://example.gov/immigration"),
            _evidence("E2", "C1", "Archived Visa Guidance", "Embassy Archive", "official_archive", "stale", 0.31, "https://example.gov/archive"),
        ],
        thesis={
            "problem_observed": "The base answer makes a current legal-status claim without verified current evidence.",
            "temporal_failure_type": "High-risk unverifiable policy claim.",
            "evidence_quality": "Insufficient and possibly stale evidence.",
            "system_decision": "Do not assert the answer; require official verification.",
            "research_value": "Demonstrates risk-aware handling for high-impact temporal claims.",
        },
    )


def _demo_world_cup() -> dict[str, Any]:
    return _demo_payload(
        question="Who won the 2014 FIFA World Cup?",
        original_answer="France won the 2014 FIFA World Cup.",
        corrected_answer="Germany won the 2014 FIFA World Cup, defeating Argentina 1-0 in the final.",
        badge="INCORRECT - CORRECTED",
        risk="low_risk",
        trust=0.96,
        temporal_category="HISTORICAL_STATIC",
        outdatedness="FACTUALLY_INCORRECT",
        verification_status="CONTRADICTED",
        correction_status="corrected",
        warning=None,
        claims=[
            _claim("C1", "France won the 2014 FIFA World Cup.", "historical_fact", "CONTRADICTED", "low", "France", "Germany", True)
        ],
        evidence=[
            _evidence("E1", "C1", "2014 FIFA World Cup Final", "FIFA", "official", "stable", 0.97, "https://www.fifa.com/"),
            _evidence("E2", "C1", "2014 FIFA World Cup", "Encyclopaedia Britannica", "reference", "stable", 0.89, "https://www.britannica.com/"),
        ],
        thesis={
            "problem_observed": "The answer is not outdated but contradicts stable historical evidence.",
            "temporal_failure_type": "Static factual contradiction.",
            "evidence_quality": "Official and reference sources agree.",
            "system_decision": "Correct the entity and mark as low temporal risk.",
            "research_value": "Shows the dashboard can separate temporal risk from factual correction.",
        },
    )


def _demo_openai_ceo() -> dict[str, Any]:
    return _demo_payload(
        question="Who is the CEO of OpenAI?",
        original_answer="Mira Murati is the CEO of OpenAI.",
        corrected_answer="Sam Altman is the CEO of OpenAI in this demo snapshot; leadership answers should be checked against OpenAI's current company information.",
        badge="OUTDATED - CORRECTED",
        risk="medium_risk",
        trust=0.88,
        temporal_category="RECENT_ONLY",
        outdatedness="OUTDATED",
        verification_status="OUTDATED",
        correction_status="corrected",
        warning="Company leadership can change; verify against the organization's current official page.",
        claims=[
            _claim("C1", "Mira Murati is the CEO of OpenAI.", "current_organization_role", "OUTDATED", "medium", "Mira Murati", "Sam Altman", True)
        ],
        evidence=[
            _evidence("E1", "C1", "OpenAI Leadership", "OpenAI", "official", "fresh", 0.9, "https://openai.com/"),
            _evidence("E2", "C1", "OpenAI Company Profile", "Company Registry Demo", "reference", "recent", 0.78, "https://example.com/openai-profile"),
        ],
        thesis={
            "problem_observed": "The base answer relies on stale leadership information.",
            "temporal_failure_type": "Current-role drift.",
            "evidence_quality": "Official organizational source preferred.",
            "system_decision": "Correct with a freshness caveat.",
            "research_value": "Demonstrates current-entity verification for LLM answers.",
        },
    )


def _demo_openai_api() -> dict[str, Any]:
    return _demo_payload(
        question="How do I use the OpenAI API in Python?",
        original_answer="Install openai and call openai.Completion.create with a text-davinci model.",
        corrected_answer=(
            "Use the current OpenAI Python SDK client pattern for new projects: create a client, call the Responses API or another current endpoint, "
            "and keep the API key in an environment variable rather than source code."
        ),
        badge="STALE API PATTERN - UPDATED",
        risk="medium_risk",
        trust=0.86,
        temporal_category="RECENT_ONLY",
        outdatedness="PARTIALLY_OUTDATED",
        verification_status="NEEDS_UPDATE",
        correction_status="corrected",
        warning="API SDK patterns change; verify against the current official OpenAI documentation before shipping code.",
        claims=[
            _claim("C1", "Use openai.Completion.create for new Python applications.", "api_usage", "OUTDATED", "medium", "Completion.create", "current SDK client pattern", True),
            _claim("C2", "Store API keys outside source code.", "security_practice", "SUPPORTED", "low", "environment variable", "environment variable", False),
        ],
        evidence=[
            _evidence("E1", "C1", "OpenAI API Documentation", "OpenAI", "official", "fresh", 0.92, "https://platform.openai.com/docs"),
            _evidence("E2", "C2", "OpenAI API Key Safety", "OpenAI", "official", "fresh", 0.88, "https://help.openai.com/"),
        ],
        thesis={
            "problem_observed": "The answer uses an older SDK pattern for a rapidly changing API.",
            "temporal_failure_type": "Developer documentation drift.",
            "evidence_quality": "Official docs are required for implementation guidance.",
            "system_decision": "Update the pattern and add a verification warning.",
            "research_value": "Shows practical temporal correction for developer-tool answers.",
        },
    )


def _demo_payload(
    question: str,
    original_answer: str,
    corrected_answer: str,
    badge: str,
    risk: str,
    trust: float,
    temporal_category: str,
    outdatedness: str,
    verification_status: str,
    correction_status: str,
    warning: str | None,
    claims: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    thesis: dict[str, str],
) -> dict[str, Any]:
    evidence_by_claim: dict[str, list[dict[str, Any]]] = {}
    freshness_by_claim: dict[str, list[dict[str, Any]]] = {}
    for item in evidence:
        claim_id = str(item["claim_id"])
        evidence_by_claim.setdefault(claim_id, []).append(
            {
                "evidence_id": item["evidence_id"],
                "title": item["title"],
                "url": item["url"],
                "publisher": item["publisher"],
                "source_type": item["source_type"],
                "evidence_summary": f"{item['publisher']} evidence for {claim_id}.",
            }
        )
        freshness_by_claim.setdefault(claim_id, []).append(
            {
                "evidence_id": item["evidence_id"],
                "freshness_label": item["freshness_label"],
                "combined_score": item["combined_score"],
            }
        )

    verification_results = [
        {
            "claim_id": claim["claim_id"],
            "verification_status": claim["verification_status"],
            "risk_level": claim["risk_level"],
            "claim_value": claim["claim_value"],
            "evidence_value": claim["evidence_value"],
            "requires_correction": claim["requires_correction"],
            "correction": "Update claim" if claim["requires_correction"] else "No correction needed",
        }
        for claim in claims
    ]
    safety = "safe_to_show" if risk == "safe" else ("needs_official_verification" if "critical" in risk else "show_with_caution")
    return {
        "run_id": "DEMO_RUN",
        "question": question,
        "original_answer": original_answer,
        "temporal_detection": {
            "temporal_category": temporal_category,
            "needs_fresh_evidence": temporal_category not in {"STATIC", "HISTORICAL_STATIC"},
            "reason": "Demo classification generated for frontend presentation.",
        },
        "claims": {"claims": claims, "total_claims": len(claims)},
        "evidence": {
            "evidence_results": [
                {"claim_id": claim_id, "evidence_items": items} for claim_id, items in evidence_by_claim.items()
            ],
            "total_evidence_items": len(evidence),
        },
        "freshness": {
            "overall_freshness_score": trust,
            "overall_temporal_risk": "low" if trust >= 0.85 else "high",
            "freshness_results": [
                {"claim_id": claim_id, "evidence_scores": scores} for claim_id, scores in freshness_by_claim.items()
            ],
        },
        "verification": {
            "overall_verification_status": verification_status,
            "verification_results": verification_results,
        },
        "outdatedness": {
            "outdatedness_status": outdatedness,
            "answer_temporal_risk": risk.replace("_risk", ""),
            "requires_correction": correction_status not in {"no_correction_needed"},
            "main_issue": thesis["problem_observed"],
        },
        "correction": {
            "corrected_answer": corrected_answer,
            "correction_status": correction_status,
            "changed_claim_ids": [claim["claim_id"] for claim in claims if claim["requires_correction"]],
            "unsupported_claim_ids": [claim["claim_id"] for claim in claims if claim["verification_status"] == "INSUFFICIENT_EVIDENCE"],
            "freshness_note": "Demo mode uses curated illustrative evidence for UI validation.",
            "uncertainty_note": warning,
            "safety_note": warning,
            "user_visible_explanation": "This demo result was generated locally without calling external services.",
        },
        "risk_label": {
            "dashboard_badge": badge,
            "final_risk_label": risk,
            "uncertainty_label": "low" if trust >= 0.85 else "high",
            "trust_score": trust,
            "temporal_safety_status": safety,
            "user_warning": warning,
        },
        "report": {
            "executive_summary": _executive_summary(outdatedness, correction_status, trust),
            "final_answer": corrected_answer,
            "claim_report": [_claim_row(claim) for claim in claims],
            "evidence_report": [_evidence_row(item) for item in evidence],
            "dashboard_summary": {
                "badge": badge,
                "risk_label": risk,
                "trust_score": trust,
                "temporal_safety_status": safety,
                "user_warning": warning,
            },
            "pipeline_summary": {
                "temporal_category": temporal_category,
                "needs_fresh_evidence": temporal_category not in {"STATIC", "HISTORICAL_STATIC"},
                "total_claims": len(claims),
                "verification_status": verification_status,
                "outdatedness_status": outdatedness,
                "correction_status": correction_status,
                "final_risk_label": risk,
            },
            "thesis_summary": thesis,
        },
        "pipeline_status": "success",
        "errors": [],
        "warnings": ["Demo mode uses curated mock evidence."] if warning else [],
    }


def _claim(
    claim_id: str,
    text: str,
    claim_type: str,
    verification: str,
    risk: str,
    claim_value: str,
    evidence_value: str,
    requires_correction: bool,
) -> dict[str, Any]:
    return {
        "claim_id": claim_id,
        "claim_text": text,
        "claim_type": claim_type,
        "verification_status": verification,
        "risk_level": risk,
        "claim_value": claim_value,
        "evidence_value": evidence_value,
        "requires_correction": requires_correction,
        "correction": "Update claim" if requires_correction else "No correction needed",
    }


def _evidence(
    evidence_id: str,
    claim_id: str,
    title: str,
    publisher: str,
    source_type: str,
    freshness_label: str,
    score: float,
    url: str,
) -> dict[str, Any]:
    return {
        "evidence_id": evidence_id,
        "claim_id": claim_id,
        "title": title,
        "publisher": publisher,
        "source_type": source_type,
        "freshness_label": freshness_label,
        "combined_score": score,
        "url": url,
    }


def _executive_summary(outdatedness: str, correction_status: str, trust: float) -> str:
    return (
        f"TemporalGuard classified the answer as {format_label(outdatedness).lower()} and "
        f"set correction handling to {format_label(correction_status).lower()} with a trust score of {trust:.2f}."
    )


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
