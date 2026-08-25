"""可观测性运行状态的稳定只读数据模型。"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType


class RuntimeLifecycle(StrEnum):
    """Runtime 生命周期状态。"""

    CREATED = "created"
    STARTING = "starting"
    STARTED = "started"
    CLOSING = "closing"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class BackendStatus:
    """单个 backend 的启用与就绪摘要。"""

    name: str
    enabled: bool
    state: str


@dataclass(frozen=True, slots=True)
class InstrumentationStatus:
    """单个 instrumentation adapter 的安装状态与低风险详情。"""

    name: str
    installed: bool
    started: bool
    details: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class WorkerStatus:
    """单个 Worker operation 的当前执行状态。"""

    operation: str
    in_flight: int
    last_result: str | None
    last_finished_at: datetime | None


@dataclass(frozen=True, slots=True)
class RuntimeStatus:
    """Runtime 聚合状态快照。"""

    enabled: bool
    lifecycle: RuntimeLifecycle
    backends: tuple[BackendStatus, ...]
    instrumentations: tuple[InstrumentationStatus, ...]
    workers: tuple[WorkerStatus, ...]
    observed_at: datetime

    def to_dict(self) -> dict[str, object]:
        """转换为稳定、可直接返回给 HTTP health endpoint 的字典。"""
        return {
            "enabled": self.enabled,
            "lifecycle": self.lifecycle.value,
            "observed_at": self.observed_at.isoformat(),
            "backends": [
                {"name": item.name, "enabled": item.enabled, "state": item.state}
                for item in self.backends
            ],
            "instrumentations": [
                {
                    "name": item.name,
                    "installed": item.installed,
                    "started": item.started,
                    "details": {
                        key: _to_plain_value(value)
                        for key, value in item.details.items()
                    },
                }
                for item in self.instrumentations
            ],
            "workers": [
                {
                    "operation": item.operation,
                    "in_flight": item.in_flight,
                    "last_result": item.last_result,
                    "last_finished_at": (
                        item.last_finished_at.isoformat()
                        if item.last_finished_at is not None
                        else None
                    ),
                }
                for item in self.workers
            ],
        }


def immutable_details(values: Mapping[str, object]) -> Mapping[str, object]:
    """递归冻结常用容器，隔离 adapter 后续修改与快照调用方写入。"""
    return MappingProxyType(
        {key: _freeze_value(value) for key, value in values.items()}
    )


def _freeze_value(value: object) -> object:
    """把详情中的内建可变容器递归转换为只读结构。"""
    if isinstance(value, Mapping):
        return MappingProxyType(
            {key: _freeze_value(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze_value(item) for item in value)
    return value


def _to_plain_value(value: object) -> object:
    """把冻结详情转换为 FastAPI 可稳定序列化的普通容器。"""
    if isinstance(value, Mapping):
        return {key: _to_plain_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_to_plain_value(item) for item in value]
    if isinstance(value, frozenset):
        converted = [_to_plain_value(item) for item in value]
        return sorted(converted, key=repr)
    return value
