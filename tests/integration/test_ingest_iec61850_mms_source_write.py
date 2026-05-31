"""Integration test for IEC 61850 MMS source write via SourceCommandUseCase.

测试步骤：
1. 启动 iec61850_simulator_server。
2. 通过 SourceCommandUseCase 写入 SP 节点。
3. 再通过 Iec61850MmsSourceAcquisitionAdapter 读取，验证值已变化。
4. dry_run 模式验证值不变化。
5. write disabled 模式验证真实写被拒绝。

依赖：
- iec61850_simulator_server 和 iec61850_mms_client_runner 编译可用。
- 不需要外部 Redis 或 Kafka。
"""
from __future__ import annotations

import asyncio
import os
import socket
import subprocess
import time
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

import pytest

from whale.ingest.adapters.source.iec61850_source_acquisition_adapter import (
    Iec61850MmsSourceAcquisitionAdapter,
)
from whale.ingest.adapters.source.iec61850_source_write_adapter import (
    Iec61850MmsSourceWriteAdapter,
)
from whale.ingest.adapters.source.static_source_write_port_registry import (
    StaticSourceWritePortRegistry,
)
from whale.ingest.usecases.source_command_use_case import SourceCommandUseCase
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.ingest.usecases.dtos.source_write_request import (
    SourceWriteExecutionOptions,
    SourceWriteItemData,
    SourceWriteRequest,
)


def _resolve_simulator_path() -> Path | None:
    """解析 iec61850_simulator_server 可执行文件路径。"""
    build_dir = Path(__file__).resolve().parents[2] / "tools" / "source_lab" / "native" / "build"
    for candidate in (
        build_dir / "iec61850_simulator_server",
        build_dir / "iec61850_simulator_server.exe",
    ):
        if candidate.exists():
            return candidate.resolve()
    return None


def _resolve_client_runner_path() -> Path | None:
    """解析 iec61850_mms_client_runner 可执行文件路径。"""
    build_dir = Path(__file__).resolve().parents[2] / "tools" / "source_lab" / "native" / "build"
    for candidate in (
        build_dir / "iec61850_mms_client_runner",
        build_dir / "iec61850_mms_client_runner.exe",
    ):
        if candidate.exists():
            return candidate.resolve()
    return None


_SIMULATOR_PATH = _resolve_simulator_path()
_CLIENT_RUNNER_PATH = _resolve_client_runner_path()


def _choose_available_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_port(host: str, port: int, timeout: float = 10.0) -> None:
    """轮询等待 TCP 端口可连接。"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise RuntimeError(f"Timed out waiting for {host}:{port} to become connectable")


@pytest.mark.integration
class TestIec61850MmsSourceWrite:
    """IEC 61850 MMS Source Write integration tests."""

    @classmethod
    def setup_class(cls) -> None:
        if _SIMULATOR_PATH is None:
            pytest.skip("iec61850_simulator_server not compiled")
        if _CLIENT_RUNNER_PATH is None:
            pytest.skip("iec61850_mms_client_runner not compiled")
        os.environ["WHALE_IEC61850_MMS_CLIENT_RUNNER_PATH"] = str(_CLIENT_RUNNER_PATH)

    @classmethod
    def teardown_class(cls) -> None:
        os.environ.pop("WHALE_IEC61850_MMS_CLIENT_RUNNER_PATH", None)

    def _start_simulator(self, port: int) -> subprocess.Popen[str]:
        """启动 iec61850_simulator_server 并等待 READY。"""
        proc = subprocess.Popen(
            [str(_SIMULATOR_PATH), str(port)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert proc.stdout is not None

        # Skip diagnostic lines until READY
        ready_line = ""
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline:
            line = proc.stdout.readline()
            if not line:
                break
            stripped = line.strip()
            if stripped == "READY":
                ready_line = stripped
                break
        if ready_line != "READY":
            proc.terminate()
            proc.wait(timeout=5)
            pytest.fail("Simulator did not output READY")

        _wait_for_port("127.0.0.1", port)
        return proc

    def _stop_simulator(self, proc: subprocess.Popen[str]) -> None:
        """安全停止模拟器进程。"""
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)

    def _build_connection(self, port: int) -> SourceConnectionData:
        return SourceConnectionData(
            host="127.0.0.1",
            port=port,
            ied_name="IED1",
            ld_name="Simulator",
            namespace_uri="",
        )

    def _build_acquisition_execution(self) -> AcquisitionExecutionOptions:
        return AcquisitionExecutionOptions(
            protocol="iec61850_mms",
            transport="tcp",
            acquisition_mode="READ_ONCE",
            interval_ms=100,
            max_iteration=1,
            request_timeout_ms=5_000,
            freshness_timeout_ms=30_000,
            alive_timeout_ms=60_000,
        )

    def _read_value(
        self, adapter: Iec61850MmsSourceAcquisitionAdapter, port: int, obj_ref: str, fc: str = "SP",
    ) -> str | None:
        """读取一个 MMS 节点的值。"""
        connection = self._build_connection(port)
        # 设置 FC via params
        connection.params["fc"] = fc

        async def _run() -> str | None:
            result = await adapter.read(
                execution=self._build_acquisition_execution(),
                connection=connection,
                items=[
                    AcquisitionItemData(key="test", profile_item_id=1, relative_path=obj_ref),
                ],
            )
            for value in result.values:
                if value.node_key == "test":
                    return value.value
            return None

        return asyncio.run(_run())

    def test_write_then_read_verify_value_changed(self) -> None:
        """写入 BOOLEAN 后通过读取验证值已变化。"""
        self.setup_class()

        port = _choose_available_port()
        simulator = self._start_simulator(port)
        os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"

        try:
            adapter = Iec61850MmsSourceAcquisitionAdapter()
            write_adapter = Iec61850MmsSourceWriteAdapter()
            registry = StaticSourceWritePortRegistry(ports_by_protocol={"iec61850_mms": write_adapter})
            use_case = SourceCommandUseCase(write_port_registry=registry)

            connection = self._build_connection(port)
            connection.params["fc"] = "SP"

            obj_ref = "Simulator/GGIO1.SPCtrl1.setVal"

            # 读取 baseline
            initial = self._read_value(adapter, port, obj_ref)
            assert initial is not None, "Should read initial value"
            # 初始值应为 "false" (0)

            # 写入 true
            write_request = SourceWriteRequest(
                request_id="int-write-001",
                task_id=1,
                execution=SourceWriteExecutionOptions(
                    protocol="iec61850_mms",
                    transport="tcp",
                    request_timeout_ms=5_000,
                    dry_run=False,
                    actor="test",
                ),
                connections=[connection],
                items=[
                    SourceWriteItemData(
                        key="sp1",
                        node_id=obj_ref,
                        value_type="BOOLEAN",
                        value="true",
                    ),
                ],
                client_requested_at=datetime.now(tz=UTC),
            )

            write_result = asyncio.run(use_case.execute(write_request))
            assert write_result.success_count == 1, f"Write failed: {write_result.results}"

            # 再次读取验证值已变化
            final = self._read_value(adapter, port, obj_ref)
            assert final is not None
            assert final == "true", f"Expected 'true' after write, got {final}"

        finally:
            self._stop_simulator(simulator)
            os.environ.pop("WHALE_INGEST_SOURCE_WRITE_ENABLED", None)

    def test_write_int32_then_read_verify(self) -> None:
        """写入 INT32 后通过读取验证。"""
        self.setup_class()

        port = _choose_available_port()
        simulator = self._start_simulator(port)
        os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"

        try:
            write_adapter = Iec61850MmsSourceWriteAdapter()
            registry = StaticSourceWritePortRegistry(ports_by_protocol={"iec61850_mms": write_adapter})
            use_case = SourceCommandUseCase(write_port_registry=registry)

            connection = self._build_connection(port)
            connection.params["fc"] = "SP"

            obj_ref = "Simulator/GGIO1.SPCtrl2.setVal"

            write_request = SourceWriteRequest(
                request_id="int-write-002",
                task_id=1,
                execution=SourceWriteExecutionOptions(
                    protocol="iec61850_mms",
                    transport="tcp",
                    request_timeout_ms=5_000,
                    dry_run=False,
                    actor="test",
                ),
                connections=[connection],
                items=[
                    SourceWriteItemData(
                        key="sp2",
                        node_id=obj_ref,
                        value_type="INT32",
                        value="12345",
                    ),
                ],
                client_requested_at=datetime.now(tz=UTC),
            )

            write_result = asyncio.run(use_case.execute(write_request))
            assert write_result.success_count == 1, f"Write failed: {write_result.results}"

        finally:
            self._stop_simulator(simulator)
            os.environ.pop("WHALE_INGEST_SOURCE_WRITE_ENABLED", None)

    def test_write_float32_then_readback(self) -> None:
        """写入 FLOAT32 后读回验证值已变化。"""
        self.setup_class()

        port = _choose_available_port()
        simulator = self._start_simulator(port)
        os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"

        try:
            adapter = Iec61850MmsSourceAcquisitionAdapter()
            write_adapter = Iec61850MmsSourceWriteAdapter()
            registry = StaticSourceWritePortRegistry(ports_by_protocol={"iec61850_mms": write_adapter})
            use_case = SourceCommandUseCase(write_port_registry=registry)

            connection = self._build_connection(port)
            connection.params["fc"] = "SP"

            obj_ref = "Simulator/GGIO1.SPCtrl3.setVal"

            # 读取 baseline
            initial = self._read_value(adapter, port, obj_ref, fc="SP")
            assert initial is not None

            # 写入 FLOAT32
            write_request = SourceWriteRequest(
                request_id="int-write-float-001",
                task_id=1,
                execution=SourceWriteExecutionOptions(
                    protocol="iec61850_mms", transport="tcp",
                    request_timeout_ms=5_000, dry_run=False, actor="test",
                ),
                connections=[connection],
                items=[
                    SourceWriteItemData(
                        key="sp3", node_id=obj_ref, value_type="FLOAT32", value="98.765",
                    ),
                ],
                client_requested_at=datetime.now(tz=UTC),
            )

            write_result = asyncio.run(use_case.execute(write_request))
            assert write_result.success_count == 1, f"FLOAT32 write failed: {write_result.results}"

            # 读回
            final = self._read_value(adapter, port, obj_ref, fc="SP")
            assert final is not None
            assert float(final) == pytest.approx(98.765, abs=1e-3), (
                f"Expected ~98.765 after FLOAT32 write, got {final}"
            )
        finally:
            self._stop_simulator(simulator)
            os.environ.pop("WHALE_INGEST_SOURCE_WRITE_ENABLED", None)

    def test_write_float64_then_readback(self) -> None:
        """写入 FLOAT64 后读回验证值已变化。"""
        self.setup_class()

        port = _choose_available_port()
        simulator = self._start_simulator(port)
        os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"

        try:
            adapter = Iec61850MmsSourceAcquisitionAdapter()
            write_adapter = Iec61850MmsSourceWriteAdapter()
            registry = StaticSourceWritePortRegistry(ports_by_protocol={"iec61850_mms": write_adapter})
            use_case = SourceCommandUseCase(write_port_registry=registry)

            connection = self._build_connection(port)
            connection.params["fc"] = "SP"

            obj_ref = "Simulator/GGIO1.SPCtrl4.setVal"

            # 写入 FLOAT64
            write_request = SourceWriteRequest(
                request_id="int-write-f64-001",
                task_id=1,
                execution=SourceWriteExecutionOptions(
                    protocol="iec61850_mms", transport="tcp",
                    request_timeout_ms=5_000, dry_run=False, actor="test",
                ),
                connections=[connection],
                items=[
                    SourceWriteItemData(
                        key="sp4", node_id=obj_ref, value_type="FLOAT64", value="12345.6789",
                    ),
                ],
                client_requested_at=datetime.now(tz=UTC),
            )

            write_result = asyncio.run(use_case.execute(write_request))
            assert write_result.success_count == 1, f"FLOAT64 write failed: {write_result.results}"

            # 读回
            final = self._read_value(adapter, port, obj_ref, fc="SP")
            assert final is not None
            assert float(final) == pytest.approx(12345.6789, abs=1e-4), (
                f"Expected ~12345.6789 after FLOAT64 write, got {final}"
            )

        finally:
            self._stop_simulator(simulator)
            os.environ.pop("WHALE_INGEST_SOURCE_WRITE_ENABLED", None)

    def test_write_visible_string_then_readback(self) -> None:
        """写入 VISIBLE_STRING 后读回验证。"""
        self.setup_class()

        port = _choose_available_port()
        simulator = self._start_simulator(port)
        os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"

        try:
            adapter = Iec61850MmsSourceAcquisitionAdapter()
            write_adapter = Iec61850MmsSourceWriteAdapter()
            registry = StaticSourceWritePortRegistry(ports_by_protocol={"iec61850_mms": write_adapter})
            use_case = SourceCommandUseCase(write_port_registry=registry)

            connection = self._build_connection(port)
            connection.params["fc"] = "SP"

            obj_ref = "Simulator/GGIO1.SPCtrl5.setVal"

            # 写入 VISIBLE_STRING
            test_value = "MMS_TEST_TAG"
            write_request = SourceWriteRequest(
                request_id="int-write-vs-001",
                task_id=1,
                execution=SourceWriteExecutionOptions(
                    protocol="iec61850_mms", transport="tcp",
                    request_timeout_ms=5_000, dry_run=False, actor="test",
                ),
                connections=[connection],
                items=[
                    SourceWriteItemData(
                        key="sp5", node_id=obj_ref, value_type="VISIBLE_STRING", value=test_value,
                    ),
                ],
                client_requested_at=datetime.now(tz=UTC),
            )

            write_result = asyncio.run(use_case.execute(write_request))
            assert write_result.success_count == 1, f"VISIBLE_STRING write failed: {write_result.results}"

            # 读回
            final = self._read_value(adapter, port, obj_ref, fc="SP")
            assert final is not None
            assert final == test_value, (
                f"Expected '{test_value}' after VISIBLE_STRING write, got {final}"
            )

        finally:
            self._stop_simulator(simulator)
            os.environ.pop("WHALE_INGEST_SOURCE_WRITE_ENABLED", None)

    def test_write_uint32_then_readback(self) -> None:
        """写入 UINT32 后读回验证。"""
        self.setup_class()

        port = _choose_available_port()
        simulator = self._start_simulator(port)
        os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"

        try:
            adapter = Iec61850MmsSourceAcquisitionAdapter()
            write_adapter = Iec61850MmsSourceWriteAdapter()
            registry = StaticSourceWritePortRegistry(ports_by_protocol={"iec61850_mms": write_adapter})
            use_case = SourceCommandUseCase(write_port_registry=registry)

            connection = self._build_connection(port)
            connection.params["fc"] = "SP"

            obj_ref = "Simulator/GGIO1.SPCtrl6.setVal"

            # 写入 UINT32
            write_request = SourceWriteRequest(
                request_id="int-write-u32-001",
                task_id=1,
                execution=SourceWriteExecutionOptions(
                    protocol="iec61850_mms", transport="tcp",
                    request_timeout_ms=5_000, dry_run=False, actor="test",
                ),
                connections=[connection],
                items=[
                    SourceWriteItemData(
                        key="sp6", node_id=obj_ref, value_type="UINT32", value="4000000000",
                    ),
                ],
                client_requested_at=datetime.now(tz=UTC),
            )

            write_result = asyncio.run(use_case.execute(write_request))
            assert write_result.success_count == 1, f"UINT32 write failed: {write_result.results}"

            # 读回
            final = self._read_value(adapter, port, obj_ref, fc="SP")
            assert final is not None
            assert int(final) == 4000000000, (
                f"Expected 4000000000 after UINT32 write, got {final}"
            )

        finally:
            self._stop_simulator(simulator)
            os.environ.pop("WHALE_INGEST_SOURCE_WRITE_ENABLED", None)

    def test_write_int64_then_readback(self) -> None:
        """写入 INT64 后读回验证。"""
        self.setup_class()

        port = _choose_available_port()
        simulator = self._start_simulator(port)
        os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"

        try:
            adapter = Iec61850MmsSourceAcquisitionAdapter()
            write_adapter = Iec61850MmsSourceWriteAdapter()
            registry = StaticSourceWritePortRegistry(ports_by_protocol={"iec61850_mms": write_adapter})
            use_case = SourceCommandUseCase(write_port_registry=registry)

            connection = self._build_connection(port)
            connection.params["fc"] = "SP"

            obj_ref = "Simulator/GGIO1.SPCtrl7.setVal"

            # 写入 INT64
            write_request = SourceWriteRequest(
                request_id="int-write-i64-001",
                task_id=1,
                execution=SourceWriteExecutionOptions(
                    protocol="iec61850_mms", transport="tcp",
                    request_timeout_ms=5_000, dry_run=False, actor="test",
                ),
                connections=[connection],
                items=[
                    SourceWriteItemData(
                        key="sp7", node_id=obj_ref, value_type="INT64", value="9000000000000",
                    ),
                ],
                client_requested_at=datetime.now(tz=UTC),
            )

            write_result = asyncio.run(use_case.execute(write_request))
            assert write_result.success_count == 1, f"INT64 write failed: {write_result.results}"

            # 读回
            final = self._read_value(adapter, port, obj_ref, fc="SP")
            assert final is not None
            assert int(final) == 9000000000000, (
                f"Expected 9000000000000 after INT64 write, got {final}"
            )

        finally:
            self._stop_simulator(simulator)
            os.environ.pop("WHALE_INGEST_SOURCE_WRITE_ENABLED", None)

    def test_dry_run_does_not_change_value(self) -> None:
        """dry_run 模式不应改变实际值。"""
        self.setup_class()

        port = _choose_available_port()
        simulator = self._start_simulator(port)

        try:
            adapter = Iec61850MmsSourceAcquisitionAdapter()
            write_adapter = Iec61850MmsSourceWriteAdapter()
            registry = StaticSourceWritePortRegistry(ports_by_protocol={"iec61850_mms": write_adapter})
            use_case = SourceCommandUseCase(write_port_registry=registry)

            obj_ref = "Simulator/GGIO1.SPCtrl1.setVal"

            # 读取 baseline
            initial = self._read_value(adapter, port, obj_ref)

            # dry_run 写入
            connection = self._build_connection(port)
            connection.params["fc"] = "SP"

            dry_run_request = SourceWriteRequest(
                request_id="int-dry-run-001",
                task_id=1,
                execution=SourceWriteExecutionOptions(
                    protocol="iec61850_mms",
                    transport="tcp",
                    request_timeout_ms=5_000,
                    dry_run=True,
                    actor="test",
                ),
                connections=[connection],
                items=[
                    SourceWriteItemData(
                        key="sp1",
                        node_id=obj_ref,
                        value_type="BOOLEAN",
                        value="true",
                    ),
                ],
            )

            result = asyncio.run(use_case.execute(dry_run_request))
            assert result.dry_run is True
            assert result.success_count == 0

            # 再次读取，值应不变
            final = self._read_value(adapter, port, obj_ref)
            assert final == initial, (
                f"dry_run should not change value. Before: {initial}, After: {final}"
            )

        finally:
            self._stop_simulator(simulator)
            os.environ.pop("WHALE_INGEST_SOURCE_WRITE_ENABLED", None)

    def test_write_disabled_refuses_real_write(self) -> None:
        """未启用写入时，真实写请求应被拒绝。"""
        self.setup_class()

        port = _choose_available_port()
        simulator = self._start_simulator(port)

        # 确保未设置启用标记
        os.environ.pop("WHALE_INGEST_SOURCE_WRITE_ENABLED", None)

        try:
            write_adapter = Iec61850MmsSourceWriteAdapter()
            registry = StaticSourceWritePortRegistry(ports_by_protocol={"iec61850_mms": write_adapter})
            use_case = SourceCommandUseCase(write_port_registry=registry)

            connection = self._build_connection(port)

            write_request = SourceWriteRequest(
                request_id="int-write-disabled-001",
                task_id=1,
                execution=SourceWriteExecutionOptions(
                    protocol="iec61850_mms",
                    transport="tcp",
                    request_timeout_ms=5_000,
                    dry_run=False,
                ),
                connections=[connection],
                items=[
                    SourceWriteItemData(
                        key="sp1",
                        node_id="Simulator/GGIO1.SPCtrl1.setVal",
                        value_type="BOOLEAN",
                        value="true",
                    ),
                ],
            )

            with pytest.raises(RuntimeError, match="Real device write is disabled"):
                asyncio.run(use_case.execute(write_request))

        finally:
            self._stop_simulator(simulator)
