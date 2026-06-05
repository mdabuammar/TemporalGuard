# Skill 17: Benchmark Annotation Guidelines

## Purpose

This skill defines how to manually annotate TemporalGuard benchmark examples.

A thesis benchmark needs consistent labels. If labels are unclear, evaluation results will not be trustworthy.

This file gives rules for human annotation.

---

## Core Task

Create annotation guidelines and helper validation logic so each benchmark example receives correct gold labels.

The annotation process must define:

1. Temporal category
2. Claim type
3. Outdatedness status
4. Evidence value
5. Correction requirement
6. Final risk label
7. Domain
8. Difficulty
9. High-risk flag
10. Annotation status

---

## Annotation Labels

### Temporal Category

```text
STATIC
TIME_SENSITIVE
RECENT_ONLY
HISTORICAL
VERSION_DEPENDENT
UNKNOWN
```

### Outdatedness Status

```text
NOT_OUTDATED
OUTDATED
PARTIALLY_OUTDATED
CONTRADICTED
UNVERIFIED_RISKY
NOT_ENOUGH_INFORMATION
NOT_APPLICABLE
```

### Final Risk Label

```text
safe
low_risk
medium_risk
high_risk
critical_risk
unknown_risk
```

### Domain

```text
software
company_leadership
law_policy
medical_science
finance_market
sports_events
academic_research
historical
static_education
other
```

### Difficulty

```text
easy
medium
hard
adversarial
```

### Annotation Status

```text
draft
verified
needs_review
rejected
```

---

## Annotation Rules

### Rule 1: Label by user question context

If the question asks for latest/current/today, choose `RECENT_ONLY`.

### Rule 2: Use official or authoritative evidence

Gold evidence values must come from trusted sources, not guesses.

### Rule 3: Do not label as OUTDATED without evidence

If there is no evidence showing the answer is old, use `UNVERIFIED_RISKY` or `NOT_ENOUGH_INFORMATION`.

### Rule 4: Separate outdated from contradicted

- OUTDATED: likely old value replaced by new value.
- CONTRADICTED: wrong for the requested time/context.

### Rule 5: High-risk domains require strict evidence

Visa, legal, medical, finance, safety, and regulation examples should be `critical_risk` if evidence is insufficient.

### Rule 6: Record evidence value

For each outdated or contradicted claim, record `gold_evidence_value`, `gold_source_url`, and `gold_source_date`.

### Rule 7: Keep examples simple first

For first thesis benchmark, prefer one main claim per example. Add multi-claim examples later.

---

## Example Annotation

```json
{
  "example_id": "EX001",
  "question": "What is the latest Python version?",
  "original_answer": "Python 3.10 is the latest stable version.",
  "gold_temporal_category": "RECENT_ONLY",
  "gold_outdatedness_status": "OUTDATED",
  "gold_requires_correction": true,
  "gold_evidence_value": "Python 3.13.5",
  "gold_final_risk_label": "medium_risk",
  "domain": "software",
  "difficulty": "easy",
  "high_risk_domain": false,
  "annotation_status": "verified"
}
```

---

## Suggested Python Interface

```python
def validate_annotation(example: dict) -> dict:
    """
    Validate one benchmark annotation and return errors/warnings.
    """
```

```python
def annotation_checklist(example: dict) -> list[str]:
    """
    Return human-readable checklist items for annotation review.
    """
```

---

## Recommended Project Files

Create:

```text
docs/annotation_guidelines.md
src/temporalguard/data/annotation_validator.py
tests/test_annotation_validator.py
```

---

## Prompt for Claude or Codex Agent

You are implementing Skill 17 for TemporalGuard.

Read `skills/17_benchmark_annotation_guidelines.md` carefully.

Create:

1. `docs/annotation_guidelines.md`
2. `src/temporalguard/data/annotation_validator.py`
3. `tests/test_annotation_validator.py`

Requirements:

- Write a clean annotation guideline document.
- Implement validation for benchmark annotation fields.
- Check allowed labels.
- Detect missing gold evidence for outdated/contradicted examples.
- Detect high-risk examples with too-low risk labels.
- Return JSON-compatible validation results.
- Add unit tests.
- No web search.
- No LLM calls.
- Use package name `temporalguard`.

Run tests and fix all failures. Report files created, logic summary, test result, and assumptions.
