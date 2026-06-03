"""消息管道模块。

作为 ingest 与 speed layer 之间的异步解耦边界，提供统一的消息 envelope、
topic/partition 配置、source-sink 端口、DLQ、回放和 adapter 抽象。

本模块不重造 Kafka/Pulsar，只做领域模型和端口层。具体 broker 实现由
adapters 子模块提供。
"""

from __future__ import annotations

from whale.message_pipeline.model import (
    Envelope,
    MessageOffset,
    PartitionKey,
    PartitionKeyStrategy,
    ReplayRequest,
    TopicSpec,
)
from whale.message_pipeline.ports import (
    DeadLetterSinkPort,
    MessageSinkPort,
    MessageSourcePort,
    ReplayPort,
    SchemaRegistryPort,
)

__all__ = [
    # 领域模型
    "Envelope",
    "MessageOffset",
    "PartitionKey",
    "PartitionKeyStrategy",
    "ReplayRequest",
    "TopicSpec",
    # 端口
    "DeadLetterSinkPort",
    "MessageSinkPort",
    "MessageSourcePort",
    "ReplayPort",
    "SchemaRegistryPort",
]
