"""IEC104 production capacity and profile gate.

本测试显式验证 IEC104 的生产能力门禁，确保不是仅 registry/gate 层面通过。

验证内容：
1. supports_access_mode("iec104", "polling") == True
2. build_capacity_runner("iec104") 可构建
3. Python Iec104Simulator 可 start/writes/stop
4. iec104_client_runner 二进制存在
5. iec104_simulator_server 二进制存在
6. read_once 实测（启动 C server，通过 Iec104SourceAcquisitionAdapter 读取）
7. write_then_readback 实测（写入 C_SC_NA_1 后读取验证状态变更）

不允许 skipped — 所有门禁必须明确通过或失败。
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

from tools.source_lab.access.runners.registry import build_capacity_runner, supports_access_mode
from tools.source_lab.factory import build_simulator
from tools.source_lab.model import SimulatedPoint, SimulatedSource, SourceConnection
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

_REPO_ROOT = Path(__file__).resolve().parents[4]
_NATIVE_BUILD = _REPO_ROOT / "tools" / "source_lab" / "native" / "build"


def _resolve_binary(name: str) -> Path | None:
    for candidate in (_NATIVE_BUILD / name, _NATIVE_BUILD / f"{name}.exe"):
        if candidate.exists():
            return candidate.resolve()
    return None


def _choose_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextmanager
def _run_simulator_server(port: int) -> Generator[subprocess.Popen[bytes], Any, None]:
    """Start iec104_simulator_server, wait for READY, yield, then terminate."""
    sim_path = _resolve_binary("iec104_simulator_server")
    assert sim_path is not None, "iec104_simulator_server not compiled"
    proc = subprocess.Popen(
        [str(sim_path), str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        ready = proc.stdout.readline()  # type: ignore[union-attr]
        assert ready.strip() == b"READY", f"Expected READY, got {ready!r}"
        yield proc
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


# ── 1. Registry / framework gate ─────────────────────────────────────────────


def test_iec104_supports_polling_access_mode() -> None:
    """IEC104 must support polling access mode."""
    assert supports_access_mode("iec104", "polling") is True


def test_iec104_capacity_runner_can_be_built() -> None:
    """build_capacity_runner must return a concrete runner for iec104."""
    runner = build_capacity_runner("iec104")
    assert runner is not None
    assert runner.name.endswith("runner")


def test_iec104_python_simulator_can_start_and_stop() -> None:
    """Python Iec104Simulator must start/writes/stop without error."""
    port = _choose_free_port()
    source = SimulatedSource(
        connection=SourceConnection(
            name="iec104-gate-test", ied_name="IED1", ld_name="LD0",
            host="127.0.0.1", port=port, transport="tcp", protocol="iec104",
        ),
        points=(SimulatedPoint(ln_name="", do_name="0", unit=None, data_type="BOOL", initial_value=True),),
    )
    simulator = build_simulator(source)
    simulator.start()
    simulator.writes({"0": False})
    simulator.stop()


# ── 2. Binary existence gate ─────────────────────────────────────────────────


def test_iec104_client_runner_binary_exists() -> None:
    """iec104_client_runner must be compiled."""
    path = _resolve_binary("iec104_client_runner")
    assert path is not None, (
        "iec104_client_runner not found in native/build. "
        "Run cmake --build . to compile."
    )
    assert path.exists()


def test_iec104_simulator_server_binary_exists() -> None:
    """iec104_simulator_server must be compiled."""
    path = _resolve_binary("iec104_simulator_server")
    assert path is not None, (
        "iec104_simulator_server not found in native/build. "
        "Run cmake --build . to compile."
    )
    assert path.exists()


# ── 3. Read_once gate ────────────────────────────────────────────────────────


@pytest.mark.integration
def test_iec104_read_once_via_acquisition_adapter() -> None:
    """Start C simulator server, read IOA 101 via acquisition adapter."""
    sim_path = _resolve_binary("iec104_simulator_server")
    if sim_path is None:
        pytest.fail("iec104_simulator_server not compiled — cannot test read_once")
    client_path = _resolve_binary("iec104_client_runner")
    if client_path is None:
        pytest.fail("iec104_client_runner not compiled — cannot test read_once")

    port = _choose_free_port()
    connection = SourceConnectionData(
        host="127.0.0.1", port=port, ied_name="IED001",
        ld_name="iec104_gate_test", namespace_uri="",
        params={"common_address": 1},
    )

    with _run_simulator_server(port):
        adapter = Iec104SourceAcquisitionAdapter()
        read_request = SourceAcquisitionRequest(
            request_id="gate-read-once",
            task_id=1,
            execution=AcquisitionExecutionOptions(
                protocol="iec104", transport="tcp", acquisition_mode="READ_ONCE",
                interval_ms=100, max_iteration=1, request_timeout_ms=10_000,
                freshness_timeout_ms=30_000, alive_timeout_ms=60_000,
            ),
            connections=[connection],
            items=[AcquisitionItemData(key="sp101", profile_item_id=1, relative_path="101")],
        )

        result = asyncio.run(adapter.read(
            execution=read_request.execution,
            connection=connection,
            items=read_request.items,
        ))
        assert result is not None
        assert len(result.values) == 1
        val = result.values[0]
        assert val.quality == "GOOD", f"Expected GOOD quality, got {val.quality}"
        assert val.value in ("0", "1"), f"Expected SP value 0 or 1, got {val.value!r}"


# ── 4. Write_then_readback gate ──────────────────────────────────────────────


@pytest.mark.integration
def test_iec104_write_then_readback() -> None:
    """Write C_SC_NA_1 to simulator server, then read back to verify change."""
    sim_path = _resolve_binary("iec104_simulator_server")
    if sim_path is None:
        pytest.fail("iec104_simulator_server not compiled")
    client_path = _resolve_binary("iec104_client_runner")
    if client_path is None:
        pytest.fail("iec104_client_runner not compiled")

    port = _choose_free_port()
    connection = SourceConnectionData(
        host="127.0.0.1", port=port, ied_name="IED001",
        ld_name="iec104_gate_test", namespace_uri="",
        params={"common_address": 1},
    )

    try:
        os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"
        with _run_simulator_server(port):
            read_adapter = Iec104SourceAcquisitionAdapter()
            write_port = Iec104SourceWriteAdapter()
            registry = StaticSourceWritePortRegistry(ports_by_protocol={"iec104": write_port})
            use_case = SourceCommandUseCase(write_port_registry=registry)

            # Read baseline — IOA 101 starts as 1 (odd IOA → True)
            read_request = SourceAcquisitionRequest(
                request_id="gate-read-baseline",
                task_id=1,
                execution=AcquisitionExecutionOptions(
                    protocol="iec104", transport="tcp", acquisition_mode="READ_ONCE",
                    interval_ms=100, max_iteration=1, request_timeout_ms=10_000,
                    freshness_timeout_ms=30_000, alive_timeout_ms=60_000,
                ),
                connections=[connection],
                items=[AcquisitionItemData(key="sp101", profile_item_id=1, relative_path="101")],
            )

            async def _read() -> str:
                result = await read_adapter.read(
                    execution=read_request.execution,
                    connection=connection,
                    items=read_request.items,
                )
                return result.values[0].value

            baseline = asyncio.run(_read())
            assert baseline == "1", f"Expected baseline sp101=1, got {baseline!r}"

            # Write value="0" (toggle off)
            write_request = SourceWriteRequest(
                request_id="gate-write-001", task_id=1,
                execution=SourceWriteExecutionOptions(
                    protocol="iec104", transport="tcp",
                    request_timeout_ms=10_000, dry_run=False, actor="gate-test",
                ),
                connections=[connection],
                items=[SourceWriteItemData(key="sp101", node_id="101", value_type="BOOL", value="0")],
                client_requested_at=datetime.now(tz=UTC),
            )

            write_result = asyncio.run(use_case.execute(write_request))
            assert write_result.success_count == 1, (
                f"Write failed: {write_result.results}"
            )

            # Read back — sp101 should now be "0"
            after = asyncio.run(_read())
            assert after == "0", f"Expected sp101=0 after write, got {after!r}"
    finally:
        os.environ.pop("WHALE_INGEST_SOURCE_WRITE_ENABLED", None)
