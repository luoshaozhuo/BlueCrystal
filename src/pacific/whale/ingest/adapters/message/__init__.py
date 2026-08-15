"""消息发布适配器。

实现 MessagePublisherPort，将状态快照发布到消息中间件。
外部依赖：Kafka / Redis。
失败处理：失败不传播到调用方，记录 error 后继续。
"""

from __future__ import annotations

from importlib import import_module

__all__ = [
    "KafkaMessagePublisher",
    "RelationalOutboxMessagePublisher",
    "RedisStreamsMessagePublisher",
]


def __getattr__(name: str) -> object:
    """延迟暴露消息发布器，避免导入无关后端依赖。"""

    module_by_name = {
        "KafkaMessagePublisher": "whale.ingest.adapters.message.kafka_message_publisher",
        "RedisStreamsMessagePublisher": (
            "whale.ingest.adapters.message.redis_streams_message_publisher"
        ),
        "RelationalOutboxMessagePublisher": (
            "whale.ingest.adapters.message.relational_outbox_message_publisher"
        ),
    }
    module_name = module_by_name.get(name)
    if module_name is None:
        raise AttributeError(name)
    return getattr(import_module(module_name), name)
