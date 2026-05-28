"""Structured audit event schema for ingest runtime and API."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

_SENSITIVE_MARKERS = (
    "password",
    "token",
    "private_key",
    "private-key",
    "cert_secret",
    "cert-secret",
    "secret",
)


def redact_value(value: Any) -> Any:
    """Recursively redact sensitive nested values."""

    if isinstance(value, dict):
        return {key: redact_pair(key, item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    return value


def redact_pair(key: str, value: Any) -> Any:
    """Redact one key/value pair when the key is sensitive."""

    normalized = key.strip().lower().replace(" ", "_")
    if any(marker in normalized for marker in _SENSITIVE_MARKERS):
        return "***REDACTED***"
    return redact_value(value)


@dataclass(frozen=True, slots=True)
class IngestAuditEvent:
    """One structured ingest audit event."""

    request_id: str
    actor: str | None
    action: str
    resource_type: str
    resource_id: str | None
    decision: str
    result: str
    reason_code: str | None
    http_status: int | None
    trace_id: str | None
    client_ip: str | None
    node_id: str | None
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    before_version: int | None = None
    after_version: int | None = None
    changed_fields: list[str] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)

    def sanitized_payload(self) -> dict[str, Any]:
        """Return one JSON/DB friendly redacted payload."""

        payload = asdict(self)
        payload["attributes"] = redact_value(payload["attributes"])
        return payload
