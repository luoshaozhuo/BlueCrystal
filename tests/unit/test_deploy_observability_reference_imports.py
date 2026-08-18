"""可观测性参考包重命名后的开发期导入契约测试。

测试通过 Python 导入系统和 AST 静态扫描验证新包入口、旧绝对路径清理及
公开导出，不调用 adapter 或外部服务，因而不证明生产 observability 链路可用。
"""

from __future__ import annotations

import ast
import importlib
import importlib.util
from pathlib import Path

import pytest

import deploy.observability_reference as observability_reference


REFERENCE_PACKAGE = "deploy.observability_reference"
LEGACY_PACKAGE = "deploy.observability"
REFERENCE_ROOT = Path(observability_reference.__file__).resolve().parent
PUBLIC_MODULES = (
    f"{REFERENCE_PACKAGE}.shared",
    f"{REFERENCE_PACKAGE}.logs",
    f"{REFERENCE_PACKAGE}.metrics",
    f"{REFERENCE_PACKAGE}.diagnostics",
    f"{REFERENCE_PACKAGE}.audit",
    f"{REFERENCE_PACKAGE}.instrumentation",
)


@pytest.mark.parametrize("module_name", (REFERENCE_PACKAGE, *PUBLIC_MODULES))
def test_observability_reference_public_modules_import(module_name: str) -> None:
    """新包根入口及关键能力模块应能通过稳定路径导入。"""
    module = importlib.import_module(module_name)
    assert module.__name__ == module_name


def test_observability_reference_has_no_legacy_imports() -> None:
    """参考包源码不得残留旧包绝对导入，旧包路径也不应继续存在。"""
    assert importlib.util.find_spec(LEGACY_PACKAGE) is None

    offenders: dict[str, list[str]] = {}
    for source_path in REFERENCE_ROOT.rglob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        legacy_imports: list[str] = []
        for node in ast.walk(tree):
            imported_names: tuple[str, ...]
            if isinstance(node, ast.Import):
                imported_names = tuple(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_names = (node.module or "",)
            else:
                continue
            legacy_imports.extend(
                name
                for name in imported_names
                if name == LEGACY_PACKAGE or name.startswith(f"{LEGACY_PACKAGE}.")
            )
        if legacy_imports:
            offenders[str(source_path.relative_to(REFERENCE_ROOT))] = legacy_imports

    assert not offenders, f"参考包仍引用旧 observability 路径: {offenders}"


@pytest.mark.parametrize("module_name", PUBLIC_MODULES)
def test_observability_reference_public_exports_resolve(module_name: str) -> None:
    """关键能力包声明的公开名称应存在且不重复。"""
    module = importlib.import_module(module_name)
    exported_names = tuple(module.__all__)
    assert exported_names
    assert len(exported_names) == len(set(exported_names))
    assert all(hasattr(module, exported_name) for exported_name in exported_names)
