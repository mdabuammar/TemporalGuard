from fastapi.testclient import TestClient

from temporalguard.api import main


client = TestClient(main.app)


def _pipeline_output(question: str = "What is binary search?") -> dict:
    return {
        "question": question,
        "original_answer": "Binary search divides a sorted search space in half.",
        "temporal_detection": {"temporal_category": "STATIC", "needs_fresh_evidence": False},
        "claims": {"claims": [], "total_claims": 0},
        "evidence": {"evidence_results": []},
        "freshness": {"overall_freshness_score": 0.0},
        "verification": {"verification_results": [], "overall_verification_status": "NOT_VERIFIABLE"},
        "outdatedness": {"outdatedness_status": "NOT_APPLICABLE", "requires_correction": False},
        "correction": {"correction_status": "no_correction_needed", "corrected_answer": "Binary search divides a sorted search space in half."},
        "risk_label": {"final_risk_label": "safe", "dashboard_badge": "SAFE"},
    }


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": "temporalguard-api",
        "status": "ok",
        "version": "0.1.0",
    }


def test_cors_headers_for_local_frontend() -> None:
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_analyze_endpoint_uses_orchestrator(monkeypatch) -> None:
    calls = []

    def fake_pipeline(**kwargs):
        calls.append(kwargs)
        return _pipeline_output(kwargs["question"])

    monkeypatch.setattr(main, "run_temporalguard_pipeline", fake_pipeline)

    response = client.post(
        "/analyze",
        json={
            "question": "What is binary search?",
            "base_answer": "Binary search divides a sorted search space in half.",
            "report_type": "technical",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "What is binary search?"
    assert data["temporal_detection"]["temporal_category"] == "STATIC"
    assert calls[0]["base_answer"] == "Binary search divides a sorted search space in half."
    assert calls[0]["llm_provider"] is None
    assert calls[0]["search_provider"] is None
    assert calls[0]["report_type"] == "technical"


def test_analyze_endpoint_returns_structured_error(monkeypatch) -> None:
    def fake_pipeline(**kwargs):
        del kwargs
        raise RuntimeError("pipeline failed")

    monkeypatch.setattr(main, "run_temporalguard_pipeline", fake_pipeline)

    response = client.post("/analyze", json={"question": "What is current?"})

    assert response.status_code == 500
    detail = response.json()["detail"]
    assert detail["error_type"] == "pipeline_error"
    assert detail["module"] == "api.analyze"
    assert detail["recoverable"] is False
    assert detail["details"]["exception_type"] == "RuntimeError"


def test_batch_analyze_endpoint_continues_after_item_failure(monkeypatch) -> None:
    def fake_pipeline(**kwargs):
        if "bad" in kwargs["question"]:
            raise RuntimeError("bad item")
        return _pipeline_output(kwargs["question"])

    monkeypatch.setattr(main, "run_temporalguard_pipeline", fake_pipeline)

    response = client.post(
        "/batch-analyze",
        json={
            "items": [
                {"example_id": "EX001", "question": "good question", "base_answer": "answer"},
                {"example_id": "EX002", "question": "bad question", "base_answer": "answer"},
            ]
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_items"] == 2
    assert data["successful_items"] == 1
    assert data["failed_items"] == 1
    assert data["outputs"][0]["example_id"] == "EX001"
    assert data["errors"][0]["details"]["example_id"] == "EX002"


def test_report_endpoint_uses_report_generator(monkeypatch) -> None:
    def fake_report(pipeline_output, report_type="dashboard", max_evidence_items=5):
        return {
            "report_type": report_type,
            "max_evidence_items": max_evidence_items,
            "pipeline_question": pipeline_output["question"],
        }

    monkeypatch.setattr(main, "generate_report", fake_report)

    response = client.post(
        "/report",
        json={
            "pipeline_output": {"question": "Q"},
            "report_type": "thesis",
            "max_evidence_items": 3,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "report_type": "thesis",
        "max_evidence_items": 3,
        "pipeline_question": "Q",
    }


def test_evaluate_endpoint_uses_metrics_module() -> None:
    response = client.post(
        "/evaluate",
        json={
            "benchmark_examples": [
                {
                    "id": "EX001",
                    "domain": "static_education",
                    "difficulty": "easy",
                    "expected_temporal_category": "STATIC",
                    "expected_outdatedness_status": "NOT_OUTDATED",
                    "expected_requires_correction": False,
                    "expected_risk_label": "safe",
                }
            ],
            "system_outputs": [
                {
                    "id": "EX001",
                    "temporal_detection": {"temporal_category": "STATIC"},
                    "outdatedness": {"outdatedness_status": "NOT_OUTDATED", "requires_correction": False},
                    "correction": {"correction_status": "no_correction_needed"},
                    "risk_label": {"final_risk_label": "safe"},
                }
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_examples"] == 1
    assert data["temporal_category_accuracy"] == 1.0
    assert data["outdatedness_accuracy"] == 1.0
    assert data["risk_label_accuracy"] == 1.0


def test_request_validation_rejects_empty_question() -> None:
    response = client.post("/analyze", json={"question": ""})

    assert response.status_code == 422
