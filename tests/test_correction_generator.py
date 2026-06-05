from temporalguard.skills.correction_generator import generate_correction


def test_generate_correction_preserves_answer():
    assert generate_correction("answer", []) == {"answer": "answer", "corrected": False}
