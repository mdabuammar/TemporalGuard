"""Deterministic model comparison runner for TemporalGuard."""

from __future__ import annotations

from datetime import UTC, datetime
import json
import re
from pathlib import Path
from typing import Any

from temporalguard.evaluation.metrics import evaluate_pipeline_outputs
from temporalguard.llm.answer_generator import generate_base_answer
from temporalguard.pipeline.orchestrator import run_temporalguard_pipeline
from temporalguard.utils.errors import make_error


def run_model_comparison(
    benchmark_examples: list[dict[str, Any]],
    model_providers: dict[str, Any],
    search_provider: Any = None,
    output_dir: str = "outputs/model_comparison",
    max_examples: int | None = None,
) -> dict[str, Any]:
    """Compare multiple injected LLM providers using TemporalGuard."""
    comparison_id = _comparison_id()
    examples = _select_examples(benchmark_examples, max_examples)
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    warnings: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    model_results: dict[str, Any] = {}

    if not model_providers:
        warnings.append(make_error("no_models", "No model providers supplied.", "model_comparison", True))

    for model_name, provider in model_providers.items():
        outputs: list[dict[str, Any]] = []
        model_errors: list[dict[str, Any]] = []
        for index, example in enumerate(examples, start=1):
            example_id = str(example.get("example_id") or example.get("id") or f"row-{index}")
            answer_result = generate_base_answer(str(example.get("question") or ""), provider)
            if answer_result.get("status") != "success":
                error = make_error(
                    "answer_generation_failed",
                    "; ".join(str(item) for item in answer_result.get("errors", [])) or "Model answer generation failed.",
                    "model_comparison",
                    recoverable=True,
                    details={"model": model_name, "example_id": example_id, "warnings": answer_result.get("warnings", [])},
                )
                model_errors.append(error)
                errors.append(error)
                outputs.append(_failed_output(example, model_name, answer_result, error))
                continue

            try:
                output = run_temporalguard_pipeline(
                    question=str(example.get("question") or ""),
                    base_answer=str(answer_result.get("answer") or ""),
                    llm_provider=None,
                    search_provider=search_provider,
                    config={},
                    report_type="technical",
                )
            except Exception as exc:  # pragma: no cover - defensive boundary
                error = make_error(
                    "pipeline_failed",
                    str(exc),
                    "model_comparison",
                    recoverable=True,
                    details={"model": model_name, "example_id": example_id, "exception_type": exc.__class__.__name__},
                )
                model_errors.append(error)
                errors.append(error)
                outputs.append(_failed_output(example, model_name, answer_result, error))
                continue

            output["id"] = example_id
            output["example_id"] = example_id
            output["model_name"] = model_name
            output["model_answer"] = answer_result
            outputs.append(output)

        outputs_path = output_root / f"{_safe_filename(model_name)}_outputs.jsonl"
        _save_jsonl(outputs, outputs_path)
        metrics = evaluate_pipeline_outputs(_metric_benchmark(examples), outputs)
        model_results[model_name] = {
            "outputs_path": str(outputs_path),
            "metrics": metrics,
            "summary": _model_summary(outputs, metrics),
            "errors": model_errors,
        }

    comparison_table = [_table_row(model_name, result) for model_name, result in model_results.items()]
    best_model = _best_model(comparison_table)
    return {
        "comparison_id": comparison_id,
        "models": list(model_providers.keys()),
        "total_examples": len(examples),
        "model_results": model_results,
        "comparison_table": comparison_table,
        "best_model": best_model,
        "warnings": warnings,
        "errors": errors,
    }


def compare_models(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Compatibility helper that ranks already-computed model result rows."""
    table = [_normalize_result_row(row) for row in results]
    return {
        "models": [row["model_name"] for row in table],
        "comparison_table": table,
        "best_model": _best_model(table),
    }


def _select_examples(examples: list[dict[str, Any]], max_examples: int | None) -> list[dict[str, Any]]:
    selected = list(examples)
    if max_examples is not None:
        selected = selected[: max(0, int(max_examples))]
    return selected


def _failed_output(
    example: dict[str, Any],
    model_name: str,
    answer_result: dict[str, Any],
    error: dict[str, Any],
) -> dict[str, Any]:
    example_id = str(example.get("example_id") or example.get("id") or "")
    return {
        "id": example_id,
        "example_id": example_id,
        "model_name": model_name,
        "question": str(example.get("question") or ""),
        "original_answer": str(answer_result.get("answer") or ""),
        "model_answer": answer_result,
        "pipeline_status": "failed",
        "errors": [error],
        "temporal_detection": {},
        "outdatedness": {},
        "correction": {},
        "risk_label": {},
    }


def _metric_benchmark(examples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, example in enumerate(examples, start=1):
        rows.append(
            {
                "id": example.get("example_id") or example.get("id") or f"row-{index}",
                "domain": example.get("domain"),
                "difficulty": example.get("difficulty"),
                "expected_temporal_category": example.get("gold_temporal_category") or example.get("expected_temporal_category"),
                "expected_outdatedness_status": example.get("gold_outdatedness_status") or example.get("expected_outdatedness_status"),
                "expected_requires_correction": example.get("gold_requires_correction")
                if "gold_requires_correction" in example
                else example.get("expected_requires_correction"),
                "expected_risk_label": example.get("gold_final_risk_label") or example.get("expected_risk_label"),
            }
        )
    return rows


def _model_summary(outputs: list[dict[str, Any]], metrics: dict[str, Any]) -> dict[str, Any]:
    trust_scores = [
        float(output.get("risk_label", {}).get("trust_score"))
        for output in outputs
        if isinstance(output.get("risk_label"), dict) and isinstance(output["risk_label"].get("trust_score"), int | float)
    ]
    outdated_count = sum(
        1
        for output in outputs
        if isinstance(output.get("outdatedness"), dict)
        and output["outdatedness"].get("outdatedness_status") in {"OUTDATED", "PARTIALLY_OUTDATED", "CONTRADICTED"}
    )
    total = len(outputs)
    return {
        "temporal_accuracy": metrics.get("temporal_category_accuracy"),
        "outdated_answer_rate": outdated_count / total if total else None,
        "correction_success_rate": metrics.get("correction_success_rate"),
        "average_trust_score": sum(trust_scores) / len(trust_scores) if trust_scores else None,
    }


def _table_row(model_name: str, result: dict[str, Any]) -> dict[str, Any]:
    metrics = result.get("metrics", {})
    summary = result.get("summary", {})
    return {
        "model_name": model_name,
        "temporal_category_accuracy": metrics.get("temporal_category_accuracy"),
        "outdatedness_accuracy": metrics.get("outdatedness_accuracy"),
        "correction_success_rate": metrics.get("correction_success_rate"),
        "risk_label_accuracy": metrics.get("risk_label_accuracy"),
        "exact_decision_match_rate": metrics.get("end_to_end", {}).get("exact_decision_match_rate"),
        "average_trust_score": summary.get("average_trust_score"),
        "error_count": len(result.get("errors", [])),
    }


def _normalize_result_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "model_name": str(row.get("model_name") or row.get("model") or "unknown"),
        "temporal_category_accuracy": row.get("temporal_category_accuracy"),
        "outdatedness_accuracy": row.get("outdatedness_accuracy"),
        "correction_success_rate": row.get("correction_success_rate"),
        "risk_label_accuracy": row.get("risk_label_accuracy"),
        "exact_decision_match_rate": row.get("exact_decision_match_rate"),
        "average_trust_score": row.get("average_trust_score"),
        "error_count": int(row.get("error_count") or 0),
    }


def _best_model(table: list[dict[str, Any]]) -> str | None:
    if not table:
        return None

    def score(row: dict[str, Any]) -> tuple[float, float, float, float, float, int]:
        return (
            _number(row.get("exact_decision_match_rate")),
            _number(row.get("outdatedness_accuracy")),
            _number(row.get("risk_label_accuracy")),
            _number(row.get("correction_success_rate")),
            _number(row.get("temporal_category_accuracy")),
            -int(row.get("error_count") or 0),
        )

    return max(table, key=score)["model_name"]


def _number(value: Any) -> float:
    return float(value) if isinstance(value, int | float) else -1.0


def _save_jsonl(outputs: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as file:
        for output in outputs:
            file.write(json.dumps(output, ensure_ascii=False, sort_keys=True) + "\n")


def _safe_filename(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value).strip())
    return text.strip("._") or "model"


def _comparison_id() -> str:
    return "MC_" + datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
