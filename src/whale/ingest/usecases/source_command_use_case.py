"""Source command/write use case.

独立于 SourceAcquisitionUseCase，负责设备写入/控制命令的编排。
使用 ``source_command_use_case`` 命名，因为工业现场写入通常属于遥控/遥调/设点命令。

职责：
1. 校验 SourceWriteRequest。
2. 根据 protocol 从 SourceWritePortRegistry 获取对应写端口。
3. 调用 SourceWritePort.write()。
4. 返回 SourceWriteResult。
5. 不写 cache、不发 Kafka、不改变 source_acquisition_use_case 的行为。
"""

from __future__ import annotations

import os
from datetime import UTC, datetime

from whale.ingest.ports.source.source_write_port import SourceWritePort
from whale.ingest.ports.source.source_write_port_registry import SourceWritePortRegistry
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.ingest.usecases.dtos.source_write_request import (
    SourceWriteExecutionOptions,
    SourceWriteItemData,
    SourceWriteRequest,
)
from whale.ingest.usecases.dtos.source_write_result import SourceWriteItemResult, SourceWriteResult


class SourceCommandUseCase:
    """统一设备写入 / 控制命令入口。

    Args:
        write_port_registry: 按协议解析写端口的注册表。
    """

    # 环境变量名，用于控制是否启用真实写入
    _WRITE_ENABLED_ENV = "WHALE_INGEST_SOURCE_WRITE_ENABLED"

    def __init__(
        self,
        write_port_registry: SourceWritePortRegistry,
    ) -> None:
        self._write_port_registry = write_port_registry

    async def execute(self, request: SourceWriteRequest) -> SourceWriteResult:
        """校验并执行一次设备写入请求。

        Args:
            request: 写入请求。

        Returns:
            写入结果。

        Raises:
            ValueError: 请求参数非法时抛出。
        """
        self._validate(request)
        write_enabled = self._is_write_enabled()

        execution = request.execution

        # dry_run 模式：不调用 adapter，返回 would_write 结果
        if execution.dry_run:
            return self._build_dry_run_result(request)

        # 未显式启用真实写入时拒绝
        if not write_enabled:
            raise RuntimeError(
                "Real device write is disabled. "
                f"Set {self._WRITE_ENABLED_ENV}=true to enable, "
                "or use dry_run=True for validation-only mode."
            )

        port = self._write_port_registry.get(execution.protocol)
        connection = request.connections[0] if request.connections else SourceConnectionData(
            host="", port=0, ied_name="", ld_name="", namespace_uri="",
        )

        # 调用 port 写入
        result = await port.write(
            execution=execution,
            connection=connection,
            items=request.items,
        )
        return result

    @staticmethod
    def _validate(request: SourceWriteRequest) -> None:
        """校验写入请求参数。"""

        if not request.request_id.strip():
            raise ValueError("request_id is required")
        if not request.execution.protocol.strip():
            raise ValueError("execution.protocol is required")
        if not request.execution.transport.strip():
            raise ValueError("execution.transport is required")
        if not request.connections:
            raise ValueError("connections cannot be empty")
        if not request.items:
            raise ValueError("items cannot be empty")
        for conn in request.connections:
            if not conn.host.strip():
                raise ValueError("connection.host is required")
            if conn.port <= 0:
                raise ValueError("connection.port must be greater than 0")
        for item in request.items:
            if not item.key.strip():
                raise ValueError("item.key is required")
            if not item.node_id.strip():
                raise ValueError("item.node_id is required")
            if not item.value_type.strip():
                raise ValueError("item.value_type is required")
            if item.value is None:
                raise ValueError("item.value is required")

    def _is_write_enabled(self) -> bool:
        """检查是否已显式启用真实设备写入。"""
        val = os.environ.get(self._WRITE_ENABLED_ENV, "").strip().lower()
        return val in ("true", "1", "yes")

    @staticmethod
    def _build_dry_run_result(request: SourceWriteRequest) -> SourceWriteResult:
        """构建 dry_run 模拟结果。"""

        results = [
            SourceWriteItemResult(
                key=item.key,
                node_id=item.node_id,
                ok=False,
                status_code="DRY_RUN",
                error_message="would_write (dry_run mode)",
                value_type=item.value_type,
            )
            for item in request.items
        ]
        return SourceWriteResult(
            request_id=request.request_id,
            dry_run=True,
            success_count=0,
            failure_count=len(results),
            results=results,
            client_requested_at=request.client_requested_at,
            client_completed_at=datetime.now(tz=UTC),
            attributes={"mode": "dry_run"},
        )
