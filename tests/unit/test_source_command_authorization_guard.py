"""Unit tests for AuthorizedSourceWritePort."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from whale.ingest.decorators.source_write import AuthorizedSourceWritePort
from whale.ingest.domain.write_security_profile import (
    ProtocolWriteProfile,
    WriteSecurityProfile,
)
from whale.ingest.ports.source.source_write_port import SourceWritePort
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.ingest.usecases.dtos.source_write_request import (
    SourceWriteExecutionOptions,
    SourceWriteItemData,
)
from whale.ingest.usecases.dtos.source_write_result import SourceWriteItemResult, SourceWriteResult
from whale.shared.crosscutting.auth import AccessDecision, AccessPolicyPort, Permission, Principal


@dataclass
class _RecordingWritePort(SourceWritePort):
    """Fake write port that records calls for verification."""

    called: bool = False
    last_execution: object = None

    async def write(self, execution, connection, items):
        self.called = True
        self.last_execution = execution
        return SourceWriteResult(
            request_id="test",
            command_id=None,
            dry_run=False,
            success_count=len(items),
            failure_count=0,
            results=[
                SourceWriteItemResult(key=item.key, node_id=item.node_id, ok=True)
                for item in items
            ],
        )


class _AllowAllPolicy(AccessPolicyPort):
    """Allow every requested permission."""

    def evaluate(self, principal: Principal, permission: Permission) -> AccessDecision:
        return AccessDecision(allowed=True)


class _DenyAllPolicy(AccessPolicyPort):
    """Deny every requested permission."""

    def evaluate(self, principal: Principal, permission: Permission) -> AccessDecision:
        return AccessDecision(allowed=False, reason="denied by test policy")


@dataclass
class _RecordPolicy(AccessPolicyPort):
    """Record the last evaluated permission for inspection."""

    last_permission: Permission | None = None
    decision: AccessDecision = field(default_factory=lambda: AccessDecision(allowed=True))

    def evaluate(self, principal: Principal, permission: Permission) -> AccessDecision:
        self.last_permission = permission
        return self.decision


def _make_items(count: int = 1) -> list[SourceWriteItemData]:
    return [SourceWriteItemData(key=f"k{i}", node_id=f"n{i}", value_type="double", value="1.0") for i in range(count)]


@pytest.fixture
def principal() -> Principal:
    return Principal(principal_id="tester", principal_type="user", roles=("operator",))


@pytest.fixture
def connection() -> SourceConnectionData:
    return SourceConnectionData(host="10.0.0.1", port=4840, ied_name="IED1", ld_name="LD1", namespace_uri="")


@pytest.fixture
def execution() -> SourceWriteExecutionOptions:
    return SourceWriteExecutionOptions(protocol="opcua", transport="tcp", actor="tester")


def test_rejects_when_protocol_not_allowed(principal, execution, connection):
    """Port must reject writes for protocols not in the security profile."""
    inner = _RecordingWritePort()
    port = AuthorizedSourceWritePort(
        inner=inner,
        principal=principal,
        access_policy=_AllowAllPolicy(),
        security_profile=WriteSecurityProfile(),
    )
    with pytest.raises(PermissionError, match="Write not allowed for protocol 'opcua'"):
        asyncio_run(port.write(execution, connection, _make_items()))
    assert inner.called is False


def test_rejects_when_access_policy_denies(principal, execution, connection):
    """Port must reject writes when the access policy denies."""
    inner = _RecordingWritePort()
    port = AuthorizedSourceWritePort(
        inner=inner,
        principal=principal,
        access_policy=_DenyAllPolicy(),
        security_profile=WriteSecurityProfile(
            protocols={"opcua": ProtocolWriteProfile(allowed=True)},
        ),
    )
    with pytest.raises(PermissionError, match="denied by test policy"):
        asyncio_run(port.write(execution, connection, _make_items()))
    assert inner.called is False


def test_delegates_to_inner_when_allowed(principal, execution, connection):
    """Port must delegate to inner when both profile and policy allow."""
    inner = _RecordingWritePort()
    port = AuthorizedSourceWritePort(
        inner=inner,
        principal=principal,
        access_policy=_AllowAllPolicy(),
        security_profile=WriteSecurityProfile(
            protocols={"opcua": ProtocolWriteProfile(allowed=True)},
        ),
    )
    result = asyncio_run(port.write(execution, connection, _make_items()))
    assert inner.called is True
    assert result.success_count == 1


def test_passess_correct_permission_to_policy(principal, execution, connection):
    """Port must pass the correct resource_type and action to the policy."""
    policy = _RecordPolicy()
    port = AuthorizedSourceWritePort(
        inner=_RecordingWritePort(),
        principal=principal,
        access_policy=policy,
        security_profile=WriteSecurityProfile(
            protocols={"opcua": ProtocolWriteProfile(allowed=True)},
        ),
    )
    asyncio_run(port.write(execution, connection, _make_items()))
    assert policy.last_permission is not None
    assert policy.last_permission.resource_type == "source_write"
    assert policy.last_permission.action == "write:opcua"
    assert policy.last_permission.resource_id == "IED1"


def test_rejects_when_both_disallowed_and_denied(principal, execution, connection):
    """When profile denies AND policy denies, error must mention profile first."""
    inner = _RecordingWritePort()
    port = AuthorizedSourceWritePort(
        inner=inner,
        principal=principal,
        access_policy=_DenyAllPolicy(),
        security_profile=WriteSecurityProfile(),
    )
    with pytest.raises(PermissionError, match="Write not allowed for protocol 'opcua'"):
        asyncio_run(port.write(execution, connection, _make_items()))
    assert inner.called is False


def test_resolves_ied_name_or_ld_name_for_resource_id(principal, connection):
    """Port must use ied_name as resource_id, falling back to ld_name."""
    execution = SourceWriteExecutionOptions(protocol="modbus_tcp", transport="tcp", actor="tester")
    policy = _RecordPolicy()
    port = AuthorizedSourceWritePort(
        inner=_RecordingWritePort(),
        principal=principal,
        access_policy=policy,
        security_profile=WriteSecurityProfile(
            protocols={"modbus_tcp": ProtocolWriteProfile(allowed=True)},
        ),
    )
    no_ied = SourceConnectionData(host="10.0.0.1", port=502, ied_name="", ld_name="LD1", namespace_uri="")
    asyncio_run(port.write(execution, no_ied, _make_items()))
    assert policy.last_permission is not None
    assert policy.last_permission.resource_id == "LD1"


def test_modifies_nothing_on_inner_result(principal, execution, connection):
    """The decorator must pass through the inner result unchanged."""
    inner = _RecordingWritePort()
    port = AuthorizedSourceWritePort(
        inner=inner,
        principal=principal,
        access_policy=_AllowAllPolicy(),
        security_profile=WriteSecurityProfile(
            protocols={"opcua": ProtocolWriteProfile(allowed=True)},
        ),
    )
    result = asyncio_run(port.write(execution, connection, _make_items(3)))
    assert result.success_count == 3
    assert result.failure_count == 0
    assert len(result.results) == 3


def asyncio_run(coro):
    """Run one async call synchronously."""
    import asyncio
    return asyncio.run(coro)
