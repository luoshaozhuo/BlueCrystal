"""Unit tests for the Redis latest-state cache adapter."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import pytest

from whale.ingest.adapters.state.redis_source_state_cache import (
    RedisHashClient,
    RedisPipeline,
    RedisSourceStateCache,
    RedisSourceStateCacheSettings,
)
from whale.ingest.ports.state import SourceStateCacheWriteError
from whale.ingest.usecases.dtos.acquired_node_state import (
    AcquiredNodeStateBatch,
    AcquiredNodeValue,
)


@dataclass
class FakePipeline(RedisPipeline):
    """Collect transaction pipeline writes and commit them atomically."""

    store: dict[str, str]
    execute_error: Exception | None = None
    staged: list[tuple[str, str, str]] = field(default_factory=list)

    def hset(self, name: str, key: str, value: str) -> object:
        self.staged.append((name, key, value))
        return 1

    def execute(self) -> object:
        if self.execute_error is not None:
            raise self.execute_error

        for _, key, value in self.staged:
            self.store[key] = value
        self.staged.clear()
        return None


@dataclass
class FakeRedisClient(RedisHashClient):
    """Minimal Redis hash client fake with bytes and failure modes."""

    store: dict[str, str] = field(default_factory=dict)
    return_bytes: bool = False
    hset_error: Exception | None = None
    hget_error: Exception | None = None
    hgetall_error: Exception | None = None
    pipeline_error: Exception | None = None

    def hset(self, name: str, key: str, value: str) -> int:
        del name
        if self.hset_error is not None:
            raise self.hset_error
        self.store[key] = value
        return 1

    def hget(self, name: str, key: str) -> str | bytes | None:
        del name
        if self.hget_error is not None:
            raise self.hget_error
        value = self.store.get(key)
        if value is None:
            return None
        return value.encode("utf-8") if self.return_bytes else value

    def hgetall(self, name: str) -> dict[str, str] | dict[bytes, bytes]:
        del name
        if self.hgetall_error is not None:
            raise self.hgetall_error
        if not self.return_bytes:
            return dict(self.store)
        return {
            key.encode("utf-8"): value.encode("utf-8")
            for key, value in self.store.items()
        }

    def pipeline(self, transaction: bool = True) -> RedisPipeline:
        assert transaction is True
        return FakePipeline(
            self.store,
            execute_error=self.pipeline_error,
        )


def _settings(*, decode_responses: bool = True) -> RedisSourceStateCacheSettings:
    return RedisSourceStateCacheSettings(
        redis_url=None,
        host="127.0.0.1",
        port=6379,
        db=0,
        username=None,
        password=None,
        hash_key="whale:test",
        station_id="station-a",
        socket_connect_timeout_seconds=1.0,
        decode_responses=decode_responses,
    )


def _batch(
    *,
    value: str,
    quality: str = "GOOD",
    server_timestamp: datetime | None = None,
    client_sequence: int | None = None,
    observed_at: datetime | None = None,
) -> AcquiredNodeStateBatch:
    now = observed_at or datetime.now(tz=UTC)
    return AcquiredNodeStateBatch(
        source_id="LD_01",
        batch_observed_at=now,
        client_received_at=now,
        client_processed_at=now,
        availability_status="VALID",
        values=[
            AcquiredNodeValue(
                node_key="TotW",
                value=value,
                quality=quality,
                server_timestamp=server_timestamp,
                client_sequence=client_sequence,
                attributes={"unit": "MW"},
            )
        ],
        attributes={"acquisition_kind": "read"},
    )


def test_update_writes_ld_meta_and_variable_state() -> None:
    client = FakeRedisClient()
    cache = RedisSourceStateCache(settings=_settings(), client=client)

    updated = cache.update(ld_name="LD_01", batch=_batch(value="1"))
    snapshot = cache.read_snapshot()

    assert updated == 1
    assert len(snapshot) == 1
    assert snapshot[0].ld_name == "LD_01"
    assert snapshot[0].availability_status == "VALID"
    assert snapshot[0].values[0].node_key == "TotW"
    assert snapshot[0].values[0].value == "1"


def test_mark_unavailable_keeps_last_valid_value() -> None:
    client = FakeRedisClient()
    cache = RedisSourceStateCache(settings=_settings(), client=client)
    batch = _batch(value="2")
    cache.update(ld_name="LD_01", batch=batch)

    cache.mark_unavailable(
        ld_name="LD_01",
        status="ERROR",
        observed_at=batch.client_processed_at + timedelta(seconds=1),
        reason="runner_not_available",
    )
    snapshot = cache.read_snapshot()[0]

    assert snapshot.availability_status == "ERROR"
    assert snapshot.unavailable_reason == "runner_not_available"
    assert snapshot.values[0].value == "2"


def test_older_server_timestamp_does_not_override_newer_value() -> None:
    client = FakeRedisClient()
    cache = RedisSourceStateCache(settings=_settings(), client=client)
    newer_ts = datetime(2026, 5, 22, 9, 0, tzinfo=UTC)
    older_ts = newer_ts - timedelta(seconds=1)

    cache.update(ld_name="LD_01", batch=_batch(value="new", server_timestamp=newer_ts))
    cache.update(ld_name="LD_01", batch=_batch(value="old", server_timestamp=older_ts))
    snapshot = cache.read_snapshot()[0]

    assert snapshot.values[0].value == "new"
    assert snapshot.values[0].server_timestamp == newer_ts


def test_client_sequence_protects_against_out_of_order_updates() -> None:
    client = FakeRedisClient()
    cache = RedisSourceStateCache(settings=_settings(), client=client)

    cache.update(ld_name="LD_01", batch=_batch(value="seq-2", client_sequence=2))
    cache.update(ld_name="LD_01", batch=_batch(value="seq-1", client_sequence=1))
    snapshot = cache.read_snapshot()[0]

    assert snapshot.values[0].value == "seq-2"
    assert snapshot.values[0].client_sequence == 2


def test_stale_update_does_not_restore_valid_after_error() -> None:
    client = FakeRedisClient()
    cache = RedisSourceStateCache(settings=_settings(), client=client)
    newer_ts = datetime(2026, 5, 22, 9, 0, tzinfo=UTC)
    older_ts = newer_ts - timedelta(seconds=1)

    cache.update(ld_name="LD_01", batch=_batch(value="new", server_timestamp=newer_ts))
    cache.mark_unavailable(
        ld_name="LD_01",
        status="ERROR",
        observed_at=newer_ts + timedelta(seconds=1),
        reason="runner_not_available",
    )

    stale_updated = cache.update(ld_name="LD_01", batch=_batch(value="stale", server_timestamp=older_ts))
    stale_snapshot = cache.read_snapshot()[0]

    assert stale_updated == 0
    assert stale_snapshot.availability_status == "ERROR"
    assert stale_snapshot.unavailable_reason == "runner_not_available"
    assert stale_snapshot.values[0].value == "new"


def test_fresh_update_restores_valid_and_clears_reason() -> None:
    client = FakeRedisClient()
    cache = RedisSourceStateCache(settings=_settings(), client=client)
    now = datetime(2026, 5, 22, 9, 0, tzinfo=UTC)

    cache.update(ld_name="LD_01", batch=_batch(value="old", server_timestamp=now))
    cache.mark_unavailable(
        ld_name="LD_01",
        status="ERROR",
        observed_at=now + timedelta(seconds=1),
        reason="runner_not_available",
    )
    cache.update(
        ld_name="LD_01",
        batch=_batch(value="fresh", server_timestamp=now + timedelta(seconds=2)),
    )
    snapshot = cache.read_snapshot()[0]

    assert snapshot.availability_status == "VALID"
    assert snapshot.unavailable_reason is None
    assert snapshot.values[0].value == "fresh"


def test_mark_alive_does_not_promote_error_without_new_update() -> None:
    client = FakeRedisClient()
    cache = RedisSourceStateCache(settings=_settings(), client=client)
    batch = _batch(value="4")
    cache.update(ld_name="LD_01", batch=batch)
    cache.mark_unavailable(
        ld_name="LD_01",
        status="ERROR",
        observed_at=batch.client_processed_at + timedelta(seconds=1),
        reason="runner_not_available",
    )

    cache.mark_alive(
        ld_name="LD_01",
        observed_at=batch.client_processed_at + timedelta(seconds=2),
    )
    snapshot = cache.read_snapshot()[0]

    assert snapshot.availability_status == "ERROR"
    assert snapshot.values[0].value == "4"


def test_read_snapshot_returns_ld_level_state_with_utc_datetimes() -> None:
    observed_at = datetime(2026, 5, 22, 10, 0, tzinfo=UTC)
    client = FakeRedisClient()
    cache = RedisSourceStateCache(settings=_settings(), client=client)
    cache.update(ld_name="LD_01", batch=_batch(value="5", observed_at=observed_at))
    cache.mark_alive(ld_name="LD_01", observed_at=observed_at + timedelta(seconds=1))

    snapshot = cache.read_snapshot()[0]

    assert snapshot.ld_name == "LD_01"
    assert snapshot.source_id == "LD_01"
    assert snapshot.last_alive_at is not None and snapshot.last_alive_at.tzinfo is UTC
    assert snapshot.last_value_updated_at is not None and snapshot.last_value_updated_at.tzinfo is UTC
    assert snapshot.batch_observed_at is not None and snapshot.batch_observed_at.tzinfo is UTC
    assert snapshot.values[0].updated_at is not None and snapshot.values[0].updated_at.tzinfo is UTC


def test_read_snapshot_supports_bytes_backed_redis_payloads() -> None:
    client = FakeRedisClient(return_bytes=True)
    cache = RedisSourceStateCache(settings=_settings(decode_responses=False), client=client)
    cache.update(ld_name="LD_01", batch=_batch(value="6"))

    snapshot = cache.read_snapshot()[0]

    assert snapshot.values[0].value == "6"
    assert snapshot.values[0].quality == "GOOD"


def test_pipeline_execute_failure_raises_classified_write_error_and_preserves_meta_state() -> None:
    client = FakeRedisClient()
    cache = RedisSourceStateCache(settings=_settings(), client=client)
    cache.update(ld_name="LD_01", batch=_batch(value="seed"))
    cache.mark_unavailable(
        ld_name="LD_01",
        status="ERROR",
        observed_at=datetime.now(tz=UTC),
        reason="runner_not_available",
    )
    client.pipeline_error = RuntimeError("OOM command not allowed when used memory > 'maxmemory'")

    with pytest.raises(SourceStateCacheWriteError) as exc_info:
        cache.update(ld_name="LD_01", batch=_batch(value="newer"))

    snapshot = cache.read_snapshot()[0]

    assert exc_info.value.error_code == "redis_oom"
    assert snapshot.availability_status == "ERROR"
    assert snapshot.values[0].value == "seed"


def test_transaction_pipeline_failure_does_not_leave_partial_writes() -> None:
    client = FakeRedisClient()
    cache = RedisSourceStateCache(settings=_settings(), client=client)
    cache.update(ld_name="LD_01", batch=_batch(value="seed"))

    client.pipeline_error = RuntimeError("READONLY replica")

    with pytest.raises(SourceStateCacheWriteError):
        cache.update(ld_name="LD_01", batch=_batch(value="next"))

    snapshot = cache.read_snapshot()[0]

    assert snapshot.availability_status == "VALID"
    assert snapshot.values[0].value == "seed"


def test_mark_unavailable_uses_transaction_pipeline_without_partial_downgrade() -> None:
    client = FakeRedisClient()
    cache = RedisSourceStateCache(settings=_settings(), client=client)
    cache.update(ld_name="LD_01", batch=_batch(value="seed"))

    client.pipeline_error = RuntimeError("BUSY Redis is busy running a script")

    with pytest.raises(SourceStateCacheWriteError) as exc_info:
        cache.mark_unavailable(
            ld_name="LD_01",
            status="ERROR",
            observed_at=datetime.now(tz=UTC),
            reason="runner_not_available",
        )

    snapshot = cache.read_snapshot()[0]

    assert exc_info.value.error_code == "redis_busy"
    assert snapshot.availability_status == "VALID"
    assert snapshot.values[0].value == "seed"


@pytest.mark.parametrize(
    ("error", "expected_code"),
    [
        (RuntimeError("OOM command not allowed when used memory > 'maxmemory'"), "redis_oom"),
        (RuntimeError("MISCONF Redis is configured to save RDB snapshots"), "redis_misconf"),
        (RuntimeError("READONLY You can't write against a read only replica."), "redis_readonly"),
        (RuntimeError("LOADING Redis is loading the dataset in memory"), "redis_loading"),
        (RuntimeError("BUSY Redis is busy running a script"), "redis_busy"),
        (TimeoutError("timed out"), "redis_timeout"),
        (ConnectionError("connection reset by peer"), "redis_connection_error"),
    ],
)
def test_redis_failures_are_classified_to_stable_error_codes(
    error: Exception,
    expected_code: str,
) -> None:
    client = FakeRedisClient(pipeline_error=error)
    cache = RedisSourceStateCache(settings=_settings(), client=client)

    with pytest.raises(SourceStateCacheWriteError) as exc_info:
        cache.update(ld_name="LD_01", batch=_batch(value="7"))

    assert exc_info.value.error_code == expected_code
    assert exc_info.value.retryable is True


def test_transaction_failure_is_classified_for_mark_alive() -> None:
    client = FakeRedisClient(pipeline_error=RuntimeError("READONLY replica"))
    cache = RedisSourceStateCache(settings=_settings(), client=client)

    with pytest.raises(SourceStateCacheWriteError) as exc_info:
        cache.mark_alive(ld_name="LD_01", observed_at=datetime.now(tz=UTC))

    assert exc_info.value.error_code == "redis_readonly"
