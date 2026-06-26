"""starfish 高层 server manager API。

本模块为 CLI 和其他消费者提供统一 manager 对象，外部只需要操作
`StarfishServerManager`，无需直接感知底层协议实现、注册表或配置加载细节。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from starfish.application import BuiltManager, LoadedConfig, StarfishServerManagerService
from starfish.domain import DriverEntry


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

        started_entries: list[Any] = []
        current_entry: Any | None = None
        try:
            for current_entry in self.registry.entries:
                if not current_entry.available or current_entry.driver is None:
                    continue
                current_entry.driver.start()
                started_entries.append(current_entry)
        except Exception as exc:
            self._stop_entries(started_entries)
            endpoint_id = (
                current_entry.endpoint.endpoint_id if current_entry is not None else "unknown"
            )
            raise RuntimeError(f"启动 endpoint={endpoint_id} 失败: {exc}") from exc

        self._started_entries = started_entries

    def stop(self) -> None:
        """停止已启动 endpoint。"""
        self._stop_entries(self._started_entries)
        self._started_entries = []

    def status(self) -> dict[str, Any]:
        """返回聚合运行状态。"""
        return {
            "scenario_id": self.config.scenario_id,
            "config_name": self.config.config_name,
            "synthetic": self.config.synthetic,
            "server_count": len(self.config.servers),
            "endpoints": self.registry.health_all(),
        }

    def health(self, endpoint_id: str | None = None) -> dict[str, Any]:
        """查询健康状态。"""
        if endpoint_id is None:
            return self.status()
        # DriverEntry.driver 字段类型为 `ServerDriver | Any`（见
        # starfish.domain.driver），调用 .health() 时 mypy 推导出 Any。
        # ServerDriver.health() 实际返回 dict[str, Any]，此处 cast 仅做
        # 类型显式声明，不影响运行时行为。
        return cast(
            "dict[str, Any]",
            self._resolve_entry(endpoint_id).driver.health(),
        )

    def read(
        self,
        point_ids: list[str] | None = None,
        *,
        endpoint_id: str | None = None,
    ) -> dict[str, Any]:
        """读取当前点位值。"""
        if endpoint_id is not None:
            # 同 health()：DriverEntry.driver 字段类型为 `ServerDriver | Any`，
            # 推导为 Any；ServerDriver.read() 实际返回 dict[str, Any]，
            # 此处 cast 仅做类型显式声明，不影响运行时行为。
            return cast(
                "dict[str, Any]",
                self._resolve_entry(endpoint_id).driver.read(point_ids),
            )

        return {
            entry.endpoint.endpoint_id: entry.driver.read(point_ids)
            for entry in self._iter_available_entries()
        }

    def write(
        self,
        point_id: str,
        value: Any,
        *,
        endpoint_id: str | None = None,
    ) -> None:
        """向单个 endpoint 写值。"""
        self._resolve_entry(endpoint_id).driver.write(point_id, value)

    def _iter_available_entries(self) -> list[DriverEntry]:
        return [
            entry for entry in self.registry.entries
            if entry.available and entry.driver is not None
        ]

    def _resolve_entry(self, endpoint_id: str | None) -> DriverEntry:
        available_entries = self._iter_available_entries()
        if endpoint_id is None:
            if len(available_entries) != 1:
                raise ValueError("存在多个可用 endpoint，请显式传入 endpoint_id。")
            return available_entries[0]

        for entry in available_entries:
            if entry.endpoint.endpoint_id == endpoint_id:
                return entry
        raise ValueError(f"未找到可用 endpoint: {endpoint_id}")

    @staticmethod
    def _stop_entries(entries: list[Any]) -> None:
        for entry in reversed(entries):
            try:
                entry.driver.stop()
            except Exception:
                continue


def load_config(input_path: Path) -> LoadedConfig:
    """加载并校验服务端配置。"""
    return StarfishServerManagerService().load_config(input_path)


def build_manager(input_path: Path) -> BuiltManager:
    """构建 server manager 装配结果。"""
    return StarfishServerManagerService().build_manager(input_path)


def open_manager(input_path: Path) -> StarfishServerManager:
    """构建并返回统一高层 manager 对象。"""
    return StarfishServerManager(build_manager(input_path))


__all__ = ["StarfishServerManager", "load_config", "build_manager", "open_manager"]
