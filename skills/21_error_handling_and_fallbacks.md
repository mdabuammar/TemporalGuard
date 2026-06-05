# Skill 21: Error Handling and Fallbacks

## Purpose

This skill defines project-wide error handling and fallback behavior for TemporalGuard.

TemporalGuard has multiple modules. Some may fail because of missing LLM provider, missing search provider, API timeout, malformed JSON, empty answer, no evidence found, bad dates, unsupported report type, or missing benchmark labels.

The system should not crash. It should return useful structured errors and continue when possible.

---

## Core Task

Create shared utilities for:

1. Standard error object
2. Safe function execution
3. Warning collection
4. Fallback outputs
5. Input validation helpers
6. Logging helpers

---

## Standard Error Format

```json
{
  "error_type": "string",
  "message": "string",
  "module": "string",
  "recoverable": true,
  "details": {}
}
```

---

## Standard Warning Format

```json
{
  "warning_type": "string",
  "message": "string",
  "module": "string",
  "details": {}
}
```

---

## Fallback Rules

### LLM failure

Return failed base answer generation and let user provide base answer manually.

### Search failure

Continue pipeline with insufficient evidence.

### Freshness scoring failure

Continue with unknown freshness and high/unknown risk.

### Verification failure

Return insufficient evidence or not verifiable.

### Correction failure

Return unable_to_correct with uncertainty note.

### Report failure

Return minimal debug report.

---

## Suggested Python Interfaces

```python
def make_error(error_type: str, message: str, module: str, recoverable: bool = True, details: dict | None = None) -> dict:
    ...

def make_warning(warning_type: str, message: str, module: str, details: dict | None = None) -> dict:
    ...

def safe_call(func, *args, module: str, fallback=None, **kwargs):
    ...
```

---

## Recommended Project Files

Create:

```text
src/temporalguard/utils/errors.py
tests/test_error_handling.py
```

---

## Prompt for Claude or Codex Agent

You are implementing Skill 21 for TemporalGuard.

Read `skills/21_error_handling_and_fallbacks.md` carefully and implement shared error handling utilities.

Create:

1. `src/temporalguard/utils/errors.py`
2. `tests/test_error_handling.py`

Requirements:

- Implement `make_error`.
- Implement `make_warning`.
- Implement `safe_call`.
- Standardize recoverable and non-recoverable errors.
- Return JSON-compatible dictionaries.
- Do not hide exceptions silently; record them.
- Add tests for success, recoverable failure, non-recoverable failure, and fallback behavior.
- Use package name `temporalguard`.

Run tests and fix all failures. Report files created, logic summary, test result, and assumptions.
