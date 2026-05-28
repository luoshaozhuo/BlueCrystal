"""Unit tests for audit event redaction."""

from __future__ import annotations

from datetime import UTC, datetime

from whale.ingest.domain.audit_event import IngestAuditEvent, redact_value


def test_redact_password_in_attributes():
    event = IngestAuditEvent(
        request_id="r1", actor="tester", action="test",
        resource_type="test", resource_id="r1", decision="ALLOW",
        result="SUCCESS", reason_code=None, http_status=200,
        trace_id=None, client_ip=None, node_id="n1",
        timestamp=datetime.now(tz=UTC),
        attributes={"password": "my_secret", "safe": "ok"},
    )
    payload = event.sanitized_payload()
    assert payload["attributes"]["password"] == "***REDACTED***"
    assert payload["attributes"]["safe"] == "ok"


def test_redact_token_in_attributes():
    event = IngestAuditEvent(
        request_id="r2", actor="tester", action="test",
        resource_type="test", resource_id="r2", decision="ALLOW",
        result="SUCCESS", reason_code=None, http_status=200,
        trace_id=None, client_ip=None, node_id="n1",
        timestamp=datetime.now(tz=UTC),
        attributes={"access_token": "tok_abc123", "visible": "data"},
    )
    payload = event.sanitized_payload()
    assert payload["attributes"]["access_token"] == "***REDACTED***"
    assert payload["attributes"]["visible"] == "data"


def test_redact_private_key_in_attributes():
    event = IngestAuditEvent(
        request_id="r3", actor="tester", action="test",
        resource_type="test", resource_id="r3", decision="ALLOW",
        result="SUCCESS", reason_code=None, http_status=200,
        trace_id=None, client_ip=None, node_id="n1",
        timestamp=datetime.now(tz=UTC),
        attributes={"private_key": "abc123", "cert_secret": "xyz"},
    )
    payload = event.sanitized_payload()
    assert payload["attributes"]["private_key"] == "***REDACTED***"
    assert payload["attributes"]["cert_secret"] == "***REDACTED***"


def test_redact_nested_attributes():
    data = {"outer": {"password": "secret", "inner": {"token": "tok"}}}
    result = redact_value(data)
    assert result["outer"]["password"] == "***REDACTED***"
    assert result["outer"]["inner"]["token"] == "***REDACTED***"
