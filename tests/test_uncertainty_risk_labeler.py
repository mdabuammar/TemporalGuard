from temporalguard.skills.uncertainty_risk_labeler import label_uncertainty_and_risk


def test_label_uncertainty_and_risk_defaults():
    assert label_uncertainty_and_risk("answer") == {"uncertainty": "low", "risk": "low"}
