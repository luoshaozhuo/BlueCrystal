"""starfish Native Runner 管理框架。

本包提供协议二进制 native runner 的探查、规格定义和子进程生命周期管理能力。
当前用途：为 OPC_UA / IEC104 / IEC61850 等依赖 C runner 的协议 backend
提供统一的 native binary 探查和进程管理接口。

本包不自行启动 protocol server，仅提供底层通用原语。

默认 binary 路径：src/starfish/infrastructure/native/bin/，各 backend 可通过环境变量覆盖。

安全边界：
- 不得 import seahorse / whale.ingest / whale.shared.source。
- 不连接生产二进制路径，所有路径由调用方显式传入。
"""

from __future__ import annotations

from pathlib import Path

from starfish.infrastructure.native.runner_spec import NativeRunnerSpec
from starfish.infrastructure.native.runner_probe import probe_native_runner
from starfish.infrastructure.native.process_handle import NativeProcessHandle


def default_native_bin_dir() -> Path:
    """返回 starfish native binary 默认目录的绝对路径。

    路径为 src/starfish/infrastructure/native/bin/，由调用方用于构建各协议
    C runner 的默认路径（backend 可通过环境变量覆盖）。

    Returns:
        src/starfish/infrastructure/native/bin/ 目录的绝对路径。
        non_existent_reason 由调用方自行判断。
    """
    return Path(__file__).resolve().parent / "bin"


__all__ = [
    "NativeRunnerSpec",
    "probe_native_runner",
    "NativeProcessHandle",
    "default_native_bin_dir",
]
