import json

import pytest

from temporalguard.search.providers import (
    BingSearchProvider,
    BraveSearchProvider,
    DuckDuckGoSearchProvider,
    MockSearchProvider,
    SearchResult,
    SerpApiSearchProvider,
    TavilySearchProvider,
    create_search_provider,
    infer_source_type_from_url,
)
from temporalguard.skills.fresh_evidence_retriever import retrieve_fresh_evidence
from temporalguard.skills.temporal_verifier import verify_temporal_claims


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://example.gov/resource", "government"),
        ("https://www.canada.ca/en/immigration.html", "other"),
        ("https://www.python.org/downloads/", "official"),
        ("https://platform.openai.com/docs/api-reference", "documentation"),
        ("https://docs.python.org/3/", "documentation"),
        ("https://arxiv.org/abs/1234.5678", "academic"),
        ("https://pubmed.ncbi.nlm.nih.gov/123/", "database"),
        ("https://www.w3.org/TR/", "standards"),
        ("https://www.reuters.com/world/", "reputable_news"),
        ("https://random.example/blog", "other"),
        ("", "other"),
    ],
)
def test_infer_source_type_from_url(url: str, expected: str) -> None:
    assert infer_source_type_from_url(url) == expected


def test_search_result_to_dict_and_defaults() -> None:
    result = SearchResult(title="Download Python", url="https://www.python.org/downloads/")

    assert result.publisher == "unknown"
    assert result.source_type == "official"
    assert result.to_dict() == {
        "title": "Download Python",
        "url": "https://www.python.org/downloads/",
        "snippet": "",
        "publisher": "unknown",
        "published_date": None,
        "updated_date": None,
        "source_type": "official",
    }
    json.dumps(result.to_dict())


def test_mock_search_provider_returns_configured_results_and_tracks_queries() -> None:
    provider = MockSearchProvider(
        [
            {
                "title": "OpenAI Docs",
                "url": "https://platform.openai.com/docs",
                "snippet": "Documentation",
                "publisher": "OpenAI",
            },
            SearchResult(title="Reuters", url="https://www.reuters.com/article", source_type="reputable_news"),
        ]
    )

    results = provider.search("OpenAI API docs", max_results=1)

    assert provider.queries == [("OpenAI API docs", 1)]
    assert len(results) == 1
    assert results[0].source_type == "documentation"
    assert provider.search("", max_results=5) == []


def test_create_search_provider_defaults_to_mock(monkeypatch) -> None:
    monkeypatch.delenv("DEFAULT_SEARCH_PROVIDER", raising=False)
    provider = create_search_provider({})

    assert isinstance(provider, MockSearchProvider)
    assert provider.search("query") == []


def test_create_search_provider_mock_uses_configured_results() -> None:
    provider = create_search_provider(
        {
            "search_provider": "mock",
            "mock_results": [{"title": "Python", "url": "https://www.python.org/"}],
        }
    )

    results = provider.search("python", max_results=5)
    assert len(results) == 1
    assert results[0].title == "Python"
    assert results[0].source_type == "official"


@pytest.mark.parametrize(
    ("provider_name", "provider_class"),
    [
        ("duckduckgo", DuckDuckGoSearchProvider),
        ("serpapi", SerpApiSearchProvider),
        ("bing", BingSearchProvider),
    ],
)
def test_create_search_provider_returns_safe_skeletons(provider_name: str, provider_class: type) -> None:
    provider = create_search_provider(
        {
            "search_provider": provider_name,
            "api_key": "test-key",
            "timeout_seconds": 3,
            "max_results": 2,
        }
    )

    assert isinstance(provider, provider_class)
    assert provider.timeout_seconds == 3
    assert provider.max_results == 2
    assert provider.search("query", max_results=2) == []
    assert provider.last_error == "provider_not_implemented"


def test_api_provider_without_key_fails_safely(monkeypatch) -> None:
    monkeypatch.delenv("BRAVE_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    provider = create_search_provider({"search_provider": "brave"})

    assert isinstance(provider, BraveSearchProvider)
    assert provider.search("query") == []
    assert provider.last_error == "brave_api_key_missing"
    tavily = create_search_provider({"search_provider": "tavily"})
    assert isinstance(tavily, TavilySearchProvider)
    assert tavily.search("query") == []
    assert tavily.last_error == "tavily_api_key_missing"


def test_tavily_provider_parses_mocked_response(monkeypatch) -> None:
    calls = []

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "results": [
                    {
                        "title": "Python Downloads",
                        "url": "https://www.python.org/downloads/",
                        "content": "Python 3.13.5 is the newest release.",
                        "published_date": "2026-06-01",
                    }
                ]
            }

    def fake_post(*args, **kwargs):
        calls.append({"args": args, "kwargs": kwargs})
        return FakeResponse()

    monkeypatch.setattr("temporalguard.search.providers.requests.post", fake_post)

    provider = TavilySearchProvider(api_key="test-key", timeout_seconds=3, max_results=2)
    results = provider.search("latest Python version", max_results=1)

    assert len(results) == 1
    assert results[0].title == "Python Downloads"
    assert results[0].source_type == "official"
    assert results[0].snippet == "Python 3.13.5 is the newest release."
    assert calls[0]["args"][0] == "https://api.tavily.com/search"
    assert calls[0]["kwargs"]["json"]["api_key"] == "test-key"
    assert calls[0]["kwargs"]["json"]["max_results"] == 1


def test_live_style_tavily_result_verifies_latest_python_version(monkeypatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "results": [
                    {
                        "title": "Download Python",
                        "url": "https://www.python.org/downloads/",
                        "content": "Latest Python 3.14.5 release is available for download.",
                        "published_date": "2026-06-01",
                    }
                ]
            }

    monkeypatch.setattr("temporalguard.search.providers.requests.post", lambda *args, **kwargs: FakeResponse())
    provider = TavilySearchProvider(api_key="test-key")
    claims_payload = {
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
    }

    evidence_payload = retrieve_fresh_evidence(
        "What is the latest Python version?",
        claims_payload,
        "RECENT_ONLY",
        provider,
    )
    verification = verify_temporal_claims(
        "What is the latest Python version?",
        claims_payload,
        evidence_payload,
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

    evidence = evidence_payload["evidence_results"][0]["evidence_items"][0]
    result = verification["verification_results"][0]
    assert evidence["evidence_value"] == "Python 3.14.5"
    assert result["verification_status"] == "SUPPORTED"
    assert result["claim_value"] == "Python 3.14"
    assert result["evidence_value"] == "Python 3.14.5"


def test_brave_provider_parses_mocked_response(monkeypatch) -> None:
    calls = []

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "web": {
                    "results": [
                        {
                            "title": "Python Downloads",
                            "url": "https://www.python.org/downloads/",
                            "description": "Download the latest Python release.",
                            "profile": {"name": "Python"},
                            "page_age": "2026-06-01T00:00:00Z",
                        }
                    ]
                }
            }

    def fake_get(*args, **kwargs):
        calls.append({"args": args, "kwargs": kwargs})
        return FakeResponse()

    monkeypatch.setattr("temporalguard.search.providers.requests.get", fake_get)

    provider = BraveSearchProvider(api_key="test-key", timeout_seconds=3, max_results=2)
    results = provider.search("latest Python version", max_results=1)

    assert len(results) == 1
    assert results[0].publisher == "Python"
    assert results[0].updated_date == "2026-06-01"
    assert calls[0]["args"][0] == "https://api.search.brave.com/res/v1/web/search"
    assert calls[0]["kwargs"]["headers"]["X-Subscription-Token"] == "test-key"


def test_duckduckgo_skeleton_does_not_require_key_but_does_not_search_in_tests() -> None:
    provider = create_search_provider({"search_provider": "duckduckgo"})

    assert isinstance(provider, DuckDuckGoSearchProvider)
    assert provider.configured is True
    assert provider.search("query") == []
    assert provider.last_error == "provider_not_implemented"


def test_unknown_provider_falls_back_to_mock() -> None:
    provider = create_search_provider({"search_provider": "unknown"})

    assert isinstance(provider, MockSearchProvider)
