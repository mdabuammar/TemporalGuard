"""Shared error handling helpers for TemporalGuard.

The helpers in this module return JSON-compatible dictionaries so pipeline
steps can report recoverable failures without crashing the whole run.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class TemporalGuardError(Exception):
    """Base exception for TemporalGuard."""


class ProviderUnavailableError(TemporalGuardError):
    """Raised when a configured provider cannot be used."""


def make_error(
    error_type: str,
    message: str,
    module: str,
    recoverable: bool = True,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a standard JSON-compatible error object."""
    return {
        "error_type": str(error_type or "unknown_error"),
        "message": str(message or ""),
        "module": str(module or "unknown"),
        "recoverable": bool(recoverable),
        "details": _json_safe(details or {}),
    }


def make_warning(
    warning_type: str,
    message: str,
    module: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a standard JSON-compatible warning object."""
    return {
        "warning_type": str(warning_type or "unknown_warning"),
        "message": str(message or ""),
        "module": str(module or "unknown"),
        "details": _json_safe(details or {}),
    }


def safe_call(
    func: Callable[..., Any],
    *args: Any,
    module: str,
    fallback: Any = None,
    recoverable: bool = True,
    error_type: str = "execution_error",
    **kwargs: Any,
) -> dict[str, Any]:
    """Execute a callable and return structured success or failure metadata.

    Exceptions are captured in the returned error object. Non-recoverable
    failures are still recorded, but no exception is silently swallowed because
    the caller receives ``ok=False`` plus type/message details.
    """
    try:
        return {
            "ok": True,
            "result": func(*args, **kwargs),
            "error": None,
            "used_fallback": False,
        }
    except Exception as exc:  # pragma: no cover - exact branches covered by tests
        error = make_error(
            error_type=error_type,
            message=str(exc),
            module=module,
            recoverable=recoverable,
            details={
                "exception_type": exc.__class__.__name__,
            },
        )
        return {
            "ok": False,
            "result": fallback if recoverable else None,
            "error": error,
            "used_fallback": recoverable and fallback is not None,
        }


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    return str(value)
