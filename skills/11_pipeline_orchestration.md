# Skill 11: Pipeline Orchestration

## Purpose

This skill connects all TemporalGuard skills into one complete end-to-end pipeline.

TemporalGuard must run in a controlled order:

1. Generate or receive the base LLM answer.
2. Detect whether the question is time-sensitive.
3. Extract factual claims.
4. Retrieve evidence when needed.
5. Score source freshness.
6. Verify claims.
7. Detect whether the whole answer is outdated.
8. Generate correction if needed.
9. Label uncertainty and risk.
10. Generate final report.

This skill is the main controller. It does not perform the inner work of each skill. It calls the already implemented modules and combines their outputs.

---

## Core Task

Build a pipeline function that receives a user question and optional base answer, runs the required TemporalGuard skills, and returns a full structured pipeline output.

The pipeline must be deterministic where possible, easy to debug, safe with missing inputs, modular, testable, not over-engineered, and suitable for Streamlit and FastAPI use.

---

## Expected Pipeline Flow

```text
question
  ↓
Skill 12: LLM Answer Generation
  ↓
Skill 01: Temporal Question Detection
  ↓
Skill 02: Claim Extraction
  ↓
Skill 03: Fresh Evidence Retrieval
  ↓
Skill 04: Source Freshness Scoring
  ↓
Skill 05: Temporal Verification
  ↓
Skill 06: Outdated Answer Detection
  ↓
Skill 07: Correction Generation
  ↓
Skill 08: Uncertainty and Risk Labeling
  ↓
Skill 10: Report Generation
```

Skill 09 is used for offline evaluation, not usually in one user request.

---

## Required Output Format

Return JSON-compatible dictionary:

```json
{
  "run_id": "string",
  "question": "string",
  "original_answer": "string",
  "temporal_detection": {},
  "claims": {},
  "evidence": {},
  "freshness": {},
  "verification": {},
  "outdatedness": {},
  "correction": {},
  "risk_label": {},
  "report": {},
  "runtime": {
    "started_at": "ISO timestamp",
    "finished_at": "ISO timestamp",
    "duration_ms": 0
  },
  "pipeline_status": "success | partial_success | failed",
  "errors": [],
  "warnings": []
}
```

---

## Pipeline Rules

### Rule 1: Do not duplicate skill logic

The orchestrator must call existing modules. It must not reimplement claim extraction, evidence retrieval, verification, or correction logic.

### Rule 2: Continue safely after recoverable errors

If evidence retrieval fails, the pipeline should still continue to verification, outdatedness detection, correction, and risk labeling with insufficient-evidence status where possible.

### Rule 3: Skip unnecessary retrieval for static questions

If Skill 01 says `STATIC` and Skill 02 finds only optional claims, evidence retrieval may be skipped unless `force_retrieval=True`.

### Rule 4: Keep output complete

Even if one step fails, return the full structure with error details.

### Rule 5: No hidden network calls

Only Skill 03 or a configured search provider should use external search. The orchestrator itself should not browse the web.

### Rule 6: Support dependency injection

The pipeline should accept `llm_provider`, `search_provider`, config dict, and optional logger.

---

## Suggested Python Interface

```python
def run_temporalguard_pipeline(
    question: str,
    base_answer: str | None = None,
    llm_provider=None,
    search_provider=None,
    config: dict | None = None,
    report_type: str = "dashboard"
) -> dict:
    """
    Run the full TemporalGuard pipeline for one question.

    Args:
        question: User question.
        base_answer: Optional pre-generated LLM answer.
        llm_provider: Optional LLM provider for answer generation.
        search_provider: Optional search provider for evidence retrieval.
        config: Optional settings.
        report_type: dashboard, technical, thesis, or debug.

    Returns:
        Full JSON-compatible TemporalGuard pipeline output.
    """
```

---

## Recommended Project Files

Create:

```text
src/temporalguard/pipeline/orchestrator.py
tests/test_pipeline_orchestrator.py
```

---

## Quality Requirements

1. Use existing skill modules.
2. No web search inside orchestrator.
3. No LLM call unless base answer is missing and llm_provider is provided.
4. Return valid JSON-compatible output every time.
5. Handle missing or failed steps gracefully.
6. Include runtime metadata.
7. Include warnings and errors.
8. Make pipeline easy to use in Streamlit and FastAPI.
9. Add unit tests with mock LLM and mock search provider.
10. Use package name `temporalguard`.

---

## Minimum Test Cases

Test:

1. Static question with provided answer.
2. Recent software question with mock evidence.
3. Missing search provider for time-sensitive question.
4. Base answer missing and mock LLM provider used.
5. Skill failure simulated and pipeline returns `partial_success`.

---

## Prompt for Claude or Codex Agent

You are implementing Skill 11 for TemporalGuard.

Read `skills/11_pipeline_orchestration.md` carefully and implement the pipeline orchestrator only.

Create:

1. `src/temporalguard/pipeline/orchestrator.py`
2. `tests/test_pipeline_orchestrator.py`

Implement:

```python
def run_temporalguard_pipeline(
    question: str,
    base_answer: str | None = None,
    llm_provider=None,
    search_provider=None,
    config: dict | None = None,
    report_type: str = "dashboard"
) -> dict:
```

Requirements:

- Call the already implemented TemporalGuard skill modules in order.
- Do not reimplement skill logic.
- Support mock providers for tests.
- Continue gracefully when evidence retrieval fails.
- Return full JSON-compatible pipeline output.
- Include runtime timestamps, warnings, and errors.
- Use package name `temporalguard`.
- Keep code small, typed, deterministic, and easy to explain.
- Run tests and fix all failures.

At the end, report files created, logic summary, test result, and assumptions.
