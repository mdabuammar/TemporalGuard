"""LLM provider adapters for TemporalGuard.

The providers expose one shared ``generate(prompt, **kwargs)`` method and
return a normalized response shape that can be consumed by answer generation.
"""

from __future__ import annotations

import os
from typing import Any, Protocol

import requests

from temporalguard.utils.errors import ProviderUnavailableError


EMPTY_USAGE = {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None}


class LLMProvider(Protocol):
    def generate(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """Generate a model answer for a prompt."""


class MockLLMProvider:
    provider_name = "mock"

    def __init__(self, model_name: str | None = None, answer: str | None = None) -> None:
        self.model_name = model_name or "mock-temporalguard"
        self.answer = answer

    def generate(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        del kwargs
        answer = self.answer or _mock_answer(prompt)
        return _provider_response(answer=answer, model_name=self.model_name, provider=self.provider_name)


class OpenAIProvider:
    provider_name = "openai"
    default_model = "gpt-4o-mini"
    endpoint = "https://api.openai.com/v1/chat/completions"

    def __init__(self, api_key: str | None = None, model_name: str | None = None, timeout_seconds: int = 30) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model_name or os.getenv("DEFAULT_MODEL_NAME") or self.default_model
        self.timeout_seconds = max(1, int(timeout_seconds or 30))

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        if not self.configured:
            raise ProviderUnavailableError("OPENAI_API_KEY is not configured.")
        max_tokens = int(kwargs.get("max_tokens") or 512)
        response = requests.post(
            self.endpoint,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        answer = str(payload.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
        return _provider_response(
            answer=answer,
            model_name=str(payload.get("model") or self.model_name),
            provider=self.provider_name,
            usage=_usage_from_openai(payload.get("usage")),
        )


class GeminiProvider:
    provider_name = "gemini"
    default_model = "gemini-1.5-flash"

    def __init__(self, api_key: str | None = None, model_name: str | None = None, timeout_seconds: int = 30) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name or os.getenv("DEFAULT_MODEL_NAME") or self.default_model
        self.timeout_seconds = max(1, int(timeout_seconds or 30))

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        if not self.configured:
            raise ProviderUnavailableError("GEMINI_API_KEY is not configured.")
        del kwargs
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"
        response = requests.post(
            endpoint,
            params={"key": self.api_key},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        answer = _extract_gemini_answer(payload)
        return _provider_response(
            answer=answer,
            model_name=self.model_name,
            provider=self.provider_name,
            usage=_usage_from_gemini(payload.get("usageMetadata")),
        )


class AnthropicProvider:
    provider_name = "anthropic"
    default_model = "claude-3-5-haiku-latest"
    endpoint = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key: str | None = None, model_name: str | None = None, timeout_seconds: int = 30) -> None:
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = model_name or os.getenv("DEFAULT_MODEL_NAME") or self.default_model
        self.timeout_seconds = max(1, int(timeout_seconds or 30))

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        if not self.configured:
            raise ProviderUnavailableError("ANTHROPIC_API_KEY is not configured.")
        max_tokens = int(kwargs.get("max_tokens") or 512)
        response = requests.post(
            self.endpoint,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model_name,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        answer = _extract_anthropic_answer(payload)
        return _provider_response(
            answer=answer,
            model_name=str(payload.get("model") or self.model_name),
            provider=self.provider_name,
            usage=_usage_from_anthropic(payload.get("usage")),
        )


class OpenRouterProvider:
    provider_name = "openrouter"
    default_model = "openrouter/free"

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        base_url: str | None = None,
        timeout_seconds: int = 30,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = (base_url or os.getenv("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1").rstrip("/")
        self.model_name = model_name or os.getenv("DEFAULT_MODEL_NAME") or self.default_model
        self.timeout_seconds = max(1, int(timeout_seconds or 30))

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        if not self.configured:
            raise ProviderUnavailableError("OPENROUTER_API_KEY is not configured.")
        max_tokens = int(kwargs.get("max_tokens") or 512)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Title": "TemporalGuard",
        }
        referer = os.getenv("OPENROUTER_HTTP_REFERER")
        if referer:
            headers["HTTP-Referer"] = referer
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json={
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": max_tokens,
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        answer = str(payload.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
        return _provider_response(
            answer=answer,
            model_name=str(payload.get("model") or self.model_name),
            provider=self.provider_name,
            usage=_usage_from_openai(payload.get("usage")),
        )


def create_llm_provider(
    provider_name: str | None = None,
    model_name: str | None = None,
    require_configured: bool = False,
) -> LLMProvider:
    name = normalize_provider_name(provider_name or os.getenv("DEFAULT_LLM_PROVIDER") or "mock")
    if name == "mock":
        return MockLLMProvider(model_name=model_name or os.getenv("DEFAULT_MODEL_NAME"))
    if name == "openai":
        provider = OpenAIProvider(model_name=model_name)
    elif name == "gemini":
        provider = GeminiProvider(model_name=model_name)
    elif name == "anthropic":
        provider = AnthropicProvider(model_name=model_name)
    elif name == "openrouter":
        provider = OpenRouterProvider(model_name=model_name)
    else:
        raise ProviderUnavailableError(f"Unsupported LLM provider: {provider_name}")
    if require_configured and not provider.configured:
        env_name = {
            "openai": "OPENAI_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
        }[name]
        raise ProviderUnavailableError(f"{env_name} is not configured.")
    return provider


def normalize_provider_name(provider_name: str | None) -> str:
    text = str(provider_name or "mock").strip().lower()
    aliases = {
        "demo": "mock",
        "demo/mock": "mock",
        "mock": "mock",
        "openai": "openai",
        "gpt": "openai",
        "gemini": "gemini",
        "google": "gemini",
        "anthropic": "anthropic",
        "claude": "anthropic",
        "claude/anthropic": "anthropic",
        "openrouter": "openrouter",
        "openrouter/free": "openrouter",
    }
    return aliases.get(text, text)


def _provider_response(
    answer: str,
    model_name: str,
    provider: str,
    usage: dict[str, int | None] | None = None,
) -> dict[str, Any]:
    return {
        "answer": str(answer or ""),
        "model_name": str(model_name or ""),
        "provider": str(provider or ""),
        "usage": usage or dict(EMPTY_USAGE),
    }


def _mock_answer(prompt: str) -> str:
    question = prompt.split("Question:", 1)[-1].strip() if "Question:" in prompt else prompt.strip()
    if "latest python" in question.lower():
        return "Python 3.10 is the latest stable version of Python."
    if "binary search" in question.lower():
        return "Binary search repeatedly halves a sorted search space to find a target value."
    return f"Mock answer for: {question}"


def _usage_from_openai(value: Any) -> dict[str, int | None]:
    if not isinstance(value, dict):
        return dict(EMPTY_USAGE)
    return {
        "prompt_tokens": _optional_int(value.get("prompt_tokens")),
        "completion_tokens": _optional_int(value.get("completion_tokens")),
        "total_tokens": _optional_int(value.get("total_tokens")),
    }


def _usage_from_gemini(value: Any) -> dict[str, int | None]:
    if not isinstance(value, dict):
        return dict(EMPTY_USAGE)
    return {
        "prompt_tokens": _optional_int(value.get("promptTokenCount")),
        "completion_tokens": _optional_int(value.get("candidatesTokenCount")),
        "total_tokens": _optional_int(value.get("totalTokenCount")),
    }


def _usage_from_anthropic(value: Any) -> dict[str, int | None]:
    if not isinstance(value, dict):
        return dict(EMPTY_USAGE)
    prompt_tokens = _optional_int(value.get("input_tokens"))
    completion_tokens = _optional_int(value.get("output_tokens"))
    total_tokens = prompt_tokens + completion_tokens if prompt_tokens is not None and completion_tokens is not None else None
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


def _extract_gemini_answer(payload: dict[str, Any]) -> str:
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        return ""
    parts = candidates[0].get("content", {}).get("parts", [])
    if not isinstance(parts, list):
        return ""
    return "\n".join(str(part.get("text") or "") for part in parts if isinstance(part, dict)).strip()


def _extract_anthropic_answer(payload: dict[str, Any]) -> str:
    content = payload.get("content")
    if not isinstance(content, list):
        return ""
    return "\n".join(str(item.get("text") or "") for item in content if isinstance(item, dict)).strip()


def _optional_int(value: Any) -> int | None:
    return int(value) if isinstance(value, int) else None
