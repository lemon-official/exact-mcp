"""Stable, secret-safe domain errors returned by MCP tools."""

from typing import Any


class ExactMCPError(Exception):
    """Base error carrying a machine-readable code and safe details."""

    code = "exact_mcp_error"

    def __init__(
        self,
        message: str,
        *,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.retryable = retryable
        self.details = details or {}

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
            "details": self.details,
        }


class AuthenticationRequiredError(ExactMCPError):
    code = "authentication_required"


class AmbiguousMatchError(ExactMCPError):
    code = "ambiguous_match"


class NotFoundError(ExactMCPError):
    code = "not_found"


class ValidationFailedError(ExactMCPError):
    code = "validation_failed"


class RateLimitedError(ExactMCPError):
    code = "rate_limited"


class UnsupportedOperationError(ExactMCPError):
    code = "unsupported_operation"


class ExactAPIError(ExactMCPError):
    code = "exact_api_error"

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        request_id: str | None = None,
        retryable: bool = False,
    ) -> None:
        details: dict[str, Any] = {}
        if status_code is not None:
            details["status_code"] = status_code
        if request_id:
            details["request_id"] = request_id
        super().__init__(message, retryable=retryable, details=details)

