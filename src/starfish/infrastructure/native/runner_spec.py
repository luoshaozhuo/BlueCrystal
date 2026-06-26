"""Native runner 规格定义 —— NativeRunnerSpec dataclass。

本模块定义 native runner 的元数据规格，供 runner_probe 和 process_handle 模块使用。
规格定义与协议无关，可被所有 native-runner facade 复用。

安全边界：
- 不得 import seahorse / whale.ingest / whale.shared.source。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class NativeRunnerSpec:
    """Native runner 二进制文件的元数据规格。

    描述一个 native C/Python runner 二进制的基本属性，
    供 probe_native_runner 探查和 NativeProcessHandle 管理子进程生命周期使用。

    不负责：实际二进制编译、路径解析、协议语义。

    Attributes:
        protocol: 归一化协议名（如 "OPC_UA"、"IEC104"）。
        binary_name: 二进制文件名（如 "iec104_simulator_server"）。
        default_source_path: 二进制文件的默认搜索目录绝对路径。
        ready_signal: 日志/输出中判定进程就绪的信号字符串，为空表示不需要。
        health_port: 进程就绪后监听的健康检查 TCP 端口，0 表示不需要。
        min_binary_size: 二进制文件的最小字节数，用于判断是否为有效可执行文件。
    """

    protocol: str = ""
    binary_name: str = ""
    default_source_path: Path = Path(".")
    ready_signal: str = ""
    health_port: int = 0
    min_binary_size: int = 1024


__all__ = ["NativeRunnerSpec"]
