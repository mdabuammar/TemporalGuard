from temporalguard.evaluation.model_comparison import compare_models


def test_compare_models_returns_scaffold_status():
    assert compare_models([]) == {"status": "scaffold"}
