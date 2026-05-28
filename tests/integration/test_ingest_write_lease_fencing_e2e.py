"""Write lease / fencing / readback integration tests."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field

import pytest

from whale.ingest.adapters.source.static_source_write_port_registry import StaticSourceWritePortRegistry
from whale.ingest.framework.persistence import create_runtime_engine, create_runtime_session_factory, initialize_runtime_database
from whale.ingest.ports.command.source_command_audit_port import SourceCommandAuditEvent, SourceCommandAuditPort
from whale.ingest.ports.source.source_write_port import SourceWritePort
from whale.ingest.runtime.fencing import FencingTokenRepository
from whale.ingest.runtime.lease import LeaseService
from whale.ingest.runtime.write_lease import WriteLeaseService
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.ingest.usecases.dtos.source_write_request import SourceWriteExecutionOptions, SourceWriteItemData, SourceWriteRequest
from whale.ingest.usecases.dtos.source_write_result import SourceWriteItemResult, SourceWriteResult
from whale.ingest.usecases.source_command_use_case import SourceCommandUseCase


@dataclass
class _AuditCollector(SourceCommandAuditPort):
    events: list[SourceCommandAuditEvent] = field(default_factory=list)

    def emit(self, event: SourceCommandAuditEvent) -> None:
        self.events.append(event)


class _WritePort(SourceWritePort):
    def __init__(self, *, readback_value: str = "1.0", precheck: bool = True) -> None:
        self._readback_value = readback_value
        self._precheck = precheck

    async def write(self, execution, connection, items):
        del execution, connection
        return SourceWriteResult(
            request_id="req-1",
            command_id="cmd-1",
            dry_run=False,
            success_count=len(items),
            failure_count=0,
            results=[SourceWriteItemResult(key=item.key, node_id=item.node_id, ok=True) for item in items],
        )

    async def precheck(self, execution, connection, items):
        del execution, connection, items
        return True if self._precheck else "precheck_failed"

    async def readback(self, execution, connection, items, write_result):
        del execution, connection, write_result
        return {item.node_id: self._readback_value for item in items}


def _request(*, fencing_token: int | None = None, require_readback: bool = False) -> SourceWriteRequest:
    params = {}
    if fencing_token is not None:
        params["fencing_token"] = fencing_token
    if require_readback:
        params["require_readback"] = True
    return SourceWriteRequest(
        request_id="req-1",
        command_id="cmd-1",
        trace_id="trace-1",
        execution=SourceWriteExecutionOptions(protocol="opcua", transport="tcp", actor="node-a", params=params),
        connections=[SourceConnectionData(host="127.0.0.1", port=4840, ied_name="IED1", ld_name="LD1", namespace_uri="")],
        items=[SourceWriteItemData(key="k1", node_id="n1", value_type="double", value="1.0")],
    )


def _use_case(tmp_path, port: SourceWritePort):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'write-e2e.sqlite'}")
    initialize_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)
    lease_service = LeaseService(session_factory, FencingTokenRepository(session_factory))
    audit = _AuditCollector()
    use_case = SourceCommandUseCase(
        write_port_registry=StaticSourceWritePortRegistry({"opcua": port}),
        audit_port=audit,
        write_lease_port=WriteLeaseService(lease_service, ttl_seconds=5),
    )
    return lease_service, audit, use_case


def test_write_command_readback_success(tmp_path) -> None:
    os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"
    _, audit, use_case = _use_case(tmp_path, _WritePort(readback_value="1.0"))
    result = asyncio.run(use_case.execute(_request(require_readback=True)))
    os.environ.pop("WHALE_INGEST_SOURCE_WRITE_ENABLED", None)

    assert result.attributes["readback"] == "confirmed"
    assert audit.events[-1].result == "SUCCESS"


def test_write_command_readback_mismatch_is_audited(tmp_path) -> None:
    os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"
    _, audit, use_case = _use_case(tmp_path, _WritePort(readback_value="2.0"))
    with pytest.raises(RuntimeError):
        asyncio.run(use_case.execute(_request(require_readback=True)))
    os.environ.pop("WHALE_INGEST_SOURCE_WRITE_ENABLED", None)

    assert any(event.reason_code == "READBACK_MISMATCH" for event in audit.events)


def test_write_lease_conflict_is_audited(tmp_path) -> None:
    os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"
    lease_service, audit, use_case = _use_case(tmp_path, _WritePort())
    first = WriteLeaseService(lease_service, ttl_seconds=5).acquire(resource_id="LD1", holder_key="node-b")
    assert first.allowed is True
    with pytest.raises(RuntimeError):
        asyncio.run(use_case.execute(_request()))
    os.environ.pop("WHALE_INGEST_SOURCE_WRITE_ENABLED", None)

    assert any(event.reason_code == "LEASE_CONFLICT" for event in audit.events)


def test_old_primary_fencing_token_rejects_command(tmp_path) -> None:
    os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"
    lease_service, audit, use_case = _use_case(tmp_path, _WritePort())
    guard = WriteLeaseService(lease_service, ttl_seconds=5)
    first = guard.acquire(resource_id="LD1", holder_key="node-a")
    lease_service.force_expire(lease_name="write:LD1")
    second = guard.acquire(resource_id="LD1", holder_key="node-b")
    assert second.allowed is True
    with pytest.raises(RuntimeError):
        asyncio.run(use_case.execute(_request(fencing_token=first.fencing_token)))
    os.environ.pop("WHALE_INGEST_SOURCE_WRITE_ENABLED", None)

    assert any(event.reason_code == "OLD_PRIMARY_FENCED" for event in audit.events)
