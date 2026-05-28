"""Audit and metrics resilience tests under prodlike dependency failures."""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tests.support.ingest_prodlike_runtime import ensure_prodlike_stack, start_service, stop_prodlike_stack, stop_service
from whale.ingest.adapters.audit import DualIngestAuditSink
from whale.ingest.adapters.audit.db_audit_sink import DbIngestAuditSink
from whale.ingest.adapters.message.kafka_message_publisher import KafkaMessagePublisher
from whale.ingest.adapters.observability.file_sinks import JsonlIngestAuditSink, JsonlIngestMetricsSink
from whale.ingest.adapters.state.redis_source_state_cache import (
    RedisSourceStateCache,
    RedisSourceStateCacheSettings,
)
from whale.ingest.decorators.state_cache import AuditedStateCachePort
from whale.ingest.domain.audit_event import IngestAuditEvent
from whale.ingest.framework.persistence import create_runtime_engine, create_runtime_session_factory
from whale.ingest.runtime.message_pipeline_settings import KafkaMessageSettings
from whale.ingest.usecases.dtos.acquired_node_state import AcquiredNodeStateBatch, AcquiredNodeValue
from whale.ingest.usecases.dtos.state_publish_request import StateSnapshotPublishRequest
from whale.ingest.usecases.state_snapshot_publish_use_case import StateSnapshotPublishUseCase
from whale.shared.crosscutting.compliance import AuditEvent, AuditEventSinkPort


@dataclass
class _AuditSink(AuditEventSinkPort):
    events: list[AuditEvent] = field(default_factory=list)

    def emit(self, event: AuditEvent) -> None:
        self.events.append(event)


def _cache() -> RedisSourceStateCache:
    return RedisSourceStateCache(
        settings=RedisSourceStateCacheSettings(
            redis_url="redis://127.0.0.1:16379/4",
            host="127.0.0.1",
            port=16379,
            db=4,
            username=None,
            password=None,
            hash_key="whale:ingest:audit:metrics",
            station_id="whale-prod",
            socket_connect_timeout_seconds=0.5,
        )
    )


def _batch() -> AcquiredNodeStateBatch:
    now = datetime.now(tz=UTC)
    return AcquiredNodeStateBatch(
        source_id="source-1",
        batch_observed_at=now,
        client_received_at=now,
        client_processed_at=now,
        values=[
            AcquiredNodeValue(
                node_key="TotW",
                value="7",
                quality="GOOD",
                source_timestamp=now,
                server_timestamp=now,
            )
        ],
    )


def _publisher() -> KafkaMessagePublisher:
    return KafkaMessagePublisher(
        settings=KafkaMessageSettings(
            bootstrap_servers=("127.0.0.1:9092",),
            topic="whale.ingest.audit.metrics",
            ack_timeout_seconds=2.0,
            acks="all",
            retries=1,
            request_timeout_ms=1500,
            key_strategy="source_id",
        )
    )


@pytest.fixture(scope="module", autouse=True)
def prodlike_resilience_stack():
    ensure_prodlike_stack()
    yield
    stop_prodlike_stack()


@pytest.mark.integration
def test_audit_events_continue_during_redis_failure() -> None:
    audit_sink = _AuditSink()
    cache = AuditedStateCachePort(inner=_cache(), audit_sink=audit_sink)

    stop_service("redis")
    try:
        with pytest.raises(Exception):
            cache.update(ld_name="LD0", batch=_batch())
    finally:
        start_service("redis")

    assert audit_sink.events
    assert audit_sink.events[0].outcome == "failure"


@pytest.mark.integration
def test_metrics_continue_during_kafka_failure(tmp_path: Path) -> None:
    cache = _cache()
    cache.update(ld_name="LD0", batch=_batch())
    metrics_path = tmp_path / "kafka-metrics.jsonl"
    use_case = StateSnapshotPublishUseCase(
        reader=cache,
        publisher=_publisher(),
        station_id="whale-prod",
        metrics_port=JsonlIngestMetricsSink(metrics_path),
    )

    stop_service("kafka")
    try:
        use_case.execute(StateSnapshotPublishRequest(trace_id="kafka-failure-trace"))
    finally:
        start_service("kafka")

    lines = metrics_path.read_text(encoding="utf-8").splitlines()
    assert lines
    payload = json.loads(lines[-1])
    assert payload["status"] in {"FAILED", "PARTIAL"}


@pytest.mark.integration
def test_audit_db_failure_visible_and_jsonl_fallback_works() -> None:
    temp_jsonl = Path(tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False).name)
    try:
        bad_sink = DbIngestAuditSink(
            create_runtime_session_factory(
                create_runtime_engine("postgresql+psycopg://whale:whale@127.0.0.1:1/missing")
            )
        )
        sink = DualIngestAuditSink(bad_sink, JsonlIngestAuditSink(temp_jsonl))
        sink.emit(
            IngestAuditEvent(
                request_id="audit-db-failure",
                actor="tester",
                action="audit.failure",
                resource_type="audit",
                resource_id="fallback",
                decision="ALLOW",
                result="FAILED",
                reason_code="DB_DOWN",
                http_status=None,
                trace_id=None,
                client_ip=None,
                node_id="test-node",
            )
        )

        assert sink.last_error is not None
        payload = json.loads(temp_jsonl.read_text(encoding="utf-8").splitlines()[0])
        assert payload["request_id"] == "audit-db-failure"
    finally:
        temp_jsonl.unlink(missing_ok=True)


@pytest.mark.integration
def test_sensitive_fields_redacted_in_failure_events(tmp_path: Path) -> None:
    path = tmp_path / "audit-redaction.jsonl"
    sink = JsonlIngestAuditSink(path)
    sink.emit(
        IngestAuditEvent(
            request_id="redaction-failure",
            actor="tester",
            action="failure.redaction",
            resource_type="audit",
            resource_id="secret-resource",
            decision="DENY",
            result="FAILED",
            reason_code="SECRET_PRESENT",
            http_status=500,
            trace_id=None,
            client_ip=None,
            node_id="test-node",
            attributes={"password": "secret", "nested": {"private_key": "value"}},
        )
    )

    payload = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert payload["attributes"]["password"] == "***REDACTED***"
    assert payload["attributes"]["nested"]["private_key"] == "***REDACTED***"
