"""Reconnect baseline read strategy tests for SubscriptionAcquisitionRole."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime

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
    async def close(self) -> None:
        return None


@dataclass
class _StateCache:
    updates: list[str] = field(default_factory=list)
    alives: list[str] = field(default_factory=list)
    unavailable: list[str] = field(default_factory=list)

    def update(self, *, ld_name: str, batch: AcquiredNodeStateBatch) -> int:
        del batch
        self.updates.append(ld_name)
        return 1

    def mark_alive(self, *, ld_name: str, observed_at: datetime) -> None:
        del observed_at
        self.alives.append(ld_name)

    def mark_unavailable(self, *, ld_name: str, status: str, observed_at: datetime, reason: str | None = None) -> None:
        del status, observed_at, reason
        self.unavailable.append(ld_name)


class _Port:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def supports_subscription(self, execution, connection) -> bool:
        del execution, connection
        self.calls.append("supports")
        return True

    async def read(self, execution, connection, items):
        del execution, connection, items
        self.calls.append("read")
        now = datetime.now(tz=UTC)
        return AcquiredNodeStateBatch(
            source_id="s1",
            batch_observed_at=now,
            client_received_at=now,
            client_processed_at=now,
            values=[AcquiredNodeValue(node_key="k", value="1", quality="GOOD")],
        )

    async def start_subscription(
        self,
        execution,
        connection,
        items,
        *,
        state_received: SubscriptionStateHandler,
    ) -> SourceSubscriptionHandle:
        del execution, connection, items, state_received
        self.calls.append("subscribe")
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
            freshness_timeout_ms=30_000,
            alive_timeout_ms=60_000,
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
        items=[AcquisitionItemData(key="k", profile_item_id=1, relative_path="k")],
    )


def test_reconnect_attempt_replays_baseline_before_resubscribe() -> None:
    port = _Port()
    cache = _StateCache()
    role = SubscriptionAcquisitionRole(acquisition_port=port, state_cache_port=cache)
    request = _request()

    # first subscription start
    asyncio.run(role.start(request))
    # simulate reconnect by starting again with same request
    asyncio.run(role.start(request))

    assert port.calls == [
        "supports", "read", "subscribe",
        "supports", "read", "subscribe",
    ]
    assert cache.updates == ["LD1", "LD1"]
    assert cache.alives == ["LD1", "LD1"]
