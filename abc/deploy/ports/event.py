"""可选 Runtime 事实事件输出契约。

事件投递失败不能影响 Ownership、服务生命周期或 Runtime 关闭；第一阶段只冻结接口，
不把它接入核心控制路径。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class RuntimeEventPort(Protocol):
    """接收已经发生的 Runtime 事实，供宿主程序进行非关键观测。"""

    async def publish(self, event_name: str, attributes: dict[str, str]) -> None:
        """发布事实事件；实现方应自行隔离投递失败。"""
