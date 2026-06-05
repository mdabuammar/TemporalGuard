from temporalguard.skills.outdated_answer_detector import detect_outdated_answer


def test_detect_outdated_answer_defaults_to_false():
    assert detect_outdated_answer("answer", []) is False
