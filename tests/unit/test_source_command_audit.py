"""SourceCommandUseCase audit tests."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field

import pytest

from whale.ingest.adapters.source.static_source_write_port_registry import (
    StaticSourceWritePortRegistry,
)
from whale.ingest.ports.command.source_command_audit_port import (
    SourceCommandAuditEvent,
    SourceCommandAuditPort,
)
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
            request_id="r1",
            command_id=None,
            dry_run=False,
            success_count=1,
            failure_count=0,
            results=[],
        )


@dataclass
class _InMemoryAuditPort(SourceCommandAuditPort):
    events: list[SourceCommandAuditEvent] = field(default_factory=list)

    def emit(self, event: SourceCommandAuditEvent) -> None:
        self.events.append(event)


def _request(*, dry_run: bool = False) -> SourceWriteRequest:
    return SourceWriteRequest(
        request_id="req-1",
        command_id="cmd-1",
        trace_id="trace-1",
        execution=SourceWriteExecutionOptions(
            protocol="opcua",
            transport="tcp",
            dry_run=dry_run,
            actor="tester",
        ),
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


def test_source_command_emits_success_audit() -> None:
    os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"
    audit = _InMemoryAuditPort()
    use_case = SourceCommandUseCase(
        write_port_registry=StaticSourceWritePortRegistry({"opcua": _FakeWritePort()}),
        audit_port=audit,
    )
    result = asyncio.run(use_case.execute(_request()))
    os.environ.pop("WHALE_INGEST_SOURCE_WRITE_ENABLED", None)

    assert result.command_id == "cmd-1"
    assert len(audit.events) == 1
    event = audit.events[0]
    assert event.result == "SUCCESS"
    assert event.command_id == "cmd-1"
    assert event.trace_id == "trace-1"
    assert event.actor == "tester"
    assert event.protocol == "opcua"


def test_source_command_emits_rejected_audit_when_write_disabled() -> None:
    os.environ.pop("WHALE_INGEST_SOURCE_WRITE_ENABLED", None)
    audit = _InMemoryAuditPort()
    use_case = SourceCommandUseCase(
        write_port_registry=StaticSourceWritePortRegistry({"opcua": _FakeWritePort()}),
        audit_port=audit,
    )

    with pytest.raises(RuntimeError):
        asyncio.run(use_case.execute(_request(dry_run=False)))

    assert len(audit.events) == 1
    assert audit.events[0].result == "REJECTED"
    assert audit.events[0].failure_reason == "write_disabled"
