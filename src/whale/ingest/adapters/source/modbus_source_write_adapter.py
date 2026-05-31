"""协议采集适配器。

实现 SourceAcquisitionPort / SourceWritePort，
封装特定协议（工业协议）的采集或写入逻辑。
外部依赖边界：libmodbus C 库（ctypes）。
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
from whale.shared.source.modbus.backends import RawWriteItemResult
from whale.shared.source.modbus.reader import ModbusSourceReader


class ModbusSourceWriteAdapter(SourceWritePort):
    """通过 native runner 执行 Modbus TCP 写入（FC06 写单个寄存器）。"""

    async def write(
        self,
        execution: SourceWriteExecutionOptions,
        connection: SourceConnectionData,
        items: list[SourceWriteItemData],
    ) -> SourceWriteResult:
        """执行一次 Modbus TCP 批量写入。按点位列表依次写入 holding register（功能码 06 或 16）。
        Args:
            execution: Write execution options.
            connection: Target source connection.
            items: Items to write, each with ``node_id`` as register address string.
        Returns:
            Structured write result.
        """
        client_requested_at = datetime.now(tz=UTC)
        if execution.dry_run:
            return self._dry_run_result(execution, connection, items, client_requested_at)

        host = connection.host.strip()
        if not host:
            return self._error_result(
                execution, items, "host_resolution_failed",
                "connection.host is required",
                client_requested_at,
            )
        if connection.port <= 0:
            return self._error_result(
                execution, items, "port_resolution_failed",
                "connection.port must be > 0",
                client_requested_at,
            )
        unit_id = int(connection.params.get("modbus_unit_id", 1))

        item_results: list[SourceWriteItemResult] = []
        raw_results: list[RawWriteItemResult] = []

        async with ModbusSourceReader(host=host, port=connection.port, unit_id=unit_id) as reader:
            for item in items:
                reg_addr = self._resolve_reg_addr(item)
                if reg_addr is None:
                    raw = RawWriteItemResult(
                        reg_addr=-1,
                        ok=False,
                        status_code="adapter_error",
                        error_message=f"cannot parse node_id={item.node_id!r} as register address",
                    )
                else:
                    try:
                        raw = await reader.write(
                            reg_addr=reg_addr,
                            value_type=item.value_type,
                            value=item.value,
                            request_id=f"{execution.protocol}_{item.key}",
                        )
                    except Exception as exc:
                        raw = RawWriteItemResult(
                            reg_addr=reg_addr if reg_addr is not None else -1,
                            ok=False,
                            status_code="adapter_error",
                            error_message=str(exc) or type(exc).__name__,
                        )

                raw_results.append(raw)
                item_results.append(
                    SourceWriteItemResult(
                        key=item.key,
                        node_id=str(raw.reg_addr),
                        ok=raw.ok,
                        status_code=raw.status_code,
                        error_message=raw.error_message,
                        value_type=item.value_type,
                    )
                )

        success_count = sum(1 for r in raw_results if r.ok)
        failure_count = len(raw_results) - success_count

        return SourceWriteResult(
            request_id=f"modbus_write_{datetime.now(tz=UTC).timestamp()}",
            dry_run=False,
            success_count=success_count,
            failure_count=failure_count,
            results=item_results,
            client_requested_at=client_requested_at,
            client_completed_at=datetime.now(tz=UTC),
            attributes={"protocol": "modbus_tcp"},
        )

    @staticmethod
    def _resolve_reg_addr(item: SourceWriteItemData) -> int | None:
        """将 node_id（寄存器地址字符串）转换为整数。"""
        node_id = item.node_id.strip()
        if node_id.startswith("0x") or node_id.startswith("0X"):
            try:
                return int(node_id, 16)
            except ValueError:
                return None
        if node_id.isdigit() or (node_id.startswith("-") and node_id[1:].isdigit()):
            return int(node_id)
        return None

    async def readback(
        self,
        execution: SourceWriteExecutionOptions,
        connection: SourceConnectionData,
        items: list[SourceWriteItemData],
        write_result: SourceWriteResult,
    ) -> dict[str, str]:
        """写入后回读寄存器值以确认写入生效。

        连接到 Modbus TCP 设备，读取每个已写入寄存器的当前值，
        返回 ``{node_id: value_str}`` 映射供 ``SourceCommandUseCase``
        readback 验证使用。

        回读使用 FC03（read holding registers），与 FC06（write single register）
        对应。每个寄存器地址独立读取。

        Args:
            execution: 原始写入执行选项。
            connection: 目标连接（与写入相同）。
            items: 已写入的点位列表。
            write_result: 写入结果（用于元数据）。

        Returns:
            每个已写入 node_id 到 str(value) 的映射。
            如果连接失败或 host/port 无效，返回空字典。
        """
        host = connection.host.strip()
        if not host or connection.port <= 0:
            return {}
        unit_id = int(connection.params.get("modbus_unit_id", 1))

        async with ModbusSourceReader(host=host, port=connection.port, unit_id=unit_id) as reader:
            reg_addrs: list[int] = []
            for item in items:
                addr = self._resolve_reg_addr(item)
                if addr is not None:
                    reg_addrs.append(addr)
            if not reg_addrs:
                return {}
            plan = reader.prepare_read(reg_addrs)
            raw = await reader.read_prepared(plan)
            if not raw.ok:
                return {}
            result: dict[str, str] = {}
            # 按写入顺序映射 node_id 到读取值
            for item, reg_val in zip(items, raw.values, strict=False):
                result[item.node_id] = str(reg_val)
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
