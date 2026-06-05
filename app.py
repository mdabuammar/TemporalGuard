"""TemporalGuard Streamlit dashboard."""

from __future__ import annotations

import json
from typing import Any

import requests
import streamlit as st

from temporalguard.frontend.streamlit_helpers import (
    build_demo_output,
    build_metric_cards,
    claims_to_table_rows,
    evidence_to_table_rows,
    format_badge,
    get_dashboard_summary,
    get_final_answer,
    get_pipeline_summary,
    inject_custom_css,
    risk_to_css_class,
    safe_get,
)


SAMPLE_QUESTIONS = [
    "What is the latest Python version?",
    "Who is the CEO of OpenAI?",
    "Who won the 2014 FIFA World Cup?",
    "What is binary search?",
    "Is this visa rule still active?",
    "How do I use the OpenAI API in Python?",
]


def main() -> None:
    st.set_page_config(
        page_title="TemporalGuard",
        page_icon="TG",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_custom_css()

    controls = render_sidebar()
    render_hero()
    question, base_answer = render_input_panel(controls)

    if "pipeline_output" not in st.session_state:
        st.session_state.pipeline_output = None

    if controls["run_clicked"]:
        if not question.strip():
            st.warning("Please enter a question before running TemporalGuard.")
        else:
            st.session_state.pipeline_output = run_dashboard_analysis(question, base_answer, controls)

    if st.session_state.pipeline_output:
        render_results(st.session_state.pipeline_output, controls["show_raw_json"], controls["show_debug_report"])
    else:
        st.markdown(
            "<div class='result-card muted-text'>Enter a question and run TemporalGuard to see the reliability report.</div>",
            unsafe_allow_html=True,
        )


def render_sidebar() -> dict[str, Any]:
    with st.sidebar:
        st.markdown("### TemporalGuard")
        st.caption("Time-aware LLM reliability dashboard")
        run_mode = st.radio(
            "Run mode",
            ["Demo/mock mode", "Local pipeline", "API backend"],
            index=0,
        )
        sample = st.selectbox("Sample question", SAMPLE_QUESTIONS, index=0)
        report_type = st.selectbox("Report type", ["dashboard", "technical", "thesis", "debug"], index=0)

        st.markdown("#### Advanced")
        use_base_answer = st.checkbox("Use provided base answer", value=True)
        show_raw_json = st.checkbox("Show raw JSON", value=False)
        show_debug_report = st.checkbox("Show debug report", value=False)
        api_url = st.text_input("API backend URL", value="http://127.0.0.1:8000")
        max_sources = st.slider("Max sources per claim", min_value=1, max_value=5, value=3)
        run_clicked = st.button("Run TemporalGuard", type="primary", use_container_width=True)

    return {
        "run_mode": run_mode,
        "sample_question": sample,
        "report_type": report_type,
        "use_base_answer": use_base_answer,
        "show_raw_json": show_raw_json,
        "show_debug_report": show_debug_report,
        "api_url": api_url.rstrip("/"),
        "max_sources_per_claim": max_sources,
        "run_clicked": run_clicked,
    }


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero-card">
          <div class="hero-title">TemporalGuard</div>
          <div class="hero-subtitle">
            Time-aware reliability framework for detecting and correcting outdated LLM responses.
          </div>
          <span class="feature-chip">Temporal Detection</span>
          <span class="feature-chip">Evidence Freshness</span>
          <span class="feature-chip">Claim Verification</span>
          <span class="feature-chip">Risk Labeling</span>
          <span class="feature-chip">Correction</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_input_panel(controls: dict[str, Any]) -> tuple[str, str]:
    st.markdown("<div class='section-title'>Analyze an LLM answer</div>", unsafe_allow_html=True)
    question = st.text_area("User question", value=controls["sample_question"], height=92)
    default_answer = _default_base_answer(question)
    base_answer = ""
    if controls["use_base_answer"]:
        base_answer = st.text_area("Optional base LLM answer", value=default_answer, height=118)
    elif controls["run_mode"] != "Demo/mock mode":
        st.info("No base answer was provided. Use demo mode or paste an LLM answer unless an LLM provider is configured.")
    return question, base_answer


def run_dashboard_analysis(question: str, base_answer: str, controls: dict[str, Any]) -> dict[str, Any]:
    mode = controls["run_mode"]
    if mode == "Demo/mock mode":
        return build_demo_output(question, base_answer or None)
    if mode == "Local pipeline":
        try:
            from temporalguard.pipeline.orchestrator import run_temporalguard_pipeline

            return run_temporalguard_pipeline(
                question=question,
                base_answer=base_answer or None,
                config={"max_sources_per_claim": controls["max_sources_per_claim"]},
                report_type=controls["report_type"],
            )
        except Exception as exc:  # pragma: no cover - UI boundary
            return _error_output(question, base_answer, f"Local pipeline failed: {exc}")
    return call_api_backend(question, base_answer, controls)


def call_api_backend(question: str, base_answer: str, controls: dict[str, Any]) -> dict[str, Any]:
    try:
        response = requests.post(
            f"{controls['api_url']}/analyze",
            json={
                "question": question,
                "base_answer": base_answer or None,
                "report_type": controls["report_type"],
            },
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict):
            return payload
        return _error_output(question, base_answer, "API returned a non-object response.")
    except Exception as exc:  # pragma: no cover - UI boundary
        return _error_output(question, base_answer, f"TemporalGuard could not reach the API backend: {exc}")


def render_results(output: dict[str, Any], show_raw_json: bool, show_debug_report: bool) -> None:
    summary = get_dashboard_summary(output)
    final_answer = get_final_answer(output)
    badge_class = risk_to_css_class(summary["risk_label"])

    st.markdown(
        f"""
        <div class="result-card">
          <div class="section-title">Corrected Answer</div>
          <span class="risk-badge {badge_class}">{format_badge(summary["badge"])}</span>
          <div class="result-answer" style="margin-top: 16px;">{_escape(final_answer)}</div>
          <div class="muted-text" style="margin-top: 12px;">
            Risk: {format_badge(summary["risk_label"])} · Trust: {summary["trust_score"]:.2f} · Safety: {summary["temporal_safety_status"]}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if summary["user_warning"]:
        st.markdown(f"<div class='warning-card'>{_escape(str(summary['user_warning']))}</div>", unsafe_allow_html=True)

    render_metric_cards(output)
    tabs = st.tabs(["Overview", "Claims", "Evidence", "Report", "Debug"])
    with tabs[0]:
        render_overview(output)
    with tabs[1]:
        render_claims(output)
    with tabs[2]:
        render_evidence(output)
    with tabs[3]:
        render_report(output)
    with tabs[4]:
        render_debug(output, show_raw_json or show_debug_report)


def render_metric_cards(output: dict[str, Any]) -> None:
    cards = build_metric_cards(output)
    cols = st.columns(3)
    for index, card in enumerate(cards):
        with cols[index % 3]:
            st.markdown(
                f"""
                <div class="metric-card">
                  <div class="metric-label">{_escape(card['label'])}</div>
                  <div class="metric-value">{_escape(card['value'])}</div>
                  <div class="metric-caption">{_escape(card['caption'])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_overview(output: dict[str, Any]) -> None:
    st.markdown("#### Original Answer")
    st.write(safe_get(output, ["original_answer"], ""))
    st.markdown("#### Corrected Answer")
    st.write(get_final_answer(output))
    st.markdown("#### Executive Summary")
    st.write(safe_get(output, ["report", "executive_summary"], "No report summary available."))
    issue = safe_get(output, ["outdatedness", "main_issue"])
    if issue:
        st.markdown("#### Main Issue")
        st.write(issue)
    warning = get_dashboard_summary(output).get("user_warning")
    if warning:
        st.warning(warning)


def render_claims(output: dict[str, Any]) -> None:
    rows = claims_to_table_rows(output)
    if not rows:
        st.info("No factual claims were extracted.")
        return
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_evidence(output: dict[str, Any]) -> None:
    rows = evidence_to_table_rows(output)
    if not rows:
        st.info("No evidence was retrieved or evidence retrieval was skipped.")
        return
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_report(output: dict[str, Any]) -> None:
    st.markdown("#### Executive Summary")
    st.write(safe_get(output, ["report", "executive_summary"], "No executive summary available."))
    thesis = safe_get(output, ["report", "thesis_summary"], {}) or {}
    st.markdown("#### Thesis Summary")
    for key, value in thesis.items():
        st.write(f"**{key.replace('_', ' ').title()}**: {value}")
    correction = safe_get(output, ["report", "correction_report"], {}) or safe_get(output, ["correction"], {}) or {}
    st.markdown("#### Correction Notes")
    for key in ("freshness_note", "uncertainty_note", "safety_note", "user_visible_explanation"):
        if correction.get(key):
            st.write(f"**{key.replace('_', ' ').title()}**: {correction[key]}")


def render_debug(output: dict[str, Any], show_raw_json: bool) -> None:
    st.write("Pipeline Status:", safe_get(output, ["pipeline_status"], "unknown"))
    st.write("Missing Sections:", safe_get(output, ["report", "debug_info", "missing_sections"], []))
    st.write("Warnings:", safe_get(output, ["warnings"], []))
    st.write("Errors:", safe_get(output, ["errors"], []))
    with st.expander("Raw JSON", expanded=show_raw_json):
        st.code(json.dumps(output, indent=2, default=str), language="json")


def _default_base_answer(question: str) -> str:
    lower = question.lower()
    if "binary search" in lower:
        return "Binary search divides a sorted search space in half."
    if "world cup" in lower:
        return "France won the 2014 FIFA World Cup."
    if "visa" in lower:
        return "Yes, this visa rule is still active."
    if "openai api" in lower:
        return "The OpenAI Python SDK lets developers call OpenAI models from Python applications."
    return "Python 3.10 is the latest stable version of Python."


def _error_output(question: str, base_answer: str, message: str) -> dict[str, Any]:
    return {
        "question": question,
        "original_answer": base_answer,
        "correction": {"corrected_answer": "TemporalGuard could not complete the analysis. Please check whether the pipeline or API backend is running."},
        "risk_label": {
            "dashboard_badge": "UNKNOWN",
            "final_risk_label": "unknown_risk",
            "trust_score": 0.0,
            "temporal_safety_status": "needs_more_evidence",
            "user_warning": message,
        },
        "report": {"executive_summary": message},
        "pipeline_status": "failed",
        "errors": [{"step": "frontend", "message": message}],
        "warnings": [],
    }


def _escape(value: str) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


if __name__ == "__main__":
    main()
