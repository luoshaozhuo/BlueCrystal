"""消息管线抽象。定义采集数据输出的发布接口和内存实现。"""

from __future__ import annotations

from typing import Protocol


class IngestMessagePipeline(Protocol):
    """消息管线 port 协议。定义将采集记录发送到下游管线的发布接口。"""

    def publish(self, records: list[object]) -> None:
        """将一批采集数据发布到下游管线。返回发布结果。"""


class InMemoryIngestMessagePipeline:
    """简单内存消息管线实现。用于测试和本地单节点运行场景，批次存储在内存列表中。"""

    def __init__(self) -> None:
        """初始化空的已发布批次存储。创建用于存储发布记录的内存列表。"""
        self._batches: list[list[object]] = []

    def publish(self, records: list[object]) -> None:
        """将一批采集数据存储到内存列表中。"""
        self._batches.append(list(records))

    def batches(self) -> list[list[object]]:
        """返回所有已发布的批次列表。主要用于测试验证和检查。"""
        return [list(batch) for batch in self._batches]
