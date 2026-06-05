# Skill 01: Temporal Question Detection

## Purpose

This skill determines whether a user question is time-sensitive or not.

TemporalGuard must not treat all questions equally. Some questions have answers that rarely change, while other questions depend strongly on the current date, recent evidence, software versions, laws, leadership changes, policies, prices, events, or scientific updates.

This skill is the first gatekeeper in the TemporalGuard pipeline. It decides whether the system needs fresh evidence checking or whether the question can be answered using normal static knowledge.

---

## Core Task

Given a user question, classify it into one temporal category:

1. `STATIC`
2. `TIME_SENSITIVE`
3. `RECENT_ONLY`
4. `HISTORICAL`
5. `VERSION_DEPENDENT`
6. `UNKNOWN`

The output must be concise, structured, and machine-readable.

---

## Category Definitions

### 1. STATIC

Use `STATIC` when the answer is generally stable and does not usually change over time.

Examples:

* What is binary search?
* What is Newton's second law?
* What is a database?
* What is the capital of France?
* Explain supervised learning.
* What is photosynthesis?

Important note:

Some facts can technically change, but if the expected answer is generally stable for educational or conceptual purposes, classify as `STATIC`.

---

### 2. TIME_SENSITIVE

Use `TIME_SENSITIVE` when the answer may change over time and should be checked against fresh evidence.

Examples:

* Who is the CEO of OpenAI?
* What is the current inflation rate in Bangladesh?
* What is the latest version of Python?
* Is this law still active?
* What are the current visa rules for Canada?
* Which company currently owns X?
* What is the newest iPhone model?
* Is this medicine still recommended?
* What are the current Kaggle competition rules?

Use this category when a question involves:

* current status
* latest information
* ongoing rules
* active policies
* recent events
* company leadership
* product versions
* prices
* market data
* legal or regulatory status
* software/library updates
* medical/scientific guideline updates

---

### 3. RECENT_ONLY

Use `RECENT_ONLY` when the question explicitly asks for current, latest, newest, today’s, this week’s, this month’s, this year’s, or real-time information.

Examples:

* What is the latest OpenAI model?
* What happened today in AI news?
* What is Bitcoin price now?
* What is the weather today?
* Who won the latest match?
* What are the newest papers about temporal LLMs?
* Find recent research on RAG evaluation.

This category means fresh retrieval is mandatory.

Difference from `TIME_SENSITIVE`:

`TIME_SENSITIVE` means the answer may change.

`RECENT_ONLY` means the user explicitly wants fresh/current information.

---

### 4. HISTORICAL

Use `HISTORICAL` when the question asks about a specific past time, past event, past fact, or historical period.

Examples:

* Who was the CEO of Microsoft in 2010?
* What were the COVID-19 rules in Bangladesh in 2021?
* What was the Python latest version in 2020?
* Who won the 2018 FIFA World Cup?
* What did the 2020 policy say?

This category still needs temporal care, but the system should search evidence from the requested time period, not only the present.

---

### 5. VERSION_DEPENDENT

Use `VERSION_DEPENDENT` when the answer depends on a specific version of a tool, software, API, library, model, dataset, documentation, or framework.

Examples:

* How do I use the OpenAI API in Python?
* Does LangChain support this feature?
* What is the syntax for TensorFlow 2.15?
* How do I install CUDA for PyTorch?
* Is this function deprecated in pandas?
* Which Python versions support this package?

If the user provides a version, preserve it.

If the user does not provide a version but the topic is software/API/library related, classify as `VERSION_DEPENDENT` or `TIME_SENSITIVE`, depending on the wording.

Prefer `VERSION_DEPENDENT` when the main risk is software/API version mismatch.

---

### 6. UNKNOWN

Use `UNKNOWN` when the temporal status cannot be confidently determined from the question.

Examples:

* Tell me about Mercury.
* Explain Apple.
* What about Java?
* Is it good?
* Can I use this?

Use `UNKNOWN` when the question is too short, ambiguous, or missing the real object being asked about.

---

## Decision Rules

Follow these rules carefully.

### Rule 1: Current words strongly indicate temporal sensitivity

If the question contains words like:

* current
* latest
* newest
* today
* now
* recent
* currently
* updated
* still
* active
* changed
* new
* this year
* this month
* this week
* as of now

Then classify as `RECENT_ONLY` or `TIME_SENSITIVE`.

Use `RECENT_ONLY` if the user explicitly asks for fresh/current information.

Use `TIME_SENSITIVE` if the question only implies change over time.

---

### Rule 2: Software and API questions are often version-dependent

Questions about software, packages, frameworks, APIs, models, tools, dependencies, or installation should usually be classified as `VERSION_DEPENDENT`.

Examples:

* OpenAI API
* LangChain
* LlamaIndex
* TensorFlow
* PyTorch
* pandas
* NumPy
* CUDA
* Python
* Node.js
* React
* Next.js
* Streamlit
* Hugging Face
* vLLM
* Docker

---

### Rule 3: Medical, legal, financial, visa, policy, and regulation questions are time-sensitive

Even if the user does not say “current,” classify these as `TIME_SENSITIVE` because outdated answers can cause harm.

Examples:

* Is this medicine safe?
* What are the visa requirements?
* What tax rule applies?
* What is the interest rate?
* Can I legally do this?
* What is the university policy?
* What is the Amazon FBA policy?

---

### Rule 4: Historical questions must preserve the requested time

If the user asks about a specific year, date, era, or past condition, classify as `HISTORICAL`.

Extract the time reference clearly.

Example:

Question:

“What was the latest Python version in 2020?”

Output category:

`HISTORICAL`

Temporal anchor:

`2020`

---

### Rule 5: Educational definitions are usually static

Basic educational questions are usually `STATIC`.

Examples:

* What is RAM?
* What is ROM?
* What is machine learning?
* Explain binary search.
* What is a neural network?

Do not over-classify simple learning questions as time-sensitive unless the question asks for the latest/current state.

---

### Rule 6: When uncertain, choose the safer category

If a question could be static or time-sensitive, choose the category that protects reliability.

Priority order:

1. `RECENT_ONLY`
2. `VERSION_DEPENDENT`
3. `TIME_SENSITIVE`
4. `HISTORICAL`
5. `STATIC`
6. `UNKNOWN`

---

## Required Output Format

Always return valid JSON only.

Do not include markdown.

Do not include explanation outside the JSON.

Use this schema:

{
"temporal_category": "STATIC | TIME_SENSITIVE | RECENT_ONLY | HISTORICAL | VERSION_DEPENDENT | UNKNOWN",
"needs_fresh_evidence": true,
"confidence": 0.0,
"reason": "short reason",
"temporal_signals": ["signal_1", "signal_2"],
"temporal_anchor": null,
"recommended_next_action": "answer_directly | retrieve_fresh_evidence | retrieve_historical_evidence | ask_clarifying_question"
}

---

## Field Instructions

### temporal_category

Must be exactly one of:

* `STATIC`
* `TIME_SENSITIVE`
* `RECENT_ONLY`
* `HISTORICAL`
* `VERSION_DEPENDENT`
* `UNKNOWN`

---

### needs_fresh_evidence

Use `true` for:

* `TIME_SENSITIVE`
* `RECENT_ONLY`
* `VERSION_DEPENDENT`

Usually use `true` for `HISTORICAL`, because historical claims still need date-matched evidence.

Use `false` for simple `STATIC` questions.

Use `true` for `UNKNOWN` if answering without clarification may be risky.

---

### confidence

Return a float between `0.0` and `1.0`.

Suggested values:

* `0.90` to `1.00`: very clear category
* `0.70` to `0.89`: likely category
* `0.50` to `0.69`: uncertain but usable
* below `0.50`: very uncertain

---

### reason

Keep this short.

Good example:

"The question asks for the latest software version, so the answer may change over time."

Bad example:

"This is temporal because many things happen in the world and therefore all answers may change."

---

### temporal_signals

List the words or concepts that caused the classification.

Examples:

* `latest`
* `current`
* `CEO`
* `software version`
* `law`
* `policy`
* `API`
* `2020`
* `today`
* `price`

If no signal exists, return an empty list.

---

### temporal_anchor

Use this field for a date, year, time period, version, or explicit temporal condition.

Examples:

* `"2020"`
* `"as of today"`
* `"Python 3.10"`
* `"during COVID-19"`
* `"current"`
* `"last week"`

Use `null` if no anchor is found.

---

### recommended_next_action

Use one of:

* `answer_directly`
* `retrieve_fresh_evidence`
* `retrieve_historical_evidence`
* `ask_clarifying_question`

Use `answer_directly` for `STATIC`.

Use `retrieve_fresh_evidence` for `TIME_SENSITIVE`, `RECENT_ONLY`, and `VERSION_DEPENDENT`.

Use `retrieve_historical_evidence` for `HISTORICAL`.

Use `ask_clarifying_question` for `UNKNOWN` when the question is too unclear.

---

## Examples

### Example 1

Input:

What is binary search?

Output:

{
"temporal_category": "STATIC",
"needs_fresh_evidence": false,
"confidence": 0.95,
"reason": "This is a stable educational concept.",
"temporal_signals": [],
"temporal_anchor": null,
"recommended_next_action": "answer_directly"
}

---

### Example 2

Input:

Who is the CEO of OpenAI?

Output:

{
"temporal_category": "TIME_SENSITIVE",
"needs_fresh_evidence": true,
"confidence": 0.95,
"reason": "Company leadership can change over time.",
"temporal_signals": ["CEO", "company leadership"],
"temporal_anchor": "current",
"recommended_next_action": "retrieve_fresh_evidence"
}

---

### Example 3

Input:

What is the latest Python version?

Output:

{
"temporal_category": "RECENT_ONLY",
"needs_fresh_evidence": true,
"confidence": 0.98,
"reason": "The question explicitly asks for the latest software version.",
"temporal_signals": ["latest", "Python version"],
"temporal_anchor": "latest",
"recommended_next_action": "retrieve_fresh_evidence"
}

---

### Example 4

Input:

What was the latest Python version in 2020?

Output:

{
"temporal_category": "HISTORICAL",
"needs_fresh_evidence": true,
"confidence": 0.96,
"reason": "The question asks about a fact at a specific past time.",
"temporal_signals": ["latest", "Python version", "2020"],
"temporal_anchor": "2020",
"recommended_next_action": "retrieve_historical_evidence"
}

---

### Example 5

Input:

How do I use the OpenAI API in Python?

Output:

{
"temporal_category": "VERSION_DEPENDENT",
"needs_fresh_evidence": true,
"confidence": 0.90,
"reason": "API usage can change across versions and documentation updates.",
"temporal_signals": ["OpenAI API", "Python", "API"],
"temporal_anchor": null,
"recommended_next_action": "retrieve_fresh_evidence"
}

---

### Example 6

Input:

Is this visa rule still active?

Output:

{
"temporal_category": "RECENT_ONLY",
"needs_fresh_evidence": true,
"confidence": 0.98,
"reason": "The question asks whether a rule is still active, which requires current verification.",
"temporal_signals": ["visa rule", "still active"],
"temporal_anchor": "current",
"recommended_next_action": "retrieve_fresh_evidence"
}

---

### Example 7

Input:

Tell me about Apple.

Output:

{
"temporal_category": "UNKNOWN",
"needs_fresh_evidence": true,
"confidence": 0.45,
"reason": "The question is ambiguous because Apple may refer to a company, fruit, product, or topic.",
"temporal_signals": [],
"temporal_anchor": null,
"recommended_next_action": "ask_clarifying_question"
}

---

## Implementation Notes for AI Coding Agents

Build this skill as a lightweight module.

Do not create a large agent chain for this step.

Do not use long context memory.

Do not call web search inside this skill.

This skill should only classify the question.

Fresh evidence retrieval happens later in Skill 03.

Recommended implementation:

* Create a Python module such as `temporal_question_detector.py`
* Create a function named `detect_temporal_category(question: str) -> dict`
* Use a hybrid approach:

  1. rule-based keyword detection first
  2. optional LLM fallback only if the rule-based confidence is low
* Keep outputs deterministic as much as possible
* Return strict JSON-compatible Python dictionary
* Add unit tests for all categories
* Add clear error handling for empty or non-string input

---

## Suggested Python Interface

Use this interface:

```python
def detect_temporal_category(question: str) -> dict:
    """
    Classify a user question into a temporal category.

    Args:
        question: User question as a string.

    Returns:
        dict with:
            temporal_category
            needs_fresh_evidence
            confidence
            reason
            temporal_signals
            temporal_anchor
            recommended_next_action
    """
```

---

## Expected Behavior

The detector should be fast, cheap, and reliable.

It must not waste tokens.

It must not call an LLM for every question.

It must not perform web search.

It must not generate final answers.

It only decides whether TemporalGuard should continue with evidence retrieval.

---

## Quality Requirements

The implementation must satisfy these requirements:

1. Correctly classify at least 90% of simple test cases.
2. Return valid JSON-compatible dictionary every time.
3. Handle empty questions safely.
4. Avoid unnecessary token usage.
5. Avoid external API calls by default.
6. Include unit tests.
7. Keep the module reusable.
8. Keep the logic easy to understand.
9. Allow future improvement without rewriting the whole file.
10. Support integration with the full TemporalGuard pipeline.

---

## Test Cases

Use these minimum test cases:

```python
test_cases = [
    ("What is machine learning?", "STATIC"),
    ("Explain binary search in easy words.", "STATIC"),
    ("Who is the CEO of Microsoft?", "TIME_SENSITIVE"),
    ("What is the latest Python version?", "RECENT_ONLY"),
    ("What happened in AI today?", "RECENT_ONLY"),
    ("What was the latest Python version in 2020?", "HISTORICAL"),
    ("Who was the president of USA in 2016?", "HISTORICAL"),
    ("How do I use the OpenAI API in Python?", "VERSION_DEPENDENT"),
    ("Is this pandas function deprecated?", "VERSION_DEPENDENT"),
    ("Is this visa rule still active?", "RECENT_ONLY"),
    ("What is the current inflation rate?", "RECENT_ONLY"),
    ("Tell me about Apple.", "UNKNOWN"),
]
```

---

## Prompt for Claude or Codex Agent

You are implementing Skill 01 for a project called TemporalGuard.

TemporalGuard is a time-aware reliability framework for detecting and correcting outdated responses in Large Language Models.

Your task is to implement only the temporal question detection skill.

Create a clean, production-quality Python module that classifies a user question into one of these categories:

* STATIC
* TIME_SENSITIVE
* RECENT_ONLY
* HISTORICAL
* VERSION_DEPENDENT
* UNKNOWN

The module must not call web search.
The module must not generate final answers.
The module must not use unnecessary LLM calls.
The module must be lightweight and deterministic.

Use rule-based detection first. Add optional LLM fallback only as a clearly separated function or placeholder, but keep it disabled by default.

Create:

1. `src/temporalgard/skills/temporal_question_detector.py`
2. `tests/test_temporal_question_detector.py`

Use this function signature:

```python
def detect_temporal_category(question: str) -> dict:
```

The function must return:

```python
{
    "temporal_category": "...",
    "needs_fresh_evidence": true_or_false,
    "confidence": 0.0_to_1.0,
    "reason": "short reason",
    "temporal_signals": ["..."],
    "temporal_anchor": None_or_string,
    "recommended_next_action": "answer_directly | retrieve_fresh_evidence | retrieve_historical_evidence | ask_clarifying_question"
}
```

Implementation requirements:

* Use Python standard library only if possible.
* Use regex for keyword and date detection.
* Detect explicit recency words like latest, current, today, now, recent, updated, still active.
* Detect historical anchors like years, dates, “in 2020,” “during 2021,” “before 2019,” “after 2022.”
* Detect version-dependent topics such as API, Python, pandas, PyTorch, TensorFlow, LangChain, LlamaIndex, CUDA, Hugging Face, Docker, React, Next.js, Streamlit, OpenAI API.
* Detect high-risk time-sensitive domains such as law, visa, policy, finance, medical guideline, regulation, price, tax, university admission, company leadership.
* Classify simple educational questions as STATIC.
* Return UNKNOWN for very ambiguous short questions like “Apple,” “Java,” “Mercury,” or “Tell me about Apple.”
* Handle empty string and invalid input safely.
* Add full unit tests for the provided examples.
* Keep code clean, typed, and easy to extend.
* Do not over-engineer.
* Do not add unnecessary dependencies.
* Do not create a large agent system.
* Do not use long prompts inside the code.

Important project path note:

Use the package name `temporalguard`, not `temporalgard`, unless the existing project already uses another name.

After implementation, run tests and fix issues until all pass.

Final output from the coding agent should include:

* Files created
* Main logic summary
* Test result
* Any assumptions
