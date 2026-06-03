"""speed layer 消息消费者与写入者。

提供从 message_pipeline 消费消息并写入各存储层的 writer 实现：
- RawArchiveWriter: 消费消息 → 写入 raw_archive 压缩文件。
- RawIndexWriter: 消费消息 → 写入 raw_index 时序索引。
- StandardizedWriter: 消费消息 → 写入 standardized 标准时序层。
- ServingCacheUpdater: 消费消息 → 更新 serving cache。

所有 writer 遵循统一模式：consume → process → sink + DLQ on failure。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from whale.message_pipeline.model import Envelope
from whale.message_pipeline.ports import (
    DeadLetterSinkPort,
    MessageSourcePort,
)
from whale.storage.raw_archive import (
    FileArchiveSinkPort,
    ManifestRepositoryPort,
)
from whale.storage.raw_index import RawIndexSinkPort
from whale.storage.standardized import StandardizedTimeSeriesSinkPort
from whale.storage.serving_cache import ServingCachePort


class RawArchiveWriter:
    """raw_archive 写入者。

    从 MessageSourcePort 消费消息，批量写入 FileArchiveSinkPort。
    单条消息失败时写入 DLQ 并继续，批次写入失败时将整批消息写入 DLQ。

    Attributes:
        _source: 消息消费端口。
        _archive: 压缩文件归档 sink。
        _manifest: batch manifest 记录仓库。
        _dlq: 死信队列 sink。
        _batch_size: 每批消息最大数量。
    """

    def __init__(
        self,
        source: MessageSourcePort,
        archive: FileArchiveSinkPort,
        manifest: ManifestRepositoryPort,
        dlq: DeadLetterSinkPort,
        *,
        batch_size: int = 100,
    ) -> None:
        """初始化 raw_archive writer。

        Args:
            source: 消息消费端口。
            archive: 压缩文件归档 sink。
            manifest: batch manifest 仓库。
            dlq: DLQ sink。
            batch_size: 每批归档的消息数量。
        """
        self._source = source
        self._archive = archive
        self._manifest = manifest
        self._dlq = dlq
        self._batch_size = batch_size

    async def run(self, topic: str, group_id: str) -> int:
        """执行一轮消费-归档循环。

        从 source 消费消息，达到 batch_size 后写入 archive 并记录 manifest。

        Args:
            topic: 消费 topic。
            group_id: consumer group ID。

        Returns:
            本轮归档的消息总数。
        """
        batch: list[dict[str, Any]] = []
        total_written = 0

        async for envelope in self._source.consume(topic, group_id):
            record = _envelope_to_dict(envelope)
            batch.append(record)

            if len(batch) >= self._batch_size:
                written = await self._flush_batch(batch)
                total_written += written
                batch.clear()

        # 处理剩余不足一组的消息
        if batch:
            written = await self._flush_batch(batch)
            total_written += written

        return total_written

    async def _flush_batch(self, batch: list[dict[str, Any]]) -> int:
        """将一批消息写入 archive 并记录 manifest。

        写入失败时，将整批消息发送到 DLQ。

        Args:
            batch: 待归档的消息列表。

        Returns:
            成功归档的消息数。
        """
        if not batch:
            return 0

        batch_id = str(uuid.uuid4())[:8]
        try:
            start_time = _extract_min_time(batch)
            end_time = _extract_max_time(batch)
            written = await self._archive.write(batch_id, batch)
            await self._archive.commit(batch_id)
            await self._manifest.record_manifest(
                batch_id=batch_id,
                file_path=f"{batch_id}.jsonl.gz",
                message_count=written,
                start_time=start_time,
                end_time=end_time,
            )
            return written
        except Exception as exc:
            error_msg = f"raw_archive 批次写入失败 batch_id={batch_id}: {exc}"
            for record in batch:
                envelope = _dict_to_envelope(record)
                await self._dlq.send(envelope, error_msg, retry_count=1)
            return 0


class RawIndexWriter:
    """raw_index 写入者。

    从 MessageSourcePort 消费消息，逐条写入 RawIndexSinkPort。
    单条写入失败时发送到 DLQ。

    Attributes:
        _source: 消息消费端口。
        _index: 原始时序索引 sink。
        _dlq: DLQ sink。
    """

    def __init__(
        self,
        source: MessageSourcePort,
        index: RawIndexSinkPort,
        dlq: DeadLetterSinkPort,
    ) -> None:
        """初始化 raw_index writer。

        Args:
            source: 消息消费端口。
            index: 原始时序索引 sink。
            dlq: DLQ sink。
        """
        self._source = source
        self._index = index
        self._dlq = dlq

    async def run(self, topic: str, group_id: str) -> int:
        """执行一轮消费-索引循环。

        Args:
            topic: 消费 topic。
            group_id: consumer group ID。

        Returns:
            成功索引的消息数。
        """
        indexed_count = 0
        async for envelope in self._source.consume(topic, group_id):
            record = _envelope_to_dict(envelope)
            try:
                success = await self._index.index(record)
                if success:
                    indexed_count += 1
            except Exception as exc:
                await self._dlq.send(
                    envelope,
                    f"raw_index 写入失败: {exc}",
                    retry_count=1,
                )
        return indexed_count


class StandardizedWriter:
    """standardized 层写入者。

    从 MessageSourcePort 消费消息，将每条消息的 items 转换为标准化
    node state 并批量写入 StandardizedTimeSeriesSinkPort。

    Attributes:
        _source: 消息消费端口。
        _sink: 标准时序写入 sink。
        _dlq: DLQ sink。
    """

    def __init__(
        self,
        source: MessageSourcePort,
        sink: StandardizedTimeSeriesSinkPort,
        dlq: DeadLetterSinkPort,
    ) -> None:
        """初始化 standardized writer。

        Args:
            source: 消息消费端口。
            sink: 标准时序写入 sink。
            dlq: DLQ sink。
        """
        self._source = source
        self._sink = sink
        self._dlq = dlq

    async def run(self, topic: str, group_id: str) -> int:
        """执行一轮消费-标准化写入循环。

        对每条 envelope 的 items 进行转换，提取为 node state 列表后批量写入。

        Args:
            topic: 消费 topic。
            group_id: consumer group ID。

        Returns:
            成功写入标准层的记录数。
        """
        total_written = 0
        async for envelope in self._source.consume(topic, group_id):
            node_states = _extract_node_states(envelope)
            if not node_states:
                continue
            try:
                written = await self._sink.write(node_states)
                total_written += written
            except Exception as exc:
                await self._dlq.send(
                    envelope,
                    f"standardized 写入失败: {exc}",
                    retry_count=1,
                )
        return total_written


class ServingCacheUpdater:
    """serving cache 更新者。

    从 MessageSourcePort 消费消息，提取 node state 并更新 ServingCachePort。
    支持乱序保护和 TTL 管理。

    Attributes:
        _source: 消息消费端口。
        _cache: serving cache sink。
        _dlq: DLQ sink。
    """

    def __init__(
        self,
        source: MessageSourcePort,
        cache: ServingCachePort,
        dlq: DeadLetterSinkPort,
        *,
        default_ttl: int = 60,
    ) -> None:
        """初始化 serving cache updater。

        Args:
            source: 消息消费端口。
            cache: serving cache sink。
            dlq: DLQ sink。
            default_ttl: 默认缓存 TTL（秒）。
        """
        self._source = source
        self._cache = cache
        self._dlq = dlq
        self._default_ttl = default_ttl

    async def run(self, topic: str, group_id: str) -> int:
        """执行一轮消费-cache 更新循环。

        Args:
            topic: 消费 topic。
            group_id: consumer group ID。

        Returns:
            成功更新的缓存条目数。
        """
        updated_count = 0
        async for envelope in self._source.consume(topic, group_id):
            for item in envelope.items:
                cache_key = _build_cache_key(envelope, item)
                cache_value = {
                    "source_id": envelope.source_id,
                    "message_type": envelope.message_type,
                    "observed_at": item.get("source_observed_at"),
                    "value": item.get("value"),
                    "quality_code": item.get("quality_code"),
                    "variable_key": item.get("variable_key"),
                }
                try:
                    accepted = await self._cache.set(
                        cache_key,
                        cache_value,
                        ttl_seconds=self._default_ttl,
                    )
                    if accepted:
                        updated_count += 1
                except Exception as exc:
                    await self._dlq.send(
                        envelope,
                        f"serving_cache 更新失败 key={cache_key}: {exc}",
                        retry_count=1,
                    )
        return updated_count


# ---- 辅助函数 ----

def _envelope_to_dict(envelope: Envelope) -> dict[str, Any]:
    """将 Envelope 对象转换为可序列化的 dict。

    用于 raw_archive 和 raw_index 的序列化存储。

    Args:
        envelope: 消息信封对象。

    Returns:
        可 JSON 序列化的字典。
    """
    return {
        "schema_version": envelope.schema_version,
        "message_id": envelope.message_id,
        "message_type": envelope.message_type,
        "trace_id": envelope.trace_id,
        "source_id": envelope.source_id,
        "published_at": envelope.published_at.isoformat(),
        "items": envelope.items,
        "partition_key": envelope.partition_key,
    }


def _dict_to_envelope(record: dict[str, Any]) -> Envelope:
    """将 dict 反序列化为 Envelope 对象。

    用于 DLQ 恢复时从 dict 重建 Envelope。

    Args:
        record: 从文件或索引中读取的记录字典。

    Returns:
        Envelope 对象。
    """
    published_at_str = record.get("published_at", "")
    try:
        published_at = datetime.fromisoformat(str(published_at_str))
    except (ValueError, TypeError):
        published_at = datetime.now(tz=timezone.utc)

    return Envelope(
        schema_version=str(record.get("schema_version", "1.0")),
        message_id=str(record.get("message_id", "")),
        message_type=str(record.get("message_type", "")),
        trace_id=record.get("trace_id"),
        source_id=str(record.get("source_id", "")),
        published_at=published_at,
        items=list(record.get("items", [])),
        partition_key=record.get("partition_key"),
    )


def _extract_min_time(batch: list[dict[str, Any]]) -> datetime:
    """从批次中提取最早时间。

    Args:
        batch: 消息记录列表。

    Returns:
        批次中最早的 published_at 时间。
    """
    min_ts = datetime.now(tz=timezone.utc)
    for record in batch:
        ts_str = record.get("published_at", "")
        try:
            ts = datetime.fromisoformat(str(ts_str))
            if ts < min_ts:
                min_ts = ts
        except (ValueError, TypeError):
            pass
    return min_ts


def _extract_max_time(batch: list[dict[str, Any]]) -> datetime:
    """从批次中提取最晚时间。

    Args:
        batch: 消息记录列表。

    Returns:
        批次中最晚的 published_at 时间。
    """
    max_ts = datetime.min.replace(tzinfo=timezone.utc)
    for record in batch:
        ts_str = record.get("published_at", "")
        try:
            ts = datetime.fromisoformat(str(ts_str))
            if ts > max_ts:
                max_ts = ts
        except (ValueError, TypeError):
            pass
    return max_ts if max_ts != datetime.min.replace(tzinfo=timezone.utc) else datetime.now(tz=timezone.utc)


def _extract_node_states(envelope: Envelope) -> list[dict[str, Any]]:
    """从 Envelope 的 items 中提取标准化 node state 列表。

    将 envelope.items 中每个 item 转换为符合 standardized 层格式的 node state。
    每条 state 包含 node_key、variable_key、value、quality_code、schema_version、
    observed_at、received_at。

    Args:
        envelope: 消息信封。

    Returns:
        标准化 node state 列表。
    """
    node_states: list[dict[str, Any]] = []
    for item in envelope.items:
        state = {
            "source_id": envelope.source_id,
            "message_id": envelope.message_id,
            "schema_version": envelope.schema_version,
            "node_key": (
                item.get("device_id")
                or item.get("device_code")
                or envelope.source_id
            ),
            "variable_key": item.get("variable_key", ""),
            "value": item.get("value"),
            "value_type": item.get("value_type"),
            "quality_code": item.get("quality_code", "0"),
            "observed_at": item.get("source_observed_at"),
            "received_at": envelope.published_at.isoformat(),
        }
        node_states.append(state)
    return node_states


def _build_cache_key(envelope: Envelope, item: dict[str, object]) -> str:
    """构造 serving cache 的缓存键。

    按 source/device/variable 三级构造唯一缓存键。

    Args:
        envelope: 消息信封。
        item: 消息载荷中的一个数据项。

    Returns:
        缓存键字符串，格式为 "source_id:device_id:variable_key"。
    """
    source_id = envelope.source_id
    device_id = item.get("device_id") or item.get("device_code") or source_id
    variable_key = item.get("variable_key", "")
    return f"{source_id}:{device_id}:{variable_key}"
