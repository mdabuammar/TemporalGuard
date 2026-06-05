# Skill 07: Correction Generation

## Purpose

This skill generates a corrected, time-aware answer when TemporalGuard detects that the original LLM answer is outdated, contradicted, partially outdated, or too risky to trust without clearer evidence.

TemporalGuard should not only say:

“The answer is outdated.”

It should also provide a safer corrected answer using the best available evidence.

This skill is the seventh step in the TemporalGuard pipeline.

It receives:

1. Original user question
2. Original LLM answer
3. Temporal category from Skill 01
4. Extracted claims from Skill 02
5. Retrieved evidence from Skill 03
6. Freshness scores from Skill 04
7. Verification results from Skill 05
8. Outdated answer detection result from Skill 06

It returns a corrected answer, evidence notes, uncertainty warnings, and correction metadata.

---

## Core Task

Given the original answer and verification results, generate a corrected answer that is:

1. faithful to the evidence
2. time-aware
3. clear and concise
4. honest about uncertainty
5. safe for high-risk domains
6. suitable for final user display

This skill must correct outdated or contradicted information without inventing facts.

---

## Important Boundary

This skill does not:

* retrieve new evidence
* verify claims from scratch
* score source freshness
* fabricate facts
* hide uncertainty
* overclaim unsupported information
* produce long unnecessary explanations
* use too much context
* call an LLM by default unless the project explicitly enables it

This skill only generates the corrected response from already available structured inputs.

---

## Inputs

The skill may receive input like this:

```json
{
  "question": "What is the latest Python version?",
  "answer": "Python 3.10 is the latest stable version of Python.",
  "temporal_category": "RECENT_ONLY",
  "claims_payload": {
    "claims": [
      {
        "claim_id": "C1",
        "claim_text": "Python 3.10 is the latest stable version of Python.",
        "claim_type": "software_version",
        "entities": ["Python", "Python 3.10"],
        "temporal_sensitivity": "high",
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
            "url": "https://www.python.org/downloads/",
            "source_type": "official",
            "publisher": "Python Software Foundation",
            "updated_date": "2026-06-01",
            "retrieved_at": "2026-06-05T12:00:00Z",
            "evidence_summary": "The official Python downloads page lists Python 3.13.5 as the latest release."
          }
        ]
      }
    ]
  },
  "verification_payload": {
    "verification_results": [
      {
        "claim_id": "C1",
        "verification_status": "OUTDATED",
        "claim_value": "Python 3.10",
        "evidence_value": "Python 3.13.5",
        "reason": "The claim says Python 3.10 is latest, but official evidence lists Python 3.13.5 as latest.",
        "requires_correction": true,
        "risk_level": "high"
      }
    ]
  },
  "outdatedness_payload": {
    "outdatedness_status": "OUTDATED",
    "is_outdated": true,
    "requires_correction": true,
    "answer_temporal_risk": "high",
    "recommended_next_action": "generate_correction"
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
  "corrected_answer": "string",
  "correction_status": "corrected | partially_corrected | unable_to_correct | no_correction_needed",
  "correction_type": "update_outdated_fact | fix_contradiction | add_uncertainty | partial_revision | no_change",
  "changed_claim_ids": ["C1"],
  "unchanged_claim_ids": [],
  "unsupported_claim_ids": [],
  "evidence_used": [
    {
      "claim_id": "C1",
      "evidence_id": "E1",
      "title": "string",
      "url": "string",
      "publisher": "string",
      "date_used": "YYYY-MM-DD or null",
      "source_type": "string"
    }
  ],
  "freshness_note": "string",
  "uncertainty_note": "string or null",
  "safety_note": "string or null",
  "answer_temporal_risk": "low | medium | high | critical | unknown",
  "confidence": 0.0,
  "user_visible_explanation": "short explanation",
  "warnings": ["string"]
}
```

---

## Correction Status Definitions

### 1. corrected

Use `corrected` when the system can confidently replace the wrong or outdated claim with evidence-backed information.

Example:

Original:

```text
Python 3.10 is the latest stable version.
```

Evidence:

```text
Python 3.13.5 is the latest release.
```

Corrected:

```text
Python 3.10 is not the latest stable version. Based on the official Python source checked, Python 3.13.5 is listed as the latest release.
```

---

### 2. partially_corrected

Use `partially_corrected` when some parts can be corrected, but some parts remain uncertain.

Example:

Original answer has three claims:

* one outdated
* one supported
* one insufficient evidence

The corrected answer should fix the outdated part and clearly mark the uncertain part.

---

### 3. unable_to_correct

Use `unable_to_correct` when the evidence is insufficient, weak, missing, or conflicting.

Do not invent a corrected fact.

Example:

```text
I could not safely correct this answer because reliable evidence was not available.
```

---

### 4. no_correction_needed

Use `no_correction_needed` when Skill 06 says the answer is not outdated and does not require correction.

---

## Correction Type Definitions

Use one of:

```text
update_outdated_fact
fix_contradiction
add_uncertainty
partial_revision
no_change
```

### update_outdated_fact

Use when an old claim is replaced with a current evidence-backed claim.

### fix_contradiction

Use when the original answer is directly contradicted by evidence.

### add_uncertainty

Use when the original answer cannot be verified safely.

### partial_revision

Use when the answer has mixed results.

### no_change

Use when the original answer is safe.

---

## Field Instructions

### corrected_answer

This is the final corrected answer text.

It must be:

* concise
* evidence-grounded
* time-aware
* not overconfident
* safe for high-risk topics

Good:

```text
Python 3.10 is not the latest stable Python version. Based on the official Python source checked on 2026-06-05, Python 3.13.5 is listed as the latest release.
```

Bad:

```text
Python 3.13.5 is definitely the latest forever.
```

---

### changed_claim_ids

List claims that were corrected.

Example:

```json
["C1"]
```

---

### unchanged_claim_ids

List claims that were supported and kept.

Example:

```json
["C2"]
```

---

### unsupported_claim_ids

List claims that could not be corrected because evidence was insufficient.

Example:

```json
["C3"]
```

---

### evidence_used

Include only the most important evidence used.

Do not include too many sources.

Default maximum:

```text
3 evidence items
```

Each evidence item should include:

* claim_id
* evidence_id
* title
* url
* publisher
* date_used
* source_type

---

### freshness_note

Mention the evidence timing.

Examples:

```text
Evidence was retrieved from an official source checked on 2026-06-05.
```

```text
The source had no clear update date, so the correction should be treated with caution.
```

```text
The answer concerns a historical fact, so the evidence was checked against the requested year.
```

---

### uncertainty_note

Use `null` if no uncertainty exists.

Use a clear note if:

* evidence is missing
* evidence is weak
* sources conflict
* date is unknown
* claim is high-risk
* correction is partial

Example:

```text
Reliable evidence was not strong enough to fully verify this claim.
```

---

### safety_note

Use for high-risk domains.

High-risk domains include:

```text
medical
legal
visa
immigration
finance
tax
safety
security
policy
regulation
clinical guideline
drug safety
Amazon policy
university admission
```

Example:

```text
Because this is a visa/policy-related question, the final decision should be checked against the official government source before action.
```

Use `null` if not needed.

---

### answer_temporal_risk

Use the risk from Skill 06 unless the correction reduces risk.

Suggested rule:

* corrected with strong evidence → reduce risk by one level if appropriate
* unable to correct → keep high or critical risk
* no correction needed → low risk

Do not reduce `critical` to `low` directly.

---

### confidence

Confidence in the corrected answer.

Suggested values:

```text
0.90–1.00 = strong evidence and clear correction
0.75–0.89 = good evidence but some uncertainty
0.60–0.74 = partial correction
0.40–0.59 = weak correction
0.00–0.39 = unable to correct safely
```

---

### user_visible_explanation

A short explanation that can be shown in the dashboard.

Good:

```text
The original answer was outdated because the claimed latest version differed from the official source.
```

Bad:

```text
Changed because wrong.
```

---

## Correction Rules

### Rule 1: Never invent a corrected fact

Only use corrected values that appear in the evidence or verification result.

Good:

* claim_value: Python 3.10
* evidence_value: Python 3.13.5
* corrected answer may say Python 3.13.5

Bad:

* evidence only says “newer version exists”
* corrected answer invents “Python 3.14.0”

---

### Rule 2: Prefer evidence_value from Skill 05

If `evidence_value` exists in verification result, use it as the main corrected value.

If `evidence_value` is missing, use evidence summary carefully.

If neither exists, do not correct the fact directly.

---

### Rule 3: For outdated claims, replace old value with evidence value

Example:

Claim:

```text
Python 3.10 is the latest stable version.
```

Evidence value:

```text
Python 3.13.5
```

Corrected answer:

```text
Python 3.10 is not the latest stable version. Based on the checked evidence, Python 3.13.5 is listed as the latest release.
```

---

### Rule 4: For contradicted claims, state the contradiction clearly

Example:

Claim:

```text
France won the 2014 FIFA World Cup.
```

Evidence value:

```text
Germany
```

Corrected answer:

```text
France did not win the 2014 FIFA World Cup. The evidence indicates that Germany won the 2014 FIFA World Cup.
```

---

### Rule 5: For partially supported answers, keep supported parts and fix only bad parts

Do not rewrite everything unnecessarily.

Example:

Original:

```text
Python 3.10 is the latest version. Python is widely used in data science.
```

Corrected:

```text
The version part needs correction: Python 3.10 is not the latest version according to the checked evidence; Python 3.13.5 is listed as the latest release. The general statement that Python is widely used in data science can remain.
```

---

### Rule 6: For insufficient evidence, add uncertainty instead of correction

Example:

```text
I could not verify this claim with reliable evidence. Because the question is time-sensitive, this answer should not be treated as confirmed.
```

For high-risk domains, add a safety note.

---

### Rule 7: For historical claims, keep the historical time anchor

Example:

Question:

```text
Who was the U.S. president in 2016?
```

Wrong answer:

```text
Donald Trump was the U.S. president in 2016.
```

Evidence:

```text
Barack Obama served from 2009 to 2017.
```

Corrected answer:

```text
Donald Trump was not the U.S. president in 2016. Based on the checked evidence, Barack Obama was president during 2016.
```

---

### Rule 8: For version-specific claims, preserve version context

Example:

Claim:

```text
In pandas 2.0, method X is deprecated.
```

Correction should not talk about pandas 1.5 or pandas 3.0 unless evidence supports that context.

---

### Rule 9: Include evidence timing

For current claims, mention:

```text
Based on the source checked on [date]
```

For historical claims, mention:

```text
For the requested time period
```

For undated sources, mention caution.

---

### Rule 10: Keep answer short unless explanation is needed

The corrected answer should usually be 1–4 sentences.

Do not create a long report.

---

## Evidence Selection Rules

Use evidence in this order:

1. Evidence used in verification result
2. Best evidence ID from freshness result
3. Highest relevance evidence from evidence payload
4. First reliable evidence item

Do not include more than 3 evidence items.

---

## High-Risk Safety Rules

For high-risk topics, do not make strong recommendations without strong evidence.

High-risk examples:

* medical guideline
* medicine safety
* visa rule
* law
* tax
* finance
* policy
* regulation
* cybersecurity vulnerability
* safety instruction

If evidence is strong:

```text
Based on the official source checked, ...
```

If evidence is weak:

```text
I could not safely confirm this. Please check the official source before taking action.
```

Do not provide medical, legal, or financial advice as final authority.

---

## Output Examples

### Example 1: Outdated Software Version

Input:

```json
{
  "question": "What is the latest Python version?",
  "answer": "Python 3.10 is the latest stable version of Python.",
  "verification_payload": {
    "verification_results": [
      {
        "claim_id": "C1",
        "verification_status": "OUTDATED",
        "claim_value": "Python 3.10",
        "evidence_value": "Python 3.13.5",
        "risk_level": "high"
      }
    ]
  }
}
```

Output:

```json
{
  "corrected_answer": "Python 3.10 is not the latest stable Python version. Based on the checked official evidence, Python 3.13.5 is listed as the latest release.",
  "correction_status": "corrected",
  "correction_type": "update_outdated_fact",
  "changed_claim_ids": ["C1"],
  "unchanged_claim_ids": [],
  "unsupported_claim_ids": [],
  "freshness_note": "The correction uses checked evidence for a current software-version claim.",
  "uncertainty_note": null,
  "safety_note": null,
  "answer_temporal_risk": "medium",
  "confidence": 0.92,
  "user_visible_explanation": "The original answer was outdated because the claimed latest version differed from the checked evidence.",
  "warnings": []
}
```

---

### Example 2: Contradicted Event Result

Input:

```json
{
  "question": "Who won the 2014 FIFA World Cup?",
  "answer": "France won the 2014 FIFA World Cup.",
  "verification_payload": {
    "verification_results": [
      {
        "claim_id": "C1",
        "verification_status": "CONTRADICTED",
        "claim_value": "France",
        "evidence_value": "Germany",
        "risk_level": "high"
      }
    ]
  }
}
```

Output:

```json
{
  "corrected_answer": "France did not win the 2014 FIFA World Cup. Based on the checked evidence, Germany won the 2014 FIFA World Cup.",
  "correction_status": "corrected",
  "correction_type": "fix_contradiction",
  "changed_claim_ids": ["C1"],
  "unchanged_claim_ids": [],
  "unsupported_claim_ids": [],
  "freshness_note": "The correction uses evidence for the requested historical event.",
  "uncertainty_note": null,
  "safety_note": null,
  "answer_temporal_risk": "medium",
  "confidence": 0.92,
  "user_visible_explanation": "The original answer was contradicted by the checked evidence.",
  "warnings": []
}
```

---

### Example 3: Unverified Risky Visa Claim

Input:

```json
{
  "question": "Is this visa rule still active?",
  "answer": "Yes, this visa rule is still active.",
  "outdatedness_payload": {
    "outdatedness_status": "UNVERIFIED_RISKY",
    "answer_temporal_risk": "critical"
  },
  "verification_payload": {
    "verification_results": [
      {
        "claim_id": "C1",
        "verification_status": "INSUFFICIENT_EVIDENCE",
        "risk_level": "critical"
      }
    ]
  }
}
```

Output:

```json
{
  "corrected_answer": "I could not safely verify whether this visa rule is still active from the available evidence. Because visa rules can change and may affect real decisions, this should be checked directly on the official immigration or government website before taking action.",
  "correction_status": "unable_to_correct",
  "correction_type": "add_uncertainty",
  "changed_claim_ids": [],
  "unchanged_claim_ids": [],
  "unsupported_claim_ids": ["C1"],
  "freshness_note": "Reliable fresh evidence was not available for this current policy claim.",
  "uncertainty_note": "The claim could not be verified safely.",
  "safety_note": "This is a visa or policy-related question, so official confirmation is required before action.",
  "answer_temporal_risk": "critical",
  "confidence": 0.35,
  "user_visible_explanation": "The original answer could not be verified with enough reliable evidence.",
  "warnings": ["insufficient_evidence_for_high_risk_claim"]
}
```

---

### Example 4: No Correction Needed

Input:

```json
{
  "question": "What is binary search?",
  "answer": "Binary search divides a sorted search space in half.",
  "outdatedness_payload": {
    "outdatedness_status": "NOT_OUTDATED",
    "requires_correction": false
  }
}
```

Output:

```json
{
  "corrected_answer": "Binary search divides a sorted search space in half.",
  "correction_status": "no_correction_needed",
  "correction_type": "no_change",
  "changed_claim_ids": [],
  "unchanged_claim_ids": ["C1"],
  "unsupported_claim_ids": [],
  "freshness_note": "No temporal correction was needed for this stable concept.",
  "uncertainty_note": null,
  "safety_note": null,
  "answer_temporal_risk": "low",
  "confidence": 0.88,
  "user_visible_explanation": "The answer did not appear outdated based on the verification result.",
  "warnings": []
}
```

---

## Implementation Notes for AI Coding Agents

Build this skill as a controlled correction module.

Do not call web search.

Do not retrieve evidence.

Do not verify claims from scratch.

Do not invent corrected facts.

Do not call an LLM by default.

Start with deterministic template-based correction.

Optional LLM rewrite can be added later as a disabled extension point.

Recommended implementation:

* Create a Python module such as `correction_generator.py`
* Create a function named `generate_correction(...) -> dict`
* Use verification statuses and evidence values
* Use evidence summaries only when evidence_value is missing
* Keep corrected answer short
* Return strict JSON-compatible dictionary
* Include unit tests
* Keep logic easy to understand and thesis-explainable

---

## Suggested Python Interface

Use this interface:

```python
def generate_correction(
    question: str,
    answer: str,
    verification_payload: dict,
    outdatedness_payload: dict,
    claims_payload: dict | None = None,
    evidence_payload: dict | None = None,
    freshness_payload: dict | None = None,
    temporal_category: str | None = None
) -> dict:
    """
    Generate an evidence-grounded corrected answer.

    Args:
        question: Original user question.
        answer: Original LLM-generated answer.
        verification_payload: Output from Skill 05.
        outdatedness_payload: Output from Skill 06.
        claims_payload: Optional output from Skill 02.
        evidence_payload: Optional output from Skill 03.
        freshness_payload: Optional output from Skill 04.
        temporal_category: Optional category from Skill 01.

    Returns:
        JSON-compatible dict with corrected answer and correction metadata.
    """
```

---

## Expected Behavior

The generator should be careful, short, and evidence-grounded.

It must not waste tokens.

It must not call an LLM.

It must not perform web search.

It must not invent facts.

It only generates a corrected answer from verified evidence.

---

## Quality Requirements

The implementation must satisfy these requirements:

1. Return valid JSON-compatible dictionary every time.
2. Use verification payload as main truth input.
3. Use outdatedness payload to decide whether correction is needed.
4. Use evidence value when available.
5. Never invent replacement values.
6. Produce uncertainty wording when evidence is insufficient.
7. Add safety notes for high-risk domains.
8. Keep corrected answer concise.
9. Preserve historical and version-specific context.
10. Keep supported claims when partial correction is needed.
11. Include evidence metadata.
12. Handle missing evidence safely.
13. Avoid LLM calls by default.
14. Include unit tests.
15. Keep logic explainable for thesis writing.
16. Use the package name `temporalguard`.

---

## Test Cases

Use these minimum test cases:

```python
test_cases = [
    {
        "name": "correct outdated Python version",
        "question": "What is the latest Python version?",
        "answer": "Python 3.10 is the latest stable version of Python.",
        "temporal_category": "RECENT_ONLY",
        "verification_payload": {
            "verification_results": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python 3.10 is the latest stable version of Python.",
                    "verification_status": "OUTDATED",
                    "claim_value": "Python 3.10",
                    "evidence_value": "Python 3.13.5",
                    "risk_level": "high",
                    "verification_confidence": 0.94,
                    "requires_correction": True
                }
            ]
        },
        "outdatedness_payload": {
            "outdatedness_status": "OUTDATED",
            "requires_correction": True,
            "answer_temporal_risk": "high"
        },
        "expected_correction_status": "corrected",
        "expected_correction_type": "update_outdated_fact"
    },
    {
        "name": "correct contradicted world cup winner",
        "question": "Who won the 2014 FIFA World Cup?",
        "answer": "France won the 2014 FIFA World Cup.",
        "temporal_category": "HISTORICAL",
        "verification_payload": {
            "verification_results": [
                {
                    "claim_id": "C1",
                    "claim_text": "France won the 2014 FIFA World Cup.",
                    "verification_status": "CONTRADICTED",
                    "claim_value": "France",
                    "evidence_value": "Germany",
                    "risk_level": "high",
                    "verification_confidence": 0.93,
                    "requires_correction": True
                }
            ]
        },
        "outdatedness_payload": {
            "outdatedness_status": "CONTRADICTED",
            "requires_correction": True,
            "answer_temporal_risk": "high"
        },
        "expected_correction_status": "corrected",
        "expected_correction_type": "fix_contradiction"
    },
    {
        "name": "unable to correct high risk visa claim",
        "question": "Is this visa rule still active?",
        "answer": "Yes, this visa rule is still active.",
        "temporal_category": "RECENT_ONLY",
        "verification_payload": {
            "verification_results": [
                {
                    "claim_id": "C1",
                    "claim_text": "This visa rule is still active.",
                    "verification_status": "INSUFFICIENT_EVIDENCE",
                    "risk_level": "critical",
                    "verification_confidence": 0.75,
                    "requires_correction": True
                }
            ]
        },
        "outdatedness_payload": {
            "outdatedness_status": "UNVERIFIED_RISKY",
            "requires_correction": True,
            "answer_temporal_risk": "critical"
        },
        "expected_correction_status": "unable_to_correct",
        "expected_correction_type": "add_uncertainty"
    },
    {
        "name": "no correction needed static answer",
        "question": "What is binary search?",
        "answer": "Binary search divides a sorted search space in half.",
        "temporal_category": "STATIC",
        "verification_payload": {
            "verification_results": [
                {
                    "claim_id": "C1",
                    "claim_text": "Binary search divides a sorted search space in half.",
                    "verification_status": "SUPPORTED",
                    "risk_level": "low",
                    "verification_confidence": 0.88,
                    "requires_correction": False
                }
            ]
        },
        "outdatedness_payload": {
            "outdatedness_status": "NOT_OUTDATED",
            "requires_correction": False,
            "answer_temporal_risk": "low"
        },
        "expected_correction_status": "no_correction_needed",
        "expected_correction_type": "no_change"
    },
    {
        "name": "partially corrected mixed answer",
        "question": "What is the latest Python version and why is Python useful?",
        "answer": "Python 3.10 is the latest version. Python is widely used in data science.",
        "temporal_category": "RECENT_ONLY",
        "verification_payload": {
            "verification_results": [
                {
                    "claim_id": "C1",
                    "claim_text": "Python 3.10 is the latest version.",
                    "verification_status": "OUTDATED",
                    "claim_value": "Python 3.10",
                    "evidence_value": "Python 3.13.5",
                    "risk_level": "high",
                    "verification_confidence": 0.92,
                    "requires_correction": True
                },
                {
                    "claim_id": "C2",
                    "claim_text": "Python is widely used in data science.",
                    "verification_status": "SUPPORTED",
                    "risk_level": "low",
                    "verification_confidence": 0.86,
                    "requires_correction": False
                }
            ]
        },
        "outdatedness_payload": {
            "outdatedness_status": "PARTIALLY_OUTDATED",
            "requires_correction": True,
            "answer_temporal_risk": "high"
        },
        "expected_correction_status": "partially_corrected",
        "expected_correction_type": "partial_revision"
    }
]
```

---

## Prompt for Claude or Codex Agent

You are implementing Skill 07 for a project called TemporalGuard.

TemporalGuard is a time-aware reliability framework for detecting and correcting outdated responses in Large Language Models.

Your task is to implement only the correction generation skill.

Create a clean, production-quality Python module that generates a concise, evidence-grounded corrected answer from verification and outdatedness results.

Create:

1. `src/temporalguard/skills/correction_generator.py`
2. `tests/test_correction_generator.py`

Use this function signature:

```python
def generate_correction(
    question: str,
    answer: str,
    verification_payload: dict,
    outdatedness_payload: dict,
    claims_payload: dict | None = None,
    evidence_payload: dict | None = None,
    freshness_payload: dict | None = None,
    temporal_category: str | None = None
) -> dict:
```

The function must return:

```python
{
    "corrected_answer": "...",
    "correction_status": "corrected | partially_corrected | unable_to_correct | no_correction_needed",
    "correction_type": "update_outdated_fact | fix_contradiction | add_uncertainty | partial_revision | no_change",
    "changed_claim_ids": ["C1"],
    "unchanged_claim_ids": [],
    "unsupported_claim_ids": [],
    "evidence_used": [],
    "freshness_note": "...",
    "uncertainty_note": None,
    "safety_note": None,
    "answer_temporal_risk": "low | medium | high | critical | unknown",
    "confidence": 0.0,
    "user_visible_explanation": "short explanation",
    "warnings": []
}
```

Implementation requirements:

* Use Python standard library only.
* Do not call an LLM by default.
* Do not call web search.
* Do not retrieve new evidence.
* Do not verify claims from scratch.
* Do not invent corrected facts.
* Use `verification_payload` as the main truth input.
* Use `outdatedness_payload` to decide correction status.
* Use `evidence_value` from verification results when available.
* Use evidence summaries only if `evidence_value` is missing and the summary clearly contains the replacement value.
* Generate short, clear corrected answers.
* Add uncertainty wording for insufficient evidence.
* Add safety notes for high-risk domains.
* Preserve historical context for historical questions.
* Preserve software/API version context for version-dependent questions.
* Include evidence metadata from evidence payload or freshness payload where possible.
* Keep supported claims in partial corrections.
* Return `no_correction_needed` if outdatedness says no correction is required.
* Return `unable_to_correct` if evidence is insufficient and no safe replacement value is available.
* Clamp and round confidence to 3 decimals.
* Add unit tests for all provided examples.
* Keep code typed, deterministic, clean, and easy to extend.
* Use the package name `temporalguard`.

Recommended internal helper functions:

```python
_get_verification_results(verification_payload: dict) -> list[dict]
_get_outdatedness_status(outdatedness_payload: dict) -> str
_get_claims_by_id(claims_payload: dict | None) -> dict
_collect_evidence_metadata(evidence_payload: dict | None, freshness_payload: dict | None, claim_ids: list[str]) -> list[dict]
_detect_high_risk_domain(question: str, answer: str, verification_results: list[dict]) -> bool
_generate_outdated_update(ver_result: dict, question: str, temporal_category: str | None) -> str
_generate_contradiction_fix(ver_result: dict, question: str, temporal_category: str | None) -> str
_generate_insufficient_evidence_response(question: str, high_risk: bool) -> str
_generate_partial_revision(results: list[dict], question: str, temporal_category: str | None) -> str
_build_freshness_note(evidence_used: list[dict], temporal_category: str | None, status: str) -> str
_build_safety_note(high_risk: bool, status: str) -> str | None
_calculate_correction_confidence(results: list[dict], correction_status: str) -> float
_reduce_risk_after_correction(original_risk: str, correction_status: str, high_risk: bool) -> str
```

Important behavior:

* If correction status is `corrected`, `corrected_answer` must include the evidence-backed replacement value.
* If `evidence_value` is missing for an outdated/contradicted claim, do not invent the replacement. Return `unable_to_correct` or add uncertainty.
* If there are both corrected and unsupported claims, return `partially_corrected`.
* If the original answer is safe, return it unchanged.
* If high-risk and insufficient evidence, warn clearly and keep risk `critical`.
* Do not include raw JSON in the corrected answer.
* Do not include long citations in the corrected answer; evidence metadata is returned separately.
* Keep the answer suitable for a Streamlit dashboard.

After implementation:

1. Run tests.
2. Fix all failing tests.
3. Report:

   * files created
   * main logic summary
   * test result
   * assumptions
