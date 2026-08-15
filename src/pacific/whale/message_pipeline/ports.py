"""消息管道端口接口。

定义 message_pipeline 的六边形架构端口层：消息消费、消息发布、schema 注册、
dead letter queue、消息回放。所有端口使用 ABC 定义调用方契约，不包含具体
broker（Kafka/Pulsar）实现。

本文件是 ingest 层与 speed layer 之间的解耦边界，替代 ingest 现有的
MessagePublisherPort（保留不变），提供更完整的消息管道抽象。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from pacific.whale.message_pipeline.model import (
    Envelope,
    MessageOffset,
    ReplayRequest,
)

# Schema 类型: 在 schema registry 中注册和获取的 schema 定义。
# 生产环境中对应 Avro/JSON Schema/Protobuf 对象，此处为通用占位 object。


class MessageSourcePort(ABC):
    """消息消费端口。

    定义从 message pipeline 消费消息的异步契约。调用方通过 consumer group 订阅
    topic，按 offset 管理进度，支持手动 commit 和 seek 操作。

    实现方责任：
    - broker 连接管理与重连。
    - consumer group 协调与 rebalance。
    - 消息反序列化和 envelope 重建。
    - offset 持久化和恢复。

    不负责：
    - 消息处理逻辑（由 speed layer 负责）。
    - schema 演进兼容（由 SchemaRegistryPort 负责）。
    """

    @abstractmethod
    def consume(
        self, topic: str, group_id: str
    ) -> AsyncIterator[Envelope]:
        """从指定 topic 消费消息。

        返回异步迭代器，每次 yield 一条 Envelope。消费者应在消费完成后通过
        commit() 确认 offset。

        Args:
            topic: 消费的 topic 名称。
            group_id: consumer group 标识，用于 offset 管理和负载均衡。

        Yields:
            从 topic 消费到的 Envelope 消息。

        Raises:
            RuntimeError: broker 连接不可用或消费过程发生不可恢复错误。
        """
        ...

    @abstractmethod
    async def commit(self, offsets: list[MessageOffset]) -> None:
        """提交消费 offset。

        确认指定分区的消息已被成功处理，允许 broker 推进 consumer group 的
        committed offset。

        Args:
            offsets: 待提交的 offset 列表。

        Raises:
            RuntimeError: broker 不可用或提交失败（偏移可能丢失，需重试或记录）。
        """
        ...

    @abstractmethod
    async def seek(self, offsets: list[MessageOffset]) -> None:
        """重置消费位置到指定 offset。

        用于回放场景或错误恢复，将 consumer 的读取位置重置到指定 offset。

        Args:
            offsets: 目标 offset 列表。

        Raises:
            RuntimeError: broker 不可用或 seek 操作失败。
        """
        ...


class MessageSinkPort(ABC):
    """消息发布端口。

    定义向 message pipeline 发布消息的异步契约。是 ingest 现有
    MessagePublisherPort 的替代升级，提供更完整的发布抽象（含 flush 和异步支持）。

    实现方责任：
    - broker 连接管理与重连。
    - 消息序列化。
    - 分区路由（按 PartitionKey 策略）。
    - 发布缓冲与批量提交。

    不负责：
    - 消息业务语义校验。
    - DLQ 处理（由 DeadLetterSinkPort 负责）。
    """

    @abstractmethod
    async def publish(self, envelope: Envelope) -> MessageOffset:
        """发布一条消息到 pipeline。

        将 Envelope 发布到对应 topic。具体 topic 映射由 adapter 配置决定。

        Args:
            envelope: 待发布的消息信封。

        Returns:
            消息发布后的 offset 信息。

        Raises:
            RuntimeError: broker 不可用或发布失败。
        """
        ...

    @abstractmethod
    async def flush(self) -> None:
        """刷新发布缓冲区。

        确保所有缓冲消息被提交到 broker。调用方可在批次结束时调用以获得发送保证。

        Raises:
            RuntimeError: flush 操作失败。
        """
        ...


class SchemaRegistryPort(ABC):
    """schema 注册端口。

    管理 topic 的 schema 注册和查询，支持 schema 演进兼容性检查。生产环境中
    对应 Confluent Schema Registry 或类似服务。

    实现方责任：
    - schema 存储和版本管理。
    - 兼容性检查（BACKWARD / FORWARD / FULL）。
    - schema 与 topic 的绑定关系维护。

    不负责：
    - schema 内容本身的定义和变更批准。
    """

    @abstractmethod
    async def register(self, topic: str, schema: object) -> int:
        """注册或更新 topic 的 schema。

        如果 topic 已注册，执行兼容性检查后可能创建新版本。

        Args:
            topic: topic 名称。
            schema: schema 定义（类型取决于具体 registry 实现）。

        Returns:
            schema 版本号。

        Raises:
            RuntimeError: registry 不可用或兼容性检查失败。
        """
        ...

    @abstractmethod
    async def get_schema(self, topic: str) -> object | None:
        """获取 topic 当前有效的 schema。

        Args:
            topic: topic 名称。

        Returns:
            topic 的当前 schema，未注册时返回 None。

        Raises:
            RuntimeError: registry 不可用。
        """
        ...


class DeadLetterSinkPort(ABC):
    """死信队列（DLQ）写入端口。

    当消息处理失败达到重试上限后，将消息写入 DLQ 以供后续人工或自动恢复。

    实现方责任：
    - DLQ topic/存储的写入。
    - 失败上下文（error 信息、重试次数）的完整记录。
    - 消息原始内容的不变性保证。

    不负责：
    - 重试决策（由调用方在写入 DLQ 前判断）。
    - DLQ 消息的自动重放（由 ReplayRequest 驱动）。
    """

    @abstractmethod
    async def send(
        self,
        envelope: Envelope,
        error: str,
        retry_count: int,
    ) -> None:
        """将失败消息写入 DLQ。

        记录原始消息、失败原因和已执行的重试次数，用于后续排查和重放。

        Args:
            envelope: 处理失败的消息信封。
            error: 失败原因描述。
            retry_count: 已执行的重试次数（含当前失败的那次）。

        Raises:
            RuntimeError: DLQ 写入失败（可能导致消息丢失，调用方应有兜底机制）。
        """
        ...


class ReplayPort(ABC):
    """消息回放端口。

    支持按时间窗口或 offset 范围回放历史消息，用于故障恢复、数据补全和验证。

    实现方责任：
    - 按 ReplayRequest 参数查询并返回历史消息。
    - 对大量消息提供流式返回（AsyncIterator）。

    不负责：
    - 回放触发策略判断。
    """

    @abstractmethod
    def replay(
        self, request: ReplayRequest
    ) -> AsyncIterator[Envelope]:
        """按请求参数回放消息。

        返回异步迭代器，按时间/offset 顺序回放历史消息。

        Args:
            request: 回放请求，指定 topic 和时间/offset 范围。

        Yields:
            回放的历史 Envelope 消息。

        Raises:
            RuntimeError: broker 不可用或查询失败。
        """
        ...
