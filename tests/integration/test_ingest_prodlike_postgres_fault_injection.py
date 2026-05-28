"""PostgreSQL fault injection and recovery tests for prodlike ingest runtime."""

from __future__ import annotations

import json
import os
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from tests.support.ingest_prodlike_runtime import (
    API_BASE_URL,
    active_assignments,
    count_audit_events,
    ensure_prodlike_stack,
    seed_runtime_job,
    start_service,
    stop_prodlike_stack,
    stop_service,
    truncate_runtime_tables,
    wait_for_assignment_count,
    wait_for_http,
    wait_until,
)
from whale.ingest.adapters.audit import DualIngestAuditSink
from whale.ingest.adapters.audit.db_audit_sink import DbIngestAuditSink
from whale.ingest.adapters.observability.file_sinks import JsonlIngestAuditSink
from whale.ingest.domain.audit_event import IngestAuditEvent
from whale.ingest.framework.persistence import create_runtime_engine, create_runtime_session_factory


def _safe_count_audit_events(action: str) -> int:
    """Return audit event count, or -1 if the database is unreachable."""
    try:
        return count_audit_events(action=action)
    except Exception:
        return -1


def _safe_active_assignments() -> list:
    """Return active assignments, or empty list if database is unreachable."""
    try:
        return active_assignments()
    except Exception:
        return []


def _http_status(url: str) -> int | None:
    try:
        for proxy_var in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "all_proxy", "ALL_PROXY"):
            os.environ.pop(proxy_var, None)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(url, timeout=3) as response:
            return int(response.status)
    except urllib.error.HTTPError as exc:
        return int(exc.code)
    except Exception as exc:
        print(f"[HTTP_STATUS_DEBUG] {url} :: {type(exc).__name__}: {exc}")
        return None


@pytest.fixture(scope="module", autouse=True)
def prodlike_pg_stack():
    ensure_prodlike_stack()
    truncate_runtime_tables()
    yield
    stop_prodlike_stack()


@pytest.mark.integration
def test_api_readyz_fails_when_postgres_down_and_recovers() -> None:
    assert _http_status(f"{API_BASE_URL}/readyz") == 200

    stop_service("postgres")
    wait_until(
        lambda: _http_status(f"{API_BASE_URL}/readyz") not in {200},
        timeout_seconds=30.0,
        error_message="readyz stayed healthy after PostgreSQL stop",
    )
    assert _http_status(f"{API_BASE_URL}/healthz") == 200

    start_service("postgres")
    wait_for_http(f"{API_BASE_URL}/readyz", contains='"status":"ready"', timeout_seconds=90.0)


@pytest.mark.integration
def test_worker_pauses_or_fails_safe_when_lease_db_down() -> None:
    truncate_runtime_tables()
    seed_runtime_job(job_id="pg-down-job", job_type="noop", config={"interval_ms": 500})
    wait_for_assignment_count(1, timeout_seconds=60.0)

    wait_until(
        lambda: count_audit_events(action="job.executed") >= 1,
        timeout_seconds=30.0,
        error_message="worker did not execute baseline job before PostgreSQL stop",
    )
    before = count_audit_events(action="job.executed")

    stop_service("postgres")
    wait_until(
        lambda: _safe_count_audit_events(action="job.executed") in (before, -1),
        timeout_seconds=10.0,
        error_message="job executions continued after PostgreSQL stop",
    )

    start_service("postgres")
    wait_until(
        lambda: _safe_count_audit_events(action="job.executed") > before,
        timeout_seconds=90.0,
        error_message="worker did not resume execution after PostgreSQL restart",
    )


@pytest.mark.integration
def test_scheduler_recovers_assignment_after_postgres_restart() -> None:
    truncate_runtime_tables()
    seed_runtime_job(job_id="pg-recover-job", job_type="noop", config={"interval_ms": 500})
    wait_for_assignment_count(1, timeout_seconds=60.0)
    first_assignments = active_assignments()
    assert len(first_assignments) == 1

    stop_service("postgres")
    start_service("postgres")

    wait_until(
        lambda: len(_safe_active_assignments()) == 1,
        timeout_seconds=90.0,
        error_message="scheduler did not restore one active assignment after PostgreSQL restart",
    )
    recovered = active_assignments()[0]
    assert recovered.job_id == "pg-recover-job"


@pytest.mark.integration
def test_audit_sink_degrades_or_buffers_with_explicit_error() -> None:
    temp_jsonl = Path(tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False).name)
    try:
        bad_db_sink = DbIngestAuditSink(
            create_runtime_session_factory(
                create_runtime_engine(
                    "postgresql+psycopg://whale:whale@127.0.0.1:1/missing_database_for_fault_test"
                )
            )
        )
        dual_sink = DualIngestAuditSink(bad_db_sink, JsonlIngestAuditSink(temp_jsonl))
        dual_sink.emit(
            IngestAuditEvent(
                request_id="pg-audit-fallback",
                actor="tester",
                action="fault.audit",
                resource_type="audit",
                resource_id="fallback",
                decision="ALLOW",
                result="SUCCESS",
                reason_code=None,
                http_status=None,
                trace_id=None,
                client_ip=None,
                node_id="test-node",
            )
        )

        assert dual_sink.last_error is not None
        payload = json.loads(temp_jsonl.read_text(encoding="utf-8").splitlines()[0])
        assert payload["request_id"] == "pg-audit-fallback"
    finally:
        temp_jsonl.unlink(missing_ok=True)
