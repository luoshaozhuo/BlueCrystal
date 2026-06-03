"""Structured logging data models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class StructuredLogContext:
    """Cross-module log context fields safe to attach to structured logs."""

    request_id: str | None = None
    task_id: int | None = None
    ld_name: str | None = None
    profile_id: str | None = None
    node_key: str | None = None
    error_code: str | None = None
    attributes: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class OperationLogFields:
    """Operation-level log payload fields."""

    operation: str
    component: str
    outcome: str
    context: StructuredLogContext = field(default_factory=StructuredLogContext)


@dataclass(frozen=True, slots=True)
class ErrorEvent:
    """Structured error event suitable for logs, audit, or metrics sinks."""

    error_code: str
    message: str
    component: str
    retryable: bool = False
    context: StructuredLogContext = field(default_factory=StructuredLogContext)
