import json
import re

import pytest

from temporalguard.search.providers import SearchResult
from temporalguard.skills.fresh_evidence_retriever import retrieve_fresh_evidence


class MockSearchProvider:
    def __init__(self, results: list[SearchResult | dict] | None = None) -> None:
        self.results = results or []
        self.queries: list[tuple[str, int]] = []

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        self.queries.append((query, max_results))
        coerced: list[SearchResult] = []
        for result in self.results:
            if isinstance(result, SearchResult):
                coerced.append(result)
            else:
                coerced.append(SearchResult(**result))
        return coerced[:max_results]


@pytest.mark.parametrize(
    ("question", "claims_payload", "mock_results", "expected_status"),
    [
        (
            "What is the latest Python version?",
            {
                "claims": [
                    {
                        "claim_id": "C1",
                        "claim_text": "Python 3.10 is the latest stable version of Python.",
                        "claim_type": "software_version",
                        "entities": ["Python", "Python 3.10"],
                        "temporal_sensitivity": "high",
                        "temporal_anchor": "latest",
                        "evidence_need": "fresh",
                    }
                ]
            },
            [
                {
                    "title": "Download Python",
                    "url": "https://www.python.org/downloads/",
                    "snippet": "Download the latest version of Python.",
                    "publisher": "Python Software Foundation",
                    "source_type": "official",
                    "updated_date": "2026-06-01",
                }
            ],
            "success",
        ),
        (
            "Who was the president of the USA in 2016?",
            {
                "claims": [
                    {
                        "claim_id": "C1",
                        "claim_text": "Barack Obama was the president of the United States in 2016.",
                        "claim_type": "historical_fact",
                        "entities": ["Barack Obama", "United States", "president"],
                        "temporal_sensitivity": "low",
                        "temporal_anchor": "2016",
                        "evidence_need": "historical",
                    }
                ]
            },
            [
                {
                    "title": "Presidents of the United States",
                    "url": "https://www.whitehouse.gov/about-the-white-house/presidents/",
                    "snippet": "Barack Obama served as the 44th President of the United States.",
                    "publisher": "The White House",
                    "source_type": "government",
                }
            ],
            "success",
        ),
        (
            "What is binary search?",
            {
                "claims": [
                    {
                        "claim_id": "C1",
                        "claim_text": "Binary search divides a sorted search space in half.",
                        "claim_type": "definition",
                        "entities": ["binary search"],
                        "temporal_sensitivity": "low",
                        "temporal_anchor": None,
                        "evidence_need": "optional",
                    }
                ]
            },
            [],
            "skipped",
        ),
        (
            "Is the Canada student visa SDS program still active?",
            {
                "claims": [
                    {
                        "claim_id": "C1",
                        "claim_text": "The Canada student visa SDS program is no longer active.",
                        "claim_type": "law_or_policy",
                        "entities": ["Canada student visa SDS program"],
                        "temporal_sensitivity": "high",
                        "temporal_anchor": "current",
                        "evidence_need": "fresh",
                    }
                ]
            },
            [
                {
                    "title": "Student Direct Stream",
                    "url": (
                        "https://www.canada.ca/en/immigration-refugees-citizenship/"
                        "services/study-canada/study-permit/student-direct-stream.html"
                    ),
                    "snippet": "Information about the Student Direct Stream program.",
                    "publisher": "Government of Canada",
                    "source_type": "government",
                    "updated_date": "2026-01-01",
                }
            ],
            "success",
        ),
        (
            "Unknown claim",
            {
                "claims": [
                    {
                        "claim_id": "C1",
                        "claim_text": "Xyzabc system is currently active.",
                        "claim_type": "other",
                        "entities": ["Xyzabc system"],
                        "temporal_sensitivity": "high",
                        "temporal_anchor": "current",
                        "evidence_need": "fresh",
                    }
                ]
            },
            [],
            "failed",
        ),
    ],
)
def test_retrieve_fresh_evidence_minimum_cases(
    question: str,
    claims_payload: dict,
    mock_results: list[dict],
    expected_status: str,
) -> None:
    provider = MockSearchProvider(mock_results)

    result = retrieve_fresh_evidence(
        question=question,
        claims_payload=claims_payload,
        temporal_category=None,
        search_provider=provider,
    )

    assert result["evidence_results"][0]["retrieval_status"] == expected_status
    json.dumps(result)


def test_success_result_contains_required_evidence_fields() -> None:
    provider = MockSearchProvider(
        [
            SearchResult(
                title="Download Python",
                url="https://www.python.org/downloads/",
                snippet="Download the latest version of Python.",
                publisher="Python Software Foundation",
                source_type="official",
                updated_date="2026-06-01",
            )
        ]
    )
    result = retrieve_fresh_evidence(
        "What is the latest Python version?",
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python 3.10 is the latest stable version of Python.",
                    "claim_type": "software_version",
                    "entities": ["Python", "Python 3.10"],
                    "temporal_sensitivity": "high",
                    "temporal_anchor": "latest",
                    "evidence_need": "fresh",
                }
            ]
        },
        search_provider=provider,
    )

    claim_result = result["evidence_results"][0]
    evidence = claim_result["evidence_items"][0]

    assert "Python" in claim_result["query_used"]
    assert "official" in claim_result["query_used"]
    assert evidence["evidence_id"] == "E1"
    assert evidence["title"] == "Download Python"
    assert evidence["url"] == "https://www.python.org/downloads/"
    assert evidence["source_type"] == "official"
    assert evidence["publisher"] == "Python Software Foundation"
    assert evidence["published_date"] is None
    assert evidence["updated_date"] == "2026-06-01"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", evidence["retrieved_at"])
    assert evidence["evidence_summary"] == "Download the latest version of Python."
    assert evidence["relevance_score"] >= 0.70
    assert evidence["freshness_hint"] == "fresh"
    assert evidence["quote"] is None
    assert claim_result["evidence_count"] == 1
    assert result["total_claims_processed"] == 1
    assert result["total_evidence_items"] == 1


def test_no_search_provider_returns_failed_with_warning() -> None:
    result = retrieve_fresh_evidence(
        "What is the latest Python version?",
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python 3.10 is the latest stable version of Python.",
                    "claim_type": "software_version",
                    "entities": ["Python"],
                    "temporal_sensitivity": "high",
                    "temporal_anchor": "latest",
                    "evidence_need": "fresh",
                }
            ]
        },
    )

    assert result["evidence_results"][0]["retrieval_status"] == "failed"
    assert result["retrieval_warnings"] == ["No search provider supplied; evidence retrieval failed."]


def test_empty_claims_are_safe() -> None:
    result = retrieve_fresh_evidence("Question", {"claims": []}, search_provider=MockSearchProvider())

    assert result == {
        "evidence_results": [],
        "total_claims_processed": 0,
        "total_evidence_items": 0,
        "retrieval_warnings": ["No claims supplied for evidence retrieval."],
    }


def test_limits_processed_claims_and_sources() -> None:
    provider = MockSearchProvider(
        [
            {
                "title": f"Official source {index}",
                "url": f"https://example.gov/{index}",
                "snippet": "Python official latest version.",
                "publisher": "Example",
                "source_type": "government",
            }
            for index in range(8)
        ]
    )
    claims = [
        {
            "claim_id": f"C{index}",
            "claim_text": f"Python {index}.0 is the latest stable version of Python.",
            "claim_type": "software_version",
            "entities": ["Python"],
            "temporal_sensitivity": "high",
            "temporal_anchor": "latest",
            "evidence_need": "fresh",
        }
        for index in range(3)
    ]

    result = retrieve_fresh_evidence(
        "What is the latest Python version?",
        {"claims": claims},
        "RECENT_ONLY",
        provider,
        max_sources_per_claim=2,
        max_claims=2,
    )

    assert result["total_claims_processed"] == 2
    assert all(item["evidence_count"] == 2 for item in result["evidence_results"])
    assert all(max_results == 4 for _, max_results in provider.queries)


def test_authoritative_sources_rank_before_weak_sources() -> None:
    provider = MockSearchProvider(
        [
            {
                "title": "Random blog about Python",
                "url": "https://randomblog.example/python",
                "snippet": "Python latest version notes.",
                "publisher": "Random Blog",
                "source_type": "other",
            },
            {
                "title": "Download Python",
                "url": "https://www.python.org/downloads/",
                "snippet": "Download the latest version of Python.",
                "publisher": "Python Software Foundation",
                "source_type": "official",
            },
        ]
    )

    result = retrieve_fresh_evidence(
        "What is the latest Python version?",
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python 3.10 is the latest stable version of Python.",
                    "claim_type": "software_version",
                    "entities": ["Python"],
                    "temporal_sensitivity": "high",
                    "temporal_anchor": "latest",
                    "evidence_need": "fresh",
                }
            ]
        },
        "RECENT_ONLY",
        provider,
        max_sources_per_claim=1,
    )

    evidence = result["evidence_results"][0]["evidence_items"][0]
    assert evidence["source_type"] == "official"
