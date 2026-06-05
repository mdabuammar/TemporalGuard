# Skill 06: Outdated Answer Detection

## Purpose

This skill decides whether the original LLM answer is outdated, partially outdated, risky, or safe based on the claim-level verification results from Skill 05.

TemporalGuard should not only verify individual claims. It must also judge the whole answer.

An answer can contain many claims. Some may be correct, some may be outdated, and some may have insufficient evidence. This skill summarizes the answer-level temporal risk.

This skill is the sixth step in the TemporalGuard pipeline.

It receives:

1. Original user question
2. Original LLM answer
3. Temporal category from Skill 01
4. Extracted claims from Skill 02
5. Temporal verification results from Skill 05
6. Optional freshness scores from Skill 04

It returns a structured decision about whether the full answer is outdated and whether correction is needed.

---

## Core Task

Given the verification results for extracted claims, classify the full answer into one answer-level outdatedness status:

1. `NOT_OUTDATED`
2. `OUTDATED`
3. `PARTIALLY_OUTDATED`
4. `CONTRADICTED`
5. `UNVERIFIED_RISKY`
6. `NOT_ENOUGH_INFORMATION`
7. `NOT_APPLICABLE`

This skill must decide:

* Is the answer outdated?
* Is only part of the answer outdated?
* Is the answer contradicted by evidence?
* Is the answer too risky to trust because evidence is missing?
* Does the answer need correction?
* What is the answer-level temporal risk?

---

## Important Boundary

This skill does not:

* retrieve evidence
* score source freshness
* verify individual claims from scratch
* correct the answer
* generate the final revised response
* call web search
* call an LLM by default
* invent facts
* change the original answer

Correction happens later in Skill 07: Correction Generation.

This skill only detects outdatedness at the answer level.

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
        "temporal_sensitivity": "high",
        "evidence_need": "fresh"
      }
    ]
  },
  "verification_payload": {
    "verification_results": [
      {
        "claim_id": "C1",
        "claim_text": "Python 3.10 is the latest stable version of Python.",
        "verification_status": "OUTDATED",
        "temporal_validity": "expired",
        "verification_confidence": 0.94,
        "reason": "The claim says Python 3.10 is latest, but official evidence lists Python 3.13.5 as latest.",
        "detected_conflict": "Claim value: Python 3.10; Evidence value: Python 3.13.5.",
        "claim_value": "Python 3.10",
        "evidence_value": "Python 3.13.5",
        "requires_correction": true,
        "risk_level": "high"
      }
    ],
    "overall_verification_status": "NEEDS_CORRECTION",
    "overall_confidence": 0.94
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
  "outdatedness_status": "NOT_OUTDATED | OUTDATED | PARTIALLY_OUTDATED | CONTRADICTED | UNVERIFIED_RISKY | NOT_ENOUGH_INFORMATION | NOT_APPLICABLE",
  "is_outdated": true,
  "requires_correction": true,
  "answer_temporal_risk": "low | medium | high | critical | unknown",
  "outdated_claim_ids": ["C1"],
  "contradicted_claim_ids": [],
  "unsupported_claim_ids": [],
  "supported_claim_ids": [],
  "critical_claim_ids": [],
  "main_issue": "short issue summary",
  "decision_reason": "short reason",
  "confidence": 0.0,
  "recommended_next_action": "no_action | generate_correction | request_more_evidence | ask_clarifying_question",
  "answer_level_summary": {
    "total_claims": 0,
    "supported_count": 0,
    "outdated_count": 0,
    "contradicted_count": 0,
    "partially_supported_count": 0,
    "insufficient_evidence_count": 0,
    "not_verifiable_count": 0
  },
  "warnings": ["string"]
}
```

---

## Outdatedness Status Definitions

### 1. NOT_OUTDATED

Use `NOT_OUTDATED` when the answer is supported by evidence and does not appear temporally stale.

Example:

Question:

```text
Who was the president of the USA in 2016?
```

Answer:

```text
Barack Obama was the president of the United States in 2016.
```

Verification:

```text
SUPPORTED
```

Answer status:

```text
NOT_OUTDATED
```

---

### 2. OUTDATED

Use `OUTDATED` when the main answer is outdated.

Example:

Question:

```text
What is the latest Python version?
```

Answer:

```text
Python 3.10 is the latest stable version.
```

Evidence:

```text
Python 3.13.5 is latest.
```

Answer status:

```text
OUTDATED
```

Use this when most important claims are `OUTDATED`.

---

### 3. PARTIALLY_OUTDATED

Use `PARTIALLY_OUTDATED` when some important claims are outdated, but the full answer is not completely wrong.

Example:

Answer:

```text
Python 3.10 is the latest version. Python is widely used for web development and machine learning.
```

Verification:

* Latest version claim: `OUTDATED`
* Python usage claim: `SUPPORTED`

Answer status:

```text
PARTIALLY_OUTDATED
```

---

### 4. CONTRADICTED

Use `CONTRADICTED` when the main claim is directly contradicted by reliable evidence.

Example:

Question:

```text
Who won the 2014 FIFA World Cup?
```

Answer:

```text
France won the 2014 FIFA World Cup.
```

Evidence:

```text
Germany won the 2014 FIFA World Cup.
```

Answer status:

```text
CONTRADICTED
```

---

### 5. UNVERIFIED_RISKY

Use `UNVERIFIED_RISKY` when the answer cannot be trusted because it lacks sufficient reliable evidence, especially for high-risk or current claims.

Example:

Question:

```text
Is this visa rule still active?
```

Answer:

```text
Yes, it is still active.
```

Verification:

```text
INSUFFICIENT_EVIDENCE
```

Answer status:

```text
UNVERIFIED_RISKY
```

Use this for:

* legal claims
* visa claims
* medical claims
* finance claims
* safety claims
* current policy claims
* high-risk claims with missing evidence

---

### 6. NOT_ENOUGH_INFORMATION

Use `NOT_ENOUGH_INFORMATION` when the system cannot make an outdatedness decision because the answer has no clear claims or evidence is missing.

Example:

Answer:

```text
It depends.
```

No factual claims extracted.

Answer status:

```text
NOT_ENOUGH_INFORMATION
```

---

### 7. NOT_APPLICABLE

Use `NOT_APPLICABLE` when outdatedness is not relevant.

Examples:

* subjective answers
* creative writing
* personal advice without factual claims
* simple greetings
* stable conceptual explanations where verification is optional

Example:

Question:

```text
Write a short poem about rain.
```

Answer status:

```text
NOT_APPLICABLE
```

---

## Field Instructions

### is_outdated

Use `true` for:

* `OUTDATED`
* `PARTIALLY_OUTDATED`

Usually use `true` for `CONTRADICTED` if the contradiction is caused by stale or replaced information.

Use `false` for:

* `NOT_OUTDATED`
* `UNVERIFIED_RISKY`
* `NOT_ENOUGH_INFORMATION`
* `NOT_APPLICABLE`

Important:

`UNVERIFIED_RISKY` means “not safe to trust,” but not necessarily outdated.

---

### requires_correction

Use `true` for:

* `OUTDATED`
* `PARTIALLY_OUTDATED`
* `CONTRADICTED`
* high-risk `UNVERIFIED_RISKY`

Use `false` for:

* `NOT_OUTDATED`
* `NOT_APPLICABLE`

Use `true` for `NOT_ENOUGH_INFORMATION` only if the question requires factual answering.

---

### answer_temporal_risk

Use:

```text
low
medium
high
critical
unknown
```

Use `critical` when:

* legal, medical, visa, finance, safety, or regulatory answer is contradicted, outdated, or unsupported
* the answer may cause real-world harm if followed

Use `high` when:

* the main claim is outdated or contradicted
* the question asks for current/latest information and evidence disagrees
* evidence is missing for an important time-sensitive claim

Use `medium` when:

* only secondary claims are uncertain or partially supported
* evidence exists but is not very strong

Use `low` when:

* all important claims are supported
* outdatedness is not relevant

Use `unknown` when:

* no decision can be made

---

### outdated_claim_ids

List claim IDs with verification status:

```text
OUTDATED
```

---

### contradicted_claim_ids

List claim IDs with verification status:

```text
CONTRADICTED
```

---

### unsupported_claim_ids

List claim IDs with verification status:

```text
INSUFFICIENT_EVIDENCE
```

---

### supported_claim_ids

List claim IDs with verification status:

```text
SUPPORTED
```

---

### critical_claim_ids

List claim IDs where risk level is:

```text
critical
```

---

### main_issue

Short summary of the biggest problem.

Examples:

```text
The answer uses an old software version as the latest version.
```

```text
The main claim is contradicted by official evidence.
```

```text
Current policy status could not be verified with reliable evidence.
```

---

### decision_reason

A concise explanation of the final outdatedness decision.

Good:

```text
The main high-sensitivity claim is marked OUTDATED, so the answer requires correction.
```

Bad:

```text
The answer is bad.
```

---

### confidence

This is confidence in the answer-level outdatedness decision.

Suggested calculation:

```text
confidence = average confidence of verification results that drive the decision
```

If verification confidence is missing, use:

```text
SUPPORTED = 0.85
OUTDATED = 0.90
CONTRADICTED = 0.90
PARTIALLY_SUPPORTED = 0.75
INSUFFICIENT_EVIDENCE = 0.70
NOT_VERIFIABLE = 0.60
```

---

### recommended_next_action

Use one of:

```text
no_action
generate_correction
request_more_evidence
ask_clarifying_question
```

Use `generate_correction` for:

* `OUTDATED`
* `PARTIALLY_OUTDATED`
* `CONTRADICTED`

Use `request_more_evidence` for:

* `UNVERIFIED_RISKY`
* `NOT_ENOUGH_INFORMATION` caused by missing evidence

Use `ask_clarifying_question` when the original question or answer is ambiguous.

Use `no_action` for:

* `NOT_OUTDATED`
* `NOT_APPLICABLE`

---

## Decision Rules

### Rule 1: Contradiction has highest priority

If any main claim is `CONTRADICTED`, and the claim is important to the answer, answer status should usually be:

```text
CONTRADICTED
```

If only a minor claim is contradicted, use:

```text
PARTIALLY_OUTDATED
```

or `UNVERIFIED_RISKY`, depending on context.

---

### Rule 2: Outdated main claim means outdated answer

If the main claim is `OUTDATED`, classify the answer as:

```text
OUTDATED
```

If there are multiple claims and only some are outdated, classify as:

```text
PARTIALLY_OUTDATED
```

---

### Rule 3: Insufficient evidence for high-risk claims means risky answer

If the answer involves legal, visa, medical, finance, safety, or active policy claims and evidence is insufficient, classify as:

```text
UNVERIFIED_RISKY
```

Do not call it outdated unless evidence actually shows it is old.

---

### Rule 4: All supported claims means not outdated

If all extracted factual claims are `SUPPORTED`, classify as:

```text
NOT_OUTDATED
```

---

### Rule 5: No extracted claims means not enough information or not applicable

If no claims were extracted:

* Use `NOT_APPLICABLE` for creative, subjective, greeting, or personal style outputs.
* Use `NOT_ENOUGH_INFORMATION` for factual questions where a claim should have been present.

---

### Rule 6: Mixed supported and insufficient evidence

If some claims are supported and some have insufficient evidence:

* Use `UNVERIFIED_RISKY` if the insufficient claim is high-risk or central.
* Use `NOT_ENOUGH_INFORMATION` if there is not enough reliable evidence overall.
* Use `NOT_OUTDATED` only if unsupported claims are minor and low-risk.

---

### Rule 7: Be conservative for current/latest questions

For `RECENT_ONLY` or `TIME_SENSITIVE` questions:

* Do not classify as `NOT_OUTDATED` unless important claims are supported by good evidence.
* If evidence is missing, use `UNVERIFIED_RISKY`.
* If evidence conflicts, use `OUTDATED` or `CONTRADICTED`.

---

### Rule 8: Static answers can be lower risk

For `STATIC` questions, if verification is optional and no strong risk exists:

* Use `NOT_APPLICABLE` if no factual claim needs checking.
* Use `NOT_OUTDATED` if stable claims are supported.
* Use `NOT_ENOUGH_INFORMATION` only if the answer clearly fails to make factual sense.

---

## Main Claim Importance

This skill should treat some claims as more important than others.

A claim is likely central if:

* it directly answers the user’s question
* it has high temporal sensitivity
* it contains the main entity from the question
* it has claim type:

  * `software_version`
  * `current_status`
  * `company_leadership`
  * `law_or_policy`
  * `medical_or_scientific_guideline`
  * `price_or_market_data`
  * `event_result`
  * `date_or_deadline`
  * `api_or_library_behavior`

A claim is likely secondary if:

* it is background information
* it is a general explanation
* it is low temporal sensitivity
* it does not directly answer the question

---

## High-Risk Domain Detection

Treat these as high-risk:

```text
medical
medicine
clinical
drug
diagnosis
treatment
law
legal
visa
immigration
tax
finance
interest rate
stock
crypto
policy
regulation
safety
security
vulnerability
government rule
university admission
Amazon FBA policy
```

For these domains, missing or outdated evidence should increase risk.

---

## Output Examples

### Example 1: Outdated Answer

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
        "verification_confidence": 0.94,
        "risk_level": "high",
        "requires_correction": true
      }
    ]
  }
}
```

Output:

```json
{
  "outdatedness_status": "OUTDATED",
  "is_outdated": true,
  "requires_correction": true,
  "answer_temporal_risk": "high",
  "outdated_claim_ids": ["C1"],
  "contradicted_claim_ids": [],
  "unsupported_claim_ids": [],
  "supported_claim_ids": [],
  "critical_claim_ids": [],
  "main_issue": "The answer uses an old software version as the latest version.",
  "decision_reason": "The main high-sensitivity claim is marked OUTDATED, so the answer requires correction.",
  "confidence": 0.94,
  "recommended_next_action": "generate_correction",
  "answer_level_summary": {
    "total_claims": 1,
    "supported_count": 0,
    "outdated_count": 1,
    "contradicted_count": 0,
    "partially_supported_count": 0,
    "insufficient_evidence_count": 0,
    "not_verifiable_count": 0
  },
  "warnings": []
}
```

---

### Example 2: Partially Outdated Answer

Verification:

```json
{
  "verification_results": [
    {
      "claim_id": "C1",
      "verification_status": "OUTDATED",
      "verification_confidence": 0.92,
      "risk_level": "high"
    },
    {
      "claim_id": "C2",
      "verification_status": "SUPPORTED",
      "verification_confidence": 0.88,
      "risk_level": "low"
    }
  ]
}
```

Output status:

```text
PARTIALLY_OUTDATED
```

---

### Example 3: Contradicted Answer

Verification:

```json
{
  "verification_results": [
    {
      "claim_id": "C1",
      "verification_status": "CONTRADICTED",
      "verification_confidence": 0.93,
      "risk_level": "high"
    }
  ]
}
```

Output status:

```text
CONTRADICTED
```

---

### Example 4: High-Risk Unverified Answer

Question:

```text
Is this visa rule still active?
```

Verification:

```json
{
  "verification_results": [
    {
      "claim_id": "C1",
      "verification_status": "INSUFFICIENT_EVIDENCE",
      "verification_confidence": 0.75,
      "risk_level": "critical"
    }
  ]
}
```

Output status:

```text
UNVERIFIED_RISKY
```

---

### Example 5: Safe Static Answer

Question:

```text
What is binary search?
```

Verification:

```json
{
  "verification_results": [
    {
      "claim_id": "C1",
      "verification_status": "SUPPORTED",
      "verification_confidence": 0.88,
      "risk_level": "low"
    }
  ]
}
```

Output status:

```text
NOT_OUTDATED
```

---

## Implementation Notes for AI Coding Agents

Build this skill as a lightweight answer-level decision module.

Do not call web search.

Do not call an LLM by default.

Do not browse URLs.

Do not retrieve evidence.

Do not correct answers.

Use verification results from Skill 05 only.

Recommended implementation:

* Create a Python module such as `outdated_answer_detector.py`
* Create a function named `detect_outdated_answer(...) -> dict`
* Use deterministic rules
* Count claim statuses
* Detect high-risk domains
* Identify central claims using claim type, temporal sensitivity, and question overlap
* Return strict JSON-compatible dictionary
* Add unit tests
* Keep the module easy to understand and thesis-explainable

---

## Suggested Python Interface

Use this interface:

```python
def detect_outdated_answer(
    question: str,
    answer: str,
    verification_payload: dict,
    claims_payload: dict | None = None,
    temporal_category: str | None = None,
    freshness_payload: dict | None = None
) -> dict:
    """
    Detect whether the full LLM answer is outdated, contradicted, partially outdated, or risky.

    Args:
        question: Original user question.
        answer: Original LLM-generated answer.
        verification_payload: Output from Skill 05.
        claims_payload: Optional output from Skill 02.
        temporal_category: Optional category from Skill 01.
        freshness_payload: Optional output from Skill 04.

    Returns:
        JSON-compatible dict with answer-level outdatedness status and correction decision.
    """
```

---

## Expected Behavior

The detector should be fast, cheap, and deterministic.

It must not waste tokens.

It must not call an LLM.

It must not perform web search.

It must not generate corrected answers.

It only decides whether correction or more evidence is needed.

---

## Quality Requirements

The implementation must satisfy these requirements:

1. Return valid JSON-compatible dictionary every time.
2. Use verification results as the main input.
3. Count supported, outdated, contradicted, partially supported, insufficient, and not-verifiable claims.
4. Distinguish outdated from unverified risky.
5. Distinguish fully outdated from partially outdated.
6. Treat contradiction as high priority.
7. Treat high-risk domains more strictly.
8. Use temporal category to adjust strictness.
9. Identify central claims where possible.
10. Return correction recommendation.
11. Never invent new facts.
12. Never correct the answer inside this module.
13. Avoid LLM calls by default.
14. Include unit tests.
15. Keep logic simple and explainable for thesis writing.
16. Use the package name `temporalguard`.

---

## Test Cases

Use these minimum test cases:

```python
test_cases = [
    {
        "name": "outdated latest Python answer",
        "question": "What is the latest Python version?",
        "answer": "Python 3.10 is the latest stable version of Python.",
        "temporal_category": "RECENT_ONLY",
        "claims_payload": {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_type": "software_version",
                    "temporal_sensitivity": "high",
                    "evidence_need": "fresh"
                }
            ]
        },
        "verification_payload": {
            "verification_results": [
                {
                    "claim_id": "C1",
                    "verification_status": "OUTDATED",
                    "verification_confidence": 0.94,
                    "risk_level": "high",
                    "requires_correction": True
                }
            ]
        },
        "expected_status": "OUTDATED"
    },
    {
        "name": "partially outdated mixed answer",
        "question": "What is the latest Python version and why is Python useful?",
        "answer": "Python 3.10 is the latest version. Python is widely used in data science.",
        "temporal_category": "RECENT_ONLY",
        "claims_payload": {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_type": "software_version",
                    "temporal_sensitivity": "high",
                    "evidence_need": "fresh"
                },
                {
                    "claim_id": "C2",
                    "claim_type": "general_fact",
                    "temporal_sensitivity": "medium",
                    "evidence_need": "optional"
                }
            ]
        },
        "verification_payload": {
            "verification_results": [
                {
                    "claim_id": "C1",
                    "verification_status": "OUTDATED",
                    "verification_confidence": 0.92,
                    "risk_level": "high",
                    "requires_correction": True
                },
                {
                    "claim_id": "C2",
                    "verification_status": "SUPPORTED",
                    "verification_confidence": 0.86,
                    "risk_level": "low",
                    "requires_correction": False
                }
            ]
        },
        "expected_status": "PARTIALLY_OUTDATED"
    },
    {
        "name": "contradicted world cup answer",
        "question": "Who won the 2014 FIFA World Cup?",
        "answer": "France won the 2014 FIFA World Cup.",
        "temporal_category": "HISTORICAL",
        "claims_payload": {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_type": "event_result",
                    "temporal_sensitivity": "low",
                    "evidence_need": "historical"
                }
            ]
        },
        "verification_payload": {
            "verification_results": [
                {
                    "claim_id": "C1",
                    "verification_status": "CONTRADICTED",
                    "verification_confidence": 0.93,
                    "risk_level": "high",
                    "requires_correction": True
                }
            ]
        },
        "expected_status": "CONTRADICTED"
    },
    {
        "name": "high risk unverified visa answer",
        "question": "Is this visa rule still active?",
        "answer": "Yes, this visa rule is still active.",
        "temporal_category": "RECENT_ONLY",
        "claims_payload": {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_type": "law_or_policy",
                    "temporal_sensitivity": "high",
                    "evidence_need": "fresh"
                }
            ]
        },
        "verification_payload": {
            "verification_results": [
                {
                    "claim_id": "C1",
                    "verification_status": "INSUFFICIENT_EVIDENCE",
                    "verification_confidence": 0.75,
                    "risk_level": "critical",
                    "requires_correction": True
                }
            ]
        },
        "expected_status": "UNVERIFIED_RISKY"
    },
    {
        "name": "supported static answer",
        "question": "What is binary search?",
        "answer": "Binary search divides a sorted search space in half.",
        "temporal_category": "STATIC",
        "claims_payload": {
            "claims": [
                {
                    "claim_id": "C1",
                    "claim_type": "definition",
                    "temporal_sensitivity": "low",
                    "evidence_need": "optional"
                }
            ]
        },
        "verification_payload": {
            "verification_results": [
                {
                    "claim_id": "C1",
                    "verification_status": "SUPPORTED",
                    "verification_confidence": 0.88,
                    "risk_level": "low",
                    "requires_correction": False
                }
            ]
        },
        "expected_status": "NOT_OUTDATED"
    },
    {
        "name": "no factual claims creative answer",
        "question": "Write a poem about rain.",
        "answer": "Rain falls softly on the silent street.",
        "temporal_category": "STATIC",
        "claims_payload": {
            "claims": []
        },
        "verification_payload": {
            "verification_results": []
        },
        "expected_status": "NOT_APPLICABLE"
    },
    {
        "name": "factual question no claims",
        "question": "Who is the CEO of OpenAI?",
        "answer": "I am not sure.",
        "temporal_category": "TIME_SENSITIVE",
        "claims_payload": {
            "claims": []
        },
        "verification_payload": {
            "verification_results": []
        },
        "expected_status": "NOT_ENOUGH_INFORMATION"
    }
]
```

---

## Prompt for Claude or Codex Agent

You are implementing Skill 06 for a project called TemporalGuard.

TemporalGuard is a time-aware reliability framework for detecting and correcting outdated responses in Large Language Models.

Your task is to implement only the outdated answer detection skill.

Create a clean, production-quality Python module that detects whether a full LLM answer is outdated, partially outdated, contradicted, unverified risky, or safe.

Create:

1. `src/temporalguard/skills/outdated_answer_detector.py`
2. `tests/test_outdated_answer_detector.py`

Use this function signature:

```python
def detect_outdated_answer(
    question: str,
    answer: str,
    verification_payload: dict,
    claims_payload: dict | None = None,
    temporal_category: str | None = None,
    freshness_payload: dict | None = None
) -> dict:
```

The function must return:

```python
{
    "outdatedness_status": "NOT_OUTDATED | OUTDATED | PARTIALLY_OUTDATED | CONTRADICTED | UNVERIFIED_RISKY | NOT_ENOUGH_INFORMATION | NOT_APPLICABLE",
    "is_outdated": True,
    "requires_correction": True,
    "answer_temporal_risk": "low | medium | high | critical | unknown",
    "outdated_claim_ids": ["C1"],
    "contradicted_claim_ids": [],
    "unsupported_claim_ids": [],
    "supported_claim_ids": [],
    "critical_claim_ids": [],
    "main_issue": "short issue summary",
    "decision_reason": "short reason",
    "confidence": 0.0,
    "recommended_next_action": "no_action | generate_correction | request_more_evidence | ask_clarifying_question",
    "answer_level_summary": {
        "total_claims": 0,
        "supported_count": 0,
        "outdated_count": 0,
        "contradicted_count": 0,
        "partially_supported_count": 0,
        "insufficient_evidence_count": 0,
        "not_verifiable_count": 0
    },
    "warnings": []
}
```

Implementation requirements:

* Use Python standard library only.
* Do not call an LLM.
* Do not call web search.
* Do not retrieve new evidence.
* Do not verify claims from scratch.
* Do not correct answers.
* Use only verification results, claims metadata, temporal category, and optional freshness payload.
* Count claim statuses accurately.
* Identify claim IDs by verification status.
* Treat `CONTRADICTED` as highest priority.
* Treat `OUTDATED` as next priority.
* Distinguish:

  * one central outdated claim only → `OUTDATED`
  * outdated plus supported secondary claims → `PARTIALLY_OUTDATED`
  * only insufficient high-risk evidence → `UNVERIFIED_RISKY`
  * all supported → `NOT_OUTDATED`
  * no factual claims in creative/personal request → `NOT_APPLICABLE`
  * no factual claims in factual/time-sensitive request → `NOT_ENOUGH_INFORMATION`
* Use temporal category:

  * `RECENT_ONLY`, `TIME_SENSITIVE`, `VERSION_DEPENDENT` require stricter evidence
  * `STATIC` can be lower risk
  * `HISTORICAL` should rely on historical verification
* Detect high-risk domains from question, answer, and claim types.
* Infer whether claims are central using claim type, temporal sensitivity, evidence need, and overlap with question.
* Calculate confidence from decisive verification results.
* Set `recommended_next_action` correctly.
* Keep code typed, clean, deterministic, and easy to extend.
* Add unit tests for all provided examples.
* Use the package name `temporalguard`.

Recommended internal helper functions:

```python
_get_verification_results(verification_payload: dict) -> list[dict]
_get_claims_by_id(claims_payload: dict | None) -> dict
_count_statuses(results: list[dict]) -> dict
_detect_high_risk_domain(question: str, answer: str, claims: list[dict]) -> bool
_is_central_claim(claim_id: str, claim: dict | None, question: str) -> bool
_collect_claim_ids_by_status(results: list[dict]) -> dict
_infer_answer_status(results: list[dict], claims_by_id: dict, question: str, answer: str, temporal_category: str | None) -> str
_infer_answer_risk(status: str, results: list[dict], high_risk: bool) -> str
_infer_requires_correction(status: str, risk: str) -> bool
_infer_recommended_action(status: str) -> str
_calculate_confidence(status: str, results: list[dict]) -> float
_build_main_issue(status: str, decisive_results: list[dict]) -> str
```

Important behavior:

* If there are no verification results:

  * If question is creative/subjective/general chat, return `NOT_APPLICABLE`.
  * If question is factual or time-sensitive, return `NOT_ENOUGH_INFORMATION`.
* If any central claim is contradicted, return `CONTRADICTED`.
* If one central claim is outdated and all other claims are absent or minor, return `OUTDATED`.
* If some but not all claims are outdated, return `PARTIALLY_OUTDATED`.
* If all important claims are supported, return `NOT_OUTDATED`.
* If unsupported claims are high-risk or central, return `UNVERIFIED_RISKY`.
* Use `critical` risk for high-risk domains with contradicted, outdated, or unsupported central claims.
* Clamp and round confidence to 3 decimals.

After implementation:

1. Run tests.
2. Fix all failing tests.
3. Report:

   * files created
   * main logic summary
   * test result
   * assumptions
