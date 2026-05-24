"""OPC UA source write adapter.

本模块负责把 ingest DTO 转换为 shared/source 的 open62541 raw writer 调用，
并将 ``RawWriteItemResult`` 转换为 ``SourceWriteResult``。

设计约定：
- 实现 SourceWritePort，不依赖 source_lab。
- 通过 OpcUaSourceReader 执行写入。
- 每次 write 创建一个短期 reader 连接，写完后释放。
- 不支持订阅 / polling 写，只支持单次写入。
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
from whale.shared.source.models import SourceConnectionProfile
from whale.shared.source.opcua.backends import RawWriteItemResult
from whale.shared.source.opcua.reader import OpcUaSourceReader


class OpcUaSourceWriteAdapter(SourceWritePort):
    """通过 open62541 后端执行 OPC UA 变量写入。"""

    async def write(
        self,
        execution: SourceWriteExecutionOptions,
        connection: SourceConnectionData,
        items: list[SourceWriteItemData],
    ) -> SourceWriteResult:
        """执行一次 OPC UA 批量写入。

        Args:
            execution: 写入执行选项。
            connection: 目标 source 连接。
            items: 待写入点位列表。

        Returns:
            结构化写入结果。
        """
        client_requested_at = datetime.now(tz=UTC)
        if execution.dry_run:
            return self._dry_run_result(execution, connection, items, client_requested_at)

        endpoint = self._build_endpoint(execution, connection)
        if not endpoint:
            return self._error_result(
                execution, items, "endpoint_resolution_failed",
                "Cannot resolve OPC UA endpoint from connection and execution options.",
                client_requested_at,
            )

        namespace_uri = connection.namespace_uri.strip() if connection.namespace_uri else None
        profile = SourceConnectionProfile(
            endpoint=endpoint,
            namespace_uri=namespace_uri,
            timeout_seconds=max(execution.request_timeout_ms / 1000, 2.0),
            params=dict(execution.params),
        )

        item_results: list[SourceWriteItemResult] = []
        raw_results: list[RawWriteItemResult] = []

        async with OpcUaSourceReader(profile) as reader:
            for item in items:
                try:
                    raw = await reader.write(
                        node_id=item.node_id,
                        value_type=item.value_type,
                        value=item.value,
                        request_id=f"{execution.protocol}_{item.key}",
                    )
                except Exception as exc:
                    raw = RawWriteItemResult(
                        node_id=item.node_id,
                        ok=False,
                        status_code="adapter_error",
                        error_message=str(exc) or type(exc).__name__,
                        value_type=item.value_type,
                    )

                raw_results.append(raw)
                item_results.append(
                    SourceWriteItemResult(
                        key=item.key,
                        node_id=raw.node_id,
                        ok=raw.ok,
                        status_code=raw.status_code,
                        error_message=raw.error_message,
                        value_type=raw.value_type or item.value_type,
                    )
                )

        success_count = sum(1 for r in raw_results if r.ok)
        failure_count = len(raw_results) - success_count

        return SourceWriteResult(
            request_id=f"opcua_write_{datetime.now(tz=UTC).timestamp()}",
            dry_run=False,
            success_count=success_count,
            failure_count=failure_count,
            results=item_results,
            client_requested_at=client_requested_at,
            client_completed_at=datetime.now(tz=UTC),
            attributes={"protocol": "opcua"},
        )

    @staticmethod
    def _build_endpoint(
        execution: SourceWriteExecutionOptions,
        connection: SourceConnectionData,
    ) -> str:
        """构造 OPC UA endpoint URL。"""

        protocol = execution.protocol.strip().lower()
        transport = execution.transport.strip().lower()
        host = connection.host.strip()
        port = connection.port

        if not protocol or not transport or not host or port <= 0:
            return ""

        scheme = "opc.tcp" if protocol == "opcua" and transport == "tcp" else f"{protocol}.{transport}"
        return f"{scheme}://{host}:{port}"

    @staticmethod
    def _dry_run_result(
        execution: SourceWriteExecutionOptions,
        connection: SourceConnectionData,
        items: list[SourceWriteItemData],
        client_requested_at: datetime,
    ) -> SourceWriteResult:
        """构建 dry_run 模拟结果。"""

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
        """构建初始化错误结果。"""

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
