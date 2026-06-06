import pytest

from temporalguard.llm.answer_generator import generate_base_answer
from temporalguard.llm.providers import (
    AnthropicProvider,
    GeminiProvider,
    MockLLMProvider,
    OpenAIProvider,
    create_llm_provider,
    normalize_provider_name,
)
from temporalguard.utils.errors import ProviderUnavailableError


def test_mock_provider_returns_valid_response_shape() -> None:
    provider = MockLLMProvider(model_name="mock-test", answer="A deterministic answer.")

    result = provider.generate("Question: What is binary search?")

    assert result == {
        "answer": "A deterministic answer.",
        "model_name": "mock-test",
        "provider": "mock",
        "usage": {
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
        },
    }


def test_provider_factory_supports_aliases() -> None:
    assert normalize_provider_name("Demo/mock") == "mock"
    assert normalize_provider_name("Claude/Anthropic") == "anthropic"
    assert isinstance(create_llm_provider("mock"), MockLLMProvider)


def test_missing_openai_api_key_fails_safely(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("DEFAULT_MODEL_NAME", raising=False)

    with pytest.raises(ProviderUnavailableError, match="OPENAI_API_KEY"):
        create_llm_provider("openai", require_configured=True)

    with pytest.raises(ProviderUnavailableError, match="OPENAI_API_KEY"):
        OpenAIProvider(api_key="").generate("Question: What is current?")


def test_missing_gemini_and_anthropic_keys_fail_safely(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("DEFAULT_MODEL_NAME", raising=False)

    with pytest.raises(ProviderUnavailableError, match="GEMINI_API_KEY"):
        GeminiProvider(api_key="").generate("Question: What is current?")

    with pytest.raises(ProviderUnavailableError, match="ANTHROPIC_API_KEY"):
        AnthropicProvider(api_key="").generate("Question: What is current?")


def test_answer_generation_uses_mock_provider() -> None:
    result = generate_base_answer("What is binary search?", MockLLMProvider(answer="Binary search halves sorted input."))

    assert result["status"] == "success"
    assert result["answer"] == "Binary search halves sorted input."
    assert result["provider"] == "mock"
    assert result["usage"]["total_tokens"] is None
