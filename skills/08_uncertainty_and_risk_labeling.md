# Skill 08: Uncertainty and Risk Labeling

## Purpose

This skill assigns clear uncertainty labels, temporal risk labels, and user-facing safety messages to the final TemporalGuard output.

TemporalGuard should not only say whether an answer is corrected. It must also explain how much the user should trust the answer.

This skill is the eighth step in the TemporalGuard pipeline.

It receives:

1. Original user question
2. Original LLM answer
3. Temporal category from Skill 01
4. Source freshness result from Skill 04
5. Temporal verification result from Skill 05
6. Outdated answer detection result from Skill 06
7. Correction generation result from Skill 07

It returns a final risk label, uncertainty label, trust score, safety warning, and dashboard-ready explanation.

---

## Core Task

Given the pipeline outputs, classify the final answer into a clear risk and uncertainty level.

This skill must answer:

1. How risky is the answer?
2. How uncertain is the correction?
3. Is the answer safe to show?
4. Does the user need fresh evidence, official confirmation, or expert verification?
5. What short label should appear in the dashboard?

---

## Important Boundary

This skill does not:

* retrieve evidence
* verify claims from scratch
* correct the answer
* rewrite the whole final answer
* call web search
* call an LLM by default
* invent confidence values without reason
* hide uncertainty
* overstate safety

This skill only labels risk and uncertainty using previous pipeline outputs.

---

## Inputs

The skill may receive input like this:

```json
{
  "question": "What is the latest Python version?",
  "answer": "Python 3.10 is the latest stable version of Python.",
  "temporal_category": "RECENT_ONLY",
  "freshness_payload": {
    "overall_freshness_score": 0.98,
    "overall_temporal_risk": "low"
  },
  "verification_payload": {
    "overall_verification_status": "NEEDS_CORRECTION",
    "overall_confidence": 0.94,
    "verification_results": [
      {
        "claim_id": "C1",
        "verification_status": "OUTDATED",
        "verification_confidence": 0.94,
        "risk_level": "high"
      }
    ]
  },
  "outdatedness_payload": {
    "outdatedness_status": "OUTDATED",
    "is_outdated": true,
    "requires_correction": true,
    "answer_temporal_risk": "high"
  },
  "correction_payload": {
    "correction_status": "corrected",
    "answer_temporal_risk": "medium",
    "confidence": 0.92,
    "warnings": []
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
  "final_risk_label": "safe | low_risk | medium_risk | high_risk | critical_risk | unknown_risk",
  "uncertainty_label": "very_low | low | medium | high | very_high | unknown",
  "trust_score": 0.0,
  "temporal_safety_status": "safe_to_show | show_with_caution | needs_more_evidence | do_not_use_as_final | not_applicable",
  "user_warning": "string or null",
  "dashboard_badge": "string",
  "risk_reasons": ["string"],
  "uncertainty_reasons": ["string"],
  "recommended_user_action": "none | verify_official_source | retrieve_more_evidence | ask_clarifying_question | consult_expert",
  "high_risk_domain": true,
  "freshness_dependency": "none | low | medium | high | critical",
  "label_confidence": 0.0,
  "notes": "short note"
}
```

---

## Field Instructions

### final_risk_label

Use one of:

```text
safe
low_risk
medium_risk
high_risk
critical_risk
unknown_risk
```

### safe

Use when:

* answer is not time-sensitive
* claims are supported
* no important uncertainty exists
* correction was not needed

Example:

```text
Binary search divides a sorted search space in half.
```

### low_risk

Use when:

* answer is supported
* evidence is reliable
* topic is not high-risk
* small uncertainty may exist

### medium_risk

Use when:

* answer was corrected successfully
* some uncertainty remains
* source is reliable but not perfect
* topic is time-sensitive but not high-risk

### high_risk

Use when:

* original answer was outdated or contradicted
* correction is partial
* evidence is not strong enough
* source freshness is weak
* the topic could affect real decisions

### critical_risk

Use when:

* high-risk domain is involved
* evidence is insufficient
* answer is contradicted or unsupported
* user may make legal, medical, visa, finance, safety, or policy decisions based on it

### unknown_risk

Use when:

* no clear decision can be made
* pipeline inputs are missing or malformed

---

### uncertainty_label

Use one of:

```text
very_low
low
medium
high
very_high
unknown
```

Suggested mapping:

```text
confidence >= 0.90 → very_low uncertainty
0.75–0.89 → low uncertainty
0.60–0.74 → medium uncertainty
0.40–0.59 → high uncertainty
< 0.40 → very_high uncertainty
missing confidence → unknown
```

Important:

Uncertainty is the opposite of confidence.

High confidence means low uncertainty.

---

### trust_score

A score from `0.0` to `1.0`.

This represents how much TemporalGuard trusts the final corrected answer.

Suggested formula:

```text
trust_score = weighted average of:
- correction confidence
- verification confidence
- freshness score
- source reliability score
```

Simple recommended formula:

```text
trust_score = (0.40 * correction_confidence) + (0.30 * verification_confidence) + (0.30 * freshness_score)
```

If no correction was needed:

```text
trust_score = (0.50 * verification_confidence) + (0.30 * freshness_score) + (0.20 * source_reliability)
```

If evidence is insufficient:

```text
trust_score should usually be below 0.50
```

Always clamp between `0.0` and `1.0`.

Round to 3 decimals.

---

### temporal_safety_status

Use one of:

```text
safe_to_show
show_with_caution
needs_more_evidence
do_not_use_as_final
not_applicable
```

### safe_to_show

Use when the final answer is supported or safely corrected.

### show_with_caution

Use when the answer is probably useful but still time-sensitive.

### needs_more_evidence

Use when evidence is incomplete or weak.

### do_not_use_as_final

Use when the topic is high-risk and evidence is insufficient, contradicted, or uncertain.

### not_applicable

Use when the answer is creative, subjective, or does not contain factual claims.

---

### user_warning

Use `null` if no warning is needed.

Use a short warning when risk exists.

Examples:

```text
This answer depends on current information and should be verified with an official source before action.
```

```text
Reliable evidence was insufficient, so this answer should not be treated as confirmed.
```

```text
This is a high-risk legal or policy-related question; official confirmation is recommended.
```

---

### dashboard_badge

A short label for UI display.

Examples:

```text
SAFE
LOW RISK
TIME-SENSITIVE
OUTDATED - CORRECTED
PARTIALLY CORRECTED
UNVERIFIED
HIGH RISK
CRITICAL - VERIFY OFFICIAL SOURCE
NO FACTUAL CLAIMS
```

Keep it short and readable.

---

### risk_reasons

List short reasons.

Examples:

```text
original_answer_outdated
correction_successful
fresh_official_evidence_available
insufficient_evidence
high_risk_domain
source_date_missing
contradicted_claim_detected
time_sensitive_question
```

---

### uncertainty_reasons

List short reasons.

Examples:

```text
fresh_evidence_available
official_source_used
evidence_missing
source_date_unknown
partial_correction
low_verification_confidence
conflicting_evidence
```

---

### recommended_user_action

Use one of:

```text
none
verify_official_source
retrieve_more_evidence
ask_clarifying_question
consult_expert
```

Use `consult_expert` for:

* medical
* legal
* visa
* finance
* safety
* policy/regulation

Use `verify_official_source` for:

* current software versions
* company leadership
* admission rules
* Amazon policies
* immigration rules
* government policies

Use `retrieve_more_evidence` when:

* evidence is insufficient
* sources conflict
* date is unknown

Use `ask_clarifying_question` when:

* the question is too ambiguous

Use `none` when:

* answer is supported and low-risk

---

### high_risk_domain

Return `true` if the question, answer, or claims involve:

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
insurance
employment law
```

Otherwise return `false`.

---

### freshness_dependency

Use one of:

```text
none
low
medium
high
critical
```

Use `critical` when the answer is useless or dangerous without current evidence.

Examples:

* visa rule currently active
* medical guideline currently recommended
* stock price now
* active legal policy

Use `high` for:

* latest software version
* current CEO
* active product policy
* latest model

Use `medium` for:

* recent research
* technology documentation
* university admission rules

Use `low` for:

* slowly changing facts

Use `none` for:

* stable definitions
* historical facts already anchored to a past date
* creative writing

---

### label_confidence

Confidence in the assigned risk label.

This is not the same as answer trust.

Use high label confidence when the decision is clear.

Example:

* clear outdated answer with successful correction → label confidence high
* missing inputs → label confidence low

Suggested:

```text
0.90–1.00 = very clear label
0.75–0.89 = clear label
0.60–0.74 = moderate label
0.40–0.59 = weak label
below 0.40 = uncertain label
```

---

## Risk Decision Rules

### Rule 1: Critical domains are stricter

If high-risk domain is true and evidence is insufficient, contradicted, or correction failed:

```text
final_risk_label = critical_risk
temporal_safety_status = do_not_use_as_final
recommended_user_action = consult_expert or verify_official_source
```

---

### Rule 2: Corrected outdated answer usually becomes medium risk

If answer was outdated but corrected with strong evidence:

```text
final_risk_label = medium_risk
temporal_safety_status = show_with_caution
dashboard_badge = OUTDATED - CORRECTED
```

Use `low_risk` only if the correction is strong and the domain is not high-risk.

---

### Rule 3: Supported low-risk answer is safe

If all important claims are supported and topic is not high-risk:

```text
final_risk_label = safe or low_risk
temporal_safety_status = safe_to_show
recommended_user_action = none
```

---

### Rule 4: Unverified current answer is risky

If the question is `RECENT_ONLY`, `TIME_SENSITIVE`, or `VERSION_DEPENDENT` and evidence is missing:

```text
final_risk_label = high_risk
temporal_safety_status = needs_more_evidence
recommended_user_action = retrieve_more_evidence or verify_official_source
```

---

### Rule 5: Contradicted answer remains high risk even after correction

If original answer was contradicted but corrected:

```text
final_risk_label = medium_risk or high_risk
```

Use high risk if the domain is high-risk.

---

### Rule 6: No factual claims means not applicable

If outdatedness status is `NOT_APPLICABLE`:

```text
final_risk_label = safe
uncertainty_label = very_low
temporal_safety_status = not_applicable
dashboard_badge = NO FACTUAL CLAIMS
recommended_user_action = none
```

---

### Rule 7: Missing pipeline inputs means unknown risk

If required inputs are missing or malformed:

```text
final_risk_label = unknown_risk
uncertainty_label = unknown
temporal_safety_status = needs_more_evidence
dashboard_badge = UNKNOWN
recommended_user_action = retrieve_more_evidence
```

---

## User Warning Rules

Use a warning only when needed.

### No warning

For:

* safe static answer
* supported historical answer
* supported low-risk answer

### Light warning

For:

* corrected outdated answer
* time-sensitive answer with good evidence

Example:

```text
This answer was updated using checked evidence, but it may change again in the future.
```

### Strong warning

For:

* high-risk domain
* insufficient evidence
* contradicted answer
* partial correction

Example:

```text
This answer should not be used as final because reliable evidence was insufficient.
```

### Critical warning

For:

* legal/medical/visa/finance/safety topic with insufficient evidence

Example:

```text
This is a high-risk topic. Do not rely on this answer without checking an official source or qualified expert.
```

---

## Output Examples

### Example 1: Outdated but Corrected Software Version

Input summary:

```text
Original answer outdated.
Correction successful.
Fresh official evidence available.
Topic: latest software version.
```

Output:

```json
{
  "final_risk_label": "medium_risk",
  "uncertainty_label": "low",
  "trust_score": 0.93,
  "temporal_safety_status": "show_with_caution",
  "user_warning": "This answer was updated using checked evidence, but software versions can change again.",
  "dashboard_badge": "OUTDATED - CORRECTED",
  "risk_reasons": ["original_answer_outdated", "correction_successful", "time_sensitive_question"],
  "uncertainty_reasons": ["fresh_evidence_available"],
  "recommended_user_action": "verify_official_source",
  "high_risk_domain": false,
  "freshness_dependency": "high",
  "label_confidence": 0.92,
  "notes": "The answer was corrected using reliable evidence."
}
```

---

### Example 2: Supported Static Answer

Input summary:

```text
Static question.
Claims supported.
No correction needed.
```

Output:

```json
{
  "final_risk_label": "safe",
  "uncertainty_label": "very_low",
  "trust_score": 0.91,
  "temporal_safety_status": "safe_to_show",
  "user_warning": null,
  "dashboard_badge": "SAFE",
  "risk_reasons": ["supported_static_answer"],
  "uncertainty_reasons": ["stable_knowledge"],
  "recommended_user_action": "none",
  "high_risk_domain": false,
  "freshness_dependency": "none",
  "label_confidence": 0.95,
  "notes": "The answer is a stable concept and does not require temporal correction."
}
```

---

### Example 3: High-Risk Unverified Visa Claim

Input summary:

```text
Visa question.
Evidence insufficient.
Correction failed.
```

Output:

```json
{
  "final_risk_label": "critical_risk",
  "uncertainty_label": "very_high",
  "trust_score": 0.25,
  "temporal_safety_status": "do_not_use_as_final",
  "user_warning": "This is a high-risk visa or policy-related question. Do not rely on this answer without checking the official government source.",
  "dashboard_badge": "CRITICAL - VERIFY OFFICIAL SOURCE",
  "risk_reasons": ["high_risk_domain", "insufficient_evidence", "time_sensitive_question"],
  "uncertainty_reasons": ["evidence_missing", "correction_failed"],
  "recommended_user_action": "consult_expert",
  "high_risk_domain": true,
  "freshness_dependency": "critical",
  "label_confidence": 0.93,
  "notes": "The answer is not safe to use as final because reliable evidence was insufficient."
}
```

---

### Example 4: No Factual Claims

Input summary:

```text
Creative answer.
No factual claim extracted.
```

Output:

```json
{
  "final_risk_label": "safe",
  "uncertainty_label": "very_low",
  "trust_score": 1.0,
  "temporal_safety_status": "not_applicable",
  "user_warning": null,
  "dashboard_badge": "NO FACTUAL CLAIMS",
  "risk_reasons": ["not_applicable"],
  "uncertainty_reasons": [],
  "recommended_user_action": "none",
  "high_risk_domain": false,
  "freshness_dependency": "none",
  "label_confidence": 0.95,
  "notes": "Temporal risk labeling is not applicable to this response."
}
```

---

## Implementation Notes for AI Coding Agents

Build this skill as a deterministic labeler.

Do not call web search.

Do not call an LLM by default.

Do not retrieve evidence.

Do not verify claims from scratch.

Do not correct the answer.

Use previous pipeline outputs only.

Recommended implementation:

* Create a Python module such as `uncertainty_risk_labeler.py`
* Create a function named `label_uncertainty_and_risk(...) -> dict`
* Use deterministic rules
* Calculate trust score from correction confidence, verification confidence, and freshness score
* Detect high-risk domains with keyword rules
* Use conservative labels when evidence is missing
* Return strict JSON-compatible dictionary
* Add unit tests
* Keep the module easy to understand and thesis-explainable

---

## Suggested Python Interface

Use this interface:

```python
def label_uncertainty_and_risk(
    question: str,
    answer: str,
    temporal_category: str | None = None,
    freshness_payload: dict | None = None,
    verification_payload: dict | None = None,
    outdatedness_payload: dict | None = None,
    correction_payload: dict | None = None
) -> dict:
    """
    Assign final uncertainty, risk, trust, and safety labels for the TemporalGuard output.

    Args:
        question: Original user question.
        answer: Original LLM-generated answer.
        temporal_category: Optional category from Skill 01.
        freshness_payload: Optional output from Skill 04.
        verification_payload: Optional output from Skill 05.
        outdatedness_payload: Optional output from Skill 06.
        correction_payload: Optional output from Skill 07.

    Returns:
        JSON-compatible dict with final risk label, uncertainty label,
        trust score, dashboard badge, warning, and recommended action.
    """
```

---

## Expected Behavior

The labeler should be fast, cheap, and deterministic.

It must not waste tokens.

It must not call an LLM.

It must not perform web search.

It must not generate corrected answers.

It only assigns uncertainty and risk labels.

---

## Quality Requirements

The implementation must satisfy these requirements:

1. Return valid JSON-compatible dictionary every time.
2. Use correction output when available.
3. Use outdatedness result as the main risk signal.
4. Use verification confidence as the main evidence confidence signal.
5. Use freshness score as the main temporal confidence signal.
6. Detect high-risk domains from question, answer, and claim/status metadata.
7. Treat high-risk unsupported claims conservatively.
8. Distinguish risk from uncertainty.
9. Produce clear dashboard badges.
10. Produce short user warnings only when needed.
11. Never invent new facts.
12. Never retrieve or verify evidence.
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
        "name": "outdated corrected software version",
        "question": "What is the latest Python version?",
        "answer": "Python 3.10 is the latest stable version.",
        "temporal_category": "RECENT_ONLY",
        "freshness_payload": {
            "overall_freshness_score": 0.98,
            "overall_temporal_risk": "low"
        },
        "verification_payload": {
            "overall_verification_status": "NEEDS_CORRECTION",
            "overall_confidence": 0.94
        },
        "outdatedness_payload": {
            "outdatedness_status": "OUTDATED",
            "is_outdated": True,
            "requires_correction": True,
            "answer_temporal_risk": "high"
        },
        "correction_payload": {
            "correction_status": "corrected",
            "correction_type": "update_outdated_fact",
            "answer_temporal_risk": "medium",
            "confidence": 0.92,
            "warnings": []
        },
        "expected_final_risk_label": "medium_risk",
        "expected_dashboard_badge": "OUTDATED - CORRECTED"
    },
    {
        "name": "supported static answer",
        "question": "What is binary search?",
        "answer": "Binary search divides a sorted search space in half.",
        "temporal_category": "STATIC",
        "freshness_payload": {
            "overall_freshness_score": 0.85,
            "overall_temporal_risk": "low"
        },
        "verification_payload": {
            "overall_verification_status": "SUPPORTED",
            "overall_confidence": 0.90
        },
        "outdatedness_payload": {
            "outdatedness_status": "NOT_OUTDATED",
            "is_outdated": False,
            "requires_correction": False,
            "answer_temporal_risk": "low"
        },
        "correction_payload": {
            "correction_status": "no_correction_needed",
            "correction_type": "no_change",
            "answer_temporal_risk": "low",
            "confidence": 0.88,
            "warnings": []
        },
        "expected_final_risk_label": "safe",
        "expected_dashboard_badge": "SAFE"
    },
    {
        "name": "critical unverified visa claim",
        "question": "Is this visa rule still active?",
        "answer": "Yes, this visa rule is still active.",
        "temporal_category": "RECENT_ONLY",
        "freshness_payload": {
            "overall_freshness_score": 0.20,
            "overall_temporal_risk": "critical"
        },
        "verification_payload": {
            "overall_verification_status": "INSUFFICIENT_EVIDENCE",
            "overall_confidence": 0.70
        },
        "outdatedness_payload": {
            "outdatedness_status": "UNVERIFIED_RISKY",
            "is_outdated": False,
            "requires_correction": True,
            "answer_temporal_risk": "critical"
        },
        "correction_payload": {
            "correction_status": "unable_to_correct",
            "correction_type": "add_uncertainty",
            "answer_temporal_risk": "critical",
            "confidence": 0.30,
            "warnings": ["insufficient_evidence_for_high_risk_claim"]
        },
        "expected_final_risk_label": "critical_risk",
        "expected_dashboard_badge": "CRITICAL - VERIFY OFFICIAL SOURCE"
    },
    {
        "name": "contradicted but corrected historical claim",
        "question": "Who won the 2014 FIFA World Cup?",
        "answer": "France won the 2014 FIFA World Cup.",
        "temporal_category": "HISTORICAL",
        "freshness_payload": {
            "overall_freshness_score": 0.90,
            "overall_temporal_risk": "low"
        },
        "verification_payload": {
            "overall_verification_status": "NEEDS_CORRECTION",
            "overall_confidence": 0.93
        },
        "outdatedness_payload": {
            "outdatedness_status": "CONTRADICTED",
            "is_outdated": False,
            "requires_correction": True,
            "answer_temporal_risk": "high"
        },
        "correction_payload": {
            "correction_status": "corrected",
            "correction_type": "fix_contradiction",
            "answer_temporal_risk": "medium",
            "confidence": 0.92,
            "warnings": []
        },
        "expected_final_risk_label": "medium_risk",
        "expected_dashboard_badge": "CONTRADICTION - CORRECTED"
    },
    {
        "name": "no factual claims",
        "question": "Write a poem about rain.",
        "answer": "Rain falls softly on the silent street.",
        "temporal_category": "STATIC",
        "freshness_payload": None,
        "verification_payload": {
            "overall_verification_status": "NOT_VERIFIABLE",
            "overall_confidence": 0.90
        },
        "outdatedness_payload": {
            "outdatedness_status": "NOT_APPLICABLE",
            "is_outdated": False,
            "requires_correction": False,
            "answer_temporal_risk": "low"
        },
        "correction_payload": {
            "correction_status": "no_correction_needed",
            "correction_type": "no_change",
            "answer_temporal_risk": "low",
            "confidence": 1.0,
            "warnings": []
        },
        "expected_final_risk_label": "safe",
        "expected_dashboard_badge": "NO FACTUAL CLAIMS"
    },
    {
        "name": "missing inputs unknown risk",
        "question": "Who is the CEO of OpenAI?",
        "answer": "Sam Altman is the CEO of OpenAI.",
        "temporal_category": "TIME_SENSITIVE",
        "freshness_payload": None,
        "verification_payload": None,
        "outdatedness_payload": None,
        "correction_payload": None,
        "expected_final_risk_label": "unknown_risk",
        "expected_dashboard_badge": "UNKNOWN"
    }
]
```

---

## Prompt for Claude or Codex Agent

You are implementing Skill 08 for a project called TemporalGuard.

TemporalGuard is a time-aware reliability framework for detecting and correcting outdated responses in Large Language Models.

Your task is to implement only the uncertainty and risk labeling skill.

Create a clean, production-quality Python module that assigns final risk labels, uncertainty labels, trust scores, dashboard badges, safety statuses, warnings, and recommended user actions.

Create:

1. `src/temporalguard/skills/uncertainty_risk_labeler.py`
2. `tests/test_uncertainty_risk_labeler.py`

Use this function signature:

```python
def label_uncertainty_and_risk(
    question: str,
    answer: str,
    temporal_category: str | None = None,
    freshness_payload: dict | None = None,
    verification_payload: dict | None = None,
    outdatedness_payload: dict | None = None,
    correction_payload: dict | None = None
) -> dict:
```

The function must return:

```python
{
    "final_risk_label": "safe | low_risk | medium_risk | high_risk | critical_risk | unknown_risk",
    "uncertainty_label": "very_low | low | medium | high | very_high | unknown",
    "trust_score": 0.0,
    "temporal_safety_status": "safe_to_show | show_with_caution | needs_more_evidence | do_not_use_as_final | not_applicable",
    "user_warning": None,
    "dashboard_badge": "...",
    "risk_reasons": [],
    "uncertainty_reasons": [],
    "recommended_user_action": "none | verify_official_source | retrieve_more_evidence | ask_clarifying_question | consult_expert",
    "high_risk_domain": False,
    "freshness_dependency": "none | low | medium | high | critical",
    "label_confidence": 0.0,
    "notes": "short note"
}
```

Implementation requirements:

* Use Python standard library only.
* Do not call an LLM.
* Do not call web search.
* Do not retrieve evidence.
* Do not correct answers.
* Use previous pipeline outputs only.
* Treat `outdatedness_payload` as the main risk signal.
* Treat `correction_payload` as the main final-answer safety signal.
* Treat `freshness_payload` and `verification_payload` as confidence signals.
* Calculate trust score with a simple deterministic weighted formula.
* Clamp and round all scores to 3 decimals.
* Detect high-risk domains from question, answer, and status metadata.
* Detect freshness dependency from temporal category and domain.
* Produce short dashboard badges.
* Produce user warnings only when needed.
* Use conservative risk labels when data is missing.
* Return `unknown_risk` if required pipeline inputs are missing for a factual/time-sensitive question.
* Return `safe` and `NO FACTUAL CLAIMS` for not-applicable creative outputs.
* Add unit tests for all provided examples.
* Keep code typed, deterministic, clean, and easy to extend.
* Use the package name `temporalguard`.

Recommended internal helper functions:

```python
_detect_high_risk_domain(question: str, answer: str, *payloads: dict | None) -> bool
_infer_freshness_dependency(temporal_category: str | None, high_risk: bool, question: str) -> str
_get_confidence_values(freshness_payload: dict | None, verification_payload: dict | None, correction_payload: dict | None) -> dict
_calculate_trust_score(confidences: dict, status: str, high_risk: bool) -> float
_confidence_to_uncertainty_label(confidence: float | None) -> str
_infer_final_risk_label(outdatedness_payload: dict | None, correction_payload: dict | None, high_risk: bool, temporal_category: str | None) -> str
_infer_safety_status(final_risk_label: str, correction_status: str | None) -> str
_build_dashboard_badge(outdatedness_status: str | None, correction_status: str | None, final_risk_label: str) -> str
_build_user_warning(final_risk_label: str, high_risk: bool, freshness_dependency: str, correction_status: str | None) -> str | None
_infer_recommended_action(final_risk_label: str, high_risk: bool, freshness_dependency: str, correction_status: str | None) -> str
_build_risk_reasons(...)
_build_uncertainty_reasons(...)
```

Important behavior:

* If all payloads are missing and the question is time-sensitive, return:

  * `final_risk_label = "unknown_risk"`
  * `uncertainty_label = "unknown"`
  * `trust_score = 0.0`
  * `temporal_safety_status = "needs_more_evidence"`
  * `dashboard_badge = "UNKNOWN"`
* If correction status is `corrected` after `OUTDATED`, return badge `OUTDATED - CORRECTED`.
* If correction status is `corrected` after `CONTRADICTED`, return badge `CONTRADICTION - CORRECTED`.
* If correction status is `unable_to_correct` and high risk, return `critical_risk`.
* If no correction needed and status is `NOT_OUTDATED`, return `safe` or `low_risk`.
* If status is `NOT_APPLICABLE`, return badge `NO FACTUAL CLAIMS`.
* Keep warnings short.
* Do not include raw JSON in user_warning or notes.

After implementation:

1. Run tests.
2. Fix all failing tests.
3. Report:

   * files created
   * main logic summary
   * test result
   * assumptions
