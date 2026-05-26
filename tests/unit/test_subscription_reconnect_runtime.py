"""Subscription runtime reconnect/backoff/max-retry tests."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime

import pytest

from whale.ingest.ports.metrics import IngestMetricEvent, IngestMetricsPort
from whale.ingest.ports.source.source_acquisition_port import (
    SourceSubscriptionHandle,
    SubscriptionStateHandler,
)
from whale.ingest.usecases.dtos.acquired_node_state import (
    AcquiredNodeStateBatch,
    AcquiredNodeValue,
)
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
    SourceAcquisitionRequest,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.ingest.usecases.roles.subscription_acquisition_role import (
    SubscriptionAcquisitionRole,
)


@dataclass(slots=True)
class _Handle(SourceSubscriptionHandle):
    closed: bool = False

    async def close(self) -> None:
        self.closed = True


@dataclass
class _Metrics(IngestMetricsPort):
    events: list[IngestMetricEvent] = field(default_factory=list)

    def emit(self, event: IngestMetricEvent) -> None:
        self.events.append(event)


class _Cache:
    def update(self, *, ld_name, batch):
        del ld_name, batch
        return 1

    def mark_alive(self, *, ld_name, observed_at):
        del ld_name, observed_at

    def mark_unavailable(self, *, ld_name, status, observed_at, reason=None):
        del ld_name, status, observed_at, reason


class _Port:
    def __init__(self, *, fail_times: int) -> None:
        self.fail_times = fail_times
        self.read_calls = 0
        self.sub_calls = 0

    def supports_subscription(self, execution, connection):
        del execution, connection
        return True

    async def read(self, execution, connection, items):
        del execution, connection, items
        self.read_calls += 1
        now = datetime.now(tz=UTC)
        return AcquiredNodeStateBatch(
            source_id="s1",
            batch_observed_at=now,
            client_received_at=now,
            client_processed_at=now,
            values=[AcquiredNodeValue(node_key="k1", value="1", quality="GOOD")],
        )

    async def start_subscription(self, execution, connection, items, *, state_received: SubscriptionStateHandler):
        del execution, connection, items, state_received
        self.sub_calls += 1
        if self.sub_calls <= self.fail_times:
            raise RuntimeError("subscribe_failed")
        return _Handle()


def _request() -> SourceAcquisitionRequest:
    return SourceAcquisitionRequest(
        request_id="req-1",
        task_id=1,
        execution=AcquisitionExecutionOptions(
            protocol="opcua",
            transport="tcp",
            acquisition_mode="SUBSCRIBE",
            interval_ms=100,
            max_iteration=None,
            request_timeout_ms=1000,
            freshness_timeout_ms=1000,
            alive_timeout_ms=1000,
            params={"subscription_max_retry": 2, "subscription_backoff_ms": 1},
        ),
        connections=[
            SourceConnectionData(
                host="127.0.0.1",
                port=4840,
                ied_name="IED1",
                ld_name="LD1",
                namespace_uri="",
            )
        ],
        items=[AcquisitionItemData(key="k1", profile_item_id=1, relative_path="k1")],
    )


def test_subscription_reconnect_runtime_succeeds_before_max_retry() -> None:
    metrics = _Metrics()
    port = _Port(fail_times=1)
    role = SubscriptionAcquisitionRole(
        acquisition_port=port,
        state_cache_port=_Cache(),
        metrics_port=metrics,
    )
    result = asyncio.run(role.start(_request()))
    assert result.mode == "SUBSCRIBE"
    assert port.read_calls == 2
    assert port.sub_calls == 2
    ops = [e.operation for e in metrics.events]
    assert "subscription_reconnect" in ops
    assert "subscription_start" in ops


def test_subscription_reconnect_runtime_fails_after_max_retry() -> None:
    metrics = _Metrics()
    port = _Port(fail_times=10)
    role = SubscriptionAcquisitionRole(
        acquisition_port=port,
        state_cache_port=_Cache(),
        metrics_port=metrics,
    )
    with pytest.raises(RuntimeError, match="subscribe_failed"):
        asyncio.run(role.start(_request()))
    assert port.sub_calls == 3
    failed = [e for e in metrics.events if e.operation == "subscription_reconnect" and e.status == "FAILED"]
    assert len(failed) >= 1
