"""starfish 高层 server manager API。

本模块为 CLI 和其他消费者提供统一 manager 对象，外部只需要操作
`StarfishServerManager`，无需直接感知底层协议实现、注册表或配置加载细节。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from starfish.application import BuiltManager, LoadedConfig, StarfishServerManagerService
from starfish.application.use_cases import (
    HealthSystemUseCase,
    ReadSystemUseCase,
    StartSystemUseCase,
    StopSystemUseCase,
    WriteSystemUseCase,
)
from starfish.adapters.config.server_config_loader import ServerConfigJsonLoader
from starfish.adapters.drivers.factory import StarfishDriverFactory


class StarfishServerManager:
    """Starfish 对外 server 管理对象。"""

    def __init__(self, built_manager: BuiltManager) -> None:
        self._built_manager = built_manager
        self._started_entries: list[Any] = []

    @property
    def config(self) -> Any:
        """返回当前 manager 绑定的服务端配置。"""
        return self._built_manager.config

    @property
    def registry(self) -> Any:
        """返回底层驱动注册表。"""
        return self._built_manager.registry

    def describe(self) -> dict[str, Any]:
        """返回当前 manager 管理的 servers 结构描述。"""
        return {
            "scenario_id": self.config.scenario_id,
            "config_name": self.config.config_name,
            "synthetic": self.config.synthetic,
            "server_count": len(self.config.servers),
            "endpoints": [
                {
                    "server_id": entry.server.server_id,
                    "server_name": entry.server.server_name,
                    "endpoint_id": entry.endpoint.endpoint_id,
                    "protocol": entry.endpoint.protocol,
                    "mode": entry.mode,
                    "available": entry.available,
                    "reason": entry.reason,
                }
                for entry in self.registry.entries
            ],
        }

    def start(self) -> None:
        """启动全部可用 endpoint。"""
        if self._started_entries:
            return

        self._started_entries = StartSystemUseCase().execute(self.registry)

    def stop(self) -> None:
        """停止已启动 endpoint。"""
        StopSystemUseCase().execute(self.registry, self._started_entries)
        self._started_entries = []

    def status(self) -> dict[str, Any]:
        """返回聚合运行状态。"""
        return {
            "scenario_id": self.config.scenario_id,
            "config_name": self.config.config_name,
            "synthetic": self.config.synthetic,
            "server_count": len(self.config.servers),
            "endpoints": HealthSystemUseCase().execute(self.registry),
        }

    def health(self, endpoint_id: str | None = None) -> dict[str, Any]:
        """查询健康状态。"""
        if endpoint_id is None:
            return self.status()
        return HealthSystemUseCase().execute(self.registry, endpoint_id=endpoint_id)

    def read(
        self,
        point_ids: list[str] | None = None,
        *,
        endpoint_id: str | None = None,
    ) -> dict[str, Any]:
        """读取当前点位值。"""
        return ReadSystemUseCase().execute(
            self.registry,
            point_ids,
            endpoint_id=endpoint_id,
        )

    def write(
        self,
        point_id: str,
        value: Any,
        *,
        endpoint_id: str | None = None,
    ) -> None:
        """向单个 endpoint 写值。"""
        WriteSystemUseCase().execute(
            self.registry,
            point_id,
            value,
            endpoint_id=endpoint_id,
        )


def _default_service() -> StarfishServerManagerService:
    """创建默认运行时应用服务。

    API 层承担 composition root 职责，负责把 adapters 注入 application
    ports；application 层不直接依赖具体 driver 或文件 I/O 实现。
    """
    return StarfishServerManagerService(
        config_loader=ServerConfigJsonLoader(),
        driver_factory=StarfishDriverFactory(),
    )


def load_config(input_path: Path) -> LoadedConfig:
    """加载并校验服务端配置。"""
    return _default_service().load_config(input_path)


def build_manager(input_path: Path) -> BuiltManager:
    """构建 server manager 装配结果。"""
    return _default_service().build_manager(input_path)


def open_manager(input_path: Path) -> StarfishServerManager:
    """构建并返回统一高层 manager 对象。"""
    return StarfishServerManager(build_manager(input_path))


__all__ = ["StarfishServerManager", "load_config", "build_manager", "open_manager"]
