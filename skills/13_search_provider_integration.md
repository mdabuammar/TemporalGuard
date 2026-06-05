# Skill 13: Search Provider Integration

## Purpose

This skill connects TemporalGuard to real search providers while keeping Skill 03 testable and provider-independent.

Skill 03 already defines evidence retrieval logic. This skill provides practical search provider classes for real use.

Supported providers may include DuckDuckGo, Brave Search API, Tavily API, SerpAPI, Bing Search API, and custom local/mock provider.

---

## Core Task

Create provider classes that expose a common interface:

```python
search(query: str, max_results: int = 5) -> list[SearchResult]
```

The rest of TemporalGuard should not care which search backend is used.

---

## Required Provider Output

Each provider must return `SearchResult` objects or JSON-compatible dictionaries with:

```json
{
  "title": "string",
  "url": "string",
  "snippet": "string",
  "publisher": "string",
  "published_date": null,
  "updated_date": null,
  "source_type": "official | government | academic | standards | documentation | reputable_news | company | database | other"
}
```

---

## Provider Selection Rule

Use config:

```python
{
    "search_provider": "mock | duckduckgo | brave | tavily | serpapi | bing",
    "api_key": "...",
    "timeout_seconds": 10,
    "max_results": 5
}
```

Create a factory:

```python
def create_search_provider(config: dict):
    ...
```

---

## Source Type Inference

If the provider does not return source type, infer from URL:

- `.gov` → government
- `python.org`, `openai.com`, official docs domains → official/documentation
- `arxiv.org`, `aclanthology.org`, `ieee.org`, `acm.org`, `springer.com`, `nature.com`, `pubmed.ncbi.nlm.nih.gov` → academic/database
- `reuters.com`, `apnews.com`, `bbc.com` → reputable_news
- otherwise → other

---

## Safety Rules

1. Do not scrape full pages by default.
2. Do not run unlimited search.
3. Respect timeout.
4. Handle API failures safely.
5. Never fabricate results.
6. Never invent dates.
7. Unit tests must not require internet.
8. Real providers should be integration-ready but optional.

---

## Recommended Project Files

Create:

```text
src/temporalguard/search/providers.py
tests/test_search_providers.py
```

---

## Prompt for Claude or Codex Agent

You are implementing Skill 13 for TemporalGuard.

Read `skills/13_search_provider_integration.md` carefully and implement the search provider integration layer.

Create:

1. `src/temporalguard/search/providers.py`
2. `tests/test_search_providers.py`

Requirements:

- Implement common provider interface.
- Implement `SearchResult` dataclass if not already available, or import/reuse existing one.
- Implement `MockSearchProvider`.
- Implement `create_search_provider(config: dict)`.
- Add safe optional provider skeletons for DuckDuckGo, Brave, Tavily, SerpAPI, and Bing.
- Unit tests must not require internet.
- Never fabricate results.
- Infer source type from URL.
- Handle missing API key and provider errors safely.
- Keep code typed, small, and easy to extend.
- Use package name `temporalguard`.

Run tests and fix all failures. Report files created, logic summary, test result, and assumptions.
