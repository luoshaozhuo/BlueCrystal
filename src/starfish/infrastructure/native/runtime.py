"""starfish native runner 启动辅助。

集中处理 native runner 的路径推导、动态库目录注入和二进制探测，
避免各协议 backend 重复实现一份近似逻辑。
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def starfish_root_from(module_file: str) -> Path:
    """根据模块文件路径返回 `src/starfish` 根目录。

    native backend 已从 adapters 迁入 infrastructure，不同 backend 的目录
    深度不再一致；按目录名向上查找可以避免路径层级变化影响 runner 定位。
    """
    path = Path(module_file).absolute()
    for parent in (path.parent, *path.parents):
        if parent.name == "starfish":
            return parent
    return path.parents[2]


def native_runner_env(binary_path: Path) -> dict[str, str]:
    """为 native runner 构造运行环境。

    当前重点是补齐 `LD_LIBRARY_PATH`，让同仓库内的动态库能被加载器发现。
    如果仓库内不存在动态库，本函数不会伪造可用性。
    """
    env = os.environ.copy()
    native_root = binary_path.parent.parent
    lib_dirs: list[str] = []

    try:
        for candidate in native_root.rglob("*.so*"):
            lib_dir = str(candidate.parent)
            if lib_dir not in lib_dirs:
                lib_dirs.append(lib_dir)
    except Exception:
        return env

    if lib_dirs:
        existing = env.get("LD_LIBRARY_PATH", "")
        env["LD_LIBRARY_PATH"] = ":".join(
            lib_dirs + ([existing] if existing else [])
        )

    return env


def probe_native_binary(
    binary_path: Path,
    *,
    display_name: str,
    min_size: int = 1,
) -> tuple[bool, str]:
    """探测 native binary 是否真正可运行。

    除了存在性和执行权限外，还会检查动态库依赖是否可解析。
    """
    try:
        st = os.stat(binary_path)
    except OSError:
        return False, f"{display_name} binary 不存在: {binary_path}"

    if st.st_size < min_size:
        return False, f"{display_name} binary 文件过小 ({st.st_size} bytes): {binary_path}"

    if not os.access(binary_path, os.X_OK):
        return False, f"{display_name} binary 无执行权限: {binary_path}"

    ldd_path = shutil.which("ldd")
    if ldd_path:
        result = subprocess.run(
            [ldd_path, str(binary_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=native_runner_env(binary_path),
            check=False,
        )
        merged_output = f"{result.stdout}\n{result.stderr}"
        if "not found" in merged_output:
            missing = sorted({
                line.strip().split("=>", 1)[0].strip()
                for line in merged_output.splitlines()
                if "not found" in line
            })
            return False, (
                f"{display_name} binary 缺少动态库依赖: {', '.join(missing)}"
            )

    return True, f"{display_name} binary 可用: {binary_path} ({st.st_size} bytes)"
__all__ = [
    "native_runner_env",
    "probe_native_binary",
    "starfish_root_from",
]
