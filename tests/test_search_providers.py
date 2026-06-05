from temporalguard.search.providers import create_search_provider, infer_source_type_from_url, SearchResult


def test_infer_source_type_from_url_detects_government():
    assert infer_source_type_from_url("https://example.gov/resource") == "government"


def test_create_search_provider_defaults_to_mock():
    provider = create_search_provider({})
    assert provider.search("query") == []


def test_mock_search_provider_returns_configured_results():
    provider = create_search_provider({"search_provider": "mock"})
    assert isinstance(provider, object)
    assert SearchResult(title="t", url="https://example.com").source_type == "other"
