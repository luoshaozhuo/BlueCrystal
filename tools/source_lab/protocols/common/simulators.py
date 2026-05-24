"""多协议 source simulator 实现集合。"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import socket
import struct
import threading

from tools.source_lab.contracts import SourceSimulator
from tools.source_lab.model import SimulatedSource


class _TcpThreadedSimulator(SourceSimulator):
    """基于 TCP 监听线程的协议 simulator 基类。"""

    def __init__(self, source: SimulatedSource, *, name: str) -> None:
        self._source = source
        self._name = name
        self._values: dict[str, str | int | float | bool] = {
            point.key: (point.initial_value if point.initial_value is not None else 0)
            for point in source.points
        }
        self._server_socket: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    @property
    def endpoint(self) -> str:
        return f"{self._source.connection.protocol}://{self._source.connection.host}:{self._source.connection.port}"

    @property
    def name(self) -> str:
        return self._name

    def start(self) -> SourceSimulator:
        if self._thread is not None:
            return self
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self._source.connection.host, self._source.connection.port))
        server.listen(64)
        server.settimeout(0.2)
        self._server_socket = server
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._serve_loop, daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        self._stop_event.set()
        if self._server_socket is not None:
            self._server_socket.close()
            self._server_socket = None
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def __enter__(self) -> SourceSimulator:
        return self.start()

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.stop()

    def writes(self, values_by_key: dict[str, str | int | float | bool]) -> None:
        self._values.update(values_by_key)

    def _serve_loop(self) -> None:
        assert self._server_socket is not None
        while not self._stop_event.is_set():
            try:
                client, _addr = self._server_socket.accept()
            except OSError:
                if self._stop_event.is_set():
                    return
                continue
            threading.Thread(target=self._handle_client, args=(client,), daemon=True).start()

    def _handle_client(self, client: socket.socket) -> None:
        with client:
            client.settimeout(0.5)
            while not self._stop_event.is_set():
                try:
                    request = client.recv(4096)
                except OSError:
                    return
                if not request:
                    return
                response = self._handle_request(request)
                if response:
                    try:
                        client.sendall(response)
                    except OSError:
                        return

    def _handle_request(self, request: bytes) -> bytes:
        raise NotImplementedError


class ModbusTcpSimulator(_TcpThreadedSimulator):
    """Modbus TCP simulator。"""

    def __init__(self, source: SimulatedSource) -> None:
        super().__init__(source, name="modbus_tcp_simulator")

    def _handle_request(self, request: bytes) -> bytes:
        if len(request) < 12:
            return b""
        tid, pid, _length, unit_id, function_code, start_addr, quantity = struct.unpack(
            ">HHHBBHH", request[:12]
        )
        if function_code == 6:
            # FC06: write single register
            reg_addr = start_addr
            reg_value = quantity  # In FC06, the 4th field is the value, not quantity
            self._values[str(reg_addr)] = reg_value
            # Echo response for FC06
            pdu = struct.pack(">BHH", function_code, reg_addr, reg_value)
            mbap = struct.pack(">HHHB", tid, pid, len(pdu) + 1, unit_id)
            return mbap + pdu
        if function_code != 3:
            return struct.pack(">HHHBBB", tid, pid, 3, unit_id, function_code | 0x80, 1)
        registers = []
        for offset in range(quantity):
            value = self._values.get(str(start_addr + offset), offset)
            if isinstance(value, bool):
                reg = 1 if value else 0
            elif isinstance(value, (int, float)):
                reg = int(value) & 0xFFFF
            else:
                reg = 0
            registers.append(reg)
        payload = b"".join(struct.pack(">H", reg) for reg in registers)
        pdu = struct.pack(">BB", function_code, len(payload)) + payload
        mbap = struct.pack(">HHHB", tid, pid, len(pdu) + 1, unit_id)
        return mbap + pdu


class Iec104Simulator(_TcpThreadedSimulator):
    """IEC104 simulator。"""

    def __init__(self, source: SimulatedSource) -> None:
        super().__init__(source, name="iec104_simulator")

    def _handle_request(self, request: bytes) -> bytes:
        if request.startswith(b"\x68\x04\x43\x00\x00\x00"):
            return b"\x68\x04\x83\x00\x00\x00"
        return b"\x68\x04\x07\x00\x00\x00"


class Iec61850MmsSimulator(_TcpThreadedSimulator):
    """IEC61850 MMS simulator。"""

    def __init__(self, source: SimulatedSource) -> None:
        super().__init__(source, name="iec61850_mms_simulator")

    def _handle_request(self, request: bytes) -> bytes:
        # 返回一个最小化确认 PDU，占位满足连接与读取链路。
        del request
        return b"\x30\x03\xa0\x01\x00"


class Iec61850ReportSimulator(_TcpThreadedSimulator):
    """IEC61850 report simulator。"""

    def __init__(self, source: SimulatedSource) -> None:
        super().__init__(source, name="iec61850_report_simulator")

    def _handle_request(self, request: bytes) -> bytes:
        del request
        return b"\x30\x03\xa0\x01\x00"


def _decode_remaining_length(data: bytes, start: int = 1) -> tuple[int, int]:
    multiplier = 1
    value = 0
    index = start
    while index < len(data):
        byte = data[index]
        value += (byte & 0x7F) * multiplier
        if (byte & 0x80) == 0:
            return value, index + 1
        multiplier *= 128
        index += 1
    return 0, start


def _mqtt_publish_packet(topic: str, payload: str) -> bytes:
    topic_bytes = topic.encode("utf-8")
    payload_bytes = payload.encode("utf-8")
    variable = len(topic_bytes).to_bytes(2, "big") + topic_bytes
    remaining = variable + payload_bytes
    # 固定头 + 单字节 Remaining Length（测试负载很小）。
    return b"\x30" + bytes([len(remaining)]) + remaining


class MqttSimulator(_TcpThreadedSimulator):
    """MQTT broker-lite simulator。"""

    def __init__(self, source: SimulatedSource) -> None:
        super().__init__(source, name="mqtt_simulator")

    def _handle_request(self, request: bytes) -> bytes:
        packet_type = request[0] >> 4
        if packet_type == 1:
            return b"\x20\x02\x00\x00"
        if packet_type == 8:
            remaining, index = _decode_remaining_length(request)
            if remaining <= 2:
                return b""
            packet_id = request[index : index + 2]
            topic_len = int.from_bytes(request[index + 2 : index + 4], "big")
            topic = request[index + 4 : index + 4 + topic_len].decode("utf-8", errors="ignore")
            first_key = next(iter(self._values.keys()), "value")
            payload = str(self._values.get(first_key, 1))
            return b"\x90\x03" + packet_id + b"\x00" + _mqtt_publish_packet(topic, payload)
        return b""


class HttpRestSimulator(SourceSimulator):
    """HTTP REST simulator。"""

    def __init__(self, source: SimulatedSource) -> None:
        self._source = source
        self._name = "http_rest_simulator"
        self._values: dict[str, str | int | float | bool] = {
            point.key: (point.initial_value if point.initial_value is not None else 0)
            for point in source.points
        }
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def endpoint(self) -> str:
        return f"http://{self._source.connection.host}:{self._source.connection.port}"

    @property
    def name(self) -> str:
        return self._name

    def start(self) -> SourceSimulator:
        if self._server is not None:
            return self

        simulator = self

        class _Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                if not self.path.startswith("/points"):
                    self.send_response(404)
                    self.end_headers()
                    return
                payload = {
                    "values": [
                        {"point": key, "value": value}
                        for key, value in simulator._values.items()
                    ]
                }
                body = json.dumps(payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args: object) -> None:  # noqa: A003
                del format, args

        server = ThreadingHTTPServer((self._source.connection.host, self._source.connection.port), _Handler)
        self._server = server
        self._thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.2}, daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def __enter__(self) -> SourceSimulator:
        return self.start()

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.stop()

    def writes(self, values_by_key: dict[str, str | int | float | bool]) -> None:
        self._values.update(values_by_key)


class ModbusRtuSimulator(_TcpThreadedSimulator):
    """Modbus RTU over TCP gateway-style simulator。"""

    def __init__(self, source: SimulatedSource) -> None:
        super().__init__(source, name="modbus_rtu_gateway_simulator")

    def _handle_request(self, request: bytes) -> bytes:
        # 首轮使用网关模式承载 RTU 语义，便于实验室无串口环境验证链路。
        if len(request) < 8:
            return b""
        unit_id = request[0]
        function_code = request[1]
        if function_code != 3:
            return bytes([unit_id, function_code | 0x80, 1])
        quantity = int.from_bytes(request[4:6], "big")
        byte_count = quantity * 2
        return bytes([unit_id, function_code, byte_count]) + b"\x00\x01" * quantity


class Iec101Simulator(_TcpThreadedSimulator):
    """IEC101 gateway-style simulator。"""

    def __init__(self, source: SimulatedSource) -> None:
        super().__init__(source, name="iec101_gateway_simulator")

    def _handle_request(self, request: bytes) -> bytes:
        # 最小确认帧，用于链路读写探测。
        del request
        return b"\x10\x00\x00\x16"


def build_simulator_for_protocol(protocol: str, source: SimulatedSource) -> SourceSimulator:
    """按协议构建 simulator 实例。"""

    if protocol == "modbus_tcp":
        return ModbusTcpSimulator(source)
    if protocol == "modbus_rtu":
        return ModbusRtuSimulator(source)
    if protocol == "iec101":
        return Iec101Simulator(source)
    if protocol == "iec104":
        return Iec104Simulator(source)
    if protocol == "iec61850_mms":
        return Iec61850MmsSimulator(source)
    if protocol == "iec61850_report":
        return Iec61850ReportSimulator(source)
    if protocol == "mqtt":
        return MqttSimulator(source)
    if protocol == "http_rest":
        return HttpRestSimulator(source)
    raise ValueError(f"source simulator not implemented for protocol: {protocol}")
