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


# ── Round 8 v4.1 对齐：controllers / drivers 收紧 ─────────────────────────


SEAHORSE_MAIN_FILE = SEAHORSE_ROOT / "__main__.py"


def _read_text(path: Path) -> str:
    """读取文件 UTF-8 文本，统一错误处理。

    Args:
        path: 目标文件绝对路径。

    Returns:
        文件正文文本。
    """
    return path.read_text(encoding="utf-8")


def test_seahorse_controllers_directory_removed() -> None:
    """src/seahorse/adapters/controllers 必须物理删除。

    v4.1 输入侧不再默认承载 CLI controller；CLI 收敛到 ``__main__.py``。
    """
    controllers_dir = SEAHORSE_ADAPTERS_ROOT / "controllers"
    assert not controllers_dir.exists(), (
        f"{controllers_dir} 应已被删除；CLI 不应放入 adapters/controllers。"
    )


def test_seahorse_adapters_has_no_controllers_subdir() -> None:
    """src/seahorse/adapters 下不应存在 controllers 子目录（名称层面）。"""
    if not SEAHORSE_ADAPTERS_ROOT.is_dir():
        pytest.skip(f"{SEAHORSE_ADAPTERS_ROOT} 不存在")
    current = {p.name for p in SEAHORSE_ADAPTERS_ROOT.iterdir() if p.is_dir()}
    assert "controllers" not in current, (
        f"seahorse/adapters 子目录仍含 controllers: {sorted(current)}"
    )


@pytest.mark.parametrize(
    "legacy_driver_file",
    [
        SEAHORSE_ADAPTERS_ROOT / "drivers" / "curve_generation.py",
        SEAHORSE_ADAPTERS_ROOT / "drivers" / "random_generation.py",
        SEAHORSE_ADAPTERS_ROOT / "drivers" / "replay_generation.py",
    ],
    ids=lambda p: p.name,
)
def test_seahorse_drivers_shim_generation_files_removed(
    legacy_driver_file: Path,
) -> None:
    """adapters/drivers 下不应残留 curve_generation / random_generation /
    replay_generation 等应用层生成策略 shim。

    这些是历史 driver adapter 兼容入口（已确认是 re-export shim），
    真实策略实现位于 ``seahorse.application.use_cases``；v4.1 收紧后
    不再保留于 ``adapters/drivers``。
    """
    assert not legacy_driver_file.exists(), (
        f"{legacy_driver_file} 应已被删除；真实策略实现位于 "
        "seahorse.application.use_cases。"
    )


def test_seahorse_main_does_not_import_application_adapters_infrastructure() -> None:
    """``__main__.py`` 不得 import ``seahorse.application`` /
    ``seahorse.adapters`` / ``seahorse.infrastructure``。

    薄入口必须只依赖 ``seahorse.api``（包括 ``seahorse_cli`` /
    ``seahorse_facade``）或同等 CLI 框架自身。
    """
    assert SEAHORSE_MAIN_FILE.is_file(), (
        f"{SEAHORSE_MAIN_FILE} 必须存在"
    )
    text = _read_text(SEAHORSE_MAIN_FILE)
    tree = ast.parse(text)
    forbidden_prefixes = (
        "seahorse.application",
        "seahorse.adapters",
        "seahorse.infrastructure",
    )
    offenders: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        module: str | None = None
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name
        elif isinstance(node, ast.ImportFrom):
            module = node.module
        if module is None:
            continue
        for prefix in forbidden_prefixes:
            if module == prefix or module.startswith(prefix + "."):
                offenders.append((str(SEAHORSE_MAIN_FILE), module))
                break
    assert offenders == [], (
        "__main__.py 不应 import seahorse.application / adapters / "
        f"infrastructure: {offenders}"
    )


def test_seahorse_main_does_not_create_backend_or_runtime() -> None:
    """``__main__.py`` 不得创建 backend / scheduler / repository / writer。

    薄入口仅解析命令行参数并调用 facade，构造与装配必须放在
    ``container.py`` 或 ``seahorse.api`` 内部。
    """
    assert SEAHORSE_MAIN_FILE.is_file(), (
        f"{SEAHORSE_MAIN_FILE} 必须存在"
    )
    text = _read_text(SEAHORSE_MAIN_FILE)
    forbidden_constructs = (
        "InMemoryStarfishWriterBackend",
        "InMemoryDataSourceRuntime",
        "DeterministicScheduler",
        "MonotonicClock",
        "WhaleMetadataRepository",
        "build_starfish_writer_gateway",
        "build_write_plan_use_case",
        "build_dispatch_write_batch_use_case",
        "build_runtime_smoke_workflow",
        "build_seahorse_facade",
    )
    offenders = [name for name in forbidden_constructs if name in text]
    assert offenders == [], (
        "__main__.py 不应直接构造 backend / scheduler / repository / writer "
        f"或调用 container.build_* 装配函数: {offenders}"
    )


def test_application_domain_do_not_import_adapters_infrastructure_api() -> None:
    """``seahorse.application`` / ``seahorse.domain`` 不得 import
    adapters / infrastructure / api。

    该断言在 v4.1 下继续生效：domain / application 只能依赖自身与
    ports；不允许穿越到 adapters / infrastructure / api。
    """
    offenders: list[tuple[str, Path]] = []
    for root in (SEAHORSE_DOMAIN_ROOT, SEAHORSE_APPLICATION_ROOT):
        if not root.is_dir():
            pytest.skip(f"{root} 不存在")
        modules = _collect_import_modules(root)
        for module in modules:
            if (
                module.startswith("seahorse.adapters")
                or module.startswith("seahorse.infrastructure")
                or module.startswith("seahorse.api")
            ):
                offenders.append((module, root))
    assert offenders == [], (
        "domain/application 不应 import adapters/infrastructure/api: "
        f"{offenders}"
    )


def test_seahorse_root_does_not_import_starfish() -> None:
    """``src/seahorse`` 任何模块均不得 import starfish。

    Round 8 复查：除 ``__init__.py`` 文档说明中显式声明"不得
    import starfish"的字符串外，AST 层面亦必须无真实 starfish
    import 语句。
    """
    assert SEAHORSE_ROOT.is_dir(), f"{SEAHORSE_ROOT} 必须存在"

    offenders: list[tuple[str, str]] = []
    for file_path in SEAHORSE_ROOT.rglob("*.py"):
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            module: str | None = None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name
            elif isinstance(node, ast.ImportFrom):
                module = node.module
            if module is None:
                continue
            if module == "starfish" or module.startswith("starfish."):
                offenders.append((str(file_path), module))
    assert offenders == [], (
        f"src/seahorse 不应 import starfish: {offenders}"
    )


# ── v4.2 蓝图：CLI 统一 Typer，且 CLI 只在 __main__.py ─────────────────────────


SEAHORSE_API_DIR = SEAHORSE_ROOT / "api"


def test_seahorse_api_has_no_cli_helper_files() -> None:
    """``src/seahorse/api`` 不得出现 ``*_cli.py`` / ``cli.py``。

    v4.2 蓝图 §5.3 api 白名单仅允许 ``__init__.py`` 与
    ``<package>_facade.py``；CLI 必须收敛到 ``__main__.py``。
    """
    if not SEAHORSE_API_DIR.is_dir():
        pytest.skip(f"{SEAHORSE_API_DIR} 不存在")

    offenders: list[Path] = []
    for file_path in SEAHORSE_API_DIR.iterdir():
        if not file_path.is_file():
            continue
        if file_path.suffix != ".py":
            continue
        if file_path.name in {"__init__.py", "seahorse_facade.py"}:
            continue
        offenders.append(file_path)
    assert offenders == [], (
        f"src/seahorse/api 下不应有 CLI helper / 控制器 / 额外 facade: "
        f"{[p.name for p in offenders]}"
    )


@pytest.mark.parametrize(
    "forbidden_name",
    ["seahorse_cli.py", "cli.py", "controllers.py"],
)
def test_seahorse_api_forbidden_filename_absent(forbidden_name: str) -> None:
    """``src/seahorse/api`` 不得出现 ``seahorse_cli.py`` /
    ``cli.py`` / ``controllers.py``。

    v4.2 蓝图 §5.3 明确禁止 ``api/<package>_cli.py`` /
    ``api/cli.py`` / ``api/controllers.py``。
    """
    if not SEAHORSE_API_DIR.is_dir():
        pytest.skip(f"{SEAHORSE_API_DIR} 不存在")
    target = SEAHORSE_API_DIR / forbidden_name
    assert not target.exists(), f"{target} 不应存在（v4.2 api 白名单禁止）"


def test_seahorse_main_uses_typer_not_argparse() -> None:
    """``__main__.py`` 必须使用 Typer，且不得使用 argparse。

    v4.2 蓝图 §5.2 / §8.1 / §11：CLI 统一 Typer，不允许 argparse。
    """
    assert SEAHORSE_MAIN_FILE.is_file(), f"{SEAHORSE_MAIN_FILE} 必须存在"
    text = SEAHORSE_MAIN_FILE.read_text(encoding="utf-8")
    assert "import typer" in text, "__main__.py 必须 import typer"
    assert "argparse" not in text, "__main__.py 不得 import 或使用 argparse"
    assert "ArgumentParser" not in text, "__main__.py 不得使用 argparse.ArgumentParser"


def test_seahorse_main_only_depends_on_typer_and_api() -> None:
    """``__main__.py`` 只允许依赖标准库 / typer / ``seahorse.api``。

    v4.2 蓝图 §2.1 / §5.2 / §9：CLI 薄入口只能 import api、Typer
    和标准库；不得 import domain / application / adapters /
    infrastructure，也不得 import 任何第三方 CLI 框架（click / argparse）。
    """
    import sys as _sys

    assert SEAHORSE_MAIN_FILE.is_file(), f"{SEAHORSE_MAIN_FILE} 必须存在"
    tree = ast.parse(SEAHORSE_MAIN_FILE.read_text(encoding="utf-8"))
    stdlib_names = set(_sys.stdlib_module_names)
    offenders: list[str] = []
    for node in ast.walk(tree):
        module: str | None = None
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module = node.module.split(".")[0]
        if not module:
            continue
        if module in stdlib_names:
            continue
        if module in {"typer", "seahorse", "__future__"}:
            continue
        offenders.append(module)
    assert offenders == [], (
        "__main__.py 只允许 import 标准库 / typer / seahorse；违规: "
        f"{sorted(set(offenders))}"
    )


def test_seahorse_main_forbids_inner_layer_imports() -> None:
    """``__main__.py`` AST 层面不得 import 内层模块。

    v4.2 蓝图 §2.1 / §9：CLI 薄入口禁止 import ``seahorse.domain`` /
    ``seahorse.application`` / ``seahorse.adapters`` /
    ``seahorse.infrastructure``。
    """
    assert SEAHORSE_MAIN_FILE.is_file(), f"{SEAHORSE_MAIN_FILE} 必须存在"
    tree = ast.parse(SEAHORSE_MAIN_FILE.read_text(encoding="utf-8"))
    forbidden_prefixes = (
        "seahorse.domain",
        "seahorse.application",
        "seahorse.adapters",
        "seahorse.infrastructure",
    )
    offenders: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        module: str | None = None
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name
        elif isinstance(node, ast.ImportFrom):
            module = node.module
        if module is None:
            continue
        for prefix in forbidden_prefixes:
            if module == prefix or module.startswith(prefix + "."):
                offenders.append((prefix, module))
                break
    assert offenders == [], (
        "__main__.py 不应 import 内层模块: "
        f"{sorted(set(module for _, module in offenders))}"
    )


def test_seahorse_main_does_not_construct_scenario_config_directly() -> None:
    """``__main__.py`` AST 层不得引用 ``ScenarioConfig``。

    v4.2 蓝图 §2.1.5：CLI 应以 primitives / Path / list / dict 传给
    Facade，由 Facade 在内部装配 domain model。docstring 中提到
    "ScenarioConfig" 仅作为规则说明，不算违规。
    """
    assert SEAHORSE_MAIN_FILE.is_file(), f"{SEAHORSE_MAIN_FILE} 必须存在"
    tree = ast.parse(SEAHORSE_MAIN_FILE.read_text(encoding="utf-8"))
    offenders: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "ScenarioConfig" or alias.name.endswith(".ScenarioConfig"):
                    offenders.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and (
                node.module == "ScenarioConfig"
                or node.module.endswith(".ScenarioConfig")
            ):
                offenders.append(node.module)
        if isinstance(node, ast.Name) and node.id == "ScenarioConfig":
            offenders.append(f"Name[{node.lineno}]")
        if isinstance(node, ast.Attribute) and node.attr == "ScenarioConfig":
            offenders.append(f"Attribute[{node.lineno}]")
    assert offenders == [], (
        "__main__.py AST 层不得引用 ScenarioConfig；"
        f"应通过 SeahorseFacade wrapper 间接装配 domain model。违规: {offenders}"
    )


def test_seahorse_main_does_not_create_backend_or_runtime() -> None:
    """``__main__.py`` 不得直接构造 backend / scheduler / repository / writer。

    v4.2 蓝图 §5.2：CLI 薄入口禁止构造 backend；装配只允许在
    ``container.py`` 或 facade 内部完成。
    """
    assert SEAHORSE_MAIN_FILE.is_file(), f"{SEAHORSE_MAIN_FILE} 必须存在"
    text = SEAHORSE_MAIN_FILE.read_text(encoding="utf-8")
    forbidden_constructs = (
        "InMemoryStarfishWriterBackend",
        "InMemoryDataSourceRuntime",
        "DeterministicScheduler",
        "MonotonicClock",
        "WhaleMetadataRepository",
        "build_starfish_writer_gateway",
        "build_write_plan_use_case",
        "build_dispatch_write_batch_use_case",
        "build_runtime_smoke_workflow",
        "build_seahorse_facade",
    )
    offenders = [name for name in forbidden_constructs if name in text]
    assert offenders == [], (
        "__main__.py 不应直接构造 backend / scheduler / repository / writer "
        f"或调用 container.build_*: {offenders}"
    )


def test_seahorse_facade_exposes_cli_wrapper_methods() -> None:
    """``SeahorseFacade`` 必须暴露 CLI 用的 primitives wrapper 方法。

    v4.2 蓝图 §2.1.5：CLI 不得直接构造 ``ScenarioConfig``，由 Facade
    wrapper 在内部装配。新增 wrapper：
    ``generate_bundle_from_cli_params`` /
    ``generate_minimal_server_config_from_cli_params``。
    """
    from seahorse.api.seahorse_facade import SeahorseFacade

    assert hasattr(SeahorseFacade, "generate_bundle_from_cli_params")
    assert hasattr(SeahorseFacade, "generate_minimal_server_config_from_cli_params")
    assert callable(SeahorseFacade.generate_bundle_from_cli_params)
    assert callable(SeahorseFacade.generate_minimal_server_config_from_cli_params)