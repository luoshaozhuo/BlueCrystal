"""采集请求 DTO。"""

from __future__ import annotations

from dataclasses import dataclass, field

from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData


@dataclass(slots=True)
class AcquisitionExecutionOptions:
    """描述采集请求的执行选项。"""

    protocol: str
    transport: str
    acquisition_mode: str
    interval_ms: int
    max_iteration: int | None
    request_timeout_ms: int
    freshness_timeout_ms: int
    alive_timeout_ms: int
    client_backend: str | None = None
    params: dict[str, str | int | float | bool] = field(default_factory=dict)

    polling_max_concurrent_connections: int = 4
    polling_connection_start_interval_ms: int = 0

    subscription_start_interval_ms: int = 0
    subscription_notification_queue_size: int = 1000
    subscription_notification_max_lag_ms: int = 5000


@dataclass(slots=True)
class AcquisitionItemData:
    """描述一个待采集点位及其基础元数据。"""

    key: str
    profile_item_id: int
    relative_path: str


@dataclass(slots=True)
class SourceAcquisitionRequest:
    """描述一个 source 的采集请求。"""

    request_id: str
    task_id: int
    execution: AcquisitionExecutionOptions
    connections: list[SourceConnectionData]
    items: list[AcquisitionItemData]
