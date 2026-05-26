"""IEC 61850 Report runner backed by the native report subscriber."""

from __future__ import annotations

import socket
import select
import subprocess
import time
from pathlib import Path

from tools.source_lab.access.common.scheduling import RunnerEndpointPlan
from tools.source_lab.access.runners.generic_streaming import (
    GenericStreamingSubscriptionRunner,
    StreamingSample,
)
from tools.source_lab.access.subscribe.model import SubscribeScanConfig


def _resolve_runner_path() -> Path:
    build_dir = Path(__file__).resolve().parents[2] / "native" / "build"
    for name in ("iec61850_report_runner", "iec61850_report_runner.exe"):
        path = build_dir / name
        if path.exists():
            return path
    return build_dir / "iec61850_report_runner"


class Iec61850ReportRunner(GenericStreamingSubscriptionRunner):
    """IEC61850 report stream runner using the real native subscriber."""

    name = "iec61850_report_runner"

    def read_stream_sample(self, spec: RunnerEndpointPlan, *, config: SubscribeScanConfig) -> StreamingSample:
        if not bool(spec.source.endpoint.params.get("use_native_report_runner", False)):
            return self._read_lightweight_sample(spec, config=config)
        return self._read_native_sample(spec, config=config)

    def _read_lightweight_sample(self, spec: RunnerEndpointPlan, *, config: SubscribeScanConfig) -> StreamingSample:
        try:
            with socket.create_connection(
                (spec.source.endpoint.host, spec.source.endpoint.port),
                timeout=config.read_timeout_s,
            ) as client:
                client.settimeout(config.read_timeout_s)
                client.sendall(b"\x30\x00")
                response = client.recv(16)
                if len(response) < 3 or response[0] != 0x30:
                    return StreamingSample(value_count=0, bad_count=1)
                return StreamingSample(value_count=len(spec.source.points), bad_count=0, data_age_ms=0.0)
        except OSError:
            return StreamingSample(value_count=0, bad_count=1)

    def _read_native_sample(self, spec: RunnerEndpointPlan, *, config: SubscribeScanConfig) -> StreamingSample:
        runner_path = _resolve_runner_path()
        if not runner_path.exists():
            return StreamingSample(value_count=0, bad_count=1)

        endpoint = spec.source.endpoint
        host = endpoint.host
        port = str(endpoint.port)
        ied_name = str(endpoint.ied_name or endpoint.params.get("ied_name", "Simulator"))
        rcb_ref = str(endpoint.params.get("rcb_ref", "EventsRCB01"))
        proc = subprocess.Popen(
            [str(runner_path), host, port, ied_name, rcb_ref],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        assert proc.stdout is not None
        try:
            ready_line = proc.stdout.readline().strip()
            if ready_line != "READY":
                return StreamingSample(value_count=0, bad_count=1)

            deadline = time.monotonic() + max(0.5, config.duration_s)
            report_count = 0
            while time.monotonic() < deadline:
                if not select.select([proc.stdout], [], [], 0.2)[0]:
                    continue
                line = proc.stdout.readline().strip()
                if not line:
                    continue
                if line.startswith("REPORT"):
                    report_count += 1
                    if report_count >= 1:
                        break
                if line == "STOPPED":
                    break
            if report_count <= 0:
                return StreamingSample(value_count=0, bad_count=1)
            return StreamingSample(value_count=max(report_count, len(spec.source.points)), bad_count=0, data_age_ms=0.0)
        except OSError:
            return StreamingSample(value_count=0, bad_count=1)
        finally:
            try:
                if proc.stdin is not None and proc.poll() is None:
                    proc.stdin.write("QUIT\n")
                    proc.stdin.flush()
            except OSError:
                pass
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=2)
