"""消息发布适配器。

实现 MessagePublisherPort，将状态快照发布到消息中间件。
外部依赖：Kafka / Redis。
失败处理：失败不传播到调用方，记录 error 后继续。
"""

from __future__ import annotations

from datetime import UTC, datetime

from pacific.whale.ingest.ports.message import MessagePublisherPort
from pacific.whale.ingest.ports.message.message_publisher_port import (
    MessagePublishResult,
    StateSnapshotMessage,
)


class RelationalOutboxMessagePublisher(MessagePublisherPort):
    """No-op outbox 发布器（schema 重写后表已移除）。"""

    def publish_snapshot(self, message: StateSnapshotMessage) -> MessagePublishResult:
        """返回当前快照。"""
        return MessagePublishResult(
            pipeline_name="relational_outbox",
            success=True,
            message_id=message.message_id,
            message_count=1,
            published_at=datetime.now(tz=UTC),
        )
