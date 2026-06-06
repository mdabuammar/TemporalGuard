"""Premium Streamlit styling for TemporalGuard."""

from __future__ import annotations

import streamlit as st


def inject_premium_css() -> None:
    st.markdown(
        """
        <style>
        :root {
          --tg-bg: #020617;
          --tg-bg-soft: #050816;
          --tg-panel: rgba(15, 23, 42, 0.74);
          --tg-panel-strong: rgba(15, 23, 42, 0.9);
          --tg-border: rgba(148, 163, 184, 0.22);
          --tg-border-hot: rgba(56, 189, 248, 0.36);
          --tg-text: #f8fafc;
          --tg-muted: #cbd5e1;
          --tg-soft: #94a3b8;
          --tg-faint: #64748b;
          --tg-cyan: #38bdf8;
          --tg-blue: #2563eb;
          --tg-violet: #8b5cf6;
          --tg-emerald: #22c55e;
          --tg-amber: #f59e0b;
          --tg-rose: #fb7185;
          --tg-red: #ef4444;
          --tg-radius: 8px;
        }

        @keyframes tgFadeUp {
          from { opacity: 0; transform: translateY(14px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes tgGlow {
          0%, 100% { transform: translate3d(0, 0, 0) scale(1); opacity: .72; }
          50% { transform: translate3d(16px, -10px, 0) scale(1.04); opacity: .94; }
        }
        @keyframes tgGradientMove {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }
        @keyframes tgPulse {
          0%, 100% { box-shadow: 0 0 0 0 rgba(251, 113, 133, 0.28); }
          50% { box-shadow: 0 0 0 7px rgba(251, 113, 133, 0); }
        }

        html, body, .stApp {
          font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          color: var(--tg-text);
          background:
            radial-gradient(circle at top left, rgba(56, 189, 248, 0.16), transparent 30%),
            radial-gradient(circle at top right, rgba(168, 85, 247, 0.14), transparent 32%),
            linear-gradient(135deg, #020617 0%, #050816 45%, #0f172a 100%);
        }

        .stApp::before {
          content: "";
          position: fixed;
          inset: -20%;
          pointer-events: none;
          background:
            radial-gradient(circle at 18% 18%, rgba(34, 211, 238, 0.13), transparent 26%),
            radial-gradient(circle at 74% 10%, rgba(139, 92, 246, 0.13), transparent 28%),
            radial-gradient(circle at 80% 80%, rgba(20, 184, 166, 0.08), transparent 26%);
          filter: blur(8px);
          animation: tgGlow 16s ease-in-out infinite;
          z-index: 0;
        }

        .stApp > div { position: relative; z-index: 1; }
        #MainMenu, footer, header { visibility: hidden; }
        .block-container {
          max-width: 1180px;
          padding-top: 2rem;
          padding-bottom: 3rem;
        }

        section[data-testid="stSidebar"] {
          background: linear-gradient(180deg, #020617 0%, #07111f 52%, #0f172a 100%);
          border-right: 1px solid rgba(148, 163, 184, 0.16);
          box-shadow: 18px 0 55px rgba(2, 6, 23, 0.32);
        }
        section[data-testid="stSidebar"] * { color: var(--tg-muted); }
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] label { color: var(--tg-text) !important; }
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: var(--tg-soft); }

        .tg-app-shell { animation: tgFadeUp .55s ease both; }
        .tg-hero {
          display: grid;
          grid-template-columns: minmax(0, 1.4fr) minmax(280px, .78fr);
          gap: 18px;
          align-items: stretch;
          margin-bottom: 18px;
        }
        .tg-card,
        .tg-glass-card {
          position: relative;
          background: linear-gradient(180deg, rgba(15, 23, 42, 0.78), rgba(15, 23, 42, 0.58));
          border: 1px solid var(--tg-border);
          border-radius: var(--tg-radius);
          box-shadow: 0 22px 70px rgba(2, 6, 23, 0.34);
          backdrop-filter: blur(20px);
          padding: 22px;
          animation: tgFadeUp .55s ease both;
        }
        .tg-card:hover,
        .tg-kpi-card:hover {
          transform: translateY(-2px);
          border-color: rgba(56, 189, 248, 0.34);
          box-shadow: 0 26px 80px rgba(2, 6, 23, 0.42);
        }
        .tg-card, .tg-kpi-card, .tg-result-card, button {
          transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease, background .18s ease;
        }

        .tg-hero-title {
          margin: 0 0 12px;
          color: var(--tg-text);
          font-size: 48px;
          line-height: 1;
          font-weight: 850;
          letter-spacing: 0;
        }
        .tg-hero-subtitle {
          max-width: 760px;
          color: var(--tg-muted);
          font-size: 17px;
          line-height: 1.65;
          margin: 0 0 18px;
        }
        .tg-chip {
          display: inline-flex;
          align-items: center;
          min-height: 30px;
          padding: 6px 10px;
          margin: 0 7px 8px 0;
          border-radius: 999px;
          border: 1px solid rgba(56, 189, 248, 0.24);
          background: rgba(15, 23, 42, 0.7);
          color: #dbeafe;
          font-size: 12px;
          font-weight: 720;
          letter-spacing: .01em;
        }

        .tg-result-card {
          position: relative;
          overflow: hidden;
          border-radius: var(--tg-radius);
          padding: 1px;
          margin: 18px 0;
          background: linear-gradient(135deg, #38bdf8, #2563eb, #8b5cf6, #22d3ee);
          background-size: 280% 280%;
          animation: tgFadeUp .55s ease both, tgGradientMove 9s ease infinite;
          box-shadow: 0 28px 90px rgba(37, 99, 235, 0.2);
        }
        .tg-result-card-inner {
          border-radius: var(--tg-radius);
          padding: 22px;
          background: linear-gradient(180deg, rgba(2, 6, 23, 0.92), rgba(15, 23, 42, 0.86));
        }
        .tg-result-header {
          display: flex;
          justify-content: space-between;
          gap: 14px;
          align-items: flex-start;
          margin-bottom: 16px;
        }
        .tg-answer-text {
          color: var(--tg-text);
          font-size: 18px;
          line-height: 1.7;
          margin-top: 12px;
        }

        .tg-kpi-grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 12px;
          margin: 16px 0 18px;
        }
        .tg-kpi-card {
          min-height: 118px;
          padding: 17px;
          border-radius: var(--tg-radius);
          border: 1px solid var(--tg-border);
          background: linear-gradient(180deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.7));
          box-shadow: 0 18px 48px rgba(2, 6, 23, 0.24);
        }
        .tg-kpi-label {
          color: var(--tg-soft);
          text-transform: uppercase;
          font-size: 11px;
          font-weight: 780;
          letter-spacing: .08em;
        }
        .tg-kpi-value {
          color: var(--tg-text);
          font-size: 22px;
          font-weight: 830;
          line-height: 1.18;
          margin-top: 10px;
          overflow-wrap: anywhere;
        }
        .tg-kpi-caption {
          color: var(--tg-soft);
          font-size: 12px;
          line-height: 1.45;
          margin-top: 8px;
        }
        .tg-kpi-card::after {
          content: "";
          display: block;
          width: 46px;
          height: 2px;
          margin-top: 14px;
          border-radius: 999px;
          background: linear-gradient(90deg, #38bdf8, #8b5cf6);
        }

        .tg-badge {
          display: inline-flex;
          align-items: center;
          white-space: nowrap;
          border-radius: 999px;
          padding: 7px 10px;
          border: 1px solid transparent;
          font-size: 11px;
          line-height: 1;
          font-weight: 850;
          letter-spacing: .055em;
        }
        .tg-badge-safe { color: #bbf7d0; background: rgba(34, 197, 94, .12); border-color: rgba(34, 197, 94, .32); }
        .tg-badge-low { color: #d9f99d; background: rgba(132, 204, 22, .12); border-color: rgba(132, 204, 22, .32); }
        .tg-badge-medium { color: #fde68a; background: rgba(245, 158, 11, .13); border-color: rgba(245, 158, 11, .34); }
        .tg-badge-high { color: #fecdd3; background: rgba(251, 113, 133, .13); border-color: rgba(251, 113, 133, .38); animation: tgPulse 2.8s ease-in-out infinite; }
        .tg-badge-critical { color: #fecaca; background: rgba(239, 68, 68, .15); border-color: rgba(239, 68, 68, .45); animation: tgPulse 2.4s ease-in-out infinite; }
        .tg-badge-unknown { color: #cbd5e1; background: rgba(148, 163, 184, .12); border-color: rgba(148, 163, 184, .28); }

        .tg-warning-card {
          border: 1px solid rgba(251, 113, 133, 0.32);
          background: linear-gradient(180deg, rgba(127, 29, 29, .28), rgba(15, 23, 42, .76));
          color: #fecdd3;
          border-radius: var(--tg-radius);
          padding: 14px 16px;
          margin: 12px 0 18px;
          animation: tgFadeUp .55s ease both;
        }
        .tg-section-title {
          color: var(--tg-text);
          font-size: 13px;
          font-weight: 820;
          letter-spacing: .08em;
          text-transform: uppercase;
          margin: 8px 0 12px;
        }
        .tg-muted { color: var(--tg-soft); }
        .tg-split-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 14px;
          margin-bottom: 14px;
        }
        .tg-footer {
          color: var(--tg-soft);
          border-top: 1px solid rgba(148, 163, 184, 0.16);
          margin-top: 26px;
          padding-top: 16px;
          font-size: 13px;
          text-align: center;
        }
        .tg-debug-box {
          background: rgba(2, 6, 23, .74);
          border: 1px solid rgba(148, 163, 184, .18);
          border-radius: var(--tg-radius);
          padding: 14px;
          color: var(--tg-muted);
        }

        div[data-testid="stTextArea"] textarea,
        div[data-testid="stTextInput"] input {
          color: var(--tg-text) !important;
          background: rgba(2, 6, 23, 0.62) !important;
          border: 1px solid rgba(148, 163, 184, 0.24) !important;
          border-radius: var(--tg-radius) !important;
          box-shadow: inset 0 1px 0 rgba(255,255,255,.03);
        }
        div[data-testid="stTextArea"] textarea:focus,
        div[data-testid="stTextInput"] input:focus {
          border-color: rgba(56, 189, 248, .58) !important;
          box-shadow: 0 0 0 1px rgba(56, 189, 248, .28) !important;
        }
        div[data-testid="stSelectbox"] div,
        div[data-testid="stRadio"] label,
        div[data-testid="stCheckbox"] label,
        div[data-testid="stSlider"] label {
          color: var(--tg-muted) !important;
        }
        .stButton > button {
          width: 100%;
          border: 0;
          color: #f8fafc;
          border-radius: var(--tg-radius);
          background: linear-gradient(135deg, #38bdf8 0%, #2563eb 45%, #8b5cf6 100%);
          box-shadow: 0 14px 36px rgba(37, 99, 235, .34);
          font-weight: 820;
        }
        .stButton > button:hover {
          transform: translateY(-1px);
          box-shadow: 0 18px 44px rgba(56, 189, 248, .28);
          color: #ffffff;
        }
        button[kind="secondary"] {
          background: rgba(15, 23, 42, .82) !important;
          border: 1px solid rgba(148, 163, 184, .22) !important;
        }
        .stTabs [data-baseweb="tab-list"] {
          gap: 8px;
          border-bottom: 1px solid rgba(148, 163, 184, .16);
        }
        .stTabs [data-baseweb="tab"] {
          color: var(--tg-soft);
          border-radius: var(--tg-radius) var(--tg-radius) 0 0;
          padding: 10px 14px;
        }
        .stTabs [aria-selected="true"] {
          color: var(--tg-text) !important;
          background: rgba(56, 189, 248, .10);
          border-bottom: 2px solid #38bdf8;
        }
        div[data-testid="stDataFrame"] {
          border: 1px solid rgba(148, 163, 184, .18);
          border-radius: var(--tg-radius);
          overflow: hidden;
          background: rgba(15, 23, 42, .78);
        }
        pre, code {
          color: #dbeafe !important;
          background: rgba(2, 6, 23, .76) !important;
          border-radius: var(--tg-radius) !important;
        }

        @media (max-width: 900px) {
          .tg-hero,
          .tg-split-grid,
          .tg-kpi-grid {
            grid-template-columns: 1fr;
          }
          .tg-hero-title { font-size: 38px; }
          .block-container { padding-left: 1rem; padding-right: 1rem; }
          .tg-result-header { flex-direction: column; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
