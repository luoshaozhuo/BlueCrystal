"""ServerSimulatorFacade 数据模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SimulatorStatus(str, Enum):
    """Simulator 操作结果状态码。

    所有 Facade 方法返回的结果均包含状态码，NOT_IMPLEMENTED
    是合法状态而非异常。
    """

    OK = "OK"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    BAD_REQUEST = "BAD_REQUEST"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"
    UNAVAILABLE = "UNAVAILABLE"
    ALREADY_RUNNING = "ALREADY_RUNNING"
    NOT_RUNNING = "NOT_RUNNING"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"


@dataclass(frozen=True)
class SimulatorResult:
    """通用操作结果。"""

    status: SimulatorStatus
    message: str = ""


@dataclass(frozen=True)
class ReadSimulatorResult:
    """Read 操作结果。

    values 接受 dict 映射（正常读取结果）或 str 字符串
    （用于 NOT_IMPLEMENTED 或错误场景）。构造时自动将 str 迁移到
    message 字段并将 values 置为空 dict，保证下游调用方始终获取
    dict 类型。Simulator 工具不进入生产路径。
    """

    status: SimulatorStatus
    values: dict[str, str | int | float | bool | None] | str = field(default_factory=dict)
    message: str = ""

    def __post_init__(self) -> None:
        """将 str 类型的 values 规范化为 message 字段。

        多个协议 Simulator 在 NOT_IMPLEMENTED / BAD_REQUEST 场景中
        将错误描述直接传入 values 字段。此处通过 frozen dataclass
        的 object.__setattr__ 将字符串移到 message 字段，values
        重置为空 dict，保证下游（含测试）始终对 values 做 dict 访问。
        """
        if isinstance(self.values, str):
            # 如果调用方同时传了 message 和 string values，拼接两者
            combined = self.values
            if self.message:
                combined = f"{self.message}: {self.values}"
            object.__setattr__(self, 'message', combined)
            object.__setattr__(self, 'values', {})


@dataclass(frozen=True)
class SimulatorHealth:
    """Health check 结果。"""

    status: SimulatorStatus
    running: bool = False
    points_count: int = 0
    uptime_ms: int = 0
    message: str = ""


@dataclass(frozen=True)
class SimulatorPoint:
    """统一 simulator 点位描述。"""

    source_id: str
    node_key: str
    address: str
    value_type: str
    initial_value: str | int | float | bool | None = None
    writable: bool = False
    subscribable: bool = False
    reportable: bool = False


@dataclass(frozen=True)
class SimulatorCapabilities:
    """Simulator 支持能力矩阵。

    每个 bool 字段表示该操作是否真正实现（True = real implementation，
    False = 返回 NOT_IMPLEMENTED）。
    """

    start: bool = True
    stop: bool = True
    health: bool = True
    load_points: bool = True
    read: bool = False
    write: bool = False
    subscribe: bool = False
    report: bool = False
    update_values: bool = True
