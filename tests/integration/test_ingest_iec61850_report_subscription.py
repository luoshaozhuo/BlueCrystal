"""IEC 61850 Report subscription integration tests.

Tests the full pipeline: simulator -> report runner -> backend -> adapter -> callback.
"""

from __future__ import annotations

import asyncio
import subprocess
import time
from pathlib import Path

import pytest

from whale.ingest.adapters.source.iec61850_report_source_acquisition_adapter import (
    Iec61850ReportSourceAcquisitionAdapter,
)
from whale.ingest.usecases.dtos.acquired_node_state import AcquiredNodeStateBatch
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData

_REPO_ROOT = Path(__file__).resolve().parents[2]
_NATIVE_BUILD_DIR = _REPO_ROOT / "tools" / "source_lab" / "native" / "build"
_SIMULATOR_EXE = _NATIVE_BUILD_DIR / "iec61850_simulator_server"
_RUNNER_EXE = _NATIVE_BUILD_DIR / "iec61850_report_runner"


def _require_binaries() -> None:
    missing = []
    if not _SIMULATOR_EXE.exists():
        missing.append(str(_SIMULATOR_EXE))
    if not _RUNNER_EXE.exists():
        missing.append(str(_RUNNER_EXE))
    if missing:
        pytest.skip(f"Missing binaries: {', '.join(missing)}")


def _find_free_port() -> int:
    """Find a free TCP port."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def simulator_port() -> int:
    """Start the IEC 61850 simulator and yield its port."""
    port = _find_free_port()
    proc = subprocess.Popen(
        [str(_SIMULATOR_EXE), str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Wait for READY
    start = time.monotonic()
    ready_line = b""
    while time.monotonic() - start < 10:
        assert proc.stdout is not None
        line = proc.stdout.readline()
        if b"READY" in line:
            ready_line = line
            break
    assert ready_line, f"Simulator did not become ready; stderr: {proc.stderr.read(1024) if proc.stderr else b''}"
    yield port
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


@pytest.mark.asyncio
async def test_report_subscription_receives_events(simulator_port: int) -> None:
    """完整的 Report 订阅集成测试: simulator → C runner → backend → adapter → callback."""
    _require_binaries()

    adapter = Iec61850ReportSourceAcquisitionAdapter()
    connection = SourceConnectionData(
        host="127.0.0.1",
        port=simulator_port,
        ied_name="Simulator",
        ld_name="Simulator",
        namespace_uri="",
        params={},
    )
    execution = AcquisitionExecutionOptions(
        protocol="iec61850",
        transport="tcp",
        acquisition_mode="subscription",
        interval_ms=0,
        max_iteration=None,
        request_timeout_ms=15000,
        freshness_timeout_ms=5000,
        alive_timeout_ms=15000,
        subscription_start_interval_ms=0,
        params={},
    )
    items = [
        AcquisitionItemData(key="key_0", profile_item_id=0, relative_path="Ind1.stVal"),
        AcquisitionItemData(key="key_1", profile_item_id=1, relative_path="Ind2.stVal"),
        AcquisitionItemData(key="key_2", profile_item_id=2, relative_path="AnIn1.mag"),
    ]

    received_batches: list[AcquiredNodeStateBatch] = []

    async def on_batch(batch: AcquiredNodeStateBatch) -> None:
        received_batches.append(batch)

    handle = await adapter.start_subscription(
        execution, connection, items,
        state_received=on_batch,
    )

    # Wait for simulator to trigger data changes (simulator updates every 1s)
    await asyncio.sleep(4)

    assert len(received_batches) >= 1, (
        f"Expected at least 1 report event, got {len(received_batches)}"
    )

    # Verify batch content
    batch = received_batches[0]
    assert not batch.is_empty()
    assert batch.attributes.get("acquisition_kind") == "report_subscription"
    assert len(batch.values) >= 1

    # Cleanup
    await handle.close()


@pytest.mark.asyncio
async def test_report_subscription_close_releases_resources(simulator_port: int) -> None:
    """停止订阅后资源释放验证。"""
    _require_binaries()

    adapter = Iec61850ReportSourceAcquisitionAdapter()
    connection = SourceConnectionData(
        host="127.0.0.1",
        port=simulator_port,
        ied_name="Simulator",
        ld_name="Simulator",
        namespace_uri="",
        params={},
    )
    execution = AcquisitionExecutionOptions(
        protocol="iec61850",
        transport="tcp",
        acquisition_mode="subscription",
        interval_ms=0,
        max_iteration=None,
        request_timeout_ms=15000,
        freshness_timeout_ms=5000,
        alive_timeout_ms=15000,
        subscription_start_interval_ms=0,
        params={},
    )
    items = [AcquisitionItemData(key="key_0", profile_item_id=0, relative_path="Ind1.stVal")]

    async def on_batch(batch: AcquiredNodeStateBatch) -> None:
        pass

    handle = await adapter.start_subscription(
        execution, connection, items,
        state_received=on_batch,
    )

    # Let it run briefly
    await asyncio.sleep(1)

    # Close
    await handle.close()

    # Verify no crashes after close
    await asyncio.sleep(0.5)
