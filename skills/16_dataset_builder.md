# Skill 16: Dataset Builder

## Purpose

This skill builds the TemporalGuard benchmark dataset for thesis experiments.

The dataset should contain time-sensitive, historical, version-dependent, static, and high-risk examples. It will be used to test whether TemporalGuard detects and corrects outdated LLM answers.

This skill is important because a strong thesis needs a measurable benchmark, not only a demo.

---

## Core Task

Create a dataset builder that can:

1. Load seed examples from CSV/JSONL.
2. Validate required fields.
3. Normalize labels.
4. Save benchmark examples as JSONL.
5. Split data into train/dev/test or evaluation subsets.
6. Generate dataset summary statistics.

---

## Benchmark Example Format

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

---

## Required Domains

Include examples from:

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

For thesis first version, target 100 examples minimum and 200–300 examples ideally.

---

## Required Temporal Categories

Include:

```text
STATIC
TIME_SENSITIVE
RECENT_ONLY
HISTORICAL
VERSION_DEPENDENT
UNKNOWN
```

---

## Suggested Dataset Balance

For 100 examples:

```text
RECENT_ONLY: 25
TIME_SENSITIVE: 20
VERSION_DEPENDENT: 20
HISTORICAL: 15
STATIC: 15
UNKNOWN: 5
```

---

## Suggested Python Interface

```python
def build_benchmark_dataset(
    input_path: str,
    output_path: str,
    format: str = "jsonl",
    split: bool = False,
    seed: int = 42
) -> dict:
    """
    Build and validate a TemporalGuard benchmark dataset.
    """
```

Additional functions:

```python
def validate_benchmark_example(example: dict) -> tuple[bool, list[str]]:
    ...

def summarize_benchmark(examples: list[dict]) -> dict:
    ...

def save_jsonl(examples: list[dict], path: str) -> None:
    ...

def load_examples(path: str) -> list[dict]:
    ...
```

---

## Recommended Project Files

Create:

```text
src/temporalguard/data/dataset_builder.py
tests/test_dataset_builder.py
data/evaluation/README.md
```

---

## Validation Rules

Required fields:

```text
example_id
question
original_answer
gold_temporal_category
gold_outdatedness_status
gold_requires_correction
domain
difficulty
annotation_status
```

Valid labels:

- temporal category must match Skill 01 categories
- outdatedness status must match Skill 06 statuses
- risk label must match Skill 08 labels if present
- difficulty must be easy, medium, hard, or adversarial

---

## Prompt for Claude or Codex Agent

You are implementing Skill 16 for TemporalGuard.

Read `skills/16_dataset_builder.md` carefully and implement the benchmark dataset builder.

Create:

1. `src/temporalguard/data/dataset_builder.py`
2. `tests/test_dataset_builder.py`
3. `data/evaluation/README.md`

Requirements:

- Load examples from JSONL and CSV.
- Validate required fields and allowed labels.
- Save normalized JSONL.
- Generate dataset summary by category, domain, difficulty, and annotation status.
- Support deterministic split if requested.
- No web search.
- No LLM calls.
- Use standard library only if possible.
- Keep code typed, clean, and thesis-explainable.
- Use package name `temporalguard`.

Run tests and fix all failures. Report files created, logic summary, test result, and assumptions.
