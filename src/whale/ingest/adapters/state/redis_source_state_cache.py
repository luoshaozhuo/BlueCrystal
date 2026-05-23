"""Redis-backed latest-state cache for ingest.

本模块提供 Redis 版本的 latest-state cache。

设计约定：
- Redis 使用一个 hash 保存全部 LD/source 状态；
- 每个 LD/source 有一个 meta 字段，保存可用性、统一状态时间和链路活性；
- 每个点位一个 var 字段，保存最新值和点级版本信息；
- cache 对外以 LD/source 为状态视图单位；
- batch_observed_at 是 LD 统一状态时间；
- source_timestamp / server_timestamp / client_sequence 只用于乱序保护和诊断；
- mark_alive() 只刷新链路活性，不改变点位值；
- mark_unavailable() 只降级 LD 状态，不删除最后有效值；
- read_snapshot() 返回 LD 级快照，不兼容旧的单点快照结构。
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol, cast

from whale.ingest.config import CONFIG, RedisStateCacheConfig
from whale.ingest.ports.state.source_state_cache_port import (
    SourceStateCachePort,
    SourceStateCacheWriteError,
)
from whale.ingest.ports.state.source_state_snapshot_reader_port import (
    CachedNodeValue,
    CachedSourceState,
    SourceStateSnapshotReaderPort,
)
from whale.ingest.usecases.dtos.acquired_node_state import (
    AcquiredNodeStateBatch,
    AcquiredNodeValue,
)
from whale.shared.crosscutting.resilience.error_classifier import ClassifiedError
from whale.shared.utils.time import ensure_utc, max_datetime


class RedisPipeline(Protocol):
    """Minimal Redis pipeline contract used by the Redis state cache."""

    def hset(self, name: str, key: str, value: str) -> object:
        """Set one hash field in pipeline."""

    def execute(self) -> object:
        """Execute queued Redis commands."""


class RedisHashClient(Protocol):
    """Minimal Redis hash client contract used by the Redis state cache."""

    def hset(self, name: str, key: str, value: str) -> int:
        """Set one hash field."""

    def hget(self, name: str, key: str) -> str | bytes | None:
        """Get one hash field."""

    def hgetall(self, name: str) -> Mapping[str, str] | Mapping[bytes, bytes]:
        """Return all hash fields and values."""

    def pipeline(self, transaction: bool = True) -> RedisPipeline:
        """Return a Redis pipeline for batch operations."""


@dataclass(frozen=True, slots=True)
class RedisSourceStateCacheSettings:
    """Connection and key settings for the Redis latest-state cache."""

    host: str
    port: int
    db: int
    username: str | None
    password: str | None
    hash_key: str
    station_id: str
    decode_responses: bool = True

    @classmethod
    def from_config(
        cls,
        config: RedisStateCacheConfig,
    ) -> RedisSourceStateCacheSettings:
        """Build adapter settings from the ingest module config."""

        missing_names = [
            name
            for name, value in (
                ("WHALE_INGEST_REDIS_HOST", config.host),
                ("WHALE_INGEST_REDIS_PORT", config.port),
                ("WHALE_INGEST_REDIS_DB", config.db),
                ("WHALE_INGEST_REDIS_STATE_HASH_KEY", config.hash_key),
                ("WHALE_INGEST_STATION_ID", config.station_id),
                ("WHALE_INGEST_REDIS_DECODE_RESPONSES", config.decode_responses),
            )
            if value is None
        ]
        if missing_names:
            raise RuntimeError(
                "Missing required Redis state cache environment variables: "
                + ", ".join(missing_names)
            )

        return cls(
            host=config.host,
            port=config.port,
            db=config.db,
            username=config.username,
            password=config.password,
            hash_key=config.hash_key,
            station_id=config.station_id,
            decode_responses=config.decode_responses,
        )


class RedisSourceStateCache(SourceStateCachePort, SourceStateSnapshotReaderPort):
    """Use one Redis hash as the production latest-state cache."""

    def __init__(
        self,
        settings: RedisSourceStateCacheSettings | None = None,
        client: RedisHashClient | None = None,
    ) -> None:
        """Create the Redis-backed state cache."""

        if settings is None:
            if not isinstance(CONFIG.state_cache, RedisStateCacheConfig):
                raise RuntimeError(
                    "RedisSourceStateCache requires the redis state-cache backend "
                    "to be configured."
                )
            settings = RedisSourceStateCacheSettings.from_config(CONFIG.state_cache)

        self._settings = settings
        self._client = client or self._build_client(self._settings)

    def update(
        self,
        *,
        ld_name: str,
        batch: AcquiredNodeStateBatch,
    ) -> int:
        """按 batch 刷新一个 LD/source 的 latest-state。"""

        if batch.is_empty():
            return 0

        now = datetime.now(tz=UTC)
        try:
            meta_field = self._build_ld_meta_field(ld_name=ld_name)
            current_meta = self._load_payload(meta_field)
            updated_count = 0
            value_payloads: list[tuple[str, dict[str, Any]]] = []

            for value in batch.values:
                value_field = self._build_variable_field(
                    ld_name=ld_name,
                    node_key=value.node_key,
                )
                current_value_payload = self._load_payload(value_field)

                if current_value_payload is not None and not _should_update_value(
                    incoming=value,
                    current_payload=current_value_payload,
                ):
                    continue

                value_payloads.append(
                    (
                        value_field,
                        self._build_value_payload(
                            ld_name=ld_name,
                            batch=batch,
                            value=value,
                            now=now,
                        ),
                    )
                )
                updated_count += 1

            next_meta = self._build_next_meta_payload(
                ld_name=ld_name,
                batch=batch,
                current_meta=current_meta,
                now=now,
                values_updated=updated_count > 0,
            )

            pipe = self._client.pipeline(transaction=True)
            for value_field, next_value_payload in value_payloads:
                pipe.hset(
                    self._settings.hash_key,
                    value_field,
                    self._dump_payload(next_value_payload),
                )
            pipe.hset(
                self._settings.hash_key,
                meta_field,
                self._dump_payload(next_meta),
            )
            self._execute_pipeline(pipe, operation="update", ld_name=ld_name)
            return updated_count
        except SourceStateCacheWriteError:
            raise
        except Exception as exc:
            raise self._build_write_error(
                operation="update",
                ld_name=ld_name,
                exc=exc,
            ) from exc

    def mark_alive(
        self,
        *,
        ld_name: str,
        observed_at: datetime,
    ) -> None:
        """标记一个 LD/source 的采集链路仍然存活。"""

        try:
            now = datetime.now(tz=UTC)
            observed_at = ensure_utc(observed_at)
            meta_field = self._build_ld_meta_field(ld_name=ld_name)
            current_meta = self._load_payload(meta_field) or {}

            current_status = str(current_meta.get("availability_status") or "UNKNOWN")
            next_status = (
                "VALID"
                if current_status in {"UNKNOWN", "STALE", "OFFLINE"}
                else current_status
            )

            next_meta = {
                **current_meta,
                "station_id": self._settings.station_id,
                "ld_name": ld_name,
                "source_id": str(current_meta.get("source_id") or ld_name),
                "availability_status": next_status,
                "unavailable_reason": None
                if next_status == "VALID"
                else current_meta.get("unavailable_reason"),
                "last_alive_at": _datetime_to_iso(
                    max_datetime(
                        _parse_datetime(current_meta.get("last_alive_at")),
                        observed_at,
                    )
                ),
                "state_updated_at": now.isoformat(),
            }

            pipe = self._client.pipeline(transaction=True)
            pipe.hset(
                self._settings.hash_key,
                meta_field,
                self._dump_payload(next_meta),
            )
            self._execute_pipeline(pipe, operation="mark_alive", ld_name=ld_name)
        except SourceStateCacheWriteError:
            raise
        except Exception as exc:
            raise self._build_write_error(
                operation="mark_alive",
                ld_name=ld_name,
                exc=exc,
            ) from exc

    def mark_unavailable(
        self,
        *,
        ld_name: str,
        status: str,
        observed_at: datetime,
        reason: str | None = None,
    ) -> None:
        """将一个 LD/source 标记为不可用或降级状态。"""

        try:
            now = datetime.now(tz=UTC)
            observed_at = ensure_utc(observed_at)
            meta_field = self._build_ld_meta_field(ld_name=ld_name)
            current_meta = self._load_payload(meta_field) or {}

            next_meta = {
                **current_meta,
                "station_id": self._settings.station_id,
                "ld_name": ld_name,
                "source_id": str(current_meta.get("source_id") or ld_name),
                "availability_status": status,
                "unavailable_reason": reason,
                "state_updated_at": _datetime_to_iso(
                    max_datetime(
                        _parse_datetime(current_meta.get("state_updated_at")),
                        observed_at,
                    )
                ),
            }

            pipe = self._client.pipeline(transaction=True)
            raw_rows = self._client.hgetall(self._settings.hash_key)
            prefix = self._build_variable_prefix(ld_name=ld_name)

            for raw_field, raw_payload in raw_rows.items():
                field = self._decode_value(raw_field)
                if not field.startswith(prefix):
                    continue

                payload = json.loads(self._decode_value(raw_payload))
                payload["availability_status"] = status
                payload["updated_at"] = now.isoformat()
                pipe.hset(
                    self._settings.hash_key,
                    field,
                    self._dump_payload(payload),
                )

            pipe.hset(
                self._settings.hash_key,
                meta_field,
                self._dump_payload(next_meta),
            )
            self._execute_pipeline(pipe, operation="mark_unavailable", ld_name=ld_name)
        except SourceStateCacheWriteError:
            raise
        except Exception as exc:
            raise self._build_write_error(
                operation="mark_unavailable",
                ld_name=ld_name,
                exc=exc,
            ) from exc

    def read_snapshot(self) -> list[CachedSourceState]:
        """读取全部 LD/source 的 latest-state 快照。"""

        raw_rows = self._client.hgetall(self._settings.hash_key)

        meta_payloads: dict[str, dict[str, Any]] = {}
        values_by_ld: dict[str, list[CachedNodeValue]] = {}

        for raw_field, raw_payload in raw_rows.items():
            field = self._decode_value(raw_field)
            payload = json.loads(self._decode_value(raw_payload))

            if self._is_ld_meta_field(field):
                ld_name = str(payload["ld_name"])
                meta_payloads[ld_name] = payload
                values_by_ld.setdefault(ld_name, [])
                continue

            if self._is_variable_field(field):
                ld_name = str(payload["ld_name"])
                values_by_ld.setdefault(ld_name, []).append(
                    CachedNodeValue(
                        node_key=str(payload["node_key"]),
                        value=str(payload["value"]),
                        quality=self._optional_str(payload.get("quality")),
                        source_timestamp=_parse_datetime(payload.get("source_timestamp")),
                        server_timestamp=_parse_datetime(payload.get("server_timestamp")),
                        client_sequence=_optional_int(payload.get("client_sequence")),
                        updated_at=_parse_datetime(payload.get("updated_at")),
                        attributes=dict(payload.get("attributes") or {}),
                    )
                )

        snapshots: list[CachedSourceState] = []
        for ld_name in sorted(meta_payloads):
            meta = meta_payloads[ld_name]
            values = sorted(values_by_ld.get(ld_name, []), key=lambda item: item.node_key)

            snapshots.append(
                CachedSourceState(
                    ld_name=ld_name,
                    source_id=str(meta["source_id"]),
                    availability_status=str(meta["availability_status"]),
                    unavailable_reason=self._optional_str(meta.get("unavailable_reason")),
                    batch_observed_at=_parse_datetime(meta.get("batch_observed_at")),
                    client_received_at=_parse_datetime(meta.get("client_received_at")),
                    client_processed_at=_parse_datetime(meta.get("client_processed_at")),
                    last_alive_at=_parse_datetime(meta.get("last_alive_at")),
                    last_value_updated_at=_parse_datetime(meta.get("last_value_updated_at")),
                    state_updated_at=(
                        _parse_datetime(meta.get("state_updated_at")) or datetime.now(tz=UTC)
                    ),
                    values=values,
                )
            )

        return snapshots

    def _build_next_meta_payload(
        self,
        *,
        ld_name: str,
        batch: AcquiredNodeStateBatch,
        current_meta: dict[str, Any] | None,
        now: datetime,
        values_updated: bool,
    ) -> dict[str, Any]:
        """构造下一版 LD meta payload。"""

        current_meta = current_meta or {}
        batch_observed_at_current = ensure_utc(batch.batch_observed_at)
        client_received_at_current = ensure_utc(batch.client_received_at)
        client_processed_at_current = ensure_utc(batch.client_processed_at)

        batch_observed_at = max_datetime(
            _parse_datetime(current_meta.get("batch_observed_at")),
            batch_observed_at_current,
        )
        client_received_at = max_datetime(
            _parse_datetime(current_meta.get("client_received_at")),
            client_received_at_current,
        )
        client_processed_at = max_datetime(
            _parse_datetime(current_meta.get("client_processed_at")),
            client_processed_at_current,
        )

        return {
            **current_meta,
            "station_id": self._settings.station_id,
            "ld_name": ld_name,
            "source_id": batch.source_id,
            "availability_status": (
                batch.availability_status
                if values_updated
                else str(current_meta.get("availability_status") or "UNKNOWN")
            ),
            "unavailable_reason": None if values_updated else current_meta.get("unavailable_reason"),
            "batch_observed_at": _datetime_to_iso(batch_observed_at),
            "client_received_at": _datetime_to_iso(client_received_at),
            "client_processed_at": _datetime_to_iso(client_processed_at),
            "last_alive_at": _datetime_to_iso(
                max_datetime(
                    _parse_datetime(current_meta.get("last_alive_at")),
                    client_processed_at_current,
                )
            ),
            "last_value_updated_at": _datetime_to_iso(
                max_datetime(
                    _parse_datetime(current_meta.get("last_value_updated_at")),
                    client_processed_at_current if values_updated else None,
                )
            ),
            "state_updated_at": now.isoformat(),
            "attributes": batch.attributes,
        }

    def _build_value_payload(
        self,
        *,
        ld_name: str,
        batch: AcquiredNodeStateBatch,
        value: AcquiredNodeValue,
        now: datetime,
    ) -> dict[str, Any]:
        """构造点位 latest-state payload。"""

        return {
            "station_id": self._settings.station_id,
            "ld_name": ld_name,
            "source_id": batch.source_id,
            "node_key": value.node_key,
            "value": value.value,
            "quality": value.quality,
            "availability_status": batch.availability_status,
            "batch_observed_at": ensure_utc(batch.batch_observed_at).isoformat(),
            "client_received_at": ensure_utc(batch.client_received_at).isoformat(),
            "client_processed_at": ensure_utc(batch.client_processed_at).isoformat(),
            "source_timestamp": _datetime_to_iso(value.source_timestamp),
            "server_timestamp": _datetime_to_iso(value.server_timestamp),
            "client_sequence": value.client_sequence,
            "updated_at": now.isoformat(),
            "attributes": value.attributes,
        }

    def _execute_pipeline(
        self,
        pipe: RedisPipeline,
        *,
        operation: str,
        ld_name: str,
    ) -> None:
        """Execute one Redis pipeline and raise a stable cache error on failure."""

        try:
            pipe.execute()
        except Exception as exc:
            raise self._build_write_error(
                operation=operation,
                ld_name=ld_name,
                exc=exc,
            ) from exc

    def _build_write_error(
        self,
        *,
        operation: str,
        ld_name: str,
        exc: Exception,
    ) -> SourceStateCacheWriteError:
        """Convert one Redis client failure into a stable cache write error."""

        classified = _classify_redis_error(exc)
        message = f"{operation} failed for {ld_name}: {classified.message}"
        return SourceStateCacheWriteError(
            classified.error_code,
            message,
            retryable=classified.retryable,
        )

    def _load_payload(self, field: str) -> dict[str, Any] | None:
        """读取一个 Redis hash field 并解析 JSON。"""

        raw_payload = self._client.hget(self._settings.hash_key, field)
        if raw_payload is None:
            return None

        return cast(dict[str, Any], json.loads(self._decode_value(raw_payload)))

    def _build_ld_meta_field(self, *, ld_name: str) -> str:
        """构造 LD/source meta 字段名。"""

        return f"{self._settings.station_id}:ld:{ld_name}:meta"

    def _build_variable_prefix(self, *, ld_name: str) -> str:
        """构造某个 LD/source 下全部点位字段名前缀。"""

        return f"{self._settings.station_id}:ld:{ld_name}:var:"

    def _build_variable_field(self, *, ld_name: str, node_key: str) -> str:
        """构造点位 latest-state 字段名。"""

        return f"{self._build_variable_prefix(ld_name=ld_name)}{node_key}"

    def _is_ld_meta_field(self, field: str) -> bool:
        """判断 Redis hash field 是否为 LD meta 字段。"""

        prefix = f"{self._settings.station_id}:ld:"
        return field.startswith(prefix) and field.endswith(":meta")

    def _is_variable_field(self, field: str) -> bool:
        """判断 Redis hash field 是否为点位字段。"""

        prefix = f"{self._settings.station_id}:ld:"
        return field.startswith(prefix) and ":var:" in field

    @staticmethod
    def _build_client(settings: RedisSourceStateCacheSettings) -> RedisHashClient:
        """Build one real Redis client lazily so tests can inject a fake client."""

        try:
            from redis import Redis
        except ImportError as exc:
            raise RuntimeError(
                "Redis support requires the `redis` package to be installed."
            ) from exc

        return cast(
            RedisHashClient,
            Redis(
                host=settings.host,
                port=settings.port,
                db=settings.db,
                username=settings.username,
                password=settings.password,
                decode_responses=settings.decode_responses,
            ),
        )

    @staticmethod
    def _decode_value(value: object) -> str:
        """Decode one Redis field name or value into text."""

        if isinstance(value, bytes):
            return value.decode("utf-8")
        return str(value)

    @staticmethod
    def _dump_payload(payload: dict[str, Any]) -> str:
        """Serialize one payload as compact JSON."""

        return json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )

    @staticmethod
    def _optional_str(value: object) -> str | None:
        """Return one optional string value."""

        if value is None:
            return None
        return str(value)


def _should_update_value(
    *,
    incoming: AcquiredNodeValue,
    current_payload: dict[str, Any],
) -> bool:
    """判断 incoming 点值是否允许覆盖当前点值。"""

    if incoming.server_timestamp is not None:
        current_server_timestamp = _parse_datetime(current_payload.get("server_timestamp"))
        if current_server_timestamp is None:
            return True
        return ensure_utc(incoming.server_timestamp) >= current_server_timestamp

    if incoming.client_sequence is not None:
        current_client_sequence = _optional_int(current_payload.get("client_sequence"))
        if current_client_sequence is None:
            return True
        return incoming.client_sequence >= current_client_sequence

    return True


def _classify_redis_error(exc: Exception) -> ClassifiedError:
    """Classify one Redis client failure into a stable cache error shape."""

    message = str(exc).strip() or type(exc).__name__
    normalized = message.upper()
    class_name = type(exc).__name__.lower()

    if "OOM COMMAND NOT ALLOWED" in normalized or "MAXMEMORY" in normalized:
        return ClassifiedError(
            error_code="redis_oom",
            category="cache",
            retryable=True,
            message=message,
        )
    if "MISCONF" in normalized:
        return ClassifiedError(
            error_code="redis_misconf",
            category="cache",
            retryable=True,
            message=message,
        )
    if "READONLY" in normalized:
        return ClassifiedError(
            error_code="redis_readonly",
            category="cache",
            retryable=True,
            message=message,
        )
    if "LOADING" in normalized:
        return ClassifiedError(
            error_code="redis_loading",
            category="cache",
            retryable=True,
            message=message,
        )
    if "BUSY" in normalized:
        return ClassifiedError(
            error_code="redis_busy",
            category="cache",
            retryable=True,
            message=message,
        )
    if isinstance(exc, TimeoutError) or "TIMEOUT" in normalized or "TIMEOUT" in class_name.upper():
        return ClassifiedError(
            error_code="redis_timeout",
            category="cache",
            retryable=True,
            message=message,
        )
    if (
        isinstance(exc, OSError)
        or "CONNECTION" in normalized
        or "BROKEN PIPE" in normalized
        or "RESET BY PEER" in normalized
        or "CONNECTION" in class_name.upper()
    ):
        return ClassifiedError(
            error_code="redis_connection_error",
            category="cache",
            retryable=True,
            message=message,
        )
    return ClassifiedError(
        error_code="redis_write_failed",
        category="cache",
        retryable=True,
        message=message,
    )


def _parse_datetime(value: object) -> datetime | None:
    """Parse one ISO datetime value if present."""

    if value is None:
        return None

    parsed = datetime.fromisoformat(str(value))
    return ensure_utc(parsed)


def _datetime_to_iso(value: datetime | None) -> str | None:
    """Serialize optional datetime."""

    if value is None:
        return None

    return ensure_utc(value).isoformat()


def _optional_int(value: object) -> int | None:
    """Parse optional integer value."""

    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        return int(value)
    return int(str(value))
