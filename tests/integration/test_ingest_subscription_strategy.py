"""Integration tests for current subscription strategy boundaries."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import pytest

from whale.ingest.adapters.source.opcua_source_acquisition_adapter import (
    OpcUaSourceAcquisitionAdapter,
)
from whale.ingest.adapters.state.redis_source_state_cache import (
    RedisSourceStateCache,
    RedisSourceStateCacheSettings,
)
from whale.ingest.ports.source.source_acquisition_port import (
    SourceAcquisitionPort,
    SourceSubscriptionHandle,
    SourceSubscriptionUnsupportedError,
    SubscriptionStateHandler,
)
from whale.ingest.usecases import SourceAcquisitionUseCase
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
from whale.ingest.usecases.roles.polling_acquisition_role import PollingAcquisitionRole
from whale.ingest.usecases.roles.subscription_acquisition_role import (
    SubscriptionAcquisitionRole,
)


@pytest.mark.integration
def test_subscription_unsupported_fails_fast_without_baseline_cache_write(
    real_redis_client: Any,
    real_redis_hash_key: str,
) -> None:
    """Do not baseline-read or write cache when the adapter reports unsupported subscription."""

    cache = RedisSourceStateCache(
        settings=RedisSourceStateCacheSettings(
            host="127.0.0.1",
            port=16379,
            db=15,
            username=None,
            password=None,
            hash_key=real_redis_hash_key,
            station_id="station-subscription",
        ),
        client=real_redis_client,
    )
    adapter = OpcUaSourceAcquisitionAdapter()
    use_case = SourceAcquisitionUseCase(
        polling_role=PollingAcquisitionRole(
            acquisition_port=adapter,
            state_cache_port=cache,
        ),
        subscription_role=SubscriptionAcquisitionRole(
            acquisition_port=adapter,
            state_cache_port=cache,
        ),
    )
    request = SourceAcquisitionRequest(
        request_id="subscription-unsupported",
        task_id=21,
        execution=AcquisitionExecutionOptions(
            protocol="opcua",
            transport="tcp",
            acquisition_mode="SUBSCRIBE",
            interval_ms=100,
            max_iteration=None,
            request_timeout_ms=1_000,
            freshness_timeout_ms=30_000,
            alive_timeout_ms=60_000,
        ),
        connections=[
            SourceConnectionData(
                host="127.0.0.1",
                port=4840,
                ied_name="IED_SUB",
                ld_name="LD_SUB",
                namespace_uri="urn:test:sub",
            )
        ],
        items=[AcquisitionItemData(key="TotW", profile_item_id=1, relative_path="TotW")],
    )

    try:
        with pytest.raises(SourceSubscriptionUnsupportedError, match="subscription_unsupported"):
            asyncio.run(use_case.start(request))

        snapshot = cache.read_snapshot()
        assert snapshot == [] or (
            len(snapshot) == 1
            and snapshot[0].availability_status == "ERROR"
            and snapshot[0].unavailable_reason == "subscription_unsupported"
            and snapshot[0].values == []
            and snapshot[0].last_alive_at is None
        )
    finally:
        real_redis_client.delete(real_redis_hash_key)


@dataclass(slots=True)
class _FakeSubscriptionHandle(SourceSubscriptionHandle):
    closed: bool = False

    async def close(self) -> None:
        self.closed = True


@dataclass
class _SequencedSubscriptionPort(SourceAcquisitionPort):
    supports_value: bool = True
    call_order: list[str] = field(default_factory=list)

    def supports_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> bool:
        del execution, connection
        self.call_order.append("supports_subscription")
        return self.supports_value

    async def read(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> AcquiredNodeStateBatch:
        del execution, items
        self.call_order.append("baseline_read")
        now = datetime.now(tz=UTC)
        return AcquiredNodeStateBatch(
            source_id=connection.ld_name,
            batch_observed_at=now,
            client_received_at=now,
            client_processed_at=now,
            values=[AcquiredNodeValue(node_key="TotW", value="42.0", quality="GOOD")],
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
        self.call_order.append("start_subscription")
        return _FakeSubscriptionHandle()


@pytest.mark.integration
def test_subscription_supported_strategy_baseline_before_start_with_real_redis_cache(
    real_redis_client: Any,
    real_redis_hash_key: str,
) -> None:
    """Current strategy is baseline read -> cache update -> mark_alive -> start_subscription.

    Future reconnect behavior follows the same rule: reconnect must perform a
    fresh baseline read before starting a new subscription handle again.
    """

    acquisition_port = _SequencedSubscriptionPort()
    cache = RedisSourceStateCache(
        settings=RedisSourceStateCacheSettings(
            host="127.0.0.1",
            port=16379,
            db=15,
            username=None,
            password=None,
            hash_key=real_redis_hash_key,
            station_id="station-subscription-sequenced",
        ),
        client=real_redis_client,
    )
    use_case = SourceAcquisitionUseCase(
        polling_role=PollingAcquisitionRole(
            acquisition_port=acquisition_port,
            state_cache_port=cache,
        ),
        subscription_role=SubscriptionAcquisitionRole(
            acquisition_port=acquisition_port,
            state_cache_port=cache,
        ),
    )
    request = SourceAcquisitionRequest(
        request_id="subscription-supported",
        task_id=22,
        execution=AcquisitionExecutionOptions(
            protocol="opcua",
            transport="tcp",
            acquisition_mode="SUBSCRIBE",
            interval_ms=100,
            max_iteration=None,
            request_timeout_ms=1_000,
            freshness_timeout_ms=30_000,
            alive_timeout_ms=60_000,
        ),
        connections=[
            SourceConnectionData(
                host="127.0.0.1",
                port=4840,
                ied_name="IED_SUB",
                ld_name="LD_SUB",
                namespace_uri="urn:test:sub",
            )
        ],
        items=[AcquisitionItemData(key="TotW", profile_item_id=1, relative_path="TotW")],
    )

    try:
        result = asyncio.run(use_case.start(request))
        snapshot = cache.read_snapshot()

        assert acquisition_port.call_order == [
            "supports_subscription",
            "baseline_read",
            "start_subscription",
        ]
        assert len(result.sessions) == 1
        assert len(snapshot) == 1
        assert snapshot[0].availability_status == "VALID"
        assert snapshot[0].values[0].value == "42.0"
        assert snapshot[0].last_alive_at is not None
    finally:
        real_redis_client.delete(real_redis_hash_key)
