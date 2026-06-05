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


def test_create_search_provider_defaults_to_mock() -> None:
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
        ("brave", BraveSearchProvider),
        ("tavily", TavilySearchProvider),
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


def test_api_provider_without_key_fails_safely() -> None:
    provider = create_search_provider({"search_provider": "brave"})

    assert isinstance(provider, BraveSearchProvider)
    assert provider.search("query") == []
    assert provider.last_error == "brave_api_key_missing"


def test_duckduckgo_skeleton_does_not_require_key_but_does_not_search_in_tests() -> None:
    provider = create_search_provider({"search_provider": "duckduckgo"})

    assert isinstance(provider, DuckDuckGoSearchProvider)
    assert provider.configured is True
    assert provider.search("query") == []
    assert provider.last_error == "provider_not_implemented"


def test_unknown_provider_falls_back_to_mock() -> None:
    provider = create_search_provider({"search_provider": "unknown"})

    assert isinstance(provider, MockSearchProvider)
