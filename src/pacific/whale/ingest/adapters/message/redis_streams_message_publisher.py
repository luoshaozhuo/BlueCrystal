"""消息发布适配器。

实现 MessagePublisherPort，将状态快照发布到消息中间件。
外部依赖：Kafka / Redis。
失败处理：失败不传播到调用方，记录 error 后继续。
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol, cast

from pacific.whale.ingest.ports.message import MessagePublisherPort
from pacific.whale.ingest.ports.message.message_publisher_port import (
    MessagePublishResult,
    StateSnapshotMessage,
)
from pacific.whale.ingest.runtime.message_pipeline_settings import RedisStreamsMessageSettings


class RedisStreamsClient(Protocol):
    """发布器使用的最小 Redis Streams 客户端契约。"""

    def xadd(
        self,
        name: str,
        fields: dict[str, str],
    ) -> str | bytes:
        """向 Redis stream 追加一条记录。"""


class RedisStreamsMessagePublisher(MessagePublisherPort):
    """通过 XADD 将快照消息发布到 Redis stream。"""

    def __init__(
        self,
        settings: RedisStreamsMessageSettings,
        client: RedisStreamsClient | None = None,
    ) -> None:
        """保存配置和可选的注入 Redis 客户端实例。"""
        self._settings = settings
        self._client = client or self._build_client(settings)

    def publish_snapshot(self, message: StateSnapshotMessage) -> MessagePublishResult:
        """将单个快照消息发布到 Redis Streams。"""
        record_id = self._client.xadd(
            self._settings.stream_key,
            {
                "message": message.to_json(),
                "message_id": message.message_id,
                "snapshot_id": message.snapshot_id,
                "message_type": message.message_type,
            },
        )
        return MessagePublishResult(
            pipeline_name="redis_streams",
            success=True,
            message_id=message.message_id,
            message_count=1,
            published_at=datetime.now(tz=UTC),
            error_message=None if record_id else None,
        )

    @staticmethod
    def _build_client(settings: RedisStreamsMessageSettings) -> RedisStreamsClient:
        """延迟构造真实的 redis-py 客户端实例。"""
        try:
            from redis import Redis
        except ImportError as exc:
            raise RuntimeError(
                "Redis Streams publishing requires the `redis` package to be installed."
            ) from exc

        return cast(
            RedisStreamsClient,
            Redis.from_url(
                settings.redis_url,
                decode_responses=True,
            ),
        )
