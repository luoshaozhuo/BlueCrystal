"""消息管道适配器包。

导出 message_pipeline 的各类适配器实现：
- InMemory 家族：测试用内存实现。
- Kafka 家族：基于 kafka-python 的真实/contract adapter。
- Pulsar 家族：contract-only adapter（optional 依赖，environment-pending）。
"""

from __future__ import annotations

from pacific.whale.message_pipeline.adapters.in_memory import (
    InMemoryDeadLetterSink,
    InMemoryMessageBus,
    InMemorySchemaRegistry,
)
from pacific.whale.message_pipeline.adapters.kafka import (
    KafkaSinkAdapter,
    KafkaSourceAdapter,
)
from pacific.whale.message_pipeline.adapters.pulsar import (
    PulsarSinkAdapter,
    PulsarSourceAdapter,
)

__all__ = [
    "InMemoryDeadLetterSink",
    "InMemoryMessageBus",
    "InMemorySchemaRegistry",
    "KafkaSinkAdapter",
    "KafkaSourceAdapter",
    "PulsarSinkAdapter",
    "PulsarSourceAdapter",
]
