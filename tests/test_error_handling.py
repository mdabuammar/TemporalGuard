from temporalguard.utils.errors import ProviderUnavailableError, TemporalGuardError


def test_error_hierarchy():
    assert issubclass(ProviderUnavailableError, TemporalGuardError)
