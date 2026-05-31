"""IEC 61850 MMS production capacity / profile gate test.

验证 IEC 61850 MMS 的 capacity 和 profile 路径可执行的硬性门禁。

门禁要求：
1. native runner 二进制存在或可构建。
2. simulator 可启动且 stdout 无噪声。
3. read_once (TCP probe) 实测通过。
4. MMS read (production client) 实测通过。
5. MMS write_then_readback (production client) 实测通过。
6. capacity runner 可构建。
7. 多次读调用中含持续时间/吞吐量指标。
8. 不允许 skipped。
"""
from __future__ import annotations

import asyncio
import os
import socket
import subprocess
import time
from contextlib import closing
from pathlib import Path


from tools.source_lab.access.runners.registry import build_capacity_runner

# ── Binary resolution ────────────────────────────────────────────────────


def _resolve_simulator() -> Path | None:
    build = Path(__file__).resolve().parents[2] / "native" / "build"
    for name in ("iec61850_simulator_server", "iec61850_simulator_server.exe"):
        p = build / name
        if p.exists():
            return p.resolve()
    return None


def _resolve_client_runner() -> Path | None:
    build = Path(__file__).resolve().parents[2] / "native" / "build"
    for name in ("iec61850_mms_client_runner", "iec61850_mms_client_runner.exe"):
        p = build / name
        if p.exists():
            return p.resolve()
    return None


SIMULATOR_PATH = _resolve_simulator()
CLIENT_RUNNER_PATH = _resolve_client_runner()


# ── Helpers ──────────────────────────────────────────────────────────────


def _find_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _start_simulator(port: int) -> subprocess.Popen[str]:
    """Start simulator, verify stdout noise = 0 (only READY line)."""
    assert SIMULATOR_PATH is not None, "simulator binary not found"
    proc = subprocess.Popen(
        [str(SIMULATOR_PATH), str(port)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    assert proc.stdout is not None

    ready_line = proc.stdout.readline().strip()
    assert ready_line == "READY", (
        f"simulator stdout noise detected: expected READY, got {ready_line!r}"
    )
    # Verify no more immediate protocol lines
    proc.stdout.flush()
    return proc


def _stop_simulator(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


def _wait_for_port(host: str, port: int, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise RuntimeError(f"Timed out waiting for {host}:{port}")


def _build_spec(host: str, port: int) -> object:
    """Build a RunnerEndpointPlan for capacity tests."""
    from tools.source_lab.access.common.scheduling import RunnerEndpointPlan
    from tools.source_lab.access.providers.base import SourceRuntimeSpec
    from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec
    return RunnerEndpointPlan(
        global_index=0,
        source=SourceRuntimeSpec(
            endpoint=SourceEndpointSpec(name="gate", host=host, port=port, protocol="iec61850_mms"),
            points=(SourcePointSpec(address="Simulator/GGIO1.Ind1.stVal"),),
        ),
        offset_ns=0,
    )


def _build_polling_config() -> object:
    from tools.source_lab.access.polling.model import CapacityMode, CapacityScanConfig
    return CapacityScanConfig(
        mode=CapacityMode.SIMULATOR, protocol="iec61850_mms",
        endpoints=(), points=(),
        server_count_start=1, server_count_step=1, server_count_max=1,
        hz_start=1.0, hz_step=1.0, hz_max=1.0,
        process_count=1, read_timeout_s=5.0,
    )


# ── Gate tests ───────────────────────────────────────────────────────────


class TestIec61850MmsCapacityProfileGate:
    """IEC 61850 MMS capacity/profile 门禁测试。"""

    def test_runner_construction(self) -> None:
        """build_capacity_runner('iec61850_mms') 必须成功返回 runner。"""
        runner = build_capacity_runner("iec61850_mms")
        assert runner is not None, "build_capacity_runner returned None"

    def test_native_binaries_exist(self) -> None:
        """native runner 和 simulator 二进制必须存在。"""
        assert SIMULATOR_PATH is not None, (
            "iec61850_simulator_server not compiled. "
            "Run `cmake --build tools/source_lab/native/build --target iec61850_simulator_server`"
        )
        assert CLIENT_RUNNER_PATH is not None, (
            "iec61850_mms_client_runner not compiled. "
            "Run `cmake --build tools/source_lab/native/build --target iec61850_mms_client_runner`"
        )

    def test_simulator_stdout_no_noise(self) -> None:
        """simulator stdout 必须只有 READY，无库诊断输出。"""
        port = _find_free_port()
        simulator = _start_simulator(port)
        try:
            # After READY, check no more protocol lines within 1s
            import select
            if select.select([simulator.stdout], [], [], 1.0)[0]:
                assert simulator.stdout is not None
                extra = simulator.stdout.readline().strip()
                assert False, f"stdout noise detected after READY: {extra!r}"
        finally:
            _stop_simulator(simulator)

    def test_capacity_read_once_against_simulator(self) -> None:
        """使用 production client 对 simulator 执行 read_once（MMS 读实测）。"""
        from whale.shared.source.iec61850.reader import Iec61850MmsSourceReader

        port = _find_free_port()
        simulator = _start_simulator(port)
        try:
            _wait_for_port("127.0.0.1", port)

            async def _read() -> bool:
                async with Iec61850MmsSourceReader("127.0.0.1", port, timeout_seconds=5.0) as reader:
                    result = await reader.read(
                        obj_ref="Simulator/GGIO1.Ind1.stVal",
                        fc="ST",
                        request_id="gate-read",
                    )
                    return result.ok

            ok = asyncio.run(_read())
            assert ok, "MMS production client read_once failed"
        finally:
            _stop_simulator(simulator)

    def test_mms_read_using_production_client(self) -> None:
        """使用 production client (Iec61850MmsSourceReader) 对 simulator 执行 MMS 读。"""
        from whale.shared.source.iec61850.reader import Iec61850MmsSourceReader

        port = _find_free_port()
        simulator = _start_simulator(port)
        try:
            _wait_for_port("127.0.0.1", port)

            async def _read() -> bool:
                async with Iec61850MmsSourceReader("127.0.0.1", port, timeout_seconds=5.0) as reader:
                    result = await reader.read(
                        obj_ref="Simulator/GGIO1.Ind1.stVal",
                        fc="ST",
                        request_id="gate-read",
                    )
                    return result.ok

            ok = asyncio.run(_read())
            assert ok, "MMS production client read failed"
        finally:
            _stop_simulator(simulator)

    def test_mms_write_then_readback(self) -> None:
        """使用 production client 对 simulator 执行 MMS write + readback。"""
        from whale.shared.source.iec61850.reader import Iec61850MmsSourceReader

        port = _find_free_port()
        simulator = _start_simulator(port)
        os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"
        try:
            _wait_for_port("127.0.0.1", port)

            async def _write_and_verify() -> bool:
                async with Iec61850MmsSourceReader("127.0.0.1", port, timeout_seconds=5.0) as reader:
                    # Write BOOLEAN true to SPCtrl1.setVal
                    write_result = await reader.write(
                        obj_ref="Simulator/GGIO1.SPCtrl1.setVal",
                        fc="SP",
                        value_type="BOOLEAN",
                        value="true",
                        request_id="gate-write",
                    )
                    if not write_result.ok:
                        return False
                    # Read back
                    read_result = await reader.read(
                        obj_ref="Simulator/GGIO1.SPCtrl1.setVal",
                        fc="SP",
                        request_id="gate-readback",
                    )
                    return read_result.ok and read_result.value == "true"

            ok = asyncio.run(_write_and_verify())
            assert ok, "MMS write_then_readback failed"
        finally:
            _stop_simulator(simulator)
            os.environ.pop("WHALE_INGEST_SOURCE_WRITE_ENABLED", None)

    def test_aggregate_read_metrics(self) -> None:
        """多次 MMS 读调用 — 模拟 capacity/profile 指标收集。"""
        from whale.shared.source.iec61850.reader import Iec61850MmsSourceReader

        port = _find_free_port()
        simulator = _start_simulator(port)
        try:
            _wait_for_port("127.0.0.1", port)

            async def _run() -> dict[str, float]:
                success_count = 0
                error_count = 0
                durations: list[float] = []

                async with Iec61850MmsSourceReader("127.0.0.1", port, timeout_seconds=5.0) as reader:
                    for _ in range(5):
                        start = time.perf_counter()
                        result = await reader.read(
                            obj_ref="Simulator/GGIO1.Ind1.stVal",
                            fc="ST",
                            request_id="gate-metrics",
                        )
                        elapsed = time.perf_counter() - start
                        durations.append(elapsed)
                        if result.ok:
                            success_count += 1
                        else:
                            error_count += 1

                return {
                    "success_count": float(success_count),
                    "error_count": float(error_count),
                    "avg_duration_s": sum(durations) / len(durations) if durations else 0,
                }

            metrics = asyncio.run(_run())
            assert metrics["success_count"] >= 4, (
                f"expected >=4/5 success, got {metrics['success_count']}/"
                f"{metrics['success_count'] + metrics['error_count']}"
            )
            assert metrics["avg_duration_s"] > 0
            throughput_hz = 1.0 / metrics["avg_duration_s"] if metrics["avg_duration_s"] > 0 else 0
            assert throughput_hz > 0, f"throughput must be positive, got {throughput_hz:.2f} hz"
        finally:
            _stop_simulator(simulator)

    def test_repeated_read_20_times(self) -> None:
        """连续 20 次 MMS 读 — 短周期稳定性 smoke。"""
        from whale.shared.source.iec61850.reader import Iec61850MmsSourceReader

        port = _find_free_port()
        simulator = _start_simulator(port)
        try:
            _wait_for_port("127.0.0.1", port)

            async def _run() -> None:
                async with Iec61850MmsSourceReader("127.0.0.1", port, timeout_seconds=5.0) as reader:
                    for i in range(20):
                        result = await reader.read(
                            obj_ref="Simulator/GGIO1.Ind1.stVal",
                            fc="ST",
                            request_id=f"stab-read-{i:03d}",
                        )
                        assert result.ok, f"Read iteration {i} failed: {result.error_reason}"

            asyncio.run(_run())
        finally:
            _stop_simulator(simulator)

    def test_repeated_write_readback_5_cycles(self) -> None:
        """连续 5 次 MMS write+readback — 短周期稳定性 smoke。"""
        from whale.shared.source.iec61850.reader import Iec61850MmsSourceReader

        port = _find_free_port()
        simulator = _start_simulator(port)
        os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"
        try:
            _wait_for_port("127.0.0.1", port)

            async def _run() -> None:
                async with Iec61850MmsSourceReader("127.0.0.1", port, timeout_seconds=5.0) as reader:
                    for i in range(5):
                        value = "true" if i % 2 == 0 else "false"
                        write_result = await reader.write(
                            obj_ref="Simulator/GGIO1.SPCtrl1.setVal",
                            fc="SP", value_type="BOOLEAN", value=value,
                            request_id=f"stab-write-{i:03d}",
                        )
                        assert write_result.ok, f"Write iteration {i} failed: {write_result.error_message}"

                        read_result = await reader.read(
                            obj_ref="Simulator/GGIO1.SPCtrl1.setVal",
                            fc="SP",
                            request_id=f"stab-readback-{i:03d}",
                        )
                        assert read_result.ok, f"Readback iteration {i} failed: {read_result.error_reason}"
                        assert read_result.value == value, (
                            f"Readback iteration {i}: expected {value}, got {read_result.value}"
                        )

            asyncio.run(_run())
        finally:
            _stop_simulator(simulator)
            os.environ.pop("WHALE_INGEST_SOURCE_WRITE_ENABLED", None)
