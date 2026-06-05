# Skill 23: Model Comparison Runner

## Purpose

This skill compares multiple base LLMs using TemporalGuard.

For thesis and portfolio, you should show how different models perform on temporal reliability.

Example models:

- GPT
- Gemini
- Claude
- Llama
- Mistral
- local/Ollama models
- any custom provider

This skill runs the same benchmark questions across multiple LLM providers and stores results.

---

## Core Task

Create a runner that:

1. Loads benchmark examples.
2. Runs base answer generation for each model.
3. Runs TemporalGuard pipeline for each answer.
4. Saves system outputs.
5. Computes evaluation metrics per model.
6. Creates comparison summary.

---

## Required Output Format

```json
{
  "comparison_id": "string",
  "models": ["gpt", "gemini", "llama"],
  "total_examples": 0,
  "model_results": {
    "model_name": {
      "outputs_path": "string",
      "metrics": {},
      "summary": {
        "temporal_accuracy": 0.0,
        "outdated_answer_rate": 0.0,
        "correction_success_rate": 0.0,
        "average_trust_score": 0.0
      }
    }
  },
  "best_model": "string or null",
  "comparison_table": [],
  "warnings": [],
  "errors": []
}
```

---

## Suggested Python Interface

```python
def run_model_comparison(
    benchmark_examples: list[dict],
    model_providers: dict,
    search_provider=None,
    output_dir: str = "outputs/model_comparison",
    max_examples: int | None = None
) -> dict:
    """
    Compare multiple LLM providers using TemporalGuard.
    """
```

---

## Rules

1. Use same benchmark for every model.
2. Use same search provider for fairness.
3. Save outputs per model.
4. Evaluate using Skill 09.
5. Do not crash if one model fails.
6. Record failures per model.
7. Support max_examples for quick testing.
8. Make results reproducible.

---

## Recommended Project Files

Create:

```text
src/temporalguard/evaluation/model_comparison.py
tests/test_model_comparison.py
```

---

## Prompt for Claude or Codex Agent

You are implementing Skill 23 for TemporalGuard.

Read `skills/23_model_comparison_runner.md` carefully and implement the model comparison runner.

Create:

1. `src/temporalguard/evaluation/model_comparison.py`
2. `tests/test_model_comparison.py`

Requirements:

- Accept benchmark examples and model provider dictionary.
- Run TemporalGuard pipeline for each model and example.
- Use same search provider for fairness.
- Save outputs per model.
- Evaluate outputs using Skill 09 metrics.
- Return comparison summary and table.
- Do not crash if one model/provider fails.
- Tests must use mock model providers and mock search provider.
- No real API calls in unit tests.
- Keep code typed, deterministic, and thesis-explainable.
- Use package name `temporalguard`.

Run tests and fix all failures. Report files created, logic summary, test result, and assumptions.
