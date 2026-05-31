"""基于 APScheduler 的 ingest worker 运行时。管理作业调度、心跳和指标。"""
# mypy: disable-error-code=import-untyped

from __future__ import annotations

import logging
import math
import threading
import time
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from whale.ingest.domain.audit_event import IngestAuditEvent
from whale.ingest.ports.audit import IngestAuditSinkPort
from whale.ingest.runtime.fencing import FencingTokenRepository, redact_fencing_token
from whale.ingest.runtime.job_assignment import (
    JobAssignmentRepository,
    RuntimeJobRepository,
)
from whale.ingest.runtime.lease import LeaseService
from whale.ingest.runtime.node_runtime import NodeRuntimeRepository
from whale.ingest.runtime.scheduler import SourceScheduler
from whale.ingest.runtime.scheduler_settings import SchedulerSettings
from whale.shared.persistence.orm.ingest_runtime import IngestRuntimeJob

_logger = logging.getLogger(__name__)

_JOB_STARTED = "job_started"
_JOB_COMPLETED = "job_completed"
_JOB_FAILED = "job_failed"
_JOB_HANDLER_NOT_FOUND = "job_handler_not_found"
_JOB_SKIPPED_NO_LEASE = "job_skipped_no_lease"
_LEASE_RENEWAL_SUCCESS = "lease_renewal_success"
_LEASE_RENEWAL_FAILED = "lease_renewal_failed"
_MISSED_TICK = "missed_tick"
_ASSIGNMENT_LAG_MS = "assignment_lag_ms"
_JOB_DURATION_MS = "job_duration_ms"


class JobHandler(Protocol):
    """WorkerRuntime 分发的作业类型 handler 协议。定义 execute 接口契约。"""

    def execute(self, job: IngestRuntimeJob) -> None:
        """执行一个作业。失败时抛出异常以记录 job_failed 指标。"""


class WorkerRuntimeMetrics:
    """Worker 运行时的最小内存指标计数器。跟踪执行次数、成功/失败数。"""

    def __init__(self) -> None:
        """初始化 worker 指标收集器。"""
        self._lock = threading.Lock()
        self._counters: dict[str, int] = {}
        self._gauges: dict[str, float] = {}
        self._samples: dict[str, list[float]] = {}

    def inc(self, name: str, value: int = 1) -> None:
        """递增计数器。"""
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + value

    def gauge(self, name: str, value: float) -> None:
        """设置仪表值。"""
        with self._lock:
            self._gauges[name] = value
            self._samples.setdefault(name, []).append(value)

    def snapshot(self) -> dict[str, int | float]:
        """获取指标快照。"""
        with self._lock:
            return {**self._counters, **self._gauges}

    def summary(self) -> dict[str, int | float]:
        """返回指标摘要。"""
        with self._lock:
            summary: dict[str, int | float] = {**self._counters, **self._gauges}
            for name, values in self._samples.items():
                if not values:
                    continue
                summary[f"{name}_p95"] = _percentile(values, 0.95)
                summary[f"{name}_p99"] = _percentile(values, 0.99)
            return summary


class WorkerRuntime:
    """基于 APScheduler 的 ingest worker 运行时。管理心跳、作业调和和指标。"""

    def __init__(
        self,
        *,
        settings: SchedulerSettings,
        node_repository: NodeRuntimeRepository,
        job_repository: RuntimeJobRepository,
        assignment_repository: JobAssignmentRepository,
        lease_service: LeaseService,
        fencing_token_repository: FencingTokenRepository,
        audit_sink: IngestAuditSinkPort | None = None,
        metrics: WorkerRuntimeMetrics | None = None,
        handlers: dict[str, JobHandler] | None = None,
    ) -> None:
        """初始化 worker 运行时。Args: settings: 配置实例。job_repository: 作业仓库。handler_registry: handler 注册字典。"""
        self._settings = settings
        self._node_repository = node_repository
        self._job_repository = job_repository
        self._assignment_repository = assignment_repository
        self._lease_service = lease_service
        self._fencing_token_repository = fencing_token_repository
        self._audit_sink = audit_sink
        self._metrics = metrics or WorkerRuntimeMetrics()
        self._handlers = handlers or {}

        self._scheduler = SourceScheduler(
            settings=settings,
            node_repository=node_repository,
            job_repository=job_repository,
            assignment_repository=assignment_repository,
            lease_service=lease_service,
            audit_sink=audit_sink,
        )

        self._aps = BackgroundScheduler(
            jobstores={"default": MemoryJobStore()},
            executors={"default": ThreadPoolExecutor(settings.pull_max_in_flight)},
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": settings.job_defaults.misfire_grace_time,
            },
            timezone=settings.timezone,
        )

        self._shutdown_event = threading.Event()
        self._started_at: datetime | None = None

    # ---- public API ---------------------------------------------------------

    @property
    def node_key(self) -> str:
        """获取当前节点标识键。"""
        return self._settings.node_key

    @property
    def metrics_snapshot(self) -> dict[str, int | float]:
        """获取指标快照字典。"""
        return self._metrics.snapshot()

    @property
    def metrics_summary(self) -> dict[str, int | float]:
        """返回当前 worker 运行指标摘要。"""
        return self._metrics.summary()

    def start(self) -> None:
        """启动心跳循环和 APScheduler 调和 tick。注册定期任务并开始调度。"""
        self._started_at = datetime.now(tz=UTC)

        # Heartbeat every N seconds
        self._aps.add_job(
            self._tick_heartbeat,
            trigger="interval",
            seconds=self._settings.heartbeat_interval_seconds,
            id="_worker_heartbeat",
            replace_existing=True,
            name="worker-heartbeat",
        )

        # Reconcile (assign + execute) every N seconds
        self._aps.add_job(
            self._tick_reconcile,
            trigger="interval",
            seconds=max(self._settings.heartbeat_interval_seconds, 5),
            id="_worker_reconcile",
            replace_existing=True,
            name="worker-reconcile",
        )

        self._aps.start()
        _logger.info(
            "WorkerRuntime started node=%s mode=%s heartbeat=%ds",
            self._settings.node_key,
            self._settings.runtime_mode.value,
            self._settings.heartbeat_interval_seconds,
        )

    def stop(self, *, timeout_seconds: int = 15) -> dict[str, int | float]:
        """优雅停止 worker 运行时。关闭调度器并清理资源。"""
        _logger.info("WorkerRuntime stopping node=%s", self._settings.node_key)
        self._shutdown_event.set()

        if self._aps.running:
            self._aps.shutdown(wait=False)

        # Release all active assignments for this node
        try:
            active_assignments = self._assignment_repository.list_active_assignments()
            owned_job_ids = [
                a.job_id for a in active_assignments if a.node_key == self._settings.node_key
            ]
            if owned_job_ids:
                self._scheduler.release_jobs(owned_job_ids)
                _logger.info(
                    "Released %d leases on shutdown node=%s",
                    len(owned_job_ids),
                    self._settings.node_key,
                )
        except Exception:
            _logger.exception("Error releasing leases during shutdown")

        self._emit_audit_event(
            action="worker.shutdown",
            resource_type="worker",
            resource_id=self._settings.node_key,
            decision="ALLOW",
            result="SUCCESS",
            attributes={
                "graceful": True,
                "timeout_seconds": timeout_seconds,
            },
        )

        return self.metrics_snapshot

    # ---- internal ticks -----------------------------------------------------

    def _tick_heartbeat(self) -> None:
        """持久化一次心跳并发出审计和指标事件。更新节点存活状态。"""
        try:
            now = datetime.now(tz=UTC)
            self._scheduler.heartbeat(now=now)
        except Exception:
            _logger.exception("Heartbeat tick failed")

    def _tick_reconcile(self) -> None:
        """调和作业分配并执行本节点拥有的作业。从数据库获取分配，逐个委托 handler 执行。"""
        now = datetime.now(tz=UTC)
        try:
            snapshot = self._scheduler.assign_jobs(now=now)
        except Exception:
            _logger.exception("Job assignment reconcile failed")
            return

        for job_id in snapshot.assigned_jobs:
            if self._shutdown_event.is_set():
                break
            fencing_token = snapshot.fencing_tokens.get(job_id, 0)
            self._execute_one(job_id=job_id, fencing_token=fencing_token, now=now)

    def _execute_one(self, *, job_id: str, fencing_token: int, now: datetime) -> None:
        """验证租约后执行一个 job，或标记跳过。

        异常处理策略：
        - 如果 handler 不存在（_do_execute 返回 False），记录 job_handler_not_found 指标，
          不标记 completed，不上抛异常。
        - 如果 handler 抛出异常，记录 job_failed 指标和 audit 事件，然后 re-raise，
          交由 APScheduler 处理（misfire/re-schedule）。
        - 如果 lease 验证失败，记录 job_skipped_no_lease 指标，不执行 handler。
        - finally 块不处理 lease 释放：lease 由 scheduler.assign_jobs 在下一 tick 覆盖。

        Note:
            真实设备采集 handler 当前为待注册状态。CLI 入口 cli.py 注册了 noop/acquisition/
            publish 三类 mock handler，但 production 级别的采集 handler 尚未接入。
            _do_execute 通过 job_row.job_type 分发到 self._handlers 字典，
            若 job_type 未注册，记录 HANDLER_NOT_FOUND 并返回 False。
        """
        decision = self._scheduler.validate_execution(
            job_id=job_id,
            holder_key=self._settings.node_key,
            fencing_token=fencing_token,
            now=now,
        )
        if not decision.allowed:
            self._metrics.inc(_JOB_SKIPPED_NO_LEASE)
            self._emit_audit_event(
                action="job.skipped",
                resource_type="job",
                resource_id=job_id,
                decision="DENY",
                result="NO_LEASE",
                reason_code=decision.reason_code,
                attributes={
                    "job_id": job_id,
                    "fencing_token_hash": redact_fencing_token(fencing_token),
                },
            )
            return

        # Look up job to determine interval for missed-tick detection
        job_row = self._job_repository.get(job_id)
        if job_row is None:
            return
        interval_ms = _get_interval_ms(job_row.config_json)
        stagger_ms = _get_stagger_ms(job_row.config_json)

        # Apply stagger offset
        if stagger_ms and stagger_ms > 0:
            time.sleep(stagger_ms / 1000.0)

        self._metrics.inc(_JOB_STARTED)
        started_at = time.monotonic()
        try:
            # Renew lease before executing to extend coverage
            try:
                self._lease_service.renew(
                    lease_name=f"job:{job_id}",
                    holder_key=self._settings.node_key,
                    ttl_seconds=self._settings.lease_ttl_seconds,
                    now=datetime.now(tz=UTC),
                )
                self._metrics.inc(_LEASE_RENEWAL_SUCCESS)
            except ValueError:
                self._metrics.inc(_LEASE_RENEWAL_FAILED)
                self._metrics.inc(_JOB_FAILED)
                return

            # Record assignment lag
            assignment_lag = int((datetime.now(tz=UTC) - now).total_seconds() * 1000)
            self._metrics.gauge(_ASSIGNMENT_LAG_MS, float(assignment_lag))

            # ---- actual job execution ----
            executed = self._do_execute(job_row)
            if executed is False:
                return

            elapsed_ms = (time.monotonic() - started_at) * 1000.0
            self._metrics.gauge(_JOB_DURATION_MS, elapsed_ms)
            self._metrics.inc(_JOB_COMPLETED)

            # Detect missed tick if execution time exceeds interval
            if interval_ms and interval_ms > 0 and elapsed_ms > interval_ms:
                self._metrics.inc(_MISSED_TICK)

            self._emit_audit_event(
                action="job.executed",
                resource_type="job",
                resource_id=job_id,
                decision="ALLOW",
                result="SUCCESS",
                attributes={
                    "job_id": job_id,
                    "duration_ms": elapsed_ms,
                    "assignment_lag_ms": assignment_lag,
                    "fencing_token_hash": redact_fencing_token(fencing_token),
                },
            )
        except Exception:
            elapsed_ms = (time.monotonic() - started_at) * 1000.0
            self._metrics.inc(_JOB_FAILED)
            self._emit_audit_event(
                action="job.failed",
                resource_type="job",
                resource_id=job_id,
                decision="ALLOW",
                result="FAILED",
                reason_code="EXECUTION_ERROR",
                attributes={
                    "job_id": job_id,
                    "duration_ms": elapsed_ms,
                    "fencing_token_hash": redact_fencing_token(fencing_token),
                },
            )
            raise

    def _do_execute(self, job_row: IngestRuntimeJob) -> bool:
        """Execute one job by dispatching to the registered handler for its type.

        Returns True when a handler was found and called (even if it raised).
        Returns False when no handler is registered, so the caller can avoid
        recording the job as completed.

        Note:
            真实设备采集 handler 当前为待实现状态。CLI 入口 cli.py 注册了
            noop/acquisition/publish 三类 handler，但 acquisition handler 仅
            为 noop 占位，未连接真实的 SourceAcquisitionUseCase。
            当 production 采集 handler 就绪后，需在此处按 job_type 注册。
            在此之前，_do_execute 通过 HANDLER_NOT_FOUND 机制通知上层。
        """
        handler = self._handlers.get(job_row.job_type)
        if handler is None:
            self._metrics.inc(_JOB_HANDLER_NOT_FOUND)
            self._emit_audit_event(
                action="job.handler_not_found",
                resource_type="job",
                resource_id=job_row.job_id,
                decision="DENY",
                result="HANDLER_NOT_FOUND",
                reason_code="JOB_HANDLER_NOT_FOUND",
                attributes={
                    "job_id": job_row.job_id,
                    "job_type": job_row.job_type,
                },
            )
            return False
        handler.execute(job_row)
        return True

    # ---- audit / helpers ---------------------------------------------------

    def _emit_audit_event(
        self,
        *,
        action: str,
        resource_type: str,
        resource_id: str | None,
        decision: str,
        result: str,
        reason_code: str | None = None,
        attributes: dict[str, object] | None = None,
    ) -> None:
        if self._audit_sink is None:
            return
        self._audit_sink.emit(
            IngestAuditEvent(
                request_id=f"worker-{uuid4()}",
                actor=self._settings.node_key,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                decision=decision,
                result=result,
                reason_code=reason_code,
                http_status=None,
                trace_id=None,
                client_ip=None,
                node_id=self._settings.node_key,
                attributes=attributes or {},
            )
        )


def _get_interval_ms(config: dict[str, object]) -> int | None:
    """从作业配置 JSON 中提取 interval_ms 字段。"""
    raw = config.get("interval_ms")
    if raw is None:
        return None
    if isinstance(raw, bool):
        return int(raw)
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float):
        return int(raw)
    if isinstance(raw, str):
        try:
            return int(raw)
        except ValueError:
            return None
    return None


def _get_stagger_ms(config: dict[str, object]) -> int | None:
    """从作业配置 JSON 中提取 stagger_offset_ms 字段。"""
    raw = config.get("stagger_offset_ms")
    if raw is None:
        return None
    if isinstance(raw, bool):
        return int(raw)
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float):
        return int(raw)
    if isinstance(raw, str):
        try:
            return int(raw)
        except ValueError:
            return None
    return None


def _percentile(values: list[float], quantile: float) -> float:
    """对非空有序列表计算确定性最近秩百分位数。使用线性插值。"""

    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = max(0, min(len(ordered) - 1, math.ceil(len(ordered) * quantile) - 1))
    return ordered[rank]
