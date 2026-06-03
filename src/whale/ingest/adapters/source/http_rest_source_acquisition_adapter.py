"""HTTP REST source 采集适配器。

实现 SourceAcquisitionPort，通过 shared/source/http_rest 生产级 client backend
执行 HTTP GET 请求并将响应解析为节点状态。

职责边界：
- 负责采集 DTO 与 HTTP client 调用之间的转换；
- 不负责 HTTP 协议细节——由 whale.shared.source.http_rest.client 处理；
- 不负责缓存、重试、授权——由上层 decorator 链处理；
- 不负责写入（HTTP POST/PUT/DELETE）——当前 NOT_IMPLEMENTED。

采集模式：
- 支持 polling read：对每个 item 发起 HTTP GET 请求；
- 支持 JSON path 提取：通过 jp (JSONPath) 从响应中提取值；
- 不实现 subscription 模式。

Write 状态：NOT_IMPLEMENTED。仅实现 SourceAcquisitionPort，不实现 SourceWritePort。
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from whale.ingest.ports.source.source_acquisition_port import (
    SourceAcquisitionPort,
    SourceReadError,
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
from whale.shared.source.http_rest.client import HttpRestClientBackend, HttpResponseData
from whale.shared.utils.time import ensure_utc


class HttpRestSourceAcquisitionAdapter(SourceAcquisitionPort):
    """通过 HttpRestClientBackend 采集 HTTP REST 端点数据。

    对每个 item 执行 HTTP GET 请求，从响应中提取值。
    支持 JSON Path 提取：当 item 的 relative_path 以 "$." 开头时，
    执行 JSON Path 提取；否则使用整个响应体作为值。
    """

    def supports_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> bool:
        """HTTP REST 为 polling 协议，不支持订阅模式。"""
        del execution, connection
        return False

    async def read(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> AcquiredNodeStateBatch:
        """执行 HTTP GET 请求并采集响应数据。

        对每个 item 发起独立的 HTTP GET 请求（支持 JSON Path 提取）。
        所有请求共享同一个 client backend 实例。

        Args:
            execution: 采集执行选项。
            connection: 目标 HTTP 端点连接信息。
            items: 采集点位（每个 item 的 relative_path 指定请求路径或 JSON Path）。

        Returns:
            AcquiredNodeStateBatch 包含各节点的 HTTP 响应值。

        Raises:
            SourceReadError: HTTP 请求或响应解析失败。
        """
        host = connection.host.strip()
        if not host:
            raise SourceReadError("connection.host is required for HTTP REST")
        if connection.port <= 0:
            raise SourceReadError("connection.port must be > 0 for HTTP REST")

        base_url_raw = connection.params.get("base_url", "")
        base_url = str(base_url_raw) if base_url_raw else ""
        if not base_url:
            scheme_raw = connection.params.get("scheme", "http")
            scheme = str(scheme_raw)
            base_url = f"{scheme}://{host}:{connection.port}"

        client_received_at = datetime.now(tz=UTC)

        client = HttpRestClientBackend(
            base_url=base_url,
            timeout_seconds=15.0,
            default_headers=(
                {"Accept": "application/json"}
            ),
        )

        try:
            values: list[AcquiredNodeValue] = []
            for item in items:
                path, json_path = self._parse_relative_path(item.relative_path)
                result = await client.get(path=path)

                if result.ok:
                    extracted = self._extract_value(result, json_path)
                    values.append(
                        AcquiredNodeValue(
                            node_key=item.key,
                            value=extracted,
                            quality="GOOD",
                            source_timestamp=None,
                            server_timestamp=ensure_utc(result.response_at),
                            client_sequence=None,
                            attributes={
                                "profile_item_id": item.profile_item_id,
                                "relative_path": item.relative_path,
                                "http_status": str(result.status_code),
                                "http_path": path,
                            },
                        )
                    )
                else:
                    values.append(
                        AcquiredNodeValue(
                            node_key=item.key,
                            value="",
                            quality="BAD",
                            source_timestamp=None,
                            server_timestamp=None,
                            client_sequence=None,
                            attributes={
                                "profile_item_id": item.profile_item_id,
                                "relative_path": item.relative_path,
                                "http_error": result.error_reason or "unknown",
                            },
                        )
                    )

            client_processed_at = datetime.now(tz=UTC)
            return AcquiredNodeStateBatch(
                source_id=connection.ld_name.strip() or "http_rest_source",
                batch_observed_at=client_processed_at,
                client_received_at=ensure_utc(client_received_at),
                client_processed_at=ensure_utc(client_processed_at),
                values=values,
                availability_status="VALID",
                attributes={"acquisition_kind": "polling"},
            )
        except Exception as exc:
            raise SourceReadError(str(exc) or type(exc).__name__) from exc

    async def start_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
        *,
        state_received: SubscriptionStateHandler,
    ) -> SourceSubscriptionHandle:
        """HTTP REST 当前不支持持久订阅采集。"""
        del execution, connection, items, state_received
        raise SourceSubscriptionUnsupportedError(
            "HTTP REST persistent subscription is not supported. Use read() for polling acquisition."
        )

    @staticmethod
    def _parse_relative_path(relative_path: str) -> tuple[str, str | None]:
        """解析 relative_path 中的路径和可选的 JSON Path。

        格式：``/api/endpoint`` 或 ``/api/endpoint#$.data.value``。

        Args:
            relative_path: item 的 relative_path 字符串。

        Returns:
            (http_path, json_path) 元组，json_path 可为 None。
        """
        if "#" in relative_path:
            http_path, _, json_path = relative_path.partition("#")
            return http_path.strip() or "/", json_path.strip() or None
        return relative_path.strip() or "/", None

    @staticmethod
    def _resolve_json_path(data: Any, path: str) -> Any:
        """从 JSON 数据中提取指定路径的值。

        支持简单 JSON Path 语法：``$.key.subkey`` 和 ``$[0].key``。

        Args:
            data: 已解析的 JSON 数据（dict 或 list）。
            path: JSON Path 字符串（如 ``$.data.temperature``）。

        Returns:
            提取到的值，若路径无效则返回 None。
        """
        if not path.startswith("$"):
            return data
        segments = path[1:].lstrip(".")
        if not segments:
            return data

        current = data
        for segment in segments.split("."):
            if current is None:
                return None
            # Handle array index like key[0]
            if "[" in segment and segment.endswith("]"):
                key, _, idx_str = segment.partition("[")
                idx = int(idx_str.rstrip("]"))
                if isinstance(current, dict):
                    current = current.get(key) if key else current
                if isinstance(current, list) and idx < len(current):
                    current = current[idx]
                else:
                    return None
            elif isinstance(current, dict):
                current = current.get(segment)
            elif isinstance(current, list) and segment.isdigit():
                idx = int(segment)
                current = current[idx] if idx < len(current) else None
            else:
                return None
        return current

    @staticmethod
    def _extract_value(
        response: HttpResponseData, json_path: str | None
    ) -> str:
        """从 HTTP 响应中提取值。

        Args:
            response: HTTP 响应数据。
            json_path: 可选的 JSON Path 用于提取。

        Returns:
            提取的字符串值。
        """
        if json_path and response.json_body is not None:
            extracted = HttpRestSourceAcquisitionAdapter._resolve_json_path(
                response.json_body, json_path
            )
            if extracted is not None:
                if isinstance(extracted, (dict, list)):
                    import json as _json

                    return _json.dumps(extracted)
                return str(extracted)
        return response.body
