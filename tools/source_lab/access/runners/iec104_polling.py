"""IEC 60870-5-104 polling runner（TCP 探测 + TESTFR）。"""

from __future__ import annotations

import socket
import time

from tools.source_lab.access.polling.model import CapacityScanConfig
from tools.source_lab.access.runners.generic_polling import GenericPollingCapacityRunner, PollingReadSample
from tools.source_lab.access.common.scheduling import RunnerEndpointPlan

_TESTFR_ACT = b"\x68\x04\x43\x00\x00\x00"


class Iec104PollingRunner(GenericPollingCapacityRunner):
    """IEC104 polling runner。"""

    name = "iec104_polling_runner"

    def read_once(self, spec: RunnerEndpointPlan, *, target_hz: float, config: CapacityScanConfig) -> PollingReadSample:
        try:
            with socket.create_connection((spec.source.endpoint.host, spec.source.endpoint.port), timeout=config.read_timeout_s) as client:
                client.sendall(_TESTFR_ACT)
                _ = client.recv(16)
                return PollingReadSample(ok=True, value_count=len(spec.source.points), response_timestamp_s=time.time())
        except OSError:
            return PollingReadSample(ok=False, value_count=0, response_timestamp_s=None, error_code="transport_error")
