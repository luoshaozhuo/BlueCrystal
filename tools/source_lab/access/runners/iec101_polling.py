"""IEC 60870-5-101 polling runner（串口链路探测）。"""

from __future__ import annotations

import socket
import time

from tools.source_lab.access.polling.model import CapacityScanConfig
from tools.source_lab.access.runners.generic_polling import GenericPollingCapacityRunner, PollingReadSample
from tools.source_lab.access.common.scheduling import RunnerEndpointPlan


class Iec101PollingRunner(GenericPollingCapacityRunner):
    """IEC101 polling runner，执行串口链路读探测。"""

    name = "iec101_polling_runner"

    def read_once(self, spec: RunnerEndpointPlan, *, target_hz: float, config: CapacityScanConfig) -> PollingReadSample:
        del target_hz
        serial_result = self._read_serial(spec, config)
        if serial_result is not None:
            return serial_result
        return self._read_tcp_gateway(spec, config)

    def _read_serial(self, spec: RunnerEndpointPlan, config: CapacityScanConfig) -> PollingReadSample | None:
        try:
            import serial  # type: ignore[import-untyped]
        except Exception:
            return None
        device = str(spec.source.endpoint.params.get("serial_port", ""))
        if not device:
            return None
        try:
            with serial.Serial(device, baudrate=int(spec.source.endpoint.params.get("baudrate", 9600)), timeout=config.read_timeout_s):
                return PollingReadSample(ok=True, value_count=len(spec.source.points), response_timestamp_s=time.time())
        except Exception:
            return PollingReadSample(ok=False, value_count=0, response_timestamp_s=None, error_code="transport_error")

    def _read_tcp_gateway(self, spec: RunnerEndpointPlan, config: CapacityScanConfig) -> PollingReadSample:
        try:
            with socket.create_connection(
                (spec.source.endpoint.host, spec.source.endpoint.port),
                timeout=config.read_timeout_s,
            ) as conn:
                conn.sendall(b"\x10\x49\x00\x49\x16")
                conn.settimeout(config.read_timeout_s)
                _response = conn.recv(256)
                return PollingReadSample(ok=True, value_count=len(spec.source.points), response_timestamp_s=time.time())
        except Exception:
            return PollingReadSample(ok=False, value_count=0, response_timestamp_s=None, error_code="transport_error")
