"""Write lease service tests."""

from __future__ import annotations

from whale.ingest.framework.persistence import (
    create_runtime_engine,
    create_runtime_session_factory,
    initialize_runtime_database,
)
from whale.ingest.runtime.fencing import FencingTokenRepository
from whale.ingest.runtime.lease import LeaseService
from whale.ingest.runtime.write_lease import WriteLeaseService


def test_write_lease_conflict_and_reuse(tmp_path) -> None:
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'write-lease.sqlite'}")
    initialize_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)
    service = WriteLeaseService(
        LeaseService(session_factory, FencingTokenRepository(session_factory)),
        ttl_seconds=30,
    )

    first = service.acquire(resource_id="LD1", holder_key="node-a")
    second = service.acquire(resource_id="LD1", holder_key="node-b")

    assert first.allowed is True
    assert second.allowed is False
    # 不传 requested_fencing_token 时有其他 holder 活跃租约 → FENCED (QA-3 修复)
    assert second.result == "FENCED"
