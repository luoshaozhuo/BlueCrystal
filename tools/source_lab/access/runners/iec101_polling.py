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
                response = conn.recv(4096)

                value_count = 0
                pos = 0
                while pos < len(response):
                    if response[pos] == 0x10:
                        pos += 5  # 固定帧: 0x10 CI ADDR CHK 0x16
                        continue
                    if response[pos] != 0x68:
                        pos += 1
                        continue
                    if pos + 3 >= len(response):
                        break
                    L = response[pos + 1]
                    frame_end = pos + 3 + L + 1
                    if frame_end > len(response):
                        break
                    # ASDU 从 pos+6 开始: 0x68 LEN LEN 0x68 CI ADDR ASDU...
                    asdu_start = pos + 6
                    if asdu_start + 1 >= len(response):
                        pos = frame_end
                        continue
                    vsq = response[asdu_start + 1]
                    elements = vsq & 0x7F  # VSQ 低7位为元素数
                    if elements == 0:
                        elements = 1
                    value_count += elements
                    pos = frame_end

                if value_count == 0:
                    return PollingReadSample(ok=False, value_count=0, response_timestamp_s=None, error_code="no_asdu")
                return PollingReadSample(ok=True, value_count=value_count, response_timestamp_s=time.time())
        except Exception:
            return PollingReadSample(ok=False, value_count=0, response_timestamp_s=None, error_code="transport_error")
