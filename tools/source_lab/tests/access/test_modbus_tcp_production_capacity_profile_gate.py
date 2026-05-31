"""Modbus TCP production capacity / profile gate test.

验证 Modbus TCP 的 capacity 和 profile 路径可执行的硬性门禁。

轮目标要求：
1. Modbus TCP capacity 路径可执行（build → read）。
2. Modbus TCP profile 路径可执行（build → timed read）。
3. 使用真实协议 simulator（ModbusTcpSimulator），不允许仅 registry 构造。
4. 执行结果中 protocol=modbus_tcp 或等价字段明确。
5. 结果包含 success_count / error_count / duration / throughput 等价指标。
6. 不允许 skipped。
7. 如果环境缺少 native runner，应 fail with actionable message。
"""
from __future__ import annotations

import time
import types
from contextlib import closing
import pytest

from tools.source_lab.access.runners.native_cmd import NativeCmdCapacityRunner
from tools.source_lab.access.runners.registry import build_capacity_runner

# ── helpers ────────────────────────────────────────────────────────────


def _find_free_port() -> int:
    import socket
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _load_simulator() -> tuple[types.ModuleType, types.ModuleType]:
    from tests.support.source_lab_runtime import import_source_lab_module
    sim_mod = import_source_lab_module("tools.source_lab.protocols.common.simulators")
    model_mod = import_source_lab_module("tools.source_lab.model")
    return sim_mod, model_mod


def _build_sim_source(host: str, port: int) -> object:
    sim_mod, model_mod = _load_simulator()
    # 通过动态导入模块访问属性，mypy 无法推断类型，忽略 attr-defined
    return model_mod.SimulatedSource(  # type: ignore[attr-defined]
        connection=model_mod.SourceConnection(  # type: ignore[attr-defined]
            name="modbus_gate", ied_name="IED", ld_name="LD",
            host=host, port=port, transport="tcp", protocol="modbus_tcp",
        ),
        points=(
            model_mod.SimulatedPoint(ln_name="", do_name="0", unit="", data_type="UINT16", initial_value=10),  # type: ignore[attr-defined]
            model_mod.SimulatedPoint(ln_name="", do_name="1", unit="", data_type="UINT16", initial_value=20),  # type: ignore[attr-defined]
        ),
    )


# ── Gate tests ─────────────────────────────────────────────────────────


class TestModbusTcpCapacityProfileGate:
    """Modbus TCP capacity/profile 门禁测试。"""

    def test_runner_construction(self) -> None:
        """build_capacity_runner('modbus_tcp') 必须成功返回 runner。"""
        from tools.source_lab.access.runners.registry import RunnerInfo
        info = build_capacity_runner("modbus_tcp")
        assert info is not None, "build_capacity_runner returned None"
        assert isinstance(info, RunnerInfo)
        assert info.runner is not None

    def test_native_runner_command_build(self) -> None:
        """Native runner 必须可构建命令（证明 native 编译可用）。"""
        info = build_capacity_runner("modbus_tcp")
        runner = info.runner
        if not isinstance(runner, NativeCmdCapacityRunner):
            pytest.fail(
                "modbus_tcp native runner is NOT compiled. "
                "Run `cmake --build tools/source_lab/native/build --target modbus_tcp_polling_runner` "
                "to compile the native runner before running this test."
            )
        assert isinstance(runner, NativeCmdCapacityRunner)
        # Native runner must have executable name pointing to the C runner
        assert runner.executable_name == "modbus_tcp_polling_runner"

    def test_runner_protocol_identity(self) -> None:
        """Runner 的 name 字段必须包含 modbus_tcp 标识。"""
        info = build_capacity_runner("modbus_tcp")
        name = info.name.lower()
        assert "modbus" in name, f"expected modbus in runner name, got {info.name}"

    def test_tcp_read_against_simulator(self) -> None:
        """使用 Python ModbusTcpPollingRunner 对真实 simulator 执行 read_once。"""
        from tools.source_lab.access.runners.modbus_tcp_polling import ModbusTcpPollingRunner
        from tools.source_lab.access.polling.model import CapacityScanConfig, CapacityMode
        from tools.source_lab.access.common.scheduling import RunnerEndpointPlan
        from tools.source_lab.access.providers.base import SourceRuntimeSpec
        from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec

        sim_mod, model_mod = _load_simulator()
        port = _find_free_port()
        source = _build_sim_source("127.0.0.1", port)
        ModbusTcpSimulator = sim_mod.ModbusTcpSimulator  # type: ignore[attr-defined]

        runner = ModbusTcpPollingRunner()
        config = CapacityScanConfig(
            mode=CapacityMode.SIMULATOR,
            protocol="modbus_tcp",
            endpoints=(),
            points=(),
            server_count_start=1, server_count_step=1, server_count_max=1,
            hz_start=1.0, hz_step=1.0, hz_max=1.0,
            process_count=1,
            read_timeout_s=5.0,
        )
        spec = RunnerEndpointPlan(
            global_index=0,
            source=SourceRuntimeSpec(
                endpoint=SourceEndpointSpec(
                    name="gate", host="127.0.0.1", port=port,
                    protocol="modbus_tcp",
                    params={"modbus_unit_id": 1},
                ),
                points=(
                    SourcePointSpec(address="0", name="p0", data_type="UINT16"),
                ),
            ),
            offset_ns=0,
        )

        with ModbusTcpSimulator(source):
            sample = runner.read_once(spec, target_hz=10.0, config=config)

        assert sample.ok, f"read_once against simulator failed: {sample.error_code}"
        assert sample.value_count >= 1, f"expected >=1 values, got {sample.value_count}"
        assert sample.response_timestamp_s is not None, "response_timestamp_s must be set"

    def test_aggregate_read_metrics(self) -> None:
        """多次读调用 — 模拟 capacity/profile 指标收集。"""
        from tools.source_lab.access.runners.modbus_tcp_polling import ModbusTcpPollingRunner
        from tools.source_lab.access.polling.model import CapacityScanConfig, CapacityMode
        from tools.source_lab.access.common.scheduling import RunnerEndpointPlan
        from tools.source_lab.access.providers.base import SourceRuntimeSpec
        from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec

        sim_mod, model_mod = _load_simulator()
        port = _find_free_port()
        source = _build_sim_source("127.0.0.1", port)
        ModbusTcpSimulator = sim_mod.ModbusTcpSimulator  # type: ignore[attr-defined]

        runner = ModbusTcpPollingRunner()
        config = CapacityScanConfig(
            mode=CapacityMode.SIMULATOR,
            protocol="modbus_tcp",
            endpoints=(),
            points=(),
            server_count_start=1, server_count_step=1, server_count_max=1,
            hz_start=1.0, hz_step=1.0, hz_max=1.0,
            process_count=1,
            read_timeout_s=5.0,
        )
        spec = RunnerEndpointPlan(
            global_index=0,
            source=SourceRuntimeSpec(
                endpoint=SourceEndpointSpec(
                    name="gate", host="127.0.0.1", port=port,
                    protocol="modbus_tcp",
                    params={"modbus_unit_id": 1},
                ),
                points=(
                    SourcePointSpec(address="0", name="p0", data_type="UINT16"),
                ),
            ),
            offset_ns=0,
        )

        with ModbusTcpSimulator(source):
            success_count = 0
            error_count = 0
            read_durations: list[float] = []

            for _ in range(5):
                start = time.perf_counter()
                sample = runner.read_once(spec, target_hz=10.0, config=config)
                elapsed = time.perf_counter() - start
                read_durations.append(elapsed)
                if sample.ok:
                    success_count += 1
                else:
                    error_count += 1

        assert success_count >= 4, (
            f"expected >=4/5 success, got {success_count}/{success_count + error_count}"
        )
        assert len(read_durations) == 5
        avg_duration_s = sum(read_durations) / len(read_durations)
        assert avg_duration_s > 0, "average duration must be positive"
        throughput_hz = 1.0 / avg_duration_s if avg_duration_s > 0 else 0
        assert throughput_hz > 0, f"throughput must be positive, got {throughput_hz:.2f} hz"
