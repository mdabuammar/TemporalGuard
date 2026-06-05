"""Search provider abstractions for TemporalGuard."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Protocol, Sequence
from urllib.parse import urlparse


@dataclass(slots=True)
class SearchResult:
    title: str
    url: str
    snippet: str = ""
    publisher: str = ""
    published_date: Optional[str] = None
    updated_date: Optional[str] = None
    source_type: str = "other"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SearchProvider(Protocol):
    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        ...


_OFFICIAL_DOMAINS = ("python.org", "openai.com")
_ACADEMIC_DOMAINS = (
    "arxiv.org",
    "aclanthology.org",
    "ieee.org",
    "acm.org",
    "springer.com",
    "nature.com",
    "pubmed.ncbi.nlm.nih.gov",
)
_REPUTABLE_NEWS_DOMAINS = ("reuters.com", "apnews.com", "bbc.com")


def infer_source_type_from_url(url: str) -> str:
    parsed = urlparse(url)
    hostname = parsed.netloc.lower()
    if hostname.endswith(".gov"):
        return "government"
    if any(domain in hostname for domain in _OFFICIAL_DOMAINS):
        return "official"
    if any(domain in hostname for domain in _ACADEMIC_DOMAINS):
        return "academic"
    if any(domain in hostname for domain in _REPUTABLE_NEWS_DOMAINS):
        return "reputable_news"
    if hostname:
        return "other"
    return "other"


class MockSearchProvider:
    def __init__(self, results: Optional[Sequence[SearchResult | Dict[str, Any]]] = None) -> None:
        self._results = [self._coerce_result(result) for result in results or ()]

    def _coerce_result(self, result: SearchResult | Dict[str, Any]) -> SearchResult:
        if isinstance(result, SearchResult):
            return result
        data = dict(result)
        data.setdefault("source_type", infer_source_type_from_url(data.get("url", "")))
        return SearchResult(**data)

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        del query
        return list(self._results[:max_results])


class _UnavailableSearchProvider:
    def __init__(self, name: str, *, api_key: Optional[str] = None, timeout_seconds: int = 10) -> None:
        self.name = name
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        del query, max_results
        return []


class DuckDuckGoSearchProvider(_UnavailableSearchProvider):
    pass


class BraveSearchProvider(_UnavailableSearchProvider):
    pass


class TavilySearchProvider(_UnavailableSearchProvider):
    pass


class SerpApiSearchProvider(_UnavailableSearchProvider):
    pass


class BingSearchProvider(_UnavailableSearchProvider):
    pass


def create_search_provider(config: Dict[str, Any]) -> SearchProvider:
    provider_name = str(config.get("search_provider", "mock")).lower()
    api_key = config.get("api_key")
    timeout_seconds = int(config.get("timeout_seconds", 10))
    if provider_name == "duckduckgo":
        return DuckDuckGoSearchProvider("duckduckgo", api_key=api_key, timeout_seconds=timeout_seconds)
    if provider_name == "brave":
        return BraveSearchProvider("brave", api_key=api_key, timeout_seconds=timeout_seconds)
    if provider_name == "tavily":
        return TavilySearchProvider("tavily", api_key=api_key, timeout_seconds=timeout_seconds)
    if provider_name == "serpapi":
        return SerpApiSearchProvider("serpapi", api_key=api_key, timeout_seconds=timeout_seconds)
    if provider_name == "bing":
        return BingSearchProvider("bing", api_key=api_key, timeout_seconds=timeout_seconds)
    return MockSearchProvider()
