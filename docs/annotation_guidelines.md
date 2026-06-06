# TemporalGuard Benchmark Annotation Guidelines

These guidelines define how human annotators should label TemporalGuard
benchmark examples for thesis evaluation. The goal is consistency: every row
should describe the user question, the original answer, the gold temporal
decision, the gold evidence value, and the expected safety label.

## Required Fields

Each benchmark example should include:

- `example_id`: Stable unique id, such as `EX001`.
- `question`: The user question.
- `original_answer`: The stale, correct, risky, or static answer being tested.
- `gold_temporal_category`: Gold Skill 01 category.
- `gold_outdatedness_status`: Gold answer-level Skill 06 status.
- `gold_requires_correction`: Boolean correction requirement.
- `gold_evidence_value`: Correct value or evidence conclusion when applicable.
- `gold_source_url`: Authoritative source URL when evidence is required.
- `gold_source_date`: Publication, access, or effective date for the evidence.
- `gold_final_risk_label`: Gold Skill 08 risk label.
- `domain`: Benchmark domain.
- `difficulty`: Annotation difficulty.
- `high_risk_domain`: Boolean high-risk flag.
- `source_notes`: Short note explaining the evidence choice.
- `annotation_status`: Review status.

## Temporal Category Labels

- `STATIC`: Stable educational or conceptual knowledge.
- `TIME_SENSITIVE`: Answer can change over time, even if the question does not say latest/current.
- `RECENT_ONLY`: The question explicitly asks for latest, current, today, now, still active, or similar current information.
- `HISTORICAL`: The question asks about a specific past date, year, period, or event.
- `VERSION_DEPENDENT`: The answer depends on a software, API, model, library, or documentation version.
- `UNKNOWN`: The question is ambiguous and cannot be safely classified.

Label by the question context first. For example, "latest Python version" is
`RECENT_ONLY`; "How do I use the OpenAI API in Python?" is
`VERSION_DEPENDENT`; "What is binary search?" is `STATIC`.

## Outdatedness Status Labels

- `NOT_OUTDATED`: The answer is supported and not temporally stale.
- `OUTDATED`: The main answer gives an old value that has been replaced.
- `PARTIALLY_OUTDATED`: Some important claims are outdated, but the whole answer is not completely wrong.
- `CONTRADICTED`: The answer is wrong for the requested time or context.
- `UNVERIFIED_RISKY`: The answer cannot be trusted because evidence is missing or insufficient, especially for high-risk/current claims.
- `NOT_ENOUGH_INFORMATION`: There is not enough information to judge the factual answer.
- `NOT_APPLICABLE`: Temporal verification does not apply, such as creative writing or no factual claim.

Do not label an example as `OUTDATED` without evidence that shows the original
answer is old. If the evidence is missing, use `UNVERIFIED_RISKY` or
`NOT_ENOUGH_INFORMATION`.

## Evidence Rules

For `OUTDATED`, `PARTIALLY_OUTDATED`, and `CONTRADICTED`, annotators must record:

- `gold_evidence_value`
- `gold_source_url`
- `gold_source_date`

Use official or authoritative evidence where possible:

- Software versions: official release pages or documentation.
- Company leadership: official company pages or trusted filings.
- Laws and policies: government, regulator, or official institution pages.
- Medical/science: official guidelines, papers, or recognized medical bodies.
- Sports and historical events: official event pages or authoritative references.

The evidence value should be concise. Example: `Python 3.13.5`, `Germany`,
`Sam Altman`, or `insufficient official evidence`.

## Correction Requirement

Set `gold_requires_correction` to `true` when the original answer should be
changed, corrected, or replaced with an uncertainty warning.

Usually `true`:

- `OUTDATED`
- `PARTIALLY_OUTDATED`
- `CONTRADICTED`
- high-risk `UNVERIFIED_RISKY`

Usually `false`:

- `NOT_OUTDATED`
- `NOT_APPLICABLE`

Use reviewer judgment for `NOT_ENOUGH_INFORMATION`.

## Final Risk Label

Allowed labels:

- `safe`
- `low_risk`
- `medium_risk`
- `high_risk`
- `critical_risk`
- `unknown_risk`

High-risk domains include legal, visa, policy, medical, finance, safety,
regulation, and similar real-world decision areas. If evidence is insufficient
for a high-risk example, use `critical_risk` or `unknown_risk`, not `safe`,
`low_risk`, or `medium_risk`.

## Domains

Use one of:

- `software`
- `company_leadership`
- `law_policy`
- `medical_science`
- `finance_market`
- `sports_events`
- `academic_research`
- `historical`
- `static_education`
- `other`

## Difficulty

- `easy`: One clear claim and obvious evidence.
- `medium`: Requires careful evidence reading or mild temporal ambiguity.
- `hard`: Multiple claims, high-risk status, or nuanced time context.
- `adversarial`: Designed to expose edge cases, ambiguity, or misleading phrasing.

## Annotation Status

- `draft`: Initial annotation not yet reviewed.
- `verified`: Evidence and labels have been checked.
- `needs_review`: Annotator is uncertain or evidence is incomplete.
- `rejected`: Example should not be used in benchmark evaluation.

Only mark an example as `verified` after the evidence value, source URL, source
date, labels, and high-risk flag have been reviewed.

## Review Checklist

1. Does the question context match the temporal category?
2. Does the original answer contain the annotated claim?
3. Are all labels from the allowed label set?
4. If the answer is outdated or contradicted, are evidence value, source URL, and source date recorded?
5. Is `gold_requires_correction` consistent with the outdatedness status?
6. Is the high-risk flag correct for legal, medical, visa, finance, policy, safety, and regulatory examples?
7. Is the final risk label strict enough for high-risk examples?
8. Is the annotation status honest about review completeness?

## Example

```json
{
  "example_id": "EX001",
  "question": "What is the latest Python version?",
  "original_answer": "Python 3.10 is the latest stable version.",
  "gold_temporal_category": "RECENT_ONLY",
  "gold_outdatedness_status": "OUTDATED",
  "gold_requires_correction": true,
  "gold_evidence_value": "Python 3.13.5",
  "gold_source_url": "https://www.python.org/downloads/",
  "gold_source_date": "2026-06-06",
  "gold_final_risk_label": "medium_risk",
  "domain": "software",
  "difficulty": "easy",
  "high_risk_domain": false,
  "source_notes": "Official Python downloads page checked manually.",
  "annotation_status": "verified"
}
```
