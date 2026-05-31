"""Production-like Redis cache integration tests.

Requires real Redis reachable via WHALE_INGEST_REDIS_HOST / port.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest

from whale.ingest.adapters.state.redis_source_state_cache import (
    RedisSourceStateCache,
    RedisSourceStateCacheSettings,
)
from whale.ingest.usecases.dtos.acquired_node_state import AcquiredNodeStateBatch, AcquiredNodeValue

REDIS_HOST = os.environ.get("WHALE_INGEST_REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.environ.get("WHALE_INGEST_REDIS_PORT", "16379"))


@pytest.fixture
def redis_settings():
    return RedisSourceStateCacheSettings(
        redis_url=None,
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=1,
        username=None,
        password=None,
        hash_key="test:prodlike:state",
        station_id="test-prod",
        socket_connect_timeout_seconds=1.0,
    )


@pytest.fixture
def cache(redis_settings):
    return RedisSourceStateCache(settings=redis_settings)


@pytest.fixture
def raw_client(redis_settings):
    from redis import Redis

    client = Redis(
        host=redis_settings.host,
        port=redis_settings.port,
        db=redis_settings.db,
        decode_responses=True,
    )
    yield client
    client.delete(redis_settings.hash_key)
    client.close()


def _skip_no_redis(redis_settings):
    """Skip test when Redis is unreachable."""
    try:
        from redis import Redis

        r = Redis(
            host=redis_settings.host,
            port=redis_settings.port,
            db=redis_settings.db,
            socket_connect_timeout=1,
        )
        r.ping()
        r.close()
    except Exception:
        pytest.skip(f"Redis not reachable at {redis_settings.host}:{redis_settings.port}")


# ── Writes to real Redis ───────────────────────────────────────────────


def test_source_state_cache_writes_to_real_redis(redis_settings, cache):
    """Verify update() persists data in real Redis."""
    _skip_no_redis(redis_settings)

    now = datetime.now(tz=UTC)
    batch = AcquiredNodeStateBatch(
        source_id="test-source",
        batch_observed_at=now,
        client_received_at=now,
        client_processed_at=now,
        values=[
            AcquiredNodeValue(
                node_key="point1",
                value="42.0",
                quality="GOOD",
                source_timestamp=now,
                server_timestamp=now,
            ),
        ],
    )
    updated = cache.update(ld_name="test-ld", batch=batch)
    assert updated == 1

    # Verify via raw Redis
    from redis import Redis

    client = Redis(
        host=redis_settings.host,
        port=redis_settings.port,
        db=redis_settings.db,
        decode_responses=True,
    )
    meta = client.hget(redis_settings.hash_key, "test-prod:ld:test-ld:meta")
    client.close()
    assert meta is not None
    assert "test-source" in meta


# ── Reads snapshot from real Redis ─────────────────────────────────────


def test_source_state_cache_reads_snapshot_from_real_redis(redis_settings, cache):
    """Verify read_snapshot() returns data written to real Redis."""
    _skip_no_redis(redis_settings)

    now = datetime.now(tz=UTC)
    batch = AcquiredNodeStateBatch(
        source_id="test-source-2",
        batch_observed_at=now,
        client_received_at=now,
        client_processed_at=now,
        values=[
            AcquiredNodeValue(
                node_key="point-a",
                value="100",
                quality="GOOD",
                source_timestamp=now,
                server_timestamp=now,
            ),
        ],
    )
    cache.update(ld_name="test-ld-2", batch=batch)

    snapshots = cache.read_snapshot()
    matching = [s for s in snapshots if s.source_id == "test-source-2"]
    assert len(matching) == 1
    assert matching[0].values[0].value == "100"


# ── Error when Redis unavailable ───────────────────────────────────────


def test_source_state_cache_error_when_redis_unavailable():
    """Verify unavailable Redis raises a cache write error."""
    bad_settings = RedisSourceStateCacheSettings(
        redis_url=None,
        host="127.0.0.1",
        port=1,  # unlikely to be open
        db=0,
        username=None,
        password=None,
        hash_key="test:unreachable",
        station_id="test",
        socket_connect_timeout_seconds=0.2,
    )
    bad_cache = RedisSourceStateCache(settings=bad_settings)

    now = datetime.now(tz=UTC)
    batch = AcquiredNodeStateBatch(
        source_id="test",
        batch_observed_at=now,
        client_received_at=now,
        client_processed_at=now,
        values=[
            AcquiredNodeValue(
                node_key="p1",
                value="1",
                quality="GOOD",
                source_timestamp=now,
                server_timestamp=now,
            ),
        ],
    )
    from whale.ingest.ports.state.source_state_cache_port import SourceStateCacheWriteError

    with pytest.raises(SourceStateCacheWriteError):
        bad_cache.update(ld_name="test-ld", batch=batch)
