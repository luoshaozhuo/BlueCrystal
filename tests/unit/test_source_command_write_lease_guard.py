"""Source command write lease guard tests."""

from __future__ import annotations

import asyncio
import os

import pytest

from whale.ingest.adapters.source.static_source_write_port_registry import StaticSourceWritePortRegistry
from whale.ingest.ports.runtime.write_lease_port import WriteLeaseDecisionData
from whale.ingest.ports.source.source_write_port import SourceWritePort
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.ingest.usecases.dtos.source_write_request import (
    SourceWriteExecutionOptions,
    SourceWriteItemData,
    SourceWriteRequest,
)
from whale.ingest.usecases.dtos.source_write_result import SourceWriteResult
from whale.ingest.usecases.source_command_use_case import SourceCommandUseCase


class _FakeWritePort(SourceWritePort):
    async def write(self, execution, connection, items):
        del execution, connection, items
        return SourceWriteResult(
            request_id="req-1",
            command_id="cmd-1",
            dry_run=False,
            success_count=1,
            failure_count=0,
            results=[],
        )


class _DenyingLease:
    def acquire(self, *, resource_id: str, holder_key: str) -> WriteLeaseDecisionData:
        del resource_id, holder_key
        return WriteLeaseDecisionData(
            allowed=False,
            result="CONFLICT",
            reason_code="LEASE_CONFLICT",
            fencing_token=2,
        )

    def release(self, *, resource_id: str, holder_key: str) -> None:
        del resource_id, holder_key


def _request() -> SourceWriteRequest:
    return SourceWriteRequest(
        request_id="req-1",
        command_id="cmd-1",
        trace_id="trace-1",
        execution=SourceWriteExecutionOptions(protocol="opcua", transport="tcp", actor="tester"),
        connections=[
            SourceConnectionData(
                host="127.0.0.1",
                port=4840,
                ied_name="IED1",
                ld_name="LD1",
                namespace_uri="",
            )
        ],
        items=[SourceWriteItemData(key="k1", node_id="n1", value_type="double", value="1.0")],
    )


def test_source_command_rejects_when_write_lease_denies() -> None:
    os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"
    use_case = SourceCommandUseCase(
        write_port_registry=StaticSourceWritePortRegistry({"opcua": _FakeWritePort()}),
        write_lease_port=_DenyingLease(),
    )

    with pytest.raises(RuntimeError):
        asyncio.run(use_case.execute(_request()))

    os.environ.pop("WHALE_INGEST_SOURCE_WRITE_ENABLED", None)
