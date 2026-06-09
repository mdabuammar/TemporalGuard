import json

import pytest

from temporalguard.skills.temporal_verifier import verify_temporal_claim, verify_temporal_claims


@pytest.mark.parametrize(
    (
        "name",
        "question",
        "temporal_category",
        "claims_payload",
        "evidence_payload",
        "freshness_payload",
        "expected_status",
    ),
    [
        (
            "outdated latest Python claim",
            "What is the latest Python version?",
            "RECENT_ONLY",
            {
                "claims": [
                    {
                        "claim_id": "C1",
                        "claim_text": "Python 3.10 is the latest stable version of Python.",
                        "normalized_claim": "Python 3.10 is the latest stable Python version.",
                        "claim_type": "software_version",
                        "entities": ["Python", "Python 3.10"],
                        "temporal_anchor": "latest",
                        "evidence_need": "fresh",
                    }
                ]
            },
            {
                "evidence_results": [
                    {
                        "claim_id": "C1",
                        "evidence_items": [
                            {
                                "evidence_id": "E1",
                                "title": "Download Python",
                                "source_type": "official",
                                "publisher": "Python Software Foundation",
                                "evidence_summary": (
                                    "The official Python downloads page lists Python 3.13.5 as the latest release."
                                ),
                                "relevance_score": 0.95,
                            }
                        ],
                        "retrieval_status": "success",
                    }
                ]
            },
            {
                "freshness_results": [
                    {
                        "claim_id": "C1",
                        "claim_freshness_score": 0.98,
                        "claim_reliability_score": 0.98,
                        "claim_temporal_risk": "low",
                        "best_evidence_id": "E1",
                    }
                ]
            },
            "OUTDATED",
        ),
        (
            "supported historical president claim",
            "Who was the president of the USA in 2016?",
            "HISTORICAL",
            {
                "claims": [
                    {
                        "claim_id": "C1",
                        "claim_text": "Barack Obama was the president of the United States in 2016.",
                        "claim_type": "historical_fact",
                        "entities": ["Barack Obama", "United States", "president"],
                        "temporal_anchor": "2016",
                        "evidence_need": "historical",
                    }
                ]
            },
            {
                "evidence_results": [
                    {
                        "claim_id": "C1",
                        "evidence_items": [
                            {
                                "evidence_id": "E1",
                                "title": "Presidents of the United States",
                                "source_type": "government",
                                "publisher": "The White House",
                                "evidence_summary": (
                                    "Barack Obama served as the 44th President of the United States from 2009 to 2017."
                                ),
                                "relevance_score": 0.90,
                            }
                        ],
                        "retrieval_status": "success",
                    }
                ]
            },
            {
                "freshness_results": [
                    {
                        "claim_id": "C1",
                        "claim_freshness_score": 0.90,
                        "claim_reliability_score": 0.95,
                        "claim_temporal_risk": "low",
                        "best_evidence_id": "E1",
                    }
                ]
            },
            "SUPPORTED",
        ),
        (
            "contradicted world cup claim",
            "Who won the 2014 FIFA World Cup?",
            "HISTORICAL",
            {
                "claims": [
                    {
                        "claim_id": "C1",
                        "claim_text": "France won the 2014 FIFA World Cup.",
                        "claim_type": "event_result",
                        "entities": ["France", "2014 FIFA World Cup"],
                        "temporal_anchor": "2014",
                        "evidence_need": "historical",
                    }
                ]
            },
            {
                "evidence_results": [
                    {
                        "claim_id": "C1",
                        "evidence_items": [
                            {
                                "evidence_id": "E1",
                                "title": "2014 FIFA World Cup",
                                "source_type": "official",
                                "publisher": "FIFA",
                                "evidence_summary": "Germany won the 2014 FIFA World Cup.",
                                "relevance_score": 0.95,
                            }
                        ],
                        "retrieval_status": "success",
                    }
                ]
            },
            {
                "freshness_results": [
                    {
                        "claim_id": "C1",
                        "claim_freshness_score": 0.90,
                        "claim_reliability_score": 0.95,
                        "claim_temporal_risk": "low",
                        "best_evidence_id": "E1",
                    }
                ]
            },
            "CONTRADICTED",
        ),
        (
            "insufficient evidence for unknown current system",
            "Is Xyzabc system currently active?",
            "RECENT_ONLY",
            {
                "claims": [
                    {
                        "claim_id": "C1",
                        "claim_text": "The Xyzabc system is currently active.",
                        "claim_type": "current_status",
                        "entities": ["Xyzabc system"],
                        "temporal_anchor": "current",
                        "evidence_need": "fresh",
                    }
                ]
            },
            {"evidence_results": [{"claim_id": "C1", "evidence_items": [], "retrieval_status": "failed"}]},
            {
                "freshness_results": [
                    {
                        "claim_id": "C1",
                        "claim_freshness_score": 0.0,
                        "claim_reliability_score": 0.0,
                        "claim_temporal_risk": "high",
                        "best_evidence_id": None,
                    }
                ]
            },
            "INSUFFICIENT_EVIDENCE",
        ),
        (
            "supported static definition",
            "What is binary search?",
            "STATIC",
            {
                "claims": [
                    {
                        "claim_id": "C1",
                        "claim_text": "Binary search divides a sorted search space in half.",
                        "claim_type": "definition",
                        "entities": ["binary search"],
                        "temporal_anchor": None,
                        "evidence_need": "optional",
                    }
                ]
            },
            {
                "evidence_results": [
                    {
                        "claim_id": "C1",
                        "evidence_items": [
                            {
                                "evidence_id": "E1",
                                "title": "Binary Search",
                                "source_type": "academic",
                                "publisher": "Educational Source",
                                "evidence_summary": (
                                    "Binary search works by repeatedly dividing a sorted search interval in half."
                                ),
                                "relevance_score": 0.90,
                            }
                        ],
                        "retrieval_status": "success",
                    }
                ]
            },
            {
                "freshness_results": [
                    {
                        "claim_id": "C1",
                        "claim_freshness_score": 0.70,
                        "claim_reliability_score": 0.90,
                        "claim_temporal_risk": "low",
                        "best_evidence_id": "E1",
                    }
                ]
            },
            "SUPPORTED",
        ),
    ],
)
def test_verify_temporal_claims_minimum_cases(
    name: str,
    question: str,
    temporal_category: str,
    claims_payload: dict,
    evidence_payload: dict,
    freshness_payload: dict,
    expected_status: str,
) -> None:
    del name
    result = verify_temporal_claims(
        question,
        claims_payload,
        evidence_payload,
        freshness_payload,
        temporal_category,
    )

    assert result["verification_results"][0]["verification_status"] == expected_status
    json.dumps(result)


def test_outdated_python_result_has_conflict_fields() -> None:
    result = verify_temporal_claims(
        "What is the latest Python version?",
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python 3.10 is the latest stable version of Python.",
                    "claim_type": "software_version",
                    "entities": ["Python", "Python 3.10"],
                    "temporal_anchor": "latest",
                    "evidence_need": "fresh",
                }
            ]
        },
        {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "title": "Download Python",
                            "publisher": "Python Software Foundation",
                            "evidence_summary": "The official Python downloads page lists Python 3.13.5 as the latest release.",
                            "relevance_score": 0.95,
                        }
                    ],
                }
            ]
        },
        {
            "freshness_results": [
                {
                    "claim_id": "C1",
                    "claim_freshness_score": 0.98,
                    "claim_reliability_score": 0.98,
                    "claim_temporal_risk": "low",
                    "best_evidence_id": "E1",
                }
            ]
        },
        "RECENT_ONLY",
    )
    verification = result["verification_results"][0]

    assert verification["temporal_validity"] == "expired"
    assert verification["evidence_used"] == ["E1"]
    assert verification["best_evidence_id"] == "E1"
    assert verification["claim_value"] == "Python 3.10"
    assert verification["evidence_value"] == "Python 3.13.5"
    assert verification["detected_conflict"] == "Claim value: Python 3.10; Evidence value: Python 3.13.5."
    assert verification["requires_correction"] is True
    assert verification["risk_level"] == "high"
    assert result["overall_verification_status"] == "NEEDS_CORRECTION"


def test_python_compact_version_matches_spaced_evidence_version() -> None:
    result = verify_temporal_claims(
        "What is the latest Python version?",
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python3.14 is the latest Python version.",
                    "claim_type": "software_version",
                    "entities": ["Python"],
                    "temporal_anchor": "latest",
                    "evidence_need": "fresh",
                }
            ]
        },
        {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "title": "Python 3.14.5 is available",
                            "publisher": "Python Software Foundation",
                            "evidence_summary": "The latest release is Python 3.14.5.",
                            "evidence_value": "Python 3.14.5",
                            "source_type": "official",
                            "relevance_score": 0.98,
                        }
                    ],
                }
            ]
        },
        {
            "freshness_results": [
                {
                    "claim_id": "C1",
                    "claim_freshness_score": 0.98,
                    "claim_reliability_score": 0.98,
                    "claim_temporal_risk": "low",
                    "best_evidence_id": "E1",
                }
            ]
        },
        "RECENT_ONLY",
    )
    verification = result["verification_results"][0]

    assert verification["verification_status"] == "SUPPORTED"
    assert verification["claim_value"] == "Python 3.14"
    assert verification["evidence_value"] == "Python 3.14.5"
    assert verification["detected_conflict"] is None


def test_latest_python_older_major_minor_is_outdated_against_newer_evidence() -> None:
    result = verify_temporal_claims(
        "What is the latest Python version?",
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python 3.10 is the latest Python version.",
                    "claim_type": "software_version",
                    "entities": ["Python"],
                    "temporal_anchor": "latest",
                    "evidence_need": "fresh",
                }
            ]
        },
        {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "title": "Python 3.14.5 release",
                            "publisher": "Python Software Foundation",
                            "evidence_summary": "Latest release is Python 3.14.5.",
                            "source_type": "official",
                            "relevance_score": 0.98,
                        }
                    ],
                }
            ]
        },
        {
            "freshness_results": [
                {
                    "claim_id": "C1",
                    "claim_freshness_score": 0.98,
                    "claim_reliability_score": 0.98,
                    "claim_temporal_risk": "low",
                    "best_evidence_id": "E1",
                }
            ]
        },
        "RECENT_ONLY",
    )
    verification = result["verification_results"][0]

    assert verification["verification_status"] == "OUTDATED"
    assert verification["claim_value"] == "Python 3.10"
    assert verification["evidence_value"] == "Python 3.14.5"


def test_latest_python_3124_claim_is_outdated_against_3145_evidence() -> None:
    result = verify_temporal_claims(
        "What is the latest Python version?",
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "The latest Python version is 3.12.4.",
                    "claim_type": "software_version",
                    "entities": ["Python"],
                    "temporal_anchor": "latest",
                    "evidence_need": "fresh",
                }
            ]
        },
        {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "title": "Download Python",
                            "url": "https://www.python.org/downloads/",
                            "publisher": "Python Software Foundation",
                            "evidence_summary": "Download Python 3.14.5.",
                            "evidence_value": "Python 3.14.5",
                            "source_type": "official",
                            "relevance_score": 0.98,
                        }
                    ],
                }
            ]
        },
        {
            "freshness_results": [
                {
                    "claim_id": "C1",
                    "claim_freshness_score": 0.98,
                    "claim_reliability_score": 0.98,
                    "claim_temporal_risk": "low",
                    "best_evidence_id": "E1",
                }
            ]
        },
        "RECENT_ONLY",
    )
    verification = result["verification_results"][0]

    assert verification["verification_status"] == "OUTDATED"
    assert verification["claim_value"] == "3.12.4"
    assert verification["evidence_value"] == "Python 3.14.5"


def test_python_stable_release_preferred_over_future_development_version() -> None:
    result = verify_temporal_claims(
        "What is the latest Python version?",
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python 3.10 is the latest Python version.",
                    "claim_type": "software_version",
                    "entities": ["Python"],
                    "temporal_anchor": "latest",
                    "evidence_need": "fresh",
                }
            ]
        },
        {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "title": "Download Python 3.14.5",
                            "publisher": "Python Software Foundation",
                            "evidence_summary": (
                                "Python 3.14.5 is the latest stable release available for download. "
                                "Python 3.16 is a future development preview."
                            ),
                            "evidence_value": "Python 3.14.5",
                            "source_type": "official",
                            "relevance_score": 0.99,
                        }
                    ],
                }
            ]
        },
        {
            "freshness_results": [
                {
                    "claim_id": "C1",
                    "claim_freshness_score": 0.98,
                    "claim_reliability_score": 0.98,
                    "claim_temporal_risk": "low",
                    "best_evidence_id": "E1",
                }
            ]
        },
        "RECENT_ONLY",
    )
    verification = result["verification_results"][0]

    assert verification["verification_status"] == "OUTDATED"
    assert verification["claim_value"] == "Python 3.10"
    assert verification["evidence_value"] == "Python 3.14.5"
    assert "3.16" not in verification["evidence_value"]


def test_python_evidence_value_overrides_older_release_title() -> None:
    result = verify_temporal_claims(
        "What is the latest Python version?",
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python 3.16 is the latest Python version.",
                    "claim_type": "software_version",
                    "entities": ["Python"],
                    "temporal_anchor": "latest",
                    "evidence_need": "fresh",
                }
            ]
        },
        {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "title": "Python Release Python 3.14.0",
                            "url": "https://www.python.org/downloads/release/python-3140",
                            "publisher": "python.org",
                            "snippet": (
                                "Python 3.14.0 has been superseded by Python 3.14.5. "
                                "Release date: Oct. 7, 2025 is the newest major release."
                            ),
                            "evidence_summary": (
                                "Python 3.14.0 has been superseded by Python 3.14.5."
                            ),
                            "evidence_value": "Python 3.14.5",
                            "source_type": "official",
                            "relevance_score": 1.0,
                        }
                    ],
                }
            ]
        },
        {
            "freshness_results": [
                {
                    "claim_id": "C1",
                    "claim_freshness_score": 0.98,
                    "claim_reliability_score": 0.98,
                    "claim_temporal_risk": "low",
                    "best_evidence_id": "E1",
                }
            ]
        },
        "RECENT_ONLY",
    )
    verification = result["verification_results"][0]

    assert verification["verification_status"] == "CONTRADICTED"
    assert verification["claim_value"] == "Python 3.16"
    assert verification["evidence_value"] == "Python 3.14.5"


def test_version_claim_without_evidence_version_is_insufficient_not_entity_supported() -> None:
    result = verify_temporal_claims(
        "What is the latest Python version?",
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python 3.10 is the latest Python version.",
                    "claim_type": "software_version",
                    "entities": ["Python"],
                    "temporal_anchor": "latest",
                    "evidence_need": "fresh",
                }
            ]
        },
        {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "title": "Python versions",
                            "publisher": "Python documentation",
                            "evidence_summary": "This page describes Python version support policy.",
                            "source_type": "documentation",
                            "relevance_score": 0.80,
                        }
                    ],
                }
            ]
        },
        {
            "freshness_results": [
                {
                    "claim_id": "C1",
                    "claim_freshness_score": 0.90,
                    "claim_reliability_score": 0.90,
                    "claim_temporal_risk": "low",
                    "best_evidence_id": "E1",
                }
            ]
        },
        "RECENT_ONLY",
    )
    verification = result["verification_results"][0]

    assert verification["verification_status"] == "INSUFFICIENT_EVIDENCE"
    assert verification["claim_value"] == "Python 3.10"
    assert verification["evidence_value"] is None


def test_python_verifier_selects_best_version_bearing_evidence_item() -> None:
    result = verify_temporal_claims(
        "What is the latest Python version?",
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python 3.10 is the latest Python version.",
                    "claim_type": "software_version",
                    "entities": ["Python"],
                    "temporal_anchor": "latest",
                    "evidence_need": "fresh",
                }
            ]
        },
        {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "title": "Python versions",
                            "url": "https://devguide.python.org/versions",
                            "publisher": "Python documentation",
                            "evidence_summary": "This page describes Python version support policy.",
                            "source_type": "documentation",
                            "relevance_score": 1.0,
                        },
                        {
                            "evidence_id": "E2",
                            "title": "Python Source Releases",
                            "url": "https://www.python.org/downloads/source",
                            "publisher": "Python Software Foundation",
                            "evidence_summary": "The latest stable source release is Python 3.14.5.",
                            "evidence_value": "Python 3.14.5",
                            "source_type": "official",
                            "relevance_score": 0.94,
                        },
                    ],
                }
            ]
        },
        {
            "freshness_results": [
                {
                    "claim_id": "C1",
                    "claim_freshness_score": 0.98,
                    "claim_reliability_score": 0.98,
                    "claim_temporal_risk": "low",
                    "best_evidence_id": "E1",
                }
            ]
        },
        "RECENT_ONLY",
    )
    verification = result["verification_results"][0]

    assert verification["verification_status"] == "OUTDATED"
    assert verification["best_evidence_id"] == "E2"
    assert verification["claim_value"] == "Python 3.10"
    assert verification["evidence_value"] == "Python 3.14.5"


def test_python_verifier_ignores_unrelated_download_tool_versions() -> None:
    result = verify_temporal_claims(
        "What is the latest Python version?",
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python 3.16 is the latest Python version.",
                    "claim_type": "software_version",
                    "entities": ["Python"],
                    "temporal_anchor": "latest",
                    "evidence_need": "fresh",
                }
            ]
        },
        {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "title": "Download Python for Windows",
                            "url": "https://www.python.org/downloads/windows",
                            "publisher": "python.org",
                            "evidence_summary": "The Python install manager 26.2 is available for Windows users.",
                            "evidence_value": "manager 26.2",
                            "source_type": "official",
                            "relevance_score": 1.0,
                        },
                        {
                            "evidence_id": "E2",
                            "title": "Python Source Releases",
                            "url": "https://www.python.org/downloads/source",
                            "publisher": "python.org",
                            "evidence_summary": "Stable Releases - Python 3.14.5 - May 10, 2026.",
                            "evidence_value": "Python 3.14.5",
                            "source_type": "official",
                            "relevance_score": 1.0,
                        },
                    ],
                }
            ]
        },
        {
            "freshness_results": [
                {
                    "claim_id": "C1",
                    "claim_freshness_score": 0.98,
                    "claim_reliability_score": 0.98,
                    "claim_temporal_risk": "low",
                    "best_evidence_id": "E1",
                }
            ]
        },
        "RECENT_ONLY",
    )
    verification = result["verification_results"][0]

    assert verification["verification_status"] == "CONTRADICTED"
    assert verification["best_evidence_id"] == "E2"
    assert verification["evidence_value"] == "Python 3.14.5"


def test_latest_python_313_claim_is_outdated_against_3145_evidence() -> None:
    result = verify_temporal_claims(
        "What is the latest Python version?",
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python 3.13 is the latest Python version.",
                    "claim_type": "software_version",
                    "entities": ["Python", "Python 3.13"],
                    "temporal_anchor": "latest",
                    "evidence_need": "fresh",
                }
            ]
        },
        {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "title": "Python Source Releases",
                            "url": "https://www.python.org/downloads/source",
                            "publisher": "python.org",
                            "evidence_summary": (
                                "Stable Releases - Python 3.13.13 - April 7, 2026 - "
                                "Python 3.14.5 - May 10, 2026."
                            ),
                            "evidence_value": "Python 3.14.5",
                            "source_type": "official",
                            "relevance_score": 1.0,
                        },
                    ],
                }
            ]
        },
        {
            "freshness_results": [
                {
                    "claim_id": "C1",
                    "claim_freshness_score": 0.98,
                    "claim_reliability_score": 0.98,
                    "claim_temporal_risk": "low",
                    "best_evidence_id": "E1",
                }
            ]
        },
        "RECENT_ONLY",
    )
    verification = result["verification_results"][0]

    assert verification["verification_status"] == "OUTDATED"
    assert verification["claim_value"] == "Python 3.13"
    assert verification["evidence_value"] == "Python 3.14.5"


def test_latest_python_compact_3145_claim_is_supported() -> None:
    result = verify_temporal_claims(
        "What is the latest Python version?",
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python3.14.5 is the latest Python version.",
                    "claim_type": "software_version",
                    "entities": ["Python", "Python 3.14.5"],
                    "temporal_anchor": "latest",
                    "evidence_need": "fresh",
                }
            ]
        },
        {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "title": "Download Python",
                            "url": "https://www.python.org/downloads/",
                            "publisher": "python.org",
                            "evidence_summary": "Download Python 3.14.5.",
                            "evidence_value": "Python 3.14.5",
                            "source_type": "official",
                            "relevance_score": 1.0,
                        },
                    ],
                }
            ]
        },
        {
            "freshness_results": [
                {
                    "claim_id": "C1",
                    "claim_freshness_score": 0.98,
                    "claim_reliability_score": 0.98,
                    "claim_temporal_risk": "low",
                    "best_evidence_id": "E1",
                }
            ]
        },
        "RECENT_ONLY",
    )
    verification = result["verification_results"][0]

    assert verification["verification_status"] == "SUPPORTED"
    assert verification["claim_value"] == "Python 3.14.5"
    assert verification["evidence_value"] == "Python 3.14.5"


def test_world_cup_winner_uses_actual_winner_entity() -> None:
    result = verify_temporal_claims(
        "Who won the 2014 FIFA World Cup?",
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "France won the 2014 FIFA World Cup.",
                    "claim_type": "event_result",
                    "entities": ["France", "2014 FIFA World Cup"],
                    "temporal_anchor": "2014",
                    "evidence_need": "historical",
                }
            ]
        },
        {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "title": "2014 FIFA World Cup",
                            "evidence_summary": "Germany won the 2014 FIFA World Cup.",
                            "evidence_value": "Germany",
                            "source_type": "official",
                            "relevance_score": 0.95,
                        }
                    ],
                }
            ]
        },
        {"freshness_results": [{"claim_id": "C1", "claim_reliability_score": 0.95, "best_evidence_id": "E1"}]},
        "HISTORICAL",
    )
    verification = result["verification_results"][0]

    assert verification["verification_status"] == "CONTRADICTED"
    assert verification["claim_value"] == "France"
    assert verification["evidence_value"] == "Germany"


def test_who_pheic_date_uses_actual_date_not_title_fragment() -> None:
    result = verify_temporal_claims(
        "When did WHO end the COVID-19 public health emergency of international concern?",
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "WHO ended the COVID-19 public health emergency in 2022.",
                    "claim_type": "historical_fact",
                    "entities": ["WHO", "COVID-19 public health emergency"],
                    "temporal_anchor": "2022",
                    "evidence_need": "historical",
                }
            ]
        },
        {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "title": "Results Report",
                            "evidence_summary": "WHO ended the PHEIC on May 5, 2023.",
                            "evidence_value": "May 5, 2023",
                            "source_type": "official",
                            "relevance_score": 0.95,
                        }
                    ],
                }
            ]
        },
        {"freshness_results": [{"claim_id": "C1", "claim_reliability_score": 0.95, "best_evidence_id": "E1"}]},
        "HISTORICAL",
    )
    verification = result["verification_results"][0]

    assert verification["verification_status"] == "CONTRADICTED"
    assert verification["claim_value"] == "2022"
    assert verification["evidence_value"] == "May 5, 2023"


def test_node_lifecycle_uses_support_status_not_unrelated_numbers() -> None:
    result = verify_temporal_claims(
        "Is Node.js 18 still actively supported?",
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Yes, Node.js 18 is still active LTS.",
                    "claim_type": "software_version",
                    "entities": ["Node.js 18"],
                    "temporal_anchor": "current",
                    "evidence_need": "fresh",
                }
            ]
        },
        {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "title": "Node.js previous releases",
                            "evidence_summary": "Node.js 18 reached end-of-life on April 30, 2025.",
                            "evidence_value": "end-of-life on April 30, 2025",
                            "source_type": "official",
                            "relevance_score": 0.95,
                        }
                    ],
                }
            ]
        },
        {"freshness_results": [{"claim_id": "C1", "claim_reliability_score": 0.95, "best_evidence_id": "E1"}]},
        "RECENT_ONLY",
    )
    verification = result["verification_results"][0]

    assert verification["verification_status"] in {"OUTDATED", "CONTRADICTED"}
    assert verification["evidence_value"] == "end-of-life on April 30, 2025"


def test_pandas_append_removed_status_is_contradicted() -> None:
    result = verify_temporal_claims(
        "Does pandas 2.0 still support DataFrame.append?",
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Yes, pandas 2.0 still supports DataFrame.append.",
                    "claim_type": "api_or_library_behavior",
                    "entities": ["pandas 2.0", "DataFrame.append"],
                    "temporal_anchor": "pandas 2.0",
                    "evidence_need": "version_specific",
                }
            ]
        },
        {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "title": "pandas 2.0 release notes",
                            "evidence_summary": "DataFrame.append was removed in pandas 2.0. Use pandas.concat instead.",
                            "evidence_value": "DataFrame.append was removed in pandas 2.0; use pandas.concat",
                            "source_type": "official",
                            "relevance_score": 0.95,
                        }
                    ],
                }
            ]
        },
        {"freshness_results": [{"claim_id": "C1", "claim_reliability_score": 0.95, "best_evidence_id": "E1"}]},
        "VERSION_DEPENDENT",
    )
    verification = result["verification_results"][0]

    assert verification["verification_status"] in {"OUTDATED", "CONTRADICTED"}
    assert verification["evidence_value"] == "DataFrame.append was removed in pandas 2.0; use pandas.concat"


def test_unseen_winner_question_extracts_champion_not_event_name() -> None:
    result = verify_temporal_claims(
        "Who won Super Bowl LVII?",
        {"claims": [{"claim_id": "C1", "claim_text": "Philadelphia Eagles won Super Bowl LVII.", "claim_type": "event_result"}]},
        {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "evidence_summary": "Kansas City Chiefs defeated Philadelphia Eagles to win Super Bowl LVII.",
                            "evidence_value": "Kansas City Chiefs",
                            "source_type": "official",
                            "relevance_score": 0.95,
                        }
                    ],
                }
            ]
        },
        {"freshness_results": [{"claim_id": "C1", "claim_reliability_score": 0.95, "best_evidence_id": "E1"}]},
        "HISTORICAL",
    )

    verification = result["verification_results"][0]
    assert verification["verification_status"] == "CONTRADICTED"
    assert verification["claim_value"] == "Philadelphia Eagles"
    assert verification["evidence_value"] == "Kansas City Chiefs"


def test_unseen_when_question_extracts_full_date() -> None:
    result = verify_temporal_claims(
        "When was the first iPhone announced?",
        {"claims": [{"claim_id": "C1", "claim_text": "The first iPhone was announced in 2008.", "claim_type": "historical_fact"}]},
        {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "evidence_summary": "Apple announced the first iPhone on January 9, 2007.",
                            "evidence_value": "January 9, 2007",
                            "source_type": "official",
                            "relevance_score": 0.95,
                        }
                    ],
                }
            ]
        },
        {"freshness_results": [{"claim_id": "C1", "claim_reliability_score": 0.95, "best_evidence_id": "E1"}]},
        "HISTORICAL",
    )

    verification = result["verification_results"][0]
    assert verification["verification_status"] == "CONTRADICTED"
    assert verification["evidence_value"] == "January 9, 2007"


def test_unseen_software_lifecycle_extracts_standard_support_end() -> None:
    result = verify_temporal_claims(
        "Is Ubuntu 18.04 still in standard support?",
        {"claims": [{"claim_id": "C1", "claim_text": "Ubuntu 18.04 is still in standard support.", "claim_type": "software_version"}]},
        {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "evidence_summary": "Ubuntu 18.04 standard support ended on May 31, 2023.",
                            "evidence_value": "end-of-life on May 31, 2023",
                            "source_type": "official",
                            "relevance_score": 0.95,
                        }
                    ],
                }
            ]
        },
        {"freshness_results": [{"claim_id": "C1", "claim_reliability_score": 0.95, "best_evidence_id": "E1"}]},
        "RECENT_ONLY",
    )

    verification = result["verification_results"][0]
    assert verification["verification_status"] in {"OUTDATED", "CONTRADICTED"}
    assert verification["evidence_value"] == "end-of-life on May 31, 2023"


def test_unseen_latest_software_version_uses_newer_stable_value() -> None:
    result = verify_temporal_claims(
        "What is the latest React version?",
        {"claims": [{"claim_id": "C1", "claim_text": "React 18.2.0 is the latest React version.", "claim_type": "software_version"}]},
        {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "evidence_summary": "React 19.1.0 is the latest stable release.",
                            "evidence_value": "React 19.1.0",
                            "source_type": "official",
                            "relevance_score": 0.95,
                        }
                    ],
                }
            ]
        },
        {"freshness_results": [{"claim_id": "C1", "claim_reliability_score": 0.95, "best_evidence_id": "E1"}]},
        "VERSION_DEPENDENT",
    )

    verification = result["verification_results"][0]
    assert verification["verification_status"] == "OUTDATED"
    assert verification["evidence_value"] == "React 19.1.0"


def test_unseen_static_educational_fact_remains_supported() -> None:
    result = verify_temporal_claims(
        "Is RAM volatile memory?",
        {"claims": [{"claim_id": "C1", "claim_text": "RAM is volatile memory.", "claim_type": "definition", "entities": ["RAM"]}]},
        {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "evidence_summary": "RAM is volatile memory because it loses stored data when power is removed.",
                            "source_type": "academic",
                            "relevance_score": 0.95,
                        }
                    ],
                }
            ]
        },
        {"freshness_results": [{"claim_id": "C1", "claim_reliability_score": 0.95, "best_evidence_id": "E1"}]},
        "STATIC",
    )

    verification = result["verification_results"][0]
    assert verification["verification_status"] == "SUPPORTED"
    assert verification["requires_correction"] is False


def test_weak_freshness_blocks_supported_for_recent_claim() -> None:
    result = verify_temporal_claims(
        "Is the system current?",
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "The Xyzabc system is currently active.",
                    "claim_type": "current_status",
                    "entities": ["Xyzabc system"],
                    "temporal_anchor": "current",
                    "evidence_need": "fresh",
                }
            ]
        },
        {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "title": "Xyzabc status",
                            "evidence_summary": "The Xyzabc system is currently active.",
                            "relevance_score": 0.95,
                        }
                    ],
                }
            ]
        },
        {
            "freshness_results": [
                {
                    "claim_id": "C1",
                    "claim_freshness_score": 0.20,
                    "claim_reliability_score": 0.40,
                    "claim_temporal_risk": "high",
                    "best_evidence_id": "E1",
                }
            ]
        },
        "RECENT_ONLY",
    )

    assert result["verification_results"][0]["verification_status"] == "INSUFFICIENT_EVIDENCE"


def test_subjective_claim_is_not_verifiable() -> None:
    result = verify_temporal_claims(
        "What is best?",
        {"claims": [{"claim_id": "C1", "claim_text": "Python is the best programming language."}]},
        {"evidence_results": []},
        None,
        "STATIC",
    )

    assert result["verification_results"][0]["verification_status"] == "NOT_VERIFIABLE"
    assert result["overall_verification_status"] == "NOT_VERIFIABLE"


def test_no_claims_returns_empty_warning_schema() -> None:
    result = verify_temporal_claims("Question", {"claims": []}, {}, None, None)

    assert result == {
        "verification_results": [],
        "overall_verification_status": "NOT_VERIFIABLE",
        "overall_confidence": 0.0,
        "verification_warnings": ["No claims supplied for verification."],
    }


def test_backward_compatible_wrapper_returns_verified_boolean() -> None:
    result = verify_temporal_claim(
        "Binary search divides a sorted search space in half.",
        [
            {
                "evidence_id": "E1",
                "title": "Binary Search",
                "evidence_summary": "Binary search repeatedly divides a sorted search interval in half.",
                "relevance_score": 0.90,
            }
        ],
    )

    assert result["verified"] is True
