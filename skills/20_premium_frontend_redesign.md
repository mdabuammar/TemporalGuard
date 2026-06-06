# Skill 20: Premium Frontend Redesign

## Purpose

This skill upgrades the TemporalGuard frontend into a world-class, modern, premium, animated, portfolio-ready AI product dashboard.

The current frontend works functionally, but it looks too basic and Streamlit-default. This skill focuses only on visual design, user experience, smooth interaction, and product-level polish.

The goal is to make TemporalGuard look like a real AI reliability product, not a normal student project or default Streamlit app.

---

## Main Design Goal

The frontend must look:

```text
world-class
premium
modern
dark
minimal
smooth
animated
high-tech
clean
professional
AI SaaS product style
research product style
not default Streamlit
not regular AI-generated frontend
not plain HTML-looking
```

The UI should feel like a real product from an advanced AI company.

Visual inspiration:

```text
AI observability dashboard
LLM evaluation platform
trust and safety control panel
cybersecurity analytics dashboard
modern dark SaaS dashboard
developer tools dashboard
AI research console
```

---

## Important Rule

This skill is for frontend redesign only.

Do not change:

```text
backend logic
pipeline logic
skill modules
evaluation logic
search provider logic
LLM provider logic
tests unrelated to frontend
```

Only improve:

```text
app.py
frontend helper functions
frontend styles
frontend components
frontend visual layout
demo/mock data richness
```

---

## Required Files

Update or create:

```text
app.py
src/temporalguard/frontend/streamlit_helpers.py
src/temporalguard/frontend/styles.py
src/temporalguard/frontend/components.py
tests/test_streamlit_helpers.py
```

If `styles.py` or `components.py` already exists, improve them.

If they do not exist, create them.

---

## Visual Identity

### Product Name

```text
TemporalGuard
```

### Product Tagline

```text
Time-aware reliability layer for detecting and correcting outdated LLM responses.
```

### Visual Mood

The design should feel like:

```text
dark intelligence
temporal signal analysis
AI safety cockpit
reliability control center
premium research dashboard
```

---

## Color System

Use a dark theme with gradient accents.

### Main Background

Use dark black/navy gradient:

```text
#020617
#050816
#0f172a
#111827
```

Recommended background:

```css
background:
radial-gradient(circle at top left, rgba(56, 189, 248, 0.16), transparent 30%),
radial-gradient(circle at top right, rgba(168, 85, 247, 0.14), transparent 32%),
linear-gradient(135deg, #020617 0%, #050816 45%, #0f172a 100%);
```

### Primary Gradient

Use blue, cyan, violet:

```text
#38bdf8
#2563eb
#8b5cf6
#a855f7
```

Recommended gradient:

```css
linear-gradient(135deg, #38bdf8 0%, #2563eb 45%, #8b5cf6 100%)
```

### Accent Gradient

Use cyan, emerald, violet:

```text
#22d3ee
#14b8a6
#8b5cf6
```

### Card Background

Use glassmorphism:

```text
rgba(15, 23, 42, 0.72)
rgba(30, 41, 59, 0.65)
```

### Border

```text
rgba(148, 163, 184, 0.22)
rgba(56, 189, 248, 0.24)
```

### Text

```text
main text: #f8fafc
secondary text: #cbd5e1
muted text: #94a3b8
soft text: #64748b
```

### Status Colors

```text
safe: #22c55e
low: #84cc16
medium: #f59e0b
high: #fb7185
critical: #ef4444
unknown: #94a3b8
```

---

## Typography Requirements

Use clean, premium typography.

Because Streamlit cannot easily load custom font safely without extra complexity, use CSS font stack:

```css
font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
```

Typography style:

```text
large bold hero title
small uppercase section labels
clean body text
compact metric labels
monospace only for raw JSON/debug sections
```

Avoid:

```text
too much bold everywhere
oversized paragraphs
messy font sizes
childish emojis
```

---

## Animation Requirements

Add smooth CSS animation. It should feel premium, not distracting.

Use animations such as:

```text
soft fade-in
slide-up reveal
floating glow background
animated gradient border
hover lift effect on cards
subtle pulse for active risk badge
smooth tab/card transition
```

Required CSS animations:

```css
@keyframes tgFadeUp
@keyframes tgGlow
@keyframes tgGradientMove
@keyframes tgPulse
```

Animation behavior:

```text
hero card fades in
result card slides up
metric cards lift on hover
risk badge softly pulses only for high/critical
background glow slowly moves
buttons have smooth hover effect
```

Do not make animation too much. It should be smooth and professional.

---

## Layout Requirements

Use a modern dashboard layout.

### Overall Structure

```text
Dark background
Left sidebar control panel
Main content area
Hero/status header
Question analysis card
Corrected answer spotlight card
KPI cards
Tabbed analysis panel
Footer
```

### Top Section

Use a two-column hero layout:

Left side:

```text
TemporalGuard title
tagline
feature chips
short explanation
```

Right side:

```text
System status card
pipeline mode
trust score placeholder
status badge
```

### Input Section

The input area should look like a command center card.

Fields:

```text
Question input
Optional base answer
Run button
```

The run button should look premium with gradient background.

Button style:

```text
rounded
gradient
hover lift
glow
clear label
```

Text areas should look dark, polished, and not default gray.

---

## Sidebar Requirements

The sidebar must also be styled.

It should include:

```text
TemporalGuard mini-brand
Run mode
Sample question
Report type
Advanced options
API URL
Small project status
```

Sidebar should feel like a control panel, not default Streamlit.

Use dark sidebar styling:

```css
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617 0%, #0f172a 100%);
    border-right: 1px solid rgba(148, 163, 184, 0.16);
}
```

---

## Required UI Components

Create reusable frontend components if possible.

Recommended component functions in:

```text
src/temporalguard/frontend/components.py
```

Suggested functions:

```python
def render_hero():
    ...

def render_status_card(summary: dict):
    ...

def render_result_card(final_answer: str, dashboard_summary: dict):
    ...

def render_metric_grid(metrics: list[dict]):
    ...

def render_warning_card(message: str):
    ...

def render_footer():
    ...
```

Keep these functions simple. Do not over-engineer.

---

## Required CSS Classes

Create these CSS classes in:

```text
src/temporalguard/frontend/styles.py
```

Required classes:

```text
tg-app-shell
tg-hero
tg-hero-title
tg-hero-subtitle
tg-chip
tg-card
tg-glass-card
tg-result-card
tg-result-header
tg-answer-text
tg-kpi-grid
tg-kpi-card
tg-kpi-label
tg-kpi-value
tg-kpi-caption
tg-badge
tg-badge-safe
tg-badge-low
tg-badge-medium
tg-badge-high
tg-badge-critical
tg-badge-unknown
tg-warning-card
tg-section-title
tg-muted
tg-split-grid
tg-footer
tg-debug-box
```

Required function:

```python
def inject_premium_css():
    ...
```

This function must inject all design CSS using:

```python
st.markdown(css, unsafe_allow_html=True)
```

---

## Result Card Requirements

The corrected answer card is the most important UI element.

It must show:

```text
badge
corrected answer
trust score
risk label
safety status
warning
```

Design it like a premium insight card.

Example layout:

```text
[OUTDATED - CORRECTED]       Trust 0.93
Corrected Answer
Python 3.10 is not the latest stable Python version...
Risk: medium_risk · Safety: show_with_caution
Warning: This answer was updated using checked evidence...
```

The card should use:

```text
gradient border
dark glass background
large readable answer
soft glow
smooth fade-up animation
```

---

## KPI Card Requirements

Metric cards should look modern and compact.

Cards:

```text
Temporal Category
Outdatedness
Verification
Correction
Trust Score
Freshness Score
```

Each KPI card must include:

```text
small uppercase label
large value
short caption
optional accent line
```

KPI cards should animate slightly on hover.

---

## Tabs Requirements

Use tabs:

```text
Overview
Claims
Evidence
Report
Debug
```

Tab content should be card-based.

### Overview Tab

Show original answer and corrected answer side by side.

Use:

```text
Original Answer card
Corrected Answer card
Executive Summary card
```

### Claims Tab

Show a clean table.

If possible, use `st.dataframe` with compact rows.

Columns:

```text
Claim ID
Claim Text
Claim Type
Verification
Risk
Claim Value
Evidence Value
Correction
```

### Evidence Tab

Show a clean evidence table.

Columns:

```text
Evidence ID
Claim ID
Title
Publisher
Type
Freshness
Score
URL
```

### Report Tab

Show thesis-ready sections:

```text
Executive Summary
Problem Observed
Temporal Failure Type
Evidence Quality
System Decision
Research Value
```

### Debug Tab

Show:

```text
Pipeline Status
Warnings
Errors
Raw JSON expander
```

Raw JSON must be hidden by default.

---

## Demo Mode Requirements

Demo/mock mode must look rich and complete.

Add high-quality demo outputs for at least:

```text
latest Python version
binary search
visa rule active
2014 FIFA World Cup winner
OpenAI CEO
OpenAI API usage
```

Each demo output should include:

```text
temporal_detection
claims
evidence
freshness
verification
outdatedness
correction
risk_label
report
```

Do not leave claims/evidence empty in demo mode unless the example is truly static.

This is important because screenshots need to look complete.

---

## Backend Modes

Support three modes:

```text
Demo/mock mode
Local pipeline
API backend
```

### Demo/mock mode

Must always work.

### Local pipeline

Call:

```python
from temporalguard.pipeline.orchestrator import run_temporalguard_pipeline
```

### API backend

POST to:

```text
/api/analyze or /analyze
```

Use the sidebar URL.

If API fails, show a polished error card.

---

## Error UI Requirements

Do not show ugly stack traces in normal mode.

Show a clean error card:

```text
TemporalGuard could not complete the analysis.
Check whether the pipeline or API backend is running.
```

If debug is enabled, then show details inside expander.

---

## Streamlit Default UI Reduction

Hide or reduce default Streamlit look where safe:

```css
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1180px;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
```

Style common widgets:

```text
text area
select box
radio
button
tabs
dataframe container
```

Do not break functionality.

---

## Helper Functions

In:

```text
src/temporalguard/frontend/streamlit_helpers.py
```

Keep or improve these functions:

```python
def safe_get(data: dict, path: list[str], default=None):
    ...

def risk_to_css_class(risk_label: str) -> str:
    ...

def badge_to_css_class(badge: str) -> str:
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

Add helper functions if needed, but keep them simple and testable.

---

## Testing Requirements

Only test helper logic, not visual rendering.

Tests must cover:

```text
safe_get
risk_to_css_class
badge_to_css_class
get_final_answer
get_dashboard_summary
build_metric_cards
claims_to_table_rows
evidence_to_table_rows
build_demo_output for all sample questions
missing fields do not crash
```

Tests must not require Streamlit rendering.

---

## Manual UI Check Requirement

After implementation, run:

```bash
pytest tests/test_streamlit_helpers.py
pytest
python -m py_compile app.py src/temporalguard/frontend/*.py
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

Manual check:

```text
Dashboard loads
Dark theme visible
Hero looks premium
Sidebar looks styled
Result card looks premium
KPI cards look modern
Tabs work
Demo mode works
Claims table appears
Evidence table appears
Raw JSON hidden by default
No ugly stack trace visible
```

---

## Strict Do Not Do

Do not:

```text
change backend pipeline logic
change core skill logic
add heavy frontend frameworks
add React
add random images
use childish emoji-heavy design
use default Streamlit only styling
make it cluttered
make everything bright
hard-code API keys
expose secrets
break demo mode
break tests
```

---

## Expected Result

After this skill, the frontend should look like:

```text
a real AI product dashboard
a premium LLM reliability platform
a professional thesis demonstration tool
a GitHub portfolio-ready project
```

It should not look like:

```text
a normal Streamlit homework app
a plain HTML page
a default AI-generated interface
a basic form and table page
```

---

## Prompt for Claude or Codex Agent

You are implementing Skill 20 for TemporalGuard.

Read `skills/20_premium_frontend_redesign.md` carefully.

Your task is to redesign the existing Streamlit frontend into a premium, world-class, dark, modern AI product dashboard.

This is a frontend redesign only. Do not change backend logic, pipeline logic, skill modules, search logic, evaluation logic, or API logic.

Update or create:

1. `app.py`
2. `src/temporalguard/frontend/streamlit_helpers.py`
3. `src/temporalguard/frontend/styles.py`
4. `src/temporalguard/frontend/components.py`
5. `tests/test_streamlit_helpers.py`

Design requirements:

* Make the UI dark, premium, modern, minimal, and animated.
* Use black/navy background with blue/cyan/violet gradient accents.
* Use glassmorphism cards, gradient borders, polished badges, KPI cards, and smooth CSS animations.
* Avoid regular default Streamlit look.
* Make it look like a real AI SaaS dashboard or LLM reliability monitoring product.
* Add a compact premium hero section.
* Add a styled sidebar control panel.
* Add a strong corrected-answer spotlight card.
* Add modern metric/KPI cards.
* Add tabs: Overview, Claims, Evidence, Report, Debug.
* Put Original Answer and Corrected Answer side by side in Overview.
* Make Claims and Evidence tabs look clean and data-rich.
* Keep raw JSON hidden inside an expander.
* Add a polished footer.
* Demo/mock mode must work without backend/API.
* Demo/mock mode must include rich outputs for multiple sample questions.
* Local pipeline mode must still work.
* API backend mode must still work.
* Handle missing fields safely.
* Show clean error cards instead of ugly stack traces.
* Do not expose secrets or API keys.
* Do not add heavy frontend frameworks.
* Keep pure Streamlit + CSS.

Animation requirements:

* Add soft fade-up animation.
* Add subtle background glow animation.
* Add hover lift effect for cards.
* Add animated gradient border for result card.
* Add subtle pulse for high/critical risk badges only.
* Keep animations smooth and professional, not distracting.

Testing requirements:

* Tests should cover helper functions only.
* Tests must not require Streamlit rendering.
* Run:

  * `pytest tests/test_streamlit_helpers.py`
  * `pytest`
  * `python -m py_compile app.py src/temporalguard/frontend/*.py`

Manual check:

* Run `streamlit run app.py`.
* Open localhost.
* Confirm the UI looks premium and not default Streamlit.
* Confirm Demo/mock mode works.
* Confirm Claims, Evidence, Report, and Debug tabs work.

At the end, report:

1. Files created/modified
2. Design improvements made
3. Demo mode improvements
4. Test results
5. Manual localhost check result
6. Assumptions

Important: prioritize visual quality. The current frontend looks too basic. Make it look like a real premium AI reliability product dashboard.
