"""speed layer 指标收集。

提供 pipeline 运行时的可观测性指标收集端口和测试实现：
- MetricsCollectorPort: 指标收集端口。
- InMemoryMetricsCollector: 测试用内存指标收集器。

收集的指标包括：checkpoint position、consumer lag、latency histogram、
sink success/failure count。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any


class MetricsCollectorPort(ABC):
    """指标收集端口。

    收集 speed layer 运行时的关键指标，用于监控和告警。

    实现方责任：
    - 高效记录和聚合指标。
    - 提供查询接口供健康检查和外部监控使用。
    - 支持按 writer/topic 维度分组。

    不负责：
    - 告警触发逻辑（由 octopus/monitoring 负责）。
    - 指标持久化（由 observability 层负责）。
    """

    @abstractmethod
    async def record_checkpoint(
        self,
        writer_name: str,
        topic: str,
        partition: int,
        offset: int,
    ) -> None:
        """记录 checkpoint position。

        记录指定 writer/topic/partition 的已处理 offset。

        Args:
            writer_name: writer 名称。
            topic: topic 名称。
            partition: 分区编号。
            offset: 已处理的 offset。
        """
        ...

    @abstractmethod
    async def record_lag(
        self,
        writer_name: str,
        topic: str,
        partition: int,
        lag: int,
    ) -> None:
        """记录 consumer lag。

        Args:
            writer_name: writer 名称。
            topic: topic 名称。
            partition: 分区编号。
            lag: 积压消息数。
        """
        ...

    @abstractmethod
    async def record_latency(
        self,
        writer_name: str,
        latency_ms: float,
    ) -> None:
        """记录消息处理延迟。

        Args:
            writer_name: writer 名称。
            latency_ms: 端到端延迟（毫秒）。
        """
        ...

    @abstractmethod
    async def record_sink_success(self, writer_name: str) -> None:
        """记录 sink 写入成功一次。

        Args:
            writer_name: writer 名称。
        """
        ...

    @abstractmethod
    async def record_sink_failure(self, writer_name: str, error: str) -> None:
        """记录 sink 写入失败一次。

        Args:
            writer_name: writer 名称。
            error: 失败原因。
        """
        ...


class InMemoryMetricsCollector(MetricsCollectorPort):
    """测试用内存指标收集器。

    将所有指标保存在内存中，支持按 writer 查询和 metrics dump。

    Attributes:
        checkpoints: writer -> topic -> partition -> offset 的检查点映射。
        lags: writer -> topic -> partition -> lag 的积压映射。
        latencies: writer -> [latency_ms, ...] 的延迟记录列表。
        sink_success_count: writer -> 成功次数映射。
        sink_failure_count: writer -> 失败次数映射。
        sink_errors: writer -> [error, ...] 的失败记录列表。
    """

    def __init__(self) -> None:
        """初始化空的内存指标收集器。"""
        self.checkpoints: dict[str, dict[str, dict[int, int]]] = (
            defaultdict(lambda: defaultdict(dict))
        )
        """检查点位置记录。"""
        self.lags: dict[str, dict[str, dict[int, int]]] = (
            defaultdict(lambda: defaultdict(dict))
        )
        """consumer lag 记录。"""
        self.latencies: dict[str, list[float]] = defaultdict(list)
        """延迟记录（毫秒）。"""
        self.sink_success_count: dict[str, int] = defaultdict(int)
        """sink 成功计数。"""
        self.sink_failure_count: dict[str, int] = defaultdict(int)
        """sink 失败计数。"""
        self.sink_errors: dict[str, list[str]] = defaultdict(list)
        """sink 错误消息列表。"""

    async def record_checkpoint(
        self,
        writer_name: str,
        topic: str,
        partition: int,
        offset: int,
    ) -> None:
        """记录 checkpoint position。

        更新内存中的检查点偏移量。

        Args:
            writer_name: writer 名称。
            topic: topic 名称。
            partition: 分区编号。
            offset: 已处理的 offset。
        """
        self.checkpoints[writer_name][topic][partition] = offset

    async def record_lag(
        self,
        writer_name: str,
        topic: str,
        partition: int,
        lag: int,
    ) -> None:
        """记录 consumer lag。

        Args:
            writer_name: writer 名称。
            topic: topic 名称。
            partition: 分区编号。
            lag: 积压消息数。
        """
        self.lags[writer_name][topic][partition] = lag

    async def record_latency(
        self,
        writer_name: str,
        latency_ms: float,
    ) -> None:
        """记录延迟。

        Args:
            writer_name: writer 名称。
            latency_ms: 端到端延迟（毫秒）。
        """
        self.latencies[writer_name].append(latency_ms)

    async def record_sink_success(self, writer_name: str) -> None:
        """记录一次成功的 sink 写入。

        Args:
            writer_name: writer 名称。
        """
        self.sink_success_count[writer_name] += 1

    async def record_sink_failure(self, writer_name: str, error: str) -> None:
        """记录一次失败的 sink 写入。

        Args:
            writer_name: writer 名称。
            error: 失败原因。
        """
        self.sink_failure_count[writer_name] += 1
        self.sink_errors[writer_name].append(error)

    def dump(self) -> dict[str, Any]:
        """导出全部指标快照。

        测试辅助方法，用于断言验证。

        Returns:
            包含所有指标的字典快照。
        """
        return {
            "checkpoints": dict(self.checkpoints),
            "lags": dict(self.lags),
            "latencies": dict(self.latencies),
            "sink_success_count": dict(self.sink_success_count),
            "sink_failure_count": dict(self.sink_failure_count),
            "snapshot_at": datetime.now(tz=timezone.utc).isoformat(),
        }

    def get_success_count(self, writer_name: str) -> int:
        """获取指定 writer 的成功计数。

        Args:
            writer_name: writer 名称。

        Returns:
            成功次数。
        """
        return self.sink_success_count.get(writer_name, 0)

    def get_failure_count(self, writer_name: str) -> int:
        """获取指定 writer 的失败计数。

        Args:
            writer_name: writer 名称。

        Returns:
            失败次数。
        """
        return self.sink_failure_count.get(writer_name, 0)

    def get_avg_latency(self, writer_name: str) -> float:
        """获取指定 writer 的平均延迟。

        Args:
            writer_name: writer 名称。

        Returns:
            平均延迟（毫秒），无数据时返回 0.0。
        """
        values = self.latencies.get(writer_name, [])
        if not values:
            return 0.0
        return sum(values) / len(values)
