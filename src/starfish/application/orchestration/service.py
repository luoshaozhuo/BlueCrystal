"""starfish server manager 应用服务。

本模块显式承担 usecase/orchestration 角色：
- 组合文件加载驱动与运行时注册驱动。
- 统一处理配置加载、校验失败和 server manager 装配流程。
- 为 API/CLI 提供稳定的高层调用入口。

不负责：
- CLI 参数解析与终端输出格式。
- 协议细节实现。
- 原始 JSON 解析细节本身。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from starfish.application.ports import ConfigLoaderPort, DriverFactoryPort
from starfish.domain import StarfishServerConfig, ValidationResult
from starfish.application.orchestration.registry import ServerRegistry, create_server_registry


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


@dataclass(frozen=True)
class BuiltManager:
    """Server manager 装配结果。

    Args:
        config: 已通过校验的 server 配置。
        validation: 加载阶段校验结果。
        registry: 基于配置装配出的 server 注册表。
    """

    config: StarfishServerConfig
    validation: ValidationResult
    registry: ServerRegistry


class StarfishServerManagerService:
    """Starfish server manager 用例编排服务。"""

    def __init__(
        self,
        *,
        config_loader: ConfigLoaderPort,
        driver_factory: DriverFactoryPort,
    ) -> None:
        """初始化应用服务依赖。

        Args:
            config_loader: server config 加载 port。
            driver_factory: endpoint driver 装配 port。
        """
        self._config_loader = config_loader
        self._driver_factory = driver_factory

    def load_config(self, input_path: Path) -> LoadedConfig:
        """加载并校验 server 配置。

        Args:
            input_path: server config JSON 文件路径。

        Returns:
            包含配置和校验结果的 `LoadedConfig`。
        """
        result = self._config_loader.load_server_config(input_path)
        return LoadedConfig(config=result.config, validation=result.validation)

    def build_manager(self, input_path: Path) -> BuiltManager:
        """加载配置并创建 server manager。

        Args:
            input_path: server config JSON 文件路径。

        Returns:
            可供 API/CLI 使用的 manager 装配结果。

        Raises:
            ServerManagerBuildError: 校验失败或 config 缺失，无法进入 manager 阶段。
        """
        loaded = self.load_config(input_path)
        if loaded.config is None:
            raise ServerManagerBuildError("config 为 None", validation=loaded.validation)
        if not loaded.validation.is_valid:
            raise ServerManagerBuildError(
                f"校验失败 ({len(loaded.validation.errors)} 个错误)",
                validation=loaded.validation,
            )
        return BuiltManager(
            config=loaded.config,
            validation=loaded.validation,
            registry=create_server_registry(loaded.config, self._driver_factory),
        )


__all__ = ["LoadedConfig", "BuiltManager", "ServerManagerBuildError", "StarfishServerManagerService"]
