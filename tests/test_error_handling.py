import json

from temporalguard.utils.errors import (
    ProviderUnavailableError,
    TemporalGuardError,
    make_error,
    make_warning,
    safe_call,
)


def test_error_hierarchy():
    assert issubclass(ProviderUnavailableError, TemporalGuardError)


def test_make_error_returns_standard_json_compatible_shape() -> None:
    error = make_error(
        "search_failure",
        "Search provider timed out.",
        "fresh_evidence_retriever",
        recoverable=True,
        details={"timeout_seconds": 10, "raw": ValueError("timeout")},
    )

    assert error == {
        "error_type": "search_failure",
        "message": "Search provider timed out.",
        "module": "fresh_evidence_retriever",
        "recoverable": True,
        "details": {"timeout_seconds": 10, "raw": "timeout"},
    }
    json.dumps(error)


def test_make_warning_returns_standard_json_compatible_shape() -> None:
    warning = make_warning(
        "missing_date",
        "Evidence source has no clear publication date.",
        "source_freshness_scorer",
        details={"evidence_id": "E1"},
    )

    assert warning == {
        "warning_type": "missing_date",
        "message": "Evidence source has no clear publication date.",
        "module": "source_freshness_scorer",
        "details": {"evidence_id": "E1"},
    }
    json.dumps(warning)


def test_safe_call_success_returns_result_without_error() -> None:
    result = safe_call(lambda value: value * 2, 4, module="test_module")

    assert result == {
        "ok": True,
        "result": 8,
        "error": None,
        "used_fallback": False,
    }
    json.dumps(result)


def test_safe_call_recoverable_failure_uses_fallback_and_records_error() -> None:
    def fail() -> None:
        raise RuntimeError("provider unavailable")

    result = safe_call(
        fail,
        module="fresh_evidence_retriever",
        fallback={"evidence_results": []},
        recoverable=True,
        error_type="search_failure",
    )

    assert result["ok"] is False
    assert result["result"] == {"evidence_results": []}
    assert result["used_fallback"] is True
    assert result["error"]["error_type"] == "search_failure"
    assert result["error"]["message"] == "provider unavailable"
    assert result["error"]["module"] == "fresh_evidence_retriever"
    assert result["error"]["recoverable"] is True
    assert result["error"]["details"] == {"exception_type": "RuntimeError"}
    json.dumps(result)


def test_safe_call_recoverable_failure_without_fallback_is_explicit() -> None:
    result = safe_call(
        lambda: (_ for _ in ()).throw(ValueError("bad date")),
        module="source_freshness_scorer",
        recoverable=True,
    )

    assert result["ok"] is False
    assert result["result"] is None
    assert result["used_fallback"] is False
    assert result["error"]["recoverable"] is True
    assert result["error"]["details"]["exception_type"] == "ValueError"


def test_safe_call_non_recoverable_failure_does_not_use_fallback() -> None:
    def fail() -> None:
        raise AssertionError("schema is invalid")

    result = safe_call(
        fail,
        module="dataset_builder",
        fallback={"ignored": True},
        recoverable=False,
        error_type="validation_failure",
    )

    assert result["ok"] is False
    assert result["result"] is None
    assert result["used_fallback"] is False
    assert result["error"] == {
        "error_type": "validation_failure",
        "message": "schema is invalid",
        "module": "dataset_builder",
        "recoverable": False,
        "details": {"exception_type": "AssertionError"},
    }
