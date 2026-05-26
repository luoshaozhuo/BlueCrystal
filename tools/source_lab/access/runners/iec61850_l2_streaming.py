"""IEC 61850 GOOSE/SV native L2 subscription runners."""

from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from tools.source_lab.access.common.access_model import AccessBatch, AccessMode
from tools.source_lab.access.common.scheduling import RunnerEndpointPlan
from tools.source_lab.access.runners.base import SubscriptionRunner
from tools.source_lab.access.runners.native_process import stop_native_process
from tools.source_lab.access.runners.protocol import ProtocolDiagnostics, start_stderr_drain_thread
from tools.source_lab.access.subscribe.model import SubscribeScanConfig, SubscribeWorkerRawStats

_RAW_SOCKET_HINT = (
    "raw socket / CAP_NET_RAW required. CI: "
    "cmake -S tools/source_lab/native -B tools/source_lab/native/build && "
    "cmake --build tools/source_lab/native/build --target "
)


@dataclass(frozen=True, slots=True)
class _StreamSession:
    notifications: int
    value_count: int
    bad_count: int
    missing_ts_count: int
    noise_count: int
    noise_samples: tuple[str, ...]


def _find_executable(name: str) -> Path | None:
    root = Path(__file__).resolve().parents[2] / "native" / "build"
    for candidate in (
        root / name,
        root / "bin" / name,
        root / "Release" / name,
    ):
        if candidate.exists():
            return candidate
    return None


def _l2_interface(spec: RunnerEndpointPlan) -> str:
    raw = spec.source.endpoint.params.get("l2_interface")
    if raw is None or str(raw).strip() == "":
        return os.environ.get("SOURCE_LAB_L2_INTERFACE", "lo")
    return str(raw)


def _app_id(spec: RunnerEndpointPlan, default: int) -> int:
    raw = spec.source.endpoint.params.get("app_id", default)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


class _Iec61850L2StreamingRunner(SubscriptionRunner):
    """Run a native IEC 61850 L2 subscriber and adapt stdout to scan stats."""

    name = "iec61850_l2_streaming_runner"
    executable_name = ""
    default_app_id = 0

    def _command(self, spec: RunnerEndpointPlan, config: SubscribeScanConfig) -> list[str]:
        exe = _find_executable(self.executable_name)
        if exe is None:
            raise RuntimeError(
                f"dependency_missing: {self.executable_name} not compiled. "
                f"{_RAW_SOCKET_HINT}{self.executable_name}"
            )
        duration_s = max(1, int(round(config.duration_s)))
        return [str(exe), _l2_interface(spec), str(_app_id(spec, self.default_app_id)), str(duration_s)]

    def _parse_stream(self, proc: subprocess.Popen[str], diagnostics: ProtocolDiagnostics) -> _StreamSession:
        assert proc.stdout is not None
        notifications = 0
        value_count = 0
        bad_count = 0
        missing_ts_count = 0
        noise_count = 0
        noise_samples: tuple[str, ...] = ()

        for raw_line in proc.stdout:
            line = raw_line.rstrip("\n\r")
            if not line or line == "READY":
                continue
            if line.startswith("NOTIFY\t"):
                notifications += 1
                parts = line.split("\t")
                value_count += max(1, len(parts) - 9)
                if "0\t0" in line:
                    missing_ts_count += 1
                continue
            if line.startswith("STREAM_SUMMARY\t"):
                parts = line.split("\t")
                if len(parts) >= 3:
                    try:
                        notifications = max(notifications, int(parts[1]))
                        bad_count += int(parts[2])
                    except ValueError:
                        pass
                continue
            if line == "DONE":
                break
            if line.startswith("ERROR"):
                bad_count += 1
                diagnostics.record_stderr(line)
                continue
            noise_count += 1
            if noise_count <= 5:
                noise_samples = noise_samples + (line,)

        return _StreamSession(
            notifications=notifications,
            value_count=value_count,
            bad_count=bad_count,
            missing_ts_count=missing_ts_count,
            noise_count=noise_count,
            noise_samples=noise_samples,
        )

    def run_worker(
        self,
        worker_index: int,
        specs: tuple[RunnerEndpointPlan, ...],
        config: SubscribeScanConfig,
    ) -> SubscribeWorkerRawStats:
        if not specs:
            return SubscribeWorkerRawStats(
                worker_index=worker_index,
                endpoint_count=0,
                expected_monitored_items=0,
                monitored_created=0,
                monitored_failed=0,
                batches=(),
                notification_count=0,
                value_count=0,
                bad_count=0,
                missing_ts_count=0,
                reserved_sequence_gap_count=0,
                reserved_queue_overflow_count=0,
                keepalive_count=0,
                publish_timeout_count=0,
                reconnect_count=0,
            )

        diagnostics = ProtocolDiagnostics()
        batches: list[AccessBatch] = []
        total_notifications = 0
        total_values = 0
        total_bad = 0
        total_missing_ts = 0
        noise_count = 0
        noise_samples: tuple[str, ...] = ()

        for local_index, spec in enumerate(specs):
            cmd = self._command(spec, config)
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
                raise RuntimeError(
                    f"failed to start {self.executable_name}: {exc}. "
                    f"{_RAW_SOCKET_HINT}{self.executable_name}"
                ) from exc

            start_ns = time.time_ns()
            stderr_thread = start_stderr_drain_thread(proc.stderr, diagnostics)
            try:
                session = self._parse_stream(proc, diagnostics)
            finally:
                stop_native_process(proc)
                stderr_thread.join(timeout=1.0)

            if session.notifications <= 0:
                raise RuntimeError(
                    f"{self.executable_name} received zero events/samples. "
                    f"interface={_l2_interface(spec)} app_id={_app_id(spec, self.default_app_id)} "
                    f"{_RAW_SOCKET_HINT}{self.executable_name}"
                )

            total_notifications += session.notifications
            total_values += max(session.value_count, session.notifications)
            total_bad += session.bad_count
            total_missing_ts += session.missing_ts_count
            noise_count += session.noise_count
            noise_samples = noise_samples + session.noise_samples

            for seq in range(session.notifications):
                ts = start_ns + seq
                batches.append(
                    AccessBatch(
                        endpoint_id=spec.source.endpoint.name,
                        profile_id=str(spec.source.endpoint.params.get("profile_id", "")),
                        protocol=str(spec.source.endpoint.protocol),
                        access_mode=AccessMode.SUBSCRIBE,
                        worker_index=worker_index,
                        local_index=local_index,
                        global_index=spec.global_index,
                        batch_index=seq,
                        sequence=seq,
                        scheduled_ns=None,
                        started_ns=start_ns,
                        received_ns=ts,
                        source_timestamp_s=time.time(),
                        server_timestamp_s=time.time(),
                        value_count=1,
                        expected_count=max(1, len(spec.source.points)),
                        bad_count=0,
                        missing_timestamp_count=0,
                        error_code=None,
                        data_age_ms=0.0,
                        period_ms=config.publishing_interval_ms,
                        notify_timestamp_ns=ts,
                        flush_timestamp_ns=ts + 1,
                    )
                )

        expected = sum(len(spec.source.points) for spec in specs)
        return SubscribeWorkerRawStats(
            worker_index=worker_index,
            endpoint_count=len(specs),
            expected_monitored_items=expected,
            monitored_created=expected,
            monitored_failed=0,
            batches=tuple(batches),
            notification_count=total_notifications,
            value_count=total_values,
            bad_count=total_bad,
            missing_ts_count=total_missing_ts,
            reserved_sequence_gap_count=0,
            reserved_queue_overflow_count=0,
            keepalive_count=0,
            publish_timeout_count=0,
            reconnect_count=0,
            runner_protocol_noise_count=noise_count,
            runner_protocol_noise_samples=noise_samples[:5],
        )


class Iec61850GooseStreamingRunner(_Iec61850L2StreamingRunner):
    """IEC 61850 GOOSE native subscriber runner."""

    name = "iec61850_goose_subscriber_runner"
    executable_name = "iec61850_goose_subscriber_runner"
    default_app_id = 1000


class Iec61850SvStreamingRunner(_Iec61850L2StreamingRunner):
    """IEC 61850 SV native subscriber runner."""

    name = "iec61850_sv_subscriber_runner"
    executable_name = "iec61850_sv_subscriber_runner"
    default_app_id = 4000
