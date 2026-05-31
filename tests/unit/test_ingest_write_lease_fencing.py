"""Write lease fencing tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from whale.ingest.framework.persistence import create_runtime_engine, create_runtime_session_factory, initialize_runtime_database
from whale.ingest.runtime.fencing import FencingTokenRepository
from whale.ingest.runtime.lease import LeaseService
from whale.ingest.runtime.write_lease import WriteLeaseService


def _service(tmp_path):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'write-fencing.sqlite'}")
    initialize_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)
    lease_service = LeaseService(session_factory, FencingTokenRepository(session_factory))
    return lease_service, WriteLeaseService(lease_service, ttl_seconds=5)


def test_write_lease_renewal_extends_expiry(tmp_path) -> None:
    _, service = _service(tmp_path)
    first = service.acquire(resource_id="LD1", holder_key="node-a")
    renewed = service.renew(resource_id="LD1", holder_key="node-a")
    assert renewed.allowed is True
    assert renewed.expires_at >= first.expires_at


def test_expired_write_lease_rejects_command(tmp_path) -> None:
    lease_service, service = _service(tmp_path)
    acquired = service.acquire(resource_id="LD1", holder_key="node-a")
    lease_service.force_expire(lease_name="write:LD1", now=datetime.now(tz=UTC) + timedelta(seconds=10))
    validated = service.validate(resource_id="LD1", holder_key="node-a", fencing_token=acquired.fencing_token or 0)
    assert validated.allowed is False
    assert validated.result == "FENCED"


def test_old_primary_fencing_token_rejects_command(tmp_path) -> None:
    lease_service, service = _service(tmp_path)
    first = service.acquire(resource_id="LD1", holder_key="node-a")
    lease_service.force_expire(lease_name="write:LD1", now=datetime.now(tz=UTC) + timedelta(seconds=10))
    second = service.acquire(resource_id="LD1", holder_key="node-b")
    fenced = service.acquire(
        resource_id="LD1",
        holder_key="node-a",
        requested_fencing_token=first.fencing_token,
    )
    assert second.allowed is True
    assert fenced.allowed is False
    assert fenced.reason_code == "OLD_PRIMARY_FENCED"


# ── QA-3: 缺失 token 时的 fencing 防护 ──────────────────────────────


def test_fence_when_token_missing_and_other_holder_active(tmp_path) -> None:
    """requested_fencing_token=None 但有其他 holder 活跃租约时应被 FENCED。"""
    _, service = _service(tmp_path)

    first = service.acquire(resource_id="LD-FENCE-MISSING", holder_key="node-a")
    assert first.allowed is True

    # node-b 不传 requested_fencing_token → 应被 FENCED
    second = service.acquire(resource_id="LD-FENCE-MISSING", holder_key="node-b")
    assert second.allowed is False
    assert second.result == "FENCED"
    assert second.reason_code == "OLD_PRIMARY_FENCED"


def test_acquire_allowed_when_no_conflict(tmp_path) -> None:
    """无冲突时应正常 acquire。"""
    _, service = _service(tmp_path)
    result = service.acquire(resource_id="LD-NO-CONFLICT", holder_key="node-a")
    assert result.allowed is True
    assert result.result == "ALLOW"
    assert result.fencing_token is not None
    assert result.expires_at is not None


def test_acquire_allowed_when_same_holder_same_token(tmp_path) -> None:
    """同一 holder 使用正确 fencing_token 应允许 re-acquire。"""
    _, service = _service(tmp_path)
    first = service.acquire(resource_id="LD-RE-ACQUIRE", holder_key="node-a")
    assert first.allowed is True

    second = service.acquire(
        resource_id="LD-RE-ACQUIRE",
        holder_key="node-a",
        requested_fencing_token=first.fencing_token,
    )
    assert second.allowed is True


def test_acquire_with_snapshot_none_does_not_crash(tmp_path) -> None:
    """首次 acquire 时 get_snapshot 返回 None，不应 AttributeError (Extra 修复)。"""
    _, service = _service(tmp_path)
    # 全新 resource_id，snapshot 为 None
    result = service.acquire(resource_id="LD-BRAND-NEW", holder_key="node-a")
    assert result.allowed is True
    assert result.expires_at is not None
