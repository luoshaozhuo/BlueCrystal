"""Redis fault injection and recovery tests for prodlike ingest runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
import urllib.request

import pytest

from tests.support.ingest_prodlike_runtime import (
    API_BASE_URL,
    ensure_prodlike_stack,
    start_service,
    stop_prodlike_stack,
    stop_service,
    wait_for_http,
)
from whale.ingest.adapters.state.redis_source_state_cache import (
    RedisSourceStateCache,
    RedisSourceStateCacheSettings,
)
from whale.ingest.decorators.state_cache import AuditedStateCachePort, MetricsStateCachePort
from whale.ingest.ports.state import SourceStateCacheWriteError
from whale.ingest.usecases.dtos.acquired_node_state import (
    AcquiredNodeStateBatch,
    AcquiredNodeValue,
)
from whale.shared.crosscutting.compliance import AuditEvent, AuditEventSinkPort
from whale.shared.crosscutting.observability import MetricsSinkPort


def _settings() -> RedisSourceStateCacheSettings:
    return RedisSourceStateCacheSettings(
        redis_url="redis://127.0.0.1:16379/2",
        host="127.0.0.1",
        port=16379,
        db=2,
        username=None,
        password=None,
        hash_key="whale:ingest:redis:fault",
        station_id="whale-prod",
        socket_connect_timeout_seconds=0.5,
    )


def _batch(value: str) -> AcquiredNodeStateBatch:
    now = datetime.now(tz=UTC)
    return AcquiredNodeStateBatch(
        source_id="redis-fault-source",
        batch_observed_at=now,
        client_received_at=now,
        client_processed_at=now,
        values=[
            AcquiredNodeValue(
                node_key="TotW",
                value=value,
                quality="GOOD",
                source_timestamp=now,
                server_timestamp=now,
            )
        ],
    )


@dataclass
class _AuditSink(AuditEventSinkPort):
    events: list[AuditEvent] = field(default_factory=list)

    def emit(self, event: AuditEvent) -> None:
        self.events.append(event)


@dataclass
class _MetricsSink(MetricsSinkPort):
    counters: dict[str, int] = field(default_factory=dict)

    def increment(self, metric_name: str, value: int = 1, **labels: str) -> None:
        del labels
        self.counters[metric_name] = self.counters.get(metric_name, 0) + value

    def observe_duration(self, metric_name: str, duration_seconds: float, **labels: str) -> None:
        del duration_seconds, labels
        self.counters.setdefault(metric_name, 0)


@pytest.fixture(scope="module", autouse=True)
def prodlike_redis_stack():
    ensure_prodlike_stack()
    yield
    stop_prodlike_stack()


@pytest.mark.integration
def test_source_cache_write_failure_is_classified() -> None:
    cache = RedisSourceStateCache(settings=_settings())
    stop_service("redis")
    try:
        with pytest.raises(SourceStateCacheWriteError) as exc_info:
            cache.update(ld_name="LD0", batch=_batch("1"))
        assert exc_info.value.error_code.startswith("redis_")
    finally:
        start_service("redis")


@pytest.mark.integration
def test_source_cache_recovers_after_redis_restart() -> None:
    cache = RedisSourceStateCache(settings=_settings())
    cache.update(ld_name="LD0", batch=_batch("2"))

    stop_service("redis")
    start_service("redis")
    wait_for_http(f"{API_BASE_URL}/healthz", contains='"status":"ok"', timeout_seconds=60.0)

    updated = cache.update(ld_name="LD0", batch=_batch("3"))
    assert updated == 1


@pytest.mark.integration
def test_cache_failure_does_not_crash_api_runtime() -> None:
    stop_service("redis")
    try:
        with urllib.request.urlopen(f"{API_BASE_URL}/healthz", timeout=3) as response:
            assert response.status == 200
    finally:
        start_service("redis")


@pytest.mark.integration
def test_cache_failure_metrics_and_audit_are_emitted() -> None:
    metrics_sink = _MetricsSink()
    audit_sink = _AuditSink()
    cache = RedisSourceStateCache(settings=_settings())
    wrapped = MetricsStateCachePort(
        inner=AuditedStateCachePort(inner=cache, audit_sink=audit_sink),
        metrics_sink=metrics_sink,
    )

    stop_service("redis")
    try:
        with pytest.raises(SourceStateCacheWriteError):
            wrapped.update(ld_name="LD0", batch=_batch("4"))
    finally:
        start_service("redis")

    assert metrics_sink.counters.get("ingest_state_cache_update_failed_total", 0) >= 1
    assert len(audit_sink.events) >= 1
    assert audit_sink.events[0].outcome == "failure"
