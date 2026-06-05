from temporalguard.skills.fresh_evidence_retriever import retrieve_fresh_evidence


def test_retrieve_fresh_evidence_returns_empty_list():
    assert retrieve_fresh_evidence("TemporalGuard") == []
