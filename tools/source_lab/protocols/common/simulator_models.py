"""ServerSimulatorFacade 数据模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


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
    """Read 操作结果。"""

    status: SimulatorStatus
    values: dict[str, str | int | float | bool | None] = field(default_factory=dict)
    message: str = ""


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
