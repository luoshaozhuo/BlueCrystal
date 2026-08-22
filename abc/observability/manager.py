"""连接 backend 与可选 instrumentation 的运行时 composition root。"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, ParamSpec, TypeVar, cast

from prometheus_client import CollectorRegistry

from .audit import AuditService, SQLiteAuditStore
from .config import ObservabilityConfig, load_observability_config
from .context import initialize_runtime_context
from .instrumentation.base import Instrumentation
from .instrumentation.registry import InstrumentationRegistry
from .logs import configure_logging, get_logger
from .metrics import MetricsBackend
from .trace.backend import TracingBackend

P = ParamSpec("P")
R = TypeVar("R")


class ObservabilityRuntime:
    """管理 backend、instrumentation 组合及其幂等生命周期。"""

    def __init__(
        self,
        config: ObservabilityConfig,
        *,
        metrics_registry: CollectorRegistry | None = None,
    ) -> None:
        """按配置创建能力，但不隐式安装任何框架 instrumentation。"""
        self.config = config
        if config.logging.enabled:
            configure_logging(config.logging)
        self.metrics = (
            MetricsBackend(config.metrics, metrics_registry)
            if config.metrics.enabled
            else None
        )
        self.tracing = (
            TracingBackend(config.service, config.tracing)
            if config.tracing.enabled
            else None
        )
        self.audit = self._create_audit(config)
        self._instrumentations = InstrumentationRegistry(self)
        self._started = False
        self._closed = False
        initialize_runtime_context(
            service_name=config.service.name,
            service_instance_id=config.service.instance_id,
        )

    @staticmethod
    def _create_audit(config: ObservabilityConfig) -> AuditService | None:
        """创建默认 SQLite audit store，并拒绝不明确的 store 参数。"""
        if not config.audit.enabled:
            return None
        if config.audit.store != "sqlite":
            raise ValueError(f"audit.store: unsupported store {config.audit.store!r}")
        allowed = {"path"}
        unknown = set(config.audit.options).difference(allowed)
        if unknown:
            raise ValueError(
                "audit.options: unsupported keys: " + ", ".join(sorted(unknown))
            )
        path = config.audit.options.get("path", "./audit.sqlite3")
        if not isinstance(path, (str, Path)):
            raise ValueError("audit.options.path must be a filesystem path")
        return AuditService(SQLiteAuditStore(path))

    def install(self, instrumentation: Instrumentation) -> Instrumentation:
        """注册可扩展 instrumentation，并返回原实例便于调用方持有。"""
        if self._closed:
            raise RuntimeError("observability runtime is closed")
        self._instrumentations.register(instrumentation)
        return instrumentation

    def instrument_fastapi(self, app: object) -> Instrumentation:
        """按需安装 FastAPI adapter，根包不会提前导入 FastAPI。"""
        from .instrumentation.fastapi import FastAPIInstrumentation

        options = self.config.instrumentation.get_options("fastapi")
        adapter = cast(Any, FastAPIInstrumentation)(
            app, enabled=options.enabled, **options.options
        )
        return self.install(adapter)

    def instrument_apscheduler(self, scheduler: object) -> Instrumentation:
        """按需安装 APScheduler listener adapter。"""
        from .instrumentation.apscheduler import APSchedulerInstrumentation

        options = self.config.instrumentation.get_options("apscheduler")
        adapter = cast(Any, APSchedulerInstrumentation)(
            scheduler, enabled=options.enabled, **options.options
        )
        return self.install(adapter)

    def instrument_worker(
        self,
        name: str,
        runner: Callable[P, R],
        *,
        resolver: Callable[..., Mapping[str, object]] | None = None,
        options: Mapping[str, object] | None = None,
    ) -> Callable[P, R]:
        """包装同步或异步业务 Worker，同时保留其参数和返回契约。"""
        from .instrumentation.task_runner import wrap_worker

        configured = self.config.instrumentation.get_options("worker")
        if not configured.enabled:
            return runner
        merged = {**configured.options, **dict(options or {})}
        wrapper_factory = cast(Any, wrap_worker)
        return cast(
            Callable[P, R],
            wrapper_factory(name, runner, runtime=self, resolver=resolver, **merged),
        )

    async def start(self) -> None:
        """幂等启动已注册 adapter；失败时 registry 会逆序回滚。"""
        if self._closed:
            raise RuntimeError("observability runtime is closed")
        if self._started:
            return
        try:
            await self._instrumentations.start()
        except Exception:
            # instrumentation 已回滚结构；同时释放 backend，Runtime 不可复用。
            if self.tracing is not None:
                self.tracing.close()
            self._closed = True
            raise
        self._started = True

    async def close(self) -> None:
        """逆序卸载 adapter 并关闭 backend；重复关闭安全。"""
        if self._closed:
            return
        try:
            await self._instrumentations.shutdown()
        finally:
            if self.tracing is not None:
                self.tracing.close()
            self._started = False
            self._closed = True

    shutdown = close

    def get_logger(self, name: str | None = None) -> object:
        """返回业务 Logger；基座不替业务代码定义日志事件。"""
        return get_logger(name)


def create_observability(
    config: ObservabilityConfig | str | Path,
    *,
    metrics_registry: CollectorRegistry | None = None,
) -> ObservabilityRuntime:
    """从配置对象或 YAML 路径创建未启动的 Runtime。"""
    resolved = (
        load_observability_config(config)
        if isinstance(config, (str, Path))
        else config
    )
    return ObservabilityRuntime(resolved, metrics_registry=metrics_registry)


def install_observability(
    config: ObservabilityConfig | str | Path,
    *,
    app: object | None = None,
    scheduler: object | None = None,
) -> ObservabilityRuntime:
    """创建 Runtime，并在宿主启动前安装实际存在的框架对象。

    Args:
        config: 强类型配置或 YAML 路径。
        app: 可选 FastAPI 应用对象。
        scheduler: 可选 APScheduler 对象。

    Returns:
        已完成结构安装但尚未启动资源的 Runtime。
    """
    runtime = create_observability(config)
    if app is not None:
        runtime.instrument_fastapi(app)
        state = getattr(app, "state", None)
        if state is not None:
            state.observability = runtime
    if scheduler is not None:
        runtime.instrument_apscheduler(scheduler)
    return runtime
