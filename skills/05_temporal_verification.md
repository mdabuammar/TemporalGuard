# Skill 05: Temporal Verification

## Purpose

This skill verifies whether an extracted claim is supported, outdated, contradicted, or uncertain based on retrieved and freshness-scored evidence.

TemporalGuard should not only collect sources. It must decide whether the LLM’s claim still matches the best available evidence for the correct time period.

This skill is the fifth step in the TemporalGuard pipeline.

It receives:

1. Extracted claims from Skill 02
2. Evidence retrieved by Skill 03
3. Freshness and reliability scores from Skill 04
4. The original question
5. The temporal category from Skill 01

It returns a structured verification result for each claim.

---

## Core Task

Given a claim and its evidence, classify the claim into one verification status:

1. `SUPPORTED`
2. `OUTDATED`
3. `CONTRADICTED`
4. `PARTIALLY_SUPPORTED`
5. `INSUFFICIENT_EVIDENCE`
6. `NOT_VERIFIABLE`

This skill must check whether the claim matches the evidence and whether the evidence is fresh enough for the temporal context.

---

## Important Boundary

This skill does not:

* retrieve new sources
* score source freshness
* rewrite the final answer
* generate the corrected answer
* browse the web
* call an LLM by default
* use long context prompts
* invent missing evidence
* assume a claim is true without evidence

This skill only verifies claims using already available evidence.

Correction happens later in Skill 07.

---

## Inputs

The skill may receive input like this:

```json
{
  "question": "What is the latest Python version?",
  "temporal_category": "RECENT_ONLY",
  "claims_payload": {
    "claims": [
      {
        "claim_id": "C1",
        "claim_text": "Python 3.10 is the latest stable version of Python.",
        "normalized_claim": "Python 3.10 is the latest stable Python version.",
        "claim_type": "software_version",
        "entities": ["Python", "Python 3.10"],
        "temporal_sensitivity": "high",
        "requires_verification": true,
        "temporal_anchor": "latest",
        "evidence_need": "fresh",
        "confidence": 0.96
      }
    ]
  },
  "evidence_payload": {
    "evidence_results": [
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
            "updated_date": "2026-06-01",
            "evidence_summary": "The official Python downloads page lists Python 3.13.5 as the latest release.",
            "relevance_score": 0.95,
            "freshness_hint": "fresh"
          }
        ],
        "retrieval_status": "success"
      }
    ]
  },
  "freshness_payload": {
    "freshness_results": [
      {
        "claim_id": "C1",
        "claim_freshness_score": 0.98,
        "claim_reliability_score": 0.98,
        "claim_temporal_risk": "low",
        "best_evidence_id": "E1"
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
  "verification_results": [
    {
      "claim_id": "C1",
      "claim_text": "string",
      "verification_status": "SUPPORTED | OUTDATED | CONTRADICTED | PARTIALLY_SUPPORTED | INSUFFICIENT_EVIDENCE | NOT_VERIFIABLE",
      "temporal_validity": "current | historical | version_specific | expired | uncertain | not_applicable",
      "verification_confidence": 0.0,
      "evidence_used": ["E1"],
      "best_evidence_id": "E1",
      "reason": "short reason",
      "detected_conflict": "short conflict or null",
      "claim_value": "string or null",
      "evidence_value": "string or null",
      "requires_correction": true,
      "risk_level": "low | medium | high | critical | unknown",
      "notes": "short note"
    }
  ],
  "overall_verification_status": "SUPPORTED | NEEDS_CORRECTION | INSUFFICIENT_EVIDENCE | MIXED | NOT_VERIFIABLE",
  "overall_confidence": 0.0,
  "verification_warnings": ["string"]
}
```

---

## Verification Status Definitions

### 1. SUPPORTED

Use `SUPPORTED` when reliable evidence agrees with the claim.

Example:

Claim:

```text
Barack Obama was the president of the United States in 2016.
```

Evidence:

```text
Official White House page confirms Barack Obama served as the 44th president.
```

Status:

```text
SUPPORTED
```

---

### 2. OUTDATED

Use `OUTDATED` when the claim was likely true before but is no longer current.

Example:

Claim:

```text
Python 3.10 is the latest stable version of Python.
```

Evidence:

```text
Official Python page says Python 3.13.5 is the latest version.
```

Status:

```text
OUTDATED
```

Use this when the claim contains:

* old software version
* old CEO or leadership
* old policy status
* old price
* old guideline
* old model name
* old deadline
* old API behavior replaced by new documentation

---

### 3. CONTRADICTED

Use `CONTRADICTED` when evidence directly says the claim is false, and it is not mainly a time-staleness issue.

Example:

Claim:

```text
France won the 2014 FIFA World Cup.
```

Evidence:

```text
Germany won the 2014 FIFA World Cup.
```

Status:

```text
CONTRADICTED
```

Difference from `OUTDATED`:

* `OUTDATED`: claim may have been true earlier but is not true now.
* `CONTRADICTED`: claim appears false for the requested time/context.

---

### 4. PARTIALLY_SUPPORTED

Use `PARTIALLY_SUPPORTED` when part of the claim is correct, but another important part is missing, unclear, or wrong.

Example:

Claim:

```text
The OpenAI Python SDK supports model calls and image generation through the same endpoint.
```

Evidence:

```text
The SDK supports model calls, but image generation uses a different documented path.
```

Status:

```text
PARTIALLY_SUPPORTED
```

---

### 5. INSUFFICIENT_EVIDENCE

Use `INSUFFICIENT_EVIDENCE` when evidence is missing, weak, stale, low authority, or not relevant enough.

Example:

Claim:

```text
This visa rule is still active.
```

Evidence:

```text
Only an old blog post with no date is available.
```

Status:

```text
INSUFFICIENT_EVIDENCE
```

---

### 6. NOT_VERIFIABLE

Use `NOT_VERIFIABLE` when the claim is subjective, vague, personal, or not factual.

Example:

```text
Python is the best programming language.
```

Status:

```text
NOT_VERIFIABLE
```

This should be rare because Skill 02 should avoid extracting non-checkable claims.

---

## Temporal Validity Labels

Use one of:

```text
current
historical
version_specific
expired
uncertain
not_applicable
```

### current

Use when the claim is supported as current.

### historical

Use when the claim is supported for a specific past time.

### version_specific

Use when the claim is valid only for a specific software/API/library/model version.

### expired

Use when the claim appears outdated or no longer valid.

### uncertain

Use when evidence is not enough.

### not_applicable

Use for static facts or non-temporal facts.

---

## Field Instructions

### verification_confidence

Score from `0.0` to `1.0`.

This is confidence in the verification decision.

Suggested values:

```text
0.90 to 1.00 = strong evidence and clear decision
0.75 to 0.89 = good evidence and likely decision
0.60 to 0.74 = moderate confidence
0.40 to 0.59 = weak confidence
0.00 to 0.39 = very uncertain
```

---

### evidence_used

List the evidence IDs used for the decision.

Example:

```json
["E1", "E2"]
```

Use an empty list if no evidence is usable.

---

### best_evidence_id

Use the best evidence ID from Skill 04 when available.

Use `null` if no evidence exists.

---

### reason

A short explanation of why the status was assigned.

Good:

```text
The claim says Python 3.10 is latest, but official evidence lists Python 3.13.5 as latest.
```

Bad:

```text
The evidence is different.
```

---

### detected_conflict

Use this to show the core mismatch.

Example:

```text
Claim value: Python 3.10; Evidence value: Python 3.13.5.
```

Use `null` if there is no conflict.

---

### claim_value

Extract the important value from the claim.

Examples:

```text
Python 3.10
Sam Altman
active
92%
June 15, 2026
```

Use `null` if no clear value exists.

---

### evidence_value

Extract the important value from the evidence.

Examples:

```text
Python 3.13.5
Satya Nadella
inactive
89%
June 20, 2026
```

Use `null` if no clear value exists.

---

### requires_correction

Use `true` for:

* `OUTDATED`
* `CONTRADICTED`
* `PARTIALLY_SUPPORTED`

Usually use `true` for high-risk `INSUFFICIENT_EVIDENCE`.

Use `false` for:

* `SUPPORTED`
* low-risk `INSUFFICIENT_EVIDENCE`
* `NOT_VERIFIABLE`

---

### risk_level

Use the claim temporal risk from Skill 04 if available.

If missing, infer risk from the verification status:

```text
SUPPORTED = low
PARTIALLY_SUPPORTED = medium
OUTDATED = high
CONTRADICTED = high
INSUFFICIENT_EVIDENCE = medium/high depending on claim risk
NOT_VERIFIABLE = unknown
```

Use `critical` for high-risk domains such as legal, visa, medical, finance, safety, or regulation when evidence is insufficient or contradicted.

---

## Verification Decision Rules

### Rule 1: No useful evidence means insufficient evidence

If no evidence exists or retrieval failed:

```text
INSUFFICIENT_EVIDENCE
```

Do not guess.

---

### Rule 2: Freshness matters for current claims

For `RECENT_ONLY`, `TIME_SENSITIVE`, and `VERSION_DEPENDENT`, stale evidence should reduce confidence.

If evidence is stale or outdated:

```text
INSUFFICIENT_EVIDENCE
```

unless it clearly contradicts the claim.

---

### Rule 3: Official evidence can override model claim

If an official, government, documentation, academic, standards, or reliable database source clearly disagrees with the claim, classify as:

* `OUTDATED` if the claim is current/latest/status-based
* `CONTRADICTED` if the claim is false for the requested context

---

### Rule 4: Historical claims need time alignment

For `HISTORICAL` claims, check whether the evidence matches the requested time anchor.

Example:

Question:

```text
Who was the U.S. president in 2016?
```

Claim:

```text
Barack Obama was the U.S. president in 2016.
```

Evidence:

```text
Barack Obama served as president from 2009 to 2017.
```

Status:

```text
SUPPORTED
```

If evidence only shows the current president, classify as:

```text
INSUFFICIENT_EVIDENCE
```

or `CONTRADICTED` if it directly conflicts with the historical claim.

---

### Rule 5: Version-specific claims need version alignment

For `VERSION_DEPENDENT` claims, check whether the evidence refers to the same version or current documentation.

Example:

Claim:

```text
In pandas 2.0, method X is deprecated.
```

Good evidence:

```text
Official pandas 2.0 release notes mention method X deprecation.
```

Status:

```text
SUPPORTED
```

If evidence is for a different version and no connection is clear:

```text
INSUFFICIENT_EVIDENCE
```

---

### Rule 6: Current/latest claims need value comparison

For claims involving latest/current/newest, compare the main value.

Example:

Claim:

```text
Python 3.10 is the latest Python version.
```

Evidence:

```text
Python 3.13.5 is the latest Python version.
```

Status:

```text
OUTDATED
```

---

### Rule 7: Active/inactive policy claims need status comparison

Example:

Claim:

```text
The SDS program is still active.
```

Evidence:

```text
The SDS program ended on November 8, 2024.
```

Status:

```text
OUTDATED
```

or `CONTRADICTED`, depending on wording.

Prefer `OUTDATED` if the claim sounds like old status information.

Prefer `CONTRADICTED` if it is simply false in the requested time.

---

### Rule 8: Numbers, dates, and named entities are high-signal

Pay attention to:

* version numbers
* dates
* prices
* percentages
* names
* product names
* model names
* company names
* policy names
* status words

If these differ clearly between claim and evidence, mark conflict.

---

### Rule 9: Static educational facts can be supported with lower freshness need

For static claims, evidence freshness is less important.

Example:

```text
Binary search divides a sorted search space in half.
```

Old but reliable educational evidence can support it.

---

### Rule 10: Use conservative decisions

If unsure, choose:

```text
INSUFFICIENT_EVIDENCE
```

Do not overclaim.

---

## Simple Matching Strategy

To keep this module lightweight and token-efficient, use deterministic methods first.

Suggested approach:

1. Match claim with evidence by `claim_id`.
2. Select best evidence from Skill 04.
3. Compare important values in claim and evidence summary:

   * version numbers
   * years
   * dates
   * percentages
   * currency amounts
   * named entities
   * status words
4. Use source freshness/reliability scores.
5. Assign verification status.
6. Optional LLM/NLI fallback may be added later, but keep disabled by default.

---

## Important Value Extraction

Extract these value types:

### Version values

Examples:

```text
Python 3.10
3.13.5
v2.0
TensorFlow 2.15
```

### Date values

Examples:

```text
2020
June 15, 2026
2026-06-15
November 8, 2024
```

### Status values

Examples:

```text
active
inactive
ended
deprecated
supported
unsupported
available
not available
released
not released
```

### Numeric values

Examples:

```text
92%
0.89
$99
30 days
```

### Named entity values

Examples:

```text
Sam Altman
Barack Obama
OpenAI
Canada SDS program
```

---

## Output Examples

### Example 1: Outdated Software Version

Input claim:

```text
Python 3.10 is the latest stable version of Python.
```

Evidence summary:

```text
The official Python downloads page lists Python 3.13.5 as the latest release.
```

Output:

```json
{
  "claim_id": "C1",
  "verification_status": "OUTDATED",
  "temporal_validity": "expired",
  "verification_confidence": 0.94,
  "evidence_used": ["E1"],
  "best_evidence_id": "E1",
  "reason": "The claim says Python 3.10 is latest, but official evidence lists Python 3.13.5 as latest.",
  "detected_conflict": "Claim value: Python 3.10; Evidence value: Python 3.13.5.",
  "claim_value": "Python 3.10",
  "evidence_value": "Python 3.13.5",
  "requires_correction": true,
  "risk_level": "high"
}
```

---

### Example 2: Supported Historical Claim

Input claim:

```text
Barack Obama was the president of the United States in 2016.
```

Evidence summary:

```text
The White House lists Barack Obama as serving from 2009 to 2017.
```

Output:

```json
{
  "claim_id": "C1",
  "verification_status": "SUPPORTED",
  "temporal_validity": "historical",
  "verification_confidence": 0.92,
  "evidence_used": ["E1"],
  "best_evidence_id": "E1",
  "reason": "The evidence supports that Barack Obama was president during 2016.",
  "detected_conflict": null,
  "claim_value": "Barack Obama",
  "evidence_value": "Barack Obama",
  "requires_correction": false,
  "risk_level": "low"
}
```

---

### Example 3: Insufficient Evidence

Input claim:

```text
The Xyzabc system is currently active.
```

Evidence:

```text
No reliable evidence found.
```

Output:

```json
{
  "claim_id": "C1",
  "verification_status": "INSUFFICIENT_EVIDENCE",
  "temporal_validity": "uncertain",
  "verification_confidence": 0.80,
  "evidence_used": [],
  "best_evidence_id": null,
  "reason": "No reliable evidence was available to verify the current status of the claim.",
  "detected_conflict": null,
  "claim_value": "active",
  "evidence_value": null,
  "requires_correction": true,
  "risk_level": "high"
}
```

---

### Example 4: Contradicted Event Result

Input claim:

```text
France won the 2014 FIFA World Cup.
```

Evidence summary:

```text
Germany won the 2014 FIFA World Cup.
```

Output:

```json
{
  "claim_id": "C1",
  "verification_status": "CONTRADICTED",
  "temporal_validity": "historical",
  "verification_confidence": 0.93,
  "evidence_used": ["E1"],
  "best_evidence_id": "E1",
  "reason": "The claim says France won the 2014 FIFA World Cup, but evidence says Germany won.",
  "detected_conflict": "Claim value: France; Evidence value: Germany.",
  "claim_value": "France",
  "evidence_value": "Germany",
  "requires_correction": true,
  "risk_level": "high"
}
```

---

## Implementation Notes for AI Coding Agents

Build this skill as a deterministic verification module.

Do not call web search.

Do not browse URLs.

Do not call an LLM by default.

Do not create a large agent chain.

Do not use long prompts in the code.

Use simple rule-based comparison first. Add optional LLM/NLI fallback later only as a disabled extension point.

Recommended implementation:

* Create a Python module such as `temporal_verifier.py`
* Create a function named `verify_temporal_claims(...) -> dict`
* Use standard library only
* Match claims by `claim_id`
* Use evidence summaries, titles, quotes, and freshness scores
* Extract versions, dates, numbers, status words, and named entities with regex/simple heuristics
* Keep outputs deterministic
* Add unit tests using fixed payloads
* Return strict JSON-compatible dictionary
* Handle missing evidence safely
* Keep the module reusable for the full TemporalGuard pipeline

---

## Suggested Python Interface

Use this interface:

```python
def verify_temporal_claims(
    question: str,
    claims_payload: dict,
    evidence_payload: dict,
    freshness_payload: dict | None = None,
    temporal_category: str | None = None
) -> dict:
    """
    Verify extracted claims against retrieved and freshness-scored evidence.

    Args:
        question: Original user question.
        claims_payload: Output from Skill 02.
        evidence_payload: Output from Skill 03.
        freshness_payload: Optional output from Skill 04.
        temporal_category: Optional category from Skill 01.

    Returns:
        JSON-compatible dict with verification results and overall status.
    """
```

---

## Expected Behavior

The verifier should be fast, cheap, and conservative.

It must not waste tokens.

It must not call an LLM.

It must not perform web search.

It must not generate corrected answers.

It only verifies whether claims are supported, outdated, contradicted, partially supported, insufficient, or not verifiable.

---

## Quality Requirements

The implementation must satisfy these requirements:

1. Return valid JSON-compatible dictionary every time.
2. Match claims to evidence using `claim_id`.
3. Use best evidence from freshness scoring when available.
4. Detect conflicts in versions, names, dates, numbers, and status words.
5. Treat current/latest claims carefully.
6. Treat historical claims by checking temporal alignment.
7. Treat version-specific claims by checking version alignment.
8. Use freshness/reliability scores to avoid trusting stale sources.
9. Return `INSUFFICIENT_EVIDENCE` when evidence is missing or weak.
10. Never invent evidence values.
11. Never correct the claim inside this module.
12. Avoid LLM calls by default.
13. Include unit tests.
14. Keep code typed, clean, and easy to extend.
15. Use simple explainable logic suitable for a university thesis.

---

## Test Cases

Use these minimum test cases:

```python
test_cases = [
    {
        "name": "outdated latest Python claim",
        "question": "What is the latest Python version?",
        "temporal_category": "RECENT_ONLY",
        "claims_payload": {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python 3.10 is the latest stable version of Python.",
                    "normalized_claim": "Python 3.10 is the latest stable Python version.",
                    "claim_type": "software_version",
                    "entities": ["Python", "Python 3.10"],
                    "temporal_anchor": "latest",
                    "evidence_need": "fresh"
                }
            ]
        },
        "evidence_payload": {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "title": "Download Python",
                            "source_type": "official",
                            "publisher": "Python Software Foundation",
                            "evidence_summary": "The official Python downloads page lists Python 3.13.5 as the latest release.",
                            "relevance_score": 0.95
                        }
                    ],
                    "retrieval_status": "success"
                }
            ]
        },
        "freshness_payload": {
            "freshness_results": [
                {
                    "claim_id": "C1",
                    "claim_freshness_score": 0.98,
                    "claim_reliability_score": 0.98,
                    "claim_temporal_risk": "low",
                    "best_evidence_id": "E1"
                }
            ]
        },
        "expected_status": "OUTDATED"
    },
    {
        "name": "supported historical president claim",
        "question": "Who was the president of the USA in 2016?",
        "temporal_category": "HISTORICAL",
        "claims_payload": {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Barack Obama was the president of the United States in 2016.",
                    "claim_type": "historical_fact",
                    "entities": ["Barack Obama", "United States", "president"],
                    "temporal_anchor": "2016",
                    "evidence_need": "historical"
                }
            ]
        },
        "evidence_payload": {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "title": "Presidents of the United States",
                            "source_type": "government",
                            "publisher": "The White House",
                            "evidence_summary": "Barack Obama served as the 44th President of the United States from 2009 to 2017.",
                            "relevance_score": 0.90
                        }
                    ],
                    "retrieval_status": "success"
                }
            ]
        },
        "freshness_payload": {
            "freshness_results": [
                {
                    "claim_id": "C1",
                    "claim_freshness_score": 0.90,
                    "claim_reliability_score": 0.95,
                    "claim_temporal_risk": "low",
                    "best_evidence_id": "E1"
                }
            ]
        },
        "expected_status": "SUPPORTED"
    },
    {
        "name": "contradicted world cup claim",
        "question": "Who won the 2014 FIFA World Cup?",
        "temporal_category": "HISTORICAL",
        "claims_payload": {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "France won the 2014 FIFA World Cup.",
                    "claim_type": "event_result",
                    "entities": ["France", "2014 FIFA World Cup"],
                    "temporal_anchor": "2014",
                    "evidence_need": "historical"
                }
            ]
        },
        "evidence_payload": {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "title": "2014 FIFA World Cup",
                            "source_type": "official",
                            "publisher": "FIFA",
                            "evidence_summary": "Germany won the 2014 FIFA World Cup.",
                            "relevance_score": 0.95
                        }
                    ],
                    "retrieval_status": "success"
                }
            ]
        },
        "freshness_payload": {
            "freshness_results": [
                {
                    "claim_id": "C1",
                    "claim_freshness_score": 0.90,
                    "claim_reliability_score": 0.95,
                    "claim_temporal_risk": "low",
                    "best_evidence_id": "E1"
                }
            ]
        },
        "expected_status": "CONTRADICTED"
    },
    {
        "name": "insufficient evidence for unknown current system",
        "question": "Is Xyzabc system currently active?",
        "temporal_category": "RECENT_ONLY",
        "claims_payload": {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "The Xyzabc system is currently active.",
                    "claim_type": "current_status",
                    "entities": ["Xyzabc system"],
                    "temporal_anchor": "current",
                    "evidence_need": "fresh"
                }
            ]
        },
        "evidence_payload": {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [],
                    "retrieval_status": "failed"
                }
            ]
        },
        "freshness_payload": {
            "freshness_results": [
                {
                    "claim_id": "C1",
                    "claim_freshness_score": 0.0,
                    "claim_reliability_score": 0.0,
                    "claim_temporal_risk": "high",
                    "best_evidence_id": null
                }
            ]
        },
        "expected_status": "INSUFFICIENT_EVIDENCE"
    },
    {
        "name": "supported static definition",
        "question": "What is binary search?",
        "temporal_category": "STATIC",
        "claims_payload": {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_text": "Binary search divides a sorted search space in half.",
                    "claim_type": "definition",
                    "entities": ["binary search"],
                    "temporal_anchor": null,
                    "evidence_need": "optional"
                }
            ]
        },
        "evidence_payload": {
            "evidence_results": [
                {
                    "claim_id": "C1",
                    "evidence_items": [
                        {
                            "evidence_id": "E1",
                            "title": "Binary Search",
                            "source_type": "academic",
                            "publisher": "Educational Source",
                            "evidence_summary": "Binary search works by repeatedly dividing a sorted search interval in half.",
                            "relevance_score": 0.90
                        }
                    ],
                    "retrieval_status": "success"
                }
            ]
        },
        "freshness_payload": {
            "freshness_results": [
                {
                    "claim_id": "C1",
                    "claim_freshness_score": 0.70,
                    "claim_reliability_score": 0.90,
                    "claim_temporal_risk": "low",
                    "best_evidence_id": "E1"
                }
            ]
        },
        "expected_status": "SUPPORTED"
    }
]
```

Note for Python tests:

Use `None`, not JSON `null`.

---

## Prompt for Claude or Codex Agent

You are implementing Skill 05 for a project called TemporalGuard.

TemporalGuard is a time-aware reliability framework for detecting and correcting outdated responses in Large Language Models.

Your task is to implement only the temporal verification skill.

Create a clean, production-quality Python module that verifies extracted claims against retrieved evidence and freshness scores.

Create:

1. `src/temporalguard/skills/temporal_verifier.py`
2. `tests/test_temporal_verifier.py`

Use this function signature:

```python
def verify_temporal_claims(
    question: str,
    claims_payload: dict,
    evidence_payload: dict,
    freshness_payload: dict | None = None,
    temporal_category: str | None = None
) -> dict:
```

The function must return:

```python
{
    "verification_results": [
        {
            "claim_id": "C1",
            "claim_text": "...",
            "verification_status": "SUPPORTED | OUTDATED | CONTRADICTED | PARTIALLY_SUPPORTED | INSUFFICIENT_EVIDENCE | NOT_VERIFIABLE",
            "temporal_validity": "current | historical | version_specific | expired | uncertain | not_applicable",
            "verification_confidence": 0.0,
            "evidence_used": ["E1"],
            "best_evidence_id": "E1",
            "reason": "short reason",
            "detected_conflict": None,
            "claim_value": None,
            "evidence_value": None,
            "requires_correction": True,
            "risk_level": "low | medium | high | critical | unknown",
            "notes": "short note"
        }
    ],
    "overall_verification_status": "SUPPORTED | NEEDS_CORRECTION | INSUFFICIENT_EVIDENCE | MIXED | NOT_VERIFIABLE",
    "overall_confidence": 0.0,
    "verification_warnings": []
}
```

Implementation requirements:

* Use Python standard library only.
* Do not call an LLM by default.
* Do not call web search.
* Do not browse URLs.
* Do not retrieve new evidence.
* Do not correct claims.
* Do not generate final user answers.
* Match claims and evidence by `claim_id`.
* Use best evidence from freshness payload when available.
* Use evidence summary, quote, title, and publisher as the comparison text.
* Extract important values from claim and evidence using deterministic rules:

  * versions
  * years
  * dates
  * percentages
  * currency amounts
  * status words
  * key named entities
* Detect old-vs-new version conflicts for latest/current claims.
* Detect historical date alignment.
* Detect status conflicts such as active vs inactive, supported vs unsupported, deprecated vs not deprecated.
* Treat stale or low-reliability evidence as insufficient unless it clearly contradicts the claim.
* Return `INSUFFICIENT_EVIDENCE` when no evidence is available.
* Return `OUTDATED` when a current/latest/status claim appears replaced by newer evidence.
* Return `CONTRADICTED` when evidence directly disagrees for the requested time/context.
* Return `SUPPORTED` only when evidence clearly supports the claim.
* Return `PARTIALLY_SUPPORTED` when evidence supports part but not all of the claim.
* Return `NOT_VERIFIABLE` for subjective or vague claims.
* Keep logic conservative and explainable.
* Keep code typed, clean, and easy to extend.
* Add unit tests for all provided examples.
* Use the package name `temporalguard`.

Recommended internal helper functions:

```python
_get_claims_by_id(claims_payload: dict) -> dict
_get_evidence_by_claim_id(evidence_payload: dict) -> dict
_get_freshness_by_claim_id(freshness_payload: dict | None) -> dict
_select_best_evidence(evidence_result: dict, freshness_result: dict | None) -> dict | None
_build_evidence_text(evidence_item: dict) -> str
_extract_versions(text: str) -> list[str]
_extract_years(text: str) -> list[str]
_extract_numbers(text: str) -> list[str]
_extract_status_words(text: str) -> list[str]
_extract_candidate_entities(text: str) -> list[str]
_compare_claim_and_evidence_values(claim: dict, evidence_text: str, temporal_category: str | None) -> dict
_infer_verification_status(claim: dict, evidence_item: dict | None, freshness_result: dict | None, comparison: dict, temporal_category: str | None) -> str
_infer_temporal_validity(status: str, claim: dict, temporal_category: str | None) -> str
_infer_requires_correction(status: str, risk_level: str) -> bool
_infer_overall_status(results: list[dict]) -> str
```

Important behavior:

* If evidence reliability score is below `0.45`, treat it as weak.
* If the claim is `RECENT_ONLY` or `TIME_SENSITIVE` and freshness score is below `0.40`, do not mark it as supported.
* If the evidence has a better/current version than the claim, mark `OUTDATED`.
* If the claim asks about a historical year and evidence supports a range containing that year, mark `SUPPORTED`.
* If clear values conflict and the claim is not simply outdated, mark `CONTRADICTED`.
* If there is no clear value but evidence text overlaps strongly with the claim, mark `SUPPORTED` only if reliability is good.
* Overall status:

  * all supported → `SUPPORTED`
  * any outdated/contradicted/partial → `NEEDS_CORRECTION`
  * all insufficient → `INSUFFICIENT_EVIDENCE`
  * mixed supported and insufficient → `MIXED`
  * all not verifiable → `NOT_VERIFIABLE`

After implementation:

1. Run tests.
2. Fix all failing tests.
3. Report:

   * files created
   * main logic summary
   * test result
   * assumptions
