# Skill 12: LLM Answer Generation

## Purpose

This skill generates the original base LLM answer that TemporalGuard will later check.

TemporalGuard needs a base answer before it can detect outdatedness. This answer may come from OpenAI, Gemini, Claude, Ollama, Hugging Face, or a manually provided answer.

This skill creates a controlled interface for generating base answers without locking the project to one model provider.

---

## Core Task

Create a lightweight LLM answer generation module that can:

1. Accept a user question.
2. Use a provider interface to generate an answer.
3. Return structured metadata.
4. Fail safely if no provider is configured.
5. Avoid long prompts and unnecessary token usage.

---

## Required Output Format

Return JSON-compatible dictionary:

```json
{
  "question": "string",
  "answer": "string",
  "model_name": "string or null",
  "provider": "string or null",
  "generated_at": "ISO timestamp",
  "status": "success | failed | skipped",
  "usage": {
    "prompt_tokens": null,
    "completion_tokens": null,
    "total_tokens": null
  },
  "warnings": [],
  "errors": []
}
```

---

## LLM Provider Interface

Use a simple provider interface:

```python
class LLMProvider:
    def generate(self, prompt: str, **kwargs) -> dict:
        raise NotImplementedError
```

Expected provider response:

```python
{
    "answer": "...",
    "model_name": "...",
    "provider": "...",
    "usage": {
        "prompt_tokens": None,
        "completion_tokens": None,
        "total_tokens": None
    }
}
```

---

## Prompt Rules

Default prompt style:

```text
Answer the user question clearly and directly. Keep the answer concise. Do not add citations unless asked.
Question: {question}
```

Important:

- Do not ask the model to verify freshness.
- Do not ask the model to use web.
- Do not ask the model to self-correct.
- TemporalGuard will do checking later.

---

## Suggested Python Interface

```python
def generate_base_answer(
    question: str,
    llm_provider=None,
    prompt_template: str | None = None,
    max_tokens: int = 512
) -> dict:
    """
    Generate the original LLM answer for TemporalGuard checking.
    """
```

---

## Recommended Project Files

Create:

```text
src/temporalguard/llm/answer_generator.py
tests/test_answer_generator.py
```

---

## Rules

1. If `llm_provider` is missing, return failed status, not exception.
2. If question is empty, return failed status.
3. Keep default answer generation short.
4. No web search.
5. No evidence retrieval.
6. No outdatedness detection here.
7. Support mock provider in tests.
8. Avoid provider-specific code in the core module.

---

## Prompt for Claude or Codex Agent

You are implementing Skill 12 for TemporalGuard.

Read `skills/12_llm_answer_generation.md` carefully and implement the LLM answer generation module only.

Create:

1. `src/temporalguard/llm/answer_generator.py`
2. `tests/test_answer_generator.py`

Implement:

```python
def generate_base_answer(
    question: str,
    llm_provider=None,
    prompt_template: str | None = None,
    max_tokens: int = 512
) -> dict:
```

Requirements:

- Use a simple provider interface.
- Do not hard-code OpenAI/Gemini/Claude inside the core module.
- Use mock provider in tests.
- Return structured JSON-compatible output.
- Fail safely if provider is missing or fails.
- Do not retrieve evidence.
- Do not verify facts.
- Keep code small, typed, and easy to explain.
- Use package name `temporalguard`.

Run tests and fix all failures. Report files created, logic summary, test result, and assumptions.
