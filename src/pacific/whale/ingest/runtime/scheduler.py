"""采集调度器。

基于 APScheduler 实现定时采集任务调度，
管理任务的添加、删除、暂停和恢复。

并发模型：单进程内多线程调度。
失败处理：任务异常不影响其他任务继续执行。
资源生命周期：shutdown 时等待运行中任务完成。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
from uuid import uuid4

from pacific.whale.ingest.domain.audit_event import IngestAuditEvent
from pacific.whale.ingest.ports.audit import IngestAuditSinkPort
from pacific.whale.ingest.runtime.fencing import redact_fencing_token
from pacific.whale.ingest.runtime.job_assignment import (
    JobAssignment,
    JobAssignmentRepository,
    RuntimeJobRepository,
)
from pacific.whale.ingest.runtime.lease import LeaseService
from pacific.whale.ingest.runtime.modes import RuntimeMode
from pacific.whale.ingest.runtime.node_runtime import NodeHeartbeat, NodeRuntimeRepository
from pacific.whale.ingest.runtime.scheduler_settings import SchedulerSettings


@dataclass(slots=True)
class SchedulerSnapshot:
    """轻量级调度器状态快照。"""

    node_key: str
    runtime_mode: RuntimeMode
    assigned_jobs: tuple[str, ...]
    fencing_tokens: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SchedulerExecutionDecision:
    """单个 worker/任务/fencing token 三元组的执行决策。"""

    allowed: bool
    result: str
    reason_code: str | None


class SourceScheduler:
    """基于数据库的调度器，将单节点作为多节点特例处理。"""

    def __init__(
        self,
        *,
        settings: SchedulerSettings,
        node_repository: NodeRuntimeRepository,
        job_repository: RuntimeJobRepository,
        assignment_repository: JobAssignmentRepository,
        lease_service: LeaseService,
        audit_sink: IngestAuditSinkPort | None = None,
    ) -> None:
        """初始化调度器。Args: settings: 调度器配置。job_repository: 作业仓库。executor: APScheduler 执行器。"""
        self._settings = settings
        self._node_repository = node_repository
        self._job_repository = job_repository
        self._assignment_repository = assignment_repository
        self._lease_service = lease_service
        self._audit_sink = audit_sink

    @property
    def node_key(self) -> str:
        """返回配置的节点键。"""

        return self._settings.node_key

    def heartbeat(self, *, now: datetime | None = None) -> None:
        """持久化一个节点心跳。"""

        resolved_now = now or datetime.now(tz=UTC)
        self._node_repository.upsert_heartbeat(
            NodeHeartbeat(
                node_key=self._settings.node_key,
                runtime_mode=self._settings.runtime_mode,
                heartbeat_at=resolved_now,
            )
        )
        self._emit_event(
            action="scheduler.node_heartbeat",
            resource_type="node",
            resource_id=self._settings.node_key,
            decision="ALLOW",
            result="SUCCESS",
        )

    def assign_jobs(self, *, now: datetime | None = None) -> SchedulerSnapshot:
        """根据活跃运行时模式分配任务。"""

        resolved_now = now or datetime.now(tz=UTC)
        self._lease_service.expire_due_leases(now=resolved_now)
        alive_nodes = self._alive_node_keys(now=resolved_now)
        assigned_jobs: list[str] = []
        fencing_tokens: dict[str, int] = {}
        failover_count = 0

        for row in self._job_repository.list_enabled_jobs():
            desired_owner = self._desired_owner(
                job_id=row.job_id,
                partition_key=row.partition_key,
                alive_nodes=alive_nodes,
            )
            current_lease = self._lease_service.get_snapshot(lease_name=f"job:{row.job_id}")
            stale_holder = current_lease is not None and current_lease.holder_key not in alive_nodes
            expired = current_lease is not None and current_lease.expires_at <= resolved_now

            if stale_holder:
                self._lease_service.force_expire(
                    lease_name=f"job:{row.job_id}",
                    now=resolved_now,
                )
                self._assignment_repository.deactivate_job(row.job_id)
                failover_count += 1
                self._emit_event(
                    action="scheduler.lease_expire",
                    resource_type="job",
                    resource_id=row.job_id,
                    decision="ALLOW",
                    result="EXPIRED",
                    reason_code="NODE_TIMEOUT",
                    attributes={"job_id": row.job_id},
                )
                current_lease = None

            if expired:
                self._assignment_repository.deactivate_job(row.job_id)
                self._emit_event(
                    action="scheduler.lease_expire",
                    resource_type="job",
                    resource_id=row.job_id,
                    decision="ALLOW",
                    result="EXPIRED",
                    reason_code="LEASE_EXPIRED",
                    attributes={"job_id": row.job_id},
                )
                current_lease = None

            if desired_owner != self._settings.node_key:
                continue

            result = self._lease_service.acquire(
                lease_name=f"job:{row.job_id}",
                lease_scope="job",
                resource_id=row.job_id,
                holder_key=self._settings.node_key,
                ttl_seconds=self._settings.lease_ttl_seconds,
                now=resolved_now,
            )
            if not result.acquired:
                self._emit_event(
                    action="scheduler.lease_acquire",
                    resource_type="job",
                    resource_id=row.job_id,
                    decision="DENY",
                    result="CONFLICT",
                    reason_code=result.reason,
                    attributes={
                        "job_id": row.job_id,
                        "fencing_token_hash": redact_fencing_token(result.fencing_token),
                    },
                )
                continue

            if current_lease is not None and current_lease.holder_key == self._settings.node_key:
                action = "scheduler.lease_renew"
                result_code = "SUCCESS"
            else:
                action = "scheduler.lease_acquire"
                result_code = "SUCCESS"
                self._assignment_repository.deactivate_job(row.job_id)
            self._assignment_repository.assign(
                JobAssignment(
                    job_id=row.job_id,
                    node_key=self._settings.node_key,
                    active=True,
                    assigned_at=resolved_now,
                )
            )
            assigned_jobs.append(row.job_id)
            fencing_tokens[row.job_id] = result.fencing_token
            self._emit_event(
                action=action,
                resource_type="job",
                resource_id=row.job_id,
                decision="ALLOW",
                result=result_code,
                attributes={
                    "job_id": row.job_id,
                    "lease_id": result.lease_id,
                    "fencing_token_hash": redact_fencing_token(result.fencing_token),
                    "assignment_lag_ms": max(
                        int((resolved_now - _as_utc(row.updated_at)).total_seconds() * 1000),
                        0,
                    ),
                    "lease_renewal_latency_ms": 0,
                },
            )

        if failover_count:
            self._emit_event(
                action="scheduler.failover_count",
                resource_type="scheduler",
                resource_id=self._settings.node_key,
                decision="ALLOW",
                result="SUCCESS",
                attributes={"failover_count": failover_count},
            )

        return SchedulerSnapshot(
            node_key=self._settings.node_key,
            runtime_mode=self._settings.runtime_mode,
            assigned_jobs=tuple(assigned_jobs),
            fencing_tokens=fencing_tokens,
        )

    def bootstrap(self, *, now: datetime | None = None) -> SchedulerSnapshot:
        """持久化心跳并对账分配。"""

        resolved_now = now or datetime.now(tz=UTC)
        self.heartbeat(now=resolved_now)
        return self.assign_jobs(now=resolved_now)

    def release_jobs(self, job_ids: list[str], *, now: datetime | None = None) -> None:
        """从当前节点释放一组任务租约。"""

        resolved_now = now or datetime.now(tz=UTC)
        for job_id in job_ids:
            self._lease_service.release(
                lease_name=f"job:{job_id}",
                holder_key=self._settings.node_key,
                now=resolved_now,
            )
            self._assignment_repository.deactivate_job(job_id)
            self._emit_event(
                action="scheduler.lease_release",
                resource_type="job",
                resource_id=job_id,
                decision="ALLOW",
                result="SUCCESS",
            )

    def validate_execution(
        self,
        *,
        job_id: str,
        holder_key: str,
        fencing_token: int,
        now: datetime | None = None,
    ) -> SchedulerExecutionDecision:
        """返回 worker 是否可在给定 token 下执行任务。"""

        resolved_now = now or datetime.now(tz=UTC)
        allowed = self._lease_service.validate_execution(
            lease_name=f"job:{job_id}",
            holder_key=holder_key,
            fencing_token=fencing_token,
            now=resolved_now,
        )
        if allowed:
            return SchedulerExecutionDecision(True, "SUCCESS", None)
        self._emit_event(
            action="scheduler.fencing_reject",
            resource_type="job",
            resource_id=job_id,
            decision="DENY",
            result="FENCED",
            reason_code="FENCING_TOKEN_MISMATCH",
            attributes={
                "job_id": job_id,
                "fencing_token_hash": redact_fencing_token(fencing_token),
            },
        )
        return SchedulerExecutionDecision(False, "FENCED", "FENCING_TOKEN_MISMATCH")

    def _alive_node_keys(self, *, now: datetime) -> list[str]:
        rows = self._node_repository.list_alive_nodes(
            now=now,
            heartbeat_timeout_seconds=self._settings.heartbeat_timeout_seconds,
        )
        node_keys = sorted(row.node_key for row in rows)
        if self._settings.node_key not in node_keys:
            node_keys.append(self._settings.node_key)
            node_keys.sort()
        return node_keys

    def _desired_owner(
        self,
        *,
        job_id: str,
        partition_key: str | None,
        alive_nodes: list[str],
    ) -> str:
        if not alive_nodes:
            return self._settings.node_key
        if self._settings.runtime_mode in {RuntimeMode.STANDALONE, RuntimeMode.ACTIVE_STANDBY}:
            return alive_nodes[0]

        key = partition_key or job_id
        digest = sha256(key.encode("utf-8")).hexdigest()
        index = int(digest[:8], 16) % len(alive_nodes)
        return alive_nodes[index]

    def _emit_event(
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
                request_id=f"scheduler-{uuid4()}",
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


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
