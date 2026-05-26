"""IEC61850 ServerSimulatorFacade 实现（MMS / Report / GOOSE / SV）。

MMS 和 Report facade 分别启动对应的 native C runner 子进程，
通过 stdin/stdout TSV 协议实现真实读写与订阅。

MMS 读写使用 iec61850_mms_client_runner（交互模式），
Report 订阅使用 iec61850_report_runner。
"""

from __future__ import annotations

import asyncio
import os
import socket
import subprocess
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from tools.source_lab.model import SimulatedPoint, SimulatedSource
from tools.source_lab.access.runners.protocol import (
    ProtocolDiagnostics,
    start_stderr_drain_thread,
)
from tools.source_lab.protocols.common._base_facade import BaseSimulatorFacade
from tools.source_lab.protocols.common._interactive_runner import (
    NativeInteractiveRunner,
    _resolve_executable,
)
from tools.source_lab.protocols.common.simulator_models import (
    ReadSimulatorResult,
    SimulatorCapabilities,
    SimulatorHealth,
    SimulatorPoint,
    SimulatorResult,
    SimulatorStatus,
)
from tools.source_lab.protocols.common.simulators import (
    Iec61850MmsSimulator,
    Iec61850ReportSimulator,
)


_HOST = "127.0.0.1"


def _infer_fc(point: SimulatedPoint) -> str:
    """Infer MMS FunctionalConstraint from point attributes.

    - SP (setpoint): do_name starts with ``SP`` or ``Ctrl``
    - ST (status): BOOLEAN data type or do_name contains stVal
    - MX (measurand): numeric measurement
    """
    dn = point.do_name or ""
    if dn.startswith("SPCtrl") or dn.startswith("SP") or "setVal" in dn:
        return "SP"
    if point.data_type == "BOOLEAN" or "stVal" in dn:
        return "ST"
    return "MX"


def _point_to_mms_ref(source: SimulatedSource, point: SimulatedPoint) -> tuple[str, str]:
    """Map a SimulatedPoint to ``(obj_ref, fc)`` for MMS protocol."""
    ied_name = source.connection.ied_name or "Simulator"
    ref = f"{ied_name}/{point.ln_name}.{point.do_name}"
    fc = _infer_fc(point)
    return ref, fc


def _value_type_from_data_type(data_type: str) -> str:
    """Map SimulatedPoint.data_type to MMS value type string."""
    mapping = {
        "BOOLEAN": "BOOLEAN",
        "INT8": "INT32",
        "INT16": "INT32",
        "INT32": "INT32",
        "UINT32": "UINT32",
        "INT64": "INT64",
        "FLOAT32": "FLOAT32",
        "FLOAT": "FLOAT32",
        "FLOAT64": "FLOAT64",
        "DOUBLE": "FLOAT64",
        "STRING": "VISIBLE_STRING",
        "VISIBLE_STRING": "VISIBLE_STRING",
    }
    return mapping.get(data_type.upper(), "FLOAT64")


def _parse_read_result(response: str) -> tuple[str, str]:
    """Parse a ``READ_RESULT`` line into ``(value, value_type)``.

    Format: ``READ_RESULT\\t<request_id>\\t<obj_ref>\\tok=1\\tOK\\t<value_type>\\t<value>``
    """
    parts = response.split("\t")
    if len(parts) >= 7 and parts[3] == "ok=1":
        return parts[6], parts[5]
    return "", ""


# ── Base ────────────────────────────────────────────────────────────────


class _BaseIec61850Facade(BaseSimulatorFacade):
    """IEC61850 通用基类。"""

    def __init__(self, source: SimulatedSource | None = None) -> None:
        self._source = source
        self._sim: Iec61850MmsSimulator | Iec61850ReportSimulator | None = None
        self._start_time_ms: int = 0

    async def stop(self) -> SimulatorResult:
        if self._sim is None:
            return SimulatorResult(SimulatorStatus.NOT_RUNNING)
        try:
            await asyncio.to_thread(self._sim.stop)
            self._sim = None
            return SimulatorResult(SimulatorStatus.OK)
        except Exception as exc:
            return SimulatorResult(SimulatorStatus.ERROR, str(exc))

    async def health(self) -> SimulatorHealth:
        if self._sim is None:
            return SimulatorHealth(SimulatorStatus.NOT_RUNNING)
        try:
            host = self._source.connection.host if self._source else _HOST
            port = self._source.connection.port if self._source else 0
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            try:
                sock.connect((host, port))
                return SimulatorHealth(
                    SimulatorStatus.OK, running=True,
                    uptime_ms=_now_ms() - self._start_time_ms,
                )
            except OSError:
                return SimulatorHealth(
                    SimulatorStatus.UNAVAILABLE, running=False,
                    message="port unreachable",
                )
            finally:
                sock.close()
        except Exception as exc:
            return SimulatorHealth(SimulatorStatus.ERROR, message=str(exc))

    async def load_points(self, points: list[SimulatorPoint]) -> SimulatorResult:
        return SimulatorResult(SimulatorStatus.OK)

    async def update_values(
        self, values: dict[str, str | int | float | bool | None],
    ) -> SimulatorResult:
        if self._sim is None:
            return SimulatorResult(SimulatorStatus.NOT_RUNNING)
        try:
            filtered = {k: v for k, v in values.items() if v is not None}
            self._sim.writes(filtered)
            return SimulatorResult(SimulatorStatus.OK)
        except Exception as exc:
            return SimulatorResult(SimulatorStatus.ERROR, str(exc))


# ── MMS Facade ──────────────────────────────────────────────────────────


class Iec61850MmsSimulatorFacade(_BaseIec61850Facade):
    """IEC61850 MMS simulator facade with real read/write via native runner.

    Starts the MMS simulator server (C subprocess), then launches the
    MMS client runner in interactive mode for protocol-level reads and writes.
    """

    def __init__(self, source: SimulatedSource | None = None) -> None:
        super().__init__(source)
        self._client: NativeInteractiveRunner | None = None
        self._sim_proc: subprocess.Popen[str] | None = None
        self._sim_stderr_thread: threading.Thread | None = None

    @property
    def protocol(self) -> str:
        return "iec61850_mms"

    @property
    def capabilities(self) -> SimulatorCapabilities:
        return SimulatorCapabilities(
            read=True,
            write=True,
            update_values=True,
        )

    async def start(self) -> SimulatorResult:
        if self._sim_proc is not None:
            return SimulatorResult(SimulatorStatus.ALREADY_RUNNING)
        if self._source is None:
            return SimulatorResult(SimulatorStatus.BAD_REQUEST, "no SimulatedSource provided")
        try:
            port = int(self._source.connection.port or 0)
            if port <= 0:
                return SimulatorResult(SimulatorStatus.BAD_REQUEST, f"invalid port: {port}")

            # Keep Python stub as data holder (no port binding — don't call .start())
            self._sim = Iec61850MmsSimulator(self._source)

            # 1. Start native C simulator server
            sim_path = _resolve_executable("iec61850_simulator_server")
            if not sim_path.exists():
                return SimulatorResult(
                    SimulatorStatus.NOT_IMPLEMENTED,
                    f"simulator server not compiled: {sim_path}",
                )

            proc = subprocess.Popen(
                [str(sim_path), str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
            assert proc.stdout is not None

            ready_line = await asyncio.to_thread(proc.stdout.readline)
            if ready_line.strip() != "READY":
                proc.terminate()
                return SimulatorResult(
                    SimulatorStatus.ERROR,
                    f"simulator server: expected READY, got {ready_line!r}",
                )

            self._sim_proc = proc
            self._sim_stderr_thread = start_stderr_drain_thread(
                proc.stderr, ProtocolDiagnostics()
            )
            self._start_time_ms = _now_ms()

            # 2. Start MMS client runner in interactive mode
            runner = NativeInteractiveRunner("iec61850_mms_client_runner")
            try:
                await asyncio.to_thread(runner.start)
            except Exception:
                self._sim = None
                proc.terminate()
                self._sim_proc = None
                raise
            self._client = runner

            return SimulatorResult(SimulatorStatus.OK)
        except Exception as exc:
            return SimulatorResult(SimulatorStatus.ERROR, str(exc))

    async def stop(self) -> SimulatorResult:
        # Stop client runner first
        if self._client is not None:
            try:
                await asyncio.to_thread(self._client.stop)
            except Exception:
                pass
            self._client = None
        # Stop C simulator
        if self._sim_proc is not None:
            proc = self._sim_proc
            self._sim_proc = None
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                    proc.wait(timeout=5)
                except Exception:
                    pass
        if self._sim_stderr_thread is not None:
            self._sim_stderr_thread.join(timeout=1.0)
            self._sim_stderr_thread = None
        # Stop Python data holder via base
        return await super().stop()

    async def read(self, point_keys: list[str]) -> ReadSimulatorResult:
        if self._client is None or not self._client.running:
            return ReadSimulatorResult(SimulatorStatus.NOT_RUNNING, "client runner not started")
        if self._source is None:
            return ReadSimulatorResult(SimulatorStatus.BAD_REQUEST, "no source configured")
        try:
            host = self._source.connection.host or _HOST
            port = int(self._source.connection.port or 0)
            if port <= 0:
                return ReadSimulatorResult(SimulatorStatus.BAD_REQUEST, f"invalid port: {port}")

            points_by_key = {p.key: p for p in self._source.points}
            values: dict[str, str | int | float | bool | None] = {}
            errors: list[str] = []

            for key in point_keys:
                point = points_by_key.get(key)
                if point is None:
                    errors.append(f"point not found: {key}")
                    continue

                ref, fc = _point_to_mms_ref(self._source, point)
                cmd = f"READ\t{key}\t{host}\t{port}\t{ref}\t{fc}"
                response = await asyncio.to_thread(self._client.command, cmd)
                val_str, _ = _parse_read_result(response)
                if val_str:
                    values[key] = _coerce_value(val_str, point.data_type)
                else:
                    errors.append(f"read failed for {key}: {response}")

            status = SimulatorStatus.PARTIAL_SUCCESS if errors else SimulatorStatus.OK
            msg = "; ".join(errors) if errors else ""
            return ReadSimulatorResult(status, message=msg, values=values)
        except Exception as exc:
            return ReadSimulatorResult(SimulatorStatus.ERROR, message=str(exc))

    async def write(
        self, values: dict[str, str | int | float | bool | None],
    ) -> SimulatorResult:
        if self._client is None or not self._client.running:
            return SimulatorResult(SimulatorStatus.NOT_RUNNING, "client runner not started")
        if self._source is None:
            return SimulatorResult(SimulatorStatus.BAD_REQUEST, "no source configured")
        try:
            host = self._source.connection.host or _HOST
            port = int(self._source.connection.port or 0)
            if port <= 0:
                return SimulatorResult(SimulatorStatus.BAD_REQUEST, f"invalid port: {port}")

            points_by_key = {p.key: p for p in self._source.points}
            errors: list[str] = []

            for key, val in values.items():
                if val is None:
                    continue
                point = points_by_key.get(key)
                if point is None:
                    errors.append(f"point not found: {key}")
                    continue

                ref, fc = _point_to_mms_ref(self._source, point)
                vt = _value_type_from_data_type(point.data_type)
                val_str = "true" if isinstance(val, bool) and val else \
                          "false" if isinstance(val, bool) else \
                          str(val)
                cmd = f"WRITE\t{key}\t{host}\t{port}\t{ref}\t{fc}\t{vt}\t{val_str}"
                response = await asyncio.to_thread(self._client.command, cmd)
                if "\tok=1\t" not in response:
                    errors.append(f"write failed for {key}: {response}")

            status = SimulatorStatus.PARTIAL_SUCCESS if errors else SimulatorStatus.OK
            msg = "; ".join(errors) if errors else ""
            return SimulatorResult(status, msg)
        except Exception as exc:
            return SimulatorResult(SimulatorStatus.ERROR, str(exc))


def _coerce_value(val_str: str, data_type: str) -> str | int | float | bool:
    """Coerce a string value to the Python type matching data_type."""
    dt = data_type.upper()
    if dt == "BOOLEAN":
        return val_str.lower() in ("true", "1", "yes")
    if dt in ("INT8", "INT16", "INT32", "UINT32", "INT64"):
        try:
            return int(val_str)
        except ValueError:
            return val_str
    if dt in ("FLOAT32", "FLOAT", "FLOAT64", "DOUBLE"):
        try:
            return float(val_str)
        except ValueError:
            return val_str
    return val_str


class Iec61850ReportSimulatorFacade(_BaseIec61850Facade):
    """IEC61850 Report simulator facade with real subscribe/report via native runner.

    Starts the MMS simulator server (C subprocess), then launches the
    report runner to subscribe to Report Control Block events.
    """

    _RCB_REF = "EventsRCB01"  # RCB name in the MMS simulator server

    def __init__(self, source: SimulatedSource | None = None) -> None:
        super().__init__(source)
        self._report_proc: subprocess.Popen[str] | None = None
        self._report_events: list[dict[str, str]] = []
        self._report_lock = threading.Lock()
        self._report_stop = threading.Event()
        self._sim_proc: subprocess.Popen[str] | None = None
        self._sim_stderr_thread: threading.Thread | None = None

    @property
    def protocol(self) -> str:
        return "iec61850_report"

    @property
    def capabilities(self) -> SimulatorCapabilities:
        return SimulatorCapabilities(
            subscribe=True,
            report=True,
            update_values=True,
        )

    async def start(self) -> SimulatorResult:
        if self._sim_proc is not None:
            return SimulatorResult(SimulatorStatus.ALREADY_RUNNING)
        if self._source is None:
            return SimulatorResult(SimulatorStatus.BAD_REQUEST, "no SimulatedSource provided")
        try:
            port = int(self._source.connection.port or 0)
            if port <= 0:
                return SimulatorResult(SimulatorStatus.BAD_REQUEST, f"invalid port: {port}")

            # Keep Python stub as data holder (no port binding)
            self._sim = Iec61850ReportSimulator(self._source)

            # Start native C simulator server (same binary as MMS)
            sim_path = _resolve_executable("iec61850_simulator_server")
            if not sim_path.exists():
                return SimulatorResult(
                    SimulatorStatus.NOT_IMPLEMENTED,
                    f"simulator server not compiled: {sim_path}",
                )

            proc = subprocess.Popen(
                [str(sim_path), str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
            assert proc.stdout is not None

            ready_line = await asyncio.to_thread(proc.stdout.readline)
            if ready_line.strip() != "READY":
                proc.terminate()
                return SimulatorResult(
                    SimulatorStatus.ERROR,
                    f"simulator server: expected READY, got {ready_line!r}",
                )

            self._sim_proc = proc
            self._sim_stderr_thread = start_stderr_drain_thread(
                proc.stderr, ProtocolDiagnostics()
            )
            self._start_time_ms = _now_ms()
            return SimulatorResult(SimulatorStatus.OK)
        except Exception as exc:
            return SimulatorResult(SimulatorStatus.ERROR, str(exc))

    async def stop(self) -> SimulatorResult:
        self._report_stop.set()
        if self._report_proc is not None:
            try:
                if self._report_proc.stdin is not None and self._report_proc.poll() is None:
                    self._report_proc.stdin.write("QUIT\n")
                    self._report_proc.stdin.flush()
                if self._report_proc.poll() is None:
                    self._report_proc.terminate()
                    self._report_proc.wait(timeout=5)
            except Exception:
                pass
            self._report_proc = None
        if self._sim_proc is not None:
            proc = self._sim_proc
            self._sim_proc = None
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                    proc.wait(timeout=5)
                except Exception:
                    pass
        if self._sim_stderr_thread is not None:
            self._sim_stderr_thread.join(timeout=1.0)
            self._sim_stderr_thread = None
        return await super().stop()

    async def subscribe(self, point_keys: list[str]) -> SimulatorResult:
        """Subscribe to report events by launching the report runner.

        Starts ``iec61850_report_runner`` as a subprocess connected to the
        running simulator server, waits for READY, and begins collecting
        REPORT events in a background thread.
        """
        if self._source is None:
            return SimulatorResult(SimulatorStatus.BAD_REQUEST, "no source configured")
        if self._report_proc is not None:
            return SimulatorResult(SimulatorStatus.ALREADY_RUNNING, "report runner already subscribed")
        if self._sim is None:
            return SimulatorResult(SimulatorStatus.NOT_RUNNING, "simulator not started")

        try:
            host = self._source.connection.host or _HOST
            port = int(self._source.connection.port or 0)
            if port <= 0:
                return SimulatorResult(SimulatorStatus.BAD_REQUEST, f"invalid port: {port}")

            ied_name = self._source.connection.ied_name or "Simulator"

            runner_path = _resolve_executable("iec61850_report_runner")
            if not runner_path.exists():
                return SimulatorResult(
                    SimulatorStatus.NOT_IMPLEMENTED,
                    f"report runner not compiled: {runner_path}",
                )

            proc = subprocess.Popen(
                [str(runner_path), host, str(port), ied_name, self._RCB_REF],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                bufsize=1,
            )
            assert proc.stdout is not None

            # Wait for READY
            ready_line = await asyncio.to_thread(proc.stdout.readline)
            if ready_line.strip() != "READY":
                proc.terminate()
                return SimulatorResult(
                    SimulatorStatus.ERROR,
                    f"report runner: expected READY, got {ready_line!r}",
                )

            self._report_proc = proc
            self._report_stop.clear()

            # Start background collection thread
            thread = threading.Thread(
                target=_collect_report_events,
                args=(proc.stdout, self._report_events, self._report_lock, self._report_stop),
                daemon=True,
            )
            thread.start()

            return SimulatorResult(SimulatorStatus.OK, "report subscription active")
        except Exception as exc:
            return SimulatorResult(SimulatorStatus.ERROR, str(exc))

    async def report(self, point_keys: list[str]) -> SimulatorResult:
        """Return collected report events.

        Drains the internal event queue and returns events as a
        message string.
        """
        if self._report_proc is None:
            return SimulatorResult(SimulatorStatus.NOT_RUNNING, "report runner not subscribed")
        with self._report_lock:
            events = list(self._report_events)
            self._report_events.clear()
        if not events:
            return SimulatorResult(SimulatorStatus.OK, "no report events collected")
        lines = "\n".join(
            f"REPORT\trcb={e.get('rcb','-')}\tseq={e.get('seq','-')}\tvalues={e.get('values','-')}"
            for e in events
        )
        return SimulatorResult(SimulatorStatus.OK, lines)


def _collect_report_events(
    stream: Any,
    events: list[dict[str, str]],
    lock: threading.Lock,
    stop: threading.Event,
) -> None:
    """Background thread: read REPORT lines from stream and collect into events list."""
    try:
        while not stop.is_set():
            line = stream.readline()
            if not line:
                break
            text = line.strip()
            if text.startswith("REPORT\t"):
                parts = text.split("\t")
                event: dict[str, str] = {}
                if len(parts) >= 5:
                    event["rcb"] = parts[1]
                    event["timestamp"] = parts[2]
                    event["seq"] = parts[3]
                    event["count"] = parts[4]
                    if len(parts) > 5:
                        event["values"] = "\t".join(parts[5:])
                with lock:
                    events.append(event)
            elif text == "STOPPED":
                break
    except Exception:
        pass


class Iec61850GooseSimulatorFacade(BaseSimulatorFacade):
    """IEC61850 GOOSE simulator facade backed by native L2 publisher/subscriber."""

    def __init__(self, source: SimulatedSource | None = None) -> None:
        self._source = source
        self._proc: subprocess.Popen[str] | None = None
        self._stderr_thread: threading.Thread | None = None
        self._start_time_ms: int = 0

    @property
    def protocol(self) -> str:
        return "iec61850_goose"

    @property
    def capabilities(self) -> SimulatorCapabilities:
        return SimulatorCapabilities(
            read=False,
            write=False,
            subscribe=True,
            report=False,
            update_values=True,
        )

    async def start(self) -> SimulatorResult:
        if self._proc is not None:
            return SimulatorResult(SimulatorStatus.ALREADY_RUNNING)
        if self._source is None:
            return SimulatorResult(SimulatorStatus.BAD_REQUEST, "no SimulatedSource provided")
        runner_path = _resolve_executable("iec61850_goose_publisher_simulator")
        if not runner_path.exists():
            return SimulatorResult(
                SimulatorStatus.NOT_IMPLEMENTED,
                f"GOOSE publisher not compiled: {runner_path}",
            )
        interface_id = _l2_interface(self._source)
        app_id = str(_l2_app_id(self._source, 1000))
        interval_ms = str(_l2_interval_ms(self._source, 1000))
        return await _start_l2_publisher(
            self,
            [str(runner_path), interface_id, app_id, interval_ms],
            "GOOSE publisher",
        )

    async def stop(self) -> SimulatorResult:
        return await _stop_l2_publisher(self)

    async def health(self) -> SimulatorHealth:
        return _l2_health(self)

    async def subscribe(self, point_keys: list[str]) -> SimulatorResult:
        if self._source is None:
            return SimulatorResult(SimulatorStatus.BAD_REQUEST, "no source configured")
        return await _probe_l2_subscriber(
            source=self._source,
            runner_name="iec61850_goose_subscriber_runner",
            app_id_default=1000,
            event_label="GOOSE event",
        )


class Iec61850SvSimulatorFacade(BaseSimulatorFacade):
    """IEC61850 SV simulator facade backed by native L2 publisher/subscriber."""

    def __init__(self, source: SimulatedSource | None = None) -> None:
        self._source = source
        self._proc: subprocess.Popen[str] | None = None
        self._stderr_thread: threading.Thread | None = None
        self._start_time_ms: int = 0

    @property
    def protocol(self) -> str:
        return "iec61850_sv"

    @property
    def capabilities(self) -> SimulatorCapabilities:
        return SimulatorCapabilities(
            read=False,
            write=False,
            subscribe=True,
            report=False,
            update_values=True,
        )

    async def start(self) -> SimulatorResult:
        if self._proc is not None:
            return SimulatorResult(SimulatorStatus.ALREADY_RUNNING)
        if self._source is None:
            return SimulatorResult(SimulatorStatus.BAD_REQUEST, "no SimulatedSource provided")
        runner_path = _resolve_executable("iec61850_sv_publisher_simulator")
        if not runner_path.exists():
            return SimulatorResult(
                SimulatorStatus.NOT_IMPLEMENTED,
                f"SV publisher not compiled: {runner_path}",
            )
        interface_id = _l2_interface(self._source)
        app_id = str(_l2_app_id(self._source, 4000))
        sample_rate = str(_l2_sample_rate_hz(self._source, 1))
        return await _start_l2_publisher(
            self,
            [str(runner_path), interface_id, app_id, sample_rate],
            "SV publisher",
        )

    async def stop(self) -> SimulatorResult:
        return await _stop_l2_publisher(self)

    async def health(self) -> SimulatorHealth:
        return _l2_health(self)

    async def subscribe(self, point_keys: list[str]) -> SimulatorResult:
        if self._source is None:
            return SimulatorResult(SimulatorStatus.BAD_REQUEST, "no source configured")
        return await _probe_l2_subscriber(
            source=self._source,
            runner_name="iec61850_sv_subscriber_runner",
            app_id_default=4000,
            event_label="SV sample",
        )


def _l2_interface(source: SimulatedSource) -> str:
    value = source.connection.params.get("l2_interface")
    if value is None or str(value).strip() == "":
        return os.environ.get("SOURCE_LAB_L2_INTERFACE", "lo")
    return str(value)


def _l2_app_id(source: SimulatedSource, default: int) -> int:
    value = source.connection.params.get("app_id", default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _l2_interval_ms(source: SimulatedSource, default: int) -> int:
    value = source.connection.params.get("publish_interval_ms")
    if value is None:
        value = source.connection.params.get("internal_update_interval_ms", default)
    try:
        return max(1, int(float(value)))
    except (TypeError, ValueError):
        return default


def _l2_sample_rate_hz(source: SimulatedSource, default: int) -> int:
    value = source.connection.params.get("sample_rate_hz")
    if value is None:
        interval_ms = _l2_interval_ms(source, 1000)
        return max(1, int(round(1000.0 / interval_ms)))
    try:
        return max(1, int(float(value)))
    except (TypeError, ValueError):
        return default


async def _start_l2_publisher(
    facade: Iec61850GooseSimulatorFacade | Iec61850SvSimulatorFacade,
    cmd: list[str],
    label: str,
) -> SimulatorResult:
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
    except Exception as exc:
        return SimulatorResult(
            SimulatorStatus.UNAVAILABLE,
            f"{label} failed to start: {exc}; raw socket / CAP_NET_RAW may be required",
        )

    assert proc.stdout is not None
    ready_line = await asyncio.to_thread(proc.stdout.readline)
    if ready_line.strip() != "READY":
        stderr = ""
        if proc.stderr is not None:
            try:
                stderr = await asyncio.to_thread(proc.stderr.readline)
            except Exception:
                stderr = ""
        proc.terminate()
        return SimulatorResult(
            SimulatorStatus.UNAVAILABLE,
            f"{label}: expected READY, got {ready_line!r}. {stderr.strip()} "
            "raw socket / CAP_NET_RAW / interface permission may be required",
        )
    facade._proc = proc
    facade._stderr_thread = start_stderr_drain_thread(proc.stderr, ProtocolDiagnostics())
    facade._start_time_ms = _now_ms()
    return SimulatorResult(SimulatorStatus.OK, f"{label} active")


async def _stop_l2_publisher(
    facade: Iec61850GooseSimulatorFacade | Iec61850SvSimulatorFacade,
) -> SimulatorResult:
    if facade._proc is None:
        return SimulatorResult(SimulatorStatus.NOT_RUNNING)
    proc = facade._proc
    facade._proc = None
    try:
        proc.terminate()
        await asyncio.to_thread(proc.wait, 5)
    except Exception:
        try:
            proc.kill()
            await asyncio.to_thread(proc.wait, 5)
        except Exception:
            pass
    if facade._stderr_thread is not None:
        facade._stderr_thread.join(timeout=1.0)
        facade._stderr_thread = None
    return SimulatorResult(SimulatorStatus.OK)


def _l2_health(
    facade: Iec61850GooseSimulatorFacade | Iec61850SvSimulatorFacade,
) -> SimulatorHealth:
    proc = facade._proc
    if proc is None:
        return SimulatorHealth(SimulatorStatus.NOT_RUNNING)
    if proc.poll() is None:
        return SimulatorHealth(
            SimulatorStatus.OK,
            running=True,
            uptime_ms=_now_ms() - facade._start_time_ms,
        )
    return SimulatorHealth(
        SimulatorStatus.UNAVAILABLE,
        running=False,
        message=f"publisher exited with code {proc.returncode}",
    )


async def _probe_l2_subscriber(
    *,
    source: SimulatedSource,
    runner_name: str,
    app_id_default: int,
    event_label: str,
) -> SimulatorResult:
    runner_path = _resolve_executable(runner_name)
    if not runner_path.exists():
        return SimulatorResult(
            SimulatorStatus.NOT_IMPLEMENTED,
            f"{runner_name} not compiled: {runner_path}",
        )
    cmd = [
        str(runner_path),
        _l2_interface(source),
        str(_l2_app_id(source, app_id_default)),
        str(int(source.connection.params.get("probe_duration_s", 3))),
    ]
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
    except Exception as exc:
        return SimulatorResult(
            SimulatorStatus.UNAVAILABLE,
            f"{runner_name} failed to start: {exc}; raw socket / CAP_NET_RAW may be required",
        )

    assert proc.stdout is not None
    notifications = 0
    noise: list[str] = []
    try:
        while True:
            line = await asyncio.to_thread(proc.stdout.readline)
            if not line:
                break
            text = line.strip()
            if text.startswith("NOTIFY\t"):
                notifications += 1
            elif text.startswith("STREAM_SUMMARY\t"):
                parts = text.split("\t")
                if len(parts) >= 2:
                    try:
                        notifications = max(notifications, int(parts[1]))
                    except ValueError:
                        pass
            elif text == "DONE":
                break
            elif text and len(noise) < 3:
                noise.append(text)
        await asyncio.to_thread(proc.wait, 5)
    except Exception as exc:
        proc.terminate()
        return SimulatorResult(SimulatorStatus.ERROR, f"{runner_name} probe failed: {exc}")

    if notifications <= 0:
        return SimulatorResult(
            SimulatorStatus.UNAVAILABLE,
            f"{runner_name} received no {event_label}. raw socket / CAP_NET_RAW / "
            f"interface={_l2_interface(source)} may be required; noise={noise}",
        )
    return SimulatorResult(
        SimulatorStatus.OK,
        f"{event_label} received: count={notifications}",
    )


def _now_ms() -> int:
    return int(asyncio.get_event_loop().time() * 1000)
