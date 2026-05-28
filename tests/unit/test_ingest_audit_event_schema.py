"""Structured ingest audit event tests."""

from __future__ import annotations

from whale.ingest.domain.audit_event import IngestAuditEvent


def test_audit_event_redacts_sensitive_attributes() -> None:
    event = IngestAuditEvent(
        request_id="r1",
        actor="tester",
        action="acquisition_task.read",
        resource_type="acquisition_task",
        resource_id="1",
        decision="ALLOW",
        result="SUCCESS",
        reason_code=None,
        http_status=200,
        trace_id="t1",
        client_ip="127.0.0.1",
        node_id="node-1",
        attributes={
            "password": "secret",
            "token_value": "abc",
            "nested": {"private_key": "pem", "safe": "ok"},
        },
    )

    payload = event.sanitized_payload()
    assert payload["attributes"]["password"] == "***REDACTED***"
    assert payload["attributes"]["token_value"] == "***REDACTED***"
    assert payload["attributes"]["nested"]["private_key"] == "***REDACTED***"
    assert payload["attributes"]["nested"]["safe"] == "ok"
