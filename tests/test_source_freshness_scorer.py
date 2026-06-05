import json

import pytest

from temporalguard.skills.source_freshness_scorer import score_source_freshness


SCORING_DATETIME = "2026-06-05T12:00:00Z"


@pytest.mark.parametrize(
    ("name", "temporal_category", "evidence_payload", "expected_risk"),
    [
        (
            "fresh official current source",
            "RECENT_ONLY",
            {
                "evidence_results": [
                    {
                        "claim_id": "C1",
                        "claim_text": "Python 3.10 is the latest stable version of Python.",
                        "evidence_items": [
                            {
                                "evidence_id": "E1",
                                "url": "https://www.python.org/downloads/",
                                "source_type": "official",
                                "publisher": "Python Software Foundation",
                                "published_date": None,
                                "updated_date": "2026-06-01",
                                "retrieved_at": "2026-06-05T12:00:00Z",
                                "relevance_score": 0.95,
                            }
                        ],
                    }
                ]
            },
            "low",
        ),
        (
            "old source for current claim",
            "RECENT_ONLY",
            {
                "evidence_results": [
                    {
                        "claim_id": "C1",
                        "claim_text": "The latest TensorFlow version is 2.x.",
                        "evidence_items": [
                            {
                                "evidence_id": "E1",
                                "url": "https://example.com/tensorflow-old",
                                "source_type": "other",
                                "publisher": "unknown",
                                "published_date": "2022-01-01",
                                "updated_date": None,
                                "retrieved_at": "2026-06-05T12:00:00Z",
                                "relevance_score": 0.70,
                            }
                        ],
                    }
                ]
            },
            "high",
        ),
        (
            "historical government source",
            "HISTORICAL",
            {
                "evidence_results": [
                    {
                        "claim_id": "C1",
                        "claim_text": "Barack Obama was the president of the United States in 2016.",
                        "evidence_items": [
                            {
                                "evidence_id": "E1",
                                "url": "https://www.whitehouse.gov/about-the-white-house/presidents/",
                                "source_type": "government",
                                "publisher": "The White House",
                                "published_date": None,
                                "updated_date": None,
                                "retrieved_at": "2026-06-05T12:00:00Z",
                                "relevance_score": 0.90,
                            }
                        ],
                    }
                ]
            },
            "low",
        ),
        (
            "high risk policy source with no date",
            "RECENT_ONLY",
            {
                "evidence_results": [
                    {
                        "claim_id": "C1",
                        "claim_text": "The Canada student visa SDS program is no longer active.",
                        "evidence_items": [
                            {
                                "evidence_id": "E1",
                                "url": "https://example.com/visa-rule",
                                "source_type": "other",
                                "publisher": "unknown",
                                "published_date": None,
                                "updated_date": None,
                                "retrieved_at": "2026-06-05T12:00:00Z",
                                "relevance_score": 0.80,
                            }
                        ],
                    }
                ]
            },
            "critical",
        ),
        (
            "no evidence available",
            "TIME_SENSITIVE",
            {
                "evidence_results": [
                    {
                        "claim_id": "C1",
                        "claim_text": "Xyzabc system is currently active.",
                        "evidence_items": [],
                    }
                ]
            },
            "high",
        ),
    ],
)
def test_score_source_freshness_minimum_cases(
    name: str,
    temporal_category: str,
    evidence_payload: dict,
    expected_risk: str,
) -> None:
    del name
    result = score_source_freshness(evidence_payload, temporal_category, SCORING_DATETIME)

    assert result["freshness_results"][0]["claim_temporal_risk"] == expected_risk
    json.dumps(result)


def test_fresh_official_source_schema_and_scores() -> None:
    result = score_source_freshness(
        {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python 3.10 is the latest stable version of Python.",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "url": "https://www.python.org/downloads/",
                            "source_type": "official",
                            "publisher": "Python Software Foundation",
                            "published_date": None,
                            "updated_date": "2026-06-01",
                            "retrieved_at": "2026-06-05T12:00:00Z",
                            "relevance_score": 0.95,
                        }
                    ],
                }
            ]
        },
        "RECENT_ONLY",
        SCORING_DATETIME,
    )
    claim = result["freshness_results"][0]
    evidence = claim["evidence_scores"][0]

    assert claim["claim_id"] == "C1"
    assert claim["claim_freshness_score"] == 0.98
    assert claim["claim_reliability_score"] == 0.981
    assert claim["best_evidence_id"] == "E1"
    assert evidence["date_used"] == "2026-06-01"
    assert evidence["date_basis"] == "updated_date"
    assert evidence["source_age_days"] == 4
    assert evidence["freshness_label"] == "very_fresh"
    assert evidence["authority_score"] == 1.0
    assert evidence["relevance_score"] == 0.95
    assert evidence["combined_score"] == 0.981
    assert evidence["risk_flags"] == []
    assert result["overall_freshness_score"] == 0.981
    assert result["overall_temporal_risk"] == "low"


def test_updated_date_is_preferred_over_published_date() -> None:
    result = score_source_freshness(
        {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "claim_text": "The current policy is active.",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "url": "https://example.gov/policy",
                            "source_type": "government",
                            "publisher": "Government",
                            "published_date": "2020-01-01",
                            "updated_date": "2026-05-20",
                            "retrieved_at": "2026-06-05T12:00:00Z",
                            "relevance_score": 0.90,
                        }
                    ],
                }
            ]
        },
        "TIME_SENSITIVE",
        SCORING_DATETIME,
    )

    evidence = result["freshness_results"][0]["evidence_scores"][0]
    assert evidence["date_used"] == "2026-05-20"
    assert evidence["date_basis"] == "updated_date"
    assert evidence["source_age_days"] == 16


def test_year_only_date_adds_risk_flag() -> None:
    result = score_source_freshness(
        {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "claim_text": "The model achieved 92% accuracy.",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "url": "https://example.edu/paper",
                            "source_type": "academic",
                            "publisher": "Example University",
                            "published_date": "2024",
                            "updated_date": None,
                            "relevance_score": 0.90,
                        }
                    ],
                }
            ]
        },
        "STATIC",
        SCORING_DATETIME,
    )

    evidence = result["freshness_results"][0]["evidence_scores"][0]
    assert evidence["date_used"] == "2024"
    assert evidence["date_basis"] == "published_date"
    assert "year_only_date" in evidence["risk_flags"]


def test_malformed_date_does_not_crash_and_warns() -> None:
    result = score_source_freshness(
        {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "claim_text": "The latest package version is 1.0.",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "url": "https://example.com/pkg",
                            "source_type": "other",
                            "publisher": "unknown",
                            "published_date": "not-a-date",
                            "updated_date": None,
                            "relevance_score": 0.80,
                        }
                    ],
                }
            ]
        },
        "RECENT_ONLY",
        SCORING_DATETIME,
    )

    evidence = result["freshness_results"][0]["evidence_scores"][0]
    assert evidence["date_used"] is None
    assert evidence["date_basis"] == "unavailable"
    assert "malformed_date" in evidence["risk_flags"]
    assert result["scoring_warnings"]


def test_version_specific_official_undated_docs_are_acceptable() -> None:
    result = score_source_freshness(
        {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "claim_text": "In pandas 2.0, this method is deprecated.",
                    "evidence_need": "version_specific",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "url": "https://pandas.pydata.org/docs/",
                            "source_type": "documentation",
                            "publisher": "pandas",
                            "published_date": None,
                            "updated_date": None,
                            "retrieved_at": "2026-06-05T12:00:00Z",
                            "relevance_score": 0.85,
                        }
                    ],
                }
            ]
        },
        "VERSION_DEPENDENT",
        SCORING_DATETIME,
    )

    evidence = result["freshness_results"][0]["evidence_scores"][0]
    assert evidence["freshness_score"] >= 0.85
    assert "version_specific_claim" in evidence["risk_flags"]
    assert result["freshness_results"][0]["claim_temporal_risk"] in {"low", "medium"}


def test_empty_payload_returns_unknown_schema() -> None:
    result = score_source_freshness({}, "RECENT_ONLY", SCORING_DATETIME)

    assert result == {
        "freshness_results": [],
        "overall_freshness_score": 0.0,
        "overall_temporal_risk": "unknown",
        "scoring_warnings": ["No evidence results supplied for scoring."],
    }
