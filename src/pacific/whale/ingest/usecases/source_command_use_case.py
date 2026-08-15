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
from inspect import isawaitable

from pacific.whale.ingest.ports.command.source_command_audit_port import (
    SourceCommandAuditEvent,
    SourceCommandAuditPort,
)
from pacific.whale.ingest.ports.metrics import IngestMetricEvent, IngestMetricsPort
from pacific.whale.ingest.ports.runtime.write_lease_port import WriteLeasePort
from pacific.whale.ingest.ports.source.source_write_port_registry import SourceWritePortRegistry
from pacific.whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from pacific.whale.ingest.usecases.dtos.source_write_request import (
    SourceWriteRequest,
)
from pacific.whale.ingest.usecases.dtos.source_write_result import SourceWriteItemResult, SourceWriteResult


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
        write_lease_port: WriteLeasePort | None = None,
    ) -> None:
        """初始化命令用例。Args: write_port_registry: 写入 port 注册表。command_audit_sink: 命令审计 sink。write_lease_service: 写入租约服务。security_profile: 安全策略。"""
        self._write_port_registry = write_port_registry
        self._audit_port = audit_port
        self._metrics_port = metrics_port
        self._write_lease_port = write_lease_port

    async def execute(self, request: SourceWriteRequest) -> SourceWriteResult:
        """校验并执行一次设备写入请求。

        流程顺序：
        1. 校验请求参数。
        2. dry_run 或 write_disabled 短路返回/抛出。
        3. 获取 write port 和 connection，尝试 acquire write lease。
        4. 在 try 块内执行 precheck、write、readback。
        5. SUCCESS audit/metric 仅在 readback 验证通过后发出。
        6. finally 块确保 write lease 在所有异常路径释放。

        Args:
            request: 写入请求。

        Returns:
            写入结果。

        Raises:
            ValueError: 请求参数非法时抛出。
            RuntimeError: write_disabled、lease 冲突、precheck 失败、readback 不匹配时抛出。
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
        lease_resource_id = connection.ld_name or connection.ied_name or "unknown"
        fencing_token: int | None = None
        lease_acquired: bool = False

        # 尝试 acquire write lease（可选）
        if self._write_lease_port is not None:
            try:
                lease_decision = self._write_lease_port.acquire(
                    resource_id=lease_resource_id,
                    holder_key=execution.actor or "ingest",
                    requested_fencing_token=_int_param(execution.params.get("fencing_token")),
                )
            except TypeError:
                lease_decision = self._write_lease_port.acquire(
                    resource_id=lease_resource_id,
                    holder_key=execution.actor or "ingest",
                )
            fencing_token = lease_decision.fencing_token
            if not lease_decision.allowed:
                self._emit_audit(
                    request=request,
                    result=lease_decision.result,
                    failure_reason=lease_decision.reason_code,
                    decision="DENY",
                    reason_code=lease_decision.reason_code,
                    fencing_token=fencing_token,
                )
                self._emit_metric(
                    request=request,
                    operation="source_command",
                    status=lease_decision.result,
                    started_at=started_at,
                    error_code=lease_decision.reason_code or lease_decision.result,
                )
                raise RuntimeError(
                    f"Write lease denied: {lease_decision.reason_code or lease_decision.result}"
                )
            lease_acquired = True

        # 主执行体：precheck / write / readback 全部在 try 块内，
        # 确保任何异常路径都通过 finally 释放 lease。
        try:
            precheck = getattr(port, "precheck", None)
            if callable(precheck):
                precheck_result = precheck(execution=execution, connection=connection, items=request.items)
                if isawaitable(precheck_result):
                    precheck_result = await precheck_result
                if precheck_result not in (True, None):
                    reason = str(precheck_result)
                    self._emit_audit(
                        request=request,
                        result="FAILED",
                        failure_reason=reason,
                        decision="ALLOW",
                        reason_code="PRECHECK_FAILED",
                        fencing_token=fencing_token,
                    )
                    self._emit_metric(
                        request=request,
                        operation="source_command",
                        status="FAILED",
                        started_at=started_at,
                        error_code="PRECHECK_FAILED",
                    )
                    raise RuntimeError(reason)

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
                    decision="ALLOW",
                    reason_code=type(exc).__name__,
                    fencing_token=fencing_token,
                )
                self._emit_metric(
                    request=request,
                    operation="source_command",
                    status="FAILED",
                    started_at=started_at,
                    error_code=type(exc).__name__,
                )
                raise

            # 填充 result 元数据
            if result.trace_id is None:
                result.trace_id = request.trace_id
            result.command_id = request.command_id

            # readback 验证（在 SUCCESS 之前执行）
            readback = getattr(port, "readback", None)
            if execution.params.get("require_readback") and callable(readback):
                readback_values = readback(
                    execution=execution,
                    connection=connection,
                    items=request.items,
                    write_result=result,
                )
                if isawaitable(readback_values):
                    readback_values = await readback_values
                readback_map = dict(readback_values or {})
                mismatches = [
                    item.node_id
                    for item in request.items
                    if str(readback_map.get(item.node_id)) != str(item.value)
                ]
                if mismatches:
                    self._emit_audit(
                        request=request,
                        result="FAILED",
                        failure_reason="readback_mismatch",
                        decision="ALLOW",
                        reason_code="READBACK_MISMATCH",
                        fencing_token=fencing_token,
                    )
                    self._emit_metric(
                        request=request,
                        operation="source_command",
                        status="FAILED",
                        started_at=started_at,
                        error_code="READBACK_MISMATCH",
                    )
                    raise RuntimeError("Write readback mismatch.")
                result.attributes["readback"] = "confirmed"

            # readback 通过后才 emit SUCCESS
            self._emit_audit(
                request=request,
                result="SUCCESS",
                failure_reason=None,
                decision="ALLOW",
                reason_code=None,
                fencing_token=fencing_token,
            )
            self._emit_metric(
                request=request,
                operation="source_command",
                status="SUCCESS",
                started_at=started_at,
                error_code=None,
            )
            return result

        finally:
            # 确保所有异常路径都释放 write lease
            if lease_acquired and self._write_lease_port is not None:
                self._write_lease_port.release(
                    resource_id=lease_resource_id,
                    holder_key=execution.actor or "ingest",
                )

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
        decision: str = "ALLOW",
        reason_code: str | None = None,
        fencing_token: int | None = None,
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
                decision=decision,
                result=result,
                failure_reason=failure_reason,
                reason_code=reason_code,
                fencing_token=fencing_token,
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


def _int_param(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None
