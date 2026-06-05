# Skill 02: Claim Extraction

## Purpose

This skill extracts checkable factual claims from an LLM-generated answer.

TemporalGuard cannot verify a full paragraph directly. First, it must break the answer into smaller factual claims that can be checked against fresh or historical evidence.

This skill is the second step in the TemporalGuard pipeline.

It receives:

1. The original user question
2. The LLM answer
3. Optional temporal category from Skill 01

It returns a structured list of factual claims that may need verification.

---

## Core Task

Given a user question and an LLM answer, extract only the factual claims that can be verified.

Do not judge whether the claims are true or false.

Do not retrieve evidence.

Do not correct the answer.

Do not rewrite the final answer.

Only extract claims.

---

## Why This Skill Matters

An LLM answer may contain many parts:

* factual claims
* opinions
* explanations
* examples
* advice
* uncertainty statements
* formatting text

TemporalGuard should not verify everything. It should verify only factual claims, especially claims that may become outdated over time.

Example answer:

```text
Python 3.10 is the latest stable version of Python. It is widely used in machine learning and web development.
```

Extracted claims:

```json
[
  {
    "claim_text": "Python 3.10 is the latest stable version of Python.",
    "claim_type": "software_version",
    "entities": ["Python", "Python 3.10"],
    "temporal_sensitivity": "high"
  },
  {
    "claim_text": "Python is widely used in machine learning and web development.",
    "claim_type": "general_fact",
    "entities": ["Python", "machine learning", "web development"],
    "temporal_sensitivity": "low"
  }
]
```

---

## Inputs

The skill may receive this input:

```json
{
  "question": "What is the latest Python version?",
  "answer": "Python 3.10 is the latest stable version of Python.",
  "temporal_category": "RECENT_ONLY"
}
```

The `temporal_category` field is optional, but if available, use it to prioritize claim extraction.

---

## Required Output Format

Always return valid JSON only.

Do not include markdown.

Do not include explanation outside the JSON.

Use this schema:

```json
{
  "claims": [
    {
      "claim_id": "C1",
      "claim_text": "string",
      "normalized_claim": "string",
      "claim_type": "string",
      "entities": ["string"],
      "temporal_sensitivity": "low | medium | high",
      "requires_verification": true,
      "temporal_anchor": null,
      "evidence_need": "fresh | historical | version_specific | optional",
      "confidence": 0.0
    }
  ],
  "total_claims": 0,
  "needs_verification": true,
  "notes": "short note"
}
```

---

## Field Instructions

### claim_id

Use simple IDs:

```text
C1, C2, C3, ...
```

Do not use random IDs.

---

### claim_text

The original factual claim extracted from the answer.

Keep it short and complete.

Good:

```text
Python 3.10 is the latest stable version of Python.
```

Bad:

```text
Python 3.10
```

---

### normalized_claim

A cleaner version of the claim that is easier to verify.

Example:

Original claim:

```text
Right now, Python 3.10 is the newest stable version.
```

Normalized claim:

```text
Python 3.10 is the latest stable Python version.
```

Do not add new information.

Only simplify wording.

---

### claim_type

Use one of these claim types when possible:

```text
general_fact
current_status
software_version
api_or_library_behavior
company_leadership
law_or_policy
medical_or_scientific_guideline
price_or_market_data
event_result
date_or_deadline
research_claim
statistical_claim
recommendation_claim
historical_fact
definition
other
```

Choose the most specific type.

Examples:

* “Python 3.13 is the latest version” → `software_version`
* “Sam Altman is CEO of OpenAI” → `company_leadership`
* “This visa rule is still active” → `law_or_policy`
* “The model achieved 92% accuracy” → `statistical_claim`
* “The 2018 World Cup was won by France” → `historical_fact`

---

### entities

Extract main named entities or important objects.

Examples:

```json
["Python", "Python 3.10"]
```

```json
["OpenAI", "CEO"]
```

```json
["Canada visa", "student visa rule"]
```

If no clear entity exists, return an empty list.

---

### temporal_sensitivity

Use:

```text
low
medium
high
```

Use `high` when the claim can easily become outdated.

High examples:

* latest version
* current CEO
* active law
* current price
* latest model
* today’s weather
* current visa rule
* medical guideline
* API syntax
* software package support

Use `medium` when the claim may change slowly.

Medium examples:

* “Python is widely used for ML”
* “A policy usually requires X”
* “This framework supports many integrations”

Use `low` when the claim is stable.

Low examples:

* “Binary search divides the search space in half”
* “RAM is volatile memory”
* “The 2018 FIFA World Cup was won by France”

---

### requires_verification

Use `true` for factual claims.

Use `false` only for:

* opinions
* advice without factual content
* subjective statements
* vague non-checkable statements

However, avoid extracting non-checkable statements in the first place.

---

### temporal_anchor

Extract explicit time references from the claim or question.

Examples:

```text
2020
today
current
latest
as of 2026
during COVID-19
Python 3.10
last week
```

Use `null` if no temporal anchor exists.

---

### evidence_need

Use one of:

```text
fresh
historical
version_specific
optional
```

Use `fresh` for current/latest/active claims.

Use `historical` for past-time claims.

Use `version_specific` for software/API/library claims.

Use `optional` for stable claims that can usually be answered directly.

---

### confidence

Return a float between `0.0` and `1.0`.

This is confidence in the extraction quality, not truth.

Suggested values:

* `0.90` to `1.00`: clear factual claim
* `0.70` to `0.89`: likely factual claim
* `0.50` to `0.69`: unclear but useful
* below `0.50`: weak extraction

---

## What Counts as a Claim

Extract statements that assert something about the world.

Examples:

```text
Python 3.10 is the latest stable Python version.
```

```text
OpenAI released GPT-4 in 2023.
```

```text
France won the 2018 FIFA World Cup.
```

```text
The policy requires applicants to submit financial documents.
```

```text
The model achieved 91% accuracy on the test set.
```

---

## What Not to Extract

Do not extract:

### 1. Pure opinions

```text
Python is amazing.
```

### 2. User-facing filler

```text
Sure, here is the answer.
```

### 3. Instructions without factual claim

```text
You should check the official website.
```

### 4. Vague claims

```text
This is very important.
```

### 5. Repeated same claim

If the answer repeats the same fact, extract it once.

---

## Claim Extraction Rules

### Rule 1: Extract atomic claims

Each claim should contain one main idea.

Bad:

```text
Python 3.10 is the latest version and it is used in AI.
```

Good:

```text
Python 3.10 is the latest stable version of Python.
```

```text
Python is used in AI.
```

---

### Rule 2: Prioritize temporal claims

If the answer has many claims, prioritize claims that may become outdated.

Priority order:

1. latest/current/recent claims
2. software/API/library claims
3. law/policy/visa/financial/medical claims
4. company/person role claims
5. event result or deadline claims
6. statistical claims
7. general stable facts

---

### Rule 3: Limit number of extracted claims

To save tokens and context window, extract only the most important claims.

Default maximum:

```text
5 claims
```

If the answer is very short, extract fewer.

If the answer is long, choose the top 5 most verification-worthy claims.

---

### Rule 4: Preserve the original meaning

Do not invent new claims.

Do not add details that were not in the answer.

Do not “fix” the answer.

Do not replace old information with newer information.

This skill extracts, not corrects.

---

### Rule 5: Use the question to understand context

The answer may use pronouns like:

```text
It is still active.
```

Use the question to resolve what “it” means if clear.

Example:

Question:

```text
Is the Canada student visa SDS program still active?
```

Answer:

```text
No, it is no longer active.
```

Extracted claim:

```text
The Canada student visa SDS program is no longer active.
```

---

### Rule 6: Handle uncertainty carefully

If the answer says:

```text
As of my last update, Python 3.10 was the latest version.
```

Extract:

```text
Python 3.10 was the latest version as of the model's last update.
```

Temporal anchor:

```text
model's last update
```

Evidence need:

```text
fresh
```

This type of answer still needs verification.

---

### Rule 7: Treat numbers and dates as important

Claims containing numbers, percentages, dates, deadlines, prices, rankings, or metrics usually need extraction.

Examples:

```text
The model achieved 92% accuracy.
```

```text
The deadline is June 15, 2026.
```

```text
The price is $99.
```

---

## Temporal Sensitivity Examples

### High Sensitivity

```text
The latest Python version is Python 3.10.
```

```text
Sam Altman is the CEO of OpenAI.
```

```text
The policy is still active.
```

```text
The current price of Bitcoin is $60,000.
```

```text
The OpenAI API uses this endpoint.
```

---

### Medium Sensitivity

```text
Python is widely used in machine learning.
```

```text
Many universities require English proficiency proof.
```

```text
RAG systems are commonly used for document question answering.
```

---

### Low Sensitivity

```text
Binary search repeatedly divides the search interval in half.
```

```text
RAM is volatile memory.
```

```text
France won the 2018 FIFA World Cup.
```

---

## Evidence Need Examples

### fresh

Use when the claim depends on the present.

```text
The latest TensorFlow version is 2.x.
```

```text
This visa rule is still active.
```

---

### historical

Use when the claim depends on a past date or period.

```text
In 2020, Python 3.8 was the latest stable version.
```

---

### version_specific

Use when the claim depends on software/API/library version.

```text
In pandas 2.0, this method is deprecated.
```

---

### optional

Use when the claim is stable.

```text
Binary search has logarithmic time complexity.
```

---

## Output Examples

### Example 1

Input:

```json
{
  "question": "What is the latest Python version?",
  "answer": "Python 3.10 is the latest stable version of Python.",
  "temporal_category": "RECENT_ONLY"
}
```

Output:

```json
{
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
  ],
  "total_claims": 1,
  "needs_verification": true,
  "notes": "One high-sensitivity software version claim extracted."
}
```

---

### Example 2

Input:

```json
{
  "question": "Who was the president of the USA in 2016?",
  "answer": "Barack Obama was the president of the United States in 2016.",
  "temporal_category": "HISTORICAL"
}
```

Output:

```json
{
  "claims": [
    {
      "claim_id": "C1",
      "claim_text": "Barack Obama was the president of the United States in 2016.",
      "normalized_claim": "Barack Obama was the U.S. president in 2016.",
      "claim_type": "historical_fact",
      "entities": ["Barack Obama", "United States", "president"],
      "temporal_sensitivity": "low",
      "requires_verification": true,
      "temporal_anchor": "2016",
      "evidence_need": "historical",
      "confidence": 0.96
    }
  ],
  "total_claims": 1,
  "needs_verification": true,
  "notes": "One historical factual claim extracted."
}
```

---

### Example 3

Input:

```json
{
  "question": "What is binary search?",
  "answer": "Binary search is an algorithm that repeatedly divides a sorted search space in half to find a target value.",
  "temporal_category": "STATIC"
}
```

Output:

```json
{
  "claims": [
    {
      "claim_id": "C1",
      "claim_text": "Binary search is an algorithm that repeatedly divides a sorted search space in half to find a target value.",
      "normalized_claim": "Binary search finds a target value by repeatedly halving a sorted search space.",
      "claim_type": "definition",
      "entities": ["binary search"],
      "temporal_sensitivity": "low",
      "requires_verification": true,
      "temporal_anchor": null,
      "evidence_need": "optional",
      "confidence": 0.95
    }
  ],
  "total_claims": 1,
  "needs_verification": false,
  "notes": "Stable educational definition; verification is optional."
}
```

---

### Example 4

Input:

```json
{
  "question": "Is the Canada student visa SDS program still active?",
  "answer": "No, the Canada student visa SDS program is no longer active.",
  "temporal_category": "RECENT_ONLY"
}
```

Output:

```json
{
  "claims": [
    {
      "claim_id": "C1",
      "claim_text": "The Canada student visa SDS program is no longer active.",
      "normalized_claim": "The Canada student visa SDS program is not currently active.",
      "claim_type": "law_or_policy",
      "entities": ["Canada student visa SDS program"],
      "temporal_sensitivity": "high",
      "requires_verification": true,
      "temporal_anchor": "current",
      "evidence_need": "fresh",
      "confidence": 0.94
    }
  ],
  "total_claims": 1,
  "needs_verification": true,
  "notes": "One high-sensitivity policy status claim extracted."
}
```

---

### Example 5

Input:

```json
{
  "question": "Explain why Python is useful.",
  "answer": "Python is popular because it has simple syntax, many libraries, and strong support for data science.",
  "temporal_category": "STATIC"
}
```

Output:

```json
{
  "claims": [
    {
      "claim_id": "C1",
      "claim_text": "Python has simple syntax.",
      "normalized_claim": "Python has simple syntax.",
      "claim_type": "general_fact",
      "entities": ["Python"],
      "temporal_sensitivity": "low",
      "requires_verification": true,
      "temporal_anchor": null,
      "evidence_need": "optional",
      "confidence": 0.88
    },
    {
      "claim_id": "C2",
      "claim_text": "Python has many libraries.",
      "normalized_claim": "Python has many libraries.",
      "claim_type": "general_fact",
      "entities": ["Python"],
      "temporal_sensitivity": "medium",
      "requires_verification": true,
      "temporal_anchor": null,
      "evidence_need": "optional",
      "confidence": 0.86
    },
    {
      "claim_id": "C3",
      "claim_text": "Python has strong support for data science.",
      "normalized_claim": "Python has strong support for data science.",
      "claim_type": "general_fact",
      "entities": ["Python", "data science"],
      "temporal_sensitivity": "medium",
      "requires_verification": true,
      "temporal_anchor": null,
      "evidence_need": "optional",
      "confidence": 0.85
    }
  ],
  "total_claims": 3,
  "needs_verification": false,
  "notes": "Stable general claims extracted; verification is optional."
}
```

---

## Implementation Notes for AI Coding Agents

Build this skill as a lightweight, reusable module.

Do not create a large agent chain for this step.

Do not call web search inside this skill.

Do not correct claims.

Do not verify claims.

Do not use long prompts in the code.

This skill should only extract structured claims from an answer.

Recommended implementation:

* Create a Python module such as `claim_extractor.py`
* Create a function named `extract_claims(question: str, answer: str, temporal_category: str | None = None, max_claims: int = 5) -> dict`
* Use lightweight sentence splitting first
* Use rule-based claim typing where possible
* Optionally support an LLM-based extractor later, but keep it disabled by default
* Keep outputs deterministic as much as possible
* Return strict JSON-compatible Python dictionary
* Add unit tests for all examples
* Add error handling for empty or non-string input

---

## Suggested Python Interface

Use this interface:

```python
def extract_claims(
    question: str,
    answer: str,
    temporal_category: str | None = None,
    max_claims: int = 5
) -> dict:
    """
    Extract checkable factual claims from an LLM answer.

    Args:
        question: Original user question.
        answer: LLM-generated answer.
        temporal_category: Optional category from Skill 01.
        max_claims: Maximum number of claims to extract.

    Returns:
        dict with:
            claims
            total_claims
            needs_verification
            notes
    """
```

---

## Expected Behavior

The extractor should be fast, cheap, and reliable.

It must not waste tokens.

It must not call an LLM by default.

It must not perform web search.

It must not generate final user answers.

It only extracts factual claims for later verification.

---

## Quality Requirements

The implementation must satisfy these requirements:

1. Return valid JSON-compatible dictionary every time.
2. Extract atomic factual claims where possible.
3. Avoid extracting filler, opinion, greetings, and repeated claims.
4. Limit claims to `max_claims`.
5. Prioritize temporally sensitive claims.
6. Detect major claim types correctly.
7. Extract key entities using simple rules.
8. Detect temporal anchors such as years, “current,” “latest,” and version numbers.
9. Assign correct evidence need: `fresh`, `historical`, `version_specific`, or `optional`.
10. Include unit tests.
11. Use no external dependencies unless already used in the project.
12. Keep the module reusable for the full TemporalGuard pipeline.
13. Keep logic simple enough to debug.
14. Avoid heavy context usage and unnecessary LLM calls.

---

## Test Cases

Use these minimum test cases:

```python
test_cases = [
    {
        "question": "What is the latest Python version?",
        "answer": "Python 3.10 is the latest stable version of Python.",
        "temporal_category": "RECENT_ONLY",
        "expected_claim_type": "software_version",
        "expected_evidence_need": "fresh"
    },
    {
        "question": "Who was the president of the USA in 2016?",
        "answer": "Barack Obama was the president of the United States in 2016.",
        "temporal_category": "HISTORICAL",
        "expected_claim_type": "historical_fact",
        "expected_evidence_need": "historical"
    },
    {
        "question": "What is binary search?",
        "answer": "Binary search is an algorithm that repeatedly divides a sorted search space in half to find a target value.",
        "temporal_category": "STATIC",
        "expected_claim_type": "definition",
        "expected_evidence_need": "optional"
    },
    {
        "question": "Is the Canada student visa SDS program still active?",
        "answer": "No, the Canada student visa SDS program is no longer active.",
        "temporal_category": "RECENT_ONLY",
        "expected_claim_type": "law_or_policy",
        "expected_evidence_need": "fresh"
    },
    {
        "question": "How do I use the OpenAI API in Python?",
        "answer": "The OpenAI Python SDK lets developers call OpenAI models from Python applications.",
        "temporal_category": "VERSION_DEPENDENT",
        "expected_claim_type": "api_or_library_behavior",
        "expected_evidence_need": "version_specific"
    },
    {
        "question": "What is the model result?",
        "answer": "The model achieved 92% accuracy and 0.89 F1-score on the test set.",
        "temporal_category": "STATIC",
        "expected_claim_type": "statistical_claim",
        "expected_evidence_need": "optional"
    },
    {
        "question": "Tell me something nice.",
        "answer": "Sure, I hope you have a wonderful day.",
        "temporal_category": "STATIC",
        "expected_total_claims": 0
    }
]
```

---

## Prompt for Claude or Codex Agent

You are implementing Skill 02 for a project called TemporalGuard.

TemporalGuard is a time-aware reliability framework for detecting and correcting outdated responses in Large Language Models.

Your task is to implement only the claim extraction skill.

Create a clean, production-quality Python module that extracts checkable factual claims from an LLM answer.

Create:

1. `src/temporalguard/skills/claim_extractor.py`
2. `tests/test_claim_extractor.py`

Use this function signature:

```python
def extract_claims(
    question: str,
    answer: str,
    temporal_category: str | None = None,
    max_claims: int = 5
) -> dict:
```

The function must return:

```python
{
    "claims": [
        {
            "claim_id": "C1",
            "claim_text": "...",
            "normalized_claim": "...",
            "claim_type": "...",
            "entities": ["..."],
            "temporal_sensitivity": "low | medium | high",
            "requires_verification": True,
            "temporal_anchor": None,
            "evidence_need": "fresh | historical | version_specific | optional",
            "confidence": 0.0
        }
    ],
    "total_claims": 0,
    "needs_verification": True,
    "notes": "short note"
}
```

Implementation requirements:

* Use Python standard library where possible.
* Do not call web search.
* Do not verify whether claims are true.
* Do not correct claims.
* Do not generate final answers.
* Do not call an LLM by default.
* Use lightweight sentence splitting.
* Remove filler sentences such as “Sure,” “Here is the answer,” and “I hope this helps.”
* Extract only factual claims.
* Split compound factual sentences into smaller claims when simple.
* Avoid repeated duplicate claims.
* Limit output to `max_claims`.
* Prioritize claims that are temporally sensitive.
* Detect claim types using rules and keywords.
* Detect entities with simple heuristics such as capitalized terms, known technologies, organizations, dates, and version strings.
* Detect temporal anchors such as years, dates, “latest,” “current,” “today,” “as of,” and version numbers.
* Assign evidence need:

  * `fresh` for current/latest/active claims
  * `historical` for past-time claims
  * `version_specific` for software/API/library claims
  * `optional` for stable claims
* Handle empty string and invalid input safely.
* Add unit tests for all provided examples.
* Keep the code typed, clean, and easy to extend.
* Do not over-engineer.
* Do not add unnecessary dependencies.
* Do not use long prompts inside the code.
* Use the package name `temporalguard`.

Recommended internal helper functions:

```python
_split_sentences(text: str) -> list[str]
_is_filler(sentence: str) -> bool
_split_compound_claims(sentence: str) -> list[str]
_classify_claim_type(claim: str, question: str, temporal_category: str | None) -> str
_extract_entities(claim: str, question: str) -> list[str]
_extract_temporal_anchor(claim: str, question: str) -> str | None
_assign_temporal_sensitivity(claim_type: str, claim: str, temporal_category: str | None) -> str
_assign_evidence_need(claim_type: str, claim: str, temporal_category: str | None, temporal_anchor: str | None) -> str
_normalize_claim(claim: str) -> str
```

Important behavior:

* If the answer contains no factual claims, return:

```python
{
    "claims": [],
    "total_claims": 0,
    "needs_verification": False,
    "notes": "No checkable factual claims extracted."
}
```

* If the temporal category is `RECENT_ONLY`, `TIME_SENSITIVE`, or `VERSION_DEPENDENT`, prioritize claims with high temporal sensitivity.
* If the temporal category is `HISTORICAL`, preserve the historical year/date in the extracted claim.
* If max_claims is less than 1, treat it as 1.
* If max_claims is very large, cap internally at 10 to protect context size.

After implementation:

1. Run tests.
2. Fix all failing tests.
3. Report:

   * files created
   * main logic summary
   * test result
   * assumptions
