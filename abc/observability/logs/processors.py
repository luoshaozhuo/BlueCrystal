"""structlog 自定义 Processor：唯一上下文注入 + 安全清洗。"""
from __future__ import annotations
from collections.abc import Mapping
from ..shared import get_observation_context

_REDACTED = "***REDACTED***"
_MAX_VALUE_LENGTH = 4096
_MAX_NESTING_DEPTH = 6
_SENSITIVE_KEYS = frozenset({"authorization","password","passwd","pwd","secret","token","access_token","refresh_token","api_key","apikey","private_key","database_password","db_password"})

def add_observation_context(logger, method_name: str, event_dict: dict) -> dict:
    ctx = get_observation_context()
    for name in ("runtime_id","node_id","request_id","task_id","connection_id","actor","source","operation","target_type","target_id"):
        value = getattr(ctx, name)
        if value is not None:
            event_dict.setdefault(name, value)
    return event_dict

def sanitize_event(logger, method_name: str, event_dict: dict) -> dict:
    return _sanitize_mapping(event_dict)

def _sanitize_mapping(value: Mapping[object, object], *, depth: int = 0) -> dict[str, object]:
    if depth >= _MAX_NESTING_DEPTH:
        return {"value": "<max-depth>"}
    result: dict[str, object] = {}
    for raw_key, raw_value in value.items():
        key = str(raw_key)
        if key.strip().lower().replace("-", "_") in _SENSITIVE_KEYS:
            result[key] = _REDACTED
        else:
            result[key] = _sanitize_value(raw_value, depth=depth + 1)
    return result

def _sanitize_value(value: object, *, depth: int) -> object:
    if value is None or isinstance(value, (bool, int, float)): return value
    if isinstance(value, str): return _bounded(value)
    if isinstance(value, Mapping): return _sanitize_mapping(value, depth=depth)
    if isinstance(value, (list, tuple, set, frozenset)):
        if depth >= _MAX_NESTING_DEPTH: return ["<max-depth>"]
        return [_sanitize_value(item, depth=depth + 1) for item in value]
    return _bounded(repr(value))

def _bounded(value: str) -> str:
    return value if len(value) <= _MAX_VALUE_LENGTH else value[:_MAX_VALUE_LENGTH] + "…<truncated>"
