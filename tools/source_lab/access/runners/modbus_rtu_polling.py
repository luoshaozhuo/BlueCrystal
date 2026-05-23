"""Modbus RTU polling runner（串口帧读）。

注意：当前为 Python socket 轻量实现，未使用 libmodbus native 后端；
实现了 CRC16 校验和功能码 0x03 读写，不等价于完整 Modbus 协议栈。
"""

from __future__ import annotations

import socket
import struct
import time

from tools.source_lab.access.polling.model import CapacityScanConfig
from tools.source_lab.access.runners.generic_polling import GenericPollingCapacityRunner, PollingReadSample
from tools.source_lab.access.common.scheduling import RunnerEndpointPlan


def _crc16(data: bytes) -> int:
    crc = 0xFFFF
    for value in data:
        crc ^= value
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


class ModbusRtuPollingRunner(GenericPollingCapacityRunner):
    """基于串口 Modbus RTU 的 polling runner。"""

    name = "modbus_rtu_polling_runner"

    def read_once(
        self,
        spec: RunnerEndpointPlan,
        *,
        target_hz: float,
        config: CapacityScanConfig,
    ) -> PollingReadSample:
        del target_hz

        # 优先串口；缺失时回退到 TCP 网关模式，支持无串口实验室环境。
        serial_result = self._read_once_serial(spec, config)
        if serial_result is not None:
            return serial_result
        return self._read_once_tcp_gateway(spec, config)

    def _read_once_serial(
        self,
        spec: RunnerEndpointPlan,
        config: CapacityScanConfig,
    ) -> PollingReadSample | None:
        try:
            import serial  # type: ignore[import-untyped]
        except Exception:
            return None

        device = str(spec.source.endpoint.params.get("serial_port", ""))
        if not device:
            return None

        unit_id = int(spec.source.endpoint.params.get("modbus_unit_id", 1))
        start_address = int(spec.source.endpoint.params.get("modbus_start_address", 0))
        quantity = max(1, len(spec.source.points))
        pdu = struct.pack(">BBHH", unit_id, 3, start_address, quantity)
        crc = _crc16(pdu)
        frame = pdu + struct.pack("<H", crc)

        try:
            with serial.Serial(device, baudrate=int(spec.source.endpoint.params.get("baudrate", 9600)), timeout=config.read_timeout_s) as port:
                port.write(frame)
                response = port.read(5 + quantity * 2)
                if len(response) < 5:
                    return PollingReadSample(ok=False, value_count=0, response_timestamp_s=None, error_code="short_frame")
                if response[1] & 0x80:
                    return PollingReadSample(ok=False, value_count=0, response_timestamp_s=None, error_code="modbus_exception")
                value_count = response[2] // 2
                return PollingReadSample(ok=True, value_count=value_count, response_timestamp_s=time.time())
        except Exception:
            return PollingReadSample(ok=False, value_count=0, response_timestamp_s=None, error_code="transport_error")

    def _read_once_tcp_gateway(
        self,
        spec: RunnerEndpointPlan,
        config: CapacityScanConfig,
    ) -> PollingReadSample:
        unit_id = int(spec.source.endpoint.params.get("modbus_unit_id", 1))
        start_address = int(spec.source.endpoint.params.get("modbus_start_address", 0))
        quantity = max(1, len(spec.source.points))
        pdu = struct.pack(">BBHH", unit_id, 3, start_address, quantity)
        crc = _crc16(pdu)
        frame = pdu + struct.pack("<H", crc)
        try:
            with socket.create_connection(
                (spec.source.endpoint.host, spec.source.endpoint.port),
                timeout=config.read_timeout_s,
            ) as conn:
                conn.sendall(frame)
                conn.settimeout(config.read_timeout_s)
                response = conn.recv(5 + quantity * 2)
                if len(response) < 5:
                    return PollingReadSample(ok=False, value_count=0, response_timestamp_s=None, error_code="short_frame")
                if response[1] & 0x80:
                    return PollingReadSample(ok=False, value_count=0, response_timestamp_s=None, error_code="modbus_exception")
                value_count = response[2] // 2
                return PollingReadSample(ok=True, value_count=value_count, response_timestamp_s=time.time())
        except Exception:
            return PollingReadSample(ok=False, value_count=0, response_timestamp_s=None, error_code="transport_error")
