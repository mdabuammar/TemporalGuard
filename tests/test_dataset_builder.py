import json

import pytest

from temporalguard.data.dataset_builder import (
    build_benchmark_dataset,
    build_dataset,
    load_examples,
    save_jsonl,
    split_examples,
    summarize_benchmark,
    validate_benchmark_example,
)


def _example(example_id: str = "EX001", **overrides):
    data = {
        "example_id": example_id,
        "question": "What is the latest Python version?",
        "original_answer": "Python 3.10 is the latest stable version of Python.",
        "gold_temporal_category": "RECENT_ONLY",
        "gold_outdatedness_status": "OUTDATED",
        "gold_requires_correction": True,
        "gold_evidence_value": "Python 3.13.5",
        "gold_final_risk_label": "medium_risk",
        "domain": "software",
        "difficulty": "easy",
        "high_risk_domain": False,
        "source_notes": "Official Python download page checked manually.",
        "annotation_status": "verified",
    }
    data.update(overrides)
    return data


def test_validate_benchmark_example_accepts_valid_example() -> None:
    valid, errors = validate_benchmark_example(_example())

    assert valid is True
    assert errors == []


def test_validate_benchmark_example_rejects_missing_and_invalid_fields() -> None:
    invalid = _example(
        question="",
        gold_temporal_category="CURRENT",
        gold_outdatedness_status="STALE",
        gold_requires_correction="maybe",
        gold_final_risk_label="danger",
        domain="unknown_domain",
        difficulty="simple",
        annotation_status="done",
    )

    valid, errors = validate_benchmark_example(invalid)

    assert valid is False
    assert "missing required field: question" in errors
    assert "invalid gold_temporal_category" in errors
    assert "invalid gold_outdatedness_status" in errors
    assert "invalid gold_final_risk_label" in errors
    assert "invalid domain" in errors
    assert "invalid difficulty" in errors
    assert "invalid annotation_status" in errors
    assert "gold_requires_correction must be boolean" in errors


def test_load_examples_from_jsonl(tmp_path) -> None:
    path = tmp_path / "seed.jsonl"
    path.write_text(json.dumps(_example()) + "\n\n", encoding="utf-8")

    examples = load_examples(str(path))

    assert len(examples) == 1
    assert examples[0]["example_id"] == "EX001"


def test_load_examples_from_csv_and_normalize_booleans(tmp_path) -> None:
    path = tmp_path / "seed.csv"
    path.write_text(
        "example_id,question,original_answer,gold_temporal_category,gold_outdatedness_status,"
        "gold_requires_correction,gold_final_risk_label,domain,difficulty,high_risk_domain,annotation_status\n"
        "EX001,Question,Answer,recent_only,outdated,true,medium_risk,software,easy,false,verified\n",
        encoding="utf-8",
    )

    examples = build_dataset(load_examples(str(path)))

    assert examples[0]["gold_temporal_category"] == "RECENT_ONLY"
    assert examples[0]["gold_outdatedness_status"] == "OUTDATED"
    assert examples[0]["gold_requires_correction"] is True
    assert examples[0]["high_risk_domain"] is False


def test_save_jsonl_writes_normalized_records(tmp_path) -> None:
    path = tmp_path / "benchmark.jsonl"

    save_jsonl([_example(gold_temporal_category="recent_only")], str(path))

    saved = json.loads(path.read_text(encoding="utf-8").strip())
    assert saved["gold_temporal_category"] == "RECENT_ONLY"


def test_summarize_benchmark_counts_required_groups() -> None:
    examples = [
        _example("EX001", domain="software", difficulty="easy", annotation_status="verified"),
        _example(
            "EX002",
            gold_temporal_category="STATIC",
            gold_outdatedness_status="NOT_OUTDATED",
            gold_requires_correction=False,
            gold_final_risk_label="safe",
            domain="static_education",
            difficulty="medium",
            annotation_status="reviewed",
        ),
    ]

    summary = summarize_benchmark(examples)

    assert summary["total_examples"] == 2
    assert summary["temporal_category"] == {"RECENT_ONLY": 1, "STATIC": 1}
    assert summary["outdatedness_status"] == {"NOT_OUTDATED": 1, "OUTDATED": 1}
    assert summary["domain"] == {"software": 1, "static_education": 1}
    assert summary["difficulty"] == {"easy": 1, "medium": 1}
    assert summary["annotation_status"] == {"reviewed": 1, "verified": 1}


def test_split_examples_is_deterministic() -> None:
    examples = [_example(f"EX{i:03d}") for i in range(10)]

    first = split_examples(examples, seed=7)
    second = split_examples(examples, seed=7)

    assert first == second
    assert len(first["train"]) == 8
    assert len(first["dev"]) == 1
    assert len(first["test"]) == 1


def test_build_benchmark_dataset_saves_output_and_splits(tmp_path) -> None:
    input_path = tmp_path / "seed.jsonl"
    output_path = tmp_path / "benchmark.jsonl"
    examples = [
        _example("EX001"),
        _example(
            "EX002",
            gold_temporal_category="STATIC",
            gold_outdatedness_status="NOT_OUTDATED",
            gold_requires_correction=False,
            gold_final_risk_label="safe",
            domain="static_education",
        ),
        _example("EX003", domain="law_policy", high_risk_domain=True, difficulty="hard"),
    ]
    input_path.write_text("\n".join(json.dumps(item) for item in examples), encoding="utf-8")

    result = build_benchmark_dataset(str(input_path), str(output_path), split=True, seed=1)

    assert result["total_examples"] == 3
    assert output_path.exists()
    assert result["summary"]["domain"]["software"] == 1
    assert result["splits"] == {"train": 2, "dev": 1, "test": 0}
    assert set(result["split_paths"]) == {"train", "dev", "test"}


def test_build_benchmark_dataset_raises_for_invalid_examples(tmp_path) -> None:
    input_path = tmp_path / "seed.jsonl"
    output_path = tmp_path / "benchmark.jsonl"
    input_path.write_text(json.dumps(_example(gold_temporal_category="bad")), encoding="utf-8")

    with pytest.raises(ValueError, match="invalid gold_temporal_category"):
        build_benchmark_dataset(str(input_path), str(output_path))


def test_build_benchmark_dataset_rejects_duplicate_ids(tmp_path) -> None:
    input_path = tmp_path / "seed.jsonl"
    output_path = tmp_path / "benchmark.jsonl"
    rows = [_example("EX001"), _example("EX001")]
    input_path.write_text("\n".join(json.dumps(item) for item in rows), encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate example_id"):
        build_benchmark_dataset(str(input_path), str(output_path))
