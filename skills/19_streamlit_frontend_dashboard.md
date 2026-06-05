# Skill 19: Streamlit Frontend Dashboard

## Purpose

This skill creates a clean, modern, minimal, and professional Streamlit dashboard for TemporalGuard.

The frontend must not look like a basic AI-generated Streamlit app. It should look polished enough for:

1. University thesis presentation
2. GitHub portfolio
3. Demo video
4. Recruiter/industry showcase
5. FAANG-style AI/ML engineering portfolio

The dashboard should make TemporalGuard easy to understand visually. It should clearly show how the system checks whether an LLM answer is outdated, verifies evidence, generates a corrected answer, and labels risk.

---

## Design Goal

Build a frontend that feels:

```text
modern
minimal
clean
premium
research-grade
professional
easy to read
not crowded
not childish
not generic
```

The UI should look like a serious AI reliability product, not a simple classroom project.

The visual style should be similar to:

```text
AI observability dashboard
LLM evaluation dashboard
trust and safety monitoring tool
research system demo
modern SaaS analytics panel
```

---

## Core Task

Build a polished Streamlit app that calls TemporalGuard locally or through FastAPI.

The dashboard must let the user:

1. Enter a question.
2. Optionally enter a base LLM answer.
3. Run TemporalGuard.
4. See the corrected answer.
5. See whether the original answer was outdated.
6. See evidence and freshness information.
7. See claim-level verification.
8. See risk and uncertainty labels.
9. See a report summary for thesis/demo use.

---

## Suggested Project Files

Create:

```text
app.py
src/temporalguard/frontend/streamlit_helpers.py
tests/test_streamlit_helpers.py
```

Optional but recommended:

```text
src/temporalguard/frontend/styles.py
src/temporalguard/frontend/components.py
```

Only create optional files if they keep the code cleaner. Do not over-engineer.

---

## Required UI Layout

Use a clean wide layout:

```python
st.set_page_config(
    page_title="TemporalGuard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

The dashboard should use:

1. A sidebar for controls and sample questions.
2. A top hero section.
3. A final answer card.
4. Metric cards.
5. Tabs for details.
6. Tables for claims/evidence.
7. Expanders for technical JSON/debug info.

---

## Page Structure

### 1. Sidebar

The sidebar should contain:

```text
TemporalGuard logo/title
Short description
Run mode selector
Sample question selector
Report type selector
Advanced options
Run button
```

Run modes:

```text
Local pipeline
API backend
Demo/mock mode
```

Use `Demo/mock mode` if pipeline is not fully ready. This makes the frontend testable before backend completion.

Sidebar sample questions:

```text
What is the latest Python version?
Who is the CEO of OpenAI?
Who won the 2014 FIFA World Cup?
What is binary search?
Is this visa rule still active?
How do I use the OpenAI API in Python?
```

Advanced options:

```text
Show raw JSON
Show debug report
Use provided base answer
API backend URL
```

---

### 2. Hero Section

At the top of the main page, show a modern hero block:

Title:

```text
TemporalGuard
```

Subtitle:

```text
Time-aware reliability framework for detecting and correcting outdated LLM responses.
```

Small feature chips:

```text
Temporal Detection
Evidence Freshness
Claim Verification
Risk Labeling
Correction
```

The hero should look simple and clean using custom CSS.

---

### 3. Input Section

Use a card-like container for input.

Fields:

```text
User question
Optional base LLM answer
Run TemporalGuard button
```

Question input should be clear and large enough.

Base answer should be optional. If base answer is empty, the app may use the pipeline/LLM provider if available. If not available, show a helpful warning.

---

### 4. Final Result Section

This is the most important visible section.

Show a large clean card with:

```text
Corrected Answer
Dashboard Badge
Final Risk Label
Trust Score
Temporal Safety Status
User Warning
```

The corrected answer should be shown prominently.

Badge examples:

```text
SAFE
LOW RISK
OUTDATED - CORRECTED
CONTRADICTION - CORRECTED
PARTIALLY CORRECTED
UNVERIFIED
CRITICAL - VERIFY OFFICIAL SOURCE
UNKNOWN
```

Use color styling through CSS classes:

```text
safe = green
low risk = soft green
medium risk = amber
high risk = orange/red
critical risk = red
unknown = gray
```

Do not use too many bright colors. Keep the palette professional.

---

### 5. Metric Cards

Below the final result, show 4–6 small metric cards:

```text
Temporal Category
Outdatedness Status
Verification Status
Correction Status
Trust Score
Freshness Score
```

Each card should have:

```text
label
value
small explanation or icon
```

Example:

```text
Temporal Category
RECENT_ONLY
Requires fresh evidence
```

---

### 6. Tabs

Use tabs to organize details:

```text
Overview
Claims
Evidence
Report
Debug
```

### Tab 1: Overview

Show:

```text
Original Answer
Corrected Answer
Executive Summary
Main Issue
User Warning
```

### Tab 2: Claims

Show a clean table with:

```text
Claim ID
Claim Text
Claim Type
Verification Status
Risk Level
Claim Value
Evidence Value
Requires Correction
```

If no claims exist, show:

```text
No factual claims were extracted.
```

### Tab 3: Evidence

Show a clean table with:

```text
Evidence ID
Claim ID
Title
Publisher
Source Type
Freshness Label
Combined Score
URL
```

URLs should be clickable if possible.

If no evidence exists, show:

```text
No evidence was retrieved or evidence retrieval was skipped.
```

### Tab 4: Report

Show:

```text
Executive Summary
Thesis Summary
Correction Report
Freshness Note
Uncertainty Note
Safety Note
```

This tab should help the user take screenshots for thesis/report writing.

### Tab 5: Debug

Show:

```text
Pipeline Status
Missing Sections
Warnings
Errors
Raw JSON
```

Raw JSON should be hidden inside an expander by default.

---

## Visual Design Requirements

The frontend must use custom CSS through `st.markdown(..., unsafe_allow_html=True)`.

Use a minimal design system:

### Background

Use a soft neutral background:

```text
#f7f8fa
#f8fafc
#ffffff
```

### Cards

Cards should have:

```text
white background
rounded corners
soft border
subtle shadow
comfortable padding
```

### Typography

Use clean typography:

```text
large bold title
medium section headings
small muted descriptions
good spacing
```

### Color Palette

Use professional colors:

```text
primary: #2563eb or #0f766e
success: #16a34a
warning: #d97706
danger: #dc2626
critical: #991b1b
muted: #64748b
border: #e5e7eb
background: #f8fafc
text: #0f172a
```

Do not use childish colors. Do not use too many emojis.

### UI Style

Use:

```text
cards
badges
metric tiles
tabs
expanders
clean tables
```

Avoid:

```text
messy columns
too many emojis
huge blocks of text
raw JSON visible by default
default-looking Streamlit only UI
overcrowded layout
```

---

## Required Helper Functions

Create helper functions in:

```text
src/temporalguard/frontend/streamlit_helpers.py
```

Recommended functions:

```python
def safe_get(data: dict, path: list[str], default=None):
    ...

def format_badge(label: str) -> str:
    ...

def risk_to_css_class(risk_label: str) -> str:
    ...

def build_metric_cards(pipeline_output: dict) -> list[dict]:
    ...

def claims_to_table_rows(pipeline_output: dict) -> list[dict]:
    ...

def evidence_to_table_rows(pipeline_output: dict) -> list[dict]:
    ...

def get_final_answer(pipeline_output: dict) -> str:
    ...

def get_dashboard_summary(pipeline_output: dict) -> dict:
    ...

def get_pipeline_summary(pipeline_output: dict) -> dict:
    ...

def build_demo_output(question: str, base_answer: str | None = None) -> dict:
    ...
```

The helper functions must handle missing keys safely.

---

## Demo/Mock Mode Requirement

The frontend must work even if the backend pipeline is not fully implemented yet.

Add a `Demo/mock mode`.

Demo mode should return a realistic TemporalGuard-like output for sample questions.

Example for latest Python question:

```json
{
  "question": "What is the latest Python version?",
  "original_answer": "Python 3.10 is the latest stable version of Python.",
  "correction": {
    "corrected_answer": "Python 3.10 is not the latest stable Python version. Based on the checked evidence, Python 3.13.5 is listed as the latest release.",
    "correction_status": "corrected"
  },
  "risk_label": {
    "dashboard_badge": "OUTDATED - CORRECTED",
    "final_risk_label": "medium_risk",
    "trust_score": 0.93,
    "temporal_safety_status": "show_with_caution",
    "user_warning": "This answer was updated using checked evidence, but software versions can change again."
  }
}
```

This will let the user show the dashboard before all backend modules are finished.

---

## Backend Connection Modes

The dashboard should support three modes:

### 1. Demo/mock mode

Uses local mock output. No backend required.

### 2. Local pipeline mode

Imports and calls:

```python
from temporalguard.pipeline.orchestrator import run_temporalguard_pipeline
```

### 3. API backend mode

Calls FastAPI endpoint:

```text
POST /analyze
```

using the backend URL from sidebar.

If API fails, show a clean error message and do not crash.

---

## Error Handling Rules

The UI must not crash.

If something fails:

1. Show a clean error card.
2. Suggest what the user can do.
3. Keep the rest of the page usable.
4. Do not expose stack traces unless debug mode is enabled.

Example message:

```text
TemporalGuard could not complete the analysis. Please check whether the pipeline or API backend is running.
```

---

## Streamlit Styling Requirements

Implement a function:

```python
def inject_custom_css():
    ...
```

It should define CSS for:

```text
hero-card
result-card
metric-card
risk-badge
badge-safe
badge-low
badge-medium
badge-high
badge-critical
badge-unknown
section-title
muted-text
code-card
warning-card
```

Use HTML/CSS carefully and safely.

---

## App Behavior

### Initial Load

When the app opens:

* Show hero section.
* Show input panel.
* Show sample questions in sidebar.
* Do not run pipeline automatically unless user clicks run.

### After Run

Show:

1. Final result card
2. Metric cards
3. Tabs with details
4. Optional raw JSON

### Empty Question

If question is empty:

```text
Please enter a question before running TemporalGuard.
```

### Missing Base Answer

If base answer is empty and no LLM provider is configured:

```text
No base answer was provided. TemporalGuard can still run in demo mode, or you can paste an LLM answer manually.
```

---

## Testing Requirements

Create tests for helper functions only. Do not test Streamlit UI rendering directly.

Test:

1. `safe_get`
2. `risk_to_css_class`
3. `get_final_answer`
4. `claims_to_table_rows`
5. `evidence_to_table_rows`
6. `build_metric_cards`
7. `build_demo_output`

Tests should not require Streamlit.

---

## Quality Requirements

1. Clean modern UI.
2. Not default-looking Streamlit.
3. Works in demo mode.
4. Works with local pipeline when available.
5. Works with API backend when configured.
6. Safe with missing data.
7. Shows final answer clearly.
8. Shows risk badge clearly.
9. Shows claims and evidence tables.
10. Shows thesis-ready report summary.
11. Does not expose secrets.
12. Does not crash on missing pipeline fields.
13. Uses package name `temporalguard`.
14. Keeps code readable and not over-engineered.
15. Uses helper functions for data formatting.
16. Unit tests for helpers.

---

## Suggested `app.py` Structure

```python
import streamlit as st

from temporalguard.frontend.streamlit_helpers import (
    safe_get,
    inject_custom_css,
    build_demo_output,
    get_final_answer,
    get_dashboard_summary,
    get_pipeline_summary,
    claims_to_table_rows,
    evidence_to_table_rows,
    build_metric_cards,
)

def main():
    st.set_page_config(
        page_title="TemporalGuard",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    inject_custom_css()

    render_sidebar()
    render_hero()
    render_input_panel()
    render_results()

if __name__ == "__main__":
    main()
```

The agent can improve this structure, but must keep the app clean and understandable.

---

## Prompt for Claude or Codex Agent

You are implementing Skill 19 for TemporalGuard.

Read `skills/19_streamlit_frontend_dashboard.md` carefully and implement a clean, modern, minimal Streamlit dashboard.

This frontend must not look like a basic AI-generated Streamlit app. It should look like a polished AI reliability dashboard suitable for thesis presentation and GitHub portfolio.

Create:

1. `app.py`
2. `src/temporalguard/frontend/streamlit_helpers.py`
3. `tests/test_streamlit_helpers.py`

Optional only if useful:

4. `src/temporalguard/frontend/styles.py`
5. `src/temporalguard/frontend/components.py`

Requirements:

* Build a polished wide-layout Streamlit dashboard.
* Use custom CSS for cards, badges, metric tiles, and clean layout.
* Add hero section with title, subtitle, and feature chips.
* Add sidebar with sample questions, run mode, report type, and advanced options.
* Support three modes:

  * Demo/mock mode
  * Local pipeline mode
  * API backend mode
* Demo/mock mode must work even if backend pipeline is not ready.
* Input: user question and optional base LLM answer.
* Show final corrected answer in a prominent card.
* Show dashboard badge, final risk label, trust score, temporal safety status, and warning.
* Show metric cards for temporal category, outdatedness, verification, correction, trust, and freshness.
* Use tabs:

  * Overview
  * Claims
  * Evidence
  * Report
  * Debug
* Show claims table safely.
* Show evidence table safely.
* Show executive summary and thesis summary.
* Hide raw JSON inside an expander by default.
* Handle missing fields safely.
* Show clean error messages.
* Do not expose secrets or API keys.
* Do not hard-code real API keys.
* Keep code professional, readable, and not over-engineered.
* Use package name `temporalguard`.
* Write unit tests for helper functions only.
* Tests must not require Streamlit UI rendering.
* Run tests and fix all failures.

At the end, report:

1. Files created/modified
2. UI design summary
3. Helper logic summary
4. Test result
5. Assumptions

Important: make the frontend visually clean, modern, minimal, and portfolio-ready. Do not create a regular plain Streamlit UI.
