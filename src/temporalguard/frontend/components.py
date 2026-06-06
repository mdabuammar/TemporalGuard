"""Small Streamlit rendering components for the TemporalGuard dashboard."""

from __future__ import annotations

from typing import Any

import streamlit as st

from temporalguard.frontend.streamlit_helpers import format_badge, format_label


def render_hero() -> None:
    st.markdown(
        """
        <div class="tg-hero">
          <div class="tg-glass-card tg-hero-main">
            <div class="tg-hero-title">TemporalGuard</div>
            <p class="tg-hero-subtitle">
              Check whether an LLM answer is current, supported, and safe to use.
            </p>
            <span class="tg-chip">Ask</span>
            <span class="tg-chip">Check Claims</span>
            <span class="tg-chip">Compare Evidence</span>
            <span class="tg-chip">Get Safer Answer</span>
          </div>
          <div class="tg-glass-card tg-help-card">
            <div class="tg-section-title">How It Works</div>
            <div class="tg-muted" style="line-height: 1.65;">
              Demo works offline. Backend + Model API can generate an answer with OpenRouter when provided base answer is off.
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_card(summary: dict[str, Any]) -> None:
    st.markdown(
        f"""
        <div class="tg-card">
          <div class="tg-section-title">Current Run</div>
          <div class="tg-kpi-value">{_escape(format_label(summary.get("mode", "Demo/mock mode")))}</div>
          <div class="tg-muted" style="margin-top: 8px;">Report type: {_escape(str(summary.get("report_type", "dashboard")))}</div>
          <div style="margin-top: 14px;"><span class="tg-badge tg-badge-safe">{_escape(str(summary.get("status", "READY")).upper())}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_step_flow(active_step: int = 1) -> None:
    steps = [
        "Choose mode",
        "Enter question",
        "Add answer",
        "Run check",
        "View result",
    ]
    html = ["<div class='tg-step-flow'>"]
    for index, label in enumerate(steps, start=1):
        css = "tg-step tg-step-active" if index == active_step else "tg-step"
        html.append(
            f"<div class='{css}'><span>{index}</span><strong>{_escape(label)}</strong></div>"
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def render_result_card(final_answer: str, dashboard_summary: dict[str, Any]) -> None:
    badge = format_badge(dashboard_summary.get("badge"))
    risk = format_label(dashboard_summary.get("risk_label"))
    safety = format_label(dashboard_summary.get("temporal_safety_status"))
    trust = float(dashboard_summary.get("trust_score", 0.0) or 0.0)
    badge_class = dashboard_summary.get("badge_class") or "tg-badge-unknown"
    risk_class = dashboard_summary.get("risk_class") or "tg-badge-unknown"
    warning = dashboard_summary.get("user_warning")
    warning_html = (
        f"<div class='tg-warning-card'>{_escape(str(warning))}</div>"
        if warning
        else "<div class='tg-muted' style='margin-top: 12px;'>No user-facing warning was generated for this run.</div>"
    )
    st.markdown(
        f"""
        <div class="tg-result-card">
          <div class="tg-result-card-inner">
            <div class="tg-result-header">
              <div>
                <div class="tg-section-title">Result</div>
                <span class="tg-badge {badge_class}">{_escape(badge)}</span>
              </div>
              <div style="text-align: right;">
                <div class="tg-muted" style="font-size: 12px;">Trust Score</div>
                <div class="tg-kpi-value">{trust:.2f}</div>
              </div>
            </div>
            <div class="tg-answer-text">{_escape(final_answer)}</div>
            <div style="margin-top: 16px;">
              <span class="tg-badge {risk_class}">RISK {format_badge(risk)}</span>
              <span class="tg-badge tg-badge-unknown" style="margin-left: 8px;">SAFETY {format_badge(safety)}</span>
            </div>
            {warning_html}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_grid(metrics: list[dict[str, Any]]) -> None:
    columns = st.columns(3)
    for index, metric in enumerate(metrics):
        with columns[index % 3]:
            st.markdown(
            f"""
            <div class="tg-kpi-card">
              <div class="tg-kpi-label">{_escape(metric.get("label", ""))}</div>
              <div class="tg-kpi-value">{_escape(metric.get("value", ""))}</div>
              <div class="tg-kpi-caption">{_escape(metric.get("caption", ""))}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )


def render_warning_card(message: str) -> None:
    if message:
        st.markdown(f"<div class='tg-warning-card'>{_escape(message)}</div>", unsafe_allow_html=True)


def render_footer() -> None:
    st.markdown(
        "<div class='tg-footer'>TemporalGuard - Time-aware LLM reliability framework</div>",
        unsafe_allow_html=True,
    )


def _escape(value: Any) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
