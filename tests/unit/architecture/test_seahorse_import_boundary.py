"""seahorse / ingest / starfish import boundary 门禁测试。

验证：
1. src/whale/ingest 不得 import seahorse。
2. src/whale/ingest 不得 import starfish。
3. src/seahorse 不得 import whale.ingest。
4. src/seahorse 不得 import starfish 运行时模块。
5. seahorse/domain 与 application 不得 import adapters / infrastructure / api。
6. seahorse/domain 与 application 不得 import Whale persistence。
7. 旧顶层路径（models / exporters / strategies / generators /
   orchestration / ports / reference_data）必须不存在，且任何
   ``import seahorse.<legacy>`` 必须抛 ImportError。
8. ``StarfishWriterPort`` 与 ``BuildWriteBatchUseCase`` 不得暴露
   ``write_one`` 逐点写入热路径。
9. infrastructure 与 adapters 中不得出现 socket / subprocess /
   NativeRunner / ServerSimulatorFacade 等真实外部依赖语义。
10. 仓库内 ``src/`` 与 ``tests/unit/seahorse/``、``tests/unit/architecture``
    不得再 import 任何 ``seahorse.models`` / ``seahorse.exporters`` /
    ``seahorse.strategies`` / ``seahorse.generators`` /
    ``seahorse.orchestration`` / ``seahorse.ports`` /
    ``seahorse.reference_data`` 旧顶层包。

测试阶段：构建期验证 (P2) —— AST 扫描 + 运行时 import 检查。
不能证明：迁移后生产行为正确性、外部消费者已更新。
"""
from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "src"
TESTS_ROOT = PROJECT_ROOT / "tests"
WHALE_INGEST_ROOT = SRC_ROOT / "whale" / "ingest"
SEAHORSE_ROOT = SRC_ROOT / "seahorse"
SEAHORSE_DOMAIN_ROOT = SEAHORSE_ROOT / "domain"
SEAHORSE_APPLICATION_ROOT = SEAHORSE_ROOT / "application"
SEAHORSE_ADAPTERS_ROOT = SEAHORSE_ROOT / "adapters"
SEAHORSE_INFRASTRUCTURE_ROOT = SEAHORSE_ROOT / "infrastructure"
SEAHORSE_API_ROOT = SEAHORSE_ROOT / "api"
STARFISH_ROOT = SRC_ROOT / "starfish"

# Round 7B 硬清理目标：旧顶层目录必须物理删除，且不能再 import。
LEGACY_TOP_PACKAGES = (
    "seahorse.models",
    "seahorse.exporters",
    "seahorse.strategies",
    "seahorse.generators",
    "seahorse.orchestration",
    "seahorse.ports",
    "seahorse.reference_data",
)

LEGACY_TOP_DIRS = tuple(SEAHORSE_ROOT / name for name in LEGACY_TOP_PACKAGES)
for _name in LEGACY_TOP_PACKAGES:
    _ = _name  # 显式循环仅用于可读性，无副作用

# 需要扫描是否存在 ``seahorse.<legacy>`` import 的目录。
# Round 7C 把仓库内可能残留旧 ``seahorse.models`` /
# ``seahorse.exporters`` / ``seahorse.strategies`` /
# ``seahorse.generators`` / ``seahorse.orchestration`` /
# ``seahorse.ports`` / ``seahorse.reference_data`` import 的源/测试根
# 纳入扫描范围，跨 ``src/`` 与 ``tests/`` 子树统一硬约束。历史报告
# ``ai_shared/reports/`` 不参与 import 扫描，仅作归档。
LEGACY_SCAN_ROOTS = (
    SRC_ROOT,
    TESTS_ROOT,
)


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


def test_seahorse_domain_application_do_not_import_outer_layers() -> None:
    """domain/application 不得 import adapters 或 infrastructure。"""
    for root in (SEAHORSE_DOMAIN_ROOT, SEAHORSE_APPLICATION_ROOT):
        assert root.is_dir(), f"{root} 目录必须存在"
        modules = _collect_import_modules(root)
        offenders = [
            module
            for module in modules
            if module.startswith("seahorse.adapters")
            or module.startswith("seahorse.infrastructure")
            or module.startswith("seahorse.api")
        ]
        assert offenders == [], f"{root} imports outer layer: {sorted(offenders)}"


def test_seahorse_domain_application_do_not_import_whale_persistence() -> None:
    """domain/application 不得 import Whale persistence 或 Starfish runtime。"""
    modules = _collect_import_modules(SEAHORSE_DOMAIN_ROOT) | _collect_import_modules(
        SEAHORSE_APPLICATION_ROOT
    )
    offenders = [
        module
        for module in modules
        if module.startswith("whale.shared.persistence")
        or module == "starfish"
        or module.startswith("starfish.")
    ]
    assert offenders == [], f"domain/application forbidden imports: {sorted(offenders)}"


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


# ── 旧顶层路径硬清理边界（Round 7B） ─────────────────────────────────────────


@pytest.mark.parametrize("legacy_dir", LEGACY_TOP_DIRS, ids=lambda p: p.name)
def test_legacy_top_directories_removed(legacy_dir: Path) -> None:
    """旧顶层兼容目录必须物理删除。"""
    assert not legacy_dir.exists(), f"{legacy_dir} 应已被删除"


def _purge_legacy_module(name: str) -> None:
    targets = [
        key
        for key in list(sys.modules)
        if key == name or key.startswith(name + ".")
    ]
    for key in targets:
        sys.modules.pop(key, None)


@pytest.mark.parametrize("pkg", LEGACY_TOP_PACKAGES)
def test_legacy_top_packages_not_importable(pkg: str) -> None:
    """旧顶层包 import 必须抛 ImportError。"""
    _purge_legacy_module(pkg)
    with pytest.raises((ImportError, ModuleNotFoundError)):
        importlib.import_module(pkg)


@pytest.mark.parametrize(
    "scan_root", LEGACY_SCAN_ROOTS, ids=lambda p: p.name
)
def test_no_legacy_seahorse_imports_in_repo(scan_root: Path) -> None:
    """``src/`` 与 ``tests/`` 不得再 import 任何旧顶层 seahorse 路径。

    扫描 ``src/`` 与 ``tests/`` 下所有 ``.py`` 文件的 AST import 语句。
    命中即视为兼容层未彻底删除。
    """
    if not scan_root.is_dir():
        pytest.skip(f"{scan_root} 不存在")

    offenders: list[tuple[str, str]] = []
    for file_path in scan_root.rglob("*.py"):
        # 跳过被本测试自身的模块路径注入干扰
        text = file_path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            module: str | None = None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in LEGACY_TOP_PACKAGES:
                        module = alias.name
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module in LEGACY_TOP_PACKAGES:
                    module = node.module
            if module is not None:
                offenders.append((str(file_path), module))

    assert offenders == [], (
        f"{scan_root} 仍包含旧顶层 seahorse import: {offenders[:20]}"
    )


# ── hot path 边界 ─────────────────────────────────────────────────────────────


def test_starfish_writer_port_has_no_write_one() -> None:
    """StarfishWriterPort 不暴露逐点写入接口。"""
    from seahorse.application.ports.starfish_writer_port import StarfishWriterPort

    assert not hasattr(StarfishWriterPort, "write_one")


def test_build_write_batch_use_case_has_no_write_one() -> None:
    """BuildWriteBatchUseCase 不暴露逐点写入热路径。"""
    from seahorse.application.use_cases.atomic.build_write_batch import BuildWriteBatchUseCase

    assert not hasattr(BuildWriteBatchUseCase, "write_one")


def test_no_write_one_in_application_or_domain_or_runtime() -> None:
    """seahorse application/domain/runtime/adapters/infrastructure 不得定义 write_one。"""
    roots = (
        SEAHORSE_APPLICATION_ROOT,
        SEAHORSE_DOMAIN_ROOT,
        SEAHORSE_ADAPTERS_ROOT,
        SEAHORSE_INFRASTRUCTURE_ROOT,
    )
    offenders: list[tuple[str, str]] = []
    for root in roots:
        if not root.is_dir():
            continue
        for file_path in root.rglob("*.py"):
            tree = ast.parse(file_path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name == "write_one":
                        offenders.append((str(file_path), node.name))
                if isinstance(node, ast.ClassDef):
                    if node.name == "write_one":
                        offenders.append((str(file_path), node.name))
    assert offenders == [], f"出现 write_one 定义: {offenders}"


# ── 真实外部依赖边界 ──────────────────────────────────────────────────────────


def test_seahorse_avoids_socket_subprocess_native_runner_simulator_facade() -> None:
    """seahorse infrastructure/adapters/application 不得 import 真实外部依赖。"""
    forbidden = ("socket", "subprocess", "NativeRunner", "ServerSimulatorFacade")
    roots = (
        SEAHORSE_INFRASTRUCTURE_ROOT,
        SEAHORSE_ADAPTERS_ROOT,
        SEAHORSE_APPLICATION_ROOT,
    )
    offenders: list[tuple[str, str]] = []
    for root in roots:
        if not root.is_dir():
            continue
        for file_path in root.rglob("*.py"):
            tree = ast.parse(file_path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                targets: list[str] = []
                if isinstance(node, ast.Import):
                    targets.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        targets.append(node.module)
                for module in targets:
                    head = module.split(".")[0]
                    if head in forbidden or module in forbidden:
                        offenders.append((str(file_path), module))
    assert offenders == [], f"出现禁止的外部依赖 import: {offenders}"


# ── 星鲨 (starfish) 基础存在性 ────────────────────────────────────────────────


def test_starfish_directory_exists() -> None:
    """验证 src/starfish 目录已创建并可导入。"""
    assert STARFISH_ROOT.is_dir(), "src/starfish 目录必须存在"
    # 确认可以 import starfish 包
    import starfish  # noqa: F401


# ── Round 7C 扩展：whale.template / 全仓扫描 ─────────────────────────────────


def test_whale_template_does_not_import_seahorse_reference_data() -> None:
    """``src/whale/shared/persistence/template/`` 不再 import 旧 ``seahorse.reference_data``。

    Round 7B 删除了 ``seahorse.reference_data`` 顶层包；Round 7C 把
    ``whale.shared.persistence.template`` 改为自持真实数据或转发至
    ``whale.shared.persistence.views``，禁止再依赖已删除的兼容 wrapper。
    """
    template_root = SRC_ROOT / "whale" / "shared" / "persistence" / "template"
    if not template_root.is_dir():
        pytest.skip(f"{template_root} 不存在")

    offenders: list[tuple[str, str]] = []
    for file_path in template_root.rglob("*.py"):
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module == "seahorse.reference_data":
                    offenders.append((str(file_path), node.module))
                if node.module and node.module.startswith("seahorse.reference_data."):
                    offenders.append((str(file_path), node.module))
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "seahorse.reference_data":
                        offenders.append((str(file_path), alias.name))
                    if alias.name.startswith("seahorse.reference_data."):
                        offenders.append((str(file_path), alias.name))
    assert offenders == [], (
        "whale.shared.persistence.template 仍 import seahorse.reference_data: "
        f"{offenders}"
    )