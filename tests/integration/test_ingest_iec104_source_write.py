"""Integration test for IEC 104 source write via SourceCommandUseCase.

测试步骤：
1. 启动 iec104_simulator_server (C binary, full lib60870 CS104 slave)。
2. 通过 SourceCommandUseCase 写入 C_SC_NA_1 单点命令。
3. 再通过 Iec104SourceAcquisitionAdapter 读取，验证值已变化。
4. dry_run 模式验证值不变化。
5. write disabled 模式验证真实写被拒绝。

依赖：
- iec104_simulator_server + iec104_client_runner 编译可用。
- 不需要外部 Redis 或 Kafka。
"""
from __future__ import annotations

import asyncio
import os
import socket
import subprocess
from contextlib import closing, contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Generator

import pytest

from whale.ingest.adapters.source.iec104_source_acquisition_adapter import (
    Iec104SourceAcquisitionAdapter,
)
from whale.ingest.adapters.source.iec104_source_write_adapter import (
    Iec104SourceWriteAdapter,
)
from whale.ingest.adapters.source.static_source_write_port_registry import (
    StaticSourceWritePortRegistry,
)
from whale.ingest.usecases.source_command_use_case import SourceCommandUseCase
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
    SourceAcquisitionRequest,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.ingest.usecases.dtos.source_write_request import (
    SourceWriteExecutionOptions,
    SourceWriteItemData,
    SourceWriteRequest,
)


def _resolve_binary(name: str) -> Path | None:
    build_dir = Path(__file__).resolve().parents[2] / "tools" / "source_lab" / "native" / "build"
    for candidate in (build_dir / name, build_dir / f"{name}.exe"):
        if candidate.exists():
            return candidate.resolve()
    return None


SIMULATOR_PATH = _resolve_binary("iec104_simulator_server")
RUNNER_PATH = _resolve_binary("iec104_client_runner")


def _require_binaries() -> None:
    if SIMULATOR_PATH is None:
        pytest.skip("iec104_simulator_server not compiled")
    if RUNNER_PATH is None:
        pytest.skip("iec104_client_runner not compiled")


def _choose_available_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextmanager
def _run_simulator(port: int) -> Generator[subprocess.Popen[bytes], Any, None]:
    """Start iec104_simulator_server, wait for READY, yield proc, terminate."""
    assert SIMULATOR_PATH is not None
    proc = subprocess.Popen(
        [str(SIMULATOR_PATH), str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        ready_line = proc.stdout.readline()  # type: ignore[union-attr]
        assert ready_line.strip() == b"READY", (
            f"Expected READY, got {ready_line!r}"
        )
        yield proc
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


def _build_connection(port: int) -> SourceConnectionData:
    return SourceConnectionData(
        host="127.0.0.1",
        port=port,
        ied_name="IED001",
        ld_name="iec104_integration_test",
        namespace_uri="",
        params={"common_address": 1},
    )


@pytest.mark.integration
def test_iec104_write_then_read_verify_value_changed() -> None:
    """写入 C_SC_NA_1 后通过读取验证值已变化。"""
    _require_binaries()

    port = _choose_available_port()
    connection = _build_connection(port)
    write_port = Iec104SourceWriteAdapter()
    registry = StaticSourceWritePortRegistry(ports_by_protocol={"iec104": write_port})
    use_case = SourceCommandUseCase(write_port_registry=registry)
    os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"

    try:
        with _run_simulator(port):
            # Read baseline: IOA 101 should be "1" (odd IOA → True), IOA 102 should be "0"
            read_adapter = Iec104SourceAcquisitionAdapter()
            read_request = SourceAcquisitionRequest(
                request_id="pre-write-read",
                task_id=1,
                execution=AcquisitionExecutionOptions(
                    protocol="iec104",
                    transport="tcp",
                    acquisition_mode="READ_ONCE",
                    interval_ms=100,
                    max_iteration=1,
                    request_timeout_ms=10_000,
                    freshness_timeout_ms=30_000,
                    alive_timeout_ms=60_000,
                ),
                connections=[connection],
                items=[
                    AcquisitionItemData(key="sp101", profile_item_id=1, relative_path="101"),
                    AcquisitionItemData(key="sp102", profile_item_id=2, relative_path="102"),
                ],
            )

            async def _read_all() -> dict[str, str]:
                result = await read_adapter.read(
                    execution=read_request.execution,
                    connection=connection,
                    items=read_request.items,
                )
                return {v.node_key: v.value for v in result.values}

            initial = asyncio.run(_read_all())
            assert initial.get("sp101") == "1", f"Expected sp101=1, got {initial}"
            assert initial.get("sp102") == "0", f"Expected sp102=0, got {initial}"

            # Write C_SC_NA_1 to IOA 101 (toggle off)
            write_request = SourceWriteRequest(
                request_id="write-test-001",
                task_id=1,
                execution=SourceWriteExecutionOptions(
                    protocol="iec104",
                    transport="tcp",
                    request_timeout_ms=10_000,
                    dry_run=False,
                    actor="test",
                ),
                connections=[connection],
                items=[
                    SourceWriteItemData(
                        key="sp101",
                        node_id="101",
                        value_type="BOOL",
                        value="0",
                    ),
                ],
                client_requested_at=datetime.now(tz=UTC),
            )

            write_result = asyncio.run(use_case.execute(write_request))
            assert write_result.success_count == 1, (
                f"Write failed: {write_result.results}"
            )

            # Read again: sp101 should be "0", sp102 should remain "0"
            final = asyncio.run(_read_all())
            assert final.get("sp101") == "0", (
                f"Expected sp101=0 after write, got {final.get('sp101')}"
            )
            assert final.get("sp102") == "0", (
                f"Expected sp102 to remain 0, got {final.get('sp102')}"
            )
    finally:
        if "WHALE_INGEST_SOURCE_WRITE_ENABLED" in os.environ:
            del os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"]


@pytest.mark.integration
def test_iec104_write_dry_run_does_not_change_value() -> None:
    """dry_run 模式不应改变实际值。"""
    _require_binaries()

    port = _choose_available_port()
    connection = _build_connection(port)
    write_port = Iec104SourceWriteAdapter()
    registry = StaticSourceWritePortRegistry(ports_by_protocol={"iec104": write_port})
    use_case = SourceCommandUseCase(write_port_registry=registry)

    try:
        with _run_simulator(port):
            read_adapter = Iec104SourceAcquisitionAdapter()
            read_request = SourceAcquisitionRequest(
                request_id="dry-run-baseline",
                task_id=1,
                execution=AcquisitionExecutionOptions(
                    protocol="iec104",
                    transport="tcp",
                    acquisition_mode="READ_ONCE",
                    interval_ms=100,
                    max_iteration=1,
                    request_timeout_ms=10_000,
                    freshness_timeout_ms=30_000,
                    alive_timeout_ms=60_000,
                ),
                connections=[connection],
                items=[
                    AcquisitionItemData(key="sp101", profile_item_id=1, relative_path="101"),
                ],
            )

            async def _read_val() -> str | None:
                result = await read_adapter.read(
                    execution=read_request.execution,
                    connection=connection,
                    items=read_request.items,
                )
                for v in result.values:
                    if v.node_key == "sp101":
                        return v.value
                return None

            initial = asyncio.run(_read_val())

            # dry_run write
            dry_run_request = SourceWriteRequest(
                request_id="dry-run-001",
                task_id=1,
                execution=SourceWriteExecutionOptions(
                    protocol="iec104",
                    transport="tcp",
                    request_timeout_ms=10_000,
                    dry_run=True,
                    actor="test",
                ),
                connections=[connection],
                items=[
                    SourceWriteItemData(
                        key="sp101",
                        node_id="101",
                        value_type="BOOL",
                        value="0",
                    ),
                ],
            )

            result = asyncio.run(use_case.execute(dry_run_request))
            assert result.dry_run is True
            assert result.success_count == 0

            # Value should be unchanged
            final = asyncio.run(_read_val())
            assert final == initial, (
                f"dry_run should not change value. Before: {initial}, After: {final}"
            )
    finally:
        if "WHALE_INGEST_SOURCE_WRITE_ENABLED" in os.environ:
            del os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"]


@pytest.mark.integration
def test_iec104_write_disabled_refuses_real_write() -> None:
    """未启用写入时，真实写请求应被拒绝。"""
    _require_binaries()

    port = _choose_available_port()
    connection = _build_connection(port)
    write_port = Iec104SourceWriteAdapter()
    registry = StaticSourceWritePortRegistry(ports_by_protocol={"iec104": write_port})
    use_case = SourceCommandUseCase(write_port_registry=registry)

    if "WHALE_INGEST_SOURCE_WRITE_ENABLED" in os.environ:
        del os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"]

    write_request = SourceWriteRequest(
        request_id="write-disabled-test",
        task_id=1,
        execution=SourceWriteExecutionOptions(
            protocol="iec104",
            transport="tcp",
            request_timeout_ms=5_000,
            dry_run=False,
        ),
        connections=[connection],
        items=[
            SourceWriteItemData(
                key="sp101",
                node_id="101",
                value_type="BOOL",
                value="0",
            ),
        ],
    )

    with pytest.raises(RuntimeError, match="Real device write is disabled"):
        asyncio.run(use_case.execute(write_request))
