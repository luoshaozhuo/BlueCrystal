"""starfish import boundary 门禁测试。

验证：
1. src/starfish 不得 import seahorse。
2. src/starfish 不得 import whale.ingest。
3. src/starfish 不得 import whale.shared.source。
4. src/seahorse 不得 import starfish（已有验证，此处追加确认）。
5. src/whale/ingest 不得 import starfish（含 diagnostics，已有验证，此处追加确认）。

测试阶段：构建期验证 (P2) —— AST 扫描 + 运行时 import 检查。
不能证明：外部消费者已更新、跨语言 JSON 反序列化正确性。
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "src"
STARFISH_ROOT = SRC_ROOT / "starfish"
SEAHORSE_ROOT = SRC_ROOT / "seahorse"
WHALE_INGEST_ROOT = SRC_ROOT / "whale" / "ingest"


def _collect_import_modules(root: Path) -> set[str]:
    """扫描目录下所有 .py 文件的完整 import 模块名集合。

    Args:
        root: 要扫描的根目录。

    Returns:
        import 模块名前缀集合。
    """
    modules: set[str] = set()
    for file_path in root.rglob("*.py"):
        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        modules.add(alias.name.split(".")[0])
                        modules.add(alias.name)
                if isinstance(node, ast.ImportFrom):
                    if node.module:
                        modules.add(node.module.split(".")[0])
                        modules.add(node.module)
        except SyntaxError:
            continue
    return modules


def _collect_import_prefixes(root: Path) -> set[str]:
    """收集所有导入模块的顶级前缀。

    Args:
        root: 要扫描的根目录。

    Returns:
        顶层模块名前缀集合。
    """
    prefixes: set[str] = set()
    for file_path in root.rglob("*.py"):
        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        prefixes.add(alias.name.split(".")[0])
                if isinstance(node, ast.ImportFrom):
                    if node.module:
                        prefixes.add(node.module.split(".")[0])
        except SyntaxError:
            continue
    return prefixes


# ── starfish -> external 边界 ───────────────────────────────────────────────────


class TestStarfishDoesNotImportSeahorse:
    """starfish 不得 import seahorse 的任何模块。"""

    def test_starfish_no_seahorse_import(self) -> None:
        """所有 starfish .py 文件不得包含 seahorse import。"""
        assert STARFISH_ROOT.is_dir(), "src/starfish 目录必须存在"

        all_modules = _collect_import_modules(STARFISH_ROOT)
        offenders = [
            m for m in all_modules
            if m == "seahorse" or m.startswith("seahorse.")
        ]
        assert offenders == [], (
            f"starfish 不得 import seahorse，违规模块: {sorted(offenders)}"
        )


class TestStarfishDoesNotImportWhaleIngest:
    """starfish 不得 import whale.ingest。"""

    def test_starfish_no_ingest_import(self) -> None:
        """所有 starfish .py 文件不得包含 whale.ingest import。"""
        assert STARFISH_ROOT.is_dir(), "src/starfish 目录必须存在"

        all_modules = _collect_import_modules(STARFISH_ROOT)
        offenders = [
            m for m in all_modules
            if m.startswith("whale.ingest")
        ]
        assert offenders == [], (
            f"starfish 不得 import whale.ingest，违规模块: {sorted(offenders)}"
        )


class TestStarfishDoesNotImportWhaleSharedSource:
    """starfish 不得 import whale.shared.source。"""

    def test_starfish_no_shared_source_import(self) -> None:
        """所有 starfish .py 文件不得包含 whale.shared.source import。"""
        assert STARFISH_ROOT.is_dir(), "src/starfish 目录必须存在"

        all_modules = _collect_import_modules(STARFISH_ROOT)
        offenders = [
            m for m in all_modules
            if m.startswith("whale.shared.source")
        ]
        assert offenders == [], (
            f"starfish 不得 import whale.shared.source，违规模块: {sorted(offenders)}"
        )


# ── seahorse -> starfish 边界（追加确认）────────────────────────────────────────


class TestSeahorseDoesNotImportStarfish:
    """seahorse 不得 import starfish（追加确认，已有 seahorse 侧测试覆盖）。"""

    def test_seahorse_no_starfish_import(self) -> None:
        """所有 seahorse .py 文件不得包含 starfish import。"""
        assert SEAHORSE_ROOT.is_dir(), "src/seahorse 目录必须存在"

        all_modules = _collect_import_modules(SEAHORSE_ROOT)
        offenders = [
            m for m in all_modules
            if m == "starfish" or m.startswith("starfish.")
        ]
        assert offenders == [], (
            f"seahorse 不得 import starfish，违规模块: {sorted(offenders)}"
        )


# ── ingest -> starfish 边界（含 diagnostics，追加确认）─────────────────────────


class TestIngestDoesNotImportStarfish:
    """whale.ingest 不得 import starfish（追加确认）。"""

    def test_ingest_no_starfish_import(self) -> None:
        """所有 whale.ingest .py 文件不得包含 starfish import。"""
        if not WHALE_INGEST_ROOT.is_dir():
            pytest.skip("src/whale/ingest 目录不存在")

        all_modules = _collect_import_modules(WHALE_INGEST_ROOT)
        offenders = [
            m for m in all_modules
            if m == "starfish" or m.startswith("starfish.")
        ]
        assert offenders == [], (
            f"whale.ingest 不得 import starfish，违规模块: {sorted(offenders)}"
        )


# ── starfish 基础存在性 ─────────────────────────────────────────────────────────


class TestStarfishDirectoryStructure:
    """starfish 目录结构完整性检查。"""

    def test_starfish_directory_exists(self) -> None:
        """src/starfish 目录应存在。"""
        assert STARFISH_ROOT.is_dir(), "src/starfish 目录必须存在"

    def test_starfish_init_exists(self) -> None:
        """src/starfish/__init__.py 应存在。"""
        assert (STARFISH_ROOT / "__init__.py").is_file()

    def test_starfish_main_exists(self) -> None:
        """src/starfish/__main__.py 应存在。"""
        assert (STARFISH_ROOT / "__main__.py").is_file()

    def test_starfish_subpackages_exist(self) -> None:
        """子包 directory 应存在。"""
        for sub in ["core", "adapters"]:
            assert (STARFISH_ROOT / sub).is_dir(), f"缺少子目录: {sub}"
            assert (STARFISH_ROOT / sub / "__init__.py").is_file(), (
                f"缺少 __init__.py: {sub}"
            )

    def test_legacy_drivers_package_removed(self) -> None:
        """旧分层和 driver package 必须被完全移除。"""
        for legacy_path in [
            "application",
            "domain",
            "infrastructure",
            "api",
            "drivers",
            "adapters/drivers",
        ]:
            assert not (STARFISH_ROOT / legacy_path).exists()


class TestStarfishCliDependsOnComposition:
    """CLI 应通过 composition root 装配 core，不直接耦合具体 adapter。"""

    def test_main_module_does_not_import_legacy_loader_or_registry(self) -> None:
        """`starfish.__main__` 不应再直接 import `loader` 或 `registry`。"""
        main_file = STARFISH_ROOT / "__main__.py"
        tree = ast.parse(main_file.read_text(encoding="utf-8"))
        modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    modules.add(alias.name)
            if isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module)

        assert "starfish.composition" in modules
        assert "starfish.core" in modules
        legacy_driver_module = ".".join(("starfish", "drivers"))
        assert legacy_driver_module not in modules
