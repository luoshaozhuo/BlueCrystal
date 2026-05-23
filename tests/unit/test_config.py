"""Unit tests for ingest configuration resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from whale.ingest.config import (
    CONFIG,
    DEFAULT_SQLITE_DB_PATH,
    EnvironmentConfig,
    KafkaMessageConfig,
    PostgresDatabaseConfig,
    RedisStateCacheConfig,
    RelationalOutboxMessageConfig,
    SqliteDatabaseConfig,
    _build_config,
    _resolve_database_backend,
    _resolve_message_backend,
    _resolve_state_cache_backend,
)


def test_resolve_database_backend_defaults_to_sqlite() -> None:
    """Default the database backend to sqlite when unset."""

    assert _resolve_database_backend(None) == "sqlite"
    assert _resolve_database_backend("") == "sqlite"


def test_resolve_state_cache_backend_defaults_to_redis() -> None:
    """Default the state-cache backend to redis when unset."""

    assert _resolve_state_cache_backend(None) == "redis"
    assert _resolve_state_cache_backend("") == "redis"


def test_resolve_message_backend_defaults_to_relational_outbox() -> None:
    """Default the message backend to relational_outbox when unset."""

    assert _resolve_message_backend(None) == "relational_outbox"
    assert _resolve_message_backend("") == "relational_outbox"


@pytest.mark.parametrize("value", ["sqlite", "postgresql"])
def test_resolve_database_backend_accepts_supported_values(value: str) -> None:
    """Accept all supported database backend values."""

    assert _resolve_database_backend(value) == value


def test_resolve_state_cache_backend_accepts_only_redis() -> None:
    """Accept the Redis-only production state-cache backend."""

    assert _resolve_state_cache_backend("redis") == "redis"


@pytest.mark.parametrize("value", ["relational_outbox", "redis_streams", "kafka"])
def test_resolve_message_backend_accepts_supported_values(value: str) -> None:
    """Accept all supported message backend values."""

    assert _resolve_message_backend(value) == value


def test_resolve_database_backend_rejects_unknown_value() -> None:
    """Reject unsupported database backend values."""

    with pytest.raises(RuntimeError, match="Unsupported WHALE_INGEST_DATABASE_BACKEND"):
        _resolve_database_backend("mysql")


@pytest.mark.parametrize("value", ["memory", "relational"])
def test_resolve_state_cache_backend_rejects_non_redis_values(value: str) -> None:
    """Reject legacy or unsupported state-cache backend values."""

    with pytest.raises(RuntimeError, match="Unsupported WHALE_INGEST_STATE_CACHE_BACKEND"):
        _resolve_state_cache_backend(value)


def test_resolve_message_backend_rejects_unknown_value() -> None:
    """Reject unsupported message backend values."""

    with pytest.raises(RuntimeError, match="Unsupported WHALE_INGEST_MESSAGE_BACKEND"):
        _resolve_message_backend("rabbitmq")


def test_build_config_defaults_to_sqlite_and_redis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Build a local config with sqlite database and redis latest-state cache."""

    monkeypatch.delenv("WHALE_INGEST_DATABASE_BACKEND", raising=False)
    monkeypatch.delenv("WHALE_INGEST_STATE_CACHE_BACKEND", raising=False)
    monkeypatch.delenv("WHALE_INGEST_MESSAGE_BACKEND", raising=False)
    monkeypatch.setenv("WHALE_INGEST_REDIS_HOST", "127.0.0.1")
    monkeypatch.setenv("WHALE_INGEST_REDIS_STATE_HASH_KEY", "whale:test:state")
    monkeypatch.setenv("WHALE_INGEST_STATION_ID", "station-default")

    config = _build_config()

    assert isinstance(config, EnvironmentConfig)
    assert isinstance(config.database, SqliteDatabaseConfig)
    assert Path(str(config.database.database)) == DEFAULT_SQLITE_DB_PATH
    assert isinstance(config.state_cache, RedisStateCacheConfig)
    assert isinstance(config.message, RelationalOutboxMessageConfig)


def test_build_config_reports_missing_postgres_env_vars(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """List missing PostgreSQL variables clearly when building with postgresql backend."""

    monkeypatch.setenv("WHALE_INGEST_DATABASE_BACKEND", "postgresql")
    monkeypatch.setenv("WHALE_INGEST_STATE_CACHE_BACKEND", "redis")
    monkeypatch.setenv("WHALE_INGEST_REDIS_HOST", "127.0.0.1")
    monkeypatch.setenv("WHALE_INGEST_REDIS_STATE_HASH_KEY", "whale:test:state")
    monkeypatch.setenv("WHALE_INGEST_STATION_ID", "station-postgres")
    for name in (
        "WHALE_INGEST_DB_HOST",
        "WHALE_INGEST_DB_NAME",
        "WHALE_INGEST_DB_USERNAME",
        "WHALE_INGEST_DB_PASSWORD",
    ):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(RuntimeError, match="WHALE_INGEST_DB_HOST, WHALE_INGEST_DB_NAME"):
        _build_config()


def test_build_config_requires_redis_env_vars(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fail fast when Redis latest-state configuration is incomplete."""

    monkeypatch.setenv("WHALE_INGEST_DATABASE_BACKEND", "sqlite")
    monkeypatch.delenv("WHALE_INGEST_REDIS_HOST", raising=False)
    monkeypatch.delenv("WHALE_INGEST_REDIS_STATE_HASH_KEY", raising=False)
    monkeypatch.delenv("WHALE_INGEST_STATION_ID", raising=False)

    with pytest.raises(RuntimeError, match="WHALE_INGEST_REDIS_HOST"):
        _build_config()


def test_build_config_assembles_redis_and_kafka_backends(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Build a config with postgresql + redis + kafka when env vars are set."""

    monkeypatch.setenv("WHALE_INGEST_DATABASE_BACKEND", "postgresql")
    monkeypatch.setenv("WHALE_INGEST_STATE_CACHE_BACKEND", "redis")
    monkeypatch.setenv("WHALE_INGEST_MESSAGE_BACKEND", "kafka")
    monkeypatch.setenv("WHALE_INGEST_DB_HOST", "localhost")
    monkeypatch.setenv("WHALE_INGEST_DB_NAME", "whale_ingest")
    monkeypatch.setenv("WHALE_INGEST_DB_USERNAME", "whale")
    monkeypatch.setenv("WHALE_INGEST_DB_PASSWORD", "whale")
    monkeypatch.setenv("WHALE_INGEST_REDIS_HOST", "localhost")
    monkeypatch.setenv("WHALE_INGEST_REDIS_STATE_HASH_KEY", "whale:ingest:state")
    monkeypatch.setenv("WHALE_INGEST_STATION_ID", "station-test-001")
    monkeypatch.setenv("WHALE_INGEST_KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    monkeypatch.setenv("WHALE_INGEST_KAFKA_TOPIC", "whale.ingest.state_snapshot.v1")

    config = _build_config()

    assert isinstance(config.database, PostgresDatabaseConfig)
    assert isinstance(config.state_cache, RedisStateCacheConfig)
    assert isinstance(config.message, KafkaMessageConfig)


def test_config_module_level_object_is_valid() -> None:
    """Expose a valid top-level CONFIG object at import time."""

    assert isinstance(CONFIG, EnvironmentConfig)
    assert CONFIG.database_engine.pool_size == 10
    assert CONFIG.database_engine.pool_pre_ping is True
    assert CONFIG.state_cache_backend == CONFIG.state_cache.backend
