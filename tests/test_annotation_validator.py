from temporalguard.data.annotation_validator import validate_annotation


def test_validate_annotation_returns_true():
    assert validate_annotation({}) is True
