"""统一 source 采集 usecase。

本模块只负责请求校验与模式分发，不包含协议细节和状态缓存写入。
"""

from __future__ import annotations

from typing import cast

from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionItemData,
    SourceAcquisitionRequest,
)
from whale.ingest.usecases.dtos.source_acquisition_start_result import (
    SourceAcquisitionStartResult,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.ingest.usecases.roles.polling_acquisition_role import (
    PollingAcquisitionSession,
    PollingAcquisitionRole,
)
from whale.ingest.usecases.roles.subscription_acquisition_role import (
    SubscriptionAcquisitionRole,
)


class SourceAcquisitionUseCase:
    """统一 source 采集入口。

    Args:
        polling_role: 主动采集模式执行角色。
        subscription_role: 订阅模式执行角色。
    """

    _POLLING_MODES = {"READ", "READ_ONCE", "ONCE", "POLLING"}
    _SUBSCRIPTION_MODES = {"SUBSCRIBE", "SUBSCRIPTION"}
    _SUPPORTED_MODES = _POLLING_MODES | _SUBSCRIPTION_MODES

    def __init__(
        self,
        *,
        polling_role: PollingAcquisitionRole,
        subscription_role: SubscriptionAcquisitionRole,
    ) -> None:
        self._polling_role = polling_role
        self._subscription_role = subscription_role

    async def start(
        self,
        request: SourceAcquisitionRequest,
    ) -> SourceAcquisitionStartResult:
        """校验请求并启动采集。

        Args:
            request: 采集请求。

        Returns:
            采集启动结果。

        Raises:
            ValueError: 当请求参数非法时抛出。
            SourceAcquisitionError: 当启动阶段遇到稳定业务错误时抛出。
        """

        mode = request.execution.acquisition_mode.strip().upper()
        self._validate_request(request=request, mode=mode)

        if mode in self._POLLING_MODES:
            result = self._polling_role.start(request)
            if self._is_read_once_request(request, mode):
                session = cast(PollingAcquisitionSession, result.sessions[0])
                await session.task
            return result

        if mode in self._SUBSCRIPTION_MODES:
            return await self._subscription_role.start(request)

        raise ValueError(f"Unsupported acquisition_mode: {request.execution.acquisition_mode}")

    def _validate_request(
        self,
        *,
        request: SourceAcquisitionRequest,
        mode: str,
    ) -> None:
        """校验 source 采集请求。"""

        execution = request.execution

        if mode not in self._SUPPORTED_MODES:
            raise ValueError(f"Unsupported acquisition_mode: {request.execution.acquisition_mode}")
        if not request.request_id.strip():
            raise ValueError("request_id is required")
        if request.task_id <= 0:
            raise ValueError("task_id must be greater than 0")
        if not request.connections:
            raise ValueError("connections cannot be empty")
        if not request.items:
            raise ValueError("items cannot be empty")
        if not execution.protocol.strip():
            raise ValueError("protocol is required")
        if not execution.transport.strip():
            raise ValueError("transport is required")
        if execution.interval_ms <= 0:
            raise ValueError("interval_ms must be greater than 0")
        if execution.request_timeout_ms <= 0:
            raise ValueError("request_timeout_ms must be greater than 0")
        if execution.freshness_timeout_ms <= 0:
            raise ValueError("freshness_timeout_ms must be greater than 0")
        if execution.alive_timeout_ms <= 0:
            raise ValueError("alive_timeout_ms must be greater than 0")
        if execution.max_iteration is not None and execution.max_iteration <= 0:
            raise ValueError("max_iteration must be greater than 0")
        if mode in {"READ", "READ_ONCE", "ONCE"} and execution.max_iteration != 1:
            raise ValueError("read_once modes require max_iteration == 1")
        if execution.polling_max_concurrent_connections <= 0:
            raise ValueError("polling_max_concurrent_connections must be greater than 0")
        if execution.polling_connection_start_interval_ms < 0:
            raise ValueError("polling_connection_start_interval_ms cannot be negative")
        if execution.subscription_start_interval_ms < 0:
            raise ValueError("subscription_start_interval_ms cannot be negative")
        if execution.subscription_notification_queue_size <= 0:
            raise ValueError("subscription_notification_queue_size must be greater than 0")
        if execution.subscription_notification_max_lag_ms <= 0:
            raise ValueError("subscription_notification_max_lag_ms must be greater than 0")

        for connection in request.connections:
            self._validate_connection(connection)
        for item in request.items:
            self._validate_item(item)

    @staticmethod
    def _validate_connection(connection: SourceConnectionData) -> None:
        """校验单个连接 DTO。"""

        if not connection.host.strip():
            raise ValueError("connection.host is required")
        if connection.port <= 0:
            raise ValueError("connection.port must be greater than 0")
        if not connection.ied_name.strip():
            raise ValueError("connection.ied_name is required")
        if not connection.ld_name.strip():
            raise ValueError("connection.ld_name is required")

    @staticmethod
    def _validate_item(item: AcquisitionItemData) -> None:
        """校验单个采集点位 DTO。"""

        if not item.key.strip():
            raise ValueError("item.key is required")
        if not item.relative_path.strip():
            raise ValueError("item.relative_path is required")
        if item.profile_item_id <= 0:
            raise ValueError("item.profile_item_id must be greater than 0")

    @staticmethod
    def _is_read_once_request(request: SourceAcquisitionRequest, mode: str) -> bool:
        """判断请求是否为应立即感知结果的 one-shot 读取。"""

        return mode in {"READ", "READ_ONCE", "ONCE"} and request.execution.max_iteration == 1
