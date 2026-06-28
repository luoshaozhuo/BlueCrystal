"""Starfish server manager API facade。

API 层负责默认 adapter 装配，并将用户入口委托给 application workflow 和
runtime 控制用例；runtime context 只在内部保存，不作为外部 DTO 暴露。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from starfish.application.runtime.context import StarfishRuntimeContext
from starfish.application.use_cases import (
    HealthSystemUseCase,
    ReadSystemUseCase,
    StartSystemUseCase,
    StopSystemUseCase,
    WriteSystemUseCase,
)
from starfish.container import build_default_runtime_context


class StarfishServerManager:
    """对外唯一入口 facade。"""

    def __init__(
        self,
        conf_path: Path | None = None,
        *,
        context: StarfishRuntimeContext | None = None,
    ) -> None:
        """初始化 manager。

        Args:
            conf_path: 配置文件路径，如果提供则通过默认 composition root 构建 runtime context。
            context: 已构建的 runtime context，如果提供则直接使用。
        Raises:
            ValueError: 如果两者都未提供。
        """
        if context is not None:
            self._runtime = context
        elif conf_path is not None:
            self._runtime = build_default_runtime_context(conf_path)
        else:
            raise ValueError("必须提供 conf_path 或 context")
        self._started: list[Any] = []

    # ---------------- runtime views ----------------

    @property
    def config(self):
        """返回已加载配置对象。"""
        return self._runtime.config

    @property
    def registry(self):
        """返回内部 runtime registry 视图。"""
        return self._runtime.registry

    @property
    def validation(self):
        """返回配置加载校验结果。"""
        return self._runtime.validation

    # ---------------- lifecycle ----------------

    def start(self) -> None:
        """启动全部可用 endpoint。"""
        if self._started:
            return
        self._started = StartSystemUseCase().execute(self.registry)

    def stop(self) -> None:
        """停止本 manager 已启动的 endpoint。"""
        StopSystemUseCase().execute(self.registry, self._started)
        self._started = []

    # ---------------- observability ----------------

    def status(self) -> dict[str, Any]:
        """返回面向 API 调用方的运行状态摘要。"""
        return {
            "scenario_id": self.config.scenario_id,
            "config_name": self.config.config_name,
            "synthetic": self.config.synthetic,
            "server_count": len(self.config.servers),
            "endpoints": HealthSystemUseCase().execute(self.registry),
        }

    def describe(self) -> dict[str, Any]:
        """返回配置与 endpoint 装配摘要。"""
        return {
            "scenario_id": self.config.scenario_id,
            "config_name": self.config.config_name,
            "synthetic": self.config.synthetic,
            "server_count": len(self.config.servers),
            "endpoints": [
                {
                    "server_id": e.server.server_id,
                    "endpoint_id": e.endpoint.endpoint_id,
                    "protocol": e.endpoint.protocol,
                    "mode": e.mode,
                    "available": e.available,
                    "reason": e.reason,
                }
                for e in self.registry.entries
            ],
        }

    # ---------------- data plane ----------------

    def health(self, endpoint_id: str | None = None):
        """查询 endpoint 健康状态。"""
        if endpoint_id:
            return HealthSystemUseCase().execute(self.registry, endpoint_id=endpoint_id)
        return self.status()

    def read(self, point_ids=None, *, endpoint_id=None):
        """读取点位值。"""
        return ReadSystemUseCase().execute(
            self.registry,
            point_ids,
            endpoint_id=endpoint_id,
        )

    def write(self, point_id: str, value: Any, *, endpoint_id=None) -> None:
        """写入单点值。"""
        WriteSystemUseCase().execute(
            self.registry,
            point_id,
            value,
            endpoint_id=endpoint_id,
        )


__all__ = ["StarfishServerManager"]
