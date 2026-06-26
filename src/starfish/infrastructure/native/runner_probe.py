"""Native runner 探查函数 —— probe_native_runner。

根据 NativeRunnerSpec 对二进制文件执行存在性、大小和可读性检查。
返回 (available, reason) 二元组，供 facade 的 probe 函数和 ServerRegistry 使用。

不负责：
- 执行二进制或验证功能正确性。
- 网络连通性检查。
- 协议语义验证。

安全边界：
- 不得 import seahorse / whale.ingest / whale.shared.source。
"""

from __future__ import annotations

import os

from starfish.infrastructure.native.runner_spec import NativeRunnerSpec


def probe_native_runner(spec: NativeRunnerSpec) -> tuple[bool, str]:
    """探查 native runner 二进制文件可用性。

    探查步骤（按序）：
        1. 检查 default_source_path 目录是否存在。
        2. 检查 binary_name 对应文件是否存在。
        3. 检查文件大小 >= min_binary_size（排除空文件或 stub 占位）。
        4. 检查文件是否可读（os.R_OK）。

    Args:
        spec: NativeRunnerSpec 实例，包含二进制文件名、默认路径和最小大小阈值。

    Returns:
        (True, reason) 当二进制可读且大小满足要求时；
        (False, reason) 当任一步骤不满足时，reason 包含具体失败原因。
    """
    binary_path = spec.default_source_path / spec.binary_name

    # 1. 目录存在性
    if not spec.default_source_path.exists():
        return (
            False,
            f"Native runner 目录不存在: {spec.default_source_path}"
        )

    if not spec.default_source_path.is_dir():
        return (
            False,
            f"路径不是目录: {spec.default_source_path}"
        )

    # 2. 文件存在性
    if not binary_path.exists():
        return (
            False,
            f"Native runner 二进制不存在: {binary_path}"
        )

    if not binary_path.is_file():
        return (
            False,
            f"路径不是普通文件: {binary_path}"
        )

    # 3. 文件大小检查（os.stat 获取 st_size）
    try:
        st_size = os.stat(binary_path).st_size
    except OSError as exc:
        return (
            False,
            f"无法获取文件信息 {binary_path}: {exc}"
        )

    if st_size < spec.min_binary_size:
        return (
            False,
            f"Native runner 二进制文件过小 ({st_size} bytes < {spec.min_binary_size} bytes), "
            f"可能是 stub 占位或损坏文件: {binary_path}"
        )

    # 4. 可读性检查
    if not os.access(binary_path, os.R_OK):
        return (
            False,
            f"Native runner 二进制不可读: {binary_path}"
        )

    return (
        True,
        f"Native runner 二进制可用: {binary_path} ({st_size} bytes)"
    )


__all__ = ["probe_native_runner"]
