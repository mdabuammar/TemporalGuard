import json
import re

from temporalguard.llm.answer_generator import generate_answer, generate_base_answer


class MockLLMProvider:
    def __init__(self, response: dict) -> None:
        self.response = response
        self.prompts: list[str] = []
        self.kwargs: list[dict] = []

    def generate(self, prompt: str, **kwargs):
        self.prompts.append(prompt)
        self.kwargs.append(kwargs)
        return self.response


class FailingProvider:
    def generate(self, prompt: str, **kwargs):
        del prompt, kwargs
        raise RuntimeError("provider offline")


def test_generate_base_answer_success_with_mock_provider() -> None:
    provider = MockLLMProvider(
        {
            "answer": "TemporalGuard checks time-sensitive claims.",
            "model_name": "mock-model",
            "provider": "mock",
            "usage": {"prompt_tokens": 10, "completion_tokens": 6, "total_tokens": 16},
        }
    )

    result = generate_base_answer("What is TemporalGuard?", provider)

    assert result["question"] == "What is TemporalGuard?"
    assert result["answer"] == "TemporalGuard checks time-sensitive claims."
    assert result["model_name"] == "mock-model"
    assert result["provider"] == "mock"
    assert result["status"] == "success"
    assert result["usage"] == {"prompt_tokens": 10, "completion_tokens": 6, "total_tokens": 16}
    assert result["warnings"] == []
    assert result["errors"] == []
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", result["generated_at"])
    assert provider.prompts[0].startswith("Answer the user question clearly and directly.")
    assert provider.kwargs[0]["max_tokens"] == 512
    json.dumps(result)


def test_generate_base_answer_missing_provider_fails_safely() -> None:
    result = generate_base_answer("What is TemporalGuard?")

    assert result["status"] == "failed"
    assert result["answer"] == ""
    assert result["warnings"] == ["No LLM provider configured."]
    assert result["errors"] == []


def test_generate_base_answer_empty_question_fails_safely() -> None:
    result = generate_base_answer("   ", MockLLMProvider({"answer": "unused"}))

    assert result["status"] == "failed"
    assert result["errors"] == ["Question is empty or invalid."]


def test_generate_base_answer_provider_failure_fails_safely() -> None:
    result = generate_base_answer("Question?", FailingProvider())

    assert result["status"] == "failed"
    assert result["answer"] == ""
    assert result["errors"] == ["LLM provider failed: provider offline"]


def test_generate_base_answer_rejects_non_dict_response() -> None:
    class BadProvider:
        def generate(self, prompt: str, **kwargs):
            del prompt, kwargs
            return "plain text"

    result = generate_base_answer("Question?", BadProvider())

    assert result["status"] == "failed"
    assert result["errors"] == ["LLM provider returned a non-dict response."]


def test_generate_base_answer_rejects_empty_answer() -> None:
    result = generate_base_answer(
        "Question?",
        MockLLMProvider({"answer": "", "model_name": "mock", "provider": "mock"}),
    )

    assert result["status"] == "failed"
    assert result["model_name"] == "mock"
    assert result["provider"] == "mock"
    assert result["errors"] == ["LLM provider returned an empty answer."]


def test_generate_base_answer_custom_prompt_and_max_tokens() -> None:
    provider = MockLLMProvider({"answer": "Short answer."})

    result = generate_base_answer(
        "What is Python?",
        provider,
        prompt_template="Be concise.\nQ: {question}",
        max_tokens=64,
    )

    assert result["status"] == "success"
    assert provider.prompts == ["Be concise.\nQ: What is Python?"]
    assert provider.kwargs[0]["max_tokens"] == 64


def test_generate_answer_backward_compatible_scaffold_string() -> None:
    assert generate_answer("What is TemporalGuard?") == "Scaffold answer for: What is TemporalGuard?"


def test_generate_answer_uses_provider_when_supplied_in_context() -> None:
    provider = MockLLMProvider({"answer": "Provider answer."})

    assert generate_answer("Question?", {"llm_provider": provider}) == "Provider answer."
