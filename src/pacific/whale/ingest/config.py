"""ingest 配置管理。

从环境变量和配置文件加载 ingest 模块的运行时配置，
包括数据库连接、消息中间件地址、审计策略等。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeAlias

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SQLITE_DB_PATH = PROJECT_ROOT / ".data" / "ingest" / "whale.ingest.db"

DatabaseBackend = Literal["sqlite", "postgresql"]
StateCacheBackend = Literal["redis"]
# `relational_outbox` means published messages are persisted into an outbox
# table inside the ingest relational database, not written to a file.
MessageBackend = Literal["relational_outbox", "redis_streams", "kafka"]
SUPPORTED_DATABASE_BACKENDS = frozenset({"sqlite", "postgresql"})
SUPPORTED_STATE_CACHE_BACKENDS = frozenset({"redis"})
SUPPORTED_MESSAGE_BACKENDS = frozenset({"relational_outbox", "redis_streams", "kafka"})


@dataclass(frozen=True, slots=True)
class SqliteDatabaseConfig:
    """SQLite ingest 数据库后端的配置。"""

    database: str | Path
    backend: Literal["sqlite"] = "sqlite"


@dataclass(frozen=True, slots=True)
class PostgresDatabaseConfig:
    """PostgreSQL ingest 数据库后端的配置。"""

    host: str
    port: int
    database: str | Path
    username: str
    password: str
    database_url: str | None = None
    backend: Literal["postgresql"] = "postgresql"


DatabaseBackendConfig: TypeAlias = SqliteDatabaseConfig | PostgresDatabaseConfig


@dataclass(frozen=True, slots=True)
class DatabaseEngineConfig:
    """ingest 数据库的 SQLAlchemy 引擎和连接池设置。"""

    pool_size: int
    max_overflow: int
    pool_timeout: int
    pool_recycle: int
    pool_pre_ping: bool


@dataclass(frozen=True, slots=True)
class RedisStateCacheConfig:
    """Redis 最新状态缓存后端的配置。"""

    host: str
    port: int
    db: int
    username: str | None
    password: str | None
    hash_key: str
    station_id: str
    decode_responses: bool
    redis_url: str | None = None
    socket_connect_timeout_seconds: float = 2.0
    backend: Literal["redis"] = "redis"

StateCacheConfig: TypeAlias = RedisStateCacheConfig


@dataclass(frozen=True, slots=True)
class RelationalOutboxMessageConfig:
    """关系数据库 outbox 快照发布的配置。"""

    backend: Literal["relational_outbox"] = "relational_outbox"


@dataclass(frozen=True, slots=True)
class RedisStreamsMessageConfig:
    """Redis Streams 快照发布的配置。"""

    redis_url: str
    stream_key: str
    backend: Literal["redis_streams"] = "redis_streams"


@dataclass(frozen=True, slots=True)
class KafkaMessageConfig:
    """Kafka 快照发布的配置。"""

    bootstrap_servers: tuple[str, ...]
    topic: str
    ack_timeout_seconds: float
    acks: str = "all"
    retries: int = 3
    request_timeout_ms: int = 5000
    key_strategy: str = "snapshot_id"
    backend: Literal["kafka"] = "kafka"


MessageConfig: TypeAlias = (
    RelationalOutboxMessageConfig | RedisStreamsMessageConfig | KafkaMessageConfig
)


@dataclass(frozen=True, slots=True)
class EnvironmentConfig:
    """基于环境变量选择构造的 ingest 顶层配置。"""

    database: DatabaseBackendConfig
    database_engine: DatabaseEngineConfig
    state_cache: StateCacheConfig
    message: MessageConfig

    @property
    def state_cache_backend(self) -> StateCacheBackend:
        """返回配置的状态缓存后端。"""
        return self.state_cache.backend


def _resolve_database_backend(value: str | None) -> DatabaseBackend:
    """从 WHALE_INGEST_DATABASE_BACKEND 环境变量解析数据库后端标识符。"""
    backend = (value or "sqlite").strip().lower()
    if backend not in SUPPORTED_DATABASE_BACKENDS:
        raise RuntimeError(
            f"Unsupported WHALE_INGEST_DATABASE_BACKEND value: {value!r}. "
            f"Expected one of {sorted(SUPPORTED_DATABASE_BACKENDS)}."
        )
    return backend  # type: ignore[return-value]  # 运行时校验保证 backend 在枚举范围内，mypy 无法追踪 Literal 收窄


def _resolve_state_cache_backend(value: str | None) -> StateCacheBackend:
    """从 WHALE_INGEST_DATABASE_BACKEND 环境变量解析数据库后端。返回后端标识符字符串。
    Defaults to ``sqlite`` when unset.
    """
    backend = (value or "redis").strip().lower()
    if backend not in SUPPORTED_STATE_CACHE_BACKENDS:
        raise RuntimeError(
            f"Unsupported WHALE_INGEST_STATE_CACHE_BACKEND value: {value!r}. "
            f"Expected one of {sorted(SUPPORTED_STATE_CACHE_BACKENDS)}."
        )
    return backend  # type: ignore[return-value]  # 运行时校验保证 backend 在枚举范围内，mypy 无法追踪 Literal 收窄


def _resolve_message_backend(value: str | None) -> MessageBackend:
    """从 WHALE_INGEST_STATE_CACHE_BACKEND 环境变量解析状态缓存后端。返回后端标识符字符串。
    Defaults to ``redis`` when unset.
    """
    backend = (value or "relational_outbox").strip().lower()
    if backend not in SUPPORTED_MESSAGE_BACKENDS:
        raise RuntimeError(
            f"Unsupported WHALE_INGEST_MESSAGE_BACKEND value: {value!r}. "
            f"Expected one of {sorted(SUPPORTED_MESSAGE_BACKENDS)}."
        )
    return backend  # type: ignore[return-value]


def _require_env_vars(names: tuple[str, ...], *, scope: str) -> None:
    """从 WHALE_INGEST_MESSAGE_BACKEND 环境变量解析消息后端。返回后端标识符字符串。

Defaults to ``relational_outbox`` when unset."""
    missing_names = [name for name in names if os.environ.get(name, "").strip() == ""]
    if missing_names:
        missing_list = ", ".join(missing_names)
        raise RuntimeError(f"Missing required environment variables for {scope}: {missing_list}.")


def _build_config() -> EnvironmentConfig:
    """从环境变量读取后端选择构造 ingest 配置。"""
    database_backend = _resolve_database_backend(os.environ.get("WHALE_INGEST_DATABASE_BACKEND"))
    _resolve_state_cache_backend(os.environ.get("WHALE_INGEST_STATE_CACHE_BACKEND"))
    message_backend = _resolve_message_backend(os.environ.get("WHALE_INGEST_MESSAGE_BACKEND"))
    default_database_path = DEFAULT_SQLITE_DB_PATH
    database_engine = DatabaseEngineConfig(
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=3600,
        pool_pre_ping=True,
    )

    if database_backend == "sqlite":
        database: DatabaseBackendConfig = SqliteDatabaseConfig(
            database=os.environ.get("WHALE_INGEST_DB_PATH", default_database_path),
        )
    else:
        database_url = os.environ.get("WHALE_INGEST_DATABASE_URL", "").strip() or None
        if database_url is not None:
            database = PostgresDatabaseConfig(
                host="",
                port=5432,
                database="",
                username="",
                password="",
                database_url=database_url,
            )
        else:
            _require_env_vars(
                (
                    "WHALE_INGEST_DB_HOST",
                    "WHALE_INGEST_DB_NAME",
                    "WHALE_INGEST_DB_USERNAME",
                    "WHALE_INGEST_DB_PASSWORD",
                ),
                scope="ingest database backend 'postgresql'",
            )
            database_port = os.environ.get("WHALE_INGEST_DB_PORT")
            database = PostgresDatabaseConfig(
                host=os.environ["WHALE_INGEST_DB_HOST"],
                port=int(database_port) if database_port else 5432,
                database=os.environ["WHALE_INGEST_DB_NAME"],
                username=os.environ["WHALE_INGEST_DB_USERNAME"],
                password=os.environ["WHALE_INGEST_DB_PASSWORD"],
                database_url=None,
            )

    redis_url = os.environ.get("WHALE_INGEST_REDIS_URL", "").strip() or None
    if redis_url is None:
        _require_env_vars(
            (
                "WHALE_INGEST_REDIS_HOST",
                "WHALE_INGEST_REDIS_STATE_HASH_KEY",
                "WHALE_INGEST_STATION_ID",
            ),
            scope="ingest state-cache backend 'redis'",
        )
    redis_port = os.environ.get("WHALE_INGEST_REDIS_PORT")
    redis_db = os.environ.get("WHALE_INGEST_REDIS_DB")
    redis_decode_responses = os.environ.get("WHALE_INGEST_REDIS_DECODE_RESPONSES")
    state_cache: StateCacheConfig = RedisStateCacheConfig(
        redis_url=redis_url,
        host=os.environ.get("WHALE_INGEST_REDIS_HOST", "127.0.0.1"),
        port=int(redis_port) if redis_port else 6379,
        db=int(redis_db) if redis_db else 0,
        username=os.environ.get("WHALE_INGEST_REDIS_USERNAME") or None,
        password=os.environ.get("WHALE_INGEST_REDIS_PASSWORD") or None,
        hash_key=os.environ["WHALE_INGEST_REDIS_STATE_HASH_KEY"],
        station_id=os.environ["WHALE_INGEST_STATION_ID"],
        decode_responses=(
            True
            if redis_decode_responses in (None, "")
            else str(redis_decode_responses).lower() != "false"
        ),
        socket_connect_timeout_seconds=float(
            os.environ.get("WHALE_INGEST_REDIS_CONNECT_TIMEOUT_SECONDS", "2.0")
        ),
    )

    if message_backend == "relational_outbox":
        message: MessageConfig = RelationalOutboxMessageConfig()
    elif message_backend == "redis_streams":
        _require_env_vars(
            (
                "WHALE_INGEST_MESSAGE_REDIS_URL",
                "WHALE_INGEST_MESSAGE_REDIS_STREAM_KEY",
            ),
            scope="ingest message backend 'redis_streams'",
        )
        message = RedisStreamsMessageConfig(
            redis_url=os.environ["WHALE_INGEST_MESSAGE_REDIS_URL"],
            stream_key=os.environ["WHALE_INGEST_MESSAGE_REDIS_STREAM_KEY"],
        )
    else:
        _require_env_vars(
            (
                "WHALE_INGEST_KAFKA_BOOTSTRAP_SERVERS",
                "WHALE_INGEST_KAFKA_TOPIC",
            ),
            scope="ingest message backend 'kafka'",
        )
        message = KafkaMessageConfig(
            bootstrap_servers=tuple(
                item.strip()
                for item in os.environ["WHALE_INGEST_KAFKA_BOOTSTRAP_SERVERS"].split(",")
                if item.strip()
            ),
            topic=os.environ["WHALE_INGEST_KAFKA_TOPIC"],
            ack_timeout_seconds=float(
                os.environ.get("WHALE_INGEST_KAFKA_ACK_TIMEOUT_SECONDS", "5.0")
            ),
            acks=os.environ.get("WHALE_INGEST_KAFKA_ACKS", "all"),
            retries=int(os.environ.get("WHALE_INGEST_KAFKA_RETRIES", "3")),
            request_timeout_ms=int(
                os.environ.get("WHALE_INGEST_KAFKA_REQUEST_TIMEOUT_MS", "5000")
            ),
            key_strategy=os.environ.get(
                "WHALE_INGEST_KAFKA_KEY_STRATEGY",
                "snapshot_id",
            ),
        )

    return EnvironmentConfig(
        database=database,
        database_engine=database_engine,
        state_cache=state_cache,
        message=message,
    )


CONFIG = _build_config()
