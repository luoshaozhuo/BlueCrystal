"""Audit Hook consumer."""

from __future__ import annotations

from observability_reference.shared import get_observation_context

from .service import AuditService


class AuditInstrumentationHooks:
    """把 Audit operation facts 转换为持久化 AuditRecord."""

    def __init__(self, audit: AuditService) -> None:
        self._audit = audit

    def audit_operation_succeeded(
        self,
        *,
        status_code: int | None = None,
    ) -> None:
        context = get_observation_context()

        if context.operation is None or context.target_type is None:
            return

        detail: dict[str, object] = {}
        if status_code is not None:
            detail["status_code"] = status_code

        self._audit.success(
            actor=context.actor,
            source=context.source or "unknown",
            operation=context.operation,
            target_type=context.target_type,
            target_id=context.target_id,
            detail=detail,
        )

    def audit_operation_failed(
        self,
        *,
        status_code: int | None = None,
        exception: BaseException | None = None,
    ) -> None:
        context = get_observation_context()

        if context.operation is None or context.target_type is None:
            return

        detail: dict[str, object] = {}
        if status_code is not None:
            detail["status_code"] = status_code

        self._audit.failure(
            actor=context.actor,
            source=context.source or "unknown",
            operation=context.operation,
            target_type=context.target_type,
            target_id=context.target_id,
            detail=detail,
            exception=exception,
        )
