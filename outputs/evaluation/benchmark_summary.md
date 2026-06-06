# TemporalGuard Benchmark Summary

| dataset name | total examples | temporal category accuracy | outdatedness accuracy | correction success rate | unsupported correction avoidance | risk label accuracy | main error types |
| --- | --- | --- | --- | --- | --- | --- | --- |
| sample_benchmark_20 | 20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | none |
| benchmark_50 | 50 | 0.9600 | 0.9600 | 1.0000 | 0.7500 | 0.9600 | temporal_category_correct=2, outdatedness_correct=2, unsupported_correction_avoided=1, risk_label_correct=2 |
| benchmark_100 | 100 | 0.9200 | 0.8800 | 0.9889 | 0.6000 | 0.8900 | temporal_category_correct=8, outdatedness_correct=12, correction_success=1, unsupported_correction_avoided=4, risk_label_correct=11 |
| benchmark_200 | 200 | 0.9200 | 0.8900 | 0.9833 | 0.6000 | 0.8950 | temporal_category_correct=16, outdatedness_correct=22, correction_success=3, unsupported_correction_avoided=8, risk_label_correct=21 |
| benchmark_400 | 400 | 0.8925 | 0.8825 | 0.9861 | 0.5500 | 0.8975 | temporal_category_correct=43, outdatedness_correct=47, correction_success=5, unsupported_correction_avoided=18, risk_label_correct=41 |

Assumptions:
- Gold-field mock search provider returns one authoritative result per example.
- scoring_datetime fixed at 2026-06-06T00:00:00Z.
- No web search, LLM, real API, frontend, or pipeline-logic changes used.
