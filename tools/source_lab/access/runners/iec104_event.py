"""IEC 60870-5-104 event streaming runner。

注意：当前是 fake_or_simulated_runner，用于 source_lab access 框架验证；
只做 TESTFR_ACT 链路确认，不等价于完整 IEC104 遥测/遥信/总召规约状态机。
"""

from __future__ import annotations

import socket

from tools.source_lab.access.runners.generic_streaming import GenericStreamingSubscriptionRunner, StreamingSample
from tools.source_lab.access.common.scheduling import RunnerEndpointPlan
from tools.source_lab.access.subscribe.model import SubscribeScanConfig

_TESTFR_ACT = b"\x68\x04\x43\x00\x00\x00"


class Iec104EventRunner(GenericStreamingSubscriptionRunner):
    """IEC104 event stream runner。"""

    name = "iec104_event_runner"

    def read_stream_sample(self, spec: RunnerEndpointPlan, *, config: SubscribeScanConfig) -> StreamingSample:
        try:
            with socket.create_connection((spec.source.endpoint.host, spec.source.endpoint.port), timeout=config.read_timeout_s) as client:
                client.sendall(_TESTFR_ACT)
                _ = client.recv(16)
                return StreamingSample(value_count=len(spec.source.points), data_age_ms=0.0)
        except OSError:
            return StreamingSample(value_count=0, bad_count=1)
