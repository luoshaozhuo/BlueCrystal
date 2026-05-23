"""IEC 61850 MMS polling runner（TCP/MMS 会话可达性读取）。

注意：当前只做最小 MMS-like 语义探测（发送 \\x30\\x00 并检查响应前缀）；
未实现完整 ASN.1/MMS 解析，不等价于完整 IEC61850 协议实现。
"""

from __future__ import annotations

import socket
import time

from tools.source_lab.access.polling.model import CapacityScanConfig
from tools.source_lab.access.runners.generic_polling import GenericPollingCapacityRunner, PollingReadSample
from tools.source_lab.access.common.scheduling import RunnerEndpointPlan

_MMS_PROBE_REQUEST = b"\x30\x00"


def _is_valid_mms_like_response(payload: bytes) -> bool:
    """Validate a minimal MMS-like response frame."""

    return len(payload) >= 3 and payload[0] == 0x30


class Iec61850MmsPollingRunner(GenericPollingCapacityRunner):
    """IEC61850 MMS polling runner。"""

    name = "iec61850_mms_polling_runner"

    def read_once(self, spec: RunnerEndpointPlan, *, target_hz: float, config: CapacityScanConfig) -> PollingReadSample:
        try:
            with socket.create_connection((spec.source.endpoint.host, spec.source.endpoint.port), timeout=config.read_timeout_s) as client:
                client.settimeout(config.read_timeout_s)
                client.sendall(_MMS_PROBE_REQUEST)
                response = client.recv(16)
                if not _is_valid_mms_like_response(response):
                    return PollingReadSample(ok=False, value_count=0, response_timestamp_s=None, error_code="protocol_error")
                return PollingReadSample(ok=True, value_count=len(spec.source.points), response_timestamp_s=time.time())
        except OSError:
            return PollingReadSample(ok=False, value_count=0, response_timestamp_s=None, error_code="transport_error")
