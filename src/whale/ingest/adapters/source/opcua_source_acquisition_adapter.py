"""OPC UA source 采集适配器。

本模块负责把 ingest DTO 转换为 shared/source 的 open62541 raw reader 调用，
并将 `RawOpcUaReadResult` 转换为 `AcquiredNodeStateBatch`。

当前完成情况：
- polling / read-once 已构成生产闭环；
- subscription 当前只暴露能力边界和 fail-fast 行为；
- 真实 subscription reconnect loop 尚未实现。
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
from whale.shared.source.models import SourceConnectionProfile
from whale.shared.source.opcua.backends import RawDataValue, RawOpcUaReadResult
from whale.shared.source.opcua.reader import OpcUaSourceReader
from whale.shared.utils.time import ensure_utc


class OpcUaSourceAcquisitionAdapter(SourceAcquisitionPort):
    """执行基于 open62541 raw reader 的 OPC UA 读取。"""

    def supports_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> bool:
        """返回当前 open62541 raw reader 是否支持订阅。"""

        del execution, connection
        return False

    async def read(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> AcquiredNodeStateBatch:
        """执行一次 OPC UA 批量读取。

        Args:
            execution: 本次采集执行选项。
            connection: 一个 source 连接。
            items: 本连接需要读取的点位列表。

        Returns:
            一个可直接写入 ingest 状态缓存的批次对象。

        Raises:
            SourceReadTimeoutError: 当底层读取超时。
            SourceBatchMismatchError: 当返回值数量与点位数量不一致。
            SourceReadError: 其他读取失败。
        """

        addresses = self._resolve_node_paths(connection, items)
        client_received_at = datetime.now(tz=UTC)

        try:
            async with self._build_reader(execution, connection) as reader:
                plan = reader.prepare_read(addresses)
                raw = await reader.read_prepared_raw(plan)
        except asyncio.TimeoutError as exc:
            raise SourceReadTimeoutError("source read timed out") from exc
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
        """拒绝当前不受支持的订阅模式。

        Args:
            execution: 本次采集执行选项。
            connection: 一个 source 连接。
            items: 本连接订阅点位列表。
            state_received: 订阅回调。

        Raises:
            SourceSubscriptionUnsupportedError: 当前 shared reader 不支持订阅。
        """

        del execution, connection, items, state_received
        raise SourceSubscriptionUnsupportedError(
            "subscription acquisition is not supported by current source reader"
        )

    @staticmethod
    def _resolve_node_paths(
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> list[str]:
        """将业务点位 relative_path 转换为 OPC UA 地址。"""

        namespace_uri = connection.namespace_uri.strip() if connection.namespace_uri else ""
        node_paths: list[str] = []

        for item in items:
            relative_path = item.relative_path.strip()
            if relative_path.startswith(("ns=", "nsu=", "s=")):
                node_paths.append(relative_path)
                continue

            if namespace_uri:
                node_paths.append(f"nsu={namespace_uri};s={relative_path}")
            else:
                node_paths.append(f"s={relative_path}")

        if not node_paths:
            raise ValueError("Cannot resolve OPC UA node paths.")

        return node_paths

    @classmethod
    def _build_reader(
        cls,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> OpcUaSourceReader:
        """构造 shared/source OPC UA reader。"""

        return OpcUaSourceReader(cls._build_connection_profile(execution, connection))

    @staticmethod
    def _build_connection_profile(
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> SourceConnectionProfile:
        """构造共享 reader 使用的连接 profile。"""

        endpoint = _build_endpoint(execution, connection)
        if not endpoint:
            raise ValueError("Cannot resolve OPC UA endpoint.")

        params: dict[str, str | int | float | bool | None] = {
            **connection.params,
            **execution.params,
        }
        if execution.client_backend is not None:
            params["client_backend"] = execution.client_backend

        return SourceConnectionProfile(
            endpoint=endpoint,
            namespace_uri=_resolve_namespace_uri(connection),
            timeout_seconds=execution.request_timeout_ms / 1000,
            params=params,
        )

    @staticmethod
    def _to_acquired_batch_from_raw(
        *,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
        addresses: list[str],
        raw: RawOpcUaReadResult,
        client_received_at: datetime,
        client_processed_at: datetime,
    ) -> AcquiredNodeStateBatch:
        """将 raw read 结果转换为 ingest 批次。"""

        if not raw.ok:
            reason = raw.error_reason or raw.exception or "raw_read_failed"
            raise SourceReadError(f"raw read failed: {reason}")
        if len(raw.data_values) != len(items):
            raise SourceBatchMismatchError(
                f"raw value count {len(raw.data_values)} does not match item count {len(items)}"
            )

        batch_observed_at = ensure_utc(raw.response_timestamp or client_received_at)
        values = [
            OpcUaSourceAcquisitionAdapter._to_acquired_value(
                item=item,
                address=address,
                raw_value=raw_value,
                raw=raw,
            )
            for item, address, raw_value in zip(items, addresses, raw.data_values, strict=True)
        ]

        return AcquiredNodeStateBatch(
            source_id=_resolve_source_id(connection),
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
        address: str,
        raw_value: object,
        raw: RawOpcUaReadResult,
    ) -> AcquiredNodeValue:
        """将一个 raw DataValue 转换为 ingest 点位值。"""

        normalized = raw_value if isinstance(raw_value, RawDataValue) else RawDataValue(value=raw_value)
        raw_error_reason = raw.error_reason or raw.exception
        quality = normalized.status_code or ("GOOD" if raw.ok else raw_error_reason)
        server_timestamp = normalized.server_timestamp or raw.response_timestamp

        attributes: dict[str, object] = {
            "profile_item_id": item.profile_item_id,
            "relative_path": item.relative_path,
            "protocol_address": address,
        }
        if raw_error_reason:
            attributes["raw_error_reason"] = raw_error_reason

        return AcquiredNodeValue(
            node_key=item.key,
            value=str(normalized.value),
            quality=quality,
            source_timestamp=(
                ensure_utc(normalized.source_timestamp)
                if normalized.source_timestamp is not None
                else None
            ),
            server_timestamp=(
                ensure_utc(server_timestamp) if server_timestamp is not None else None
            ),
            client_sequence=None,
            attributes=attributes,
        )


def _resolve_namespace_uri(connection: SourceConnectionData) -> str | None:
    """解析 namespace_uri。"""

    if connection.namespace_uri.strip():
        return connection.namespace_uri.strip()
    return None


def _build_endpoint(
    execution: AcquisitionExecutionOptions,
    connection: SourceConnectionData,
) -> str:
    """构造 OPC UA endpoint。"""

    protocol = execution.protocol.strip().lower()
    transport = execution.transport.strip().lower()
    host = connection.host.strip()
    port = connection.port

    if not protocol or not transport or not host or port <= 0:
        return ""

    scheme = "opc.tcp" if protocol == "opcua" and transport == "tcp" else f"{protocol}.{transport}"
    return f"{scheme}://{host}:{port}"


def _resolve_source_id(connection: SourceConnectionData) -> str:
    """解析 source_id。"""

    if connection.ld_name.strip():
        return connection.ld_name.strip()
    if connection.ied_name.strip():
        return connection.ied_name.strip()
    return "unknown_source"
