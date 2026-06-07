"""seahorse / ingest / starfish import boundary 门禁测试。

验证：
1. src/whale/ingest 不得 import seahorse。
2. src/whale/ingest 不得 import starfish。
3. src/seahorse 不得 import whale.ingest。
4. src/seahorse/reference_data 不得依赖 whale ingest runtime。
5. src/seahorse 不得 import starfish 运行时模块。

测试阶段：构建期验证 (P2) —— AST 扫描 + 运行时 import 检查。
不能证明：迁移后生产行为正确性、外部消费者已更新。
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
WHALE_INGEST_ROOT = SRC_ROOT / "whale" / "ingest"
SEAHORSE_ROOT = SRC_ROOT / "seahorse"
SEAHORSE_REFDATA_ROOT = SEAHORSE_ROOT / "reference_data"
STARFISH_ROOT = SRC_ROOT / "starfish"


def _collect_imports(root: Path) -> set[str]:
    """扫描目录下所有 .py 文件的 import 语句，返回被导入模块前缀集合。"""
    prefixes: set[str] = set()
    for file_path in root.rglob("*.py"):
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    prefixes.add(alias.name.split(".")[0])
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    prefixes.add(node.module.split(".")[0])
    return prefixes


def _collect_import_modules(root: Path) -> set[str]:
    """扫描目录下所有 .py 文件的完整 import 模块名集合。"""
    modules: set[str] = set()
    for file_path in root.rglob("*.py"):
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    modules.add(node.module)
    return modules


# ── ingest → seahorse 边界 ────────────────────────────────────────────────────


def test_ingest_does_not_import_seahorse() -> None:
    """src/whale/ingest 生产代码不得 import seahorse。"""
    if not WHALE_INGEST_ROOT.is_dir():
        pytest.skip("src/whale/ingest 目录不存在")

    imports = _collect_imports(WHALE_INGEST_ROOT)
    offenders = [m for m in imports if m == "seahorse" or m.startswith("seahorse.")]
    assert offenders == [], f"ingest imports seahorse: {sorted(offenders)}"


def test_ingest_does_not_import_starfish() -> None:
    """src/whale/ingest 生产代码不得 import starfish。"""
    if not WHALE_INGEST_ROOT.is_dir():
        pytest.skip("src/whale/ingest 目录不存在")

    imports = _collect_imports(WHALE_INGEST_ROOT)
    offenders = [m for m in imports if m == "starfish" or m.startswith("starfish.")]
    assert offenders == [], f"ingest imports starfish: {sorted(offenders)}"


# ── seahorse → ingest 边界 ────────────────────────────────────────────────────


def test_seahorse_does_not_import_whale_ingest() -> None:
    """src/seahorse 不得 import whale.ingest。"""
    assert SEAHORSE_ROOT.is_dir(), "src/seahorse 目录必须存在"

    all_modules = _collect_import_modules(SEAHORSE_ROOT)
    offenders = [m for m in all_modules if m.startswith("whale.ingest")]
    assert offenders == [], f"seahorse imports whale.ingest: {sorted(offenders)}"


def test_seahorse_reference_data_does_not_depend_on_ingest_runtime() -> None:
    """seahorse/reference_data 不得直接或间接依赖 whale ingest runtime。

    检查所有 import 中是否包含 whale.ingest 前缀。
    """
    assert SEAHORSE_REFDATA_ROOT.is_dir(), "src/seahorse/reference_data 目录必须存在"

    all_modules = _collect_import_modules(SEAHORSE_REFDATA_ROOT)
    offenders = [m for m in all_modules if m.startswith("whale.ingest")]
    assert offenders == [], f"seahorse/reference_data imports whale.ingest: {sorted(offenders)}"


# ── seahorse → starfish 边界 ────────────────────────────────────────────────────


def test_seahorse_does_not_import_starfish() -> None:
    """src/seahorse 不得 import starfish 运行时模块。

    允许通过 JSON/dict schema 或纯 contract 模型与 Starfish 通信，
    但不得直接 import starfish Python 包。
    """
    assert SEAHORSE_ROOT.is_dir(), "src/seahorse 目录必须存在"

    all_modules = _collect_import_modules(SEAHORSE_ROOT)
    offenders = [m for m in all_modules if m == "starfish" or m.startswith("starfish.")]
    assert offenders == [], f"seahorse imports starfish: {sorted(offenders)}"


# ── 星鲨 (starfish) 基础存在性 ────────────────────────────────────────────────


def test_starfish_directory_exists() -> None:
    """验证 src/starfish 目录已创建并可导入。"""
    assert STARFISH_ROOT.is_dir(), "src/starfish 目录必须存在"
    # 确认可以 import starfish 包
    import starfish  # noqa: F401
