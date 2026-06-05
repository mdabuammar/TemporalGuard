import json

import pytest

from temporalguard.search.providers import SearchResult
from temporalguard.pipeline import orchestrator
from temporalguard.pipeline.orchestrator import run_pipeline, run_temporalguard_pipeline


class MockSearchProvider:
    def __init__(self, results: list[SearchResult] | None = None) -> None:
        self.results = results or []
        self.queries: list[str] = []

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        self.queries.append(query)
        return self.results[:max_results]


class MockLLMProvider:
    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.prompts: list[str] = []

    def generate(self, prompt: str, **kwargs) -> dict:
        del kwargs
        self.prompts.append(prompt)
        return {"answer": self.answer, "model_name": "mock-model", "provider": "mock"}


def test_static_question_with_provided_answer_returns_full_output() -> None:
    result = run_temporalguard_pipeline(
        question="What is binary search?",
        base_answer="Binary search is an algorithm that repeatedly divides a sorted search space in half to find a target value.",
        config={"scoring_datetime": "2026-06-05T12:00:00Z"},
    )

    assert result["question"] == "What is binary search?"
    assert result["original_answer"].startswith("Binary search")
    assert result["temporal_detection"]["temporal_category"] == "STATIC"
    assert result["claims"]["total_claims"] == 1
    assert result["pipeline_status"] in {"success", "partial_success"}
    assert set(
        [
            "run_id",
            "question",
            "original_answer",
            "temporal_detection",
            "claims",
            "evidence",
            "freshness",
            "verification",
            "outdatedness",
            "correction",
            "risk_label",
            "report",
            "runtime",
            "pipeline_status",
            "errors",
            "warnings",
        ]
    ).issubset(result)
    json.dumps(result)


def test_recent_software_question_with_mock_evidence_runs_end_to_end() -> None:
    provider = MockSearchProvider(
        [
            SearchResult(
                title="Download Python",
                url="https://www.python.org/downloads/",
                snippet="The official Python downloads page lists Python 3.13.5 as the latest release.",
                publisher="Python Software Foundation",
                source_type="official",
                updated_date="2026-06-01",
            )
        ]
    )

    result = run_temporalguard_pipeline(
        question="What is the latest Python version?",
        base_answer="Python 3.10 is the latest stable version of Python.",
        search_provider=provider,
        config={"scoring_datetime": "2026-06-05T12:00:00Z"},
        report_type="technical",
    )

    assert provider.queries
    assert result["temporal_detection"]["temporal_category"] == "RECENT_ONLY"
    assert result["evidence"]["total_evidence_items"] >= 1
    assert result["verification"]["verification_results"][0]["verification_status"] == "OUTDATED"
    assert result["outdatedness"]["outdatedness_status"] == "OUTDATED"
    assert result["correction"]["correction_status"] == "corrected"
    assert result["risk_label"]["dashboard_badge"] == "OUTDATED - CORRECTED"
    assert result["report"]["report_type"] == "technical"


def test_missing_search_provider_continues_with_partial_success() -> None:
    result = run_temporalguard_pipeline(
        question="What is the latest Python version?",
        base_answer="Python 3.10 is the latest stable version of Python.",
        search_provider=None,
        config={"scoring_datetime": "2026-06-05T12:00:00Z"},
    )

    assert result["pipeline_status"] == "partial_success"
    assert result["evidence"]["evidence_results"][0]["retrieval_status"] == "failed"
    assert "No search provider supplied; evidence retrieval failed." in result["warnings"]
    assert result["risk_label"]["final_risk_label"] in {"high_risk", "unknown_risk", "medium_risk"}


def test_base_answer_missing_uses_mock_llm_provider() -> None:
    llm = MockLLMProvider("Python 3.10 is the latest stable version of Python.")

    result = run_temporalguard_pipeline(
        question="What is the latest Python version?",
        base_answer=None,
        llm_provider=llm,
        search_provider=MockSearchProvider(),
    )

    assert "What is the latest Python version?" in llm.prompts[0]
    assert result["original_answer"] == "Python 3.10 is the latest stable version of Python."


def test_skill_failure_returns_partial_success(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_extract(*args, **kwargs):
        del args, kwargs
        raise RuntimeError("simulated extraction failure")

    monkeypatch.setattr(orchestrator, "extract_claims", fail_extract)

    result = run_temporalguard_pipeline(
        question="What is the latest Python version?",
        base_answer="Python 3.10 is the latest stable version of Python.",
    )

    assert result["pipeline_status"] == "partial_success"
    assert result["claims"]["total_claims"] == 0
    assert result["errors"][0]["step"] == "claims"
    assert "simulated extraction failure" in result["errors"][0]["message"]


def test_run_pipeline_backward_wrapper_uses_config() -> None:
    result = run_pipeline(
        "What is binary search?",
        {
            "base_answer": "Binary search is an algorithm that repeatedly divides a sorted search space in half to find a target value.",
            "report_type": "debug",
        },
    )

    assert result["question"] == "What is binary search?"
    assert result["report"]["report_type"] == "debug"
