from temporalguard.skills.temporal_verifier import verify_temporal_claim


def test_verify_temporal_claim_returns_scaffold_result():
    assert verify_temporal_claim("claim", []) == {"verified": False, "reason": "scaffold"}
