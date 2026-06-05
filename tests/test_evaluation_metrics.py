from temporalguard.evaluation.metrics import compute_metrics


def test_compute_metrics_returns_mapping():
    assert compute_metrics([], []) == {}
