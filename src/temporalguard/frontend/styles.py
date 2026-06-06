"""Warm SaaS Streamlit styling for TemporalGuard."""

from __future__ import annotations

import streamlit as st


def inject_premium_css() -> None:
    st.markdown(
        """
        <style>
        :root {
          --tg-bg: #fbf8ef;
          --tg-bg-2: #f7f3e8;
          --tg-cream: #fffaf0;
          --tg-card: #ffffff;
          --tg-card-warm: #fffdf7;
          --tg-text: #1f2937;
          --tg-text-soft: #2f2f2f;
          --tg-muted: #5f6673;
          --tg-faint: #8a8f98;
          --tg-border: #eee7d8;
          --tg-border-strong: #dfd6c5;
          --tg-sage: #8bbfa3;
          --tg-mint: #b7dfcf;
          --tg-sage-soft: #d9e8dc;
          --tg-beige: #eee7d8;
          --tg-charcoal: #2f2f2f;
          --tg-blue: #2563eb;
          --tg-success: #16a34a;
          --tg-warning: #d97706;
          --tg-danger: #dc2626;
          --tg-radius: 24px;
          --tg-radius-sm: 16px;
          --tg-shadow: 0 24px 70px rgba(47, 47, 47, .10);
          --tg-shadow-soft: 0 12px 34px rgba(47, 47, 47, .07);
        }

        @keyframes tgFadeUp {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes tgSoftGlow {
          0%, 100% { opacity: .55; transform: translate3d(0, 0, 0) scale(1); }
          50% { opacity: .78; transform: translate3d(10px, -10px, 0) scale(1.015); }
        }
        @keyframes tgGradientMove {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }

        html, body, .stApp {
          font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          color: var(--tg-text);
          background:
            radial-gradient(circle at 16% 8%, rgba(183, 223, 207, .42), transparent 30%),
            radial-gradient(circle at 86% 6%, rgba(238, 231, 216, .86), transparent 28%),
            linear-gradient(180deg, var(--tg-bg) 0%, var(--tg-bg-2) 100%);
        }
        .stApp::before {
          content: "";
          position: fixed;
          inset: 0;
          pointer-events: none;
          background:
            radial-gradient(circle at 78% 18%, rgba(139, 191, 163, .22), transparent 28%),
            radial-gradient(circle at 24% 82%, rgba(255, 250, 240, .85), transparent 32%);
          animation: tgSoftGlow 18s ease-in-out infinite;
          z-index: 0;
        }
        .stApp > div { position: relative; z-index: 1; }
        #MainMenu, footer, header { visibility: hidden; }

        .block-container {
          max-width: 1120px;
          padding: 1.3rem 1.4rem 2.2rem;
        }
        .tg-app-shell {
          animation: tgFadeUp .45s ease both;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
          background:
            linear-gradient(180deg, rgba(255, 250, 240, .98), rgba(247, 243, 232, .98)) !important;
          border-right: 1px solid var(--tg-border);
          box-shadow: 16px 0 50px rgba(47, 47, 47, .08);
          overflow-y: auto !important;
          scrollbar-width: thin;
          scrollbar-color: var(--tg-sage) transparent;
        }
        section[data-testid="stSidebar"] > div {
          background: transparent !important;
          max-height: 100vh;
          overflow-y: auto !important;
          padding-bottom: 30px;
        }
        section[data-testid="stSidebar"]::-webkit-scrollbar,
        section[data-testid="stSidebar"] > div::-webkit-scrollbar { width: 8px; }
        section[data-testid="stSidebar"]::-webkit-scrollbar-thumb,
        section[data-testid="stSidebar"] > div::-webkit-scrollbar-thumb {
          background: rgba(139, 191, 163, .7);
          border-radius: 999px;
        }
        section[data-testid="stSidebar"] * {
          color: var(--tg-text) !important;
        }
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        section[data-testid="stSidebar"] .stCaptionContainer,
        section[data-testid="stSidebar"] small {
          color: var(--tg-muted) !important;
        }
        section[data-testid="stSidebar"] [data-testid="stExpander"] {
          background: rgba(255, 255, 255, .66) !important;
          border: 1px solid var(--tg-border) !important;
          border-radius: 18px !important;
          box-shadow: 0 8px 24px rgba(47, 47, 47, .04);
        }
        section[data-testid="stSidebar"] [data-testid="stExpander"] details {
          background: transparent !important;
        }
        .tg-sidebar-brand {
          padding: 18px;
          margin: 4px 0 18px;
          border: 1px solid var(--tg-border);
          border-radius: 22px;
          background:
            linear-gradient(135deg, rgba(217, 232, 220, .92), rgba(255, 255, 255, .72)),
            var(--tg-card-warm);
          box-shadow: var(--tg-shadow-soft);
        }
        .tg-brand-mark {
          width: 38px;
          height: 38px;
          border-radius: 14px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 12px;
          background: linear-gradient(135deg, #2f2f2f, #6f9e82);
          color: #fffaf0 !important;
          font-weight: 900;
          letter-spacing: .02em;
          box-shadow: 0 10px 24px rgba(47, 47, 47, .18);
        }
        .tg-sidebar-title {
          color: var(--tg-charcoal);
          font-size: 24px;
          line-height: 1.1;
          font-weight: 850;
          margin-bottom: 8px;
        }
        .tg-sidebar-section {
          color: #4f7f64 !important;
          font-size: 12px;
          font-weight: 850;
          letter-spacing: .06em;
          text-transform: uppercase;
          margin: 18px 0 8px;
        }

        /* Product header and cards */
        .tg-hero { margin-bottom: 18px; }
        .tg-product-header {
          position: relative;
          overflow: hidden;
          border: 1px solid rgba(238, 231, 216, .95);
          border-radius: 32px;
          padding: 42px 34px;
          text-align: center;
          background:
            radial-gradient(circle at 18% 18%, rgba(255, 250, 240, .98), transparent 30%),
            radial-gradient(circle at 86% 18%, rgba(183, 223, 207, .58), transparent 30%),
            linear-gradient(135deg, rgba(255, 255, 255, .9), rgba(255, 250, 240, .94));
          box-shadow: var(--tg-shadow);
          animation: tgFadeUp .45s ease both;
        }
        .tg-product-header::after {
          content: "";
          position: absolute;
          right: -60px;
          bottom: -80px;
          width: 250px;
          height: 190px;
          border-radius: 50%;
          background: radial-gradient(circle, rgba(139, 191, 163, .28), transparent 70%);
          pointer-events: none;
        }
        .tg-hero-kicker {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-height: 30px;
          padding: 6px 12px;
          margin-bottom: 14px;
          border: 1px solid rgba(139, 191, 163, .32);
          border-radius: 999px;
          background: rgba(217, 232, 220, .56);
          color: #315d45;
          font-size: 13px;
          font-weight: 780;
        }
        .tg-hero-title {
          margin: 0 0 10px;
          color: var(--tg-charcoal);
          font-size: 46px;
          line-height: 1.02;
          font-weight: 870;
          letter-spacing: 0;
        }
        .tg-hero-subtitle {
          max-width: 720px;
          color: var(--tg-muted);
          font-size: 19px;
          line-height: 1.55;
          margin: 0 auto 18px;
        }
        .tg-hero-chips {
          display: flex;
          justify-content: center;
          flex-wrap: wrap;
          gap: 8px;
        }
        .tg-chip {
          display: inline-flex;
          align-items: center;
          min-height: 32px;
          padding: 7px 12px;
          margin: 0 8px 8px 0;
          border-radius: 999px;
          border: 1px solid rgba(139, 191, 163, .34);
          background: rgba(217, 232, 220, .7);
          color: #315d45;
          font-size: 13px;
          font-weight: 780;
        }
        .tg-card,
        .tg-workspace-card,
        .tg-empty-state {
          border: 1px solid var(--tg-border);
          border-radius: var(--tg-radius);
          background: rgba(255, 255, 255, .88);
          box-shadow: var(--tg-shadow-soft);
          padding: 20px;
          margin-bottom: 15px;
          animation: tgFadeUp .45s ease both;
          transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
        }
        .tg-workspace-card {
          background:
            linear-gradient(180deg, rgba(255, 255, 255, .94), rgba(255, 250, 240, .88));
          border-radius: 28px;
          padding: 24px;
        }
        .tg-card:hover,
        .tg-kpi-card:hover {
          transform: translateY(-2px);
          border-color: rgba(139, 191, 163, .45);
          box-shadow: var(--tg-shadow);
        }
        .tg-section-title {
          color: #4f7f64;
          font-size: 13px;
          line-height: 1.2;
          font-weight: 850;
          letter-spacing: .055em;
          text-transform: uppercase;
          margin: 0 0 10px;
        }
        .tg-muted {
          color: var(--tg-muted);
          font-size: 15px;
          line-height: 1.65;
        }
        .tg-input-title,
        .tg-empty-title {
          color: var(--tg-charcoal);
          font-size: 23px;
          line-height: 1.25;
          font-weight: 850;
          margin: 8px 0;
        }
        .tg-split-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 15px;
          margin-bottom: 15px;
        }

        /* Result */
        .tg-result-card {
          position: relative;
          overflow: hidden;
          border-radius: 28px;
          padding: 1px;
          margin: 12px 0 18px;
          background: linear-gradient(135deg, #8bbfa3, #b7dfcf, #eee7d8);
          background-size: 220% 220%;
          animation: tgFadeUp .45s ease both, tgGradientMove 12s ease infinite;
          box-shadow: 0 24px 70px rgba(79, 127, 100, .14);
        }
        .tg-result-card-inner {
          border-radius: 27px;
          padding: 26px;
          background: rgba(255, 255, 255, .94);
        }
        .tg-result-header {
          display: flex;
          justify-content: space-between;
          gap: 16px;
          align-items: flex-start;
          margin-bottom: 16px;
        }
        .tg-answer-text {
          color: var(--tg-text);
          font-size: 19px;
          line-height: 1.75;
          margin-top: 12px;
        }
        .tg-trust-pill {
          min-width: 116px;
          text-align: right;
          border: 1px solid rgba(139, 191, 163, .36);
          background: rgba(217, 232, 220, .62);
          border-radius: 18px;
          padding: 11px 13px;
        }
        .tg-kpi-card {
          min-height: 104px;
          padding: 16px;
          margin-bottom: 12px;
          border-radius: 20px;
          border: 1px solid var(--tg-border);
          background: rgba(255, 255, 255, .92);
          box-shadow: var(--tg-shadow-soft);
        }
        .tg-kpi-label {
          color: var(--tg-faint);
          text-transform: uppercase;
          font-size: 12px;
          font-weight: 820;
          letter-spacing: .055em;
        }
        .tg-kpi-value {
          color: var(--tg-charcoal);
          font-size: 22px;
          font-weight: 850;
          line-height: 1.18;
          margin-top: 10px;
          overflow-wrap: anywhere;
        }
        .tg-kpi-caption {
          color: var(--tg-muted);
          font-size: 14px;
          line-height: 1.45;
          margin-top: 8px;
        }

        /* Badges and warnings */
        .tg-badge {
          display: inline-flex;
          align-items: center;
          white-space: nowrap;
          border-radius: 999px;
          padding: 8px 11px;
          border: 1px solid transparent;
          font-size: 12px;
          line-height: 1;
          font-weight: 850;
          letter-spacing: .035em;
        }
        .tg-badge-safe { color: #166534; background: #dcfce7; border-color: #bbf7d0; }
        .tg-badge-low { color: #3f6212; background: #ecfccb; border-color: #d9f99d; }
        .tg-badge-medium { color: #92400e; background: #fef3c7; border-color: #fde68a; }
        .tg-badge-high { color: #9f1239; background: #ffe4e6; border-color: #fecdd3; }
        .tg-badge-critical { color: #991b1b; background: #fee2e2; border-color: #fecaca; }
        .tg-badge-unknown { color: #334155; background: #f1f5f9; border-color: #cbd5e1; }
        .tg-warning-card {
          border: 1px solid #f1d4a7;
          background: #fff8e9;
          color: #8a4b0f;
          border-radius: 20px;
          padding: 14px 16px;
          margin: 12px 0 16px;
          font-size: 15px;
          line-height: 1.55;
          animation: tgFadeUp .45s ease both;
        }
        .tg-debug-box {
          background: rgba(255, 255, 255, .72);
          border: 1px solid var(--tg-border);
          border-radius: 20px;
          padding: 14px;
          color: var(--tg-muted);
        }
        .tg-footer {
          color: var(--tg-faint);
          border-top: 1px solid rgba(223, 214, 197, .8);
          margin-top: 22px;
          padding-top: 14px;
          font-size: 13px;
          text-align: center;
        }

        /* Streamlit form controls */
        label, .stMarkdown, p, span, div { letter-spacing: 0; }
        div[data-testid="stTextArea"] label,
        div[data-testid="stTextInput"] label,
        div[data-testid="stSelectbox"] label,
        div[data-testid="stRadio"] label,
        div[data-testid="stCheckbox"] label,
        div[data-testid="stToggle"] label,
        div[data-testid="stSlider"] label {
          color: var(--tg-text) !important;
          font-size: 14px !important;
          font-weight: 730 !important;
        }
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stTextInput"] input {
          color: var(--tg-text) !important;
          -webkit-text-fill-color: var(--tg-text) !important;
          background: rgba(255, 255, 255, .96) !important;
          border: 1px solid var(--tg-border-strong) !important;
          border-radius: 18px !important;
          box-shadow: 0 1px 2px rgba(47, 47, 47, .04) !important;
          font-size: 16px !important;
          line-height: 1.55 !important;
        }
        div[data-testid="stTextArea"] textarea:hover,
        div[data-testid="stTextInput"] input:hover,
        div[data-testid="stSelectbox"] [data-baseweb="select"] > div:hover {
          border-color: rgba(139, 191, 163, .72) !important;
          box-shadow: 0 8px 22px rgba(47, 47, 47, .05) !important;
        }
        div[data-testid="stTextArea"] textarea::placeholder,
        div[data-testid="stTextInput"] input::placeholder {
          color: #737b86 !important;
          -webkit-text-fill-color: #737b86 !important;
        }
        div[data-testid="stTextArea"] textarea:focus,
        div[data-testid="stTextInput"] input:focus {
          border-color: var(--tg-sage) !important;
          box-shadow: 0 0 0 4px rgba(139, 191, 163, .18) !important;
        }

        div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
          color: var(--tg-text) !important;
          background: rgba(255, 255, 255, .96) !important;
          border: 1px solid var(--tg-border-strong) !important;
          border-radius: 18px !important;
          min-height: 44px;
        }
        div[data-testid="stSelectbox"] [data-baseweb="select"],
        div[data-testid="stSelectbox"] [data-baseweb="select"] *,
        div[data-testid="stSelectbox"] [data-baseweb="select"] span,
        div[data-testid="stSelectbox"] [data-baseweb="select"] input {
          color: var(--tg-text) !important;
          -webkit-text-fill-color: var(--tg-text) !important;
        }
        div[data-baseweb="popover"],
        div[data-baseweb="popover"] * {
          color: var(--tg-text) !important;
          background-color: #fffdf7 !important;
          -webkit-text-fill-color: var(--tg-text) !important;
        }
        ul[role="listbox"] {
          background: #fffdf7 !important;
          border: 1px solid var(--tg-border) !important;
          border-radius: 18px !important;
          box-shadow: var(--tg-shadow) !important;
          padding: 6px !important;
        }
        li[role="option"] {
          color: var(--tg-text) !important;
          background: #fffdf7 !important;
          font-size: 15px !important;
          border-radius: 12px !important;
        }
        li[role="option"]:hover,
        li[aria-selected="true"] {
          background: var(--tg-sage-soft) !important;
          color: #264a36 !important;
          -webkit-text-fill-color: #264a36 !important;
        }
        div[role="option"] {
          color: var(--tg-text) !important;
          -webkit-text-fill-color: var(--tg-text) !important;
          background: #fffdf7 !important;
        }
        div[role="option"]:hover,
        div[aria-selected="true"] {
          color: #264a36 !important;
          -webkit-text-fill-color: #264a36 !important;
          background: var(--tg-sage-soft) !important;
        }
        div[data-testid="stRadio"] label,
        div[data-testid="stCheckbox"] label,
        div[data-testid="stToggle"] label {
          color: var(--tg-text) !important;
        }
        .stButton > button {
          width: 100%;
          min-height: 52px;
          border: 0;
          color: #ffffff !important;
          border-radius: 18px;
          background: linear-gradient(135deg, #2f2f2f 0%, #4f7f64 56%, #8bbfa3 100%);
          background-size: 180% 180%;
          box-shadow: 0 16px 38px rgba(47, 47, 47, .18);
          font-size: 17px;
          font-weight: 850;
          animation: tgGradientMove 14s ease infinite;
          transition: transform .18s ease, box-shadow .18s ease;
        }
        .stButton > button:hover {
          transform: translateY(-1px);
          box-shadow: 0 20px 46px rgba(47, 47, 47, .22);
          color: #ffffff !important;
        }
        div[data-testid="stSlider"] [role="slider"] {
          background: var(--tg-sage) !important;
          border-color: var(--tg-sage) !important;
        }
        .stTabs [data-baseweb="tab-list"] {
          gap: 8px;
          border-bottom: 1px solid var(--tg-border);
          margin-top: 8px;
        }
        .stTabs [data-baseweb="tab"] {
          color: var(--tg-muted) !important;
          border-radius: 16px 16px 0 0;
          padding: 10px 14px;
          font-size: 15px;
          font-weight: 800;
        }
        .stTabs [aria-selected="true"] {
          color: #315d45 !important;
          background: rgba(217, 232, 220, .75);
          border-bottom: 2px solid var(--tg-sage);
        }
        div[data-testid="stExpander"] {
          border: 1px solid var(--tg-border) !important;
          border-radius: 20px !important;
          background: rgba(255, 255, 255, .58) !important;
          box-shadow: 0 8px 22px rgba(47, 47, 47, .04);
        }
        div[data-testid="stExpander"] summary,
        div[data-testid="stExpander"] summary * {
          color: var(--tg-text) !important;
          font-weight: 760 !important;
        }
        div[data-testid="stDataFrame"] {
          border: 1px solid var(--tg-border);
          border-radius: 20px;
          overflow: hidden;
          background: rgba(255, 255, 255, .92);
        }
        div[data-testid="stMetric"] {
          background: rgba(255, 255, 255, .92);
          border: 1px solid var(--tg-border);
          border-radius: 20px;
          padding: 14px;
          box-shadow: var(--tg-shadow-soft);
        }
        div[data-testid="stMetric"] * {
          color: var(--tg-text) !important;
        }
        div[data-testid="stCaptionContainer"] {
          color: var(--tg-muted) !important;
        }
        pre, code {
          color: var(--tg-text) !important;
          background: #fffaf0 !important;
          border-radius: 16px !important;
        }

        @media (max-width: 900px) {
          .tg-split-grid { grid-template-columns: 1fr; }
          .tg-product-header { padding: 24px; }
          .tg-hero-title { font-size: 36px; }
          .tg-result-header { flex-direction: column; }
          .tg-trust-pill {
            text-align: left;
            width: 100%;
          }
          .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
