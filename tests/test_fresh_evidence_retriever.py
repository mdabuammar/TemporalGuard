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


class QueryAwareMockSearchProvider:
    def __init__(self, results_by_query: dict[str, list[dict]]) -> None:
        self.results_by_query = results_by_query
        self.queries: list[tuple[str, int]] = []

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        self.queries.append((query, max_results))
        results = self.results_by_query.get(query, [])
        return [SearchResult(**result) for result in results[:max_results]]


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
    assert "site:python.org/downloads" in claim_result["query_used"]
    assert evidence["evidence_id"] == "E1"
    assert evidence["title"] == "Download Python"
    assert evidence["url"] == "https://www.python.org/downloads/"
    assert evidence["source_type"] == "official"
    assert evidence["publisher"] == "Python Software Foundation"
    assert evidence["published_date"] is None
    assert evidence["updated_date"] == "2026-06-01"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", evidence["retrieved_at"])
    assert evidence["evidence_summary"] == "Download the latest version of Python."
    assert evidence["snippet"] == "Download the latest version of Python."
    assert evidence["evidence_value"] is None
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
    assert all(max_results == 8 for _, max_results in provider.queries)


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


def test_evidence_snippet_version_value_is_extracted() -> None:
    provider = MockSearchProvider(
        [
            {
                "title": "Python Downloads",
                "url": "https://www.python.org/downloads/",
                "snippet": "Latest release is Python 3.14.5 and source archives are available.",
                "publisher": "Python Software Foundation",
                "source_type": "official",
                "updated_date": "2026-06-01",
            }
        ]
    )

    result = retrieve_fresh_evidence(
        "What is the latest Python version?",
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python3.14 is the latest Python version.",
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
    )

    evidence = result["evidence_results"][0]["evidence_items"][0]
    assert evidence["evidence_value"] == "Python 3.14.5"
    assert "Python 3.14.5" in evidence["evidence_summary"]


def test_python_downloads_stable_release_ranks_before_future_development_version() -> None:
    provider = MockSearchProvider(
        [
            {
                "title": "Python 3.16 development schedule",
                "url": "https://docs.python.org/3.16/whatsnew/3.16.html",
                "snippet": "Python 3.16 is a future development preview and release schedule.",
                "publisher": "Python Docs",
                "source_type": "documentation",
            },
            {
                "title": "Download Python 3.14.5",
                "url": "https://www.python.org/downloads/",
                "snippet": "Python 3.14.5 is the latest stable release available for download.",
                "publisher": "Python Software Foundation",
                "source_type": "official",
            },
            {
                "title": "Python Release Python 3.14.5",
                "url": "https://www.python.org/downloads/release/python-3145/",
                "snippet": "Python 3.14.5 was released as a stable Python release.",
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
                    "claim_text": "Python 3.10 is the latest Python version.",
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
    assert evidence["url"] == "https://www.python.org/downloads/"
    assert evidence["evidence_value"] == "Python 3.14.5"
    assert evidence["relevance_score"] > 0.90


def test_python_downloads_tie_break_prefers_highest_stable_release_value() -> None:
    provider = MockSearchProvider(
        [
            {
                "title": "Python Release Python 3.13.0",
                "url": "https://www.python.org/downloads/release/python-3130",
                "snippet": "Python 3.13.0 was released as a stable release.",
                "publisher": "Python Software Foundation",
                "source_type": "official",
            },
            {
                "title": "Python Release Python 3.14.0",
                "url": "https://www.python.org/downloads/release/python-3140",
                "snippet": "Python 3.14.0 was released as a stable release.",
                "publisher": "Python Software Foundation",
                "source_type": "official",
            },
            {
                "title": "Python Source Releases",
                "url": "https://www.python.org/downloads/source",
                "snippet": "The latest stable source release is Python 3.14.5.",
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
                    "claim_text": "Python 3.10 is the latest Python version.",
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
    assert evidence["url"] == "https://www.python.org/downloads/source"
    assert evidence["evidence_value"] == "Python 3.14.5"


def test_python_mixed_official_versions_selects_highest_stable_release() -> None:
    provider = MockSearchProvider(
        [
            {
                "title": "Python Source Releases",
                "url": "https://www.python.org/downloads/source",
                "snippet": (
                    "Stable Releases - Python 3.13.13 - April 7, 2026 - "
                    "Python 3.12.0 - Oct. 2, 2023 - Python 3.14.5 - May 10, 2026"
                ),
                "publisher": "Python Software Foundation",
                "source_type": "official",
            }
        ]
    )

    result = retrieve_fresh_evidence(
        "What is the latest stable Python version?",
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python 3.13 is the latest Python version.",
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
    assert evidence["evidence_value"] == "Python 3.14.5"


def test_python_mixed_tavily_style_results_prefers_root_download_latest_stable() -> None:
    provider = MockSearchProvider(
        [
            {
                "title": "Python Releases for Windows | Python.org",
                "url": "https://www.python.org/downloads/windows",
                "snippet": (
                    "Stable Releases Python install manager 26.2 - May 11, 2026. "
                    "Python 3.13.13 - April 7, 2026."
                ),
                "publisher": "Python Software Foundation",
                "source_type": "official",
            },
            {
                "title": "Python Release Python 3.13.1 | Python.org",
                "url": "https://www.python.org/downloads/release/python-3131/",
                "snippet": "Python 3.13.1 is the latest maintenance release for the 3.13 series.",
                "publisher": "Python Software Foundation",
                "source_type": "official",
            },
            {
                "title": "Download Python | Python.org",
                "url": "https://www.python.org/downloads/",
                "snippet": "Download Python 3.14.5. Looking for Python with a different OS?",
                "publisher": "Python Software Foundation",
                "source_type": "official",
            },
        ]
    )

    result = retrieve_fresh_evidence(
        "What is the latest stable Python version?",
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python 3.13 is the latest Python version.",
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
    assert evidence["url"] == "https://www.python.org/downloads/"
    assert evidence["evidence_value"] == "Python 3.14.5"
    assert "26.2" not in str(evidence["evidence_value"])


def test_python_prerelease_is_ignored_when_stable_release_available() -> None:
    provider = MockSearchProvider(
        [
            {
                "title": "Python Downloads",
                "url": "https://www.python.org/downloads/",
                "snippet": "Python 3.15.0a1 is a prerelease. Stable Releases include Python 3.14.5.",
                "publisher": "Python Software Foundation",
                "source_type": "official",
            }
        ]
    )

    result = retrieve_fresh_evidence(
        "What is the current Python release?",
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python 3.13 is the latest Python version.",
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
    assert evidence["evidence_value"] == "Python 3.14.5"


def test_python_version_retrieval_uses_fallback_query_when_first_search_lacks_download_value() -> None:
    provider = QueryAwareMockSearchProvider(
        {
            "Python latest stable release site:python.org/downloads": [
                {
                    "title": "Python versions",
                    "url": "https://devguide.python.org/versions",
                    "snippet": "This page describes Python version support policy.",
                    "publisher": "Python Docs",
                    "source_type": "documentation",
                }
            ],
            "Python downloads latest stable release": [
                {
                    "title": "Python Source Releases",
                    "url": "https://www.python.org/downloads/source",
                    "snippet": "The latest stable source release is Python 3.14.5.",
                    "publisher": "Python Software Foundation",
                    "source_type": "official",
                }
            ],
        }
    )

    result = retrieve_fresh_evidence(
        "What is the latest Python version?",
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python 3.10 is the latest Python version.",
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
    assert [query for query, _ in provider.queries] == [
        "Python latest stable release site:python.org/downloads",
        "Python downloads latest stable release",
        "Python Source Releases latest stable Python",
        "Download Python latest source release python.org",
        "Python Source Releases Python 3.14.5",
        "Download Python 3.14.5 python.org",
    ]
    assert evidence["url"] == "https://www.python.org/downloads/source"
    assert evidence["evidence_value"] == "Python 3.14.5"


def test_python_version_retrieval_keeps_searching_when_first_download_result_is_older() -> None:
    provider = QueryAwareMockSearchProvider(
        {
            "Python latest stable release site:python.org/downloads": [
                {
                    "title": "Python Release Python 3.13.0",
                    "url": "https://www.python.org/downloads/release/python-3130/",
                    "snippet": "Python 3.13.0 is a stable Python release.",
                    "publisher": "Python Software Foundation",
                    "source_type": "official",
                }
            ],
            "Python Source Releases latest stable Python": [
                {
                    "title": "Python Release Python 3.14.5",
                    "url": "https://www.python.org/downloads/release/python-3145/",
                    "snippet": "Python 3.14.5 is the latest stable release available for download.",
                    "publisher": "Python Software Foundation",
                    "source_type": "official",
                }
            ],
        }
    )

    result = retrieve_fresh_evidence(
        "What is the latest Python version?",
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python 3.10 is the latest Python version.",
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
    assert "Python Source Releases latest stable Python" in [query for query, _ in provider.queries]
    assert evidence["url"] == "https://www.python.org/downloads/release/python-3145/"
    assert evidence["evidence_value"] == "Python 3.14.5"


def test_python_version_retrieval_ignores_unrelated_download_tool_versions() -> None:
    provider = QueryAwareMockSearchProvider(
        {
            "Python latest stable release site:python.org/downloads": [
                {
                    "title": "Download Python for Windows",
                    "url": "https://www.python.org/downloads/windows",
                    "snippet": "The Python install manager 26.2 is available for Windows users.",
                    "publisher": "Python Software Foundation",
                    "source_type": "official",
                },
                {
                    "title": "Python Source Releases",
                    "url": "https://www.python.org/downloads/source",
                    "snippet": "Stable Releases - Python 3.14.5 - May 10, 2026 - Python 3.13.13 - April 7, 2026",
                    "publisher": "Python Software Foundation",
                    "source_type": "official",
                },
            ],
        }
    )

    result = retrieve_fresh_evidence(
        "What is the latest Python version?",
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python 3.16 is the latest Python version.",
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
    assert evidence["url"] == "https://www.python.org/downloads/source"
    assert evidence["evidence_value"] == "Python 3.14.5"


def test_python_downloads_url_without_trailing_slash_ignores_install_manager_version() -> None:
    provider = MockSearchProvider(
        [
            {
                "title": "Download Python | Python.org",
                "url": "https://www.python.org/downloads",
                "snippet": "Stable Releases Python install manager 26.2 - May 11, 2026.",
                "publisher": "Python Software Foundation",
                "source_type": "official",
            },
            {
                "title": "Python Source Releases",
                "url": "https://www.python.org/downloads/source/",
                "snippet": "Latest Python 3 Release - Python 3.14.5.",
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
                    "claim_text": "Python 3.12.4 is the latest Python version.",
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
    assert evidence["url"] == "https://www.python.org/downloads/source/"
    assert evidence["evidence_value"] == "Python 3.14.5"


def test_event_winner_evidence_value_extracts_actual_winner_not_event_title() -> None:
    provider = MockSearchProvider(
        [
            {
                "title": "2014 FIFA World Cup results",
                "url": "https://www.fifa.com/tournaments/mens/worldcup/2014",
                "snippet": "Germany won the 2014 FIFA World Cup after defeating Argentina in the final.",
                "publisher": "FIFA",
                "source_type": "official",
            }
        ]
    )

    result = retrieve_fresh_evidence(
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
        "HISTORICAL",
        provider,
        max_sources_per_claim=1,
    )

    evidence = result["evidence_results"][0]["evidence_items"][0]
    assert evidence["evidence_value"] == "Germany"


def test_date_question_evidence_value_extracts_actual_date() -> None:
    provider = MockSearchProvider(
        [
            {
                "title": "Results Report",
                "url": "https://www.who.int/news/item/covid-pheic",
                "snippet": "WHO ended the COVID-19 public health emergency of international concern on May 5, 2023.",
                "publisher": "WHO",
                "source_type": "official",
            }
        ]
    )

    result = retrieve_fresh_evidence(
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
        "HISTORICAL",
        provider,
        max_sources_per_claim=1,
    )

    evidence = result["evidence_results"][0]["evidence_items"][0]
    assert evidence["evidence_value"] == "May 5, 2023"


def test_lifecycle_question_evidence_value_ignores_unrelated_numbers() -> None:
    provider = MockSearchProvider(
        [
            {
                "title": "Node.js releases",
                "url": "https://nodejs.org/en/about/previous-releases",
                "snippet": "Node.js 18 reached end-of-life on April 30, 2025. Node.js 26.3 and 30 are unrelated future release numbers.",
                "publisher": "Node.js",
                "source_type": "official",
            }
        ]
    )

    result = retrieve_fresh_evidence(
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
        "RECENT_ONLY",
        provider,
        max_sources_per_claim=1,
    )

    evidence = result["evidence_results"][0]["evidence_items"][0]
    assert evidence["evidence_value"] == "end-of-life on April 30, 2025"
    assert "26.3" not in evidence["evidence_value"]
