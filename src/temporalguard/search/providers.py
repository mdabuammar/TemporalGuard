"""Search provider abstractions for TemporalGuard."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Protocol, Sequence
from urllib.parse import urlparse


SOURCE_TYPES = {
    "official",
    "government",
    "academic",
    "standards",
    "documentation",
    "reputable_news",
    "company",
    "database",
    "other",
}


@dataclass(slots=True)
class SearchResult:
    title: str
    url: str
    snippet: str = ""
    publisher: str = "unknown"
    published_date: Optional[str] = None
    updated_date: Optional[str] = None
    source_type: str = "other"

    def __post_init__(self) -> None:
        if not self.source_type or self.source_type == "other" or self.source_type not in SOURCE_TYPES:
            self.source_type = infer_source_type_from_url(self.url)
        if not self.publisher:
            self.publisher = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SearchProvider(Protocol):
    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        ...


_GOVERNMENT_SUFFIXES = (".gov", ".gov.bd", ".gc.ca", ".gov.uk", ".europa.eu")
_OFFICIAL_DOMAINS = (
    "python.org",
    "openai.com",
    "pytorch.org",
    "tensorflow.org",
    "pandas.pydata.org",
    "numpy.org",
    "nodejs.org",
    "react.dev",
    "nextjs.org",
    "docker.com",
    "huggingface.co",
)
_DOCUMENTATION_HINTS = ("docs.", "/docs", "documentation", "developer.", "developers.")
_STANDARDS_DOMAINS = ("w3.org", "iso.org", "ietf.org", "nist.gov")
_ACADEMIC_DOMAINS = (
    "arxiv.org",
    "aclanthology.org",
    "ieee.org",
    "acm.org",
    "springer.com",
    "nature.com",
    "sciencedirect.com",
)
_DATABASE_DOMAINS = (
    "pubmed.ncbi.nlm.nih.gov",
    "who.int",
    "worldbank.org",
    "imf.org",
    "oecd.org",
)
_REPUTABLE_NEWS_DOMAINS = ("reuters.com", "apnews.com", "bbc.com", "theverge.com")


def infer_source_type_from_url(url: str) -> str:
    parsed = urlparse(str(url or ""))
    hostname = parsed.netloc.lower()
    path = parsed.path.lower()
    if not hostname:
        return "other"
    if any(domain in hostname for domain in _STANDARDS_DOMAINS):
        return "standards"
    if any(domain in hostname for domain in _DATABASE_DOMAINS):
        return "database"
    if any(hostname.endswith(suffix) for suffix in _GOVERNMENT_SUFFIXES):
        return "government"
    if any(domain in hostname for domain in _ACADEMIC_DOMAINS):
        return "academic"
    if any(domain in hostname for domain in _OFFICIAL_DOMAINS):
        if any(hint in hostname or hint in path for hint in _DOCUMENTATION_HINTS):
            return "documentation"
        return "official"
    if any(domain in hostname for domain in _REPUTABLE_NEWS_DOMAINS):
        return "reputable_news"
    return "other"


class MockSearchProvider:
    def __init__(self, results: Optional[Sequence[SearchResult | Dict[str, Any]]] = None) -> None:
        self._results = [self._coerce_result(result) for result in results or ()]
        self.queries: list[tuple[str, int]] = []

    def _coerce_result(self, result: SearchResult | Dict[str, Any]) -> SearchResult:
        if isinstance(result, SearchResult):
            return result
        data = dict(result)
        data.setdefault("title", "")
        data.setdefault("url", "")
        data.setdefault("snippet", "")
        data.setdefault("publisher", "unknown")
        data.setdefault("published_date", None)
        data.setdefault("updated_date", None)
        data["source_type"] = _validate_source_type(data.get("source_type")) or infer_source_type_from_url(data.get("url", ""))
        return SearchResult(**data)

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        self.queries.append((query, max_results))
        if not isinstance(query, str) or not query.strip():
            return []
        limit = max(0, int(max_results or 0))
        return list(self._results[:limit])


class _SafeProviderSkeleton:
    provider_name = "unknown"
    requires_api_key = True

    def __init__(self, api_key: Optional[str] = None, timeout_seconds: int = 10, max_results: int = 5) -> None:
        self.api_key = api_key
        self.timeout_seconds = max(1, int(timeout_seconds or 10))
        self.max_results = max(1, int(max_results or 5))
        self.last_error: str | None = None

    @property
    def configured(self) -> bool:
        return bool(self.api_key) or not self.requires_api_key

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        if not isinstance(query, str) or not query.strip():
            self.last_error = "empty_query"
            return []
        if not self.configured:
            self.last_error = f"{self.provider_name}_api_key_missing"
            return []
        self.last_error = "provider_not_implemented"
        return []


class DuckDuckGoSearchProvider(_SafeProviderSkeleton):
    provider_name = "duckduckgo"
    requires_api_key = False


class BraveSearchProvider(_SafeProviderSkeleton):
    provider_name = "brave"


class TavilySearchProvider(_SafeProviderSkeleton):
    provider_name = "tavily"


class SerpApiSearchProvider(_SafeProviderSkeleton):
    provider_name = "serpapi"


class BingSearchProvider(_SafeProviderSkeleton):
    provider_name = "bing"


def create_search_provider(config: Dict[str, Any] | None) -> SearchProvider:
    cfg = config or {}
    provider_name = str(cfg.get("search_provider", "mock")).strip().lower()
    api_key = cfg.get("api_key")
    timeout_seconds = int(cfg.get("timeout_seconds", 10))
    max_results = int(cfg.get("max_results", 5))
    if provider_name == "mock":
        return MockSearchProvider(cfg.get("mock_results") or cfg.get("results") or [])
    if provider_name == "duckduckgo":
        return DuckDuckGoSearchProvider(api_key=api_key, timeout_seconds=timeout_seconds, max_results=max_results)
    if provider_name == "brave":
        return BraveSearchProvider(api_key=api_key, timeout_seconds=timeout_seconds, max_results=max_results)
    if provider_name == "tavily":
        return TavilySearchProvider(api_key=api_key, timeout_seconds=timeout_seconds, max_results=max_results)
    if provider_name == "serpapi":
        return SerpApiSearchProvider(api_key=api_key, timeout_seconds=timeout_seconds, max_results=max_results)
    if provider_name == "bing":
        return BingSearchProvider(api_key=api_key, timeout_seconds=timeout_seconds, max_results=max_results)
    return MockSearchProvider()


def _validate_source_type(value: Any) -> str | None:
    text = str(value or "").strip().lower()
    return text if text in SOURCE_TYPES else None
