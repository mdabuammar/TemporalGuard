"""TemporalGuard premium Streamlit dashboard."""

from __future__ import annotations

import json
from typing import Any

import requests
import streamlit as st

from temporalguard.frontend.components import (
    render_footer,
    render_hero,
    render_metric_grid,
    render_result_card,
    render_status_card,
    render_warning_card,
)
from temporalguard.frontend.streamlit_helpers import (
    LLM_PROVIDER_OPTIONS,
    SAMPLE_QUESTIONS,
    build_analyze_payload,
    build_demo_output,
    build_metric_cards,
    claims_to_table_rows,
    evidence_to_table_rows,
    format_label,
    get_dashboard_summary,
    get_final_answer,
    normalize_llm_provider,
    safe_get,
)
from temporalguard.frontend.styles import inject_premium_css


def main() -> None:
    st.set_page_config(
        page_title="TemporalGuard",
        page_icon="TG",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_premium_css()

    controls = render_sidebar()
    st.markdown("<div class='tg-app-shell'>", unsafe_allow_html=True)
    render_hero()
    render_status_card(
        {
            "mode": controls["run_mode"],
            "report_type": controls["report_type"],
            "status": "ready",
        }
    )
    question, base_answer = render_input_panel(controls)

    if "pipeline_output" not in st.session_state:
        st.session_state.pipeline_output = None

    if controls["run_clicked"]:
        if not question.strip():
            render_warning_card("Enter a question before running TemporalGuard.")
        else:
            with st.spinner("TemporalGuard is checking temporal reliability..."):
                st.session_state.pipeline_output = run_dashboard_analysis(question, base_answer, controls)

    if st.session_state.pipeline_output:
        render_results(
            st.session_state.pipeline_output,
            show_raw_json=controls["show_raw_json"],
            debug_enabled=controls["show_debug_report"],
        )
    else:
        st.markdown(
            """
            <div class="tg-card">
              <div class="tg-section-title">Awaiting Analysis</div>
              <div class="tg-muted">
                Select a sample or enter a custom question, then run TemporalGuard to generate a reliability report.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_footer()
    st.markdown("</div>", unsafe_allow_html=True)


def render_sidebar() -> dict[str, Any]:
    with st.sidebar:
        st.markdown(
            """
            <div class="tg-card" style="padding: 16px; margin-bottom: 14px;">
              <div class="tg-section-title">TemporalGuard</div>
              <div style="font-size: 20px; font-weight: 830; color: #f8fafc;">Control Panel</div>
              <div class="tg-muted" style="font-size: 12px; margin-top: 8px;">
                Time-aware LLM reliability checks
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        run_mode = st.radio(
            "Run mode",
            ["Demo/mock mode", "Local pipeline", "API backend"],
            index=0,
        )
        sample = st.selectbox("Sample question", SAMPLE_QUESTIONS, index=0)
        report_type = st.selectbox("Report type", ["dashboard", "technical", "thesis", "debug"], index=0)

        st.markdown("<div class='tg-section-title'>Advanced Options</div>", unsafe_allow_html=True)
        use_base_answer = st.checkbox("Use provided base answer", value=True)
        llm_provider_label = st.selectbox("LLM provider", list(LLM_PROVIDER_OPTIONS.keys()), index=0)
        model_name = st.text_input("Optional model name", value="openrouter/free")
        st.warning("API keys are read from environment variables only.")
        st.caption("OpenRouter API key is read from OPENROUTER_API_KEY in environment variables.")
        show_raw_json = st.checkbox("Expand raw JSON by default", value=False)
        show_debug_report = st.checkbox("Show debug details", value=False)
        api_url = st.text_input("API backend URL", value="http://127.0.0.1:8000")
        max_sources = st.slider("Max sources per claim", min_value=1, max_value=5, value=3)
        run_clicked = st.button("Run TemporalGuard", type="primary", width="stretch")

        st.markdown(
            """
            <div class="tg-card" style="padding: 14px; margin-top: 16px;">
              <div class="tg-section-title">Project Status</div>
              <span class="tg-badge tg-badge-safe">DEMO ONLINE</span>
              <div class="tg-muted" style="font-size: 12px; margin-top: 10px;">
                Backend modes are optional and use the existing pipeline/API boundaries.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return {
        "run_mode": run_mode,
        "sample_question": sample,
        "report_type": report_type,
        "use_base_answer": use_base_answer,
        "llm_provider": normalize_llm_provider(llm_provider_label),
        "model_name": model_name.strip(),
        "show_raw_json": show_raw_json,
        "show_debug_report": show_debug_report,
        "api_url": api_url.rstrip("/"),
        "max_sources_per_claim": max_sources,
        "run_clicked": run_clicked,
    }


def render_input_panel(controls: dict[str, Any]) -> tuple[str, str]:
    st.markdown(
        """
        <div class="tg-card">
          <div class="tg-section-title">Question Analysis</div>
          <div class="tg-muted">Run a temporal reliability check against a question and optional base LLM answer.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    question = st.text_area("Question input", value=controls["sample_question"], height=92)
    default_answer = _default_base_answer(question)
    base_answer = ""
    if controls["use_base_answer"]:
        base_answer = st.text_area("Optional base answer", value=default_answer, height=120)
    elif controls["run_mode"] != "Demo/mock mode":
        render_warning_card("No base answer was provided. Local/API modes may need an LLM provider or supplied answer.")
    return question, base_answer


def run_dashboard_analysis(question: str, base_answer: str, controls: dict[str, Any]) -> dict[str, Any]:
    mode = controls["run_mode"]
    if mode == "Demo/mock mode":
        return build_demo_output(question, base_answer or None)
    if mode == "Local pipeline":
        try:
            from temporalguard.llm.providers import create_llm_provider
            from temporalguard.pipeline.orchestrator import run_temporalguard_pipeline

            llm_provider = None
            if not base_answer:
                llm_provider = create_llm_provider(
                    controls.get("llm_provider"),
                    model_name=controls.get("model_name") or None,
                    require_configured=True,
                )
            return run_temporalguard_pipeline(
                question=question,
                base_answer=base_answer or None,
                llm_provider=llm_provider,
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
            json=build_analyze_payload(
                question=question,
                base_answer=base_answer or None,
                report_type=controls["report_type"],
                llm_provider=controls.get("llm_provider"),
                model_name=controls.get("model_name") or None,
            ),
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict):
            return payload
        return _error_output(question, base_answer, "API returned a non-object response.")
    except Exception as exc:  # pragma: no cover - UI boundary
        return _error_output(question, base_answer, f"TemporalGuard could not reach the API backend: {exc}")


def render_results(output: dict[str, Any], show_raw_json: bool, debug_enabled: bool) -> None:
    summary = get_dashboard_summary(output)
    render_result_card(get_final_answer(output), summary)
    render_metric_grid(build_metric_cards(output))

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
        render_debug(output, show_raw_json=show_raw_json, debug_enabled=debug_enabled)


def render_overview(output: dict[str, Any]) -> None:
    warning = get_dashboard_summary(output).get("user_warning")
    st.markdown(
        f"""
        <div class="tg-split-grid">
          <div class="tg-card">
            <div class="tg-section-title">Original Answer</div>
            <div class="tg-muted" style="line-height: 1.65;">{_escape(safe_get(output, ["original_answer"], "No original answer provided."))}</div>
          </div>
          <div class="tg-card">
            <div class="tg-section-title">Corrected Answer</div>
            <div class="tg-muted" style="line-height: 1.65;">{_escape(get_final_answer(output))}</div>
          </div>
        </div>
        <div class="tg-card">
          <div class="tg-section-title">Executive Summary</div>
          <div class="tg-muted" style="line-height: 1.65;">{_escape(safe_get(output, ["report", "executive_summary"], "No report summary available."))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if warning:
        render_warning_card(str(warning))


def render_claims(output: dict[str, Any]) -> None:
    rows = claims_to_table_rows(output)
    st.markdown("<div class='tg-section-title'>Claim-Level Verification</div>", unsafe_allow_html=True)
    if not rows:
        st.markdown("<div class='tg-card tg-muted'>No factual claims were extracted.</div>", unsafe_allow_html=True)
        return
    st.dataframe(rows, width="stretch", hide_index=True)


def render_evidence(output: dict[str, Any]) -> None:
    rows = evidence_to_table_rows(output)
    st.markdown("<div class='tg-section-title'>Fresh Evidence</div>", unsafe_allow_html=True)
    if not rows:
        st.markdown("<div class='tg-card tg-muted'>No evidence was retrieved or evidence retrieval was skipped.</div>", unsafe_allow_html=True)
        return
    st.dataframe(rows, width="stretch", hide_index=True)


def render_report(output: dict[str, Any]) -> None:
    thesis = safe_get(output, ["report", "thesis_summary"], {}) or {}
    sections = [
        ("Executive Summary", safe_get(output, ["report", "executive_summary"], "No executive summary available.")),
        ("Problem Observed", thesis.get("problem_observed", "Not reported.")),
        ("Temporal Failure Type", thesis.get("temporal_failure_type", "Not reported.")),
        ("Evidence Quality", thesis.get("evidence_quality", "Not reported.")),
        ("System Decision", thesis.get("system_decision", "Not reported.")),
        ("Research Value", thesis.get("research_value", "Not reported.")),
    ]
    html = ["<div class='tg-split-grid'>"]
    for title, value in sections:
        html.append(
            f"""
            <div class="tg-card">
              <div class="tg-section-title">{_escape(title)}</div>
              <div class="tg-muted" style="line-height: 1.62;">{_escape(value)}</div>
            </div>
            """
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def render_debug(output: dict[str, Any], show_raw_json: bool, debug_enabled: bool) -> None:
    status = safe_get(output, ["pipeline_status"], "unknown")
    warnings = safe_get(output, ["warnings"], [])
    errors = safe_get(output, ["errors"], [])
    st.markdown(
        f"""
        <div class="tg-debug-box">
          <div class="tg-section-title">Pipeline Status</div>
          <div>Status: {_escape(format_label(status))}</div>
          <div style="margin-top: 8px;">Warnings: {_escape(warnings)}</div>
          <div style="margin-top: 8px;">Errors: {_escape(errors)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if debug_enabled:
        st.write("Missing Sections:", safe_get(output, ["report", "debug_info", "missing_sections"], []))
    with st.expander("Raw JSON", expanded=show_raw_json):
        st.code(json.dumps(output, indent=2, default=str), language="json")


def _default_base_answer(question: str) -> str:
    lower = question.lower()
    if "binary search" in lower:
        return "Binary search divides a sorted search space in half."
    if "visa" in lower:
        return "Yes, this visa rule is still active."
    if "world cup" in lower or "2014" in lower:
        return "France won the 2014 FIFA World Cup."
    if "ceo of openai" in lower or ("openai" in lower and "ceo" in lower):
        return "Mira Murati is the CEO of OpenAI."
    if "openai api" in lower:
        return "Install openai and call openai.Completion.create with a text-davinci model."
    return "Python 3.10 is the latest stable version of Python."


def _error_output(question: str, base_answer: str, message: str) -> dict[str, Any]:
    return {
        "question": question,
        "original_answer": base_answer,
        "correction": {
            "corrected_answer": (
                "TemporalGuard could not complete the analysis. Check whether the pipeline or API backend is running, "
                "then retry the request."
            ),
            "correction_status": "failed",
            "safety_note": message,
        },
        "risk_label": {
            "dashboard_badge": "ANALYSIS UNAVAILABLE",
            "final_risk_label": "unknown_risk",
            "trust_score": 0.0,
            "temporal_safety_status": "needs_more_evidence",
            "user_warning": "TemporalGuard could not complete the analysis. Check whether the pipeline or API backend is running.",
        },
        "report": {
            "executive_summary": "The frontend caught an execution error and converted it into a safe dashboard result.",
            "thesis_summary": {
                "problem_observed": "Analysis did not complete.",
                "temporal_failure_type": "Unavailable due to runtime or backend error.",
                "evidence_quality": "No evidence available.",
                "system_decision": "Show a controlled error card and hide technical details outside Debug.",
                "research_value": "Keeps the demonstration UI stable during backend failures.",
            },
        },
        "pipeline_status": "failed",
        "errors": [{"step": "frontend", "message": message}],
        "warnings": [],
    }


def _escape(value: Any) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


if __name__ == "__main__":
    main()
