"""Runtime v2 application 运行图模型。

本模块只表达运行时拓扑、driver instance 状态和绑定关系，不执行
driver I/O、不选择协议实现，也不调用 native/process 能力。driver 字段
承载 application port 约束下的外部对象。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Any

from starfish.application.runtime.event_bus import RuntimeEvent
from starfish.application.runtime.snapshot import RuntimeSnapshot
from starfish.application.runtime.state import RuntimeState
from starfish.domain.server_config import (
    StarfishEndpointConfig,
    StarfishPointConfig,
    StarfishServerMemberConfig,
)


class DriverState(str, Enum):
    """DriverInstance 生命周期状态。

    RETIRED 只用于 hot swap 后的旧实例终态，不参与正常启动/停止循环。
    """

    CREATED = "CREATED"
    INITIALIZED = "INITIALIZED"
    RUNNING = "RUNNING"
    DEGRADED = "DEGRADED"
    STOPPED = "STOPPED"
    RETIRED = "RETIRED"


@dataclass(frozen=True)
class DriverCapability:
    """Driver runtime 的能力声明快照。

    Attributes:
        names: 从 server/endpoint 配置继承的能力名列表。
    """

    names: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DriverRuntimeHandle:
    """Driver runtime 的非 I/O 元数据句柄。

    Attributes:
        mode: adapter factory 判定的运行模式。
        available: 当前 driver 是否可被启动。
        reason: factory 或环境探测给出的装配说明。
    """

    mode: str = "stub"
    available: bool = True
    reason: str = ""


@dataclass
class DriverInstance:
    """Runtime v2 的 driver 运行实体。

    Args:
        id: 实例唯一标识，默认由 node/binding 生成。
        version: 实例版本；hot swap 时新实例使用新的版本值。
        protocol: endpoint 协议名。
        state: 当前生命周期状态。
        driver: application DriverPort 约束下的外部 driver 对象；domain 不调用它。
        runtime: adapter factory 输出的运行时模式与可用性元数据。
        config: endpoint 相关配置快照。
        capability: driver 能力声明快照。
    """

    id: str
    version: str
    protocol: str
    state: DriverState
    driver: Any
    runtime: DriverRuntimeHandle
    config: dict[str, Any] = field(default_factory=dict)
    capability: DriverCapability = field(default_factory=DriverCapability)
    event_bus: Any = field(default=None, repr=False, compare=False)
    last_error: str | None = None
    health_score: float = 1.0

    def transition_to(self, next_state: DriverState) -> None:
        """按 Runtime v2 状态机推进实例状态。

        Args:
            next_state: 目标状态。

        Raises:
            ValueError: 当前状态不能进入目标状态。
        """
        allowed: dict[DriverState, set[DriverState]] = {
            DriverState.CREATED: {DriverState.INITIALIZED},
            DriverState.INITIALIZED: {DriverState.RUNNING, DriverState.STOPPED},
            DriverState.RUNNING: {DriverState.DEGRADED, DriverState.STOPPED},
            DriverState.DEGRADED: {DriverState.RUNNING, DriverState.STOPPED},
            DriverState.STOPPED: {DriverState.RUNNING, DriverState.RETIRED},
            DriverState.RETIRED: set(),
        }
        if next_state not in allowed[self.state]:
            raise ValueError(f"非法 DriverInstance 状态迁移: {self.state.value} -> {next_state.value}")
        self.state = next_state

    def initialize(self) -> None:
        """将新建实例推进到 INITIALIZED。"""
        self.transition_to(DriverState.INITIALIZED)

    def mark_running(self) -> None:
        """标记实例已进入 RUNNING。"""
        self.transition_to(DriverState.RUNNING)

    def mark_degraded(self) -> None:
        """标记实例进入 DEGRADED。"""
        self.transition_to(DriverState.DEGRADED)

    def mark_stopped(self) -> None:
        """标记实例已停止。"""
        self.transition_to(DriverState.STOPPED)

    def mark_retired(self) -> None:
        """标记 hot swap 后旧实例已退役。"""
        self.transition_to(DriverState.RETIRED)

    def runtime_status(self) -> str:
        """返回 RuntimeState 使用的稳定状态名。"""
        if self.state == DriverState.INITIALIZED:
            return "INIT"
        if self.state == DriverState.RETIRED:
            return "STOPPED"
        return self.state.value

    def runtime_state(self) -> RuntimeState:
        """生成当前实例的可观测状态切片。"""
        return RuntimeState(
            instance_id=self.id,
            status=self.runtime_status(),
            last_error=self.last_error,
            health_score=self.health_score,
        )

    def emit_runtime_event(
        self,
        event_type: str,
        *,
        node_id: str = "",
        payload: dict[str, Any] | None = None,
    ) -> None:
        """非侵入式发出 runtime event。

        EventBus 失败不得影响 driver 主路径，因此这里按任务约束吞掉
        event emit 异常。
        """
        if self.event_bus is None:
            return
        try:
            self.event_bus.emit(
                RuntimeEvent(
                    ts=time.time(),
                    type=event_type,
                    node_id=node_id,
                    instance_id=self.id,
                    driver=self.protocol,
                    payload=dict(payload or {}),
                )
            )
        except Exception:
            pass

    def record_error(
        self,
        message: str,
        *,
        node_id: str = "",
        payload: dict[str, Any] | None = None,
    ) -> None:
        """记录最近错误并发出 ERROR 事件。"""
        self.last_error = message
        self.health_score = 0.0
        error_payload = dict(payload or {})
        error_payload["error"] = message
        self.emit_runtime_event("ERROR", node_id=node_id, payload=error_payload)


@dataclass(frozen=True)
class RuntimeSignal:
    """RuntimeGraph 中的 point/signal 视图。

    Attributes:
        signal_id: signal 唯一标识，来源于原 point_id。
        point: 原 point 配置。
    """

    signal_id: str
    point: StarfishPointConfig


@dataclass
class RuntimeBinding:
    """RuntimeGraph 中 endpoint 到 DriverInstance 的绑定。

    Attributes:
        binding_id: binding 唯一标识。
        endpoint: 原 endpoint 配置。
        signals: binding 可暴露的 signal 列表。
        driver_instance: 当前绑定的 driver 运行实体。
    """

    binding_id: str
    endpoint: StarfishEndpointConfig
    driver_instance: DriverInstance
    signals: list[RuntimeSignal] = field(default_factory=list)


@dataclass
class RuntimeNode:
    """RuntimeGraph 中的 server node。

    Attributes:
        node_id: node 唯一标识。
        server: 原 server member 配置。
        bindings: node 下的 endpoint bindings。
    """

    node_id: str
    server: StarfishServerMemberConfig
    bindings: list[RuntimeBinding] = field(default_factory=list)


@dataclass
class RuntimeGraph:
    """Runtime v2 的运行图。

    RuntimeGraph 是当前运行时视图，结构为
    nodes[] -> bindings[] -> driver_instance。它不解析配置文件，也不创建
    具体 driver。
    """

    scenario_id: str
    config_name: str
    nodes: list[RuntimeNode] = field(default_factory=list)
    event_bus: Any = field(default=None, repr=False, compare=False)

    def find_binding(self, binding_id: str) -> RuntimeBinding:
        """按 binding_id 查找绑定。

        Args:
            binding_id: binding 唯一标识。

        Returns:
            匹配的 RuntimeBinding。

        Raises:
            KeyError: 没有找到对应 binding。
        """
        for node in self.nodes:
            for binding in node.bindings:
                if binding.binding_id == binding_id:
                    return binding
        raise KeyError(f"未找到 RuntimeBinding: {binding_id}")

    def bind_driver_instance(
        self,
        binding_id: str,
        driver_instance: DriverInstance,
    ) -> DriverInstance:
        """将 binding 重新绑定到新的 DriverInstance。

        Args:
            binding_id: 待替换的 binding。
            driver_instance: 新 driver instance。

        Returns:
            替换前的旧 DriverInstance。
        """
        binding = self.find_binding(binding_id)
        old_instance = binding.driver_instance
        binding.driver_instance = driver_instance
        return old_instance

    def health_summary(self) -> dict[str, int]:
        """返回 RuntimeGraph 的轻量健康汇总。"""
        instances = [
            binding.driver_instance
            for node in self.nodes
            for binding in node.bindings
        ]
        return {
            "node_count": len(self.nodes),
            "running_instances": sum(
                1 for instance in instances
                if instance.state == DriverState.RUNNING
            ),
            "degraded_instances": sum(
                1 for instance in instances
                if instance.state == DriverState.DEGRADED
            ),
        }

    def snapshot(self) -> RuntimeSnapshot:
        """生成当前 RuntimeGraph 的只读快照。"""
        states = [
            binding.driver_instance.runtime_state()
            for node in self.nodes
            for binding in node.bindings
        ]
        events_tail = []
        if self.event_bus is not None:
            try:
                events_tail = self.event_bus.tail()
            except Exception:
                events_tail = []
        return RuntimeSnapshot(
            timestamp=time.time(),
            graph=self,
            states=states,
            events_tail=events_tail,
        )


__all__ = [
    "DriverCapability",
    "DriverInstance",
    "DriverRuntimeHandle",
    "DriverState",
    "RuntimeBinding",
    "RuntimeGraph",
    "RuntimeNode",
    "RuntimeSignal",
]
