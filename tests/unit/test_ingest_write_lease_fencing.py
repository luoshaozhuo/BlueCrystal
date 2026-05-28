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
