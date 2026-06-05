from temporalguard.reporting.report_generator import generate_report


def test_generate_report_returns_string():
    assert generate_report({}) == "TemporalGuard report scaffold"
