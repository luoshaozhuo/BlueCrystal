"""RuntimeEvent 领域事件模型。

本模块只定义运行态事件的数据结构，不负责事件存储、发送、订阅或外部
观测系统集成。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RuntimeEvent:
    """Starfish runtime 统一事件记录。

    Attributes:
        ts: 事件发生时间，使用 `time.time()` 秒级浮点时间戳。
        type: 事件类型，取值为 START / STOP / READ / WRITE / SWAP / ERROR。
        node_id: RuntimeGraph node id。
        instance_id: DriverInstance id。
        driver: driver 协议或运行模式标识。
        payload: 事件附加信息；仅保存轻量上下文，不承载外部 I/O 资源。
    """

    ts: float
    type: str
    node_id: str
    instance_id: str
    driver: str
    payload: dict[str, Any] = field(default_factory=dict)


__all__ = ["RuntimeEvent"]
