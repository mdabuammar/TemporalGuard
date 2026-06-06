# TemporalGuard Evaluation Dataset

This directory stores benchmark examples used to evaluate TemporalGuard against
manually annotated temporal reliability cases.

## Example Format

Each JSONL row should contain one benchmark example:

```json
{
  "example_id": "EX001",
  "question": "What is the latest Python version?",
  "original_answer": "Python 3.10 is the latest stable version of Python.",
  "gold_temporal_category": "RECENT_ONLY",
  "gold_outdatedness_status": "OUTDATED",
  "gold_requires_correction": true,
  "gold_evidence_value": "Python 3.13.5",
  "gold_final_risk_label": "medium_risk",
  "domain": "software",
  "difficulty": "easy",
  "high_risk_domain": false,
  "source_notes": "Official Python download page checked manually.",
  "annotation_status": "verified"
}
```

## Required Fields

- `example_id`
- `question`
- `original_answer`
- `gold_temporal_category`
- `gold_outdatedness_status`
- `gold_requires_correction`
- `domain`
- `difficulty`
- `annotation_status`

## Allowed Labels

Temporal categories:

- `STATIC`
- `TIME_SENSITIVE`
- `RECENT_ONLY`
- `HISTORICAL`
- `VERSION_DEPENDENT`
- `UNKNOWN`

Outdatedness statuses:

- `NOT_OUTDATED`
- `OUTDATED`
- `PARTIALLY_OUTDATED`
- `CONTRADICTED`
- `UNVERIFIED_RISKY`
- `NOT_ENOUGH_INFORMATION`
- `NOT_APPLICABLE`

Risk labels:

- `safe`
- `low_risk`
- `medium_risk`
- `high_risk`
- `critical_risk`
- `unknown_risk`

Domains:

- `software`
- `company_leadership`
- `law_policy`
- `medical_science`
- `finance_market`
- `sports_events`
- `academic_research`
- `historical`
- `static_education`
- `other`

Difficulty labels:

- `easy`
- `medium`
- `hard`
- `adversarial`

Annotation statuses:

- `draft`
- `reviewed`
- `verified`
- `needs_review`

## Building A Normalized Dataset

Use the dataset builder from Python:

```python
from temporalguard.data.dataset_builder import build_benchmark_dataset

result = build_benchmark_dataset(
    input_path="data/evaluation/seed_examples.jsonl",
    output_path="data/evaluation/temporalguard_benchmark.jsonl",
    split=True,
    seed=42,
)
```

The builder can load JSONL or CSV, validate required fields and labels,
normalize casing, save normalized JSONL, generate summary counts, and optionally
create deterministic `train`, `dev`, and `test` JSONL files.

## Dataset Balance Target

For a first thesis benchmark, target at least 100 examples. A balanced starter
set can use:

- `RECENT_ONLY`: 25
- `TIME_SENSITIVE`: 20
- `VERSION_DEPENDENT`: 20
- `HISTORICAL`: 15
- `STATIC`: 15
- `UNKNOWN`: 5

All examples should be manually reviewed before being marked `verified`.
