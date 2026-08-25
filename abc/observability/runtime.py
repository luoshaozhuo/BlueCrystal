"""连接 backend 与可选 instrumentation 的运行时 composition root。"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, ParamSpec, TypeVar, cast

from .audit import AuditService, SQLiteAuditStore
from .config import ObservabilityConfig, load_observability_config
from .context import initialize_runtime_context
from .instrumentation.base import Instrumentation
from .instrumentation.registry import InstrumentationRegistry
from .logs import configure_logging, get_logger
from .metrics import MetricsBackend
from .trace.backend import TracingBackend
from .status import (
    BackendStatus,
    RuntimeLifecycle,
    RuntimeStatus,
    WorkerStatusTracker,
)

P = ParamSpec("P")
R = TypeVar("R")


class ObservabilityRuntime:
    """管理 backend、instrumentation 组合及其幂等生命周期。"""

    def __init__(
        self,
        config: ObservabilityConfig,
    ) -> None:
        """按配置创建能力，但不隐式安装任何框架 instrumentation。"""
        self.config = config
        if config.logging.enabled:
            configure_logging(config.logging)
        self.metrics = (
            MetricsBackend(config.service, config.metrics)
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
        self._worker_status_tracker = (
            WorkerStatusTracker() if config.status.enabled else None
        )
        self._lifecycle_lock = Lock()
        self._lifecycle = RuntimeLifecycle.CREATED
        self.context = initialize_runtime_context(
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
        if self._current_lifecycle() is not RuntimeLifecycle.CREATED:
            raise RuntimeError(
                "instrumentation must be installed while runtime is created"
            )
        self._instrumentations.register(instrumentation)
        return instrumentation

    def instrument_fastapi(
        self,
        app: object,
    ) -> None:
        """按需安装 FastAPI adapter，并显式注入认证主体 resolver。

        Args:
            app: 待安装结构 instrumentation 的 FastAPI 对象。
            actor_resolver: 从框架请求解析可信认证主体的 Python callable；通用
                adapter 不会默认信任任意 HTTP header。

        Raises:
            ValueError: YAML options 试图提供运行期 callable 时抛出。
        """
        from .instrumentation.fastapi import FastAPIInstrumentation
        
        options = self.config.instrumentation.get_options("fastapi")
        fastapi_options = dict(options.options)
        adapter = FastAPIInstrumentation(
            app,
            enabled=True,
            **fastapi_options,
        )
        self.install(adapter)

    def instrument_apscheduler(self, scheduler: object) -> None:
        """按需安装 APScheduler listener adapter。"""
        from .instrumentation.apscheduler import APSchedulerInstrumentation

        options = self.config.instrumentation.get_options("apscheduler")

        adapter = cast(Any, APSchedulerInstrumentation)(
            scheduler,
            enabled=True,
            **options.options,
        )
        self.install(adapter)

    def instrument_worker(
        self,
        name: str,
        runner: Callable[P, R],
        *,
        options: Mapping[str, object] | None = None,
    ) -> Callable[P, R]:
        """包装同步或异步业务 Worker，同时保留其参数和返回契约。

        该方法将业务函数包装为带观测能力的 worker，保留原函数签名和返回值，
        但额外执行上下文绑定、日志、指标、链路记录等 instrumentation 逻辑。

        Args:
            name: Worker 的业务名称，用于日志、链路和度量中区分具体 worker。
                例子: "sync_orders", "daily_report", "ingest_event".
            runner: 要包装的原始业务函数。函数可以是同步或异步 callable，并保留
                其原有参数列表和返回值签名。
            options: 可覆盖或追加的 worker 配置项。它会和 YAML 中配置合并，options
                优先级更高，最终以显式调用参数覆盖配置文件。
                例子: {"timeout": 30, "retries": 2, "queue": "orders"}.

        Returns:
            包装后的 worker callable，调用方式与原 runner 保持一致。外部代码应继续
            按原函数签名调用，而不需要知道观测逻辑的细节。

        Notes:
            - 如果 worker instrumentation 在配置中被禁用，则直接返回原 runner。
            - wrapper 负责在执行前后绑定 observation context，并在失败时保留上下文。
            - 该实现不改变业务函数的契约，确保可以无缝替换原调用点。
        """
        from .instrumentation.task_runner import wrap_worker

        configured = self.config.instrumentation.get_options("worker")
        if not configured.enabled:
            return runner
        merged = {**configured.options, **dict(options or {})}
        # wrap_worker 是从动态导入的模块里拿到的，不一定被静态分析器准确推断出它的签名
        # 但代码和业务逻辑上，wrapper_factory(...) 最终确实返回一个可调用对象，且类型应当符合 Callable[P, R]
        # 所以用 cast 明确“我知道这里的类型是这个”，避免 mypy/pyright 报错
        wrapper_factory = cast(Any, wrap_worker)
        return cast(
            Callable[P, R],
            wrapper_factory(
                name,
                runner,
                runtime=self,
                status_tracker=self._worker_status_tracker,
                **merged,
            ),
        )

    async def start(self) -> None:
        """幂等启动已注册 adapter；失败时 registry 会逆序回滚。"""
        if not self._begin_start():
            return
        try:
            await self._instrumentations.start()
        except Exception:
            # instrumentation 已回滚结构；同时释放 backend，Runtime 不可复用。
            try:
                if self.tracing is not None:
                    self.tracing.close()
            finally:
                self._set_lifecycle(RuntimeLifecycle.CLOSED)
            raise
        self._set_lifecycle(RuntimeLifecycle.STARTED)

    async def close(self) -> None:
        """逆序卸载 adapter 并关闭 backend；重复关闭安全。"""
        if not self._begin_close():
            return
        try:
            await self._instrumentations.shutdown()
        finally:
            if self.tracing is not None:
                self.tracing.close()
            self._set_lifecycle(RuntimeLifecycle.CLOSED)

    shutdown = close

    def get_logger(self, name: str | None = None) -> object:
        """返回业务 Logger；基座不替业务代码定义日志事件。"""
        return get_logger(name)

    def status(self) -> RuntimeStatus:
        """返回可配置的 Runtime、backend、adapter 与 Worker 只读状态快照。"""
        enabled = self.config.status.enabled
        lifecycle = self._current_lifecycle()
        workers = (
            self._worker_status_tracker.worker_statuses()
            if self._worker_status_tracker
            else ()
        )
        return RuntimeStatus(
            enabled=enabled,
            lifecycle=lifecycle,
            backends=self._backend_statuses(lifecycle),
            instrumentations=self._instrumentations.statuses() if enabled else (),
            workers=workers,
            observed_at=datetime.now(timezone.utc),
        )

    def _backend_statuses(
        self,
        lifecycle: RuntimeLifecycle,
    ) -> tuple[BackendStatus, ...]:
        """汇总 backend 是否启用及其当前 Runtime 就绪状态。"""
        values = (
            ("logging", self.config.logging.enabled),
            ("metrics", self.metrics is not None),
            ("tracing", self.tracing is not None),
            ("audit", self.audit is not None),
        )
        def state(enabled: bool) -> str:
            """把 backend 启用状态与同一份 Runtime 生命周期快照合并。"""
            if not enabled:
                return "disabled"
            if lifecycle in {RuntimeLifecycle.CLOSING, RuntimeLifecycle.CLOSED}:
                return lifecycle.value
            return "ready"

        return tuple(BackendStatus(name, enabled, state(enabled)) for name, enabled in values)

    def _set_lifecycle(self, lifecycle: RuntimeLifecycle) -> None:
        """在线程安全边界内更新 Runtime 生命周期。"""
        with self._lifecycle_lock:
            self._lifecycle = lifecycle

    def _begin_start(self) -> bool:
        """原子进入启动阶段；已启动时返回 false，非法阶段拒绝重入。"""
        with self._lifecycle_lock:
            if self._lifecycle is RuntimeLifecycle.STARTED:
                return False
            if self._lifecycle is RuntimeLifecycle.CLOSED:
                raise RuntimeError("observability runtime is closed")
            if self._lifecycle is not RuntimeLifecycle.CREATED:
                raise RuntimeError(
                    f"observability runtime cannot start while {self._lifecycle.value}"
                )
            self._lifecycle = RuntimeLifecycle.STARTING
            return True

    def _begin_close(self) -> bool:
        """原子进入关闭阶段；已关闭或正在关闭时保持幂等。"""
        with self._lifecycle_lock:
            if self._lifecycle in {
                RuntimeLifecycle.CLOSED,
                RuntimeLifecycle.CLOSING,
            }:
                return False
            if self._lifecycle is RuntimeLifecycle.STARTING:
                raise RuntimeError("observability runtime is starting")
            self._lifecycle = RuntimeLifecycle.CLOSING
            return True

    def _current_lifecycle(self) -> RuntimeLifecycle:
        """在线程安全边界内读取 Runtime 生命周期。"""
        with self._lifecycle_lock:
            return self._lifecycle


def create_observability(
    config: ObservabilityConfig | str | Path,
) -> ObservabilityRuntime:
    """从配置对象或 YAML 路径创建未启动的 Runtime。"""
    resolved = (
        load_observability_config(config)
        if isinstance(config, (str, Path))
        else config
    )
    return ObservabilityRuntime(resolved)


def install_observability(
    config: ObservabilityConfig | str | Path,
    *,
    app: object | None = None,
    scheduler: object | None = None,
) -> ObservabilityRuntime:
    """创建 Runtime，并在宿主启动前安装实际存在的框架对象。

    Args:
        config: 观测配置对象或指向 YAML 文件的路径。支持两种来源：
            1) `ObservabilityConfig` 实例；
            2) 文件系统路径，随后由 `load_observability_config` 解析。
        app: 可选 FastAPI 应用对象。若传入，则会自动安装 FastAPI instrumentation，
            并将 runtime 挂到 `app.state.observability` 上，供后续请求处理访问。
        scheduler: 可选 APScheduler 调度器对象。若传入，则会自动安装
            APScheduler instrumentation，进入任务/触发器生命周期监控。

    Returns:
        已完成结构安装但尚未启动资源的 Runtime。调用方仍需显式执行
        `await runtime.start()` 才会真正开启 backend 和 instrumentation。

    Notes:
        - 这是一个“安装阶段”方法，不做尾部资源启动。
        - 适用于宿主应用在启动时提前挂载观测能力。
    """
    runtime = create_observability(config)

    if app is not None:
        state = getattr(app, "state", None)
        if state is None:
            raise TypeError("observability app target must expose state")
        if runtime.config.instrumentation.get_options("fastapi").enabled:
            runtime.instrument_fastapi(app)
        if runtime.config.status.enabled:
            from .status.fastapi import install_status_route

            install_status_route(app, runtime)
        setattr(state, "observability", runtime)

    if scheduler is not None:
        if runtime.config.instrumentation.get_options("apscheduler").enabled:
            runtime.instrument_apscheduler(scheduler)

    return runtime
