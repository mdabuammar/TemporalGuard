import json

from temporalguard.evaluation import model_comparison
from temporalguard.evaluation.model_comparison import compare_models, run_model_comparison


class MockModelProvider:
    def __init__(self, answer: str, model_name: str) -> None:
        self.answer = answer
        self.model_name = model_name
        self.prompts: list[str] = []

    def generate(self, prompt: str, **kwargs):
        del kwargs
        self.prompts.append(prompt)
        return {"answer": self.answer, "model_name": self.model_name, "provider": "mock"}


class FailingModelProvider:
    def generate(self, prompt: str, **kwargs):
        del prompt, kwargs
        raise RuntimeError("model unavailable")


class MockSearchProvider:
    def __init__(self) -> None:
        self.used = True


def _benchmark() -> list[dict]:
    return [
        {
            "example_id": "EX001",
            "question": "What is binary search?",
            "gold_temporal_category": "STATIC",
            "gold_outdatedness_status": "NOT_OUTDATED",
            "gold_requires_correction": False,
            "gold_final_risk_label": "safe",
            "domain": "static_education",
            "difficulty": "easy",
        },
        {
            "example_id": "EX002",
            "question": "What is the latest Python version?",
            "gold_temporal_category": "RECENT_ONLY",
            "gold_outdatedness_status": "OUTDATED",
            "gold_requires_correction": True,
            "gold_final_risk_label": "medium_risk",
            "domain": "software",
            "difficulty": "easy",
        },
    ]


def _pipeline_output(question: str, base_answer: str) -> dict:
    if "latest Python" in question:
        if "3.14" in base_answer:
            outdatedness = "NOT_OUTDATED"
            correction_status = "no_correction_needed"
            risk = "safe"
            requires_correction = False
        else:
            outdatedness = "OUTDATED"
            correction_status = "corrected"
            risk = "medium_risk"
            requires_correction = True
        temporal = "RECENT_ONLY"
    else:
        outdatedness = "NOT_OUTDATED"
        correction_status = "no_correction_needed"
        risk = "safe"
        requires_correction = False
        temporal = "STATIC"
    return {
        "question": question,
        "original_answer": base_answer,
        "temporal_detection": {"temporal_category": temporal},
        "outdatedness": {"outdatedness_status": outdatedness, "requires_correction": requires_correction},
        "correction": {"correction_status": correction_status, "corrected_answer": base_answer or "corrected"},
        "risk_label": {"final_risk_label": risk, "trust_score": 0.9},
    }


def test_run_model_comparison_saves_outputs_and_metrics(tmp_path, monkeypatch) -> None:
    calls = []

    def fake_pipeline(**kwargs):
        calls.append(kwargs)
        return _pipeline_output(kwargs["question"], kwargs["base_answer"])

    monkeypatch.setattr(model_comparison, "run_temporalguard_pipeline", fake_pipeline)
    search_provider = MockSearchProvider()
    providers = {
        "stale_model": MockModelProvider("Python 3.10 is latest.", "stale"),
        "fresh_model": MockModelProvider("Python 3.14 is latest.", "fresh"),
    }

    result = run_model_comparison(
        _benchmark(),
        providers,
        search_provider=search_provider,
        output_dir=str(tmp_path),
    )

    assert result["models"] == ["stale_model", "fresh_model"]
    assert result["total_examples"] == 2
    assert set(result["model_results"]) == {"stale_model", "fresh_model"}
    assert result["best_model"] == "stale_model"
    assert result["errors"] == []
    assert len(calls) == 4
    assert all(call["search_provider"] is search_provider for call in calls)
    assert providers["stale_model"].prompts

    for model_name in providers:
        path = tmp_path / f"{model_name}_outputs.jsonl"
        assert path.exists()
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        assert len(rows) == 2
        assert rows[0]["model_name"] == model_name

    stale_metrics = result["model_results"]["stale_model"]["metrics"]
    fresh_metrics = result["model_results"]["fresh_model"]["metrics"]
    assert stale_metrics["outdatedness_accuracy"] == 1.0
    assert fresh_metrics["outdatedness_accuracy"] == 0.5
    json.dumps(result)


def test_run_model_comparison_handles_provider_failure(tmp_path, monkeypatch) -> None:
    def fake_pipeline(**kwargs):
        return _pipeline_output(kwargs["question"], kwargs["base_answer"])

    monkeypatch.setattr(model_comparison, "run_temporalguard_pipeline", fake_pipeline)

    result = run_model_comparison(
        _benchmark(),
        {
            "ok_model": MockModelProvider("Python 3.10 is latest.", "ok"),
            "bad_model": FailingModelProvider(),
        },
        output_dir=str(tmp_path),
    )

    assert result["total_examples"] == 2
    assert result["best_model"] == "ok_model"
    assert len(result["errors"]) == 2
    assert result["model_results"]["bad_model"]["errors"][0]["error_type"] == "answer_generation_failed"

    bad_rows = [json.loads(line) for line in (tmp_path / "bad_model_outputs.jsonl").read_text(encoding="utf-8").splitlines()]
    assert bad_rows[0]["pipeline_status"] == "failed"
    assert bad_rows[0]["errors"][0]["recoverable"] is True


def test_run_model_comparison_respects_max_examples(tmp_path, monkeypatch) -> None:
    calls = []

    def fake_pipeline(**kwargs):
        calls.append(kwargs)
        return _pipeline_output(kwargs["question"], kwargs["base_answer"])

    monkeypatch.setattr(model_comparison, "run_temporalguard_pipeline", fake_pipeline)

    result = run_model_comparison(
        _benchmark(),
        {"model": MockModelProvider("answer", "model")},
        output_dir=str(tmp_path),
        max_examples=1,
    )

    assert result["total_examples"] == 1
    assert len(calls) == 1
    assert result["model_results"]["model"]["metrics"]["total_examples"] == 1


def test_run_model_comparison_handles_empty_model_dict(tmp_path) -> None:
    result = run_model_comparison(_benchmark(), {}, output_dir=str(tmp_path))

    assert result["models"] == []
    assert result["model_results"] == {}
    assert result["comparison_table"] == []
    assert result["best_model"] is None
    assert result["warnings"][0]["error_type"] == "no_models"


def test_compare_models_ranks_precomputed_rows() -> None:
    result = compare_models(
        [
            {"model_name": "weak", "exact_decision_match_rate": 0.5, "error_count": 0},
            {"model_name": "strong", "exact_decision_match_rate": 0.9, "error_count": 1},
        ]
    )

    assert result["models"] == ["weak", "strong"]
    assert result["best_model"] == "strong"
