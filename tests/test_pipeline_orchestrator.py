from temporalguard.pipeline.orchestrator import run_pipeline


def test_run_pipeline_returns_scaffold_result():
    result = run_pipeline("What is TemporalGuard?")
    assert result["status"] == "scaffold"
