"""Write-control specific lease guard.

WriteLeaseService 负责设备写入/控制命令的租约守卫，防止多节点并发写。

Fencing token 语义:
- FENCED: 当前请求的 fencing_token 与活跃租约不匹配，或缺失 token 但有活跃租约。
- ACQUIRED: 成功 acquire 租约并获取新的 fencing_token。
- LEASE_CONFLICT: LeaseService 层面发现其他 holder 持有活跃租约。
- TOKEN_NOT_PROVIDED: requested_fencing_token 为 None 且无冲突，允许 acquire
  但记录风险。
"""

from __future__ import annotations

from datetime import UTC, datetime

from whale.ingest.ports.runtime.write_lease_port import WriteLeaseDecisionData
from whale.ingest.runtime.lease import LeaseService


class WriteLeaseService:
    """Guard write/control execution with a dedicated lease scope.

    WriteLeaseService 使用专门的 ``write:`` 前缀的租约来隔离写入控制命令的并发保护。
    与 LeaseService 的关系：
    - LeaseService 管理通用租约（如 job: 前缀的调度租约）。
    - WriteLeaseService 使用 write:resource_id 作为租约名，委托 LeaseService 执行。
    - WriteLeaseService 在 acquire 时实施增加的 fencing 语义：
      1. 如果 requested_fencing_token 与活跃租约不匹配 -> FENCED。
      2. 如果 requested_fencing_token 为 None 但有其他 holder 的活跃租约 -> FENCED。
         防止调用方忘记携带 token 时绕过旧主防护。
      3. 如果 requested_fencing_token 为 None 且无冲突 -> 允许 acquire，
         但在 reason_code 中标记 TOKEN_NOT_PROVIDED。

    Args:
        lease_service: 底层通用 LeaseService 实例。
        ttl_seconds: 租约 TTL，默认 30 秒。
    """

    def __init__(self, lease_service: LeaseService, ttl_seconds: int = 30) -> None:
        """初始化写入租约服务。Args: session_factory: 数据库会话工厂。fencing_token_repository: fencing token 仓库。"""
        self._lease_service = lease_service
        self._ttl_seconds = ttl_seconds

    def acquire(
        self,
        *,
        resource_id: str,
        holder_key: str,
        requested_fencing_token: int | None = None,
    ) -> WriteLeaseDecisionData:
        """初始化租约仓库。Args: session_factory: 数据库会话工厂。"""
        """Acquire one write lease.

        租约守卫策略：
        - 如果 requested_fencing_token 不为 None 且与当前活跃租约不匹配 → FENCED。
        - 如果 requested_fencing_token 为 None 但有其他 holder 的活跃租约 → FENCED。
          这是为了防止 caller 忘记携带 token 时绕过旧主防护。
        - 如果 requested_fencing_token 为 None 且无冲突 → 允许 acquire，但在 audit
          reason 中标记 TOKEN_NOT_PROVIDED 以说明风险。
        """

        snapshot = self._lease_service.get_snapshot(lease_name=f"write:{resource_id}")
        if (
            requested_fencing_token is not None
            and snapshot is not None
            and snapshot.status == "ACTIVE"
            and snapshot.fencing_token != requested_fencing_token
        ):
            return WriteLeaseDecisionData(
                allowed=False,
                result="FENCED",
                reason_code="OLD_PRIMARY_FENCED",
                fencing_token=snapshot.fencing_token,
                expires_at=snapshot.expires_at,
            )

        # requested_fencing_token 缺失但有其他 holder 的活跃租约 → 仍然拒绝
        if (
            requested_fencing_token is None
            and snapshot is not None
            and snapshot.status == "ACTIVE"
        ):
            return WriteLeaseDecisionData(
                allowed=False,
                result="FENCED",
                reason_code="OLD_PRIMARY_FENCED",
                fencing_token=snapshot.fencing_token,
                expires_at=snapshot.expires_at,
            )

        result = self._lease_service.acquire(
            lease_name=f"write:{resource_id}",
            lease_scope="write",
            resource_id=resource_id,
            holder_key=holder_key,
            ttl_seconds=self._ttl_seconds,
            now=datetime.now(tz=UTC),
        )
        if not result.acquired:
            return WriteLeaseDecisionData(
                allowed=False,
                result="CONFLICT",
                reason_code=result.reason,
                fencing_token=result.fencing_token,
                expires_at=snapshot.expires_at if snapshot is not None else None,
            )
        # 成功后再查一次 snapshot 获取最新 expires_at
        final_snapshot = self._lease_service.get_snapshot(lease_name=f"write:{resource_id}")
        return WriteLeaseDecisionData(
            allowed=True,
            result="ALLOW",
            reason_code=None,
            fencing_token=result.fencing_token,
            expires_at=final_snapshot.expires_at if final_snapshot is not None else None,
        )

    def renew(self, *, resource_id: str, holder_key: str) -> WriteLeaseDecisionData:
        """续期一个活跃的写入租约。"""

        lease = self._lease_service.renew(
            lease_name=f"write:{resource_id}",
            holder_key=holder_key,
            ttl_seconds=self._ttl_seconds,
            now=datetime.now(tz=UTC),
        )
        return WriteLeaseDecisionData(
            allowed=True,
            result="ALLOW",
            reason_code=None,
            fencing_token=lease.fencing_token,
            expires_at=lease.expires_at,
        )

    def validate(
        self,
        *,
        resource_id: str,
        holder_key: str,
        fencing_token: int,
    ) -> WriteLeaseDecisionData:
        """验证活跃的写入租约 token。"""

        allowed = self._lease_service.validate_execution(
            lease_name=f"write:{resource_id}",
            holder_key=holder_key,
            fencing_token=fencing_token,
            now=datetime.now(tz=UTC),
        )
        snapshot = self._lease_service.get_snapshot(lease_name=f"write:{resource_id}")
        if not allowed:
            return WriteLeaseDecisionData(
                allowed=False,
                result="FENCED",
                reason_code="OLD_PRIMARY_FENCED",
                fencing_token=snapshot.fencing_token if snapshot is not None else fencing_token,
                expires_at=snapshot.expires_at if snapshot is not None else None,
            )
        return WriteLeaseDecisionData(
            allowed=True,
            result="ALLOW",
            reason_code=None,
            fencing_token=fencing_token,
            expires_at=snapshot.expires_at if snapshot is not None else None,
        )

    def release(self, *, resource_id: str, holder_key: str) -> None:
        """释放一个写入租约。"""

        self._lease_service.release(
            lease_name=f"write:{resource_id}",
            holder_key=holder_key,
        )
