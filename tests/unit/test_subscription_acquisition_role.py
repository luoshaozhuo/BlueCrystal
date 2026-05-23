"""SubscriptionAcquisitionRole unit tests."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime

import pytest

from whale.ingest.ports.source.source_acquisition_port import (
    SourceSubscriptionHandle,
    SourceSubscriptionUnsupportedError,
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


@dataclass
class FakeStateCachePort:
    """Record state-cache calls."""

    updates: list[tuple[str, AcquiredNodeStateBatch]] = field(default_factory=list)
    alive_marks: list[str] = field(default_factory=list)
    unavailable_marks: list[tuple[str, str, str | None]] = field(default_factory=list)

    def update(self, *, ld_name: str, batch: AcquiredNodeStateBatch) -> int:
        self.updates.append((ld_name, batch))
        return len(batch.values)

    def mark_alive(self, *, ld_name: str, observed_at: datetime) -> None:
        del observed_at
        self.alive_marks.append(ld_name)

    def mark_unavailable(
        self,
        *,
        ld_name: str,
        status: str,
        observed_at: datetime,
        reason: str | None = None,
    ) -> None:
        del observed_at
        self.unavailable_marks.append((ld_name, status, reason))


@dataclass(slots=True)
class FakeSubscriptionHandle(SourceSubscriptionHandle):
    """Track close calls for subscription tests."""

    closed: bool = False

    async def close(self) -> None:
        self.closed = True


class FakeAcquisitionPort:
    """Configurable fake source acquisition port."""

    def __init__(self, *, supports_subscription: bool) -> None:
        self.supports_subscription_value = supports_subscription
        self.read_calls = 0
        self.start_subscription_calls = 0
        self.call_order: list[str] = []

    def supports_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> bool:
        del execution, connection
        self.call_order.append("supports_subscription")
        return self.supports_subscription_value

    async def read(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> AcquiredNodeStateBatch:
        del execution, items
        self.read_calls += 1
        self.call_order.append("read")
        now = datetime.now(tz=UTC)
        return AcquiredNodeStateBatch(
            source_id=connection.ld_name,
            batch_observed_at=now,
            client_received_at=now,
            client_processed_at=now,
            values=[AcquiredNodeValue(node_key="TotW", value="1", quality="GOOD")],
        )

    async def start_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
        *,
        state_received: SubscriptionStateHandler,
    ) -> SourceSubscriptionHandle:
        del execution, connection, items, state_received
        self.start_subscription_calls += 1
        self.call_order.append("start_subscription")
        if not self.supports_subscription_value:
            raise SourceSubscriptionUnsupportedError("subscription_unsupported")
        return FakeSubscriptionHandle()


def _request() -> SourceAcquisitionRequest:
    return SourceAcquisitionRequest(
        request_id="request-1",
        task_id=1,
        execution=AcquisitionExecutionOptions(
            protocol="opcua",
            transport="tcp",
            acquisition_mode="SUBSCRIBE",
            interval_ms=1000,
            max_iteration=None,
            request_timeout_ms=500,
            freshness_timeout_ms=30_000,
            alive_timeout_ms=60_000,
        ),
        connections=[
            SourceConnectionData(
                host="127.0.0.1",
                port=4840,
                ied_name="IED_01",
                ld_name="LD_01",
                namespace_uri="urn:test",
            )
        ],
        items=[AcquisitionItemData(key="TotW", profile_item_id=1, relative_path="TotW")],
    )


def test_subscription_unsupported_marks_connection_unavailable_and_raises() -> None:
    state_cache = FakeStateCachePort()
    acquisition_port = FakeAcquisitionPort(supports_subscription=False)
    role = SubscriptionAcquisitionRole(
        acquisition_port=acquisition_port,
        state_cache_port=state_cache,
    )

    with pytest.raises(SourceSubscriptionUnsupportedError, match="subscription_unsupported"):
        asyncio.run(role.start(_request()))

    assert acquisition_port.read_calls == 0
    assert acquisition_port.start_subscription_calls == 0
    assert state_cache.updates == []
    assert state_cache.alive_marks == []
    assert state_cache.unavailable_marks == [("LD_01", "ERROR", "subscription_unsupported")]


def test_supported_subscription_reads_baseline_before_starting_subscription() -> None:
    state_cache = FakeStateCachePort()
    acquisition_port = FakeAcquisitionPort(supports_subscription=True)
    role = SubscriptionAcquisitionRole(
        acquisition_port=acquisition_port,
        state_cache_port=state_cache,
    )

    result = asyncio.run(role.start(_request()))

    assert result.mode == "SUBSCRIBE"
    assert acquisition_port.call_order == [
        "supports_subscription",
        "read",
        "start_subscription",
    ]
    assert len(state_cache.updates) == 1
    assert state_cache.alive_marks == ["LD_01"]
    assert state_cache.unavailable_marks == []
