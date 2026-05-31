"""协议采集适配器。

实现 SourceAcquisitionPort / SourceWritePort，
封装特定协议（工业协议）的采集或写入逻辑。
外部依赖边界：libiec61850 C 库（ctypes）。
"""

from __future__ import annotations

from datetime import UTC, datetime

from whale.ingest.ports.source.source_write_port import SourceWritePort
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.ingest.usecases.dtos.source_write_request import (
    SourceWriteExecutionOptions,
    SourceWriteItemData,
)
from whale.ingest.usecases.dtos.source_write_result import SourceWriteItemResult, SourceWriteResult
from whale.shared.source.iec61850.backends import RawWriteItemResult
from whale.shared.source.iec61850.reader import Iec61850MmsSourceReader


class Iec61850MmsSourceWriteAdapter(SourceWritePort):
    """通过 libiec61850 native runner 执行 IEC 61850 MMS 直接写入。"""

    async def write(
        self,
        execution: SourceWriteExecutionOptions,
        connection: SourceConnectionData,
        items: list[SourceWriteItemData],
    ) -> SourceWriteResult:
        """执行一次 IEC 61850 MMS 批量写入。对批量点位集合逐一发送 MMS Write 请求并按安全策略校验返回值。
        Each item's ``node_id`` is the MMS object reference,
        ``value_type`` is the MMS type (BOOLEAN, INT32, UINT32,
        FLOAT32, FLOAT64, VISIBLE_STRING).
        The functional constraint is read from
        ``execution.params["fc"]`` or defaults to "SP".
        Args:
            execution: Write execution options.
            connection: Target source connection.
            items: Items to write.
        Returns:
            Structured write result.
        """
        client_requested_at = datetime.now(tz=UTC)
        if execution.dry_run:
            return self._dry_run_result(execution, connection, items, client_requested_at)

        fc = self._resolve_fc(execution)
        host = connection.host.strip()
        if not host or connection.port <= 0:
            return self._error_result(
                execution, items, "connection_invalid",
                "Host or port is invalid.",
                client_requested_at,
            )

        timeout_s = max(execution.request_timeout_ms / 1000, 2.0)
        item_results: list[SourceWriteItemResult] = []
        raw_results: list[RawWriteItemResult] = []

        async with Iec61850MmsSourceReader(host, connection.port, timeout_seconds=timeout_s) as reader:
            for item in items:
                try:
                    raw = await reader.write(
                        obj_ref=item.node_id,
                        fc=fc,
                        value_type=item.value_type,
                        value=item.value,
                        request_id=f"{execution.protocol}_{item.key}",
                    )
                except Exception as exc:
                    raw = RawWriteItemResult(
                        obj_ref=item.node_id,
                        ok=False,
                        status_code="adapter_error",
                        error_message=str(exc) or type(exc).__name__,
                        value_type=item.value_type,
                    )

                raw_results.append(raw)
                item_results.append(
                    SourceWriteItemResult(
                        key=item.key,
                        node_id=raw.obj_ref,
                        ok=raw.ok,
                        status_code=raw.status_code,
                        error_message=raw.error_message,
                        value_type=raw.value_type or item.value_type,
                    )
                )

        success_count = sum(1 for r in raw_results if r.ok)
        failure_count = len(raw_results) - success_count

        return SourceWriteResult(
            request_id=f"iec61850_mms_write_{datetime.now(tz=UTC).timestamp()}",
            dry_run=False,
            success_count=success_count,
            failure_count=failure_count,
            results=item_results,
            client_requested_at=client_requested_at,
            client_completed_at=datetime.now(tz=UTC),
            attributes={"protocol": "iec61850_mms"},
        )

    @staticmethod
    def _resolve_fc(execution: SourceWriteExecutionOptions) -> str:
        """从执行选项中解析 functional constraint (FC)。"""
        fc = execution.params.get("fc", "SP")
        if isinstance(fc, str):
            return fc.strip().upper()
        return "SP"

    async def readback(
        self,
        execution: SourceWriteExecutionOptions,
        connection: SourceConnectionData,
        items: list[SourceWriteItemData],
        write_result: SourceWriteResult,
    ) -> dict[str, str]:
        """写入后回读 MMS 变量值以确认写入生效。

        连接到 IEC 61850 MMS 服务器，读取每个已写入 MMS 对象引用的
        当前值，返回 ``{obj_ref: value_str}`` 映射供
        ``SourceCommandUseCase`` readback 验证使用。

        每次写入后分别执行一次 MMS read 操作，读取同一 FC 下的当前值。

        Args:
            execution: 原始写入执行选项。
            connection: 目标连接（与写入相同）。
            items: 已写入的点位列表。
            write_result: 写入结果（用于元数据）。

        Returns:
            每个已写入 node_id 到 str(value) 的映射。
            如果连接失败或 host/port 无效，返回空字典。
        """
        fc = self._resolve_fc(execution)
        host = connection.host.strip()
        if not host or connection.port <= 0:
            return {}
        timeout_s = max(execution.request_timeout_ms / 1000, 2.0)

        result: dict[str, str] = {}
        async with Iec61850MmsSourceReader(host, connection.port, timeout_seconds=timeout_s) as reader:
            for item in items:
                try:
                    raw = await reader.read(
                        obj_ref=item.node_id,
                        fc=fc,
                        request_id=f"{execution.protocol}_readback_{item.key}",
                    )
                    if raw.ok:
                        result[item.node_id] = str(raw.value) if raw.value is not None else ""
                except Exception:
                    # 单个点的回读失败不影响其他点
                    pass
        return result

    @staticmethod
    def _dry_run_result(
        execution: SourceWriteExecutionOptions,
        connection: SourceConnectionData,
        items: list[SourceWriteItemData],
        client_requested_at: datetime,
    ) -> SourceWriteResult:
        _ = connection
        item_results = [
            SourceWriteItemResult(
                key=item.key,
                node_id=item.node_id,
                ok=False,
                status_code="DRY_RUN",
                error_message="would_write (dry_run mode in adapter)",
                value_type=item.value_type,
            )
            for item in items
        ]
        return SourceWriteResult(
            request_id=f"dry_run_{execution.protocol}",
            dry_run=True,
            success_count=0,
            failure_count=len(item_results),
            results=item_results,
            client_requested_at=client_requested_at,
            client_completed_at=datetime.now(tz=UTC),
            attributes={"protocol": execution.protocol, "mode": "dry_run"},
        )

    @staticmethod
    def _error_result(
        execution: SourceWriteExecutionOptions,
        items: list[SourceWriteItemData],
        error_code: str,
        error_message: str,
        client_requested_at: datetime,
    ) -> SourceWriteResult:
        item_results = [
            SourceWriteItemResult(
                key=item.key,
                node_id=item.node_id,
                ok=False,
                status_code=error_code,
                error_message=error_message,
                value_type=item.value_type,
            )
            for item in items
        ]
        return SourceWriteResult(
            request_id=f"error_{execution.protocol}",
            dry_run=False,
            success_count=0,
            failure_count=len(item_results),
            results=item_results,
            client_requested_at=client_requested_at,
            client_completed_at=datetime.now(tz=UTC),
            attributes={"protocol": execution.protocol, "error": error_code},
        )
