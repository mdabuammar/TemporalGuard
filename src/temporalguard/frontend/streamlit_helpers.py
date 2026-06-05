"""Helper utilities for the TemporalGuard Streamlit dashboard."""

from __future__ import annotations

from typing import Any


def safe_get(data: dict[str, Any] | None, path: list[str], default: Any = None) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def risk_to_css_class(risk_label: str | None) -> str:
    label = str(risk_label or "").lower()
    if label in {"safe"}:
        return "badge-safe"
    if "low" in label:
        return "badge-low"
    if "medium" in label:
        return "badge-medium"
    if "critical" in label:
        return "badge-critical"
    if "high" in label:
        return "badge-high"
    return "badge-unknown"


def format_badge(label: str | None) -> str:
    text = str(label or "UNKNOWN").replace("_", " ").upper()
    return text if text.strip() else "UNKNOWN"


def get_final_answer(pipeline_output: dict[str, Any] | None) -> str:
    return str(
        safe_get(pipeline_output, ["correction", "corrected_answer"])
        or safe_get(pipeline_output, ["report", "final_answer"])
        or safe_get(pipeline_output, ["original_answer"])
        or ""
    )


def get_dashboard_summary(pipeline_output: dict[str, Any] | None) -> dict[str, Any]:
    risk_label = safe_get(pipeline_output, ["risk_label"], {}) or {}
    report_summary = safe_get(pipeline_output, ["report", "dashboard_summary"], {}) or {}
    return {
        "badge": risk_label.get("dashboard_badge") or report_summary.get("badge") or "UNKNOWN",
        "risk_label": risk_label.get("final_risk_label") or report_summary.get("risk_label") or "unknown_risk",
        "uncertainty_label": risk_label.get("uncertainty_label") or report_summary.get("uncertainty_label") or "unknown",
        "trust_score": _as_float(risk_label.get("trust_score", report_summary.get("trust_score", 0.0))),
        "temporal_safety_status": risk_label.get("temporal_safety_status")
        or report_summary.get("temporal_safety_status")
        or "needs_more_evidence",
        "user_warning": risk_label.get("user_warning") or report_summary.get("user_warning"),
    }


def get_pipeline_summary(pipeline_output: dict[str, Any] | None) -> dict[str, Any]:
    report_summary = safe_get(pipeline_output, ["report", "pipeline_summary"], {}) or {}
    return {
        "temporal_category": safe_get(pipeline_output, ["temporal_detection", "temporal_category"])
        or report_summary.get("temporal_category")
        or "UNKNOWN",
        "needs_fresh_evidence": bool(
            safe_get(pipeline_output, ["temporal_detection", "needs_fresh_evidence"], report_summary.get("needs_fresh_evidence", False))
        ),
        "total_claims": int(safe_get(pipeline_output, ["claims", "total_claims"], report_summary.get("total_claims", 0)) or 0),
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
    trust = get_dashboard_summary(pipeline_output)["trust_score"]
    return [
        {
            "label": "Temporal Category",
            "value": str(summary["temporal_category"]),
            "caption": "Fresh evidence required" if summary["needs_fresh_evidence"] else "Stable or optional",
        },
        {
            "label": "Outdatedness",
            "value": str(summary["outdatedness_status"]),
            "caption": "Answer-level decision",
        },
        {
            "label": "Verification",
            "value": str(summary["verification_status"]),
            "caption": "Claim-level status",
        },
        {
            "label": "Correction",
            "value": str(summary["correction_status"]),
            "caption": "Final answer handling",
        },
        {
            "label": "Trust Score",
            "value": f"{trust:.2f}",
            "caption": "Final confidence signal",
        },
        {
            "label": "Freshness Score",
            "value": f"{summary['freshness_score']:.2f}",
            "caption": "Evidence timing quality",
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
        if isinstance(item, dict) and item.get("claim_id")
    }
    rows: list[dict[str, Any]] = []
    for claim in claims if isinstance(claims, list) else []:
        if not isinstance(claim, dict):
            continue
        ver = verification.get(str(claim.get("claim_id")), {})
        rows.append(_claim_row({**claim, **ver}))
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
            if not isinstance(item, dict):
                continue
            score = score_map.get((claim_id, str(item.get("evidence_id") or "")), {})
            rows.append(_evidence_row({**item, **score, "claim_id": claim_id}))
    return rows


def build_demo_output(question: str, base_answer: str | None = None) -> dict[str, Any]:
    q = question.strip() or "What is the latest Python version?"
    lower = q.lower()
    if "binary search" in lower:
        original = base_answer or "Binary search divides a sorted search space in half."
        corrected = original
        badge = "SAFE"
        risk = "safe"
        temporal_category = "STATIC"
        outdatedness = "NOT_OUTDATED"
        verification_status = "SUPPORTED"
        correction_status = "no_correction_needed"
        trust = 0.91
        warning = None
        claims = [
            {
                "claim_id": "C1",
                "claim_text": "Binary search divides a sorted search space in half.",
                "claim_type": "definition",
            }
        ]
    elif "visa" in lower:
        original = base_answer or "Yes, this visa rule is still active."
        corrected = (
            "I could not safely verify whether this visa rule is still active from the available evidence. "
            "Because visa rules can change and affect real decisions, check the official government source before action."
        )
        badge = "CRITICAL - VERIFY OFFICIAL SOURCE"
        risk = "critical_risk"
        temporal_category = "RECENT_ONLY"
        outdatedness = "UNVERIFIED_RISKY"
        verification_status = "INSUFFICIENT_EVIDENCE"
        correction_status = "unable_to_correct"
        trust = 0.25
        warning = "This is a high-risk visa or policy-related question. Verify with an official source before action."
        claims = [{"claim_id": "C1", "claim_text": "This visa rule is still active.", "claim_type": "law_or_policy"}]
    else:
        original = base_answer or "Python 3.10 is the latest stable version of Python."
        corrected = (
            "Python 3.10 is not the latest stable Python version. "
            "Based on the checked evidence, Python 3.13.5 is listed as the latest release."
        )
        badge = "OUTDATED - CORRECTED"
        risk = "medium_risk"
        temporal_category = "RECENT_ONLY"
        outdatedness = "OUTDATED"
        verification_status = "OUTDATED"
        correction_status = "corrected"
        trust = 0.93
        warning = "This answer was updated using checked evidence, but software versions can change again."
        claims = [
            {
                "claim_id": "C1",
                "claim_text": "Python 3.10 is the latest stable version of Python.",
                "claim_type": "software_version",
            }
        ]

    return _demo_payload(
        question=q,
        original_answer=original,
        corrected_answer=corrected,
        badge=badge,
        risk=risk,
        trust=trust,
        warning=warning,
        temporal_category=temporal_category,
        outdatedness=outdatedness,
        verification_status=verification_status,
        correction_status=correction_status,
        claims=claims,
    )


def build_dashboard_state(context: dict[str, Any] | None = None) -> dict[str, Any]:
    return dict(context or {})


def inject_custom_css() -> None:
    import streamlit as st

    st.markdown(
        """
        <style>
        :root {
          --tg-bg: #f8fafc;
          --tg-card: #ffffff;
          --tg-border: #e5e7eb;
          --tg-text: #0f172a;
          --tg-muted: #64748b;
          --tg-primary: #2563eb;
          --tg-success: #16a34a;
          --tg-warning: #d97706;
          --tg-danger: #dc2626;
          --tg-critical: #991b1b;
        }
        .stApp { background: var(--tg-bg); color: var(--tg-text); }
        section[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid var(--tg-border); }
        .hero-card {
          background: linear-gradient(135deg, #ffffff 0%, #eef6ff 100%);
          border: 1px solid var(--tg-border);
          border-radius: 18px;
          padding: 32px 34px;
          box-shadow: 0 18px 45px rgba(15, 23, 42, 0.07);
          margin-bottom: 22px;
        }
        .hero-title { font-size: 44px; line-height: 1; font-weight: 800; letter-spacing: 0; margin: 0 0 12px; }
        .hero-subtitle { color: var(--tg-muted); font-size: 17px; max-width: 760px; margin-bottom: 18px; }
        .feature-chip {
          display: inline-block; padding: 7px 11px; margin: 0 8px 8px 0; border-radius: 999px;
          background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; font-size: 13px; font-weight: 650;
        }
        .result-card, .input-card, .code-card, .warning-card {
          background: var(--tg-card);
          border: 1px solid var(--tg-border);
          border-radius: 14px;
          padding: 22px;
          box-shadow: 0 10px 28px rgba(15, 23, 42, 0.055);
          margin-bottom: 18px;
        }
        .result-answer { font-size: 18px; line-height: 1.65; color: var(--tg-text); }
        .metric-card {
          background: #ffffff; border: 1px solid var(--tg-border); border-radius: 14px; padding: 18px;
          min-height: 118px; box-shadow: 0 8px 22px rgba(15, 23, 42, 0.045);
        }
        .metric-label { color: var(--tg-muted); font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; }
        .metric-value { color: var(--tg-text); font-size: 22px; font-weight: 800; margin-top: 8px; overflow-wrap: anywhere; }
        .metric-caption { color: var(--tg-muted); font-size: 13px; margin-top: 8px; }
        .risk-badge {
          display: inline-flex; align-items: center; border-radius: 999px; padding: 8px 12px;
          font-size: 12px; font-weight: 800; letter-spacing: .035em; border: 1px solid transparent;
        }
        .badge-safe { background: #dcfce7; color: #166534; border-color: #bbf7d0; }
        .badge-low { background: #ecfdf5; color: #047857; border-color: #a7f3d0; }
        .badge-medium { background: #fffbeb; color: #92400e; border-color: #fde68a; }
        .badge-high { background: #fff7ed; color: #c2410c; border-color: #fed7aa; }
        .badge-critical { background: #fef2f2; color: #991b1b; border-color: #fecaca; }
        .badge-unknown { background: #f1f5f9; color: #475569; border-color: #cbd5e1; }
        .section-title { font-size: 19px; font-weight: 800; margin: 4px 0 12px; }
        .muted-text { color: var(--tg-muted); font-size: 14px; }
        .warning-card { border-color: #fed7aa; background: #fff7ed; color: #9a3412; }
        div[data-testid="stDataFrame"] { border: 1px solid var(--tg-border); border-radius: 12px; overflow: hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _claim_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "Claim ID": row.get("claim_id", ""),
        "Claim Text": row.get("claim_text", ""),
        "Claim Type": row.get("claim_type"),
        "Verification Status": row.get("verification_status"),
        "Risk Level": row.get("risk_level"),
        "Claim Value": row.get("claim_value"),
        "Evidence Value": row.get("evidence_value"),
        "Requires Correction": bool(row.get("requires_correction", False)),
    }


def _evidence_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "Evidence ID": row.get("evidence_id", ""),
        "Claim ID": row.get("claim_id", ""),
        "Title": row.get("title", ""),
        "Publisher": row.get("publisher", "unknown"),
        "Source Type": row.get("source_type", "other"),
        "Freshness Label": row.get("freshness_label"),
        "Combined Score": _as_float(row.get("combined_score", 0.0)),
        "URL": row.get("url", ""),
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


def _demo_payload(
    question: str,
    original_answer: str,
    corrected_answer: str,
    badge: str,
    risk: str,
    trust: float,
    warning: str | None,
    temporal_category: str,
    outdatedness: str,
    verification_status: str,
    correction_status: str,
    claims: list[dict[str, Any]],
) -> dict[str, Any]:
    evidence_items = [] if outdatedness == "UNVERIFIED_RISKY" else [
        {
            "evidence_id": "E1",
            "title": "Demo evidence source",
            "url": "https://example.com/demo-source",
            "publisher": "TemporalGuard Demo",
            "source_type": "official" if risk != "safe" else "academic",
            "evidence_summary": "Demo evidence used to illustrate the dashboard layout.",
        }
    ]
    return {
        "run_id": "DEMO_RUN",
        "question": question,
        "original_answer": original_answer,
        "temporal_detection": {"temporal_category": temporal_category, "needs_fresh_evidence": temporal_category != "STATIC"},
        "claims": {"claims": claims, "total_claims": len(claims)},
        "evidence": {"evidence_results": [{"claim_id": "C1", "evidence_items": evidence_items}], "total_evidence_items": len(evidence_items)},
        "freshness": {"overall_freshness_score": trust, "overall_temporal_risk": "low" if risk == "safe" else "medium"},
        "verification": {"overall_verification_status": verification_status, "verification_results": [{"claim_id": "C1", "verification_status": verification_status, "risk_level": "low" if risk == "safe" else "high", "requires_correction": correction_status == "corrected", "claim_value": "Python 3.10" if correction_status == "corrected" else None, "evidence_value": "Python 3.13.5" if correction_status == "corrected" else None}]},
        "outdatedness": {"outdatedness_status": outdatedness, "answer_temporal_risk": risk.replace("_risk", ""), "requires_correction": correction_status != "no_correction_needed"},
        "correction": {"corrected_answer": corrected_answer, "correction_status": correction_status, "changed_claim_ids": ["C1"] if correction_status == "corrected" else [], "unsupported_claim_ids": ["C1"] if correction_status == "unable_to_correct" else [], "freshness_note": "Demo output uses fixed illustrative evidence.", "uncertainty_note": warning if correction_status == "unable_to_correct" else None, "safety_note": warning if "visa" in question.lower() else None, "user_visible_explanation": "Demo result generated without calling external services."},
        "risk_label": {"dashboard_badge": badge, "final_risk_label": risk, "uncertainty_label": "low" if trust >= 0.75 else "very_high", "trust_score": trust, "temporal_safety_status": "safe_to_show" if risk == "safe" else "show_with_caution", "user_warning": warning},
        "report": {"executive_summary": "Demo mode shows a realistic TemporalGuard result without requiring a backend.", "final_answer": corrected_answer, "claim_report": [], "evidence_report": [], "dashboard_summary": {"badge": badge, "risk_label": risk, "trust_score": trust, "temporal_safety_status": "safe_to_show" if risk == "safe" else "show_with_caution", "user_warning": warning}, "thesis_summary": {"problem_observed": "Demo output for presentation.", "temporal_failure_type": "demo", "evidence_quality": "Illustrative only.", "system_decision": f"Demo status: {outdatedness}.", "research_value": "Useful for showing the dashboard before backend setup."}},
        "pipeline_status": "success",
        "errors": [],
        "warnings": [],
    }


def _as_float(value: Any) -> float:
    return float(value) if isinstance(value, int | float) else 0.0
