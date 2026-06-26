"""统一 DriverPort。

Runtime v2 只暴露 start/stop/read/write/health 五个稳定操作，配置加载、
协议 codec、native/process 细节和预连接语义不属于本 port。
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class DriverPort(Protocol):
    """协议运行时 driver 的最小统一接口。"""

    def start(self) -> None:
        """启动 driver runtime。"""

    def stop(self) -> None:
        """停止 driver runtime 并释放资源。"""

    def read(self, point_id: str | list[str] | None = None) -> dict[str, Any]:
        """读取点位值。

        Args:
            point_id: Runtime v2 单点读取参数；为保持既有 API 行为，也接受
                旧调用传入的 point id 列表或 None。

        Returns:
            点位 ID 到当前值的映射。
        """

    def write(self, point_id: str, value: Any) -> None:
        """写入单点值。"""

    def health(self) -> dict[str, Any]:
        """返回 driver 健康状态。"""
