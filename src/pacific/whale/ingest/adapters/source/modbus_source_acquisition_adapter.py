"""协议采集适配器。

实现 SourceAcquisitionPort / SourceWritePort，
封装特定协议（工业协议）的采集或写入逻辑。
外部依赖边界：libmodbus C 库（ctypes）。
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from pacific.whale.ingest.ports.source.source_acquisition_port import (
    SourceAcquisitionPort,
    SourceBatchMismatchError,
    SourceReadError,
    SourceReadTimeoutError,
    SourceSubscriptionHandle,
    SourceSubscriptionUnsupportedError,
    SubscriptionStateHandler,
)
from pacific.whale.ingest.usecases.dtos.acquired_node_state import (
    AcquiredNodeStateBatch,
    AcquiredNodeValue,
)
from pacific.whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
)
from pacific.whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from pacific.whale.shared.source.modbus.backends import RawModbusReadResult
from pacific.whale.shared.source.modbus.reader import ModbusSourceReader
from pacific.whale.shared.utils.time import ensure_utc


class ModbusSourceAcquisitionAdapter(SourceAcquisitionPort):
    """通过 native runner 执行 Modbus TCP 读取（FC03 保持寄存器）。"""

    def supports_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        
        connection: SourceConnectionData,
    ) -> bool:
        """查询当前适配器是否支持订阅模式。返回布尔值。"""
        del execution, connection
        return False

    async def read(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> AcquiredNodeStateBatch:
        """执行一次 Modbus TCP 批量读取（功能码 03）。对批量 holding register 地址发送读取请求并聚合返回值。
        Args:
            execution: Acquisition execution options.
            connection: Target source connection.
            items: Points to read, each with ``relative_path`` as register address string.
        Returns:
            A batch object for ingest state cache.
        Raises:
            SourceReadTimeoutError: When underlying read times out.
            SourceBatchMismatchError: When value count != item count.
            SourceReadError: Other read failures.
        """
        addresses = self._resolve_reg_addrs(connection, items)
        client_received_at = datetime.now(tz=UTC)

        try:
            async with self._build_reader(execution, connection) as reader:
                plan = reader.prepare_read(addresses)
                raw = await reader.read_prepared(plan)
        except asyncio.TimeoutError as exc:
            raise SourceReadTimeoutError("modbus read timed out") from exc
        except FileNotFoundError as exc:
            raise SourceReadError("runner_not_available") from exc
        except RuntimeError as exc:
            message = str(exc)
            if "does not exist" in message:
                raise SourceReadError(f"runner_not_available: {message}") from exc
            raise SourceReadError(message) from exc
        except Exception as exc:
            raise SourceReadError(str(exc) or type(exc).__name__) from exc

        client_processed_at = datetime.now(tz=UTC)
        return self._to_acquired_batch_from_raw(
            connection=connection,
            items=items,
            addresses=addresses,
            raw=raw,
            client_received_at=client_received_at,
            client_processed_at=client_processed_at,
        )

    async def start_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
        *,
        state_received: SubscriptionStateHandler,
    ) -> SourceSubscriptionHandle:
        """启动订阅。建立与数据源的订阅连接并注册回调。"""
        del execution, connection, items, state_received
        raise SourceSubscriptionUnsupportedError(
            "subscription acquisition is not supported by Modbus TCP adapter"
        )

    @staticmethod
    def _resolve_reg_addrs(
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> list[int]:
        """将业务 relative_path 转换为整数寄存器地址。"""
        del connection
        reg_addrs: list[int] = []
        for item in items:
            path = item.relative_path.strip()
            if path.startswith("0x") or path.startswith("0X"):
                reg_addrs.append(int(path, 16))
            elif path.isdigit() or (path.startswith("-") and path[1:].isdigit()):
                reg_addrs.append(int(path))
            else:
                raise ValueError(
                    f"Cannot resolve Modbus register address from relative_path={path!r} "
                    f"for item key={item.key}"
                )
        if not reg_addrs:
            raise ValueError("Cannot resolve Modbus register addresses (empty items).")
        return reg_addrs

    @classmethod
    def _build_reader(
        cls,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> ModbusSourceReader:
        """构造 shared/source Modbus 读取器。"""
        host = connection.host.strip()
        if not host:
            raise ValueError("connection.host is required")
        if connection.port <= 0:
            raise ValueError("connection.port must be > 0")
        unit_id = int(connection.params.get("modbus_unit_id", 1))
        return ModbusSourceReader(host=host, port=connection.port, unit_id=unit_id)

    @staticmethod
    def _to_acquired_batch_from_raw(
        *,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
        addresses: list[int],
        raw: RawModbusReadResult,
        client_received_at: datetime,
        client_processed_at: datetime,
    ) -> AcquiredNodeStateBatch:
        if not raw.ok:
            reason = raw.error_reason or raw.exception or "raw_read_failed"
            raise SourceReadError(f"raw read failed: {reason}")
        if len(raw.values) != len(items):
            raise SourceBatchMismatchError(
                f"raw value count {len(raw.values)} does not match item count {len(items)}"
            )

        batch_observed_at = ensure_utc(raw.response_timestamp or client_received_at)
        values = [
            ModbusSourceAcquisitionAdapter._to_acquired_value(
                item=item,
                address=address,
                raw_value=raw_value,
                raw=raw,
            )
            for item, address, raw_value in zip(items, addresses, raw.values, strict=True)
        ]

        return AcquiredNodeStateBatch(
            source_id=connection.ld_name.strip() or connection.ied_name.strip() or "modbus_source",
            batch_observed_at=batch_observed_at,
            client_received_at=ensure_utc(client_received_at),
            client_processed_at=ensure_utc(client_processed_at),
            values=values,
            availability_status="VALID",
            attributes={"acquisition_kind": "read"},
        )

    @staticmethod
    def _to_acquired_value(
        *,
        item: AcquisitionItemData,
        address: int,
        raw_value: int,
        raw: RawModbusReadResult,
    ) -> AcquiredNodeValue:
        raw_error_reason = raw.error_reason or raw.exception
        attributes: dict[str, object] = {
            "profile_item_id": item.profile_item_id,
            "relative_path": item.relative_path,
            "protocol_address": str(address),
        }
        if raw_error_reason:
            attributes["raw_error_reason"] = raw_error_reason

        return AcquiredNodeValue(
            node_key=item.key,
            value=str(raw_value),
            quality="GOOD" if raw.ok else (raw_error_reason or "UNKNOWN"),
            source_timestamp=None,
            server_timestamp=ensure_utc(raw.response_timestamp) if raw.response_timestamp else None,
            client_sequence=None,
            attributes=attributes,
        )
