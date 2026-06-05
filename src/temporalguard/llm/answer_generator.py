"""Controlled base answer generation for TemporalGuard."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Protocol


DEFAULT_PROMPT_TEMPLATE = (
    "Answer the user question clearly and directly. Keep the answer concise. "
    "Do not add citations unless asked.\nQuestion: {question}"
)
EMPTY_USAGE = {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None}


class LLMProvider(Protocol):
    """Minimal provider interface for answer generation."""

    def generate(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """Generate an answer from a prompt."""


def generate_base_answer(
    question: str,
    llm_provider: LLMProvider | None = None,
    prompt_template: str | None = None,
    max_tokens: int = 512,
) -> dict[str, Any]:
    """Generate the original LLM answer for TemporalGuard checking."""
    generated_at = _now_utc_iso()
    if not isinstance(question, str) or not question.strip():
        return _result(
            question="" if not isinstance(question, str) else question,
            answer="",
            model_name=None,
            provider=None,
            generated_at=generated_at,
            status="failed",
            usage=EMPTY_USAGE,
            warnings=[],
            errors=["Question is empty or invalid."],
        )

    if llm_provider is None:
        return _result(
            question=question,
            answer="",
            model_name=None,
            provider=None,
            generated_at=generated_at,
            status="failed",
            usage=EMPTY_USAGE,
            warnings=["No LLM provider configured."],
            errors=[],
        )

    prompt = _build_prompt(question, prompt_template)
    try:
        provider_response = llm_provider.generate(prompt, max_tokens=max(1, int(max_tokens or 1)))
    except Exception as exc:  # pragma: no cover - defensive boundary
        return _result(
            question=question,
            answer="",
            model_name=None,
            provider=None,
            generated_at=generated_at,
            status="failed",
            usage=EMPTY_USAGE,
            warnings=[],
            errors=[f"LLM provider failed: {exc}"],
        )

    if not isinstance(provider_response, dict):
        return _result(
            question=question,
            answer="",
            model_name=None,
            provider=None,
            generated_at=generated_at,
            status="failed",
            usage=EMPTY_USAGE,
            warnings=[],
            errors=["LLM provider returned a non-dict response."],
        )

    answer = str(provider_response.get("answer") or "").strip()
    if not answer:
        return _result(
            question=question,
            answer="",
            model_name=_optional_string(provider_response.get("model_name")),
            provider=_optional_string(provider_response.get("provider")),
            generated_at=generated_at,
            status="failed",
            usage=_usage(provider_response.get("usage")),
            warnings=[],
            errors=["LLM provider returned an empty answer."],
        )

    return _result(
        question=question,
        answer=answer,
        model_name=_optional_string(provider_response.get("model_name")),
        provider=_optional_string(provider_response.get("provider")),
        generated_at=generated_at,
        status="success",
        usage=_usage(provider_response.get("usage")),
        warnings=[],
        errors=[],
    )


def generate_answer(question: str, context: dict[str, Any] | None = None) -> str:
    """Backward-compatible string helper used by older code paths."""
    provider = (context or {}).get("llm_provider") if isinstance(context, dict) else None
    if provider is None:
        return f"Scaffold answer for: {question}"
    result = generate_base_answer(question, provider)
    return str(result.get("answer") or "")


def _build_prompt(question: str, prompt_template: str | None) -> str:
    template = prompt_template or DEFAULT_PROMPT_TEMPLATE
    if "{question}" in template:
        return template.format(question=question.strip())
    return f"{template.rstrip()}\nQuestion: {question.strip()}"


def _result(
    question: str,
    answer: str,
    model_name: str | None,
    provider: str | None,
    generated_at: str,
    status: str,
    usage: dict[str, int | None],
    warnings: list[str],
    errors: list[str],
) -> dict[str, Any]:
    return {
        "question": question,
        "answer": answer,
        "model_name": model_name,
        "provider": provider,
        "generated_at": generated_at,
        "status": status,
        "usage": usage,
        "warnings": warnings,
        "errors": errors,
    }


def _usage(value: Any) -> dict[str, int | None]:
    if not isinstance(value, dict):
        return dict(EMPTY_USAGE)
    return {
        "prompt_tokens": _optional_int(value.get("prompt_tokens")),
        "completion_tokens": _optional_int(value.get("completion_tokens")),
        "total_tokens": _optional_int(value.get("total_tokens")),
    }


def _optional_int(value: Any) -> int | None:
    return int(value) if isinstance(value, int) else None


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _now_utc_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
