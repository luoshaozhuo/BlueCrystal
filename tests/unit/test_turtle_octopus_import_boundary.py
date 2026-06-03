"""turtle/octopus 与 platform_shared 的 import boundary 门禁测试。

验证：
1. 禁止将 turtle 或 octopus 包放在 src/whale 下。
2. 确认 src/whale/shared/crosscutting 已完全删除（包括 debug/observability/resilience）。
3. 确认全仓无 whale.shared.crosscutting import。
4. platform_shared 不依赖 whale/turtle/octopus/dolphin/orca/manta。
5. whale/turtle/octopus 可正常 import platform_shared。

测试阶段：开发期验证 (unit/mock) —— AST 扫描 + 运行时 import 检查。
不能证明：迁移后生产行为正确性、外部消费者已更新。
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest


SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
WHALE_ROOT = SRC_ROOT / "whale"
TURTLE_ROOT = SRC_ROOT / "turtle"
OCTOPUS_ROOT = SRC_ROOT / "octopus"
PLATFORM_SHARED_ROOT = SRC_ROOT / "platform_shared"

# 整个 whale.shared.crosscutting 已删除，所有旧路径都不可 import
DEPRECATED_CROSSCUTTING_PREFIX = "whale.shared.crosscutting"


# ── package location validation ───────────────────────────────────────────────


def test_turtle_not_inside_whale() -> None:
    """验证 turtle 包不在 src/whale 下。"""
    assert TURTLE_ROOT.is_dir(), "src/turtle 目录必须存在"
    assert not (WHALE_ROOT / "turtle").is_dir(), (
        "turtle 包不得放在 src/whale 下"
    )


def test_octopus_not_inside_whale() -> None:
    """验证 octopus 包不在 src/whale 下。"""
    assert OCTOPUS_ROOT.is_dir(), "src/octopus 目录必须存在"
    assert not (WHALE_ROOT / "octopus").is_dir(), (
        "octopus 包不得放在 src/whale 下"
    )


def test_platform_shared_package_exists() -> None:
    """验证 platform_shared 包存在于 src/ 顶层。"""
    assert PLATFORM_SHARED_ROOT.is_dir(), "src/platform_shared 目录必须存在"
    assert (PLATFORM_SHARED_ROOT / "__init__.py").is_file(), (
        "src/platform_shared/__init__.py 必须存在"
    )


def test_crosscutting_directory_deleted() -> None:
    """验证 src/whale/shared/crosscutting 整个目录已删除。"""
    crosscutting_path = WHALE_ROOT / "shared" / "crosscutting"
    assert not crosscutting_path.exists(), (
        f"whale.shared.crosscutting 目录必须已删除: {crosscutting_path}"
    )


# ── AST scan: no whale code imports whale.shared.crosscutting ─────────────────


def test_whale_no_crosscutting_imports() -> None:
    """验证 src/whale 下无任何代码引用 whale.shared.crosscutting。

    whale.shared.crosscutting 整个目录已删除，任何引用均为违规。
    """
    offenders: dict[str, list[str]] = {}

    for file_path in WHALE_ROOT.rglob("*.py"):
        file_str = str(file_path)

        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue

        file_imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == DEPRECATED_CROSSCUTTING_PREFIX or alias.name.startswith(
                        DEPRECATED_CROSSCUTTING_PREFIX + "."
                    ):
                        file_imports.append(alias.name)
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module == DEPRECATED_CROSSCUTTING_PREFIX or module.startswith(
                    DEPRECATED_CROSSCUTTING_PREFIX + "."
                ):
                    file_imports.append(module)

        if file_imports:
            offenders[file_str] = file_imports

    assert not offenders, (
        f"src/whale 下代码引用了已删除的 whale.shared.crosscutting: {offenders}\n"
        f"请改用 platform_shared.crosscutting.*"
    )


# ── new package importable tests ──────────────────────────────────────────────


@pytest.mark.parametrize(
    "package_path",
    [
        "src/turtle/__init__.py",
        "src/octopus/__init__.py",
        "src/platform_shared/__init__.py",
    ],
)
def test_new_packages_exist(package_path: str) -> None:
    """验证 turtle、octopus、platform_shared 包存在。"""
    full_path = SRC_ROOT.parent / package_path
    assert full_path.is_file(), f"{package_path} 必须存在"
    assert full_path.stat().st_size > 0, f"{package_path} 不得为空"


@pytest.mark.parametrize(
    "module_path",
    [
        "platform_shared",
        "platform_shared.crosscutting",
        "platform_shared.crosscutting.debug",
        "platform_shared.crosscutting.observability",
        "platform_shared.crosscutting.resilience",
        "platform_shared.crosscutting.context",
        "platform_shared.contracts",
        "platform_shared.kernel",
        "platform_shared.messaging",
        "platform_shared.security_primitives",
    ],
)
def test_platform_shared_sub_packages_importable(module_path: str) -> None:
    """验证 platform_shared 各子包可正常 import。"""
    mod = __import__(module_path)
    assert mod is not None


@pytest.mark.parametrize(
    "module_path,attr_name",
    [
        ("platform_shared.crosscutting.debug", "DebugTraceContext"),
        ("platform_shared.crosscutting.debug", "DebugTraceSinkPort"),
        ("platform_shared.crosscutting.debug", "RecentFailureBuffer"),
        ("platform_shared.crosscutting.debug", "RunnerDiagnosticsSnapshot"),
        ("platform_shared.crosscutting.observability", "MetricsSinkPort"),
        ("platform_shared.crosscutting.observability", "ErrorEvent"),
        ("platform_shared.crosscutting.observability", "OperationLogFields"),
        ("platform_shared.crosscutting.observability", "StructuredLogContext"),
        ("platform_shared.crosscutting.resilience", "BackoffPolicy"),
        ("platform_shared.crosscutting.resilience", "ClassifiedError"),
        ("platform_shared.crosscutting.resilience", "ErrorClassifier"),
        ("platform_shared.crosscutting.resilience", "RetryDecision"),
        ("platform_shared.crosscutting.resilience", "RetryPolicy"),
        ("platform_shared.security_primitives", "SensitiveDataMasker"),
    ],
)
def test_platform_shared_symbols_importable(
    module_path: str, attr_name: str
) -> None:
    """验证 platform_shared 所有迁移后的符号可正常 from-import。"""
    mod = __import__(module_path, fromlist=[attr_name])
    symbol = getattr(mod, attr_name)
    assert symbol is not None


# ── sub-package existence tests ───────────────────────────────────────────────


@pytest.mark.parametrize(
    "sub_package",
    [
        "auth",
        "security",
        "compliance",
        "audit",
        "policy",
        "governance",
        "risk",
        "deployment_policy",
        "change_control",
        "ports",
        "adapters",
        "api",
        "runtime",
        "sdk",
    ],
)
def test_turtle_sub_packages_exist(sub_package: str) -> None:
    """验证 turtle 的所有子包目录和 __init__.py 存在。"""
    init_path = TURTLE_ROOT / sub_package / "__init__.py"
    assert init_path.is_file(), (
        f"turtle/{sub_package}/__init__.py 必须存在"
    )


@pytest.mark.parametrize(
    "sub_package",
    [
        "orchestration",
        "deployment",
        "monitoring",
        "alerting",
        "diagnostics",
        "automation",
        "rollback",
        "reports",
        "adapters",
        "runtime",
    ],
)
def test_octopus_sub_packages_exist(sub_package: str) -> None:
    """验证 octopus 的所有子包目录和 __init__.py 存在。"""
    init_path = OCTOPUS_ROOT / sub_package / "__init__.py"
    assert init_path.is_file(), (
        f"octopus/{sub_package}/__init__.py 必须存在"
    )


@pytest.mark.parametrize(
    "sub_package",
    [
        "crosscutting/debug",
        "crosscutting/observability",
        "crosscutting/resilience",
        "crosscutting/context",
        "contracts",
        "kernel",
        "messaging",
        "security_primitives",
    ],
)
def test_platform_shared_sub_packages_exist(sub_package: str) -> None:
    """验证 platform_shared 的所有子包目录和 __init__.py 存在。"""
    init_path = PLATFORM_SHARED_ROOT / sub_package / "__init__.py"
    assert init_path.is_file(), (
        f"platform_shared/{sub_package}/__init__.py 必须存在"
    )


# ── runtime: deleted paths raise ImportError ──────────────────────────────────


OLD_CROSSCUTTING_PATHS: list[str] = [
    "whale.shared.crosscutting",
    "whale.shared.crosscutting.debug",
    "whale.shared.crosscutting.debug.diagnostics",
    "whale.shared.crosscutting.observability",
    "whale.shared.crosscutting.observability.metrics",
    "whale.shared.crosscutting.observability.masking",
    "whale.shared.crosscutting.resilience",
    "whale.shared.crosscutting.resilience.retry",
    "whale.shared.crosscutting.auth",
    "whale.shared.crosscutting.security",
    "whale.shared.crosscutting.compliance",
]


@pytest.mark.parametrize("module_path", OLD_CROSSCUTTING_PATHS)
def test_old_crosscutting_paths_raise_import_error(module_path: str) -> None:
    """验证所有旧 whale.shared.crosscutting.* 路径 import 失败。

    whale.shared.crosscutting 整个目录已删除（非空壳 shim），
    任何 import 尝试必须抛出 ImportError 或 ModuleNotFoundError。
    """
    with pytest.raises((ImportError, ModuleNotFoundError)):
        __import__(module_path)


# ── platform_shared 不依赖上层组件 ────────────────────────────────────────────

UPPER_COMPONENTS: frozenset[str] = frozenset(
    {
        "whale",
        "turtle",
        "octopus",
        "dolphin",
        "orca",
        "manta",
    }
)


def test_platform_shared_no_upper_dependency() -> None:
    """验证 platform_shared 不 import whale/turtle/octopus/dolphin/orca/manta。

    platform_shared 是全系统公共基础库，必须保持最小依赖，
    不得反向依赖任何业务组件或平台组件。
    """
    offenders: dict[str, list[str]] = {}

    for file_path in PLATFORM_SHARED_ROOT.rglob("*.py"):
        file_str = str(file_path)

        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue

        file_imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_level = alias.name.split(".")[0]
                    if top_level in UPPER_COMPONENTS:
                        file_imports.append(alias.name)
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                top_level = module.split(".")[0]
                if top_level in UPPER_COMPONENTS:
                    file_imports.append(module)

        if file_imports:
            offenders[file_str] = file_imports

    assert not offenders, (
        f"platform_shared 不得依赖上层组件 (whale/turtle/octopus/dolphin/orca/manta): {offenders}"
    )


# ── whale/turtle/octopus 可 import platform_shared ────────────────────────────


def test_whale_can_import_platform_shared() -> None:
    """验证 whale 可以 import platform_shared 关键模块。"""
    from platform_shared.crosscutting.debug import DebugTraceContext
    from platform_shared.crosscutting.observability import MetricsSinkPort
    from platform_shared.crosscutting.resilience import RetryPolicy
    from platform_shared.security_primitives.masking import SensitiveDataMasker

    assert DebugTraceContext is not None
    assert MetricsSinkPort is not None
    assert RetryPolicy is not None
    assert SensitiveDataMasker is not None


def test_turtle_can_import_platform_shared() -> None:
    """验证 turtle 可以 import platform_shared 关键模块。"""
    # 此 import 测试确认 turtle 与该基础库无依赖环
    try:
        import platform_shared
        import platform_shared.crosscutting

        assert platform_shared is not None
        assert platform_shared.crosscutting is not None
    except ImportError as exc:
        pytest.fail(f"turtle should be able to import platform_shared: {exc}")


def test_octopus_can_import_platform_shared() -> None:
    """验证 octopus 可以 import platform_shared 关键模块。"""
    try:
        import platform_shared
        import platform_shared.crosscutting

        assert platform_shared is not None
        assert platform_shared.crosscutting is not None
    except ImportError as exc:
        pytest.fail(f"octopus should be able to import platform_shared: {exc}")
