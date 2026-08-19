"""可观测性实现与参考包的开发期导入契约测试。

测试通过 Python 导入系统和 AST 静态扫描验证包入口、旧绝对路径清理、包内
引用及公开导出。示例应用导入测试仅在临时目录初始化本地 adapter，不调用外部
服务，因而不证明生产 observability 链路可用。
"""

from __future__ import annotations

import ast
import importlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

REFERENCE_PACKAGE = "observability_reference"
PRODUCTION_PACKAGE = "observability"
LEGACY_PACKAGE = "deploy.observability"
REFERENCE_ROOT = Path(__file__).resolve().parents[2] / "abc" / "observability_reference"
PRODUCTION_ROOT = REFERENCE_ROOT.parent / PRODUCTION_PACKAGE
PUBLIC_MODULES = (
    f"{REFERENCE_PACKAGE}.shared",
    f"{REFERENCE_PACKAGE}.logs",
    f"{REFERENCE_PACKAGE}.metrics",
    f"{REFERENCE_PACKAGE}.diagnostics",
    f"{REFERENCE_PACKAGE}.audit",
    f"{REFERENCE_PACKAGE}.instrumentation",
)
EXPECTED_REFERENCE_MODULE_COUNT = 37
EXPECTED_REFERENCE_AUDIT_EXPORTS = frozenset(
    {
        "ActorResolver",
        "AuditContext",
        "AuditQuery",
        "AuditRecord",
        "AuditResult",
        "AuditService",
        "AuditSpec",
        "AuditStore",
        "audit_action",
        "bind_audit_context",
        "get_audit_context",
        "get_audit_spec",
        "install_fastapi_audit",
    }
)


def _reference_module_name(source_path: Path) -> str:
    """把参考包源码路径转换为可导入的模块名。

    Args:
        source_path: 位于参考包目录内的 Python 源码。

    Returns:
        与 setuptools 包发现结果一致的稳定模块名。
    """
    relative_path = source_path.relative_to(REFERENCE_ROOT)
    if relative_path.name == "__init__.py":
        parts = relative_path.parent.parts
    else:
        parts = relative_path.with_suffix("").parts
    return ".".join((REFERENCE_PACKAGE, *parts))


def _reference_source_modules() -> set[str]:
    """返回当前工作树中实际存在的全部参考包模块。"""
    return {
        _reference_module_name(source_path)
        for source_path in REFERENCE_ROOT.rglob("*.py")
    }


def test_observability_reference_all_modules_import_without_pythonpath(
    tmp_path: Path,
) -> None:
    """真实安装环境应能导入全部模块并显式关闭示例持有的资源。

    子进程在临时目录运行并移除 ``PYTHONPATH``，防止仓库当前目录掩盖包发现
    错误。v3 示例仍在导入时装配本地 adapter，测试将其限制在临时目录，并在
    子进程退出前显式关闭 SQLite 与日志句柄。

    Args:
        tmp_path: pytest 提供的隔离工作目录。
    """
    module_names = sorted(_reference_source_modules())
    command = (
        "import importlib,json; "
        f"names=json.loads({json.dumps(json.dumps(module_names))}); "
        "modules={name:importlib.import_module(name) for name in names}; "
        "example=modules['observability_reference.observability_example_app_v3']; "
        "example.audit.close(); example.logs.close(); "
        "print(len(names))"
    )
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)

    completed = subprocess.run(
        [sys.executable, "-c", command],
        cwd=tmp_path,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert completed.returncode == 0, completed.stderr
    assert len(module_names) == EXPECTED_REFERENCE_MODULE_COUNT
    assert completed.stdout.strip() == str(EXPECTED_REFERENCE_MODULE_COUNT)


def test_observability_reference_audit_exports_resolve() -> None:
    """Audit 参考入口应准确转发 canonical 包当前仍提供的契约。"""
    reference_audit = importlib.import_module(f"{REFERENCE_PACKAGE}.audit")
    canonical_audit = importlib.import_module(f"{PRODUCTION_PACKAGE}.audit")

    assert frozenset(reference_audit.__all__) == EXPECTED_REFERENCE_AUDIT_EXPORTS
    assert all(hasattr(reference_audit, name) for name in reference_audit.__all__)
    for name in canonical_audit.__all__:
        assert getattr(reference_audit, name) is getattr(canonical_audit, name)


def test_observability_audit_does_not_load_optional_composition_dependencies() -> None:
    """导入独立 Audit 能力不应加载生产组合根或 Metrics FastAPI 集成。"""
    command = (
        "import sys; import observability.audit; "
        "assert 'observability.runtime' not in sys.modules; "
        "assert 'observability.metrics.fastapi' not in sys.modules"
    )

    completed = subprocess.run(
        [sys.executable, "-c", command],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert completed.returncode == 0, completed.stderr


def test_observability_root_factory_constructs_and_closes_runtime(
    tmp_path: Path,
) -> None:
    """标准安装应能访问组合根，并在隔离目录构造和关闭最小运行时。

    Args:
        tmp_path: 隔离日志与 SQLite Audit 文件的临时目录。
    """
    command = """
import logging
import os
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
import observability
from observability.logs import LoggingRuntime


def open_fd_count(path: Path) -> int:
    expected = path.resolve()
    count = 0
    for entry in Path("/proc/self/fd").iterdir():
        try:
            target = Path(os.readlink(entry)).resolve()
        except OSError:
            continue
        if target == expected:
            count += 1
    return count


root_logger = logging.getLogger()
host_handler = logging.StreamHandler(StringIO())
root_logger.addHandler(host_handler)
runtime = None
try:
    class FailingOwnedHandler(logging.Handler):
        def __init__(self) -> None:
            super().__init__()
            self.flush_calls = 0
            self.close_calls = 0

        def emit(self, record: logging.LogRecord) -> None:
            return None

        def flush(self) -> None:
            self.flush_calls += 1
            if self.flush_calls == 1:
                raise RuntimeError("expected flush failure")

        def close(self) -> None:
            self.close_calls += 1
            if self.close_calls == 1:
                raise ValueError("expected close failure")
            super().close()

    failing_handler = FailingOwnedHandler()
    root_logger.addHandler(failing_handler)
    failing_runtime = LoggingRuntime(root_logger, (failing_handler,))
    try:
        failing_runtime.close()
    except BaseExceptionGroup as error_group:
        assert len(error_group.exceptions) == 2
    else:
        raise AssertionError("multiple cleanup failures were not aggregated")
    failing_runtime.close()
    assert failing_handler not in root_logger.handlers
    assert failing_handler.flush_calls == 1
    assert failing_handler.close_calls == 1

    formatter_failure_log = Path("formatter-failure/logs/ingest.jsonl")
    with patch(
        "observability.logs.config.RotatingFileHandler.setFormatter",
        side_effect=RuntimeError("expected formatter failure"),
    ):
        try:
            observability.create_observability(log_file=formatter_failure_log)
        except RuntimeError:
            pass
        else:
            raise AssertionError("formatter failure was not propagated")
    assert open_fd_count(formatter_failure_log) == 0
    assert host_handler in root_logger.handlers
    assert not host_handler._closed

    failed_log = Path("failed/logs/ingest.jsonl")
    with patch(
        "observability.runtime.configure_tracing",
        side_effect=RuntimeError("expected initialization failure"),
    ):
        try:
            observability.create_observability(log_file=failed_log)
        except RuntimeError:
            pass
        else:
            raise AssertionError("initialization failure was not propagated")
    assert open_fd_count(failed_log) == 0

    audit_failure_log = Path("audit-failure/logs/ingest.jsonl")
    audit_failure_file = Path("audit-failure/audit/audit.sqlite3")
    with patch(
        "observability.runtime.AuditService",
        side_effect=RuntimeError("expected AuditService failure"),
    ):
        try:
            observability.create_observability(
                log_file=audit_failure_log,
                audit_file=audit_failure_file,
            )
        except RuntimeError:
            pass
        else:
            raise AssertionError("AuditService failure was not propagated")
    assert open_fd_count(audit_failure_log) == 0
    assert open_fd_count(audit_failure_file) == 0
    assert host_handler in root_logger.handlers
    assert not host_handler._closed

    log_file = Path("logs/app.jsonl")
    audit_file = Path("audit/audit.sqlite3")
    runtime = observability.create_observability(
        log_file=log_file,
        audit_file=audit_file,
    )
    assert isinstance(runtime, observability.ObservabilityRuntime)
    assert open_fd_count(log_file) == 1
    assert open_fd_count(audit_file) == 1
    runtime.install_fastapi(FastAPI())
    runtime.close()
    runtime.close()

    assert open_fd_count(log_file) == 0
    assert open_fd_count(audit_file) == 0
    assert host_handler in root_logger.handlers
    assert not host_handler._closed
finally:
    if runtime is not None:
        runtime.close()
    root_logger.removeHandler(host_handler)
    host_handler.close()
"""
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)

    completed = subprocess.run(
        [sys.executable, "-c", command],
        cwd=tmp_path,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert completed.returncode == 0, completed.stderr


def _module_package(source_path: Path) -> str:
    """返回生产源码执行相对导入时所属的包名。

    Args:
        source_path: 生产可观测性包内的 Python 源码路径。

    Returns:
        供 ``importlib.util.resolve_name`` 使用的完整包名。
    """
    relative_parent = source_path.relative_to(PRODUCTION_ROOT).parent
    parts = (PRODUCTION_PACKAGE, *relative_parent.parts)
    return ".".join(part for part in parts if part != ".")


def _assert_production_module_exists(module_name: str, source_path: Path) -> None:
    """断言生产包内导入目标对应真实模块或子包。

    Args:
        module_name: 已解析为绝对名称的导入目标。
        source_path: 声明该导入的源码路径，用于失败定位。
    """
    if module_name == PRODUCTION_PACKAGE:
        target = PRODUCTION_ROOT / "__init__.py"
        assert target.is_file(), source_path
        return
    if not module_name.startswith(f"{PRODUCTION_PACKAGE}."):
        return

    relative_parts = module_name.split(".")[1:]
    module_path = PRODUCTION_ROOT.joinpath(*relative_parts).with_suffix(".py")
    package_path = PRODUCTION_ROOT.joinpath(*relative_parts, "__init__.py")
    assert module_path.is_file() or package_path.is_file(), (
        f"{source_path.relative_to(PRODUCTION_ROOT)} 引用了不存在的本地模块 {module_name}"
    )


@pytest.mark.parametrize("module_name", (REFERENCE_PACKAGE, *PUBLIC_MODULES))
def test_observability_reference_public_modules_import(module_name: str) -> None:
    """新包根入口及关键能力模块应能通过稳定路径导入。"""
    module = importlib.import_module(module_name)
    assert module.__name__ == module_name


def test_observability_reference_has_no_unstable_absolute_imports() -> None:
    """参考包源码不得残留旧路径或受标准库 ``abc`` 影响的包路径。"""
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
                if name == LEGACY_PACKAGE
                or name.startswith(f"{LEGACY_PACKAGE}.")
                or name == "deploy.observability_reference"
                or name.startswith("deploy.observability_reference.")
                or name == "abc.observability_reference"
                or name.startswith("abc.observability_reference.")
            )
        if legacy_imports:
            offenders[str(source_path.relative_to(REFERENCE_ROOT))] = legacy_imports

    assert not offenders, f"参考包仍引用不稳定 observability 路径: {offenders}"


def test_observability_production_sources_have_no_legacy_imports() -> None:
    """迁移后的生产源码不得继续引用已不存在的 deploy.observability。"""
    offenders: dict[str, list[str]] = {}
    for source_path in PRODUCTION_ROOT.rglob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        legacy_imports = [
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module is not None
            and (
                node.module == LEGACY_PACKAGE
                or node.module.startswith(f"{LEGACY_PACKAGE}.")
            )
        ]
        if legacy_imports:
            offenders[str(source_path.relative_to(PRODUCTION_ROOT))] = legacy_imports

    assert not offenders, f"生产可观测性源码仍引用旧包路径: {offenders}"


def test_observability_production_does_not_import_reference_package() -> None:
    """Canonical 生产包不得反向依赖 reference 包。"""
    offenders: dict[str, list[str]] = {}
    for source_path in PRODUCTION_ROOT.rglob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        reverse_imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_names = tuple(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_names = (node.module or "",)
            else:
                continue
            reverse_imports.extend(
                name
                for name in imported_names
                if name == REFERENCE_PACKAGE
                or name.startswith(f"{REFERENCE_PACKAGE}.")
            )
        if reverse_imports:
            offenders[str(source_path.relative_to(PRODUCTION_ROOT))] = reverse_imports

    assert not offenders, f"生产包反向依赖 reference 包: {offenders}"


def test_observability_production_local_import_targets_exist() -> None:
    """生产源码的相对导入和 observability 绝对导入应指向真实模块。"""
    for source_path in PRODUCTION_ROOT.rglob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        package = _module_package(source_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.level:
                    relative_name = f"{'.' * node.level}{node.module or ''}"
                    module_name = importlib.util.resolve_name(relative_name, package)
                else:
                    module_name = node.module or ""
                _assert_production_module_exists(module_name, source_path)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    _assert_production_module_exists(alias.name, source_path)


@pytest.mark.parametrize("module_name", PUBLIC_MODULES)
def test_observability_reference_public_exports_resolve(module_name: str) -> None:
    """关键能力包声明的公开名称应存在且不重复。"""
    module = importlib.import_module(module_name)
    exported_names = tuple(module.__all__)
    assert exported_names
    assert len(exported_names) == len(set(exported_names))
    assert all(hasattr(module, exported_name) for exported_name in exported_names)
