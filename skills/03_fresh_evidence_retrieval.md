# Skill 03: Fresh Evidence Retrieval

## Purpose

This skill retrieves reliable, fresh, and relevant evidence for claims that may be outdated, time-sensitive, version-dependent, or historically anchored.

TemporalGuard must not trust an LLM answer only because it sounds correct. If a claim depends on time, the system must collect evidence from trustworthy sources before verification.

This skill is the third step in the TemporalGuard pipeline.

It receives:

1. The original user question
2. The extracted claims from Skill 02
3. The temporal category from Skill 01
4. Optional temporal anchors such as `current`, `latest`, `2020`, `Python 3.10`, or `as of today`

It returns a structured list of evidence items for each claim.

---

## Core Task

Given a claim or list of claims, retrieve the most relevant evidence from trusted sources.

This skill must:

1. Build a search query for each important claim.
2. Prefer authoritative sources.
3. Retrieve only a small number of useful evidence items.
4. Record source title, URL, source type, publication/update date if available, and short evidence summary.
5. Avoid wasting tokens and context window.
6. Avoid collecting too many sources.
7. Never decide final truth by itself.

This skill retrieves evidence only.

Truth checking happens later in Skill 05: Temporal Verification.

---

## Important Boundary

This skill does not:

* verify whether a claim is true
* correct the LLM answer
* generate the final response
* write the final user-facing answer
* compare evidence deeply
* perform long browsing loops
* scrape unnecessary pages
* retrieve low-quality sources when better sources exist

---

## Inputs

The skill may receive input like this:

```json
{
  "question": "What is the latest Python version?",
  "temporal_category": "RECENT_ONLY",
  "claims": [
    {
      "claim_id": "C1",
      "claim_text": "Python 3.10 is the latest stable version of Python.",
      "claim_type": "software_version",
      "entities": ["Python", "Python 3.10"],
      "temporal_sensitivity": "high",
      "temporal_anchor": "latest",
      "evidence_need": "fresh"
    }
  ]
}
```

---

## Required Output Format

Always return valid JSON only.

Do not include markdown.

Do not include explanation outside the JSON.

Use this schema:

```json
{
  "evidence_results": [
    {
      "claim_id": "C1",
      "claim_text": "string",
      "query_used": "string",
      "evidence_items": [
        {
          "evidence_id": "E1",
          "title": "string",
          "url": "string",
          "source_type": "official | government | academic | standards | documentation | reputable_news | company | database | other",
          "publisher": "string",
          "published_date": null,
          "updated_date": null,
          "retrieved_at": "ISO-8601 timestamp",
          "evidence_summary": "short summary",
          "relevance_score": 0.0,
          "freshness_hint": "fresh | acceptable | old | unknown",
          "quote": null
        }
      ],
      "evidence_count": 0,
      "retrieval_status": "success | partial | failed | skipped",
      "notes": "short note"
    }
  ],
  "total_claims_processed": 0,
  "total_evidence_items": 0,
  "retrieval_warnings": ["string"]
}
```

---

## Field Instructions

### claim_id

Use the same claim ID from Skill 02.

Example:

```text
C1
```

---

### query_used

The actual search query used for retrieval.

Good:

```text
Python latest stable version official release
```

Bad:

```text
Python
```

The query should be specific but short.

---

### evidence_id

Use simple IDs inside each claim:

```text
E1, E2, E3
```

Do not use random IDs.

---

### title

The title of the source page or document.

---

### url

The URL of the evidence source.

The implementation should keep the URL for traceability.

---

### source_type

Use one of:

```text
official
government
academic
standards
documentation
reputable_news
company
database
other
```

Examples:

* Python.org → `official`
* U.S. government website → `government`
* arXiv / ACL Anthology / IEEE / Springer → `academic`
* W3C / ISO / NIST → `standards`
* OpenAI docs / PyTorch docs / pandas docs → `documentation`
* Reuters / AP / BBC / The Verge for tech news → `reputable_news`
* Company website or press release → `company`
* World Bank / WHO / IMF / PubMed → `database`

---

### publisher

Examples:

```text
Python Software Foundation
OpenAI
Government of Canada
Reuters
ACL Anthology
World Health Organization
```

If unknown, return:

```text
unknown
```

---

### published_date

Use the publication date if available.

Format:

```text
YYYY-MM-DD
```

If only year is available:

```text
YYYY
```

If unknown, use `null`.

---

### updated_date

Use the updated or last modified date if available.

Format:

```text
YYYY-MM-DD
```

If unknown, use `null`.

---

### retrieved_at

Use current timestamp when the retrieval happens.

Format:

```text
YYYY-MM-DDTHH:MM:SSZ
```

---

### evidence_summary

A short summary of the evidence.

Keep it short.

Good:

```text
The official Python downloads page identifies Python 3.13.5 as the latest release available for download.
```

Bad:

```text
This page is about Python.
```

---

### relevance_score

Use a float from `0.0` to `1.0`.

Suggested values:

* `0.90` to `1.00`: directly supports checking the claim
* `0.70` to `0.89`: useful but not perfect
* `0.50` to `0.69`: partially useful
* below `0.50`: weak, avoid including unless no better source exists

---

### freshness_hint

Use one of:

```text
fresh
acceptable
old
unknown
```

This is only a rough hint. Final freshness scoring happens later in Skill 04.

---

### quote

Optional short quote from the source.

Use `null` by default.

Only include a quote when:

* it is very short
* it directly supports the claim
* it is not copyright-heavy
* it helps verification

Do not include long copied text.

---

### retrieval_status

Use:

```text
success
partial
failed
skipped
```

Use `success` when at least one strong evidence item is found.

Use `partial` when only weak or indirect evidence is found.

Use `failed` when no useful evidence is found.

Use `skipped` when the claim does not require retrieval.

---

## Source Priority Rules

Always prefer authoritative sources.

### Highest Priority Sources

Use these first:

1. Official documentation
2. Official company website or press release
3. Government or legal source
4. Academic publisher or paper index
5. Standards body
6. Trusted database
7. Reputable news source
8. Other sources only if necessary

---

## Domain-Specific Source Strategy

### Software Version Claims

Claim examples:

```text
Python 3.10 is the latest stable version.
The OpenAI Python SDK uses this method.
This pandas function is deprecated.
```

Prefer:

```text
official documentation
release notes
GitHub official repository
PyPI package page
official changelog
```

Search query examples:

```text
Python latest stable version official
pandas deprecated function official documentation
OpenAI Python SDK latest documentation
PyTorch CUDA compatibility official
```

---

### API or Library Behavior Claims

Prefer:

```text
official API docs
official SDK docs
official migration guide
official changelog
GitHub repository documentation
```

Avoid random blogs unless no official source exists.

---

### Company Leadership or Ownership Claims

Claim examples:

```text
Sam Altman is CEO of OpenAI.
Microsoft owns LinkedIn.
```

Prefer:

```text
official company leadership page
official company press release
SEC filing if relevant
reputable news source
```

Search query examples:

```text
OpenAI leadership CEO official
Microsoft LinkedIn acquisition official
```

---

### Law, Policy, Visa, Tax, University, or Regulation Claims

Prefer:

```text
government website
official policy page
official legal database
university official page
official immigration website
```

Avoid blogs, forums, and unofficial summaries.

Search query examples:

```text
Canada student visa SDS program official status
Bangladesh income tax rate official
Amazon FBA policy official
```

---

### Medical or Scientific Guideline Claims

Prefer:

```text
WHO
CDC
FDA
NICE
PubMed
official clinical guideline
peer-reviewed article
medical society guideline
```

Important:

This skill only retrieves evidence. It does not give medical advice.

---

### Research Paper or Academic Claims

Prefer:

```text
ACL Anthology
arXiv
IEEE
ACM
Springer
Elsevier
Nature
Science
PubMed
Google Scholar metadata if available
```

Search query examples:

```text
temporal awareness large language models benchmark paper
outdated knowledge LLMs benchmark arXiv
LLM temporal knowledge editing paper
```

---

### Price, Market, Finance, or Crypto Claims

Prefer:

```text
official exchange
financial data provider
government central bank
company investor relations
reputable financial source
```

Important:

For real-time price claims, use fresh data APIs if available.

---

### Sports or Event Result Claims

Prefer:

```text
official league website
official tournament website
reputable sports data provider
reputable news source
```

---

## Query Construction Rules

Build queries using:

1. main entity
2. claim type
3. temporal anchor
4. source preference word such as official, documentation, government, release notes

Examples:

Claim:

```text
Python 3.10 is the latest stable version of Python.
```

Query:

```text
Python latest stable version official
```

Claim:

```text
The Canada student visa SDS program is no longer active.
```

Query:

```text
Canada student visa SDS program no longer active official
```

Claim:

```text
Barack Obama was president of the United States in 2016.
```

Query:

```text
United States president 2016 official
```

Claim:

```text
The OpenAI Python SDK lets developers call OpenAI models from Python applications.
```

Query:

```text
OpenAI Python SDK official documentation
```

---

## Retrieval Limits

To avoid wasting tokens and context:

Default limits:

```text
max_sources_per_claim = 3
max_claims_to_retrieve = 5
```

Rules:

* For high-sensitivity claims, retrieve up to 3 sources.
* For medium-sensitivity claims, retrieve up to 2 sources.
* For low-sensitivity claims, retrieve 0–1 source only if needed.
* If `evidence_need` is `optional`, retrieval may be skipped unless evaluation mode requires it.
* Do not retrieve evidence for duplicate claims.
* Do not retrieve more than needed.

---

## Freshness Rules

This skill should estimate freshness roughly.

Use `fresh` when:

* the source is official and recently updated
* the claim asks for current/latest information
* the page appears to represent the current state
* the source is a live documentation or current policy page

Use `acceptable` when:

* the source is reliable but not clearly recent
* the claim is historical or stable

Use `old` when:

* the source date is clearly outdated for the claim
* a newer source is expected but not found

Use `unknown` when:

* no date is available
* the page does not show update time

Final detailed freshness scoring belongs to Skill 04.

---

## Handling Historical Evidence

For historical claims, do not only retrieve the newest page.

Try to retrieve evidence that matches the historical anchor.

Example:

Question:

```text
Who was the president of the USA in 2016?
```

Good query:

```text
United States president 2016 official
```

Bad query:

```text
current US president
```

For historical claims, set:

```json
"freshness_hint": "acceptable"
```

because the evidence does not need to be new; it needs to match the correct time period.

---

## Handling Version-Specific Evidence

For version-dependent claims, retrieve official version-specific documentation if possible.

Example:

Claim:

```text
In pandas 2.0, this method is deprecated.
```

Good query:

```text
pandas 2.0 deprecated method official documentation
```

Bad query:

```text
pandas method
```

Set evidence need to:

```text
version_specific
```

---

## Handling Failed Retrieval

If no useful evidence is found, return:

```json
{
  "claim_id": "C1",
  "claim_text": "string",
  "query_used": "string",
  "evidence_items": [],
  "evidence_count": 0,
  "retrieval_status": "failed",
  "notes": "No reliable evidence found."
}
```

Do not invent evidence.

Do not fabricate URLs.

Do not guess dates.

---

## Reliability Rules

The retrieval system must avoid weak sources when strong sources exist.

Avoid:

* random blogs
* SEO content farms
* forum answers
* unsourced social media posts
* outdated pages
* copied summaries
* AI-generated pages
* unknown websites with no date or author

Use weaker sources only when:

* no authoritative source is available
* the claim is low risk
* the result is clearly labeled as weak

---

## Implementation Notes for AI Coding Agents

Build this skill as a lightweight retrieval module.

Do not create a large autonomous browsing agent.

Do not perform unlimited search loops.

Do not retrieve long full pages unless needed.

Do not summarize entire articles.

Do not store excessive page text in memory.

Do not call the LLM for retrieval unless strictly needed.

Recommended implementation:

* Create a Python module such as `fresh_evidence_retriever.py`
* Create a function named `retrieve_fresh_evidence(...) -> dict`
* Use a search API abstraction so the project can support multiple backends later
* Start with a simple provider interface:

  * `SearchProvider`
  * `SearchResult`
* Support a mock provider for unit tests
* Support real providers later:

  * Tavily
  * SerpAPI
  * Brave Search API
  * Bing Search API
  * DuckDuckGo search
* Keep the skill testable without internet
* Use dependency injection for the search provider
* Return strict JSON-compatible dictionary
* Add unit tests using mock search results
* Add clear error handling for no internet, no API key, empty claims, invalid input

---

## Suggested Python Interface

Use this interface:

```python
def retrieve_fresh_evidence(
    question: str,
    claims_payload: dict,
    temporal_category: str | None = None,
    search_provider=None,
    max_sources_per_claim: int = 3,
    max_claims: int = 5
) -> dict:
    """
    Retrieve fresh or time-appropriate evidence for extracted claims.

    Args:
        question: Original user question.
        claims_payload: Output from Skill 02.
        temporal_category: Optional category from Skill 01.
        search_provider: Optional provider object with a search(query, max_results) method.
        max_sources_per_claim: Maximum evidence items per claim.
        max_claims: Maximum claims to process.

    Returns:
        JSON-compatible dict with evidence_results, counts, and warnings.
    """
```

---

## Recommended Data Classes

Use simple data classes if useful:

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str = ""
    publisher: str = "unknown"
    published_date: Optional[str] = None
    updated_date: Optional[str] = None
    source_type: str = "other"
```

Provider interface:

```python
class SearchProvider:
    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        raise NotImplementedError
```

---

## Expected Behavior

The retriever should be fast, cheap, and controlled.

It must not waste tokens.

It must not browse endlessly.

It must not generate final user answers.

It must not verify truth.

It only retrieves and structures evidence.

---

## Quality Requirements

The implementation must satisfy these requirements:

1. Return valid JSON-compatible dictionary every time.
2. Use search queries that are specific and short.
3. Prefer official, government, academic, documentation, and reputable sources.
4. Avoid low-quality sources when better sources exist.
5. Limit evidence per claim.
6. Limit number of processed claims.
7. Skip optional low-risk claims unless needed.
8. Support mock search provider for tests.
9. Handle failed or empty retrieval safely.
10. Never fabricate evidence.
11. Never invent source dates.
12. Keep the module reusable.
13. Keep logic easy to debug.
14. Avoid unnecessary LLM calls.
15. Protect context window by storing short summaries only.

---

## Test Cases

Use mock search results for tests. Do not require internet in unit tests.

Minimum test cases:

```python
test_cases = [
    {
        "question": "What is the latest Python version?",
        "claims_payload": {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python 3.10 is the latest stable version of Python.",
                    "claim_type": "software_version",
                    "entities": ["Python", "Python 3.10"],
                    "temporal_sensitivity": "high",
                    "temporal_anchor": "latest",
                    "evidence_need": "fresh"
                }
            ]
        },
        "mock_results": [
            {
                "title": "Download Python",
                "url": "https://www.python.org/downloads/",
                "snippet": "Download the latest version of Python.",
                "publisher": "Python Software Foundation",
                "source_type": "official",
                "updated_date": "2026-06-01"
            }
        ],
        "expected_status": "success"
    },
    {
        "question": "Who was the president of the USA in 2016?",
        "claims_payload": {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Barack Obama was the president of the United States in 2016.",
                    "claim_type": "historical_fact",
                    "entities": ["Barack Obama", "United States", "president"],
                    "temporal_sensitivity": "low",
                    "temporal_anchor": "2016",
                    "evidence_need": "historical"
                }
            ]
        },
        "mock_results": [
            {
                "title": "Presidents of the United States",
                "url": "https://www.whitehouse.gov/about-the-white-house/presidents/",
                "snippet": "Barack Obama served as the 44th President of the United States.",
                "publisher": "The White House",
                "source_type": "government"
            }
        ],
        "expected_status": "success"
    },
    {
        "question": "What is binary search?",
        "claims_payload": {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Binary search divides a sorted search space in half.",
                    "claim_type": "definition",
                    "entities": ["binary search"],
                    "temporal_sensitivity": "low",
                    "temporal_anchor": null,
                    "evidence_need": "optional"
                }
            ]
        },
        "mock_results": [],
        "expected_status": "skipped"
    },
    {
        "question": "Is the Canada student visa SDS program still active?",
        "claims_payload": {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "The Canada student visa SDS program is no longer active.",
                    "claim_type": "law_or_policy",
                    "entities": ["Canada student visa SDS program"],
                    "temporal_sensitivity": "high",
                    "temporal_anchor": "current",
                    "evidence_need": "fresh"
                }
            ]
        },
        "mock_results": [
            {
                "title": "Student Direct Stream",
                "url": "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/study-permit/student-direct-stream.html",
                "snippet": "Information about the Student Direct Stream program.",
                "publisher": "Government of Canada",
                "source_type": "government",
                "updated_date": "2026-01-01"
            }
        ],
        "expected_status": "success"
    },
    {
        "question": "Unknown claim",
        "claims_payload": {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Xyzabc system is currently active.",
                    "claim_type": "other",
                    "entities": ["Xyzabc system"],
                    "temporal_sensitivity": "high",
                    "temporal_anchor": "current",
                    "evidence_need": "fresh"
                }
            ]
        },
        "mock_results": [],
        "expected_status": "failed"
    }
]
```

Note for Python:

In real Python tests, use `None`, not JSON `null`.

---

## Prompt for Claude or Codex Agent

You are implementing Skill 03 for a project called TemporalGuard.

TemporalGuard is a time-aware reliability framework for detecting and correcting outdated responses in Large Language Models.

Your task is to implement only the fresh evidence retrieval skill.

Create a clean, production-quality Python module that retrieves structured evidence for extracted claims.

Create:

1. `src/temporalguard/skills/fresh_evidence_retriever.py`
2. `tests/test_fresh_evidence_retriever.py`

Use this function signature:

```python
def retrieve_fresh_evidence(
    question: str,
    claims_payload: dict,
    temporal_category: str | None = None,
    search_provider=None,
    max_sources_per_claim: int = 3,
    max_claims: int = 5
) -> dict:
```

The function must return:

```python
{
    "evidence_results": [
        {
            "claim_id": "C1",
            "claim_text": "...",
            "query_used": "...",
            "evidence_items": [
                {
                    "evidence_id": "E1",
                    "title": "...",
                    "url": "...",
                    "source_type": "official | government | academic | standards | documentation | reputable_news | company | database | other",
                    "publisher": "...",
                    "published_date": None,
                    "updated_date": None,
                    "retrieved_at": "ISO-8601 timestamp",
                    "evidence_summary": "...",
                    "relevance_score": 0.0,
                    "freshness_hint": "fresh | acceptable | old | unknown",
                    "quote": None
                }
            ],
            "evidence_count": 0,
            "retrieval_status": "success | partial | failed | skipped",
            "notes": "short note"
        }
    ],
    "total_claims_processed": 0,
    "total_evidence_items": 0,
    "retrieval_warnings": []
}
```

Implementation requirements:

* Use Python standard library where possible.
* Do not call an LLM.
* Do not verify truth.
* Do not correct claims.
* Do not generate final user answers.
* Do not browse endlessly.
* Do not scrape full pages unless a provider already supplies snippets.
* Use dependency injection for `search_provider`.
* Implement a simple `SearchProvider` interface or protocol.
* Implement a simple `SearchResult` dataclass.
* Unit tests must use a mock search provider.
* No internet should be required for tests.
* Generate specific search queries from claim text, entities, claim type, temporal anchor, and evidence need.
* Prefer authoritative sources in ranking:

  1. official
  2. government
  3. academic
  4. standards
  5. documentation
  6. database
  7. company
  8. reputable_news
  9. other
* Penalize weak or irrelevant domains if obvious.
* Limit processed claims to `max_claims`.
* Cap `max_claims` internally at 10.
* Cap `max_sources_per_claim` internally at 5.
* Skip claims with `evidence_need == "optional"` unless temporal category requires verification.
* Return `failed` if no useful evidence is found.
* Return `skipped` for optional low-risk claims that do not need retrieval.
* Never fabricate URLs, dates, titles, or publishers.
* If no search provider is provided, return failed retrieval with a useful warning instead of crashing.
* Handle empty claims safely.
* Keep code clean, typed, and easy to extend.
* Use the package name `temporalguard`.

Recommended internal helper functions:

```python
_build_search_query(claim: dict, question: str, temporal_category: str | None) -> str
_should_skip_claim(claim: dict, temporal_category: str | None) -> bool
_rank_search_results(results: list[SearchResult], claim: dict) -> list[SearchResult]
_infer_freshness_hint(result: SearchResult, claim: dict) -> str
_to_evidence_item(result: SearchResult, evidence_id: str, claim: dict) -> dict
_infer_relevance_score(result: SearchResult, claim: dict) -> float
_validate_source_type(source_type: str) -> str
_now_utc_iso() -> str
```

Suggested dataclass:

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str = ""
    publisher: str = "unknown"
    published_date: Optional[str] = None
    updated_date: Optional[str] = None
    source_type: str = "other"
```

Suggested provider protocol:

```python
class SearchProvider:
    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        raise NotImplementedError
```

Important behavior:

* For software claims, add query terms like `official`, `documentation`, `release notes`, or `changelog`.
* For law/policy/visa claims, add query terms like `official` or `government`.
* For company leadership claims, add query terms like `official`, `leadership`, or `press release`.
* For academic claims, add query terms like `paper`, `arXiv`, or `ACL Anthology`.
* For historical claims, include the year/date anchor in the query.
* For latest/current claims, include `latest`, `current`, or `official`.

After implementation:

1. Run tests.
2. Fix all failing tests.
3. Report:

   * files created
   * main logic summary
   * test result
   * assumptions
