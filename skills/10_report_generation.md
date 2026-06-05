# Skill 10: Report Generation

## Purpose

This skill generates clean, human-readable reports from TemporalGuard pipeline outputs.

TemporalGuard should not only produce JSON results. It should also explain the result clearly for:

1. A user-facing dashboard
2. A thesis experiment report
3. A technical evaluation summary
4. A debugging report for developers

This skill is the tenth step in the TemporalGuard pipeline.

It receives outputs from all previous skills and converts them into a clear report without changing any facts.

---

## Core Task

Given TemporalGuard pipeline outputs, generate a structured report that explains:

1. The original question
2. The original LLM answer
3. Whether the question is time-sensitive
4. Extracted claims
5. Retrieved evidence
6. Freshness and reliability scores
7. Verification results
8. Whether the answer was outdated
9. Corrected answer
10. Final risk and uncertainty labels
11. Short conclusion

This skill must produce both machine-readable and user-readable report sections.

---

## Important Boundary

This skill does not:

* retrieve evidence
* verify claims from scratch
* score sources from scratch
* correct answers from scratch
* invent facts
* add claims not found in previous outputs
* call web search
* call an LLM by default
* hide uncertainty
* overstate the result

This skill only formats and summarizes previous pipeline outputs.

---

## Inputs

The skill may receive input like this:

```json
{
  "example_id": "EX001",
  "question": "What is the latest Python version?",
  "original_answer": "Python 3.10 is the latest stable version of Python.",
  "temporal_detection": {},
  "claims": {},
  "evidence": {},
  "freshness": {},
  "verification": {},
  "outdatedness": {},
  "correction": {},
  "risk_label": {},
  "evaluation": null
}
```

---

## Required Output Format

Always return valid JSON only.

Do not include markdown outside JSON.

Use this schema:

```json
{
  "report_id": "string",
  "example_id": "string or null",
  "report_type": "dashboard | technical | thesis | debug",
  "title": "string",
  "executive_summary": "string",
  "final_answer": "string",
  "dashboard_summary": {
    "badge": "string",
    "risk_label": "string",
    "uncertainty_label": "string",
    "trust_score": 0.0,
    "temporal_safety_status": "string",
    "user_warning": "string or null"
  },
  "pipeline_summary": {
    "temporal_category": "string or null",
    "needs_fresh_evidence": true,
    "total_claims": 0,
    "verification_status": "string or null",
    "outdatedness_status": "string or null",
    "correction_status": "string or null",
    "final_risk_label": "string or null"
  },
  "claim_report": [
    {
      "claim_id": "C1",
      "claim_text": "string",
      "claim_type": "string or null",
      "verification_status": "string or null",
      "risk_level": "string or null",
      "requires_correction": true,
      "claim_value": "string or null",
      "evidence_value": "string or null",
      "short_explanation": "string"
    }
  ],
  "evidence_report": [
    {
      "claim_id": "C1",
      "evidence_id": "E1",
      "title": "string",
      "publisher": "string",
      "source_type": "string",
      "url": "string",
      "date_used": "string or null",
      "freshness_label": "string or null",
      "combined_score": 0.0,
      "evidence_summary": "string"
    }
  ],
  "correction_report": {
    "original_answer": "string",
    "corrected_answer": "string",
    "changed_claim_ids": [],
    "unsupported_claim_ids": [],
    "freshness_note": "string or null",
    "uncertainty_note": "string or null",
    "safety_note": "string or null",
    "user_visible_explanation": "string or null"
  },
  "thesis_summary": {
    "problem_observed": "string",
    "temporal_failure_type": "string",
    "evidence_quality": "string",
    "system_decision": "string",
    "research_value": "string"
  },
  "debug_info": {
    "missing_sections": [],
    "warnings": [],
    "raw_statuses": {}
  }
}
```

---

## Report Types

The function should support four report types.

### 1. dashboard

Use for Streamlit or web UI.

Dashboard report should be short and user-friendly.

It should focus on:

* final corrected answer
* risk badge
* user warning
* evidence summary
* simple explanation

---

### 2. technical

Use for developer or project documentation.

Technical report should include:

* all pipeline statuses
* claim-level results
* source scores
* correction metadata
* warnings

---

### 3. thesis

Use for thesis result writing.

Thesis report should include:

* problem observed
* temporal failure type
* evidence quality
* verification result
* correction result
* research interpretation

Language should be formal but simple.

---

### 4. debug

Use for debugging pipeline errors.

Debug report should include:

* missing sections
* malformed fields
* raw statuses
* warnings
* empty claim/evidence issues

---

## Field Instructions

### report_id

Use a deterministic readable ID if example ID exists.

Example:

```text
RPT_EX001
```

If no example ID exists, use:

```text
RPT_UNKNOWN
```

---

### title

Examples:

```text
TemporalGuard Report for EX001
```

```text
Temporal Reliability Report
```

---

### executive_summary

A short 2–4 sentence explanation.

Good example:

```text
The original answer was time-sensitive and contained one outdated claim. TemporalGuard found that the claimed latest Python version did not match the checked evidence. The answer was corrected using the best available source, but the result remains time-sensitive because software versions can change.
```

Bad example:

```text
Here is the report.
```

---

### final_answer

Use corrected answer from Skill 07 if available.

If no correction is needed, use original answer.

If unable to correct, use the uncertainty-based corrected answer from Skill 07.

Never generate a new answer from scratch.

---

### dashboard_summary

Use values from Skill 08.

If Skill 08 is missing, infer only basic values and add a warning.

---

### pipeline_summary

Use values from previous skills:

* Skill 01 → temporal category, needs fresh evidence
* Skill 02 → total claims
* Skill 05 → verification status
* Skill 06 → outdatedness status
* Skill 07 → correction status
* Skill 08 → final risk label

---

### claim_report

Create one entry per extracted claim.

Use Skill 02 and Skill 05 together.

Each claim report must explain the claim result briefly.

Example:

```text
The claim was marked OUTDATED because the evidence value differs from the claim value.
```

If verification is missing:

```text
This claim was extracted but not verified.
```

---

### evidence_report

Include the most important evidence items only.

Default maximum:

```text
5 evidence items
```

Use evidence from Skill 03 and scores from Skill 04.

Do not include long source text.

Do not include more than needed.

---

### correction_report

Use Skill 07.

Include:

* original answer
* corrected answer
* changed claim IDs
* unsupported claim IDs
* freshness note
* uncertainty note
* safety note
* user visible explanation

---

### thesis_summary

This section is for thesis writing.

Use simple, formal academic language.

Fields:

#### problem_observed

Example:

```text
The base LLM produced an answer that depended on current information but used an outdated value.
```

#### temporal_failure_type

Use one of:

```text
outdated_current_fact
contradicted_historical_fact
insufficient_evidence_for_current_claim
version_mismatch
policy_status_uncertainty
not_applicable
no_failure_detected
unknown
```

#### evidence_quality

Examples:

```text
The evidence was fresh and authoritative.
The evidence was relevant but the source date was unclear.
The evidence was insufficient for a reliable correction.
```

#### system_decision

Examples:

```text
TemporalGuard marked the answer as OUTDATED and generated a corrected response.
TemporalGuard marked the answer as UNVERIFIED_RISKY and avoided unsupported correction.
TemporalGuard marked the answer as NOT_OUTDATED.
```

#### research_value

Explain why this example matters for the thesis.

Examples:

```text
This example shows how TemporalGuard can reduce outdated answers in current software-version questions.
```

```text
This example shows that the system avoids overclaiming when fresh evidence is not available.
```

---

### debug_info

Include missing or malformed sections.

Expected pipeline sections:

```text
temporal_detection
claims
evidence
freshness
verification
outdatedness
correction
risk_label
```

If any are missing, list them.

Also include raw statuses:

```json
{
  "temporal_category": "RECENT_ONLY",
  "overall_verification_status": "NEEDS_CORRECTION",
  "outdatedness_status": "OUTDATED",
  "correction_status": "corrected",
  "final_risk_label": "medium_risk"
}
```

---

## Report Generation Rules

### Rule 1: Never invent missing facts

If a section is missing, say it is missing.

Do not guess.

---

### Rule 2: Use corrected answer from Skill 07

Do not create a new corrected answer inside this module.

---

### Rule 3: Keep dashboard report concise

For dashboard reports, avoid long technical details.

---

### Rule 4: Keep thesis report formal

For thesis reports, use simple academic language.

---

### Rule 5: Show uncertainty clearly

If evidence is insufficient, the report must say so.

---

### Rule 6: Evidence report must stay short

Include only top evidence items.

Default maximum:

```text
5
```

---

### Rule 7: Support partial pipeline outputs

The report generator must still return a valid report if some pipeline sections are missing.

---

## Output Examples

### Example 1: Outdated Corrected Answer

Input summary:

```text
Question: What is the latest Python version?
Original answer: Python 3.10 is latest.
Outdatedness: OUTDATED
Correction: corrected to Python 3.13.5
Risk label: OUTDATED - CORRECTED
```

Output summary:

```json
{
  "executive_summary": "The original answer was time-sensitive and contained an outdated software-version claim. TemporalGuard found that the checked evidence listed a newer Python version. The answer was corrected, but the result remains time-sensitive because software versions can change.",
  "final_answer": "Python 3.10 is not the latest stable Python version. Based on the checked official evidence, Python 3.13.5 is listed as the latest release."
}
```

---

### Example 2: High-Risk Unverified Answer

Input summary:

```text
Question: Is this visa rule still active?
Outdatedness: UNVERIFIED_RISKY
Correction: unable_to_correct
Risk: CRITICAL
```

Output summary:

```json
{
  "executive_summary": "The original answer involved a high-risk current policy claim. TemporalGuard could not verify the claim with reliable fresh evidence. The system therefore avoided unsupported correction and marked the answer as critical risk.",
  "final_answer": "I could not safely verify whether this visa rule is still active from the available evidence. Because visa rules can change and may affect real decisions, this should be checked directly on the official immigration or government website before taking action."
}
```

---

## Implementation Notes for AI Coding Agents

Build this skill as a deterministic report formatter.

Do not call web search.

Do not call an LLM by default.

Do not verify, retrieve, or correct facts.

Use previous pipeline outputs only.

Recommended implementation:

* Create a Python module such as `report_generator.py`
* Create a function named `generate_report(...) -> dict`
* Support `report_type`
* Use helper functions to extract sections safely
* Return strict JSON-compatible dictionary
* Include unit tests
* Keep the report readable and dashboard-ready
* Keep thesis sections formal and concise
* Use the package name `temporalguard`

---

## Suggested Python Interface

Use this interface:

```python
def generate_report(
    pipeline_output: dict,
    report_type: str = "dashboard",
    max_evidence_items: int = 5
) -> dict:
    """
    Generate a structured TemporalGuard report from pipeline outputs.

    Args:
        pipeline_output: Full or partial TemporalGuard pipeline output.
        report_type: One of dashboard, technical, thesis, debug.
        max_evidence_items: Maximum evidence items to include.

    Returns:
        JSON-compatible dict with report sections.
    """
```

---

## Expected Pipeline Output Format

```python
pipeline_output = {
    "example_id": "EX001",
    "question": "...",
    "original_answer": "...",
    "temporal_detection": {},
    "claims": {},
    "evidence": {},
    "freshness": {},
    "verification": {},
    "outdatedness": {},
    "correction": {},
    "risk_label": {},
    "evaluation": {}
}
```

---

## Expected Behavior

The report generator should be fast, cheap, and deterministic.

It must not waste tokens.

It must not call an LLM.

It must not perform web search.

It must not invent facts.

It only formats pipeline outputs into a report.

---

## Quality Requirements

The implementation must satisfy these requirements:

1. Return valid JSON-compatible dictionary every time.
2. Support dashboard, technical, thesis, and debug report types.
3. Use Skill 07 corrected answer as final answer.
4. Use original answer when no correction was needed.
5. Use Skill 08 risk labels for dashboard summary.
6. Build claim report by combining Skill 02 and Skill 05.
7. Build evidence report by combining Skill 03 and Skill 04.
8. Detect missing pipeline sections.
9. Never invent missing values.
10. Keep evidence summaries short.
11. Include thesis-ready interpretation.
12. Include debug information.
13. Handle malformed inputs safely.
14. Avoid LLM calls by default.
15. Include unit tests.
16. Use the package name `temporalguard`.

---

## Test Cases

Use these minimum test cases:

```python
test_cases = [
    {
        "name": "outdated corrected python report",
        "pipeline_output": {
            "example_id": "EX001",
            "question": "What is the latest Python version?",
            "original_answer": "Python 3.10 is the latest stable version of Python.",
            "temporal_detection": {
                "temporal_category": "RECENT_ONLY",
                "needs_fresh_evidence": True
            },
            "claims": {
                "claims": [
                    {
                        "claim_id": "C1",
                        "claim_text": "Python 3.10 is the latest stable version of Python.",
                        "claim_type": "software_version"
                    }
                ],
                "total_claims": 1
            },
            "evidence": {
                "evidence_results": [
                    {
                        "claim_id": "C1",
                        "evidence_items": [
                            {
                                "evidence_id": "E1",
                                "title": "Download Python",
                                "url": "https://www.python.org/downloads/",
                                "publisher": "Python Software Foundation",
                                "source_type": "official",
                                "evidence_summary": "The official Python downloads page lists Python 3.13.5 as the latest release."
                            }
                        ]
                    }
                ]
            },
            "freshness": {
                "freshness_results": [
                    {
                        "claim_id": "C1",
                        "evidence_scores": [
                            {
                                "evidence_id": "E1",
                                "date_used": "2026-06-01",
                                "freshness_label": "very_fresh",
                                "combined_score": 0.98
                            }
                        ]
                    }
                ],
                "overall_freshness_score": 0.98
            },
            "verification": {
                "verification_results": [
                    {
                        "claim_id": "C1",
                        "verification_status": "OUTDATED",
                        "risk_level": "high",
                        "requires_correction": True,
                        "claim_value": "Python 3.10",
                        "evidence_value": "Python 3.13.5",
                        "reason": "The claim says Python 3.10 is latest, but official evidence lists Python 3.13.5 as latest."
                    }
                ],
                "overall_verification_status": "NEEDS_CORRECTION",
                "overall_confidence": 0.94
            },
            "outdatedness": {
                "outdatedness_status": "OUTDATED",
                "is_outdated": True,
                "requires_correction": True,
                "answer_temporal_risk": "high"
            },
            "correction": {
                "corrected_answer": "Python 3.10 is not the latest stable Python version. Based on the checked official evidence, Python 3.13.5 is listed as the latest release.",
                "correction_status": "corrected",
                "changed_claim_ids": ["C1"],
                "unsupported_claim_ids": [],
                "freshness_note": "The correction uses checked evidence for a current software-version claim.",
                "uncertainty_note": None,
                "safety_note": None,
                "user_visible_explanation": "The original answer was outdated because the claimed latest version differed from the checked evidence."
            },
            "risk_label": {
                "final_risk_label": "medium_risk",
                "uncertainty_label": "low",
                "trust_score": 0.93,
                "temporal_safety_status": "show_with_caution",
                "user_warning": "This answer was updated using checked evidence, but software versions can change again.",
                "dashboard_badge": "OUTDATED - CORRECTED"
            }
        },
        "report_type": "dashboard",
        "expected_badge": "OUTDATED - CORRECTED"
    },
    {
        "name": "safe static report",
        "pipeline_output": {
            "example_id": "EX002",
            "question": "What is binary search?",
            "original_answer": "Binary search divides a sorted search space in half.",
            "temporal_detection": {
                "temporal_category": "STATIC",
                "needs_fresh_evidence": False
            },
            "claims": {
                "claims": [
                    {
                        "claim_id": "C1",
                        "claim_text": "Binary search divides a sorted search space in half.",
                        "claim_type": "definition"
                    }
                ],
                "total_claims": 1
            },
            "verification": {
                "verification_results": [
                    {
                        "claim_id": "C1",
                        "verification_status": "SUPPORTED",
                        "risk_level": "low",
                        "requires_correction": False
                    }
                ],
                "overall_verification_status": "SUPPORTED",
                "overall_confidence": 0.90
            },
            "outdatedness": {
                "outdatedness_status": "NOT_OUTDATED",
                "is_outdated": False,
                "requires_correction": False,
                "answer_temporal_risk": "low"
            },
            "correction": {
                "corrected_answer": "Binary search divides a sorted search space in half.",
                "correction_status": "no_correction_needed",
                "changed_claim_ids": [],
                "unsupported_claim_ids": [],
                "freshness_note": "No temporal correction was needed for this stable concept.",
                "uncertainty_note": None,
                "safety_note": None,
                "user_visible_explanation": "The answer did not appear outdated based on the verification result."
            },
            "risk_label": {
                "final_risk_label": "safe",
                "uncertainty_label": "very_low",
                "trust_score": 0.91,
                "temporal_safety_status": "safe_to_show",
                "user_warning": None,
                "dashboard_badge": "SAFE"
            }
        },
        "report_type": "thesis",
        "expected_badge": "SAFE"
    },
    {
        "name": "missing sections debug report",
        "pipeline_output": {
            "example_id": "EX003",
            "question": "Who is the CEO of OpenAI?",
            "original_answer": "Sam Altman is the CEO of OpenAI."
        },
        "report_type": "debug",
        "expected_missing_sections": [
            "temporal_detection",
            "claims",
            "evidence",
            "freshness",
            "verification",
            "outdatedness",
            "correction",
            "risk_label"
        ]
    }
]
```

---

## Prompt for Claude or Codex Agent

You are implementing Skill 10 for a project called TemporalGuard.

TemporalGuard is a time-aware reliability framework for detecting and correcting outdated responses in Large Language Models.

Your task is to implement only the report generation skill.

Create a clean, production-quality Python module that generates dashboard, technical, thesis, and debug reports from TemporalGuard pipeline outputs.

Create:

1. `src/temporalguard/reporting/report_generator.py`
2. `tests/test_report_generator.py`

Use this function signature:

```python
def generate_report(
    pipeline_output: dict,
    report_type: str = "dashboard",
    max_evidence_items: int = 5
) -> dict:
```

The function must return:

```python
{
    "report_id": "...",
    "example_id": None,
    "report_type": "dashboard | technical | thesis | debug",
    "title": "...",
    "executive_summary": "...",
    "final_answer": "...",
    "dashboard_summary": {},
    "pipeline_summary": {},
    "claim_report": [],
    "evidence_report": [],
    "correction_report": {},
    "thesis_summary": {},
    "debug_info": {}
}
```

Implementation requirements:

* Use Python standard library only.
* Do not call an LLM.
* Do not call web search.
* Do not retrieve evidence.
* Do not verify claims.
* Do not correct answers.
* Use only the given pipeline output.
* Support report types:

  * `dashboard`
  * `technical`
  * `thesis`
  * `debug`
* If an unknown report type is passed, default to `dashboard` and add a warning.
* Use corrected answer from `correction.corrected_answer` as final answer when available.
* Use original answer when correction is missing.
* Use risk label output for dashboard summary.
* Combine claim and verification data by `claim_id`.
* Combine evidence and freshness data by `claim_id` and `evidence_id`.
* Limit evidence report to `max_evidence_items`.
* Detect missing pipeline sections.
* Include raw statuses in debug info.
* Keep executive summary concise.
* Create thesis summary using simple deterministic templates.
* Never invent missing values.
* Handle malformed input safely.
* Return JSON-compatible dictionary every time.
* Add unit tests for the provided examples.
* Keep code typed, deterministic, clean, and easy to extend.
* Use the package name `temporalguard`.

Recommended internal helper functions:

```python
_safe_get(data: dict, path: list[str], default=None)
_find_missing_sections(pipeline_output: dict) -> list[str]
_get_raw_statuses(pipeline_output: dict) -> dict
_build_dashboard_summary(pipeline_output: dict) -> dict
_build_pipeline_summary(pipeline_output: dict) -> dict
_build_claim_report(pipeline_output: dict) -> list[dict]
_build_evidence_report(pipeline_output: dict, max_items: int) -> list[dict]
_build_correction_report(pipeline_output: dict) -> dict
_infer_temporal_failure_type(pipeline_output: dict) -> str
_build_thesis_summary(pipeline_output: dict) -> dict
_build_executive_summary(pipeline_output: dict, report_type: str) -> str
```

Important behavior:

* If the pipeline is incomplete, report should still be generated.
* If no correction exists, final answer should be original answer.
* If no evidence exists, evidence_report should be an empty list.
* If claims exist but verification is missing, claim_report should say “not verified.”
* If verification exists but claims are missing, use verification claim text where available.
* If risk label is missing, dashboard badge should be `UNKNOWN`.
* If report type is `debug`, include all missing sections and raw statuses clearly.
* Do not include raw full pipeline output unless needed later as a separate debug option.
* Keep all string fields short and clear.

After implementation:

1. Run tests.
2. Fix all failing tests.
3. Report:

   * files created
   * main logic summary
   * test result
   * assumptions
