"""协议采集适配器。

实现 SourceAcquisitionPort / SourceWritePort，
封装特定协议（工业协议）的采集或写入逻辑。
外部依赖边界：lib60870 C 库（ctypes）。
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
from whale.shared.source.iec104.backends import RawWriteItemResult
from whale.shared.source.iec104.reader import Iec104SourceReader


class Iec104SourceWriteAdapter(SourceWritePort):
    """通过 native runner 执行 IEC 104 写入（C_SC_NA_1 命令）。"""

    async def write(
        self,
        execution: SourceWriteExecutionOptions,
        connection: SourceConnectionData,
        items: list[SourceWriteItemData],
    ) -> SourceWriteResult:
        """执行一次 IEC 104 批量写入。解析点位列表并依次发送 select/operate 命令。
        Args:
            execution: Write execution options.
            connection: Target source connection.
            items: Items to write, each with ``node_id`` as IOA string.
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
        common_addr = int(connection.params.get("common_address", 1))

        item_results: list[SourceWriteItemResult] = []
        raw_results: list[RawWriteItemResult] = []

        async with Iec104SourceReader(host=host, port=connection.port, common_addr=common_addr) as reader:
            for item in items:
                ioa = self._resolve_ioa(item)
                command_type = self._resolve_command_type(item)

                if ioa is None or command_type is None:
                    raw = RawWriteItemResult(
                        ioa=-1,
                        ok=False,
                        status_code="adapter_error",
                        error_message=(
                            f"cannot resolve ioa={item.node_id!r} "
                            f"or command_type={item.value_type!r}"
                        ),
                        command_type=None,
                    )
                else:
                    try:
                        raw = await reader.write(
                            ioa=ioa,
                            command_type=command_type,
                            value=item.value,
                            request_id=f"{execution.protocol}_{item.key}",
                        )
                    except Exception as exc:
                        raw = RawWriteItemResult(
                            ioa=ioa if ioa is not None else -1,
                            ok=False,
                            status_code="adapter_error",
                            error_message=str(exc) or type(exc).__name__,
                            command_type=command_type,
                        )

                raw_results.append(raw)
                item_results.append(
                    SourceWriteItemResult(
                        key=item.key,
                        node_id=str(raw.ioa),
                        ok=raw.ok,
                        status_code=raw.status_code,
                        error_message=raw.error_message,
                        value_type=raw.command_type or item.value_type,
                    )
                )

        success_count = sum(1 for r in raw_results if r.ok)
        failure_count = len(raw_results) - success_count

        return SourceWriteResult(
            request_id=f"iec104_write_{datetime.now(tz=UTC).timestamp()}",
            dry_run=False,
            success_count=success_count,
            failure_count=failure_count,
            results=item_results,
            client_requested_at=client_requested_at,
            client_completed_at=datetime.now(tz=UTC),
            attributes={"protocol": "iec104"},
        )

    @staticmethod
    def _resolve_ioa(item: SourceWriteItemData) -> int | None:
        """将 node_id（IOA 字符串）转换为整数。"""
        node_id = item.node_id.strip()
        if node_id.isdigit() or (node_id.startswith("-") and node_id[1:].isdigit()):
            return int(node_id)
        return None

    @staticmethod
    def _resolve_command_type(item: SourceWriteItemData) -> str | None:
        """将 value_type 映射到 IEC 104 命令类型。按点位类型选择对应的 ASDU 类型标识。"""
        vt = item.value_type.strip().upper()
        # Direct command type specification
        if vt in ("C_SC_NA_1", "C_SE_NC_1"):
            return vt
        # Value type mapping
        if vt in ("BOOL", "BOOLEAN", "BIN", "BINARY"):
            return "C_SC_NA_1"
        if vt in ("FLOAT", "SHORT", "REAL", "DOUBLE"):
            return "C_SE_NC_1"
        # Default to single command for integer types
        if vt in ("INT", "INT16", "INT32", "UINT16", "UINT32"):
            return "C_SC_NA_1"
        return None

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
