"""Modbus RTU source 采集适配器。

实现 SourceAcquisitionPort，通过 shared/source/modbus_rtu 生产级
serial backend 执行 Modbus RTU 采集（FC03 读取 holding register）。

职责边界：
- 负责采集 DTO 与 Modbus RTU reader 调用之间的转换；
- 不负责 Modbus RTU 串行通信细节——由 whale.shared.source.modbus_rtu 处理；
- 不负责缓存、重试、授权——由上层 decorator 链处理；
- 不负责写入（write/control）——当前 NOT_IMPLEMENTED。

连接参数映射：
- serial_port: connection.host 或 connection.params["serial_port"];
- baudrate: connection.params["baudrate"]（默认 9600）;
- parity: connection.params["parity"]（'N'/'E'/'O'，默认 'N'）;
- stop_bits: connection.params["stop_bits"]（1 或 2，默认 1）;
- data_bits: connection.params["data_bits"]（7 或 8，默认 8）;
- unit_id: connection.params["modbus_unit_id"]（默认 1）.

Write 状态：NOT_IMPLEMENTED。仅实现 SourceAcquisitionPort。
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from whale.ingest.ports.source.source_acquisition_port import (
    SourceAcquisitionPort,
    SourceBatchMismatchError,
    SourceReadError,
    SourceReadTimeoutError,
    SourceSubscriptionHandle,
    SourceSubscriptionUnsupportedError,
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
from whale.shared.source.modbus_rtu.backends import RawModbusRtuReadResult
from whale.shared.source.modbus_rtu.reader import ModbusRtuSourceReader
from whale.shared.utils.time import ensure_utc


class ModbusRtuSourceAcquisitionAdapter(SourceAcquisitionPort):
    """通过 ModbusRtuSourceReader 执行 Modbus RTU 串行读取（FC03）。

    从 connection.params 提取串口参数（serial_port、baudrate、
    parity、stop_bits、data_bits），构造 ModbusRtuSourceReader，
    执行 holding register 批量读取，将原始结果转换为
    AcquiredNodeStateBatch 供 ingest 缓存使用。
    """

    def supports_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> bool:
        """查询当前适配器是否支持订阅模式。Modbus RTU 不支持订阅。"""
        del execution, connection
        return False

    async def read(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> AcquiredNodeStateBatch:
        """执行一次 Modbus RTU 批量读取（FC03）。

        对批量 holding register 地址发送读取请求并聚合返回值。

        Args:
            execution: 采集执行选项。
            connection: 目标源连接（host 字段为串口路径，或从 params 提取）。
            items: 待读取点位列表，每个 relative_path 为寄存器地址字符串。

        Returns:
            供 ingest 状态缓存使用的批量对象。

        Raises:
            SourceReadTimeoutError: 底层读取超时。
            SourceBatchMismatchError: 返回值数量与 item 数量不匹配。
            SourceReadError: 其他读取失败。
        """
        addresses = self._resolve_reg_addrs(connection, items)
        client_received_at = datetime.now(tz=UTC)

        try:
            async with self._build_reader(execution, connection) as reader:
                plan = reader.prepare_read(addresses)
                raw = await reader.read_prepared(plan)
        except asyncio.TimeoutError as exc:
            raise SourceReadTimeoutError("modbus rtu read timed out") from exc
        except OSError as exc:
            raise SourceReadError(f"serial_port_error: {exc}") from exc
        except ValueError as exc:
            raise SourceReadError(f"serial_param_error: {exc}") from exc
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
        """启动订阅。Modbus RTU 不支持订阅采集。"""
        del execution, connection, items, state_received
        raise SourceSubscriptionUnsupportedError(
            "subscription acquisition is not supported by Modbus RTU adapter"
        )

    @staticmethod
    def _resolve_reg_addrs(
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> list[int]:
        """将业务 relative_path 转换为整数寄存器地址。

        Args:
            connection: 源连接（未直接使用，保留用于未来扩展）。
            items: 采集点位列表。

        Returns:
            整数寄存器地址列表。

        Raises:
            ValueError: 地址格式无法解析或列表为空。
        """
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
                    f"Cannot resolve Modbus RTU register address from "
                    f"relative_path={path!r} for item key={item.key}"
                )
        if not reg_addrs:
            raise ValueError(
                "Cannot resolve Modbus RTU register addresses (empty items)."
            )
        return reg_addrs

    @classmethod
    def _build_reader(
        cls,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> ModbusRtuSourceReader:
        """构造 shared/source Modbus RTU 读取器。

        从 connection 提取串口参数：
        - serial_port: connection.host（或 connection.params["serial_port"]）
        - baudrate: 默认 9600
        - parity: 默认 'N'
        - stop_bits: 默认 1
        - data_bits: 默认 8
        - unit_id: 默认 1

        Args:
            execution: 采集执行选项。
            connection: 目标源连接。

        Returns:
            配置好的 ModbusRtuSourceReader 实例。

        Raises:
            ValueError: 串口路径为空。
        """
        # 串口路径：优先使用 connection.host，否则从 params 提取
        serial_port = connection.host.strip()
        if not serial_port:
            serial_port = str(connection.params.get("serial_port", "")).strip()
        if not serial_port:
            raise ValueError("connection.host (serial_port) is required for Modbus RTU")

        baudrate = int(connection.params.get("baudrate", 9600))
        parity = str(connection.params.get("parity", "N")).upper()
        stop_bits = int(connection.params.get("stop_bits", 1))
        data_bits = int(connection.params.get("data_bits", 8))
        unit_id = int(connection.params.get("modbus_unit_id", 1))

        return ModbusRtuSourceReader(
            serial_port=serial_port,
            baudrate=baudrate,
            parity=parity,
            stop_bits=stop_bits,
            data_bits=data_bits,
            unit_id=unit_id,
        )

    @staticmethod
    def _to_acquired_batch_from_raw(
        *,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
        addresses: list[int],
        raw: RawModbusRtuReadResult,
        client_received_at: datetime,
        client_processed_at: datetime,
    ) -> AcquiredNodeStateBatch:
        """将原始 Modbus RTU 读取结果转换为 AcquiredNodeStateBatch。

        Args:
            connection: 源连接信息。
            items: 请求的采集点位。
            addresses: 寄存器地址列表。
            raw: 原始读取结果。
            client_received_at: 客户端接收时间戳。
            client_processed_at: 客户端处理完成时间戳。

        Returns:
            ingest 兼容的批量状态对象。

        Raises:
            SourceBatchMismatchError: 返回值数量不匹配。
            SourceReadError: 读取失败。
        """
        if not raw.ok:
            reason = raw.error_reason or raw.exception or "raw_read_failed"
            raise SourceReadError(f"raw read failed: {reason}")
        if len(raw.values) != len(items):
            raise SourceBatchMismatchError(
                f"raw value count {len(raw.values)} does not match "
                f"item count {len(items)}"
            )

        batch_observed_at = ensure_utc(
            raw.response_timestamp or client_received_at
        )
        values = [
            ModbusRtuSourceAcquisitionAdapter._to_acquired_value(
                item=item,
                address=address,
                raw_value=raw_value,
                raw=raw,
            )
            for item, address, raw_value in zip(
                items, addresses, raw.values, strict=True
            )
        ]

        source_id = (
            connection.ld_name.strip()
            or connection.ied_name.strip()
            or "modbus_rtu_source"
        )
        return AcquiredNodeStateBatch(
            source_id=source_id,
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
        raw: RawModbusRtuReadResult,
    ) -> AcquiredNodeValue:
        """将单个寄存器的原始值转换为 AcquiredNodeValue。

        Args:
            item: 采集点位。
            address: 寄存器地址。
            raw_value: 原始整数值。
            raw: 完整原始结果（用于错误上下文）。

        Returns:
            单个点位的采集值对象。
        """
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
            server_timestamp=(
                ensure_utc(raw.response_timestamp)
                if raw.response_timestamp
                else None
            ),
            client_sequence=None,
            attributes=attributes,
        )
