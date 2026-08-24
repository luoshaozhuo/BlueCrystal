"""验证 YAML 配置解析契约与 import boundary。

测试使用临时 YAML 和本地环境变量，不证明任何远端 exporter 可用。
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

import pytest

import observability
from observability.config.loader import (
    ObservabilityConfigError,
    load_observability_config,
)
from observability.manager import ObservabilityRuntime

PACKAGE_ROOT = Path(__file__).parents[3] / "abc" / "observability"
REMOVED_MODULE_PATHS = frozenset(
    {
        "observability/bootstrap/",
        "observability/context/baggage.py",
        "observability/context/propagation.py",
        "observability/context/wrapper.py",
        "observability/events/",
        "observability/instrumentation/asyncio.py",
        "observability/instrumentation/scheduler_context.py",
        "observability/lifecycle/",
        "observability/metrics/definitions.py",
        "observability/metrics/scheduler.py",
        "observability/metrics/task.py",
        "observability/status/",
        "observability/trace/config.py",
        "observability/trace/decision.py",
        "observability/trace/dedup.py",
        "observability/trace/fingerprint.py",
        "observability/trace/manager.py",
        "observability/trace/policy.py",
        "observability/trace/sampler.py",
    }
)
REMOVED_MODULE_NAMES = frozenset(
    {
        "observability.bootstrap",
        "observability.context.baggage",
        "observability.context.propagation",
        "observability.context.wrapper",
        "observability.events",
        "observability.instrumentation.asyncio",
        "observability.instrumentation.scheduler_context",
        "observability.lifecycle",
        "observability.metrics.definitions",
        "observability.metrics.scheduler",
        "observability.metrics.task",
        "observability.status",
        "observability.trace.config",
        "observability.trace.decision",
        "observability.trace.dedup",
        "observability.trace.fingerprint",
        "observability.trace.manager",
        "observability.trace.policy",
        "observability.trace.sampler",
    }
)


def test_root_and_optional_submodules_import() -> None:
    """根包及已安装可选依赖对应子模块都应可独立导入。"""
    failures: list[str] = []
    for module in pkgutil.walk_packages(
        observability.__path__, observability.__name__ + "."
    ):
        try:
            importlib.import_module(module.name)
        except Exception as exc:
            failures.append(f"{module.name}: {type(exc).__name__}: {exc}")
    assert failures == []


def test_root_exports_only_current_public_contract() -> None:
    """根包只暴露已确认的新 Runtime、配置、日志、上下文和审计入口。"""
    assert frozenset(observability.__all__) == frozenset(
        {
            "ObservationContext",
            "ObservabilityConfig",
            "ObservabilityRuntime",
            "audit_action",
            "bind_observation_context",
            "create_observability",
            "get_observation_context",
            "get_logger",
            "install_observability",
            "load_observability_config",
        }
    )


def test_removed_modules_are_not_importable() -> None:
    """被新架构替代的模块必须从源码包发现结果中彻底消失。"""
    assert all(
        importlib.util.find_spec(module_name) is None
        for module_name in REMOVED_MODULE_NAMES
    )


def test_removed_modules_have_no_internal_or_documentation_references() -> None:
    """已删除模块名和过渡别名不得残留在生产源码或模块文档。"""
    forbidden_tokens = (
        "ObservabilityManager",
        "MetricsRegistry",
        "ObservedTaskRunner",
        "configure_trace",
        "install_http_observability",
        "install_scheduler_observability",
        "context.baggage",
        "context.propagation",
        "context.wrapper",
        "instrumentation.asyncio",
        "instrumentation.scheduler_context",
        "trace.config",
    )
    references: list[str] = []
    for path in PACKAGE_ROOT.rglob("*"):
        if path.suffix not in {".py", ".md", ".txt", ".yaml"}:
            continue
        content = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            if token in content:
                references.append(f"{path.relative_to(PACKAGE_ROOT)}: {token}")
    assert references == []


def test_built_wheel_excludes_removed_modules(tmp_path: Path) -> None:
    """从隔离源码构建真实 wheel，验证旧模块不会被 setuptools 重新打包。"""
    repository_root = PACKAGE_ROOT.parents[1]
    source_root = tmp_path / "source"
    (source_root / "abc").mkdir(parents=True)
    (source_root / "src").mkdir()
    shutil.copy2(repository_root / "pyproject.toml", source_root / "pyproject.toml")
    shutil.copy2(repository_root / "README.md", source_root / "README.md")
    shutil.copytree(
        PACKAGE_ROOT,
        source_root / "abc" / "observability",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    wheel_dir = tmp_path / "wheel"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            str(source_root),
            "--no-build-isolation",
            "--no-deps",
            "--wheel-dir",
            str(wheel_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr
    wheel_path = next(wheel_dir.glob("*.whl"))
    with zipfile.ZipFile(wheel_path) as archive:
        members = frozenset(archive.namelist())
    assert "observability/manager.py" in members
    assert "observability/trace/backend.py" in members
    assert "observability/config/observability.yaml" in members
    assert all(
        not any(member == removed or member.startswith(removed) for member in members)
        for removed in REMOVED_MODULE_PATHS
    )


def test_yaml_env_expansion_and_passthrough(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """环境变量替换后应保留第三方 options 的原生结构。"""
    monkeypatch.setenv("TEST_OTLP", "http://collector:4317")
    path = tmp_path / "observability.yaml"
    path.write_text(
        """
observability:
  service:
    name: worker-only
  logging:
    enabled: false
  metrics:
    enabled: false
  tracing:
    exporter_options:
      endpoint: ${TEST_OTLP}
      headers:
        authorization: ${TEST_TOKEN:-development-only}
  instrumentation:
    kafka:
      enabled: false
      options:
        topic: data
""",
        encoding="utf-8",
    )
    config = load_observability_config(path)
    assert config.tracing.exporter_options["endpoint"] == "http://collector:4317"
    assert config.tracing.exporter_options["headers"] == {
        "authorization": "development-only"
    }
    assert config.instrumentation.get_options("kafka").options == {"topic": "data"}


@pytest.mark.parametrize(
    "body, expected",
    [
        ("service: {name: demo, typo: true}", "typo"),
        ("service: {name: demo}\n  unknown: true", "unknown"),
        ("service: {name: demo}\n  tracing: {sample_rate: 2}", "sample_rate"),
    ],
)
def test_yaml_rejects_unknown_or_invalid_stable_fields(
    tmp_path: Path, body: str, expected: str
) -> None:
    """稳定字段拼写错误和非法采样率必须在启动前失败。"""
    path = tmp_path / "invalid.yaml"
    path.write_text(f"observability:\n  {body}\n", encoding="utf-8")
    with pytest.raises(ObservabilityConfigError, match=expected):
        load_observability_config(path)


def test_yaml_requires_declared_environment_variable(tmp_path: Path) -> None:
    """无默认值的缺失环境变量必须包含配置路径。"""
    path = tmp_path / "missing-env.yaml"
    path.write_text(
        "observability:\n  service:\n    name: ${UNSET_OBSERVABILITY_NAME}\n",
        encoding="utf-8",
    )
    with pytest.raises(ObservabilityConfigError, match="observability.service.name"):
        load_observability_config(path)


def test_yaml_resolves_sqlite_path_relative_to_config(tmp_path: Path) -> None:
    """SQLite 相对路径应以 YAML 目录为基准，避免依赖启动工作目录。"""
    config_dir = tmp_path / "deployment"
    config_dir.mkdir()
    path = config_dir / "observability.yaml"
    path.write_text(
        """
observability:
  service:
    name: relative-audit
  logging:
    enabled: false
  metrics:
    enabled: false
  tracing:
    enabled: false
  audit:
    enabled: true
    store: sqlite
    options:
      path: ../state/audit.sqlite3
""",
        encoding="utf-8",
    )
    config = load_observability_config(path)
    assert config.audit.options["path"] == str(
        (tmp_path / "state" / "audit.sqlite3").resolve()
    )


def test_console_exporter_rejects_runtime_controlled_output() -> None:
    """Console exporter 的当前进程输出流不得被 YAML options 覆盖。"""
    config = observability.ObservabilityConfig.model_validate(
        {
            "service": {"name": "console-conflict"},
            "logging": {"enabled": False},
            "metrics": {"enabled": False},
            "tracing": {
                "exporter": "console",
                "exporter_options": {"out": "not-a-stream"},
            },
        }
    )
    with pytest.raises(ValueError, match="runtime-controlled console key: out"):
        ObservabilityRuntime(config)


def test_fastapi_actor_resolver_accepts_builtin_string_modes() -> None:
    """YAML 可按内置策略选择 actor resolver，而不必提供 Python callable。"""
    config = observability.ObservabilityConfig.model_validate(
        {
            "service": {"name": "actor-resolver-selector"},
            "logging": {"enabled": False},
            "metrics": {"enabled": False},
            "tracing": {"enabled": False},
            "instrumentation": {
                "fastapi": {"options": {"actor_resolver": "x-user-or-actor"}}
            },
        }
    )
    runtime = ObservabilityRuntime(config)
    app = __import__("fastapi").FastAPI()
    runtime.instrument_fastapi(app)
    assert app.user_middleware


def test_fastapi_actor_resolver_rejects_unknown_builtin_mode() -> None:
    """未知 actor resolver 名称必须在启动前显式失败。"""
    config = observability.ObservabilityConfig.model_validate(
        {
            "service": {"name": "actor-resolver-unknown"},
            "logging": {"enabled": False},
            "metrics": {"enabled": False},
            "tracing": {"enabled": False},
            "instrumentation": {
                "fastapi": {"options": {"actor_resolver": "not-a-mode"}}
            },
        }
    )
    runtime = ObservabilityRuntime(config)
    with pytest.raises(ValueError, match="unsupported actor resolver"):
        runtime.instrument_fastapi(__import__("fastapi").FastAPI())


@pytest.mark.parametrize(
    ("exporter", "exporter_options"),
    [
        ("none", {}),
        ("otlp_grpc", {"endpoint": "localhost:4317", "insecure": True}),
    ],
)
def test_non_console_trace_exporters_keep_construction_contract(
    exporter: str,
    exporter_options: dict[str, object],
) -> None:
    """Console 本地可见性扩展不得破坏 none 或 OTLP 构造和关闭。"""
    config = observability.ObservabilityConfig.model_validate(
        {
            "service": {"name": f"trace-{exporter}"},
            "logging": {"enabled": False},
            "metrics": {"enabled": False},
            "tracing": {
                "exporter": exporter,
                "exporter_options": exporter_options,
            },
        }
    )
    runtime = ObservabilityRuntime(config)
    assert runtime.tracing is not None
    runtime.tracing.close()
