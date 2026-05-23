"""IEC 60870-5-101 event streaming runner。

注意：当前是 fake_or_simulated_runner，用于 source_lab access 框架验证；
只做最小链路确认，不等价于完整 IEC101 遥测/遥信/总召规约状态机。
"""

from __future__ import annotations

import socket
import time

from tools.source_lab.access.runners.generic_streaming import GenericStreamingSubscriptionRunner, StreamingSample
from tools.source_lab.access.common.scheduling import RunnerEndpointPlan
from tools.source_lab.access.subscribe.model import SubscribeScanConfig


class Iec101EventRunner(GenericStreamingSubscriptionRunner):
    """IEC101 event stream runner。"""

    name = "iec101_event_runner"

    def read_stream_sample(self, spec: RunnerEndpointPlan, *, config: SubscribeScanConfig) -> StreamingSample:
        serial_result = self._read_serial(spec, config)
        if serial_result is not None:
            return serial_result
        return self._read_tcp_gateway(spec, config)

    def _read_serial(self, spec: RunnerEndpointPlan, config: SubscribeScanConfig) -> StreamingSample | None:
        try:
            import serial  # type: ignore[import-untyped]
        except Exception:
            return None
        device = str(spec.source.endpoint.params.get("serial_port", ""))
        if not device:
            return None
        try:
            with serial.Serial(device, baudrate=int(spec.source.endpoint.params.get("baudrate", 9600)), timeout=config.read_timeout_s):
                return StreamingSample(value_count=len(spec.source.points), data_age_ms=0.0)
        except Exception:
            return StreamingSample(value_count=0, bad_count=1)

    def _read_tcp_gateway(self, spec: RunnerEndpointPlan, config: SubscribeScanConfig) -> StreamingSample:
        try:
            with socket.create_connection(
                (spec.source.endpoint.host, spec.source.endpoint.port),
                timeout=config.read_timeout_s,
            ) as conn:
                conn.sendall(b"\x10\x49\x00\x49\x16")
                conn.settimeout(config.read_timeout_s)
                _response = conn.recv(256)
                return StreamingSample(
                    value_count=len(spec.source.points),
                    bad_count=0,
                    data_age_ms=0.0,
                )
        except Exception:
            return StreamingSample(value_count=0, bad_count=1)
