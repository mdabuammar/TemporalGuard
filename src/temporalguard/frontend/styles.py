"""Production Streamlit styling for TemporalGuard."""

from __future__ import annotations

import streamlit as st


def inject_premium_css() -> None:
    st.markdown(
        """
        <style>
        :root {
          --tg-bg: #f4f7fb;
          --tg-surface: #ffffff;
          --tg-surface-soft: #f8fafc;
          --tg-sidebar: #0b1020;
          --tg-sidebar-soft: #111827;
          --tg-text: #0f172a;
          --tg-muted: #475569;
          --tg-soft: #64748b;
          --tg-border: #e2e8f0;
          --tg-border-strong: #cbd5e1;
          --tg-primary: #2563eb;
          --tg-primary-dark: #1d4ed8;
          --tg-accent: #06b6d4;
          --tg-violet: #8b5cf6;
          --tg-success: #16a34a;
          --tg-warning: #f59e0b;
          --tg-danger: #dc2626;
          --tg-radius: 14px;
          --tg-shadow: 0 18px 45px rgba(15, 23, 42, .08);
          --tg-shadow-soft: 0 10px 28px rgba(15, 23, 42, .06);
        }

        @keyframes tgFadeUp {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes tgGlow {
          0%, 100% { opacity: .65; transform: translate3d(0, 0, 0) scale(1); }
          50% { opacity: .9; transform: translate3d(8px, -8px, 0) scale(1.02); }
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
            radial-gradient(circle at 14% 4%, rgba(37, 99, 235, .10), transparent 28%),
            radial-gradient(circle at 82% 8%, rgba(6, 182, 212, .14), transparent 26%),
            linear-gradient(180deg, #f8fafc 0%, #eef4fb 100%);
        }
        .stApp::before {
          content: "";
          position: fixed;
          inset: 0;
          pointer-events: none;
          background: radial-gradient(circle at 70% 16%, rgba(139, 92, 246, .08), transparent 30%);
          animation: tgGlow 16s ease-in-out infinite;
          z-index: 0;
        }
        .stApp > div { position: relative; z-index: 1; }
        #MainMenu, footer, header { visibility: hidden; }

        .block-container {
          max-width: 1160px;
          padding: 1.35rem 1.35rem 2.2rem;
        }
        .tg-app-shell {
          animation: tgFadeUp .45s ease both;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
          background: linear-gradient(180deg, #0b1020 0%, #111827 100%) !important;
          border-right: 1px solid rgba(148, 163, 184, .24);
          box-shadow: 14px 0 40px rgba(15, 23, 42, .12);
          overflow-y: auto !important;
          scrollbar-width: thin;
          scrollbar-color: rgba(56, 189, 248, .55) rgba(15, 23, 42, .7);
        }
        section[data-testid="stSidebar"] > div {
          background: transparent !important;
          max-height: 100vh;
          overflow-y: auto !important;
          padding-bottom: 28px;
        }
        section[data-testid="stSidebar"]::-webkit-scrollbar,
        section[data-testid="stSidebar"] > div::-webkit-scrollbar { width: 8px; }
        section[data-testid="stSidebar"]::-webkit-scrollbar-thumb,
        section[data-testid="stSidebar"] > div::-webkit-scrollbar-thumb {
          background: rgba(56, 189, 248, .5);
          border-radius: 999px;
        }
        section[data-testid="stSidebar"] * {
          color: #e5eefb !important;
        }
        section[data-testid="stSidebar"] [data-testid="stExpander"] {
          background: rgba(255, 255, 255, .05) !important;
          border: 1px solid rgba(148, 163, 184, .22) !important;
          border-radius: 14px !important;
        }
        section[data-testid="stSidebar"] [data-testid="stExpander"] details {
          background: transparent !important;
        }
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        section[data-testid="stSidebar"] .stCaptionContainer,
        section[data-testid="stSidebar"] small {
          color: #b9c7d9 !important;
        }
        .tg-sidebar-brand {
          padding: 16px;
          margin: 4px 0 16px;
          border: 1px solid rgba(148, 163, 184, .2);
          border-radius: var(--tg-radius);
          background: rgba(255, 255, 255, .06);
          box-shadow: inset 0 1px 0 rgba(255, 255, 255, .05);
        }
        .tg-sidebar-title {
          color: #ffffff;
          font-size: 22px;
          line-height: 1.1;
          font-weight: 850;
          margin-bottom: 8px;
        }
        .tg-sidebar-section {
          color: #93c5fd !important;
          font-size: 12px;
          font-weight: 850;
          letter-spacing: .08em;
          text-transform: uppercase;
          margin: 18px 0 8px;
        }

        /* Typography and cards */
        .tg-hero {
          margin-bottom: 18px;
        }
        .tg-product-header {
          position: relative;
          overflow: hidden;
          border: 1px solid rgba(226, 232, 240, .9);
          border-radius: 22px;
          padding: 28px;
          background:
            linear-gradient(135deg, rgba(37, 99, 235, .08), rgba(6, 182, 212, .08)),
            #ffffff;
          box-shadow: var(--tg-shadow);
          animation: tgFadeUp .45s ease both;
        }
        .tg-product-header::after {
          content: "";
          position: absolute;
          right: -70px;
          bottom: -90px;
          width: 260px;
          height: 200px;
          background: radial-gradient(circle, rgba(37, 99, 235, .15), transparent 70%);
          pointer-events: none;
        }
        .tg-hero-title {
          margin: 0 0 8px;
          color: var(--tg-text);
          font-size: 42px;
          line-height: 1.02;
          font-weight: 850;
          letter-spacing: 0;
        }
        .tg-hero-subtitle {
          max-width: 720px;
          color: var(--tg-muted);
          font-size: 18px;
          line-height: 1.55;
          margin: 0 0 18px;
        }
        .tg-chip {
          display: inline-flex;
          align-items: center;
          min-height: 30px;
          padding: 6px 11px;
          margin: 0 8px 8px 0;
          border-radius: 999px;
          border: 1px solid #bfdbfe;
          background: #eff6ff;
          color: #1d4ed8;
          font-size: 13px;
          font-weight: 750;
        }
        .tg-card,
        .tg-workspace-card,
        .tg-empty-state,
        .tg-summary-card {
          border: 1px solid var(--tg-border);
          border-radius: var(--tg-radius);
          background: var(--tg-surface);
          box-shadow: var(--tg-shadow-soft);
          padding: 18px;
          margin-bottom: 14px;
          animation: tgFadeUp .45s ease both;
          transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
        }
        .tg-card:hover,
        .tg-summary-card:hover,
        .tg-kpi-card:hover {
          transform: translateY(-2px);
          border-color: #bfdbfe;
          box-shadow: var(--tg-shadow);
        }
        .tg-section-title {
          color: var(--tg-primary);
          font-size: 13px;
          line-height: 1.2;
          font-weight: 850;
          letter-spacing: .06em;
          text-transform: uppercase;
          margin: 0 0 10px;
        }
        .tg-muted {
          color: var(--tg-muted);
          font-size: 15px;
          line-height: 1.6;
        }
        .tg-input-title,
        .tg-summary-value,
        .tg-empty-title {
          color: var(--tg-text);
          font-size: 22px;
          line-height: 1.25;
          font-weight: 850;
          margin: 8px 0;
        }
        .tg-split-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 14px;
          margin-bottom: 14px;
        }

        /* Result */
        .tg-result-card {
          position: relative;
          overflow: hidden;
          border-radius: 20px;
          padding: 1px;
          margin: 10px 0 16px;
          background: linear-gradient(135deg, #2563eb, #06b6d4, #8b5cf6);
          background-size: 220% 220%;
          animation: tgFadeUp .45s ease both, tgGradientMove 10s ease infinite;
          box-shadow: 0 20px 52px rgba(37, 99, 235, .16);
        }
        .tg-result-card-inner {
          border-radius: 19px;
          padding: 22px;
          background: #ffffff;
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
          font-size: 18px;
          line-height: 1.72;
          margin-top: 12px;
        }
        .tg-trust-pill {
          min-width: 116px;
          text-align: right;
          border: 1px solid #bfdbfe;
          background: #eff6ff;
          border-radius: 14px;
          padding: 10px 12px;
        }
        .tg-kpi-card {
          min-height: 104px;
          padding: 16px;
          margin-bottom: 12px;
          border-radius: var(--tg-radius);
          border: 1px solid var(--tg-border);
          background: #ffffff;
          box-shadow: var(--tg-shadow-soft);
        }
        .tg-kpi-label {
          color: var(--tg-soft);
          text-transform: uppercase;
          font-size: 12px;
          font-weight: 820;
          letter-spacing: .06em;
        }
        .tg-kpi-value {
          color: var(--tg-text);
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
          padding: 7px 10px;
          border: 1px solid transparent;
          font-size: 12px;
          line-height: 1;
          font-weight: 850;
          letter-spacing: .04em;
        }
        .tg-badge-safe { color: #166534; background: #dcfce7; border-color: #bbf7d0; }
        .tg-badge-low { color: #3f6212; background: #ecfccb; border-color: #d9f99d; }
        .tg-badge-medium { color: #92400e; background: #fef3c7; border-color: #fde68a; }
        .tg-badge-high { color: #9f1239; background: #ffe4e6; border-color: #fecdd3; }
        .tg-badge-critical { color: #991b1b; background: #fee2e2; border-color: #fecaca; }
        .tg-badge-unknown { color: #334155; background: #f1f5f9; border-color: #cbd5e1; }
        .tg-warning-card {
          border: 1px solid #fed7aa;
          background: #fff7ed;
          color: #9a3412;
          border-radius: var(--tg-radius);
          padding: 14px 16px;
          margin: 12px 0 16px;
          font-size: 15px;
          line-height: 1.55;
          animation: tgFadeUp .45s ease both;
        }
        .tg-debug-box {
          background: #f8fafc;
          border: 1px solid var(--tg-border);
          border-radius: var(--tg-radius);
          padding: 14px;
          color: var(--tg-muted);
        }
        .tg-footer {
          color: var(--tg-soft);
          border-top: 1px solid var(--tg-border);
          margin-top: 22px;
          padding-top: 14px;
          font-size: 13px;
          text-align: center;
        }

        /* Streamlit form controls */
        label, .stMarkdown, p, span, div {
          letter-spacing: 0;
        }
        div[data-testid="stTextArea"] label,
        div[data-testid="stTextInput"] label,
        div[data-testid="stSelectbox"] label,
        div[data-testid="stRadio"] label,
        div[data-testid="stCheckbox"] label,
        div[data-testid="stSlider"] label {
          color: var(--tg-text) !important;
          font-size: 14px !important;
          font-weight: 720 !important;
        }
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stTextInput"] input {
          color: var(--tg-text) !important;
          background: #ffffff !important;
          border: 1px solid var(--tg-border-strong) !important;
          border-radius: 12px !important;
          box-shadow: 0 1px 2px rgba(15, 23, 42, .04) !important;
          font-size: 16px !important;
          line-height: 1.55 !important;
        }
        div[data-testid="stTextArea"] textarea::placeholder,
        div[data-testid="stTextInput"] input::placeholder {
          color: #64748b !important;
        }
        div[data-testid="stTextArea"] textarea:focus,
        div[data-testid="stTextInput"] input:focus {
          border-color: var(--tg-primary) !important;
          box-shadow: 0 0 0 3px rgba(37, 99, 235, .12) !important;
        }
        div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
          color: var(--tg-text) !important;
          background: #ffffff !important;
          border-color: var(--tg-border-strong) !important;
          border-radius: 12px !important;
          min-height: 42px;
        }
        div[data-testid="stSelectbox"] [data-baseweb="select"],
        div[data-testid="stSelectbox"] [data-baseweb="select"] *,
        div[data-testid="stTextInput"] *,
        div[data-testid="stTextArea"] * {
          -webkit-text-fill-color: var(--tg-text) !important;
        }
        div[data-testid="stSelectbox"] [data-baseweb="select"] span,
        div[data-testid="stSelectbox"] [data-baseweb="select"] input {
          color: var(--tg-text) !important;
          -webkit-text-fill-color: var(--tg-text) !important;
        }
        div[data-baseweb="popover"],
        div[data-baseweb="popover"] * {
          color: var(--tg-text) !important;
          background-color: #ffffff !important;
        }
        ul[role="listbox"] {
          background: #ffffff !important;
          border: 1px solid var(--tg-border) !important;
          border-radius: 12px !important;
          box-shadow: var(--tg-shadow) !important;
        }
        li[role="option"] {
          color: var(--tg-text) !important;
          background: #ffffff !important;
          font-size: 15px !important;
        }
        li[role="option"]:hover,
        li[aria-selected="true"] {
          background: #eff6ff !important;
          color: #1d4ed8 !important;
        }
        div[data-testid="stRadio"] label,
        div[data-testid="stCheckbox"] label,
        div[data-testid="stToggle"] label {
          color: var(--tg-text) !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label,
        section[data-testid="stSidebar"] div[data-testid="stCheckbox"] label,
        section[data-testid="stSidebar"] div[data-testid="stToggle"] label,
        section[data-testid="stSidebar"] div[data-testid="stSlider"] label {
          color: #e5eefb !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stTextInput"] input,
        section[data-testid="stSidebar"] div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
          background: rgba(255, 255, 255, .96) !important;
          color: #0f172a !important;
          border-color: rgba(255, 255, 255, .2) !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stTextInput"] *,
        section[data-testid="stSidebar"] div[data-testid="stSelectbox"] [data-baseweb="select"],
        section[data-testid="stSidebar"] div[data-testid="stSelectbox"] [data-baseweb="select"] * {
          color: #0f172a !important;
          -webkit-text-fill-color: #0f172a !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stSelectbox"] [data-baseweb="select"] span,
        section[data-testid="stSidebar"] div[data-testid="stSelectbox"] [data-baseweb="select"] input {
          color: #0f172a !important;
          -webkit-text-fill-color: #0f172a !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stRadio"] *,
        section[data-testid="stSidebar"] div[data-testid="stCheckbox"] *,
        section[data-testid="stSidebar"] div[data-testid="stToggle"] *,
        section[data-testid="stSidebar"] div[data-testid="stSlider"] * {
          color: #e5eefb !important;
          -webkit-text-fill-color: unset !important;
        }
        .stButton > button {
          width: 100%;
          min-height: 50px;
          border: 0;
          color: #ffffff !important;
          border-radius: 13px;
          background: linear-gradient(135deg, #2563eb 0%, #06b6d4 52%, #8b5cf6 100%);
          background-size: 180% 180%;
          box-shadow: 0 14px 34px rgba(37, 99, 235, .24);
          font-size: 17px;
          font-weight: 850;
          animation: tgGradientMove 12s ease infinite;
          transition: transform .18s ease, box-shadow .18s ease;
        }
        .stButton > button:hover {
          transform: translateY(-1px);
          box-shadow: 0 18px 42px rgba(37, 99, 235, .3);
          color: #ffffff !important;
        }
        .stButton > button:focus {
          box-shadow: 0 0 0 4px rgba(37, 99, 235, .16), 0 14px 34px rgba(37, 99, 235, .24);
        }
        div[data-testid="stSlider"] [role="slider"] {
          background: var(--tg-primary) !important;
          border-color: var(--tg-primary) !important;
        }
        .stTabs [data-baseweb="tab-list"] {
          gap: 8px;
          border-bottom: 1px solid var(--tg-border);
          margin-top: 8px;
        }
        .stTabs [data-baseweb="tab"] {
          color: var(--tg-muted) !important;
          border-radius: 12px 12px 0 0;
          padding: 10px 14px;
          font-size: 15px;
          font-weight: 800;
        }
        .stTabs [aria-selected="true"] {
          color: #1d4ed8 !important;
          background: #eff6ff;
          border-bottom: 2px solid var(--tg-primary);
        }
        div[data-testid="stDataFrame"] {
          border: 1px solid var(--tg-border);
          border-radius: var(--tg-radius);
          overflow: hidden;
          background: #ffffff;
        }
        div[data-testid="stMetric"] {
          background: #ffffff;
          border: 1px solid var(--tg-border);
          border-radius: var(--tg-radius);
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
          color: #0f172a !important;
          background: #f8fafc !important;
          border-radius: 12px !important;
        }

        @media (max-width: 900px) {
          .tg-split-grid {
            grid-template-columns: 1fr;
          }
          .tg-product-header {
            padding: 22px;
          }
          .tg-hero-title {
            font-size: 36px;
          }
          .tg-result-header {
            flex-direction: column;
          }
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
