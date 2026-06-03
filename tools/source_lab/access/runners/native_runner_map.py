"""原生执行器注册表——将协议名映射到原生 CapacityRunner 类。

负责：注册各协议（modbus_tcp/rtu、iec104/101、iec61850_mms）的原生 C runner。
不负责：runner 实例创建后的生命周期管理（由 registry.build_capacity_runner 负责）。
注意：如果原生可执行文件未编译，对应的 runner 类在构造时抛出 RuntimeError。
"""

from __future__ import annotations

import glob

from tools.source_lab.access.runners.native_cmd import (
    NativeCmdCapacityRunner,
    NativeRunnerUnavailableError,
)


def _has_serial_device() -> bool:
    """检查系统是否有可用串口设备（USB/ACM 转换器，排除板载 ttyS*）。"""
    return len(glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")) > 0


class _ModbusTcpNativeRunner(NativeCmdCapacityRunner):
    name = "modbus_tcp_native_runner"
    executable_name = "modbus_tcp_polling_runner"

    def build_command(self, worker_index, specs, target_hz, config):
        spec = specs[0]
        ep = spec.source.endpoint
        interval_ms = int(1000.0 / target_hz) if target_hz > 0 else 100
        count = int(config.level_duration_s * target_hz) if target_hz > 0 else 10
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

    def check_available(self) -> None:
        super().check_available()
        if not _has_serial_device():
            raise NativeRunnerUnavailableError(
                protocol="modbus_rtu",
                runner_name=self.executable_name,
                expected_path="/dev/ttyUSB* or /dev/ttyACM*",
                build_hint="Serial device required. Use Python TCP gateway fallback.",
            )

    def build_command(self, worker_index, specs, target_hz, config):
        spec = specs[0]
        ep = spec.source.endpoint
        interval_ms = int(1000.0 / target_hz) if target_hz > 0 else 100
        count = int(config.level_duration_s * target_hz) if target_hz > 0 else 10
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
        count = int(config.level_duration_s * target_hz) if target_hz > 0 else 10
        return [
            self._resolve_exe(),
            ep.host, str(ep.port),
            str(ep.params.get("common_address", 1)),
            str(interval_ms), str(count),
        ]


class _Iec101NativeRunner(NativeCmdCapacityRunner):
    name = "iec101_native_runner"
    executable_name = "iec101_client_runner"

    def check_available(self) -> None:
        super().check_available()
        if not _has_serial_device():
            raise NativeRunnerUnavailableError(
                protocol="iec101",
                runner_name=self.executable_name,
                expected_path="/dev/ttyUSB* or /dev/ttyACM*",
                build_hint="Serial device required. Use Python TCP gateway fallback.",
            )

    def build_command(self, worker_index, specs, target_hz, config):
        spec = specs[0]
        ep = spec.source.endpoint
        interval_ms = int(1000.0 / target_hz) if target_hz > 0 else 100
        count = int(config.level_duration_s * target_hz) if target_hz > 0 else 10
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
        ep = specs[0].source.endpoint
        points = specs[0].source.points
        interval_ms = int(1000.0 / target_hz) if target_hz > 0 else 100
        count = int(config.level_duration_s * target_hz) if target_hz > 0 else 10

        # Build per-point MMS args: [ln, do, da, fc] for each point
        point_args: list[str] = []
        for pt in points:
            ln = pt.ln_name or ep.params.get("ln_class", "MMXU")
            do_name = pt.do_name
            _da_name_fallback = ""
            # Split do.da if do_name contains "."
            if "." in do_name:
                parts = do_name.split(".", 1)
                do_part = parts[0]
                da_part = parts[1]
            else:
                do_part = do_name
                da_part = ep.params.get("da_name", "")
            point_args.extend([
                ln,
                do_part,
                da_part,
                ep.params.get("fc", "NONE"),
            ])

        return [
            self._resolve_exe(),
            ep.host, str(ep.port),
            ep.params.get("ied_name", "IED1"),
            ep.params.get("ld_name", "LD1"),
            str(interval_ms), str(count),
            str(len(points)),
            *point_args,
        ]


class _BeckhoffAdsNativeRunner(NativeCmdCapacityRunner):
    """AdsLib C++ runner 预留接入点。

    当前仓库未提供 `beckhoff_ads_polling_runner` 二进制；若不存在必须通过
    NativeRunnerUnavailableError 给出明确 build hint，而不是静默成功。

    check_available 会检查：
    1. binary 文件是否存在；
    2. binary 是否可执行；
    3. 若缺失，抛出 NativeRunnerUnavailableError，包含：
       - protocol: "beckhoff_ads"
       - runner: "beckhoff_ads_polling_runner"
       - path: 期望的 binary 路径
       - build_hint: 构建命令提示

    不得让缺失二进制导致假通过。
    """

    name = "beckhoff_ads_native_runner"
    executable_name = "beckhoff_ads_polling_runner"

    def check_available(self) -> None:
        """检查 AdsLib native runner 二进制是否可用。

        覆盖父类方法，以提供更精确的 Beckhoff AdsLib 构建提示。
        若二进制缺失，抛出 NativeRunnerUnavailableError，
        包含 protocol="beckhoff_ads"、runner name、期望路径和 build hint。

        Raises:
            NativeRunnerUnavailableError: 二进制缺失或不可执行。
        """
        from pathlib import Path

        native_build_dir = (
            Path(__file__).resolve().parents[2] / "native" / "build"
        )
        exe_path = native_build_dir / self.executable_name

        # 尝试子目录
        if not exe_path.exists():
            for subdir in ("bin", "Release"):
                candidate = native_build_dir / subdir / self.executable_name
                if candidate.exists():
                    exe_path = candidate
                    break

        if not exe_path.exists():
            raise NativeRunnerUnavailableError(
                protocol="beckhoff_ads",
                runner_name=self.executable_name,
                expected_path=str(exe_path),
                build_hint=(
                    "Beckhoff AdsLib C++ runner is not included in this repository. "
                    "To enable real ADS protocol verification, "
                    "acquire the Beckhoff AdsLib SDK from Beckhoff Automation, "
                    "then compile and place the binary at "
                    f"tools/source_lab/native/build/{self.executable_name}. "
                    "Build instructions: cmake -S tools/source_lab/native -B "
                    "tools/source_lab/native/build && cmake --build "
                    f"tools/source_lab/native/build --target {self.executable_name}"
                ),
            )

        import os
        if not os.access(str(exe_path), os.X_OK):
            raise NativeRunnerUnavailableError(
                protocol="beckhoff_ads",
                runner_name=self.executable_name,
                expected_path=str(exe_path),
                build_hint=(
                    f"Binary exists at {exe_path} but is not executable. "
                    "Run: chmod +x " + str(exe_path)
                ),
            )

    def build_command(self, worker_index, specs, target_hz, config):
        """构造 AdsLib polling runner 命令行。

        当前仅作为 preflight 目标占位；仓库未内置该二进制。

        Args:
            worker_index: worker 索引。
            specs: RunnerEndpointPlan 元组。
            target_hz: 目标轮询频率。
            config: CapacityScanConfig 配置。

        Returns:
            命令行参数列表。
        """
        spec = specs[0]
        ep = spec.source.endpoint
        interval_ms = int(1000.0 / target_hz) if target_hz > 0 else 100
        count = int(config.level_duration_s * target_hz) if target_hz > 0 else 10
        return [
            self._resolve_exe(),
            ep.host,
            str(ep.port),
            str(ep.params.get("ams_net_id", "")),
            str(ep.params.get("ads_server_port", 851)),
            str(max(1, len(spec.source.points))),
            str(interval_ms),
            str(count),
        ]


def beckhoff_ads_native_preflight() -> dict[str, object]:
    """执行 Beckhoff AdsLib native runner 预检，返回结构化诊断。

    若二进制缺失，返回 unavailable，error 包含：
    protocol="beckhoff_ads"、runner="beckhoff_ads_polling_runner"、
    期望路径和 build_hint。

    Returns:
        字典，包含以下键：
        - available (bool): runner 是否可用。
        - protocol (str): "beckhoff_ads"。
        - runner (str): "beckhoff_ads_polling_runner"。
        - path (str): 期望的 binary 路径。
        - build_hint (str | None): 构建提示。
        - error (str | None): 不可用时的错误信息。
    """
    runner = _BeckhoffAdsNativeRunner()
    try:
        runner.check_available()
        return {
            "available": True,
            "protocol": "beckhoff_ads",
            "runner": runner.executable_name,
            "path": str(runner._resolve_exe()),
            "build_hint": None,
            "error": None,
        }
    except NativeRunnerUnavailableError as exc:
        return {
            "available": False,
            "protocol": exc.protocol,
            "runner": exc.runner_name,
            "path": exc.expected_path,
            "build_hint": exc.build_hint,
            "error": str(exc),
        }


# ── Registry ──────────────────────────────────────────────────────────

NATIVE_CAPACITY_RUNNERS: dict[str, type[NativeCmdCapacityRunner]] = {
    "modbus_tcp": _ModbusTcpNativeRunner,
    "modbus_rtu": _ModbusRtuNativeRunner,
    "iec104": _Iec104NativeRunner,
    "iec101": _Iec101NativeRunner,
    "iec61850_mms": _Iec61850MmsNativeRunner,
    "beckhoff_ads": _BeckhoffAdsNativeRunner,
}

NATIVE_SUBSCRIPTION_RUNNERS: dict[str, str] = {
    "iec61850_goose": "iec61850_goose_subscriber_runner",
    "iec61850_sv": "iec61850_sv_subscriber_runner",
}
