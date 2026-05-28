"""External audit/SIEM sink contract tests with a local HTTP stub server."""

from __future__ import annotations

import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import pytest

from whale.ingest.adapters.audit import DualIngestAuditSink, HttpIngestAuditSink
from whale.ingest.adapters.observability.file_sinks import JsonlIngestAuditSink
from whale.ingest.domain.audit_event import IngestAuditEvent


class _StubAuditHandler(BaseHTTPRequestHandler):
    """Collects received events and status codes."""

    received_events: list[list[dict[str, Any]]] = []
    status_code: int = 200

    def do_POST(self) -> None:  # type: ignore[override]
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length > 0 else b"{}"
        payload = json.loads(body.decode("utf-8"))
        self.__class__.received_events.append(payload)
        resp = json.dumps({"status": "ok"}).encode("utf-8")
        self.send_response(self.__class__.status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp)))
        self.end_headers()
        self.wfile.write(resp)

    def log_message(self, fmt: str, *args: Any) -> None:
        pass


@pytest.fixture(autouse=True)
def _reset_stub():
    _StubAuditHandler.received_events.clear()
    _StubAuditHandler.status_code = 200


def _stub_server(status: int = 200) -> tuple[str, HTTPServer]:
    _StubAuditHandler.status_code = status
    server = HTTPServer(("127.0.0.1", 0), _StubAuditHandler)
    port = server.server_port
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return f"http://127.0.0.1:{port}", server


def _event(request_id: str = "test-event", **overrides: Any) -> IngestAuditEvent:
    kwargs: dict[str, Any] = {
        "request_id": request_id,
        "actor": "tester",
        "action": "test.action",
        "resource_type": "test",
        "resource_id": "test-resource",
        "decision": "ALLOW",
        "result": "SUCCESS",
        "reason_code": None,
        "http_status": 200,
        "trace_id": None,
        "client_ip": None,
        "node_id": "test-node",
    }
    kwargs.update(overrides)
    return IngestAuditEvent(**kwargs)


class TestExternalAuditSinkContract:

    @pytest.mark.integration
    def test_http_audit_sink_sends_event_to_stub(self) -> None:
        url, server = _stub_server()
        try:
            sink = HttpIngestAuditSink(url, timeout_seconds=3.0, batch_size=1)
            sink.emit(_event("stub-test-1"))
            sink.flush()
            assert _StubAuditHandler.received_events
            events = _StubAuditHandler.received_events[0]
            assert len(events) == 1
            assert events[0]["request_id"] == "stub-test-1"
        finally:
            server.shutdown()

    @pytest.mark.integration
    def test_http_audit_sink_batches_events(self) -> None:
        url, server = _stub_server()
        try:
            sink = HttpIngestAuditSink(url, timeout_seconds=3.0, batch_size=3)
            sink.emit(_event("batch-1"))
            sink.emit(_event("batch-2"))
            # Should auto-flush on third event
            sink.emit(_event("batch-3"))
            assert _StubAuditHandler.received_events
            last_batch = _StubAuditHandler.received_events[-1]
            assert len(last_batch) == 3
        finally:
            server.shutdown()

    @pytest.mark.integration
    def test_http_audit_sink_failure_records_last_error(self) -> None:
        sink = HttpIngestAuditSink(
            "http://127.0.0.1:1",
            timeout_seconds=1.0,
            batch_size=1,
        )
        sink.emit(_event("fail-event"))
        sink.flush()
        assert sink.last_error is not None

    @pytest.mark.integration
    def test_http_audit_sink_jsonl_fallback(self) -> None:
        """When the HTTP sink fails, a paired JSONL fallback still captures events."""
        jsonl_path = Path(NamedTemporaryFile(suffix=".jsonl", delete=False).name)
        try:
            http_sink = HttpIngestAuditSink(
                "http://127.0.0.1:1",
                timeout_seconds=1.0,
                batch_size=1,
            )
            jsonl_sink = JsonlIngestAuditSink(jsonl_path)
            dual = DualIngestAuditSink(http_sink, jsonl_sink)
            dual.emit(_event("fallback-test"))

            # HTTP sink should have last_error, but JSONL should still have the event
            assert http_sink.last_error is not None
            lines = jsonl_path.read_text(encoding="utf-8").splitlines()
            assert any("fallback-test" in line for line in lines)
        finally:
            jsonl_path.unlink(missing_ok=True)

    @pytest.mark.integration
    def test_http_audit_sink_redacts_sensitive_fields(self) -> None:
        url, server = _stub_server()
        try:
            sink = HttpIngestAuditSink(url, timeout_seconds=3.0, batch_size=1)
            sink.emit(_event(
                "redact-test",
                attributes={"password": "secret123", "nested": {"private_key": "mykey"}},
            ))
            sink.flush()
            assert _StubAuditHandler.received_events
            payload = _StubAuditHandler.received_events[0][0]
            attrs = payload.get("attributes", {})
            assert attrs.get("password") == "***REDACTED***"
            assert attrs.get("nested", {}).get("private_key") == "***REDACTED***"
        finally:
            server.shutdown()
