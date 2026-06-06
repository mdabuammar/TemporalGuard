import pytest

from temporalguard.llm.answer_generator import generate_base_answer
from temporalguard.llm.providers import (
    AnthropicProvider,
    GeminiProvider,
    MockLLMProvider,
    OpenAIProvider,
    OpenRouterProvider,
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
    assert normalize_provider_name("OpenRouter") == "openrouter"
    assert isinstance(create_llm_provider("mock"), MockLLMProvider)
    assert isinstance(create_llm_provider("openrouter"), OpenRouterProvider)


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


def test_missing_openrouter_api_key_fails_safely(monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("DEFAULT_MODEL_NAME", raising=False)

    with pytest.raises(ProviderUnavailableError, match="OPENROUTER_API_KEY"):
        create_llm_provider("openrouter", require_configured=True)

    with pytest.raises(ProviderUnavailableError, match="OPENROUTER_API_KEY"):
        OpenRouterProvider(api_key="").generate("Question: What is current?")


def test_openrouter_provider_parses_mocked_response(monkeypatch) -> None:
    calls = []

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "model": "openrouter/free",
                "choices": [{"message": {"content": "Binary search halves sorted input."}}],
                "usage": {"prompt_tokens": 7, "completion_tokens": 5, "total_tokens": 12},
            }

    def fake_post(*args, **kwargs):
        calls.append({"args": args, "kwargs": kwargs})
        return FakeResponse()

    monkeypatch.setattr("temporalguard.llm.providers.requests.post", fake_post)
    monkeypatch.setenv("OPENROUTER_HTTP_REFERER", "https://example.test")

    provider = OpenRouterProvider(api_key="test-key", model_name="openrouter/free", base_url="https://router.test/api/v1")
    result = provider.generate("Question: What is binary search?", max_tokens=64)

    assert result["answer"] == "Binary search halves sorted input."
    assert result["model_name"] == "openrouter/free"
    assert result["provider"] == "openrouter"
    assert result["usage"]["total_tokens"] == 12
    assert calls[0]["args"][0] == "https://router.test/api/v1/chat/completions"
    assert calls[0]["kwargs"]["headers"]["Authorization"] == "Bearer test-key"
    assert calls[0]["kwargs"]["headers"]["HTTP-Referer"] == "https://example.test"
    assert calls[0]["kwargs"]["json"]["temperature"] == 0.2
    assert calls[0]["kwargs"]["json"]["max_tokens"] == 64


def test_answer_generation_uses_mock_provider() -> None:
    result = generate_base_answer("What is binary search?", MockLLMProvider(answer="Binary search halves sorted input."))

    assert result["status"] == "success"
    assert result["answer"] == "Binary search halves sorted input."
    assert result["provider"] == "mock"
    assert result["usage"]["total_tokens"] is None
