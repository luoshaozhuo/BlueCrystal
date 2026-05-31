"""IEC 61850 Report source 采集适配器。

通过 shared/source 的 report reader 实现 SourceAcquisitionPort 的订阅能力。

IEC 61850 Report 是订阅/事件能力，不通过 SourceWritePort。
Report 通过 RCB 订阅 data set 的数据变化，由 server 主动推送。
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from whale.ingest.ports.source.source_acquisition_port import (
    SourceAcquisitionError,
    SourceAcquisitionPort,
    SourceReadError,
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
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.shared.source.iec61850.report_reader import (
    Iec61850ReportSourceReader,
    RawReportEvent,
)
from whale.shared.utils.time import ensure_utc

LOGGER = logging.getLogger(__name__)


class Iec61850ReportSourceAcquisitionAdapter(SourceAcquisitionPort):
    """IEC 61850 Report 订阅采集适配器。

    只支持 subscription，不支持 polling read 和 write。
    """

    def supports_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> bool:
        """始终返回 True — Report 原生是订阅能力。"""
        del execution, connection
        return True

    async def read(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> AcquiredNodeStateBatch:
        """Report adapter 不支持 polling read，返回空 batch 用于 baseline 占位。

        SubscriptionAcquisitionRole 在 start_subscription 前会调用一次
        _read_initial_baseline。Report adapter 无法执行 polling read，
        返回空 batch 让 role 继续执行到 start_subscription。
        """
        del execution, connection, items
        now_utc = ensure_utc(datetime.now(tz=UTC))
        return AcquiredNodeStateBatch(
            source_id="-",
            batch_observed_at=now_utc,
            client_received_at=now_utc,
            client_processed_at=now_utc,
            values=[],
            availability_status="UNKNOWN",
            attributes={"acquisition_kind": "report_baseline_skip"},
        )

    async def start_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
        *,
        state_received: SubscriptionStateHandler,
    ) -> SourceSubscriptionHandle:
        """启动 Report 订阅。

        Args:
            execution: 本次采集执行选项。
            connection: 数据源连接参数。
            items: 本连接订阅点位列表（Report 的 data set items）。
            state_received: 订阅回调，收到 Report 事件后调用。

        Returns:
            订阅句柄，调用 close() 停止订阅。

        Raises:
            SourceSubscriptionUnsupportedError: 协议不支持订阅时抛出。
            SourceAcquisitionError: 订阅启动失败。
        """
        host = connection.host.strip()
        port = connection.port
        ied_name = connection.ied_name.strip() or "Simulator"
        rcb_ref = connection.params.get("rcb_ref", "EventsRCB01")
        timeout_s = max(execution.request_timeout_ms / 1000, 5.0)
        max_reconnect = int(
            execution.params.get("max_reconnect_attempts", 1)
        )

        if not host or port <= 0:
            raise SourceAcquisitionError(
                f"Invalid connection data: host={host!r}, port={port}"
            )

        reader = Iec61850ReportSourceReader(
            host=host,
            port=port,
            timeout_seconds=timeout_s,
        )
        handle = _ReportSubscriptionHandle(reader=reader)

        async def _on_report_event(event: RawReportEvent) -> None:
            """Map a RawReportEvent to AcquiredNodeStateBatch and forward."""
            batch = _report_event_to_batch(
                connection=connection,
                items=items,
                event=event,
            )
            if batch is not None and not batch.is_empty():
                await state_received(batch)

        async def _on_error(error_msg: str) -> None:
            """Log and track protocol errors / unexpected exits."""
            LOGGER.warning(
                "iec61850_report subscription error: %s (host=%s, port=%s, rcb=%s)",
                error_msg, host, port, rcb_ref,
            )
            if error_msg.startswith("subscription_terminated"):
                handle._mark_closed(error_msg)  # noqa: SLF001

        try:
            await reader.subscribe(
                ied_name=ied_name,
                rcb_ref=str(rcb_ref),
                event_callback=_on_report_event,
                error_callback=_on_error,
                max_reconnect_attempts=max_reconnect,
            )
        except RuntimeError as exc:
            message = str(exc)
            if "executable does not exist" in message:
                raise SourceReadError(f"runner_not_available: {message}") from exc
            raise SourceAcquisitionError(message) from exc
        except Exception as exc:
            raise SourceAcquisitionError(
                str(exc) or type(exc).__name__
            ) from exc

        return handle


class _ReportSubscriptionHandle(SourceSubscriptionHandle):
    """Report 订阅句柄，追踪错误和关闭状态。"""

    def __init__(self, *, reader: Iec61850ReportSourceReader) -> None:
        """初始化报告订阅句柄。Args: report_id: 报告标识符。rpt_enabled: 是否启用。cancel_fn: 取消回调。"""
        self._reader = reader
        self._closed = False
        self._error: str | None = None

    @property
    def closed(self) -> bool:
        """订阅是否已关闭（包括意外断开后无法恢复）。"""
        return self._closed or not self._reader.is_active

    @property
    def error(self) -> str | None:
        """订阅错误信息，无错误时返回 None。"""
        return self._error

    def _mark_closed(self, error_msg: str) -> None:
        """标记订阅因错误而关闭。"""
        self._closed = True
        self._error = error_msg

    async def close(self) -> None:
        """停止订阅并释放 Report reader 资源。"""
        if self._closed:
            return
        self._closed = True
        await self._reader.close()


def _report_event_to_batch(
    *,
    connection: SourceConnectionData,
    items: list[AcquisitionItemData],
    event: RawReportEvent,
) -> AcquiredNodeStateBatch | None:
    """将 RawReportEvent 映射为 AcquiredNodeStateBatch。

    每个 REPORT event 对应一条 batch。
    value 按 event.values 在 data set 中的位置映射到 items。
    如果 event 没有 values 或无法映射，返回 None。
    """
    if not event.ok or not event.values:
        return None

    now_utc = ensure_utc(datetime.now(tz=UTC))
    source_id = (
        connection.ld_name.strip()
        or connection.ied_name.strip()
        or "iec61850_report"
    )

    values: list[AcquiredNodeValue] = []
    for idx, raw_value in enumerate(event.values):
        if idx >= len(items):
            # 剩余 values 无对应 items，截断
            LOGGER.warning(
                "report event has %d values but only %d items; "
                "truncating excess values",
                len(event.values), len(items),
            )
            break
        item = items[idx]
        key = item.key if item is not None else f"report_value_{idx}"
        relative_path = item.relative_path if item is not None else ""
        profile_item_id = item.profile_item_id if item is not None else ""

        values.append(
            AcquiredNodeValue(
                node_key=key,
                value=raw_value,
                quality="GOOD",
                source_timestamp=None,
                server_timestamp=(
                    ensure_utc(datetime.fromtimestamp(event.timestamp_ms / 1000, tz=UTC))
                    if event.timestamp_ms > 0
                    else None
                ),
                client_sequence=event.seq_num,
                attributes={
                    "profile_item_id": profile_item_id,
                    "relative_path": relative_path,
                    "rcb_ref": event.rcb_ref,
                    "seq_num": str(event.seq_num),
                },
            )
        )

    if len(values) < len(items):
        LOGGER.warning(
            "report event has %d values but %d items requested; "
            "mapped %d values",
            len(event.values), len(items), len(values),
        )

    return AcquiredNodeStateBatch(
        source_id=source_id,
        batch_observed_at=now_utc,
        client_received_at=now_utc,
        client_processed_at=now_utc,
        values=values,
        availability_status="VALID",
        attributes={"acquisition_kind": "report_subscription"},
    )
