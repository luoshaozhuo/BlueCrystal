"""Native runner class registry — maps protocol names to native CapacityRunner classes.

Each entry wraps a native C executable via ``NativeCmdCapacityRunner``.
If the executable is not compiled/detected, the class raises ``RuntimeError``
at construction time, and ``registry.build_capacity_runner`` falls through to the
Python lightweight runner.

Usage::

    from tools.source_lab.access.runners.native_runner_map import NATIVE_CAPACITY_RUNNERS
    RunnerClass = NATIVE_CAPACITY_RUNNERS.get("modbus_tcp")
    if RunnerClass is not None:
        try:
            runner = RunnerClass()
        except RuntimeError:
            ...  # native not available
"""

from __future__ import annotations

from tools.source_lab.access.runners.native_cmd import NativeCmdCapacityRunner


class _ModbusTcpNativeRunner(NativeCmdCapacityRunner):
    name = "modbus_tcp_native_runner"
    executable_name = "modbus_tcp_polling_runner"

    def build_command(self, worker_index, specs, target_hz, config):
        spec = specs[0]
        ep = spec.source.endpoint
        interval_ms = int(1000.0 / target_hz) if target_hz > 0 else 100
        count = int(config.duration_s * target_hz) if target_hz > 0 else 10
        return [
            self._resolve_exe(),
            ep.host, str(ep.port),
            str(ep.params.get("modbus_unit_id", 1)),
            str(ep.params.get("modbus_start_address", 0)),
            str(max(1, len(spec.source.points))),
            str(interval_ms), str(count),
        ]


class _ModbusRtuNativeRunner(NativeCmdCapacityRunner):
    name = "modbus_rtu_native_runner"
    executable_name = "modbus_rtu_polling_runner"

    def build_command(self, worker_index, specs, target_hz, config):
        spec = specs[0]
        ep = spec.source.endpoint
        interval_ms = int(1000.0 / target_hz) if target_hz > 0 else 100
        count = int(config.duration_s * target_hz) if target_hz > 0 else 10
        return [
            self._resolve_exe(),
            ep.params.get("serial_port", "/dev/ttyUSB0"),
            str(ep.params.get("baudrate", 19200)),
            str(ep.params.get("parity", "N")),
            str(ep.params.get("data_bits", 8)),
            str(ep.params.get("stop_bits", 1)),
            str(ep.params.get("modbus_unit_id", 1)),
            str(ep.params.get("modbus_start_address", 0)),
            str(max(1, len(spec.source.points))),
            str(interval_ms), str(count),
        ]


class _Iec104NativeRunner(NativeCmdCapacityRunner):
    name = "iec104_native_runner"
    executable_name = "iec104_client_runner"

    def build_command(self, worker_index, specs, target_hz, config):
        spec = specs[0]
        ep = spec.source.endpoint
        interval_ms = int(1000.0 / target_hz) if target_hz > 0 else 100
        count = int(config.duration_s * target_hz) if target_hz > 0 else 10
        return [
            self._resolve_exe(),
            ep.host, str(ep.port),
            str(ep.params.get("common_address", 1)),
            str(interval_ms), str(count),
        ]


class _Iec101NativeRunner(NativeCmdCapacityRunner):
    name = "iec101_native_runner"
    executable_name = "iec101_client_runner"

    def build_command(self, worker_index, specs, target_hz, config):
        spec = specs[0]
        ep = spec.source.endpoint
        interval_ms = int(1000.0 / target_hz) if target_hz > 0 else 100
        count = int(config.duration_s * target_hz) if target_hz > 0 else 10
        return [
            self._resolve_exe(),
            ep.params.get("serial_port", "/dev/ttyUSB0"),
            str(ep.params.get("baudrate", 9600)),
            str(ep.params.get("parity", "E")),
            str(ep.params.get("data_bits", 8)),
            str(ep.params.get("stop_bits", 1)),
            str(ep.params.get("link_address", 1)),
            str(ep.params.get("common_address", 1)),
            str(interval_ms), str(count),
        ]


class _Iec61850MmsNativeRunner(NativeCmdCapacityRunner):
    name = "iec61850_mms_native_runner"
    executable_name = "iec61850_mms_client_runner"

    def build_command(self, worker_index, specs, target_hz, config):
        spec = specs[0]
        ep = spec.source.endpoint
        interval_ms = int(1000.0 / target_hz) if target_hz > 0 else 100
        count = int(config.duration_s * target_hz) if target_hz > 0 else 10
        return [
            self._resolve_exe(),
            ep.host, str(ep.port),
            ep.params.get("ied_name", "IED1"),
            ep.params.get("ld_name", "LD1"),
            ep.params.get("ln_class", "MMXU"),
            ep.params.get("do_name", "TotW"),
            ep.params.get("da_name", "mag.f"),
            str(interval_ms), str(count),
        ]


# ── Registry ──────────────────────────────────────────────────────────

NATIVE_CAPACITY_RUNNERS: dict[str, type[NativeCmdCapacityRunner]] = {
    "modbus_tcp": _ModbusTcpNativeRunner,
    "modbus_rtu": _ModbusRtuNativeRunner,
    "iec104": _Iec104NativeRunner,
    "iec101": _Iec101NativeRunner,
    "iec61850_mms": _Iec61850MmsNativeRunner,
}

NATIVE_SUBSCRIPTION_RUNNERS: dict[str, type[NativeCmdCapacityRunner]] = {}
