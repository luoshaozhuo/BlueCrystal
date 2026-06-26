"""Server config 加载 port。

application 通过本 port 获取 StarfishServerConfig 加载结果，不直接依赖
JSON 文件读取、hash 复算或具体文件系统 adapter。
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from starfish.domain import LoadResult


class ConfigLoaderPort(Protocol):
    """服务端配置加载抽象。"""

    def load_server_config(self, file_path: str | Path) -> LoadResult:
        """加载并校验 server config。

        Args:
            file_path: server config 文件路径。

        Returns:
            加载结果和结构化校验明细。
        """
