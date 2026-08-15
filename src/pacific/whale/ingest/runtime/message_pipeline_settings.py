"""消息管道配置。

定义消息管道（缓存到消息中间件）的可配置参数。
"""

from __future__ import annotations

from pacific.whale.ingest.config import (
    CONFIG,
    KafkaMessageConfig,
    MessageConfig,
    RedisStreamsMessageConfig,
    RelationalOutboxMessageConfig,
)

RelationalOutboxMessageSettings = RelationalOutboxMessageConfig
# Compatibility alias kept for older imports during the transition away from file outbox.
FileOutboxMessageSettings = RelationalOutboxMessageConfig
RedisStreamsMessageSettings = RedisStreamsMessageConfig
KafkaMessageSettings = KafkaMessageConfig


class _LazyMessagePipelineSettingsProxy:
    """仅在访问时才解析消息设置的延迟代理。"""

    def __getattr__(self, name: str) -> object:
        """属性访问委托给当前运行时消息设置。"""
        return getattr(CONFIG.message, name)


MESSAGE_PIPELINE_SETTINGS = _LazyMessagePipelineSettingsProxy()

__all__ = [
    "RelationalOutboxMessageSettings",
    "FileOutboxMessageSettings",
    "RedisStreamsMessageSettings",
    "KafkaMessageSettings",
    "RelationalOutboxMessageConfig",
    "RedisStreamsMessageConfig",
    "KafkaMessageConfig",
    "MessageConfig",
    "MESSAGE_PIPELINE_SETTINGS",
]
