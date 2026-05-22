"""Shared pytest fixtures for current ingest and OPC UA simulator tests."""

from __future__ import annotations

import os
import socket
import sys
from pathlib import Path
from typing import Any, Generator, cast

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
OPCUA_SIM_TEMPLATE_DIR = (
    PROJECT_ROOT / "tools" / "source_simulation" / "adapters" / "opcua" / "templates"
)
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

_VALID_STATE_CACHE_BACKENDS = frozenset({"relational", "redis"})
_VALID_MESSAGE_BACKENDS = frozenset({"relational_outbox", "redis_streams", "kafka"})
_VALID_DATABASE_BACKENDS = frozenset({"sqlite", "postgresql"})
_ROOT_OUTPUT_ARTIFACTS = (
    "all_test_output.txt",
    "compile_output.txt",
    "fail_fast_output.txt",
    "mypy_output.txt",
    "profile_test_output.txt",
    "pytest_out.txt",
    "test_output.txt",
    "output.log",
    "pytest_output.log",
    "pytest_output_v2.log",
    "test_out.log",
    "test_output.log",
)


def _cleanup_root_output_artifacts() -> None:
    """Remove known root-level test/output artifacts to keep repo clean."""

    for name in _ROOT_OUTPUT_ARTIFACTS:
        path = PROJECT_ROOT / name
        if path.is_file():
            path.unlink()


def pytest_configure(config: pytest.Config) -> None:
    """Ensure valid ingest backend env vars before test collection.

    Shell-level env vars may carry stale or invalid values from previous
    experiments. This hook corrects any invalid backend selections to safe
    lightweight defaults before whale.ingest.config is first imported.
    """
    if os.environ.get("WHALE_INGEST_DATABASE_BACKEND", "") not in _VALID_DATABASE_BACKENDS:
        os.environ["WHALE_INGEST_DATABASE_BACKEND"] = "sqlite"
    if os.environ.get("WHALE_INGEST_STATE_CACHE_BACKEND", "") not in _VALID_STATE_CACHE_BACKENDS:
        os.environ["WHALE_INGEST_STATE_CACHE_BACKEND"] = "relational"
    if os.environ.get("WHALE_INGEST_MESSAGE_BACKEND", "") not in _VALID_MESSAGE_BACKENDS:
        os.environ["WHALE_INGEST_MESSAGE_BACKEND"] = "relational_outbox"


def pytest_sessionstart(session: pytest.Session) -> None:
    """Clean root-level output artifacts before tests start."""

    _cleanup_root_output_artifacts()


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Clean root-level output artifacts when tests finish."""

    _cleanup_root_output_artifacts()


@pytest.fixture()
def sample_nodeset_path() -> str:
    """Return the standard OPC UA NodeSet path for simulator tests.

    Returns:
        String path to the NodeSet fixture.
    """
    return str(OPCUA_SIM_TEMPLATE_DIR / "OPCUANodeSet.xml")


@pytest.fixture()
def sample_opcua_connections_path() -> str:
    """Return the sample OPC UA connection config path for simulator tests.

    Returns:
        String path to the connection YAML fixture.
    """
    return str(OPCUA_SIM_TEMPLATE_DIR / "OPCUA_client_connections.yaml")


@pytest.fixture()
def free_ports() -> tuple[int, int]:
    """Return two currently free ports for simulator integration tests.

    Returns:
        Two free ports discovered from the OS.
    """
    ports: list[int] = []
    sockets: list[socket.socket] = []
    try:
        for _ in range(2):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("127.0.0.1", 0))
            sockets.append(sock)
            ports.append(int(sock.getsockname()[1]))
    finally:
        for sock in sockets:
            sock.close()
    if len(ports) != 2:
        raise RuntimeError("Could not allocate two free ports for OPC UA simulator tests.")
    return ports[0], ports[1]


@pytest.fixture()
def local_opcua_connections_path(
    tmp_path: Path,
    sample_opcua_connections_path: str,
    free_ports: tuple[int, int],
) -> str:
    """Write a localhost-only connection YAML for integration tests.

    Args:
        tmp_path: Temporary directory for test-local fixture output.
        sample_opcua_connections_path: Source fixture config path.
        free_ports: Two free localhost ports allocated for the current test.

    Returns:
        Path to the rewritten localhost connection YAML.
    """
    config = cast(
        dict[str, object],
        yaml.safe_load(Path(sample_opcua_connections_path).read_text(encoding="utf-8")),
    )
    connections = cast(list[dict[str, object]], config["connections"])
    connections[0]["endpoint"] = f"opc.tcp://127.0.0.1:{free_ports[0]}"
    connections[1]["endpoint"] = f"opc.tcp://127.0.0.1:{free_ports[1]}"
    path = tmp_path / "OPCUA_client_connections.local.yaml"
    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return str(path)


@pytest.fixture()
def opcua_server_runtime(
    sample_nodeset_path: str,
    local_opcua_connections_path: str,
) -> Generator[Any, None, None]:
    """Start a single simulator server for integration tests.

    Args:
        sample_nodeset_path: NodeSet XML fixture path.
        local_opcua_connections_path: Localhost-only connection YAML path.

    Yields:
        Running single-server runtime using the first connection entry.
    """
    from tools.opcua_sim.server_runtime import OpcUaServerRuntime, load_server_config

    runtime = OpcUaServerRuntime(
        nodeset_path=sample_nodeset_path,
        config=load_server_config(local_opcua_connections_path, "WTG_01"),
    )
    with runtime:
        yield runtime


@pytest.fixture()
def opcua_sim_fleet(
    sample_nodeset_path: str,
    local_opcua_connections_path: str,
) -> Generator[Any, None, None]:
    """Start all simulator servers described by the localhost test YAML.

    Args:
        sample_nodeset_path: NodeSet XML fixture path.
        local_opcua_connections_path: Localhost-only connection YAML path.

    Yields:
        Running fleet runtime for both wind turbine servers.
    """
    from tools.opcua_sim.fleet_runtime import OpcUaFleetRuntime

    fleet = OpcUaFleetRuntime.from_connection_config(
        nodeset_path=sample_nodeset_path,
        config_path=local_opcua_connections_path,
    )
    with fleet:
        yield fleet
