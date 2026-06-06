"""Deterministic evaluation metrics for TemporalGuard pipeline outputs.

This module compares already-produced TemporalGuard outputs against benchmark
examples. It does not call the pipeline, search, or any LLM.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any


CORRECTED_STATUSES = {"corrected", "partially_corrected", "updated"}
NO_CORRECTION_STATUSES = {"no_correction_needed", "unchanged", "not_applicable", "skipped"}
NO_CORRECTION_OUTDATEDNESS = {"NOT_OUTDATED", "NOT_APPLICABLE"}


def compute_metrics(system_outputs: list[dict[str, Any]], benchmark_examples: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute TemporalGuard evaluation metrics for paired outputs/examples.

    The function pairs examples with outputs by ``id`` when possible, otherwise
    by list order. Missing expected labels are skipped for that metric.
    """
    pairs = _pair_examples(system_outputs, benchmark_examples)
    rows = [_evaluate_pair(output, example) for output, example in pairs]

    return {
        "total_examples": len(benchmark_examples),
        "evaluated_examples": len(rows),
        "temporal_category_accuracy": _rate(row["temporal_category_correct"] for row in rows),
        "outdatedness_accuracy": _rate(row["outdatedness_correct"] for row in rows),
        "correction_success_rate": _rate(row["correction_success"] for row in rows),
        "unsupported_correction_avoidance": _rate(row["unsupported_correction_avoided"] for row in rows),
        "risk_label_accuracy": _rate(row["risk_label_correct"] for row in rows),
        "end_to_end": _end_to_end_metrics(rows),
        "domain_breakdown": _breakdown(rows, "domain"),
        "difficulty_breakdown": _breakdown(rows, "difficulty"),
        "error_analysis": _error_analysis(rows, len(system_outputs), len(benchmark_examples)),
    }


def evaluate_pipeline_outputs(
    benchmark_examples: list[dict[str, Any]], system_outputs: list[dict[str, Any]]
) -> dict[str, Any]:
    """Readable alias for thesis code that names benchmark examples first."""
    return compute_metrics(system_outputs, benchmark_examples)


def _evaluate_pair(output: dict[str, Any] | None, example: dict[str, Any]) -> dict[str, Any]:
    output = output if isinstance(output, dict) else {}
    expected_temporal = _expected(example, "expected_temporal_category", "temporal_category", "label", "annotation")
    expected_outdatedness = _expected(example, "expected_outdatedness_status", "outdatedness_status")
    expected_risk = _expected(example, "expected_risk_label", "risk_label", "final_risk_label")
    expected_correction_status = _expected(example, "expected_correction_status", "correction_status")
    expected_requires_correction = _expected_bool(
        example,
        "expected_requires_correction",
        "requires_correction",
        "correction_required",
        "should_correct",
    )

    predicted_temporal = _first(output, ["temporal_detection", "temporal_category"], ["report", "pipeline_summary", "temporal_category"])
    predicted_outdatedness = _first(
        output, ["outdatedness", "outdatedness_status"], ["report", "pipeline_summary", "outdatedness_status"]
    )
    predicted_risk = _first(output, ["risk_label", "final_risk_label"], ["report", "pipeline_summary", "final_risk_label"])
    predicted_correction_status = _first(output, ["correction", "correction_status"], ["report", "pipeline_summary", "correction_status"])
    predicted_requires_correction = _predicted_requires_correction(output, predicted_correction_status)

    if expected_requires_correction is None:
        expected_requires_correction = _requires_correction_from_labels(expected_outdatedness, expected_correction_status)

    return {
        "id": example.get("id") or output.get("id") or output.get("run_id"),
        "domain": str(example.get("domain") or "unknown"),
        "difficulty": str(example.get("difficulty") or "unknown"),
        "has_output": bool(output),
        "temporal_category_correct": _match(predicted_temporal, expected_temporal),
        "outdatedness_correct": _match(predicted_outdatedness, expected_outdatedness),
        "risk_label_correct": _match(predicted_risk, expected_risk),
        "correction_success": _correction_success(
            output,
            expected_requires_correction,
            expected_correction_status,
            predicted_correction_status,
        ),
        "unsupported_correction_avoided": _unsupported_correction_avoided(
            expected_requires_correction,
            expected_outdatedness,
            predicted_requires_correction,
            predicted_correction_status,
        ),
        "expected": {
            "temporal_category": expected_temporal,
            "outdatedness_status": expected_outdatedness,
            "risk_label": expected_risk,
            "requires_correction": expected_requires_correction,
            "correction_status": expected_correction_status,
        },
        "predicted": {
            "temporal_category": predicted_temporal,
            "outdatedness_status": predicted_outdatedness,
            "risk_label": predicted_risk,
            "requires_correction": predicted_requires_correction,
            "correction_status": predicted_correction_status,
        },
    }


def _pair_examples(
    system_outputs: list[dict[str, Any]], benchmark_examples: list[dict[str, Any]]
) -> list[tuple[dict[str, Any] | None, dict[str, Any]]]:
    outputs_by_id = {
        str(output["id"]): output
        for output in system_outputs
        if isinstance(output, dict) and output.get("id") is not None
    }
    if outputs_by_id and any(example.get("id") is not None for example in benchmark_examples):
        return [(outputs_by_id.get(str(example.get("id"))), example) for example in benchmark_examples]
    return [
        (system_outputs[index] if index < len(system_outputs) and isinstance(system_outputs[index], dict) else None, example)
        for index, example in enumerate(benchmark_examples)
    ]


def _end_to_end_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    complete = []
    for row in rows:
        decisions = [
            row["temporal_category_correct"],
            row["outdatedness_correct"],
            row["correction_success"],
            row["unsupported_correction_avoided"],
            row["risk_label_correct"],
        ]
        scored = [decision for decision in decisions if decision is not None]
        if scored:
            complete.append(all(scored))
    return {
        "exact_decision_match_rate": _rate(complete),
        "fully_correct_examples": sum(1 for value in complete if value is True),
        "scored_examples": len(complete),
    }


def _breakdown(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(key) or "unknown")].append(row)

    return {
        group: {
            "count": len(group_rows),
            "temporal_category_accuracy": _rate(row["temporal_category_correct"] for row in group_rows),
            "outdatedness_accuracy": _rate(row["outdatedness_correct"] for row in group_rows),
            "correction_success_rate": _rate(row["correction_success"] for row in group_rows),
            "unsupported_correction_avoidance": _rate(row["unsupported_correction_avoided"] for row in group_rows),
            "risk_label_accuracy": _rate(row["risk_label_correct"] for row in group_rows),
            "end_to_end_accuracy": _rate(
                all(value for value in decisions if value is not None)
                for decisions in (
                    [
                        row["temporal_category_correct"],
                        row["outdatedness_correct"],
                        row["correction_success"],
                        row["unsupported_correction_avoided"],
                        row["risk_label_correct"],
                    ]
                    for row in group_rows
                )
                if any(value is not None for value in decisions)
            ),
        }
        for group, group_rows in sorted(groups.items())
    }


def _error_analysis(rows: list[dict[str, Any]], output_count: int, example_count: int) -> dict[str, Any]:
    metric_keys = [
        "temporal_category_correct",
        "outdatedness_correct",
        "correction_success",
        "unsupported_correction_avoided",
        "risk_label_correct",
    ]
    mismatches: dict[str, int] = {key: 0 for key in metric_keys}
    examples: list[dict[str, Any]] = []

    for row in rows:
        failed = [key for key in metric_keys if row[key] is False]
        for key in failed:
            mismatches[key] += 1
        if failed:
            examples.append(
                {
                    "id": row["id"],
                    "failed_metrics": failed,
                    "expected": row["expected"],
                    "predicted": row["predicted"],
                }
            )

    return {
        "missing_output_count": sum(1 for row in rows if not row["has_output"]),
        "extra_output_count": max(0, output_count - example_count),
        "mismatch_counts": mismatches,
        "mismatched_examples": examples,
    }


def _correction_success(
    output: dict[str, Any],
    expected_requires_correction: bool | None,
    expected_correction_status: Any,
    predicted_correction_status: Any,
) -> bool | None:
    if expected_requires_correction is not True:
        return None
    if expected_correction_status is not None:
        return _normalize(predicted_correction_status) == _normalize(expected_correction_status)
    final_answer = _first(output, ["correction", "corrected_answer"], ["report", "final_answer"])
    return _normalize(predicted_correction_status) in CORRECTED_STATUSES and bool(final_answer)


def _unsupported_correction_avoided(
    expected_requires_correction: bool | None,
    expected_outdatedness: Any,
    predicted_requires_correction: bool,
    predicted_correction_status: Any,
) -> bool | None:
    should_avoid = expected_requires_correction is False or _normalize(expected_outdatedness) in NO_CORRECTION_OUTDATEDNESS
    if not should_avoid:
        return None
    return (not predicted_requires_correction) and _normalize(predicted_correction_status) in NO_CORRECTION_STATUSES


def _predicted_requires_correction(output: dict[str, Any], predicted_correction_status: Any) -> bool:
    explicit = _first(output, ["outdatedness", "requires_correction"], ["correction", "requires_correction"])
    if explicit is not None:
        return bool(explicit)
    return _normalize(predicted_correction_status) in CORRECTED_STATUSES


def _requires_correction_from_labels(expected_outdatedness: Any, expected_correction_status: Any) -> bool | None:
    if expected_correction_status is not None:
        return _normalize(expected_correction_status) not in NO_CORRECTION_STATUSES
    if expected_outdatedness is None:
        return None
    return _normalize(expected_outdatedness) not in NO_CORRECTION_OUTDATEDNESS


def _match(predicted: Any, expected: Any) -> bool | None:
    if expected is None:
        return None
    return _normalize(predicted) == _normalize(expected)


def _rate(values: Any) -> float | None:
    scored = [value for value in values if value is not None]
    if not scored:
        return None
    return sum(1 for value in scored if value is True) / len(scored)


def _expected(example: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in example and example[key] is not None:
            return example[key]
    expected = example.get("expected")
    if isinstance(expected, dict):
        for key in keys:
            if key in expected and expected[key] is not None:
                return expected[key]
    return None


def _expected_bool(example: dict[str, Any], *keys: str) -> bool | None:
    value = _expected(example, *keys)
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "1", "required", "needs_correction"}
    return bool(value)


def _first(data: dict[str, Any], *paths: list[str]) -> Any:
    for path in paths:
        current: Any = data
        for key in path:
            if not isinstance(current, dict) or key not in current:
                current = None
                break
            current = current[key]
        if current is not None:
            return current
    return None


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower()
