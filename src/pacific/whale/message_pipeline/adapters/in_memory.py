"""消息管道内存测试适配器。

提供用于单元测试和集成测试的内存实现：
- InMemoryMessageBus: 同时实现 MessageSourcePort 和 MessageSinkPort，在内存中
  传递消息。
- InMemoryDeadLetterSink: 将 DLQ 消息保存到内存列表，供断言验证。
- InMemorySchemaRegistry: 在内存中管理 topic-schema 映射。

所有实现均为测试替身（L1 unit/mock），不连接任何真实 broker。
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import TypeVar

from pacific.whale.message_pipeline.model import (
    Envelope,
    MessageOffset,
    ReplayRequest,
)
from pacific.whale.message_pipeline.ports import (
    DeadLetterSinkPort,
    MessageSinkPort,
    MessageSourcePort,
    ReplayPort,
    SchemaRegistryPort,
)

_SchemaType = TypeVar("_SchemaType")


class InMemoryMessageBus(MessageSourcePort, MessageSinkPort, ReplayPort):
    """测试用内存消息总线。

    在单个进程内实现消息发布、消费和回放，不依赖任何外部 broker。
    用于 speed layer 和 message_pipeline 的单元/集成测试。

    Attributes:
        messages: 按 topic 分组的消息列表（按发布顺序排列）。
        _offset_counter: 全局 offset 计数器。
        _consumer_offsets: 按 consumer group 和 partition 记录的已提交 offset。

    Notes:
        不支持真实分区（所有消息写入 partition=0）。
        不支持并发消费者（单一 asyncio 事件循环）。
        消息消费后不会自动删除，仅在 seek 时调整读取位置。
    """

    def __init__(self) -> None:
        """初始化空的内存消息总线。"""
        self.messages: dict[str, list[Envelope]] = defaultdict(list)
        """按 topic 存储的消息记录。"""
        self._offset_counter: int = 0
        """自增 offset 计数器。"""
        self._consumer_offsets: dict[str, dict[str, dict[int, int]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(int))
        )
        """按 consumer group、topic 和 partition 记录的 offset。"""

    # ---- MessageSinkPort ----

    async def publish(self, envelope: Envelope) -> MessageOffset:
        """模拟发布一条消息到内存总线。

        将 Envelope 追加到对应 topic 的消息列表，返回虚拟 offset。
        如果 envelope.published_at 未设置，使用当前 UTC 时间。

        Args:
            envelope: 待发布的消息信封。

        Returns:
            包含 partition=0 和自增 offset 的虚拟 MessageOffset。
        """
        topic = _resolve_topic(envelope)
        self.messages[topic].append(envelope)
        offset = MessageOffset(
            partition=0,
            offset=self._offset_counter,
            timestamp=datetime.now(tz=timezone.utc),
        )
        self._offset_counter += 1
        return offset

    async def flush(self) -> None:
        """内存总线不需要 flush，此方法为空操作。"""
        return

    # ---- MessageSourcePort ----

    async def consume(
        self, topic: str, group_id: str
    ) -> AsyncIterator[Envelope]:
        """模拟从指定的 topic 消费消息。

        从当前 consumer group 的 committed offset 开始读取，每条消息
        yield 后推进 offset。如果已通过 seek() 重置过 offset，使用 seek
        设置的 offset 作为起点。

        Args:
            topic: 消费的 topic 名称。
            group_id: consumer group 标识。

        Yields:
            topic 中未被该 group 消费的 Envelope 消息。

        Notes:
            读取完成后不会自动 commit，调用方需显式调用 commit()。
        """
        start_offset = self._consumer_offsets[group_id][topic].get(0, 0)
        all_messages = self.messages.get(topic, [])
        for i in range(start_offset, len(all_messages)):
            envelope = all_messages[i]
            self._consumer_offsets[group_id][topic][0] = i + 1
            yield envelope
            await asyncio.sleep(0)

    async def commit(self, offsets: list[MessageOffset]) -> None:
        """模拟提交消费 offset。

        更新对应 consumer group 的 partition offset。

        Args:
            offsets: 待提交的 offset 列表。
        """
        for off in offsets:
            # 不在此处更新内部状态，因为 consume 已在 yield 后推进了 offset。
            # 此方法用于兼容接口，实际提交逻辑由真实 broker adapter 实现。
            pass

    async def seek(self, offsets: list[MessageOffset]) -> None:
        """模拟重置消费位置。

        将所有已知 consumer group 和 topic 的 partition offset 重置为指定值，
        模拟真实 broker 中 seek 申请对所有 group/topic 生效。

        Args:
            offsets: 目标 offset 列表。
        """
        for off in offsets:
            for group_id in list(self._consumer_offsets.keys()):
                for topic_name in list(self._consumer_offsets[group_id].keys()):
                    self._consumer_offsets[group_id][topic_name][off.partition] = off.offset

    # ---- ReplayPort ----

    async def replay(
        self, request: ReplayRequest
    ) -> AsyncIterator[Envelope]:
        """模拟按请求参数回放消息。

        按 time/offset 范围从内存中筛选消息并 yield。

        Args:
            request: 回放请求参数。

        Yields:
            符合条件的 Envelope 消息。
        """
        all_messages = self.messages.get(request.topic, [])
        for envelope in all_messages:
            if request.start_timestamp and envelope.published_at:
                if envelope.published_at < request.start_timestamp:
                    continue
            if request.end_timestamp and envelope.published_at:
                if envelope.published_at > request.end_timestamp:
                    continue
            yield envelope
            await asyncio.sleep(0)


class InMemoryDeadLetterSink(DeadLetterSinkPort):
    """测试用内存 DLQ 实现。

    将失败消息保存到内存列表，支持测试断言验证 DLQ 内容和顺序。

    Attributes:
        dead_letters: 按时间顺序存储的 DLQ 记录列表。
    """

    def __init__(self) -> None:
        """初始化空的 DLQ 存储。"""
        self.dead_letters: list[dict[str, object]] = []
        """DLQ 记录列表，每条记录包含 envelope、error、retry_count。"""

    async def send(
        self,
        envelope: Envelope,
        error: str,
        retry_count: int,
    ) -> None:
        """将失败消息写入内存 DLQ。

        构造包含完整失败上下文的记录并追加到 dead_letters 列表。

        Args:
            envelope: 处理失败的消息信封。
            error: 失败原因描述。
            retry_count: 已执行的重试次数。
        """
        self.dead_letters.append({
            "envelope": envelope,
            "error": error,
            "retry_count": retry_count,
        })


class InMemorySchemaRegistry(SchemaRegistryPort):
    """测试用内存 schema registry 实现。

    在内存中维护 topic 到 schema 的映射，不执行兼容性检查。

    Attributes:
        _schemas: topic 到 schema 对象的映射字典。
    """

    def __init__(self) -> None:
        """初始化空的内存 schema registry。"""
        self._schemas: dict[str, object] = {}
        """topic 到 schema 的映射。"""

    async def register(self, topic: str, schema: object) -> int:
        """在内存中注册或更新 topic 的 schema。

        不执行兼容性检查，直接覆盖已有 schema。

        Args:
            topic: topic 名称。
            schema: schema 定义对象。

        Returns:
            固定返回 1（版本号）。
        """
        self._schemas[topic] = schema
        return 1

    async def get_schema(self, topic: str) -> object | None:
        """从内存中获取 topic 的 schema。

        Args:
            topic: topic 名称。

        Returns:
            topic 对应的 schema，未注册时返回 None。

        Notes:
            返回类型 object 是 _SchemaType 的运行时具体化。调用方应自行做
            类型收敛。
        """
        return self._schemas.get(topic)


def _resolve_topic(envelope: Envelope) -> str:
    """根据 Envelope 的 message_type 推导默认 topic 名称。

    作为 InMemoryMessageBus 的内部辅助函数，当 envelope 没有显式指定 topic
    时，按消息类型生成默认 topic 名称。

    Args:
        envelope: 消息信封。

    Returns:
        topic 名称字符串。
    """
    return f"whale.{envelope.message_type}"
