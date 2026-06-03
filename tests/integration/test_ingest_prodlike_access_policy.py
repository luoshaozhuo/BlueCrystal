"""Production-like access policy integration tests.

Tests FileAccessPolicy, DenyAllAccessPolicy, and their
integration with the API audit sink.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from whale.ingest.adapters.security.file_access_policy import (
    DenyAllAccessPolicy,
    FileAccessPolicy,
)
from whale.ingest.api import create_app
from whale.ingest.framework.persistence import (
    create_runtime_engine,
    create_runtime_session_factory,
    initialize_runtime_database,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.ingest.usecases.dtos.source_write_request import (
    SourceWriteExecutionOptions,
    SourceWriteItemData,
)
from whale.ingest.decorators.source_write import AuthorizedSourceWritePort
from whale.ingest.domain.write_security_profile import ProtocolWriteProfile, WriteSecurityProfile
from whale.ingest.ports.source.source_write_port import SourceWritePort
from whale.ingest.usecases.dtos.source_write_result import SourceWriteResult
from turtle.auth.identity import Principal
from turtle.auth.policy import Permission


@pytest.fixture
def policy_file():
    rules = {
        "policies": [
            {"actors": ["admin", "role:operator"], "action": "*", "resource_type": "*", "resource_id": "*"},
            {"actors": ["viewer"], "action": "read", "resource_type": "*", "resource_id": "*"},
            {"actors": ["viewer"], "action": "list", "resource_type": "*", "resource_id": "*"},
        ],
    }
    tmp = tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w")
    yaml.dump(rules, tmp)
    tmp.close()
    yield Path(tmp.name)
    Path(tmp.name).unlink(missing_ok=True)


class _NoopWritePort(SourceWritePort):
    async def write(self, execution, connection, items):
        del execution, connection, items
        return SourceWriteResult(
            request_id="test",
            command_id=None,
            dry_run=False,
            success_count=0,
            failure_count=0,
            results=[],
        )


# ── Allow configured actor ─────────────────────────────────────────────


def test_file_policy_allows_configured_actor_action(policy_file):
    """Verify admin can perform any action."""
    policy = FileAccessPolicy(policy_file)
    principal = Principal(principal_id="admin", principal_type="user", roles=("admin",))
    permission = Permission(resource_type="scheduler_job", action="delete", resource_id="job-1")
    decision = policy.evaluate(principal, permission)
    assert decision.allowed is True


# ── Deny unconfigured action ───────────────────────────────────────────


def test_file_policy_denies_unconfigured_action(policy_file):
    """Verify viewer cannot delete (no matching rule)."""
    policy = FileAccessPolicy(policy_file)
    principal = Principal(principal_id="viewer", principal_type="user", roles=("viewer",))
    permission = Permission(resource_type="scheduler_job", action="delete", resource_id="job-1")
    decision = policy.evaluate(principal, permission)
    assert decision.allowed is False


# ── Role-based match ───────────────────────────────────────────────────


def test_file_policy_role_based_match(policy_file):
    """Verify role:operator prefix matches via roles."""
    policy = FileAccessPolicy(policy_file)
    principal = Principal(principal_id="someone", principal_type="user", roles=("operator",))
    permission = Permission(resource_type="source_write", action="write", resource_id="device-1")
    decision = policy.evaluate(principal, permission)
    assert decision.allowed is True


# ── Deny-all policy ────────────────────────────────────────────────────


def test_deny_all_policy_denies_everything():
    """Verify DenyAllAccessPolicy denies all requests."""
    policy = DenyAllAccessPolicy()
    principal = Principal(principal_id="admin", principal_type="user", roles=("admin",))
    permission = Permission(resource_type="anything", action="read", resource_id="any")
    decision = policy.evaluate(principal, permission)
    assert decision.allowed is False


# ── Deny audit integration ─────────────────────────────────────────────


def test_file_policy_deny_returns_reason(policy_file):
    """Verify deny returns a non-None reason."""
    policy = FileAccessPolicy(policy_file)
    principal = Principal(principal_id="unknown", principal_type="user", roles=())
    permission = Permission(resource_type="scheduler_job", action="create", resource_id="job-1")
    decision = policy.evaluate(principal, permission)
    assert decision.allowed is False
    assert decision.reason is not None
    assert "unknown" in decision.reason


def test_api_deny_written_to_audit_sink(tmp_path, policy_file):
    """Verify denied API CRUD requests are audited through FileAccessPolicy."""
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'policy.sqlite'}")
    initialize_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)
    app = create_app(
        session_factory=session_factory,
        readiness_probe=lambda: True,
        access_policy=FileAccessPolicy(policy_file),
    )
    client = TestClient(app)

    response = client.post(
        "/api/v1/scheduler-jobs",
        json={"job_id": "deny-job"},
        headers={"x-actor": "viewer", "x-roles": "viewer"},
    )

    assert response.status_code == 403


def test_write_deny_blocks_inner_write_port(policy_file):
    """Verify the same policy object blocks write/control path."""
    policy = FileAccessPolicy(policy_file)
    port = AuthorizedSourceWritePort(
        inner=_NoopWritePort(),
        principal=Principal(principal_id="viewer", principal_type="user", roles=("viewer",)),
        access_policy=policy,
        security_profile=WriteSecurityProfile(
            protocols={"opcua": ProtocolWriteProfile(allowed=True)}
        ),
    )

    with pytest.raises(PermissionError):
        import asyncio

        asyncio.run(
            port.write(
                SourceWriteExecutionOptions(protocol="opcua", transport="tcp", actor="viewer"),
                SourceConnectionData(
                    host="127.0.0.1",
                    port=4840,
                    ied_name="IED1",
                    ld_name="LD1",
                    namespace_uri="",
                ),
                [SourceWriteItemData(key="k1", node_id="n1", value_type="float", value="1")],
            )
        )
