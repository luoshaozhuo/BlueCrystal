"""Helpers for creating isolated shared persistence sample databases in tests.

测试阶段:跨模块联调期验证级隔离样例库,供 source_lab 等模块本地消费
统一输入契约。本文件不证明真实协议 runtime、simulator 或现场设备连通性。

环境变量约束:仅通过 ``WHALE_DB_URL`` 与子进程 ``sample_data`` 通信,
不再使用任何后端 / 路径等散环境变量。
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def create_shared_persistence_sample_db(tmp_path: Path) -> Path:
    """Create one isolated SQLite DB populated by sample_data."""

    repo_root = Path(__file__).resolve().parents[2]
    db_path = tmp_path / "shared-persistence-source-lab.sqlite"
    db_url = f"sqlite:///{db_path}"
    env = {
        **os.environ,
        "PYTHONPATH": str(repo_root / "src"),
        "WHALE_DB_URL": db_url,
    }
    subprocess.run(
        [sys.executable, "-m", "whale.shared.persistence.template.sample_data"],
        cwd=repo_root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return db_path