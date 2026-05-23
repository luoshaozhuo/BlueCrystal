"""IEC 61850 Report streaming runner。

注意：当前只做最小 Report-like 语义探测（发送 \\x30\\x00 并检查响应前缀）；
未实现完整 IEC61850 Report 标准栈，不等价于完整工业协议实现。
"""

from __future__ import annotations

import socket

from tools.source_lab.access.runners.generic_streaming import GenericStreamingSubscriptionRunner, StreamingSample
from tools.source_lab.access.common.scheduling import RunnerEndpointPlan
from tools.source_lab.access.subscribe.model import SubscribeScanConfig

_MMS_PROBE_REQUEST = b"\x30\x00"


def _is_valid_mms_like_response(payload: bytes) -> bool:
    """Validate a minimal MMS-like response frame."""

    return len(payload) >= 3 and payload[0] == 0x30


class Iec61850ReportRunner(GenericStreamingSubscriptionRunner):
    """IEC61850 report stream runner。"""

    name = "iec61850_report_runner"

    def read_stream_sample(self, spec: RunnerEndpointPlan, *, config: SubscribeScanConfig) -> StreamingSample:
        try:
            with socket.create_connection((spec.source.endpoint.host, spec.source.endpoint.port), timeout=config.read_timeout_s) as client:
                client.settimeout(config.read_timeout_s)
                client.sendall(_MMS_PROBE_REQUEST)
                response = client.recv(16)
                if not _is_valid_mms_like_response(response):
                    return StreamingSample(value_count=0, bad_count=1)
                return StreamingSample(value_count=len(spec.source.points), data_age_ms=0.0)
        except OSError:
            return StreamingSample(value_count=0, bad_count=1)
