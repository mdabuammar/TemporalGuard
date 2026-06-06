"""Small Streamlit rendering components for the TemporalGuard dashboard."""

from __future__ import annotations

from typing import Any

import streamlit as st

from temporalguard.frontend.streamlit_helpers import format_badge


def render_hero() -> None:
    st.markdown(
        """
        <div class="tg-hero">
          <div class="tg-product-header">
            <div class="tg-hero-title">TemporalGuard</div>
            <p class="tg-hero-subtitle">
              Verify, correct, and trust time-sensitive AI answers.
            </p>
            <div>
              <span class="tg-chip">Detect</span>
              <span class="tg-chip">Verify</span>
              <span class="tg-chip">Correct</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_result_card(final_answer: str, dashboard_summary: dict[str, Any]) -> None:
    badge = format_badge(dashboard_summary.get("badge"))
    trust = float(dashboard_summary.get("trust_score", 0.0) or 0.0)
    badge_class = dashboard_summary.get("badge_class") or "tg-badge-unknown"
    warning = dashboard_summary.get("user_warning")
    warning_html = (
        f"<div class='tg-warning-card'>{_escape(str(warning))}</div>"
        if warning
        else ""
    )
    st.markdown(
        f"""
        <div class="tg-result-card">
          <div class="tg-result-card-inner">
            <div class="tg-result-header">
              <div>
                <div class="tg-section-title">Final answer</div>
                <span class="tg-badge {badge_class}">{_escape(badge)}</span>
              </div>
              <div class="tg-trust-pill">
                <div class="tg-muted" style="font-size: 12px;">Trust score</div>
                <div class="tg-kpi-value">{trust:.2f}</div>
              </div>
            </div>
            <div class="tg-answer-text">{_escape(final_answer)}</div>
            {warning_html}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_grid(metrics: list[dict[str, Any]]) -> None:
    columns = st.columns(2)
    for index, metric in enumerate(metrics):
        with columns[index % 2]:
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


def render_summary_card(title: str, value: str, caption: str = "", badge_class: str = "tg-badge-unknown") -> None:
    st.markdown(
        f"""
        <div class="tg-summary-card">
          <div class="tg-summary-top">
            <span class="tg-badge {badge_class}">{_escape(title)}</span>
          </div>
          <div class="tg-summary-value">{_escape(value)}</div>
          <div class="tg-muted">{_escape(caption)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_warning_card(message: str) -> None:
    if message:
        st.markdown(f"<div class='tg-warning-card'>{_escape(message)}</div>", unsafe_allow_html=True)


def render_footer() -> None:
    st.markdown(
        "<div class='tg-footer'>TemporalGuard</div>",
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
