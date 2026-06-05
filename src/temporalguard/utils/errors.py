"""Shared error types for TemporalGuard."""

from __future__ import annotations


class TemporalGuardError(Exception):
    """Base exception for TemporalGuard."""


class ProviderUnavailableError(TemporalGuardError):
    """Raised when a configured provider cannot be used."""
