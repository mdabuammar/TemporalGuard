# Skill 04: Source Freshness Scoring

## Purpose

This skill scores how fresh, reliable, and time-appropriate each retrieved evidence source is.

TemporalGuard should not only ask:

“Is there a source?”

It must also ask:

“Is this source fresh enough for this claim?”

A source may be reliable but outdated. Another source may be recent but not authoritative. This skill helps TemporalGuard decide whether the evidence is safe to use for verification.

This skill is the fourth step in the TemporalGuard pipeline.

It receives evidence from Skill 03 and assigns freshness scores, reliability scores, and risk labels.

---

## Core Task

Given evidence items for extracted claims, calculate source-level and claim-level freshness scores.

This skill must:

1. Check the evidence publication date and update date.
2. Compare the source date with the claim’s temporal need.
3. Consider source type and authority.
4. Detect stale, undated, weak, or risky evidence.
5. Produce a structured freshness score.
6. Return concise JSON output.
7. Never decide final claim truth.

Final claim truth verification happens later in Skill 05: Temporal Verification.

---

## Important Boundary

This skill does not:

* retrieve new evidence
* verify whether the claim is true or false
* correct the LLM answer
* generate the final answer
* call an LLM by default
* browse the web
* invent missing dates
* assume undated sources are fresh

This skill only scores the evidence already retrieved.

---

## Inputs

The skill may receive input like this:

```json
{
  "question": "What is the latest Python version?",
  "temporal_category": "RECENT_ONLY",
  "evidence_payload": {
    "evidence_results": [
      {
        "claim_id": "C1",
        "claim_text": "Python 3.10 is the latest stable version of Python.",
        "query_used": "Python latest stable version official",
        "evidence_items": [
          {
            "evidence_id": "E1",
            "title": "Download Python",
            "url": "https://www.python.org/downloads/",
            "source_type": "official",
            "publisher": "Python Software Foundation",
            "published_date": null,
            "updated_date": "2026-06-01",
            "retrieved_at": "2026-06-05T12:00:00Z",
            "evidence_summary": "The official Python downloads page lists the latest Python release.",
            "relevance_score": 0.95,
            "freshness_hint": "fresh",
            "quote": null
          }
        ],
        "evidence_count": 1,
        "retrieval_status": "success",
        "notes": "Strong official evidence found."
      }
    ]
  }
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
  "freshness_results": [
    {
      "claim_id": "C1",
      "claim_text": "string",
      "claim_freshness_score": 0.0,
      "claim_reliability_score": 0.0,
      "claim_temporal_risk": "low | medium | high | critical | unknown",
      "best_evidence_id": "E1",
      "evidence_scores": [
        {
          "evidence_id": "E1",
          "url": "string",
          "source_type": "official",
          "publisher": "string",
          "date_used": "YYYY-MM-DD or null",
          "date_basis": "updated_date | published_date | retrieved_at | unavailable",
          "source_age_days": 0,
          "freshness_score": 0.0,
          "authority_score": 0.0,
          "relevance_score": 0.0,
          "combined_score": 0.0,
          "freshness_label": "very_fresh | fresh | acceptable | stale | outdated | unknown",
          "risk_flags": ["string"],
          "notes": "short note"
        }
      ],
      "notes": "short note"
    }
  ],
  "overall_freshness_score": 0.0,
  "overall_temporal_risk": "low | medium | high | critical | unknown",
  "scoring_warnings": ["string"]
}
```

---

## Field Instructions

### claim_freshness_score

A score from `0.0` to `1.0`.

This represents how fresh the evidence is for this claim.

Suggested meaning:

```text
0.90 to 1.00 = very fresh
0.75 to 0.89 = fresh
0.60 to 0.74 = acceptable
0.40 to 0.59 = stale
0.00 to 0.39 = outdated or unsafe
```

---

### claim_reliability_score

A score from `0.0` to `1.0`.

This combines freshness, authority, and relevance.

Suggested formula:

```text
claim_reliability_score = best evidence combined_score
```

For multiple evidence items, use the best item as the main score, but keep all item scores.

---

### claim_temporal_risk

Use one of:

```text
low
medium
high
critical
unknown
```

Use `critical` when:

* the claim is recent/current/latest
* the source is stale or missing
* the domain is high-risk such as legal, medical, visa, finance, policy, safety, or active regulation

Use `high` when:

* the evidence is outdated
* no good source date is available for a time-sensitive claim
* source authority is weak

Use `medium` when:

* evidence is acceptable but not ideal
* source date is unknown but source is official
* source is fresh but not highly authoritative

Use `low` when:

* source is fresh
* source is authoritative
* source is relevant

Use `unknown` when:

* there is not enough evidence to score

---

### best_evidence_id

The evidence item with the highest combined score.

Use `null` if there is no evidence.

---

### date_used

Use the date that is most useful for freshness scoring.

Priority:

1. `updated_date`
2. `published_date`
3. `retrieved_at`
4. `null`

Do not invent a date.

---

### date_basis

Use one of:

```text
updated_date
published_date
retrieved_at
unavailable
```

Use `retrieved_at` only for live/current pages where no update date exists but the source represents current information, such as official downloads pages or official documentation pages.

Use `unavailable` when no meaningful date is available.

---

### source_age_days

Number of days between `date_used` and scoring date.

If date is unavailable, use `null`.

If only year is available, estimate from January 1 of that year and add a risk flag:

```text
year_only_date
```

---

### freshness_score

Score from `0.0` to `1.0`.

This measures whether the source date is fresh enough for the claim.

---

### authority_score

Score from `0.0` to `1.0`.

Suggested values:

```text
official = 1.00
government = 1.00
standards = 0.95
documentation = 0.95
academic = 0.90
database = 0.90
company = 0.85
reputable_news = 0.80
other = 0.50
unknown or weak = 0.30
```

Adjust carefully if the source is clearly weak or suspicious.

---

### relevance_score

Use the relevance score from Skill 03 if available.

If missing, infer a basic score:

```text
direct title/entity match = 0.85
partial match = 0.65
weak match = 0.40
unknown = 0.50
```

---

### combined_score

Suggested formula:

```text
combined_score = (0.45 * freshness_score) + (0.35 * authority_score) + (0.20 * relevance_score)
```

For high-risk domains, freshness and authority are especially important.

Optional high-risk formula:

```text
combined_score = (0.50 * freshness_score) + (0.35 * authority_score) + (0.15 * relevance_score)
```

Keep the formula simple and deterministic.

---

### freshness_label

Use one of:

```text
very_fresh
fresh
acceptable
stale
outdated
unknown
```

Map from freshness score:

```text
0.90 to 1.00 = very_fresh
0.75 to 0.89 = fresh
0.60 to 0.74 = acceptable
0.40 to 0.59 = stale
0.00 to 0.39 = outdated
unknown date = unknown unless official current page is acceptable
```

---

### risk_flags

Use short flags such as:

```text
no_date_available
year_only_date
source_too_old_for_recent_claim
low_authority_source
low_relevance_source
retrieval_failed
optional_claim_skipped
official_live_page_no_update_date
historical_claim_date_match_needed
version_specific_claim
high_risk_domain
```

Return an empty list if no risk flags apply.

---

## Freshness Windows by Evidence Need

Use different freshness expectations for different claim types.

### 1. Fresh / Current Claims

Evidence need:

```text
fresh
```

Examples:

* latest version
* current CEO
* active policy
* today’s price
* current visa rule
* recent research
* current software documentation

Freshness window:

```text
0–30 days = very fresh
31–90 days = fresh
91–180 days = acceptable
181–365 days = stale
365+ days = outdated
```

For official live pages, such as official docs or downloads pages, undated pages may be treated as `acceptable` or `fresh` only if the source is authoritative and clearly represents the current state.

---

### 2. Version-Specific Claims

Evidence need:

```text
version_specific
```

Examples:

* pandas 2.0 behavior
* Python 3.10 support
* CUDA compatibility
* OpenAI SDK usage

Freshness depends on the version, not only the current date.

Scoring rule:

* Official versioned docs = high score
* Official changelog/release notes = high score
* Random blog = low score
* Undated unofficial source = high risk

For version-specific evidence:

```text
official documentation/release notes = 0.85–1.00
documentation with unknown date = 0.70–0.85
unofficial old blog = 0.30–0.55
```

---

### 3. Historical Claims

Evidence need:

```text
historical
```

Examples:

* Who was president in 2016?
* What was the latest Python version in 2020?
* What did a 2021 policy say?

For historical claims, newness is not the main issue. Time alignment is the main issue.

Scoring rule:

* Reliable source that matches the historical anchor = high score
* Current page summarizing historical facts = acceptable if authoritative
* Source without the requested year/date = medium or low score
* Current-only page for a historical question = risky

For historical claims:

```text
government/official/academic historical source = 0.85–1.00
reputable historical summary = 0.70–0.85
undated or weak source = 0.40–0.60
```

Add risk flag:

```text
historical_claim_date_match_needed
```

when the evidence does not clearly contain the historical anchor.

---

### 4. Optional / Static Claims

Evidence need:

```text
optional
```

Examples:

* Binary search divides sorted data.
* RAM is volatile memory.
* Newton’s second law is F = ma.

Freshness is less important.

Scoring rule:

* Authority and relevance matter more than recency.
* Older academic or educational sources can still be acceptable.
* If retrieval was skipped, do not treat it as a critical risk.

For optional/static claims:

```text
authoritative educational source = high score
old but stable source = acceptable
no evidence = low risk if claim is truly static
```

---

## High-Risk Domains

Increase temporal risk when the claim involves:

```text
medical
medicine
clinical guideline
drug safety
law
legal rule
visa
immigration
tax
finance
price
interest rate
stock
crypto
policy
regulation
university admission
Amazon policy
safety
security advisory
software vulnerability
```

For high-risk domains:

* do not accept weak evidence
* do not accept outdated evidence
* add `high_risk_domain` risk flag
* increase risk if date is missing

---

## Source Authority Rules

### Very High Authority

```text
official
government
documentation
standards
```

Score:

```text
0.95 to 1.00
```

### High Authority

```text
academic
database
company
```

Score:

```text
0.85 to 0.95
```

### Medium Authority

```text
reputable_news
```

Score:

```text
0.75 to 0.85
```

### Low Authority

```text
other
unknown
blog
forum
social media
```

Score:

```text
0.30 to 0.60
```

---

## Date Handling Rules

### Rule 1: Prefer updated date

If both `published_date` and `updated_date` exist, use `updated_date`.

---

### Rule 2: Use retrieved_at carefully

Use `retrieved_at` as date basis only when:

* the page is official, government, documentation, or database
* the page represents current live information
* no update date is available

Add risk flag:

```text
official_live_page_no_update_date
```

Do not use `retrieved_at` for news, blogs, or academic papers unless no other option exists.

---

### Rule 3: Unknown dates are risky for time-sensitive claims

If a source has no date and the claim is current/latest/active, freshness score should not be high unless the source is official live information.

---

### Rule 4: Do not invent missing dates

If date is missing, use:

```json
"date_used": null,
"date_basis": "unavailable",
"source_age_days": null
```

---

## Risk Label Rules

### Low Risk

Use when:

* evidence is fresh enough
* source is authoritative
* relevance is high

Example:

```text
Official Python downloads page retrieved recently for latest Python version.
```

---

### Medium Risk

Use when:

* source is reliable but date is unclear
* evidence is acceptable but not perfect
* source is recent but not official

---

### High Risk

Use when:

* source is old for a current claim
* source has no date and is not official
* evidence is weak
* relevance is low

---

### Critical Risk

Use when:

* no evidence is available for a high-risk claim
* evidence is outdated for legal, medical, finance, visa, or safety claim
* evidence source is weak and the claim may cause real-world harm

---

## Output Examples

### Example 1: Fresh Official Source

Input evidence:

```json
{
  "claim_id": "C1",
  "claim_text": "Python 3.10 is the latest stable version of Python.",
  "evidence_items": [
    {
      "evidence_id": "E1",
      "title": "Download Python",
      "url": "https://www.python.org/downloads/",
      "source_type": "official",
      "publisher": "Python Software Foundation",
      "published_date": null,
      "updated_date": "2026-06-01",
      "retrieved_at": "2026-06-05T12:00:00Z",
      "relevance_score": 0.95
    }
  ]
}
```

Output:

```json
{
  "claim_id": "C1",
  "claim_freshness_score": 0.98,
  "claim_reliability_score": 0.98,
  "claim_temporal_risk": "low",
  "best_evidence_id": "E1"
}
```

---

### Example 2: Old Source for Current Claim

Evidence updated 2 years ago for a latest/current claim.

Output idea:

```json
{
  "freshness_score": 0.25,
  "freshness_label": "outdated",
  "risk_flags": ["source_too_old_for_recent_claim"],
  "claim_temporal_risk": "high"
}
```

---

### Example 3: Historical Claim

Claim:

```text
Barack Obama was the U.S. president in 2016.
```

Evidence:

White House presidents page.

Output idea:

```json
{
  "freshness_label": "acceptable",
  "claim_temporal_risk": "low",
  "risk_flags": []
}
```

---

### Example 4: No Date for Visa Rule

Claim:

```text
The Canada student visa SDS program is no longer active.
```

Evidence has no date.

Output idea:

```json
{
  "freshness_label": "unknown",
  "risk_flags": ["no_date_available", "high_risk_domain"],
  "claim_temporal_risk": "high"
}
```

---

## Implementation Notes for AI Coding Agents

Build this skill as a deterministic scoring module.

Do not call web search.

Do not call an LLM.

Do not browse URLs.

Do not use large context.

Do not verify the claim yet.

This module only scores evidence freshness and reliability.

Recommended implementation:

* Create a Python module such as `source_freshness_scorer.py`
* Create a function named `score_source_freshness(...) -> dict`
* Use standard library only
* Use `datetime` for date parsing and age calculation
* Use simple deterministic formulas
* Accept an optional `scoring_datetime` for reproducible tests
* Return strict JSON-compatible dictionary
* Add unit tests using fixed scoring dates
* Handle malformed dates safely
* Keep code typed and easy to extend

---

## Suggested Python Interface

Use this interface:

```python
def score_source_freshness(
    evidence_payload: dict,
    temporal_category: str | None = None,
    scoring_datetime: str | None = None
) -> dict:
    """
    Score freshness and reliability of retrieved evidence.

    Args:
        evidence_payload: Output from Skill 03.
        temporal_category: Optional category from Skill 01.
        scoring_datetime: Optional ISO datetime string for reproducible scoring.

    Returns:
        JSON-compatible dict with freshness results, scores, and warnings.
    """
```

---

## Expected Behavior

The scorer should be fast, cheap, and deterministic.

It must not waste tokens.

It must not call an LLM.

It must not perform web search.

It must not generate final answers.

It only scores already retrieved evidence.

---

## Quality Requirements

The implementation must satisfy these requirements:

1. Return valid JSON-compatible dictionary every time.
2. Score freshness based on claim evidence need.
3. Score source authority based on source type.
4. Use relevance score from Skill 03 when available.
5. Calculate source age in days when date exists.
6. Handle missing dates safely.
7. Handle malformed dates without crashing.
8. Treat high-risk domains more strictly.
9. Treat historical claims differently from current claims.
10. Treat version-specific claims differently from current claims.
11. Never invent dates.
12. Never fetch new evidence.
13. Never verify truth.
14. Include unit tests.
15. Keep the module reusable for the full TemporalGuard pipeline.
16. Keep formulas simple and explainable for thesis writing.

---

## Test Cases

Use fixed `scoring_datetime = "2026-06-05T12:00:00Z"` for tests.

Minimum test cases:

```python
test_cases = [
    {
        "name": "fresh official current source",
        "temporal_category": "RECENT_ONLY",
        "evidence_payload": {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python 3.10 is the latest stable version of Python.",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "url": "https://www.python.org/downloads/",
                            "source_type": "official",
                            "publisher": "Python Software Foundation",
                            "published_date": None,
                            "updated_date": "2026-06-01",
                            "retrieved_at": "2026-06-05T12:00:00Z",
                            "relevance_score": 0.95
                        }
                    ]
                }
            ]
        },
        "expected_risk": "low"
    },
    {
        "name": "old source for current claim",
        "temporal_category": "RECENT_ONLY",
        "evidence_payload": {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "claim_text": "The latest TensorFlow version is 2.x.",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "url": "https://example.com/tensorflow-old",
                            "source_type": "other",
                            "publisher": "unknown",
                            "published_date": "2022-01-01",
                            "updated_date": None,
                            "retrieved_at": "2026-06-05T12:00:00Z",
                            "relevance_score": 0.70
                        }
                    ]
                }
            ]
        },
        "expected_risk": "high"
    },
    {
        "name": "historical government source",
        "temporal_category": "HISTORICAL",
        "evidence_payload": {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "claim_text": "Barack Obama was the president of the United States in 2016.",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "url": "https://www.whitehouse.gov/about-the-white-house/presidents/",
                            "source_type": "government",
                            "publisher": "The White House",
                            "published_date": None,
                            "updated_date": None,
                            "retrieved_at": "2026-06-05T12:00:00Z",
                            "relevance_score": 0.90
                        }
                    ]
                }
            ]
        },
        "expected_risk": "low"
    },
    {
        "name": "high risk policy source with no date",
        "temporal_category": "RECENT_ONLY",
        "evidence_payload": {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "claim_text": "The Canada student visa SDS program is no longer active.",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "url": "https://example.com/visa-rule",
                            "source_type": "other",
                            "publisher": "unknown",
                            "published_date": None,
                            "updated_date": None,
                            "retrieved_at": "2026-06-05T12:00:00Z",
                            "relevance_score": 0.80
                        }
                    ]
                }
            ]
        },
        "expected_risk": "critical"
    },
    {
        "name": "no evidence available",
        "temporal_category": "TIME_SENSITIVE",
        "evidence_payload": {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "claim_text": "Xyzabc system is currently active.",
                    "evidence_items": []
                }
            ]
        },
        "expected_risk": "high"
    }
]
```

---

## Prompt for Claude or Codex Agent

You are implementing Skill 04 for a project called TemporalGuard.

TemporalGuard is a time-aware reliability framework for detecting and correcting outdated responses in Large Language Models.

Your task is to implement only the source freshness scoring skill.

Create a clean, production-quality Python module that scores evidence freshness, source authority, relevance, combined reliability, and temporal risk.

Create:

1. `src/temporalguard/skills/source_freshness_scorer.py`
2. `tests/test_source_freshness_scorer.py`

Use this function signature:

```python
def score_source_freshness(
    evidence_payload: dict,
    temporal_category: str | None = None,
    scoring_datetime: str | None = None
) -> dict:
```

The function must return:

```python
{
    "freshness_results": [
        {
            "claim_id": "C1",
            "claim_text": "...",
            "claim_freshness_score": 0.0,
            "claim_reliability_score": 0.0,
            "claim_temporal_risk": "low | medium | high | critical | unknown",
            "best_evidence_id": "E1",
            "evidence_scores": [
                {
                    "evidence_id": "E1",
                    "url": "...",
                    "source_type": "...",
                    "publisher": "...",
                    "date_used": None,
                    "date_basis": "updated_date | published_date | retrieved_at | unavailable",
                    "source_age_days": None,
                    "freshness_score": 0.0,
                    "authority_score": 0.0,
                    "relevance_score": 0.0,
                    "combined_score": 0.0,
                    "freshness_label": "very_fresh | fresh | acceptable | stale | outdated | unknown",
                    "risk_flags": [],
                    "notes": "short note"
                }
            ],
            "notes": "short note"
        }
    ],
    "overall_freshness_score": 0.0,
    "overall_temporal_risk": "low | medium | high | critical | unknown",
    "scoring_warnings": []
}
```

Implementation requirements:

* Use Python standard library only.
* Do not call an LLM.
* Do not call web search.
* Do not browse URLs.
* Do not verify whether the claim is true.
* Do not correct the claim.
* Do not generate final user answers.
* Use deterministic scoring formulas.
* Parse ISO dates safely.
* Support dates in these formats:

  * `YYYY-MM-DD`
  * `YYYY`
  * ISO datetime such as `2026-06-05T12:00:00Z`
* Prefer `updated_date` over `published_date`.
* Use `retrieved_at` only for official/government/documentation/database/standards live pages with no other date.
* Never invent missing dates.
* Assign authority score from source type.
* Use provided relevance score when available.
* Infer risk flags for missing date, stale source, weak source, high-risk domain, malformed date, and no evidence.
* Treat `RECENT_ONLY`, `TIME_SENSITIVE`, and `VERSION_DEPENDENT` claims more strictly than `STATIC`.
* Treat `HISTORICAL` claims by prioritizing source authority and relevance over recency.
* Treat `version_specific` evidence as acceptable when the source is official documentation or release notes, even if not very recent.
* Calculate combined score using:

  * normal: `(0.45 * freshness) + (0.35 * authority) + (0.20 * relevance)`
  * high-risk: `(0.50 * freshness) + (0.35 * authority) + (0.15 * relevance)`
* Clamp all scores between `0.0` and `1.0`.
* Round scores to 3 decimals.
* Add unit tests with fixed scoring datetime.
* Keep code clean, typed, and easy to extend.
* Use the package name `temporalguard`.

Recommended internal helper functions:

```python
_parse_date(value: str | None) -> tuple[datetime | None, str | None]
_select_date(evidence_item: dict) -> tuple[str | None, str]
_calculate_age_days(date_value: datetime | None, scoring_dt: datetime) -> int | None
_authority_score(source_type: str) -> float
_detect_high_risk_domain(claim_text: str) -> bool
_score_freshness(age_days: int | None, evidence_need: str | None, temporal_category: str | None, source_type: str, date_basis: str) -> tuple[float, str, list[str]]
_combined_score(freshness_score: float, authority_score: float, relevance_score: float, high_risk: bool) -> float
_risk_from_scores(combined_score: float, freshness_score: float, risk_flags: list[str], high_risk: bool, has_evidence: bool) -> str
_score_evidence_item(item: dict, claim_result: dict, temporal_category: str | None, scoring_dt: datetime) -> dict
_score_claim_evidence(claim_result: dict, temporal_category: str | None, scoring_dt: datetime) -> dict
```

Important behavior:

* If a claim has no evidence items, return:

```python
{
    "claim_freshness_score": 0.0,
    "claim_reliability_score": 0.0,
    "claim_temporal_risk": "high" or "critical",
    "best_evidence_id": None,
    "evidence_scores": [],
    "notes": "No evidence available for freshness scoring."
}
```

* Use `critical` for no evidence if the claim is high-risk domain.
* Use `high` for no evidence if the claim is time-sensitive but not high-risk.
* Use `medium` or `low` for no evidence only if the claim is optional/static.
* Overall score should be the average of claim reliability scores.
* Overall risk should be the worst risk among claims.

After implementation:

1. Run tests.
2. Fix all failing tests.
3. Report:

   * files created
   * main logic summary
   * test result
   * assumptions
