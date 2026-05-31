"""用例：将全量状态快照从缓存发布到消息队列。包含过滤、组装和发布全流程编排。"""

from __future__ import annotations

import uuid
import time
from datetime import UTC, datetime
from typing import Any

from whale.ingest.ports.message.message_publisher_port import (
    MessagePublisherPort,
    MessagePublishResult,
    StateSnapshotItem,
    StateSnapshotMessage,
)
from whale.ingest.ports.metrics import IngestMetricEvent, IngestMetricsPort
from whale.ingest.ports.state.source_state_snapshot_reader_port import (
    CachedSourceState,
    SourceStateSnapshotReaderPort,
)
from whale.ingest.usecases.dtos.state_publish_request import StateSnapshotPublishRequest
from whale.ingest.usecases.dtos.state_publish_result import (
    PublishStatus,
    StateSnapshotPublishResult,
)

_DEFAULT_SCHEMA_VERSION = "1.0"
_DEFAULT_MESSAGE_TYPE = "state_snapshot"
_DEFAULT_SOURCE_MODULE = "ingest"


class StateSnapshotPublishUseCase:
    """从缓存读取当前最新状态快照并发布到消息队列。是整个发布流程的顶层协调类。"""

    def __init__(
        self,
        reader: SourceStateSnapshotReaderPort,
        publisher: MessagePublisherPort,
        station_id: str,
        metrics_port: IngestMetricsPort | None = None,
    ) -> None:
        """存储注入的 port 和本地站标识符。保存消息发布器、缓存读取器等依赖。"""
        self._reader = reader
        self._publisher = publisher
        self._station_id = station_id
        self._metrics_port = metrics_port

    def execute(self, request: StateSnapshotPublishRequest) -> StateSnapshotPublishResult:
        """执行一次状态快照发布周期。读取缓存、应用过滤、组装消息并发布。"""
        trace_id = request.trace_id
        snapshot_at = datetime.now(tz=UTC)
        started_at = time.monotonic()

        # Step 1: read from cache
        try:
            sources: list[CachedSourceState] = self._reader.read_snapshot()
        except Exception as exc:
            self._emit_metric(
                operation="snapshot_publish",
                source_id=request.source_id,
                protocol=None,
                status="FAILED",
                error_code=type(exc).__name__,
                started_at=started_at,
            )
            return StateSnapshotPublishResult(
                status=PublishStatus.FAILED,
                source_count=0,
                item_count=0,
                trace_id=trace_id,
                snapshot_at=snapshot_at,
                error=f"Failed to read snapshot from cache: {exc}",
            )

        # Step 2: filter
        filtered = self._apply_filters(sources, request)

        if not filtered:
            self._emit_metric(
                operation="snapshot_publish",
                source_id=request.source_id,
                protocol=None,
                status="NO_DATA",
                error_code=None,
                started_at=started_at,
            )
            return StateSnapshotPublishResult(
                status=PublishStatus.NO_DATA,
                source_count=len(sources),
                item_count=0,
                trace_id=trace_id,
                snapshot_at=snapshot_at,
            )

        # Step 3: build messages
        station_id = request.station_id or self._station_id
        messages = self._build_messages(filtered, station_id, snapshot_at, request)

        if not messages:
            self._emit_metric(
                operation="snapshot_publish",
                source_id=request.source_id,
                protocol=None,
                status="NO_DATA",
                error_code=None,
                started_at=started_at,
            )
            return StateSnapshotPublishResult(
                status=PublishStatus.NO_DATA,
                source_count=len(filtered),
                item_count=0,
                trace_id=trace_id,
                snapshot_at=snapshot_at,
            )

        total_items = sum(msg.item_count for msg in messages)

        # Step 4: dry_run check
        if request.dry_run:
            self._emit_metric(
                operation="snapshot_publish",
                source_id=request.source_id,
                protocol=None,
                status="DRY_RUN",
                error_code=None,
                started_at=started_at,
            )
            return StateSnapshotPublishResult(
                status=PublishStatus.DRY_RUN,
                source_count=len(filtered),
                item_count=total_items,
                message_count=len(messages),
                trace_id=trace_id,
                snapshot_at=snapshot_at,
            )

        # Step 5: publish
        result = self._publish_all(messages, trace_id, snapshot_at, len(filtered), total_items)
        self._emit_metric(
            operation="snapshot_publish",
            source_id=request.source_id,
            protocol=None,
            status=result.status.value,
            error_code=None if result.error is None else "publish_failed",
            started_at=started_at,
        )
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_filters(
        sources: list[CachedSourceState],
        request: StateSnapshotPublishRequest,
    ) -> list[CachedSourceState]:
        """应用可选的 source_id 和 ld_name 过滤条件。按请求参数筛选缓存条目。"""

        result = sources
        if request.station_id:
            # station_id is not a first-class field on CachedSourceState;
            # filter by ld_name prefix convention (ld_name = "station/source/ld")
            result = [s for s in result if s.ld_name and s.ld_name.startswith(request.station_id)]
        if request.source_id:
            result = [s for s in result if s.source_id == request.source_id]
        if request.ld_name:
            result = [s for s in result if s.ld_name == request.ld_name]
        return result

    def _build_messages(
        self,
        sources: list[CachedSourceState],
        station_id: str,
        snapshot_at: datetime,
        request: StateSnapshotPublishRequest,
    ) -> list[StateSnapshotMessage]:
        """将过滤后的缓存源映射为一条或多条快照消息。按 source 分组构建消息。"""

        snapshot_id = _generate_snapshot_id(station_id, snapshot_at)
        trace_id = request.trace_id
        max_items = request.max_items_per_message

        all_items: list[StateSnapshotItem] = []
        for source in sources:
            source_station_id = station_id
            device_code = source.source_id or source.ld_name or ""
            device_id = source.ld_name or source.source_id or ""

            for node_value in source.values:
                item = self._map_item(
                    source=source,
                    node_value=node_value,
                    station_id=source_station_id,
                    device_id=device_id,
                    device_code=device_code,
                )
                all_items.append(item)

        if not all_items:
            return []

        if max_items <= 0:
            # Single message
            return [
                self._assemble_message(
                    snapshot_id=snapshot_id,
                    snapshot_at=snapshot_at,
                    items=all_items,
                    message_seq=0,
                    trace_id=trace_id,
                )
            ]

        # Split into multiple messages
        messages: list[StateSnapshotMessage] = []
        for seq, start in enumerate(range(0, len(all_items), max_items)):
            chunk = all_items[start : start + max_items]
            msg = self._assemble_message(
                snapshot_id=snapshot_id,
                snapshot_at=snapshot_at,
                items=chunk,
                message_seq=seq,
                trace_id=trace_id,
            )
            messages.append(msg)
        return messages

    @staticmethod
    def _map_item(
        source: CachedSourceState,
        node_value: Any,
        station_id: str,
        device_id: str,
        device_code: str,
    ) -> StateSnapshotItem:
        """将一个缓存节点值及其所属源状态映射为一条 StateSnapshotItem。"""

        attributes = _extract_attributes(node_value)
        model_id = attributes.get("model_id", device_code)

        # received_at: prefer batch-level client_received_at, fall back to
        # value-level server_timestamp, then client_sequence-based estimate
        received_at = source.client_received_at
        if received_at is None and hasattr(node_value, "server_timestamp"):
            received_at = node_value.server_timestamp  # type: ignore[union-attr]

        value_type = attributes.get("value_type") or None
        quality_value: str | None = node_value.quality  # type: ignore[union-attr]

        return StateSnapshotItem(
            station_id=station_id,
            device_id=device_id,
            device_code=device_code,
            model_id=model_id,
            variable_key=node_value.node_key,  # type: ignore[union-attr]
            value=node_value.value,  # type: ignore[union-attr]
            value_type=value_type,
            quality_code=quality_value,
            source_observed_at=node_value.source_timestamp,  # type: ignore[union-attr]
            received_at=received_at,
            updated_at=node_value.updated_at,  # type: ignore[union-attr]
        )

    @staticmethod
    def _assemble_message(
        snapshot_id: str,
        snapshot_at: datetime,
        items: list[StateSnapshotItem],
        message_seq: int,
        trace_id: str | None,
    ) -> StateSnapshotMessage:
        """将一组快照条目包装为一条 StateSnapshotMessage。设置元数据和条目列表。"""

        seq_suffix = f"-{message_seq:04d}" if message_seq > 0 else ""
        message_id = f"{snapshot_id}{seq_suffix}"
        message_type = _DEFAULT_MESSAGE_TYPE

        return StateSnapshotMessage(
            message_id=message_id,
            schema_version=_DEFAULT_SCHEMA_VERSION,
            message_type=message_type,
            source_module=_DEFAULT_SOURCE_MODULE,
            snapshot_id=snapshot_id,
            snapshot_at=snapshot_at,
            item_count=len(items),
            items=items,
            trace_id=trace_id,
        )

    def _publish_all(
        self,
        messages: list[StateSnapshotMessage],
        trace_id: str | None,
        snapshot_at: datetime,
        source_count: int,
        total_items: int,
    ) -> StateSnapshotPublishResult:
        """发布所有组装后的消息并聚合结果。逐条发布并收集成功/失败的计数。"""

        aggregated = StateSnapshotPublishResult(
            status=PublishStatus.SUCCESS,
            source_count=source_count,
            item_count=0,
            trace_id=trace_id,
            snapshot_at=snapshot_at,
        )

        for message in messages:
            try:
                result: MessagePublishResult = self._publisher.publish_snapshot(message)
            except Exception as exc:
                aggregated.merge(
                    StateSnapshotPublishResult(
                        status=PublishStatus.FAILED,
                        source_count=0,
                        item_count=message.item_count,
                        message_count=1,
                        failed_count=message.item_count,
                        trace_id=trace_id,
                        snapshot_at=snapshot_at,
                        error=f"Publish failed: {exc}",
                    )
                )
                continue

            if result.success:
                aggregated.merge(
                    StateSnapshotPublishResult(
                        status=PublishStatus.SUCCESS,
                        source_count=0,
                        item_count=message.item_count,
                        message_count=1,
                        published_count=message.item_count,
                        trace_id=trace_id,
                        snapshot_at=snapshot_at,
                    )
                )
            else:
                aggregated.merge(
                    StateSnapshotPublishResult(
                        status=PublishStatus.FAILED,
                        source_count=0,
                        item_count=message.item_count,
                        message_count=1,
                        failed_count=message.item_count,
                        trace_id=trace_id,
                        snapshot_at=snapshot_at,
                        error=result.error_message or "Unknown publish failure",
                    )
                )

        return aggregated

    def _emit_metric(
        self,
        *,
        operation: str,
        source_id: str | None,
        protocol: str | None,
        status: str,
        error_code: str | None,
        started_at: float,
    ) -> None:
        if self._metrics_port is None:
            return
        self._metrics_port.emit(
            IngestMetricEvent(
                operation=operation,
                source_id=source_id,
                protocol=protocol,
                duration_ms=(time.monotonic() - started_at) * 1000.0,
                status=status,
                error_code=error_code,
                timestamp=datetime.now(tz=UTC),
            )
        )


def _generate_snapshot_id(station_id: str, snapshot_at: datetime) -> str:
    """生成唯一快照 ID。用于标识一次发布周期。"""
    suffix = uuid.uuid4().hex[:8]
    return f"{station_id}-{snapshot_at.strftime('%Y%m%dT%H%M%S')}-{suffix}"


def _extract_attributes(obj: Any) -> dict[str, str]:
    """从可能具有 attributes 字段的对象中提取字符串键属性字典。"""
    attrs = getattr(obj, "attributes", None) or {}
    if not isinstance(attrs, dict):
        return {}
    return {str(k): str(v) for k, v in attrs.items() if v is not None}
