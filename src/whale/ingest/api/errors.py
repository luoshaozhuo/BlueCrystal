"""API error types and stable error payloads."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ApiError(Exception):
    """Structured API error used by exception handlers."""

    code: str
    message: str
    http_status: int
    action: str
    resource_type: str
    resource_id: str | None = None
    decision: str = "DENY"
    result: str = "FAILED"
    reason_code: str | None = None
    changed_fields: list[str] = field(default_factory=list)

    def to_payload(self) -> dict[str, object]:
        return {
            "error": self.code,
            "message": self.message,
        }


def not_found(*, action: str, resource_type: str, resource_id: str) -> ApiError:
    return ApiError(
        code="NOT_FOUND",
        message=f"{resource_type} `{resource_id}` was not found.",
        http_status=404,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        result="NOT_FOUND",
        reason_code="NOT_FOUND",
    )


def conflict(
    *,
    action: str,
    resource_type: str,
    resource_id: str | None,
    message: str,
    changed_fields: list[str] | None = None,
) -> ApiError:
    return ApiError(
        code="CONFLICT",
        message=message,
        http_status=409,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        result="CONFLICT",
        reason_code="VERSION_CONFLICT",
        changed_fields=changed_fields or [],
    )


def denied(*, action: str, resource_type: str, resource_id: str | None = None) -> ApiError:
    return ApiError(
        code="DENIED",
        message="Access denied.",
        http_status=403,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        result="DENIED",
        reason_code="ACCESS_DENIED",
    )
