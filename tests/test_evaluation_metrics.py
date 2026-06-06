from temporalguard.evaluation.metrics import compute_metrics, evaluate_pipeline_outputs


def test_compute_metrics_covers_required_rates_and_breakdowns() -> None:
    benchmark = [
        {
            "id": "ex-1",
            "domain": "software",
            "difficulty": "easy",
            "expected_temporal_category": "RECENT_ONLY",
            "expected_outdatedness_status": "OUTDATED",
            "expected_requires_correction": True,
            "expected_risk_label": "medium_risk",
        },
        {
            "id": "ex-2",
            "domain": "education",
            "difficulty": "easy",
            "expected_temporal_category": "STATIC",
            "expected_outdatedness_status": "NOT_OUTDATED",
            "expected_requires_correction": False,
            "expected_risk_label": "safe",
        },
        {
            "id": "ex-3",
            "domain": "policy",
            "difficulty": "hard",
            "expected_temporal_category": "RECENT_ONLY",
            "expected_outdatedness_status": "UNVERIFIED_RISKY",
            "expected_requires_correction": True,
            "expected_correction_status": "unable_to_correct",
            "expected_risk_label": "critical_risk",
        },
    ]
    outputs = [
        {
            "id": "ex-1",
            "temporal_detection": {"temporal_category": "RECENT_ONLY"},
            "outdatedness": {"outdatedness_status": "OUTDATED", "requires_correction": True},
            "correction": {"correction_status": "corrected", "corrected_answer": "Python 3.13 is current."},
            "risk_label": {"final_risk_label": "medium_risk"},
        },
        {
            "id": "ex-2",
            "temporal_detection": {"temporal_category": "STATIC"},
            "outdatedness": {"outdatedness_status": "NOT_OUTDATED", "requires_correction": False},
            "correction": {"correction_status": "no_correction_needed"},
            "risk_label": {"final_risk_label": "safe"},
        },
        {
            "id": "ex-3",
            "temporal_detection": {"temporal_category": "STATIC"},
            "outdatedness": {"outdatedness_status": "NOT_ENOUGH_INFORMATION", "requires_correction": False},
            "correction": {"correction_status": "no_correction_needed"},
            "risk_label": {"final_risk_label": "unknown_risk"},
        },
    ]

    metrics = compute_metrics(outputs, benchmark)

    assert metrics["total_examples"] == 3
    assert metrics["evaluated_examples"] == 3
    assert metrics["temporal_category_accuracy"] == 2 / 3
    assert metrics["outdatedness_accuracy"] == 2 / 3
    assert metrics["correction_success_rate"] == 1 / 2
    assert metrics["unsupported_correction_avoidance"] == 1.0
    assert metrics["risk_label_accuracy"] == 2 / 3
    assert metrics["end_to_end"]["exact_decision_match_rate"] == 2 / 3
    assert metrics["domain_breakdown"]["software"]["count"] == 1
    assert metrics["domain_breakdown"]["software"]["end_to_end_accuracy"] == 1.0
    assert metrics["difficulty_breakdown"]["hard"]["risk_label_accuracy"] == 0.0
    assert metrics["error_analysis"]["mismatch_counts"]["risk_label_correct"] == 1
    assert metrics["error_analysis"]["mismatched_examples"][0]["id"] == "ex-3"


def test_compute_metrics_pairs_by_id_when_outputs_are_shuffled() -> None:
    benchmark = [
        {"id": "a", "expected_temporal_category": "STATIC"},
        {"id": "b", "expected_temporal_category": "RECENT_ONLY"},
    ]
    outputs = [
        {"id": "b", "temporal_detection": {"temporal_category": "RECENT_ONLY"}},
        {"id": "a", "temporal_detection": {"temporal_category": "STATIC"}},
    ]

    metrics = compute_metrics(outputs, benchmark)

    assert metrics["temporal_category_accuracy"] == 1.0
    assert metrics["error_analysis"]["missing_output_count"] == 0


def test_compute_metrics_handles_missing_output_and_extra_output() -> None:
    benchmark = [
        {"id": "a", "expected_temporal_category": "STATIC"},
        {"id": "b", "expected_temporal_category": "RECENT_ONLY"},
    ]
    outputs = [
        {"id": "a", "temporal_detection": {"temporal_category": "STATIC"}},
        {"id": "extra", "temporal_detection": {"temporal_category": "STATIC"}},
    ]

    metrics = compute_metrics(outputs, benchmark)

    assert metrics["temporal_category_accuracy"] == 0.5
    assert metrics["error_analysis"]["missing_output_count"] == 1
    assert metrics["error_analysis"]["extra_output_count"] == 0


def test_compute_metrics_supports_nested_expected_labels_and_report_summary_output() -> None:
    benchmark = [
        {
            "id": "nested",
            "expected": {
                "temporal_category": "RECENT_ONLY",
                "outdatedness_status": "OUTDATED",
                "risk_label": "medium_risk",
                "requires_correction": True,
                "correction_status": "corrected",
            },
        }
    ]
    outputs = [
        {
            "id": "nested",
            "report": {
                "pipeline_summary": {
                    "temporal_category": "RECENT_ONLY",
                    "outdatedness_status": "OUTDATED",
                    "final_risk_label": "medium_risk",
                    "correction_status": "corrected",
                }
            },
            "correction": {"corrected_answer": "Updated answer."},
        }
    ]

    metrics = compute_metrics(outputs, benchmark)

    assert metrics["temporal_category_accuracy"] == 1.0
    assert metrics["outdatedness_accuracy"] == 1.0
    assert metrics["risk_label_accuracy"] == 1.0
    assert metrics["correction_success_rate"] == 1.0


def test_compute_metrics_uses_order_when_ids_are_absent() -> None:
    benchmark = [{"label": "STATIC"}, {"label": "RECENT_ONLY"}]
    outputs = [
        {"temporal_detection": {"temporal_category": "STATIC"}},
        {"temporal_detection": {"temporal_category": "RECENT_ONLY"}},
    ]

    assert compute_metrics(outputs, benchmark)["temporal_category_accuracy"] == 1.0


def test_evaluate_pipeline_outputs_alias_names_benchmark_first() -> None:
    benchmark = [{"label": "STATIC"}]
    outputs = [{"temporal_detection": {"temporal_category": "STATIC"}}]

    assert evaluate_pipeline_outputs(benchmark, outputs)["temporal_category_accuracy"] == 1.0


def test_empty_inputs_return_empty_scored_metrics() -> None:
    metrics = compute_metrics([], [])

    assert metrics["total_examples"] == 0
    assert metrics["evaluated_examples"] == 0
    assert metrics["temporal_category_accuracy"] is None
    assert metrics["end_to_end"]["scored_examples"] == 0
    assert metrics["domain_breakdown"] == {}
    assert metrics["difficulty_breakdown"] == {}
