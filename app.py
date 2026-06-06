"""TemporalGuard premium Streamlit dashboard."""

from __future__ import annotations

import json
from typing import Any

import requests
import streamlit as st

from temporalguard.frontend.components import (
    render_footer,
    render_hero,
    render_result_card,
    render_warning_card,
)
from temporalguard.frontend.streamlit_helpers import (
    LLM_PROVIDER_OPTIONS,
    SAMPLE_QUESTIONS,
    SEARCH_PROVIDER_OPTIONS,
    build_analyze_payload,
    build_demo_output,
    build_metric_cards,
    claims_to_table_rows,
    evidence_to_table_rows,
    format_label,
    get_dashboard_summary,
    get_final_answer,
    normalize_llm_provider,
    normalize_search_provider,
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

    question, base_answer, run_clicked = render_input_panel(controls)
    render_accessible_settings_summary(controls)

    if "pipeline_output" not in st.session_state:
        st.session_state.pipeline_output = None

    if run_clicked:
        if not question.strip():
            render_warning_card("Enter a question before running TemporalGuard.")
        else:
            with st.spinner("TemporalGuard is checking temporal reliability..."):
                st.session_state.pipeline_output = run_dashboard_analysis(question, base_answer, controls)

    if st.session_state.pipeline_output:
        render_results(
            st.session_state.pipeline_output,
            controls=controls,
            show_raw_json=controls["show_raw_json"],
            debug_enabled=controls["show_debug_report"],
        )
    else:
        render_empty_state()

    render_footer()
    st.markdown("</div>", unsafe_allow_html=True)


def render_sidebar() -> dict[str, Any]:
    with st.sidebar:
        st.markdown(
            """
            <div class="tg-sidebar-brand">
              <div class="tg-brand-mark">TG</div>
              <div class="tg-sidebar-title">TemporalGuard</div>
              <div class="tg-muted">
                AI answer reliability controls.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<div class='tg-sidebar-section'>Mode</div>", unsafe_allow_html=True)
        run_mode = st.radio(
            "Mode",
            ["Demo Mode", "Local Pipeline", "Backend + Model API"],
            index=0,
            label_visibility="collapsed",
        )
        if run_mode == "Backend + Model API":
            st.info("Turn off provided base answer if you want OpenRouter to generate the answer.")

        st.markdown("<div class='tg-sidebar-section'>Answer Source</div>", unsafe_allow_html=True)
        default_use_answer = run_mode != "Backend + Model API"
        if st.session_state.get("tg_last_mode") != run_mode:
            st.session_state.tg_use_own_answer = default_use_answer
            st.session_state.tg_last_mode = run_mode
        if "tg_use_own_answer" not in st.session_state:
            st.session_state.tg_use_own_answer = default_use_answer
        use_base_answer = st.toggle("Use my own answer", key="tg_use_own_answer")

        st.markdown("<div class='tg-sidebar-section'>LLM Provider</div>", unsafe_allow_html=True)
        llm_provider_label = st.selectbox("Model provider", list(LLM_PROVIDER_OPTIONS.keys()), index=0)
        st.markdown("<div class='tg-sidebar-section'>Model</div>", unsafe_allow_html=True)
        model_name = st.text_input("Model name", value="openrouter/free")
        search_provider_label = "None"
        if run_mode == "Backend + Model API":
            st.markdown("<div class='tg-sidebar-section'>Evidence Provider</div>", unsafe_allow_html=True)
            search_provider_label = st.selectbox("Evidence provider", list(SEARCH_PROVIDER_OPTIONS.keys()), index=0)
            st.caption("Evidence provider is used to verify fresh/current claims.")
        if run_mode == "Backend + Model API" and llm_provider_label == "OpenRouter":
            st.info("To test OpenRouter: turn off Use my own answer, keep model as openrouter/free, and run a question.")

        with st.expander("Advanced settings", expanded=False):
            api_url = "http://127.0.0.1:8000"
            if run_mode == "Backend + Model API":
                api_url = st.text_input(
                    "API backend URL",
                    value=api_url,
                    help="Used only when connecting the frontend to FastAPI.",
                )
            sample = st.selectbox("Sample question", SAMPLE_QUESTIONS, index=0)
            report_type = st.selectbox("Report format", ["dashboard", "technical", "debug"], index=0)
            max_sources = st.slider("Max sources per claim", min_value=1, max_value=5, value=3)
            show_raw_json = st.checkbox("Show raw JSON by default", value=False)
            show_debug_report = st.checkbox("Show debug details", value=False)

        sidebar_run_clicked = st.button("Run TemporalGuard", type="primary", width="stretch", key="sidebar_run")
        st.markdown("<div class='tg-sidebar-section'>Status</div>", unsafe_allow_html=True)
        st.success("Ready")
        st.caption("API keys are read from environment variables only.")

    return {
        "run_mode": run_mode,
        "sample_question": sample,
        "report_type": report_type,
        "use_base_answer": use_base_answer,
        "llm_provider": normalize_llm_provider(llm_provider_label),
        "model_name": model_name.strip(),
        "search_provider": normalize_search_provider(search_provider_label),
        "search_provider_label": search_provider_label,
        "show_raw_json": show_raw_json,
        "show_debug_report": show_debug_report,
        "api_url": api_url.rstrip("/"),
        "max_sources_per_claim": max_sources,
        "llm_provider_label": llm_provider_label,
        "sidebar_run_clicked": sidebar_run_clicked,
    }


def render_input_panel(controls: dict[str, Any]) -> tuple[str, str, bool]:
    st.markdown(
        """
        <div class="tg-workspace-card">
          <div class="tg-section-title">Ask a question</div>
          <div class="tg-input-title">What answer should TemporalGuard verify?</div>
          <div class="tg-muted">Enter a time-sensitive question, then provide an answer or let your selected model generate one.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    question = st.text_area("Ask a question", value=controls["sample_question"], height=105)
    default_answer = _default_base_answer(question)
    base_answer = ""
    use_base_answer = bool(controls.get("use_base_answer"))
    if use_base_answer:
        base_answer = st.text_area("Answer to check", value=default_answer, height=135)
        if controls["run_mode"] == "Backend + Model API":
            st.info("The model API will not be called because you provided an answer.")
        if controls["run_mode"] == "Backend + Model API" and controls.get("llm_provider_label") == "OpenRouter":
            st.warning("OpenRouter will not be called because Use my own answer is enabled.")
    elif controls["run_mode"] != "Demo Mode":
        st.info("The selected model will generate the first answer before TemporalGuard checks it.")
    if controls["run_mode"] == "Backend + Model API" and controls.get("search_provider") == "none":
        st.info("No evidence provider selected. Fresh/current claims may receive low trust.")
    run_clicked = st.button("Run TemporalGuard", type="primary", width="stretch", key="main_run")
    return question, base_answer, bool(run_clicked or controls.get("sidebar_run_clicked"))


def render_run_summary(controls: dict[str, Any]) -> None:
    provider = controls.get("llm_provider_label") or "Mock provider"
    mode = controls.get("run_mode", "Demo Mode")
    model = controls.get("model_name") or "Default model"
    cols = st.columns(3)
    cols[0].metric("Mode", str(mode))
    cols[1].metric("Provider", str(provider))
    cols[2].metric("Model", str(model))
    if mode == "Backend + Model API":
        st.caption(f"Evidence provider: {controls.get('search_provider_label', 'None')}")
    if mode == "Backend + Model API":
        st.caption(f"Backend: {controls.get('api_url', '')}")
    else:
        st.caption("Ready. Demo Mode does not require backend setup.")


def render_accessible_settings_summary(controls: dict[str, Any]) -> None:
    with st.expander("Settings", expanded=False):
        st.write(f"Mode: {controls.get('run_mode', 'Demo Mode')}")
        st.write(f"Model provider: {controls.get('llm_provider_label', 'Mock provider')}")
        st.write(f"Evidence provider: {controls.get('search_provider_label', 'None')}")
        st.write(f"Model: {controls.get('model_name') or 'Default model'}")


def render_empty_state() -> None:
    st.markdown(
        """
        <div class="tg-empty-state">
          <div class="tg-section-title">Result</div>
          <div class="tg-empty-title">Ready to verify an answer</div>
          <div class="tg-muted">
            Run TemporalGuard to see the final answer, trust score, evidence, and claims.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def run_dashboard_analysis(question: str, base_answer: str, controls: dict[str, Any]) -> dict[str, Any]:
    mode = controls["run_mode"]
    if mode == "Demo Mode":
        return build_demo_output(question, base_answer or None)
    if mode == "Local Pipeline":
        try:
            from temporalguard.llm.providers import create_llm_provider
            from temporalguard.pipeline.orchestrator import run_temporalguard_pipeline
            from temporalguard.search.providers import create_search_provider

            llm_provider = None
            if not base_answer:
                llm_provider = create_llm_provider(
                    controls.get("llm_provider"),
                    model_name=controls.get("model_name") or None,
                    require_configured=True,
                )
            search_provider = None
            if controls.get("search_provider") != "none":
                search_provider = create_search_provider({"search_provider": controls.get("search_provider")})
            return run_temporalguard_pipeline(
                question=question,
                base_answer=base_answer or None,
                llm_provider=llm_provider,
                search_provider=search_provider,
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
                search_provider=controls.get("search_provider"),
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


def render_results(
    output: dict[str, Any],
    controls: dict[str, Any],
    show_raw_json: bool,
    debug_enabled: bool,
) -> None:
    summary = get_dashboard_summary(output)

    tabs = st.tabs(["Answer", "Evidence", "Claims", "Details"])
    with tabs[0]:
        render_result_card(get_final_answer(output), summary)
        render_overview(output)
        render_backend_evidence_note(output, controls)
        render_what_happened()
    with tabs[1]:
        render_evidence(output)
    with tabs[2]:
        render_claims(output)
    with tabs[3]:
        render_details(output, show_raw_json=show_raw_json, debug_enabled=debug_enabled)


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
            <div class="tg-section-title">Final Answer</div>
            <div class="tg-muted" style="line-height: 1.65;">{_escape(get_final_answer(output))}</div>
          </div>
        </div>
        <div class="tg-card">
          <div class="tg-section-title">Simple Explanation</div>
          <div class="tg-muted" style="line-height: 1.65;">{_escape(safe_get(output, ["report", "executive_summary"], "No report summary available."))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if warning:
        render_warning_card(str(warning))


def render_what_happened() -> None:
    st.markdown(
        """
        <div class="tg-card">
          <div class="tg-section-title">What Happened?</div>
          <div class="tg-muted" style="line-height: 1.75;">
            TemporalGuard checked the answer, extracted factual claims, compared those claims with evidence,
            and produced a safety label plus a corrected answer when needed.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_backend_evidence_note(output: dict[str, Any], controls: dict[str, Any]) -> None:
    if controls.get("run_mode") != "Backend + Model API":
        return
    evidence_total = _as_int(safe_get(output, ["evidence", "total_evidence_items"], 0))
    trust_score = _as_float(safe_get(output, ["risk_label", "trust_score"], 0.0))
    if evidence_total == 0 or trust_score < 0.5:
        st.info(
            "Model generation is working, but evidence retrieval is not connected in this mode, "
            "so TemporalGuard may return low trust or insufficient evidence."
        )


def render_claims(output: dict[str, Any]) -> None:
    rows = claims_to_table_rows(output)
    st.markdown("<div class='tg-section-title'>Claims</div>", unsafe_allow_html=True)
    if not rows:
        st.markdown("<div class='tg-card tg-muted'>No factual claims were extracted.</div>", unsafe_allow_html=True)
        return
    st.dataframe(rows, width="stretch", hide_index=True)


def render_evidence(output: dict[str, Any]) -> None:
    rows = evidence_to_table_rows(output)
    st.markdown("<div class='tg-section-title'>Evidence</div>", unsafe_allow_html=True)
    if not rows:
        st.markdown("<div class='tg-card tg-muted'>No evidence was retrieved or evidence retrieval was skipped.</div>", unsafe_allow_html=True)
        return
    st.dataframe(rows, width="stretch", hide_index=True)


def render_details(output: dict[str, Any], show_raw_json: bool, debug_enabled: bool) -> None:
    st.markdown("#### Details")
    render_detail_metrics(output)
    render_report(output)
    render_debug(output, show_raw_json=show_raw_json, debug_enabled=debug_enabled)


def render_detail_metrics(output: dict[str, Any]) -> None:
    metrics = build_metric_cards(output)
    columns = st.columns(2)
    for index, metric in enumerate(metrics):
        with columns[index % 2]:
            st.metric(str(metric.get("label", "")), str(metric.get("value", "")))
            caption = str(metric.get("caption", "")).strip()
            if caption:
                st.caption(caption)


def render_report(output: dict[str, Any]) -> None:
    details = safe_get(output, ["report", "thesis_summary"], {}) or {}
    sections = [
        ("Summary", safe_get(output, ["report", "executive_summary"], "No summary available.")),
        ("Issue", details.get("problem_observed", "Not reported.")),
        ("Finding", details.get("temporal_failure_type", "Not reported.")),
        ("Evidence Quality", details.get("evidence_quality", "Not reported.")),
        ("Decision", details.get("system_decision", "Not reported.")),
    ]
    with st.container():
        for title, value in sections:
            st.markdown(f"**{title}**")
            st.caption(str(value))


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
        st.caption(f"Missing sections: {safe_get(output, ['report', 'debug_info', 'missing_sections'], [])}")
    with st.expander("Debug JSON", expanded=show_raw_json):
        st.code(json.dumps(output, indent=2, default=str), language="json")


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


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
