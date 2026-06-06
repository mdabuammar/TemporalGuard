"""Benchmark dataset builder for TemporalGuard.

The builder only loads, normalizes, validates, summarizes, splits, and saves
benchmark examples. It never runs the TemporalGuard pipeline or external tools.
"""

from __future__ import annotations

import csv
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "example_id",
    "question",
    "original_answer",
    "gold_temporal_category",
    "gold_outdatedness_status",
    "gold_requires_correction",
    "domain",
    "difficulty",
    "annotation_status",
}
ALLOWED_TEMPORAL_CATEGORIES = {
    "STATIC",
    "TIME_SENSITIVE",
    "RECENT_ONLY",
    "HISTORICAL",
    "VERSION_DEPENDENT",
    "UNKNOWN",
}
ALLOWED_OUTDATEDNESS_STATUSES = {
    "NOT_OUTDATED",
    "OUTDATED",
    "PARTIALLY_OUTDATED",
    "CONTRADICTED",
    "UNVERIFIED_RISKY",
    "NOT_ENOUGH_INFORMATION",
    "NOT_APPLICABLE",
}
ALLOWED_RISK_LABELS = {
    "safe",
    "low_risk",
    "medium_risk",
    "high_risk",
    "critical_risk",
    "unknown_risk",
}
ALLOWED_DOMAINS = {
    "software",
    "company_leadership",
    "law_policy",
    "medical_science",
    "finance_market",
    "sports_events",
    "academic_research",
    "historical",
    "static_education",
    "other",
}
ALLOWED_DIFFICULTIES = {"easy", "medium", "hard", "adversarial"}
ALLOWED_ANNOTATION_STATUSES = {"draft", "reviewed", "verified", "needs_review"}
OPTIONAL_FIELDS = {"gold_evidence_value", "gold_final_risk_label", "high_risk_domain", "source_notes"}


def build_benchmark_dataset(
    input_path: str,
    output_path: str,
    format: str = "jsonl",
    split: bool = False,
    seed: int = 42,
) -> dict[str, Any]:
    """Build and validate a TemporalGuard benchmark dataset."""
    examples = [_normalize_example(example) for example in load_examples(input_path, format=format)]
    errors = _validation_errors(examples)
    if errors:
        details = "; ".join(f"{item['example_id']}: {', '.join(item['errors'])}" for item in errors)
        raise ValueError(f"Invalid benchmark examples: {details}")

    save_jsonl(examples, output_path)
    summary = summarize_benchmark(examples)
    result: dict[str, Any] = {
        "output_path": str(output_path),
        "total_examples": len(examples),
        "summary": summary,
        "validation_errors": [],
    }
    if split:
        split_sets = split_examples(examples, seed=seed)
        split_paths = _save_splits(split_sets, output_path)
        result["splits"] = {name: len(items) for name, items in split_sets.items()}
        result["split_paths"] = split_paths
    return result


def load_examples(path: str, format: str | None = None) -> list[dict[str, Any]]:
    """Load benchmark examples from JSONL or CSV."""
    source = Path(path)
    data_format = (format or source.suffix.lstrip(".")).lower()
    if data_format == "jsonl":
        return _load_jsonl(source)
    if data_format == "csv":
        return _load_csv(source)
    raise ValueError(f"Unsupported dataset format: {data_format}")


def validate_benchmark_example(example: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate one normalized or raw benchmark example."""
    normalized = _normalize_example(example)
    errors: list[str] = []

    for field in sorted(REQUIRED_FIELDS):
        if normalized.get(field) in (None, ""):
            errors.append(f"missing required field: {field}")

    if normalized.get("gold_temporal_category") not in ALLOWED_TEMPORAL_CATEGORIES:
        errors.append("invalid gold_temporal_category")
    if normalized.get("gold_outdatedness_status") not in ALLOWED_OUTDATEDNESS_STATUSES:
        errors.append("invalid gold_outdatedness_status")
    if normalized.get("gold_final_risk_label") not in (None, "") and normalized["gold_final_risk_label"] not in ALLOWED_RISK_LABELS:
        errors.append("invalid gold_final_risk_label")
    if normalized.get("domain") not in ALLOWED_DOMAINS:
        errors.append("invalid domain")
    if normalized.get("difficulty") not in ALLOWED_DIFFICULTIES:
        errors.append("invalid difficulty")
    if normalized.get("annotation_status") not in ALLOWED_ANNOTATION_STATUSES:
        errors.append("invalid annotation_status")
    if not isinstance(normalized.get("gold_requires_correction"), bool):
        errors.append("gold_requires_correction must be boolean")
    if normalized.get("high_risk_domain") not in (None, "") and not isinstance(normalized.get("high_risk_domain"), bool):
        errors.append("high_risk_domain must be boolean when present")

    return not errors, errors


def summarize_benchmark(examples: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate benchmark summary statistics."""
    normalized = [_normalize_example(example) for example in examples]
    return {
        "total_examples": len(normalized),
        "temporal_category": _count_by(normalized, "gold_temporal_category"),
        "outdatedness_status": _count_by(normalized, "gold_outdatedness_status"),
        "domain": _count_by(normalized, "domain"),
        "difficulty": _count_by(normalized, "difficulty"),
        "annotation_status": _count_by(normalized, "annotation_status"),
    }


def save_jsonl(examples: list[dict[str, Any]], path: str) -> None:
    """Save normalized examples as JSONL."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as file:
        for example in examples:
            file.write(json.dumps(_normalize_example(example), ensure_ascii=False, sort_keys=True) + "\n")


def split_examples(examples: list[dict[str, Any]], seed: int = 42) -> dict[str, list[dict[str, Any]]]:
    """Create deterministic train/dev/test splits using an 80/10/10 ratio."""
    shuffled = [_normalize_example(example) for example in examples]
    random.Random(seed).shuffle(shuffled)
    total = len(shuffled)
    train_end = int(total * 0.8)
    dev_end = train_end + int(total * 0.1)
    if total >= 3 and dev_end == train_end:
        dev_end += 1
    if total >= 2 and train_end == 0:
        train_end = 1
    return {
        "train": shuffled[:train_end],
        "dev": shuffled[train_end:dev_end],
        "test": shuffled[dev_end:],
    }


def build_dataset(samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compatibility wrapper that returns normalized sample copies."""
    return [_normalize_example(sample) for sample in samples]


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                item = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at line {line_number}: {exc}") from exc
            if not isinstance(item, dict):
                raise ValueError(f"JSONL line {line_number} must contain an object")
            examples.append(item)
    return examples


def _load_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        return [dict(row) for row in csv.DictReader(file)]


def _normalize_example(example: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(example)
    for key in REQUIRED_FIELDS | OPTIONAL_FIELDS:
        if key in normalized and isinstance(normalized[key], str):
            normalized[key] = normalized[key].strip()

    normalized["example_id"] = str(normalized.get("example_id", "")).strip()
    normalized["question"] = str(normalized.get("question", "")).strip()
    normalized["original_answer"] = str(normalized.get("original_answer", "")).strip()
    normalized["gold_temporal_category"] = str(normalized.get("gold_temporal_category", "")).strip().upper()
    normalized["gold_outdatedness_status"] = str(normalized.get("gold_outdatedness_status", "")).strip().upper()
    normalized["domain"] = str(normalized.get("domain", "")).strip().lower()
    normalized["difficulty"] = str(normalized.get("difficulty", "")).strip().lower()
    normalized["annotation_status"] = str(normalized.get("annotation_status", "")).strip().lower()

    if "gold_final_risk_label" in normalized and normalized["gold_final_risk_label"] not in (None, ""):
        normalized["gold_final_risk_label"] = str(normalized["gold_final_risk_label"]).strip().lower()
    if "gold_requires_correction" in normalized:
        normalized["gold_requires_correction"] = _parse_bool(normalized["gold_requires_correction"])
    if "high_risk_domain" in normalized and normalized["high_risk_domain"] not in (None, ""):
        normalized["high_risk_domain"] = _parse_bool(normalized["high_risk_domain"])

    return normalized


def _parse_bool(value: Any) -> bool | Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"true", "1", "yes", "y"}:
            return True
        if text in {"false", "0", "no", "n"}:
            return False
    return value


def _validation_errors(examples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, example in enumerate(examples, start=1):
        valid, messages = validate_benchmark_example(example)
        example_id = str(example.get("example_id") or f"row-{index}")
        if example_id in seen_ids:
            messages.append("duplicate example_id")
        seen_ids.add(example_id)
        if not valid or messages:
            errors.append({"example_id": example_id, "errors": messages})
    return errors


def _count_by(examples: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(example.get(field) or "unknown") for example in examples).items()))


def _save_splits(split_sets: dict[str, list[dict[str, Any]]], output_path: str) -> dict[str, str]:
    target = Path(output_path)
    paths: dict[str, str] = {}
    for name, items in split_sets.items():
        split_path = target.with_name(f"{target.stem}_{name}{target.suffix or '.jsonl'}")
        save_jsonl(items, str(split_path))
        paths[name] = str(split_path)
    return paths
