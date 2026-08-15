"""ingest 运行时 source runtime config port。

负责 相关功能，包含并发模型、租约、fencing token、
异常传播和资源释放语义。
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class SourceRuntimeConfigData:
    """调度器使用的单源运行时配置。"""

    runtime_config_id: int
    source_id: str
    protocol: str
    acquisition_mode: str
    interval_ms: int
    enabled: bool


@dataclass(slots=True)
class ServerRuntimeConfigData:
    """描述从运行时配置解析的单个仿真服务器条目。"""

    endpoint_id: int
    ied_name: str
    asset_code: str
    asset_name: str
    ld_name: str
    application_protocol: str
    transport: str
    host: str | None
    port: int | None
    namespace_uri: str | None
    signal_profile_id: int


@dataclass(slots=True)
class SignalProfileItemRuntimeData:
    """描述从共享信号 profile 直接解析的单个信号条目。"""

    signal_profile_id: int
    ln_name: str | None
    do_name: str
    relative_path: str
    data_type: str
    unit: str | None


class SourceRuntimeConfigPort(Protocol):
    """加载 ingest 源的运行时调度配置。"""

    def list_enabled(self) -> list[SourceRuntimeConfigData]:
        """返回已启用的运行时配置。"""

    def list_servers(
        self,
        *,
        group_by: Sequence[str] = (),
        first_group_only: bool = False,
    ) -> list[ServerRuntimeConfigData]:
        """返回源仿真的服务器级运行时配置行。"""

    def list_profile_items(
        self,
        signal_profile_id: int,
    ) -> list[SignalProfileItemRuntimeData]:
        """返回单个信号 profile 的有序条目定义。"""
