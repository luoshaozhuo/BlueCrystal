"""starfish 高层运行时 API。

本模块为 CLI 和其他消费者提供统一运行时对象，外部只需要操作
`StarfishRuntime`，无需直接感知底层协议实现、注册表或配置加载细节。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from starfish.application import BuiltRuntime, LoadedPlan, StarfishRuntimeService


class StarfishRuntime:
    """Starfish 统一运行时对象。"""

    def __init__(self, built_runtime: BuiltRuntime) -> None:
        self._built_runtime = built_runtime
        self._started_entries: list[Any] = []

    @property
    def plan(self) -> Any:
        """返回当前运行时绑定的计划。"""
        return self._built_runtime.plan

    @property
    def registry(self) -> Any:
        """返回底层驱动注册表。"""
        return self._built_runtime.registry

    def describe(self) -> dict[str, Any]:
        """返回运行时结构描述。"""
        return {
            "scenario_id": self.plan.scenario_id,
            "server_name": self.plan.server_name,
            "synthetic": self.plan.synthetic,
            "capabilities": list(self.plan.capabilities),
            "endpoints": [
                {
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
            "scenario_id": self.plan.scenario_id,
            "server_name": self.plan.server_name,
            "synthetic": self.plan.synthetic,
            "endpoints": self.registry.health_all(),
        }

    def health(self, endpoint_id: str | None = None) -> dict[str, Any]:
        """查询健康状态。"""
        if endpoint_id is None:
            return self.status()
        return self._resolve_entry(endpoint_id).driver.health()

    def read(
        self,
        point_ids: list[str] | None = None,
        *,
        endpoint_id: str | None = None,
    ) -> dict[str, Any]:
        """读取当前点位值。"""
        if endpoint_id is not None:
            return self._resolve_entry(endpoint_id).driver.read(point_ids)

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

    def _iter_available_entries(self) -> list[Any]:
        return [
            entry for entry in self.registry.entries
            if entry.available and entry.driver is not None
        ]

    def _resolve_entry(self, endpoint_id: str | None) -> Any:
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


class StarfishRuntimeApi:
    """Starfish 高层运行时 API。"""

    def __init__(self, service: StarfishRuntimeService) -> None:
        """初始化高层 API。

        Args:
            service: 负责底层用例编排的应用服务。
        """
        self._service = service

    def load_plan(self, input_path: Path) -> LoadedPlan:
        """加载并校验计划。

        Args:
            input_path: `starfish_server_plan.json` 文件路径。

        Returns:
            `LoadedPlan` 结果。
        """
        return self._service.load_plan(input_path)

    def build_runtime(self, input_path: Path) -> BuiltRuntime:
        """构建运行时。

        Args:
            input_path: `starfish_server_plan.json` 文件路径。

        Returns:
            `BuiltRuntime` 结果。
        """
        return self._service.build_runtime(input_path)

    def open_runtime(self, input_path: Path) -> StarfishRuntime:
        """构建并返回统一高层运行时对象。"""
        return StarfishRuntime(self.build_runtime(input_path))


def create_default_runtime_api() -> StarfishRuntimeApi:
    """创建默认运行时 API。

    Returns:
        绑定默认应用服务实现的 `StarfishRuntimeApi`。
    """
    return StarfishRuntimeApi(service=StarfishRuntimeService())


__all__ = ["StarfishRuntime", "StarfishRuntimeApi", "create_default_runtime_api"]
