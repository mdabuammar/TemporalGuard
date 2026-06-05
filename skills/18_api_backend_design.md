# Skill 18: API Backend Design

## Purpose

This skill defines a FastAPI backend for TemporalGuard.

The backend allows the frontend, dashboard, or external users to run TemporalGuard through HTTP endpoints.

This makes the project more industry-level and deployable.

---

## Core Task

Create a FastAPI app that exposes TemporalGuard pipeline functions through clean endpoints.

The backend should support:

1. Health check
2. Single question analysis
3. Batch analysis
4. Report generation
5. Evaluation run
6. Config/status inspection

---

## Recommended Endpoints

### 1. Health

```http
GET /health
```

Response:

```json
{
  "service": "temporalguard-api",
  "status": "ok",
  "version": "0.1.0"
}
```

### 2. Analyze One Question

```http
POST /analyze
```

Request:

```json
{
  "question": "What is the latest Python version?",
  "base_answer": null,
  "report_type": "dashboard"
}
```

Response: full pipeline output.

### 3. Batch Analyze

```http
POST /batch-analyze
```

Request:

```json
{
  "items": [
    {
      "example_id": "EX001",
      "question": "...",
      "base_answer": "..."
    }
  ]
}
```

### 4. Generate Report

```http
POST /report
```

Request:

```json
{
  "pipeline_output": {},
  "report_type": "thesis"
}
```

### 5. Evaluate

```http
POST /evaluate
```

Request:

```json
{
  "benchmark_examples": [],
  "system_outputs": []
}
```

---

## Backend Rules

1. API should not contain skill logic.
2. API should call orchestrator and report/evaluation modules.
3. Validate request inputs.
4. Return clear error messages.
5. Add CORS for local dashboard.
6. Avoid exposing API keys.
7. Use environment variables for provider config.
8. Add request timeout if possible.
9. Keep endpoints simple.

---

## Suggested Project Files

Create:

```text
src/temporalguard/api/main.py
src/temporalguard/api/schemas.py
tests/test_api_backend.py
```

---

## Suggested Tech

Use FastAPI, Pydantic, and Uvicorn.

If dependencies are not installed, add them to requirements.

---

## Prompt for Claude or Codex Agent

You are implementing Skill 18 for TemporalGuard.

Read `skills/18_api_backend_design.md` carefully and implement the FastAPI backend.

Create:

1. `src/temporalguard/api/main.py`
2. `src/temporalguard/api/schemas.py`
3. `tests/test_api_backend.py`

Requirements:

- Implement `/health`.
- Implement `/analyze`.
- Implement `/batch-analyze`.
- Implement `/report`.
- Implement `/evaluate`.
- Use Pydantic schemas.
- Use orchestrator for analysis.
- Use report generator for report endpoint.
- Use evaluation metrics for evaluation endpoint.
- Add CORS.
- Handle errors safely.
- Do not put skill logic inside API layer.
- Use package name `temporalguard`.

Run tests and fix all failures. Report files created, logic summary, test result, and assumptions.
