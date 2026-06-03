"""IEC 101 source 采集适配器。

实现 SourceAcquisitionPort，通过 shared/source/iec101 生产级
serial backend 执行 IEC 101 interrogation（总召唤）采集。

职责边界：
- 负责采集 DTO 与 IEC 101 reader 调用之间的转换；
- 不负责 IEC 101 串行通信细节——由 whale.shared.source.iec101 处理；
- 不负责缓存、重试、授权——由上层 decorator 链处理；
- 不负责写入（write/control）——当前 NOT_IMPLEMENTED。

连接参数映射：
- serial_port: connection.host 或 connection.params["serial_port"];
- baudrate: connection.params["baudrate"]（默认 9600）;
- parity: connection.params["parity"]（'E' 为 IEC101 标准，默认 'E'）;
- stop_bits: connection.params["stop_bits"]（默认 1）;
- data_bits: connection.params["data_bits"]（默认 8）;
- link_address: connection.params["link_address"]（默认 1）;
- common_address: connection.params["common_address"]（默认 1）.

Write 状态：NOT_IMPLEMENTED。仅实现 SourceAcquisitionPort。
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from whale.ingest.ports.source.source_acquisition_port import (
    SourceAcquisitionPort,
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
from whale.shared.source.iec101.backends import RawIec101ReadResult
from whale.shared.source.iec101.reader import Iec101SourceReader
from whale.shared.utils.time import ensure_utc


class Iec101SourceAcquisitionAdapter(SourceAcquisitionPort):
    """通过 Iec101SourceReader 执行 IEC 101 interrogation（总召唤）读取。

    从 connection.params 提取串口参数（serial_port、baudrate、
    parity、stop_bits、data_bits、link_address、common_address），
    构造 Iec101SourceReader，执行 interrogation 流程，
    将原始结果转换为 AcquiredNodeStateBatch 供 ingest 缓存使用。

    IEC 101 通过串行链路进行周期性 interrogation（总召唤）读取，
    不支持传统 subscription 模式。
    """

    def supports_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> bool:
        """查询当前适配器是否支持订阅模式。

        IEC 101 的 interrogation 为 polling 模式，
        不支持传统 subscription。
        """
        del execution, connection
        return False

    async def read(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> AcquiredNodeStateBatch:
        """执行一次 IEC 101 interrogation（总召唤）读取。

        发送 C_IC_NA_1 激活命令，收集返回的 ASDU 数据后停止。

        Args:
            execution: 采集执行选项。
            connection: 目标源连接（host 为串口路径或从 params 提取）。
            items: 待读取点位列表，每个 relative_path 为 IOA 字符串。

        Returns:
            供 ingest 状态缓存使用的批量对象。

        Raises:
            SourceReadTimeoutError: 底层读取超时。
            SourceReadError: 其他读取失败。
        """
        ioa_list = self._resolve_ioa_list(connection, items)
        client_received_at = datetime.now(tz=UTC)

        try:
            async with self._build_reader(execution, connection) as reader:
                raw = await reader.read(ioa_list)
        except asyncio.TimeoutError as exc:
            raise SourceReadTimeoutError("iec101 interrogation timed out") from exc
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
            ioa_list=ioa_list,
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
        """启动订阅。IEC 101 不支持传统 subscription 采集。"""
        del execution, connection, items, state_received
        raise SourceSubscriptionUnsupportedError(
            "subscription acquisition is not supported by IEC 101 adapter"
        )

    @staticmethod
    def _resolve_ioa_list(
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> list[int]:
        """将业务 relative_path 转换为整数 IOA 值。

        Args:
            connection: 源连接（未直接使用）。
            items: 采集点位列表。

        Returns:
            整数 IOA 列表。

        Raises:
            ValueError: IOA 格式无法解析或列表为空。
        """
        del connection
        ioa_list: list[int] = []
        for item in items:
            path = item.relative_path.strip()
            if path.isdigit() or (path.startswith("-") and path[1:].isdigit()):
                ioa_list.append(int(path))
            else:
                raise ValueError(
                    f"Cannot resolve IEC 101 IOA from "
                    f"relative_path={path!r} for item key={item.key}"
                )
        if not ioa_list:
            raise ValueError("Cannot resolve IEC 101 IOA list (empty items).")
        return ioa_list

    @staticmethod
    def _build_reader(
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> Iec101SourceReader:
        """构造 shared/source IEC 101 读取器。

        从 connection 提取串口参数：
        - serial_port: connection.host（或 params["serial_port"]）
        - baudrate: 默认 9600
        - parity: 默认 'E'（IEC 101 标准偶校验）
        - stop_bits: 默认 1
        - data_bits: 默认 8
        - link_address: 默认 1
        - common_address: 默认 1

        Args:
            execution: 采集执行选项。
            connection: 目标源连接。

        Returns:
            配置好的 Iec101SourceReader 实例。

        Raises:
            ValueError: 串口路径为空。
        """
        serial_port = connection.host.strip()
        if not serial_port:
            serial_port = str(
                connection.params.get("serial_port", "")
            ).strip()
        if not serial_port:
            raise ValueError(
                "connection.host (serial_port) is required for IEC 101"
            )

        baudrate = int(connection.params.get("baudrate", 9600))
        parity = str(connection.params.get("parity", "E")).upper()
        stop_bits = int(connection.params.get("stop_bits", 1))
        data_bits = int(connection.params.get("data_bits", 8))
        link_address = int(connection.params.get("link_address", 1))
        common_address = int(
            connection.params.get("common_address", 1)
        )

        return Iec101SourceReader(
            serial_port=serial_port,
            baudrate=baudrate,
            parity=parity,
            stop_bits=stop_bits,
            data_bits=data_bits,
            link_address=link_address,
            common_address=common_address,
        )

    @staticmethod
    def _to_acquired_batch_from_raw(
        *,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
        ioa_list: list[int],
        raw: RawIec101ReadResult,
        client_received_at: datetime,
        client_processed_at: datetime,
    ) -> AcquiredNodeStateBatch:
        """将原始 IEC 101 读取结果转换为 AcquiredNodeStateBatch。

        Args:
            connection: 源连接信息。
            items: 请求的采集点位。
            ioa_list: IOA 列表。
            raw: 原始读取结果。
            client_received_at: 客户端接收时间戳。
            client_processed_at: 客户端处理完成时间戳。

        Returns:
            ingest 兼容的批量状态对象。

        Raises:
            SourceReadError: 读取失败。
        """
        if not raw.ok:
            reason = raw.error_reason or raw.exception or "raw_read_failed"
            raise SourceReadError(f"raw read failed: {reason}")

        values: list[AcquiredNodeValue] = []
        for item, ioa in zip(items, ioa_list, strict=True):
            raw_entry = raw.values.get(ioa)
            if raw_entry is None:
                values.append(
                    AcquiredNodeValue(
                        node_key=item.key,
                        value="",
                        quality="UNKNOWN",
                        source_timestamp=None,
                        server_timestamp=(
                            ensure_utc(raw.response_timestamp)
                            if raw.response_timestamp
                            else None
                        ),
                        client_sequence=None,
                        attributes={
                            "profile_item_id": item.profile_item_id,
                            "relative_path": item.relative_path,
                            "protocol_address": str(ioa),
                            "warning": "ioa_not_found_in_response",
                        },
                    )
                )
            else:
                type_tag, value_str = raw_entry
                values.append(
                    AcquiredNodeValue(
                        node_key=item.key,
                        value=value_str,
                        quality="GOOD",
                        source_timestamp=None,
                        server_timestamp=(
                            ensure_utc(raw.response_timestamp)
                            if raw.response_timestamp
                            else None
                        ),
                        client_sequence=None,
                        attributes={
                            "profile_item_id": item.profile_item_id,
                            "relative_path": item.relative_path,
                            "protocol_address": str(ioa),
                            "iec101_type": type_tag,
                        },
                    )
                )

        source_id = (
            connection.ld_name.strip()
            or connection.ied_name.strip()
            or "iec101_source"
        )
        return AcquiredNodeStateBatch(
            source_id=source_id,
            batch_observed_at=ensure_utc(
                raw.response_timestamp or client_received_at
            ),
            client_received_at=ensure_utc(client_received_at),
            client_processed_at=ensure_utc(client_processed_at),
            values=values,
            availability_status="VALID",
            attributes={"acquisition_kind": "read"},
        )
