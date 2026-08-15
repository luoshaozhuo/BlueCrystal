"""协议采集适配器。

实现 SourceAcquisitionPort / SourceWritePort，
封装特定协议（工业协议）的采集或写入逻辑。
外部依赖边界：libiec61850 C 库（ctypes）。
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
from pacific.whale.shared.source.iec61850.backends import RawMmsReadResult
from pacific.whale.shared.source.iec61850.reader import Iec61850MmsSourceReader
from pacific.whale.shared.utils.time import ensure_utc


class Iec61850MmsSourceAcquisitionAdapter(SourceAcquisitionPort):
    """通过 libiec61850 native runner 执行 IEC 61850 MMS 读取。"""

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
        """执行一次 IEC 61850 MMS 批量读取。对批量点位集合逐一发送 MMS Read 请求并聚合返回值。
        Each item's ``relative_path`` is the MMS object reference.
        The functional constraint is read from ``connection.params["fc"]``
        or defaults to "NONE".
        Args:
            execution: Acquisition execution options.
            connection: Target source connection.
            items: Points to read, each with relative_path = obj_ref.
        Returns:
            A batch object for ingest state cache.
        Raises:
            SourceReadTimeoutError: When underlying read times out.
            SourceBatchMismatchError: When value count != item count.
            SourceReadError: Other read failures.
        """
        addresses = self._resolve_obj_refs(connection, items)
        fc = self._resolve_fc(connection)
        client_received_at = datetime.now(tz=UTC)

        try:
            async with self._build_reader(execution, connection) as reader:
                raw_results: list[RawMmsReadResult] = []
                for obj_ref in addresses:
                    raw = await reader.read(
                        obj_ref=obj_ref,
                        fc=fc,
                        request_id=f"{execution.protocol}_{connection.ied_name}",
                    )
                    raw_results.append(raw)
        except asyncio.TimeoutError as exc:
            raise SourceReadTimeoutError("iec61850 mms read timed out") from exc
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
            raw_results=raw_results,
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
            "subscription acquisition is not supported by IEC 61850 MMS adapter"
        )

    @staticmethod
    def _resolve_obj_refs(
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> list[str]:
        """将业务 relative_path 转换为 MMS 对象引用。"""
        del connection
        obj_refs: list[str] = []
        for item in items:
            path = item.relative_path.strip()
            if not path:
                raise ValueError(
                    f"Empty relative_path for item key={item.key}"
                )
            obj_refs.append(path)
        if not obj_refs:
            raise ValueError("Cannot resolve MMS object references (empty items).")
        return obj_refs

    @staticmethod
    def _resolve_fc(connection: SourceConnectionData) -> str:
        """从连接参数解析功能约束。"""
        fc = connection.params.get("fc", "NONE")
        if isinstance(fc, str):
            return fc.strip().upper()
        return "NONE"

    @classmethod
    def _build_reader(
        cls,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> Iec61850MmsSourceReader:
        """构造 shared/source IEC 61850 MMS 读取器。"""
        host = connection.host.strip()
        if not host:
            raise ValueError("connection.host is required")
        if connection.port <= 0:
            raise ValueError("connection.port must be > 0")
        timeout_s = max(execution.request_timeout_ms / 1000, 2.0)
        return Iec61850MmsSourceReader(
            host=host,
            port=connection.port,
            timeout_seconds=timeout_s,
        )

    @staticmethod
    def _to_acquired_batch_from_raw(
        *,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
        addresses: list[str],
        raw_results: list[RawMmsReadResult],
        client_received_at: datetime,
        client_processed_at: datetime,
    ) -> AcquiredNodeStateBatch:
        """将原始 MMS 读取结果转换为 ingest 批次。"""
        if len(raw_results) != len(items):
            raise SourceBatchMismatchError(
                f"raw result count {len(raw_results)} does not match item count {len(items)}"
            )

        values: list[AcquiredNodeValue] = []
        for item, obj_ref, raw in zip(items, addresses, raw_results, strict=True):
            if not raw.ok:
                reason = raw.error_reason or raw.exception or "raw_read_failed"
                raise SourceReadError(
                    f"raw read failed for {obj_ref}: {reason}"
                )

            values.append(
                Iec61850MmsSourceAcquisitionAdapter._to_acquired_value(
                    item=item,
                    obj_ref=obj_ref,
                    raw=raw,
                )
            )

        return AcquiredNodeStateBatch(
            source_id=connection.ld_name.strip() or connection.ied_name.strip() or "iec61850_mms_source",
            batch_observed_at=ensure_utc(client_received_at),
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
        obj_ref: str,
        raw: RawMmsReadResult,
    ) -> AcquiredNodeValue:
        attributes: dict[str, object] = {
            "profile_item_id": item.profile_item_id,
            "relative_path": item.relative_path,
            "protocol_address": obj_ref,
        }
        if raw.value_type:
            attributes["mms_value_type"] = raw.value_type

        return AcquiredNodeValue(
            node_key=item.key,
            value=raw.value or "",
            quality="GOOD" if raw.ok else (raw.error_reason or "UNKNOWN"),
            source_timestamp=None,
            server_timestamp=None,
            client_sequence=None,
            attributes=attributes,
        )
