"""Modbus TCP polling runner（真实 TCP 帧读）。

注意：当前为 Python socket 轻量实现，未使用 libmodbus native 后端；
实现了 Modbus 功能码 0x03 读写，不等价于完整 Modbus 协议栈。
"""

from __future__ import annotations

import socket
import struct
import time

from tools.source_lab.access.polling.model import CapacityScanConfig
from tools.source_lab.access.runners.generic_polling import GenericPollingCapacityRunner, PollingReadSample
from tools.source_lab.access.common.scheduling import RunnerEndpointPlan


class ModbusTcpPollingRunner(GenericPollingCapacityRunner):
    """基于 Modbus TCP 功能码 0x03 的 polling runner。"""

    name = "modbus_tcp_polling_runner"

    def read_once(
        self,
        spec: RunnerEndpointPlan,
        *,
        target_hz: float,
        config: CapacityScanConfig,
    ) -> PollingReadSample:
        unit_id = int(spec.source.endpoint.params.get("modbus_unit_id", 1))
        start_address = int(spec.source.endpoint.params.get("modbus_start_address", 0))
        quantity = max(1, len(spec.source.points))
        transaction_id = int(time.time_ns() & 0xFFFF)
        # MBAP(7) + PDU(function=3, start, quantity)
        request = struct.pack(">HHHBBHH", transaction_id, 0, 6, unit_id, 3, start_address, quantity)
        try:
            with socket.create_connection(
                (spec.source.endpoint.host, spec.source.endpoint.port),
                timeout=config.read_timeout_s,
            ) as client:
                client.sendall(request)
                header = client.recv(7)
                if len(header) < 7:
                    return PollingReadSample(ok=False, value_count=0, response_timestamp_s=None, error_code="short_header")
                _tid, _pid, _len, _uid = struct.unpack(">HHHB", header)
                pdu = client.recv(2 + quantity * 2)
                if len(pdu) < 2:
                    return PollingReadSample(ok=False, value_count=0, response_timestamp_s=None, error_code="short_pdu")
                func = pdu[0]
                if func & 0x80:
                    return PollingReadSample(ok=False, value_count=0, response_timestamp_s=None, error_code="modbus_exception")
                byte_count = pdu[1]
                values = byte_count // 2
                return PollingReadSample(ok=True, value_count=values, response_timestamp_s=time.time())
        except OSError:
            return PollingReadSample(ok=False, value_count=0, response_timestamp_s=None, error_code="transport_error")
