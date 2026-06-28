"""Starfish runtime bootstrap workflow。

本模块承接原 builder/service 的应用编排职责：通过 port 加载
server 配置、处理校验失败，并创建 runtime context。具体 JSON loader、
driver factory 或协议 facade 的选择由外层 API/adapter 完成。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from starfish.application.ports import ConfigLoaderPort, DriverFactoryPort
from starfish.application.runtime import StarfishRuntimeContext, create_server_registry
from starfish.domain import StarfishServerConfig, ValidationResult


class ServerManagerBuildError(ValueError):
    """运行时装配失败异常。

    用于向 CLI 或其他入口稳定暴露“为什么无法进入 manager 装配阶段”，并在
    校验失败时附带结构化 `ValidationResult`，避免调用方为了打印错误明细
    再次重读同一份 config 文件。

    Args:
        message: 面向调用方的稳定错误摘要。
        validation: 可选的结构化校验明细。
    """

    def __init__(
        self,
        message: str,
        *,
        validation: ValidationResult | None = None,
    ) -> None:
        super().__init__(message)
        self.validation = validation


@dataclass(frozen=True)
class LoadedConfig:
    """Server config 加载结果。

    Args:
        config: 成功解析后的配置；校验失败时可能为 None。
        validation: 结构化校验明细。
    """

    config: StarfishServerConfig | None
    validation: ValidationResult

    @property
    def is_valid(self) -> bool:
        """返回是否可进入 manager 装配阶段。"""
        return self.config is not None and self.validation.is_valid


class BuildRuntimeContextWorkflow:
    """构建 Starfish runtime context 的组合用例。

    该 workflow 只依赖 application ports，保持 UseCase 层不直接依赖 adapter
    或 infrastructure 的具体实现。
    """

    def __init__(
        self,
        *,
        config_loader: ConfigLoaderPort,
        driver_factory: DriverFactoryPort,
    ) -> None:
        """初始化 workflow 依赖。

        Args:
            config_loader: server config 加载 port。
            driver_factory: endpoint driver 装配 port。
        """
        self._config_loader = config_loader
        self._driver_factory = driver_factory

    def load_config(self, config_path: Path) -> LoadedConfig:
        """加载并校验 server 配置。

        Args:
            config_path: server config JSON 文件路径。

        Returns:
            包含配置和校验结果的 `LoadedConfig`。
        """
        result = self._config_loader.load_server_config(config_path)
        return LoadedConfig(config=result.config, validation=result.validation)

    def execute(self, config_path: Path) -> StarfishRuntimeContext:
        """加载配置并创建 runtime context。

        Args:
            config_path: server config JSON 文件路径。

        Returns:
            application runtime kernel root。

        Raises:
            ServerManagerBuildError: 校验失败或 config 缺失，无法进入 runtime 阶段。
        """
        loaded = self.load_config(config_path)
        if loaded.config is None:
            raise ServerManagerBuildError("config 为 None", validation=loaded.validation)
        if not loaded.validation.is_valid:
            raise ServerManagerBuildError(
                f"校验失败 ({len(loaded.validation.errors)} 个错误)",
                validation=loaded.validation,
            )
        return StarfishRuntimeContext(
            config=loaded.config,
            validation=loaded.validation,
            registry=create_server_registry(loaded.config, self._driver_factory),
        )


__all__ = [
    "BuildRuntimeContextWorkflow",
    "LoadedConfig",
    "ServerManagerBuildError",
]
