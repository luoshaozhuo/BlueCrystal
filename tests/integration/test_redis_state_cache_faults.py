"""Integration tests for live Redis latest-state cache fault handling."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from whale.ingest.adapters.state.redis_source_state_cache import (
    RedisSourceStateCache,
    RedisSourceStateCacheSettings,
)
from whale.ingest.ports.state import SourceStateCacheWriteError
from whale.ingest.usecases.dtos.acquired_node_state import (
    AcquiredNodeStateBatch,
    AcquiredNodeValue,
)


def _batch(value: str) -> AcquiredNodeStateBatch:
    now = datetime.now(tz=UTC)
    return AcquiredNodeStateBatch(
        source_id="LD_FAULT",
        batch_observed_at=now,
        client_received_at=now,
        client_processed_at=now,
        values=[
            AcquiredNodeValue(
                node_key="TotW",
                value=value,
                quality="GOOD",
                server_timestamp=now,
            )
        ],
    )


@pytest.mark.integration
def test_live_redis_oom_is_classified_and_does_not_leave_partial_state(
    real_redis_client: Any,
    real_redis_hash_key: str,
) -> None:
    """Use live Redis maxmemory constraints to verify OOM classification and rollback."""

    cache = RedisSourceStateCache(
        settings=RedisSourceStateCacheSettings(
            host="127.0.0.1",
            port=16379,
            db=15,
            username=None,
            password=None,
            hash_key=real_redis_hash_key,
            station_id="station-fault",
        ),
        client=real_redis_client,
    )

    try:
        current_maxmemory = real_redis_client.config_get("maxmemory").get("maxmemory", "0")
        current_policy = real_redis_client.config_get("maxmemory-policy").get(
            "maxmemory-policy",
            "noeviction",
        )
    except Exception as exc:
        pytest.skip(f"real Redis CONFIG GET is required for OOM integration test: {exc}")

    try:
        used_memory = int(real_redis_client.info("memory")["used_memory"])
        real_redis_client.config_set("maxmemory-policy", "noeviction")
        real_redis_client.config_set("maxmemory", used_memory)
    except Exception as exc:
        pytest.skip(f"real Redis CONFIG SET is required for OOM integration test: {exc}")

    try:
        with pytest.raises(SourceStateCacheWriteError) as exc_info:
            cache.update(ld_name="LD_FAULT", batch=_batch("x" * 200_000))

        assert exc_info.value.error_code == "redis_oom"
        assert real_redis_client.hgetall(real_redis_hash_key) == {}
        assert cache.read_snapshot() == []
    finally:
        real_redis_client.delete(real_redis_hash_key)
        real_redis_client.config_set("maxmemory", current_maxmemory)
        real_redis_client.config_set("maxmemory-policy", current_policy)
