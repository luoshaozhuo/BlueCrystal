"""Audit 应用服务."""

from __future__ import annotations

import sys
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from types import MappingProxyType
from uuid import uuid4

from observability_reference.shared import get_observation_context

from .models import AuditQuery, AuditRecord, AuditResult
from .ports import AuditStore


_REDACTED = "***REDACTED***"
_MAX_VALUE_LENGTH = 4096
_MAX_NESTING_DEPTH = 6
_SENSITIVE_KEYS = frozenset(
    {
        "authorization",
        "password",
        "passwd",
        "pwd",
        "secret",
        "token",
        "access_token",
        "refresh_token",
        "api_key",
        "apikey",
        "private_key",
        "database_password",
        "db_password",
    }
)


class AuditPersistenceError(RuntimeError):
    """严格模式下 Audit 持久化失败."""


class AuditService:
    """创建并持久化管理操作审计记录.

    推荐由 FastAPI/CLI 等边界适配器自动调用 ``record()``。
    ``success()`` / ``failure()`` 保留作为底层 API 和兼容接口，
    但业务 Router 不应再显式编写 success/failure 控制流。
    """

    def __init__(
        self,
        stores: Sequence[AuditStore],
        *,
        strict: bool = False,
    ) -> None:
        self._stores = tuple(stores)
        self._strict = strict

    def success(
        self,
        *,
        actor: str | None,
        source: str,
        operation: str,
        target_type: str,
        target_id: str | int | None = None,
        detail: Mapping[str, object] | None = None,
    ) -> AuditRecord:
        return self.record(
            actor=actor,
            source=source,
            operation=operation,
            target_type=target_type,
            target_id=target_id,
            result=AuditResult.SUCCESS,
            detail=detail,
        )

    def failure(
        self,
        *,
        actor: str | None,
        source: str,
        operation: str,
        target_type: str,
        target_id: str | int | None = None,
        detail: Mapping[str, object] | None = None,
        exception: BaseException | None = None,
    ) -> AuditRecord:
        return self.record(
            actor=actor,
            source=source,
            operation=operation,
            target_type=target_type,
            target_id=target_id,
            result=AuditResult.FAILURE,
            detail=detail,
            exception=exception,
        )

    def record(
        self,
        *,
        actor: str | None,
        source: str,
        operation: str,
        target_type: str,
        target_id: str | int | None,
        result: AuditResult,
        detail: Mapping[str, object] | None = None,
        exception: BaseException | None = None,
    ) -> AuditRecord:
        context = get_observation_context()

        record = AuditRecord(
            audit_id=uuid4().hex,
            timestamp=datetime.now(timezone.utc),
            runtime_id=context.runtime_id,
            node_id=context.node_id,
            request_id=context.request_id,
            actor=_optional_bounded_text(actor),
            source=_required_bounded_text(source, "source"),
            operation=_required_bounded_text(operation, "operation"),
            target_type=_required_bounded_text(target_type, "target_type"),
            target_id=(
                None
                if target_id is None
                else _bounded_text(str(target_id))
            ),
            result=result,
            detail=MappingProxyType(
                _sanitize_mapping(detail or {})
            ),
            error_type=(
                type(exception).__name__
                if exception is not None
                else None
            ),
            error_message=(
                _bounded_text(str(exception))
                if exception is not None
                else None
            ),
        )

        failures: list[BaseException] = []

        for store in self._stores:
            try:
                store.append(record)
            except Exception as exc:
                failures.append(exc)
                _fallback_store_error(store, exc)

        if failures and self._strict:
            raise AuditPersistenceError(
                f"{len(failures)} audit store(s) failed"
            ) from failures[0]

        return record

    def query(
        self,
        query: AuditQuery,
        *,
        store_index: int = 0,
    ) -> tuple[AuditRecord, ...]:
        if not self._stores:
            return ()

        return self._stores[store_index].query(query)

    def flush(self) -> None:
        failures: list[BaseException] = []

        for store in self._stores:
            try:
                store.flush()
            except Exception as exc:
                failures.append(exc)
                _fallback_store_error(store, exc)

        if failures and self._strict:
            raise AuditPersistenceError(
                f"{len(failures)} audit store(s) failed to flush"
            ) from failures[0]

    def close(self) -> None:
        failures: list[BaseException] = []

        for store in reversed(self._stores):
            try:
                store.close()
            except Exception as exc:
                failures.append(exc)
                _fallback_store_error(store, exc)

        if failures and self._strict:
            raise AuditPersistenceError(
                f"{len(failures)} audit store(s) failed to close"
            ) from failures[0]


def _sanitize_mapping(
    value: Mapping[str, object],
    *,
    depth: int = 0,
) -> dict[str, object]:
    if depth >= _MAX_NESTING_DEPTH:
        return {"value": "<max-depth>"}

    result: dict[str, object] = {}

    for raw_key, raw_value in value.items():
        key = str(raw_key)

        if _is_sensitive_key(key):
            result[key] = _REDACTED
            continue

        result[key] = _sanitize_value(
            raw_value,
            depth=depth + 1,
        )

    return result


def _sanitize_value(
    value: object,
    *,
    depth: int,
) -> object:
    if value is None or isinstance(
        value,
        (bool, int, float),
    ):
        return value

    if isinstance(value, str):
        return _bounded_text(value)

    if isinstance(value, Mapping):
        return _sanitize_mapping(
            value,
            depth=depth,
        )

    if isinstance(
        value,
        (list, tuple, set, frozenset),
    ):
        if depth >= _MAX_NESTING_DEPTH:
            return ["<max-depth>"]

        return [
            _sanitize_value(
                item,
                depth=depth + 1,
            )
            for item in value
        ]

    return _bounded_text(repr(value))


def _is_sensitive_key(key: str) -> bool:
    normalized = (
        key.strip()
        .lower()
        .replace("-", "_")
    )
    return normalized in _SENSITIVE_KEYS


def _required_bounded_text(
    value: str,
    name: str,
) -> str:
    if not value or not value.strip():
        raise ValueError(
            f"{name} must not be empty"
        )

    return _bounded_text(value)


def _optional_bounded_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    return _bounded_text(value)


def _bounded_text(value: str) -> str:
    if len(value) <= _MAX_VALUE_LENGTH:
        return value

    return (
        value[:_MAX_VALUE_LENGTH]
        + "…<truncated>"
    )


def _fallback_store_error(
    store: object,
    exception: BaseException,
) -> None:
    try:
        sys.stderr.write(
            "BlueCrystal observability audit store failure: "
            f"store={type(store).__name__} "
            f"error={type(exception).__name__}: "
            f"{exception}\n"
        )
        sys.stderr.flush()
    except Exception:
        pass
