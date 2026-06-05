from temporalguard.llm.answer_generator import generate_answer


def test_generate_answer_returns_string():
    assert generate_answer("What is TemporalGuard?") == "Scaffold answer for: What is TemporalGuard?"
