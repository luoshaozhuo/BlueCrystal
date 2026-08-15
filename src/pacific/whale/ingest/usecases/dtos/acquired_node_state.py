"""采集状态 DTO。

本模块定义 ingest usecase 内部使用的采集结果对象。

设计约定：
- AcquiredNodeValue 表示一个点位的一次采集值；
- AcquiredNodeStateBatch 表示同一个 source/LD 的一批采集值；
- cache / role / adapter 后续统一按 batch 更新 latest-state；
- batch 级时间用于表达 LD 状态版本；
- value 级时间用于保留协议原始时间与乱序保护；
- client_sequence 是客户端本地单调递增版本，用于 server_timestamp 缺失或乱序时兜底。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class AcquiredNodeValue:
    """一个点位的一次采集值。

    字段语义：
    - node_key：业务侧点位键；
    - value：序列化后的点位值；
    - quality：协议质量位，可为空；
    - source_timestamp：源端采样/观测时间，可为空；
    - server_timestamp：OPC UA server 给出的 DataValue 时间，可为空；
    - client_sequence：客户端本地单调序号，用于乱序保护；
    - attributes：扩展字段，保留协议附加信息。
    """

    node_key: str
    value: str
    quality: str | None = None
    source_timestamp: datetime | None = None
    server_timestamp: datetime | None = None
    client_sequence: int | None = None
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AcquiredNodeStateBatch:
    """同一个 source/LD 的一批采集状态。

    字段语义：
    - source_id：采集源标识，通常为 ld_name；
    - batch_observed_at：该批数据作为 LD 状态视图的统一观测时间；
    - client_received_at：客户端收到该批数据的时间；
    - client_processed_at：客户端完成转换并准备写入 cache 的时间；
    - values：该批点位值；
    - availability_status：该批数据写入 cache 后建议形成的 LD 可用性状态；
    - attributes：扩展字段，保留批次级附加信息。
    """

    source_id: str
    batch_observed_at: datetime
    client_received_at: datetime
    client_processed_at: datetime
    values: list[AcquiredNodeValue]
    availability_status: str = "VALID"
    attributes: dict[str, Any] = field(default_factory=dict)

    def is_empty(self) -> bool:
        """返回该批次是否不包含任何点位值。"""

        return not self.values
