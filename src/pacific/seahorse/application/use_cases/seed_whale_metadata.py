"""Whale 元数据样例 seed 用例。

该用例服务 Round 1 的样例库初始化能力，和 Runtime Contract 的
``WhaleMetadataPort`` 读取契约分离。真实数据库写入/清理由
infrastructure repository 实现。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class SampleMetadataSeedPort(Protocol):
    """样例元数据 seed 端口。

    该端口允许修改样例 Whale 元数据库，不用于 runtime tick 或 WritePlan
    读取链路。
    """

    def seed_sample_metadata(self) -> None:
        """写入样例 Whale 元数据。"""
        ...

    def clear_sample_metadata(self) -> None:
        """清理样例 Whale 元数据。"""
        ...


class SeedWhaleMetadataUseCase:
    """执行 Seahorse 样例 Whale 元数据 seed。

    该用例会通过端口触发外部数据库写入或清理；调用方必须确认目标为
    样例库或受控本地环境。
    """

    def __init__(self, repository: SampleMetadataSeedPort) -> None:
        """初始化用例。

        Args:
            repository: Whale 元数据端口实现。
        """
        self._repository = repository

    def seed(self) -> None:
        """写入样例 Whale 元数据。"""
        self._repository.seed_sample_metadata()

    def reset(self) -> None:
        """清理并重建样例 Whale 元数据。"""
        self._repository.clear_sample_metadata()
        self._repository.seed_sample_metadata()
