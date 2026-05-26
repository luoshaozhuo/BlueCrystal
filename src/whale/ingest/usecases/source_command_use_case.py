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
import time
from datetime import UTC, datetime

from whale.ingest.ports.command.source_command_audit_port import (
    SourceCommandAuditEvent,
    SourceCommandAuditPort,
)
from whale.ingest.ports.metrics import IngestMetricEvent, IngestMetricsPort
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
        audit_port: SourceCommandAuditPort | None = None,
        metrics_port: IngestMetricsPort | None = None,
    ) -> None:
        self._write_port_registry = write_port_registry
        self._audit_port = audit_port
        self._metrics_port = metrics_port

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
        started_at = time.monotonic()

        execution = request.execution

        # dry_run 模式：不调用 adapter，返回 would_write 结果
        if execution.dry_run:
            result = self._build_dry_run_result(request)
            self._emit_audit(request=request, result="DRY_RUN", failure_reason=None)
            self._emit_metric(request=request, operation="source_command", status="DRY_RUN", started_at=started_at, error_code=None)
            return result

        # 未显式启用真实写入时拒绝
        if not write_enabled:
            self._emit_audit(
                request=request,
                result="REJECTED",
                failure_reason="write_disabled",
            )
            self._emit_metric(
                request=request,
                operation="source_command",
                status="REJECTED",
                started_at=started_at,
                error_code="write_disabled",
            )
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
        try:
            result = await port.write(
                execution=execution,
                connection=connection,
                items=request.items,
            )
        except Exception as exc:
            self._emit_audit(
                request=request,
                result="FAILED",
                failure_reason=str(exc) or type(exc).__name__,
            )
            self._emit_metric(
                request=request,
                operation="source_command",
                status="FAILED",
                started_at=started_at,
                error_code=type(exc).__name__,
            )
            raise
        if result.trace_id is None:
            result.trace_id = request.trace_id
        result.command_id = request.command_id
        self._emit_audit(request=request, result="SUCCESS", failure_reason=None)
        self._emit_metric(
            request=request,
            operation="source_command",
            status="SUCCESS",
            started_at=started_at,
            error_code=None,
        )
        return result

    @staticmethod
    def _validate(request: SourceWriteRequest) -> None:
        """校验写入请求参数。"""

        if not request.request_id.strip():
            raise ValueError("request_id is required")
        if request.command_id is not None and not request.command_id.strip():
            raise ValueError("command_id cannot be blank when provided")
        if request.trace_id is not None and not request.trace_id.strip():
            raise ValueError("trace_id cannot be blank when provided")
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
            command_id=request.command_id,
            dry_run=True,
            success_count=0,
            failure_count=len(results),
            results=results,
            client_requested_at=request.client_requested_at,
            client_completed_at=datetime.now(tz=UTC),
            trace_id=request.trace_id,
            attributes={"mode": "dry_run"},
        )

    def _emit_audit(
        self,
        *,
        request: SourceWriteRequest,
        result: str,
        failure_reason: str | None,
    ) -> None:
        if self._audit_port is None:
            return
        execution = request.execution
        connection = request.connections[0] if request.connections else None
        source_id = connection.ld_name if connection is not None else None
        self._audit_port.emit(
            SourceCommandAuditEvent(
                request_id=request.request_id,
                command_id=request.command_id,
                trace_id=request.trace_id,
                actor=execution.actor,
                protocol=execution.protocol,
                source_id=source_id,
                target=",".join(item.node_id for item in request.items),
                result=result,
                failure_reason=failure_reason,
                timestamp=datetime.now(tz=UTC),
            )
        )

    def _emit_metric(
        self,
        *,
        request: SourceWriteRequest,
        operation: str,
        status: str,
        started_at: float,
        error_code: str | None,
    ) -> None:
        if self._metrics_port is None:
            return
        self._metrics_port.emit(
            IngestMetricEvent(
                operation=operation,
                source_id=request.connections[0].ld_name if request.connections else None,
                protocol=request.execution.protocol,
                duration_ms=(time.monotonic() - started_at) * 1000.0,
                status=status,
                error_code=error_code,
                timestamp=datetime.now(tz=UTC),
            )
        )
