"""消息管道领域模型。

定义 message_pipeline 的核心数据结构：Envelope、TopicSpec、PartitionKey 策略、
MessageOffset 和 ReplayRequest。这些模型位于领域层，不依赖具体 message broker
（Kafka/Pulsar）实现。

本文件不包含端口接口和适配器实现。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol


@dataclass(slots=True)
class Envelope:
    """消息统一信封。

    作为 ingest 与 speed layer 之间的标准化消息载体，承载单次采集或事件的所有
    相关数据项。schema_version 支持消息格式演进和兼容性检查。

    Raises:
        ValueError: 当 items 为空列表时，取决于调用方策略；本模型不做强制校验。
    """

    schema_version: str
    """消息格式版本号，用于 schema 演进兼容。"""

    message_id: str
    """全局唯一消息标识，用于去重和追踪。"""

    message_type: str
    """消息业务类型，例如 state_snapshot、event、alarm 等。"""

    trace_id: str | None
    """分布式追踪 ID，用于跨采集/传输/存储环节的链路关联。"""

    source_id: str
    """数据源标识，对应采集点或设备逻辑 ID。"""

    published_at: datetime
    """消息发布时间，用于时效性判断和乱序处理。"""

    items: list[dict[str, object]]
    """载荷数据项列表，每项为可变键值对，按采集字段展开。"""

    partition_key: str | None = None
    """分区键，用于 topic 内分区路由；为空时由 sink adapter 自动分配。"""


class PartitionKeyStrategy(Enum):
    """分区键策略枚举。

    定义消息路由到 topic 分区时使用的键策略。sink adapter 根据此策略计算每条
    消息的目标分区。

    Attributes:
        SOURCE_ID: 按 source_id 分区，保证同一数据源的消息保序。
        DEVICE_ID: 按 device_id 分区，保证同一设备的消息保序。
        STATION_ID: 按 station_id 分区，保证同一场站的消息保序。
        CUSTOM: 使用 envelope.partition_key 字段作为分区键。
    """

    SOURCE_ID = "source_id"
    """按 source_id 分区。"""
    DEVICE_ID = "device_id"
    """按 device_id 分区。"""
    STATION_ID = "station_id"
    """按 station_id 分区。"""
    CUSTOM = "custom"
    """使用 envelope.partition_key 自定义分区键。"""


class PartitionKey(Protocol):
    """分区键解析器协议。

    实现方负责根据策略从 Envelope 中提取分区键字符串。sink adapter 调用此协议
    获取路由信息，不关心具体 brokder 如何实现分区。
    """

    def resolve(self, envelope: Envelope) -> str:
        """从消息信封中解析分区键。

        Args:
            envelope: 待发布的消息信封。

        Returns:
            分区键字符串，用于 topic 分区路由。
        """
        ...


class SourceIdPartitionKey:
    """按 source_id 解析分区键。

    从 envelope.source_id 提取分区键，保证同一数据源的消息按序进入同一分区。
    """

    def resolve(self, envelope: Envelope) -> str:
        """从消息信封中解析分区键。

        Args:
            envelope: 待发布的消息信封。

        Returns:
            envelope.source_id 作为分区键。
        """
        return envelope.source_id


class DeviceIdPartitionKey:
    """按 device_id 解析分区键。

    从 envelope.items 中提取第一个包含 device_id 的条目，用于保证同一设备的
    消息保序。如无 device_id，fallback 到 source_id。
    """

    def resolve(self, envelope: Envelope) -> str:
        """从消息信封中解析设备级分区键。

        Args:
            envelope: 待发布的消息信封。

        Returns:
            device_id 或 fallback source_id 作为分区键。
        """
        for item in envelope.items:
            device_id = item.get("device_id")
            if device_id and isinstance(device_id, str):
                return device_id
        return envelope.source_id


class StationIdPartitionKey:
    """按 station_id 解析分区键。

    从 envelope.items 中提取第一个包含 station_id 的条目，用于保证同一场站的
    消息保序。如无 station_id，fallback 到 source_id。
    """

    def resolve(self, envelope: Envelope) -> str:
        """从消息信封中解析场站级分区键。

        Args:
            envelope: 待发布的消息信封。

        Returns:
            station_id 或 fallback source_id 作为分区键。
        """
        for item in envelope.items:
            station_id = item.get("station_id")
            if station_id and isinstance(station_id, str):
                return station_id
        return envelope.source_id


class CustomPartitionKey:
    """按 envelope.partition_key 解析分区键。

    直接使用 envelope.partition_key 字段值。调用方需确保该字段已正确设置。
    """

    def resolve(self, envelope: Envelope) -> str:
        """从 envelope.partition_key 字段返回分区键。

        Args:
            envelope: 待发布的消息信封。

        Returns:
            envelope.partition_key 或 default 值。
        """
        return envelope.partition_key or envelope.source_id


@dataclass(slots=True)
class TopicSpec:
    """消息 topic 配置规格。

    定义单个 topic 的名称、分区数、副本因子和消息保留时长。用于 adapter 初始化
    时的 topic 配置，不包含运行时水位和积压信息。

    Attributes:
        name: topic 名称。
        partitions: 分区数量。
        replication_factor: 副本因子，通常 >= 1。
        retention_ms: 消息保留时长（毫秒），None 表示使用 broker 默认值。
    """

    name: str
    """topic 名称。"""
    partitions: int = 1
    """分区数量。"""
    replication_factor: int = 1
    """副本因子。"""
    retention_ms: int | None = None
    """消息保留时长（毫秒）。"""


@dataclass(slots=True)
class MessageOffset:
    """消息偏移量/位置标识。

    记录单条消息在 topic 分区内的位置信息，用于 offset 管理和回放。

    Attributes:
        partition: 分区编号。
        offset: 分区内偏移量。
        timestamp: 消息时间戳。
    """

    partition: int
    """分区编号。"""
    offset: int
    """分区内偏移量。"""
    timestamp: datetime | None = None
    """消息时间戳。"""


@dataclass(slots=True)
class ReplayRequest:
    """消息回放请求。

    定义按 topic 和时间窗口或 offset 范围回放消息的请求参数。start 和 end 可
    分别使用 offset 或 timestamp 指定，至少指定一种方式。

    Attributes:
        topic: 回放目标 topic。
        start_offset: 回放起始 offset，None 表示从最早可用消息开始。
        start_timestamp: 回放起始时间戳，None 表示不按时间过滤起点。
        end_offset: 回放结束 offset，None 表示回放到最新消息。
        end_timestamp: 回放结束时间戳，None 表示不按时间过滤终点。
    """

    topic: str
    """回放目标 topic。"""
    start_offset: MessageOffset | None = None
    """回放起始 offset。"""
    start_timestamp: datetime | None = None
    """回放起始时间戳。"""
    end_offset: MessageOffset | None = None
    """回放结束 offset。"""
    end_timestamp: datetime | None = None
    """回放结束时间戳。"""
