from temporalguard.skills.source_freshness_scorer import score_source_freshness


def test_score_source_freshness_defaults_to_zero():
    assert score_source_freshness({}) == 0.0
