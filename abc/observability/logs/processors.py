"""structlog 自定义 Processor：上下文注入与安全清洗。"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from typing import Any

from opentelemetry import trace

from ..context import get_observation_context


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
_CONTEXT_FIELDS = (
    "service_name",
    "service_instance_id",
    "request_id",
    "correlation_id",
    "actor",
    "source",
    "job_id",
    "execution_id",
)


def add_observation_context(
    logger: object,
    method_name: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """将当前关联上下文字段注入日志事件。"""
    observation = get_observation_context()
    for name in _CONTEXT_FIELDS:
        value = getattr(observation, name)
        if value is not None:
            event_dict.setdefault(name, value)
    for name, value in observation.attributes.items():
        event_dict.setdefault(name, value)
    span_context = trace.get_current_span().get_span_context()
    if span_context.is_valid:
        event_dict.setdefault("trace_id", format(span_context.trace_id, "032x"))
        event_dict.setdefault("span_id", format(span_context.span_id, "016x"))
    return event_dict


def sanitize_event(
    logger: object,
    method_name: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """递归清洗日志事件中的敏感或过长值。"""
    return _sanitize_mapping(event_dict)


def _sanitize_mapping(
    value: Mapping[str, object],
    *,
    depth: int = 0,
) -> dict[str, object]:
    if depth >= _MAX_NESTING_DEPTH:
        return {"value": "<max-depth>"}

    result: dict[str, object] = {}
    for key, raw_value in value.items():
        normalized_key = key.strip().lower().replace("-", "_")
        if normalized_key in _SENSITIVE_KEYS:
            result[key] = _REDACTED
        else:
            result[key] = _sanitize_value(raw_value, depth=depth + 1)
    return result


def _sanitize_value(value: object, *, depth: int) -> object:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return _bounded(value)
    if isinstance(value, Mapping):
        return _sanitize_mapping(
            {str(key): item for key, item in value.items()}, depth=depth
        )
    if isinstance(value, (list, tuple, set, frozenset)):
        if depth >= _MAX_NESTING_DEPTH:
            return ["<max-depth>"]
        return [
            _sanitize_value(item, depth=depth + 1)
            for item in value
        ]
    return _bounded(repr(value))


def _bounded(value: str) -> str:
    if len(value) <= _MAX_VALUE_LENGTH:
        return value
    return value[:_MAX_VALUE_LENGTH] + "…<truncated>"
