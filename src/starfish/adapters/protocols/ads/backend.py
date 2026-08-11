"""Starfish ADS/AMS TCP simulator backend。

实现 ADS client 按符号句柄或 IndexGroup/IndexOffset 同步读取所需的真实 AMS/TCP
帧链路。socket、client thread 与符号句柄都由 backend 持有，``stop`` 会关闭监听
及现存连接并等待线程退出。当前 Source 契约只授权读取，普通 ADS 写请求明确返回
service-not-supported，不把未声明写能力暴露给客户端。
"""

from __future__ import annotations

import socket
import struct
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from starfish.core.definitions import PointItemDefinition, ServerDefinition

_AMS_HEADER = struct.Struct("<6sH6sHHHIII")
_TCP_HEADER = struct.Struct("<HI")
_READ = 2
_WRITE = 3
_READ_STATE = 4
_READ_WRITE = 9
_ADD_DEVICE_NOTIFICATION = 6
_DELETE_DEVICE_NOTIFICATION = 7
_DEVICE_NOTIFICATION = 8
_STATE_REQUEST = 0x0004
_STATE_RESPONSE = 0x0005
_IGRP_SYM_HNDBYNAME = 0xF003
_IGRP_SYM_VALBYHND = 0xF005
_IGRP_SYM_RELEASEHND = 0xF006
_ADS_OK = 0
_ADS_DEVICE_SERVICE_NOT_SUPPORTED = 0x701
_ADS_DEVICE_SYMBOL_NOT_FOUND = 0x710
_ADS_DEVICE_INVALID_PARAMETER = 0x705
_MAX_FRAME_BYTES = 4 * 1024 * 1024
_TRANS_SERVER_CYCLE = 3
_TRANS_SERVER_ON_CHANGE = 4


@dataclass(eq=False)
class _ClientSession:
    """单 AMS/TCP client 的地址、发送锁与私有 handle 生命周期。"""

    sock: socket.socket
    target_net_id: bytes = b""
    target_port: int = 0
    handles: set[int] = field(default_factory=set)
    notification_handles: set[int] = field(default_factory=set)
    send_lock: threading.Lock = field(default_factory=threading.Lock)


@dataclass
class _Subscription:
    """由 Source view 约束的 ADS device-notification 订阅。"""

    handle: int
    point_id: int
    session: _ClientSession
    transmission_mode: int
    cycle_ms: int
    max_delay_ms: int
    last_sent_at: float = 0.0
    last_version: int = -1


class AdsOperationError(RuntimeError):
    """ADS definition、socket 生命周期或协议帧违反运行契约。"""


class AdsTcpBackend:
    """一个 ADS SERVER connection 对应的 AMS/TCP runtime。"""

    def __init__(self) -> None:
        """创建尚未绑定 socket 的 backend。"""
        self._definition: ServerDefinition | None = None
        self._points: dict[int, PointItemDefinition] = {}
        self._values: dict[int, Any] = {}
        self._value_versions: dict[int, int] = {}
        self._symbols: dict[str, int] = {}
        self._indexes: dict[tuple[int, int], int] = {}
        self._handles: dict[int, int] = {}
        self._next_handle = 1
        self._listener: socket.socket | None = None
        self._clients: set[_ClientSession] = set()
        self._threads: set[threading.Thread] = set()
        self._accept_thread: threading.Thread | None = None
        self._notification_thread: threading.Thread | None = None
        self._subscriptions: dict[int, _Subscription] = {}
        self._next_notification_handle = 1
        self._stop_event = threading.Event()
        self._lock = threading.RLock()
        self._started_at: datetime | None = None

    def load_points(self, definition: ServerDefinition) -> None:
        """校验并保存 ADS server 与 Source 点位定义。

        Args:
            definition: 从 comm/src views 映射的 core definition。

        Raises:
            AdsOperationError: 角色、AMS 地址、点地址或数据类型不合法。
        """
        if self._listener is not None:
            raise AdsOperationError("ADS runtime 已装配，不能重新加载 definition")
        if definition.protocol != "ADS" or definition.station_role != "SERVER":
            raise AdsOperationError(
                "ADS backend 只接受 protocol_role=SERVER 的 ADS definition"
            )
        _net_id_bytes(str(definition.connection_params.get("ams_net_id") or ""))
        points = {point.point_item_id: point for point in definition.point_items}
        symbols: dict[str, int] = {}
        indexes: dict[tuple[int, int], int] = {}
        for point in points.values():
            _encode_value(point, point.initial_value)
            symbol = str(point.metadata.get("symbol_name") or "")
            if symbol:
                if symbol in symbols:
                    raise AdsOperationError(f"重复 ADS symbol_name: {symbol}")
                symbols[symbol] = point.point_item_id
            if point.metadata.get("index_group") is not None:
                key = (
                    int(point.metadata["index_group"]),
                    int(point.metadata["index_offset"]),
                )
                if key in indexes:
                    raise AdsOperationError(f"重复 ADS index address: {key}")
                indexes[key] = point.point_item_id
        self._definition = definition
        self._points = points
        self._values = {
            point.point_item_id: point.initial_value for point in points.values()
        }
        self._value_versions = {point_id: 0 for point_id in points}
        self._symbols = symbols
        self._indexes = indexes

    def connect(self) -> None:
        """绑定 view 描述的 TCP 地址；重复调用安全。

        Raises:
            AdsOperationError: definition 未加载或 socket 绑定失败。
        """
        if self._listener is not None:
            return
        definition = self._require_definition()
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.settimeout(0.2)
        try:
            listener.bind((definition.bind_host, definition.bind_port))
            listener.listen()
        except OSError as exc:
            listener.close()
            raise AdsOperationError(
                f"绑定 ADS endpoint {definition.bind_host}:{definition.bind_port} 失败: {exc}"
            ) from exc
        self._listener = listener

    def start(self) -> None:
        """启动 AMS/TCP accept 与 notification loops；重复调用安全。

        Raises:
            AdsOperationError: definition 或 socket 尚不可用。
        """
        if self._accept_thread and self._accept_thread.is_alive():
            return
        self.connect()
        self._stop_event.clear()
        thread = threading.Thread(
            target=self._accept_loop,
            name=f"starfish-ads-{self._require_definition().connection_id}",
            daemon=True,
        )
        self._accept_thread = thread
        self._started_at = datetime.now(timezone.utc)
        thread.start()
        notification_thread = threading.Thread(
            target=self._notification_loop,
            name=f"starfish-ads-notification-{self._require_definition().connection_id}",
            daemon=True,
        )
        self._notification_thread = notification_thread
        notification_thread.start()

    def stop(self) -> None:
        """关闭 socket、清理 handles 并等待短生命周期 worker 退出。

        Raises:
            AdsOperationError: worker 未能在停止期限内退出。
        """
        self._stop_event.set()
        listener, self._listener = self._listener, None
        if listener is not None:
            listener.close()
        with self._lock:
            clients = tuple(session.sock for session in self._clients)
        for client in clients:
            try:
                client.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            client.close()
        if self._accept_thread is not None:
            self._accept_thread.join(timeout=2)
        if self._notification_thread is not None:
            self._notification_thread.join(timeout=2)
        for thread in tuple(self._threads):
            thread.join(timeout=2)
        alive = [thread.name for thread in self._threads if thread.is_alive()]
        if self._accept_thread is not None and self._accept_thread.is_alive():
            alive.append(self._accept_thread.name)
        if (
            self._notification_thread is not None
            and self._notification_thread.is_alive()
        ):
            alive.append(self._notification_thread.name)
        if alive:
            raise AdsOperationError(f"ADS shutdown incomplete，线程仍存活: {alive}")
        self._threads.clear()
        self._accept_thread = None
        self._notification_thread = None
        self._handles.clear()
        self._subscriptions.clear()

    def update_point(self, point: int | str, value: Any) -> dict[str, Any]:
        """更新进程内 Source 值，后续 read/notification 返回新值。

        Args:
            point: point item ID 或 ADS symbol。
            value: 与点 ``ads_data_type`` 兼容的新值。

        Returns:
            更新后的稳定点状态。

        Raises:
            AdsOperationError: 点不存在或值无法编码。
        """
        point_id = self._resolve_point(point)
        _encode_value(self._points[point_id], value)
        with self._lock:
            self._values[point_id] = value
            self._value_versions[point_id] += 1
        return self.point_state(point_id)

    def point_state(self, point: int | str) -> dict[str, Any]:
        """返回稳定点值快照，不暴露 socket 或 AMS 句柄。

        Args:
            point: point item ID 或 ADS symbol。

        Returns:
            点标识与当前值字典。

        Raises:
            AdsOperationError: 点不存在。
        """
        point_id = self._resolve_point(point)
        with self._lock:
            value = self._values[point_id]
        return {
            "point_item_id": point_id,
            "point_identifier": self._points[point_id].point_identifier,
            "value": value,
        }

    def health(self) -> dict[str, Any]:
        """返回 socket、client 与 Source 点位状态摘要。

        Returns:
            生命周期、连接数、订阅数与点数量字典。
        """
        running = bool(self._accept_thread and self._accept_thread.is_alive())
        return {
            "status": "started" if running else "stopped",
            "mode": "ams_tcp",
            "running": running,
            "point_count": len(self._points),
            "client_count": len(self._clients),
            "notification_count": len(self._subscriptions),
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "synthetic": False,
            "protocol": "ADS",
        }

    def _accept_loop(self) -> None:
        """接受客户端并为每条连接创建可回收 worker。"""
        while not self._stop_event.is_set():
            listener = self._listener
            if listener is None:
                return
            try:
                client, _ = listener.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            client.settimeout(0.2)
            session = _ClientSession(client)
            with self._lock:
                self._clients.add(session)
            thread = threading.Thread(
                target=self._client_loop, args=(session,), daemon=True
            )
            with self._lock:
                self._threads.add(thread)
            thread.start()

    def _client_loop(self, session: _ClientSession) -> None:
        """逐帧处理单客户端；断帧或 socket 错误只终止该连接。"""
        client = session.sock
        try:
            while not self._stop_event.is_set():
                try:
                    tcp_header = _recv_exact(client, _TCP_HEADER.size, self._stop_event)
                except TimeoutError:
                    continue
                if tcp_header is None:
                    return
                reserved, frame_length = _TCP_HEADER.unpack(tcp_header)
                if (
                    reserved != 0
                    or frame_length < _AMS_HEADER.size
                    or frame_length > _MAX_FRAME_BYTES
                ):
                    return
                frame = _recv_exact(client, frame_length, self._stop_event)
                if frame is None:
                    return
                response = self._response(session, frame)
                with session.send_lock:
                    client.sendall(response)
        except (OSError, AdsOperationError):
            return
        finally:
            with self._lock:
                self._clients.discard(session)
                for handle in session.handles:
                    self._handles.pop(handle, None)
                for handle in session.notification_handles:
                    self._subscriptions.pop(handle, None)
                self._threads.discard(threading.current_thread())
            client.close()

    def _response(self, session: _ClientSession, frame: bytes) -> bytes:
        """校验 AMS header、执行 Source read 并构造匹配 invoke ID 的响应。"""
        if len(frame) < _AMS_HEADER.size:
            raise AdsOperationError("AMS frame header 不完整")
        (
            target,
            target_port,
            source,
            source_port,
            command,
            _flags,
            length,
            _error,
            invoke,
        ) = _AMS_HEADER.unpack_from(frame)
        definition = self._require_definition()
        if target != _net_id_bytes(str(definition.connection_params["ams_net_id"])):
            raise AdsOperationError("AMS target Net ID 与 view 不一致")
        if target_port != int(definition.connection_params["ams_port"]):
            raise AdsOperationError("AMS target port 与 view 不一致")
        session.target_net_id = source
        session.target_port = source_port
        payload = frame[_AMS_HEADER.size :]
        if len(payload) != length:
            raise AdsOperationError("AMS payload length 不一致")
        response_payload = self._dispatch(session, command, payload)
        ams = (
            _AMS_HEADER.pack(
                source,
                source_port,
                target,
                target_port,
                command,
                _STATE_RESPONSE,
                len(response_payload),
                0,
                invoke,
            )
            + response_payload
        )
        return _TCP_HEADER.pack(0, len(ams)) + ams

    def _dispatch(
        self,
        session: _ClientSession,
        command: int,
        payload: bytes,
    ) -> bytes:
        """处理真实 client 打开的 ADS 同步读取命令集合。"""
        if command == _READ_WRITE:
            if len(payload) < 16:
                raise AdsOperationError("ADS READ_WRITE payload 不完整")
            group, offset, read_length, write_length = struct.unpack_from(
                "<IIII", payload
            )
            data = payload[16:]
            if len(data) != write_length:
                raise AdsOperationError("ADS READ_WRITE write_length 不一致")
            if group == _IGRP_SYM_HNDBYNAME:
                symbol = data.rstrip(b"\0").decode("utf-8")
                point_id = self._symbols.get(symbol)
                if point_id is None:
                    return struct.pack("<II", _ADS_DEVICE_SYMBOL_NOT_FOUND, 0)
                with self._lock:
                    handle = self._next_handle
                    self._next_handle += 1
                    self._handles[handle] = point_id
                    session.handles.add(handle)
                encoded = struct.pack("<I", handle)[:read_length]
                return struct.pack("<II", _ADS_OK, len(encoded)) + encoded
            return struct.pack("<II", _ADS_DEVICE_SERVICE_NOT_SUPPORTED, 0)
        if command == _READ:
            if len(payload) != 12:
                raise AdsOperationError("ADS READ payload 长度必须为 12")
            group, offset, read_length = struct.unpack("<III", payload)
            point_id = self._point_for_address(group, offset)
            if point_id is None:
                return struct.pack("<II", _ADS_DEVICE_SYMBOL_NOT_FOUND, 0)
            with self._lock:
                encoded = _encode_value(self._points[point_id], self._values[point_id])
            encoded = encoded[:read_length]
            return struct.pack("<II", _ADS_OK, len(encoded)) + encoded
        if command == _WRITE:
            if len(payload) < 12:
                raise AdsOperationError("ADS WRITE payload 不完整")
            group, offset, write_length = struct.unpack_from("<III", payload)
            data = payload[12:]
            if len(data) != write_length:
                raise AdsOperationError("ADS WRITE write_length 不一致")
            if group == _IGRP_SYM_RELEASEHND and len(data) == 4:
                handle = struct.unpack("<I", data)[0]
                with self._lock:
                    self._handles.pop(handle, None)
                    session.handles.discard(handle)
                return struct.pack("<I", _ADS_OK)
            return struct.pack("<I", _ADS_DEVICE_SERVICE_NOT_SUPPORTED)
        if command == _ADD_DEVICE_NOTIFICATION:
            return self._add_notification(session, payload)
        if command == _DELETE_DEVICE_NOTIFICATION:
            return self._delete_notification(session, payload)
        if command == _READ_STATE:
            # ADS state RUN=5，device state 0；便于标准 client 判定 server 可用。
            return struct.pack("<IHH", _ADS_OK, 5, 0)
        return struct.pack("<I", _ADS_DEVICE_SERVICE_NOT_SUPPORTED)

    def _add_notification(self, session: _ClientSession, payload: bytes) -> bytes:
        """按 view notification 契约注册真实 ADS subscription handle。"""
        if len(payload) != 40:
            raise AdsOperationError("ADS ADD_DEVICE_NOTIFICATION payload 长度必须为 40")
        group, offset, sample_length, transmission_mode, _max_delay, _cycle_time = (
            struct.unpack_from("<IIIIII", payload)
        )
        point_id = self._point_for_address(group, offset)
        if point_id is None:
            return struct.pack("<II", _ADS_DEVICE_SYMBOL_NOT_FOUND, 0)
        point = self._points[point_id]
        encoded = _encode_value(point, self._values[point_id])
        if sample_length != len(encoded):
            return struct.pack("<II", _ADS_DEVICE_INVALID_PARAMETER, 0)
        view_mode = str(point.metadata.get("notification_mode") or "").upper()
        expected_mode = {
            "CYCLIC": _TRANS_SERVER_CYCLE,
            "ON_CHANGE": _TRANS_SERVER_ON_CHANGE,
        }.get(view_mode)
        if expected_mode is None or transmission_mode != expected_mode:
            return struct.pack("<II", _ADS_DEVICE_INVALID_PARAMETER, 0)
        with self._lock:
            handle = self._next_notification_handle
            self._next_notification_handle += 1
            subscription = _Subscription(
                handle=handle,
                point_id=point_id,
                session=session,
                transmission_mode=transmission_mode,
                cycle_ms=max(int(point.metadata.get("cycle_time_ms") or 1), 1),
                max_delay_ms=max(int(point.metadata.get("max_delay_ms") or 0), 0),
            )
            self._subscriptions[handle] = subscription
            session.notification_handles.add(handle)
        return struct.pack("<II", _ADS_OK, handle)

    def _delete_notification(self, session: _ClientSession, payload: bytes) -> bytes:
        """取消当前 client 自己持有的 notification handle。"""
        if len(payload) != 4:
            raise AdsOperationError(
                "ADS DELETE_DEVICE_NOTIFICATION payload 长度必须为 4"
            )
        handle = struct.unpack("<I", payload)[0]
        with self._lock:
            if handle not in session.notification_handles:
                return struct.pack("<I", _ADS_DEVICE_INVALID_PARAMETER)
            session.notification_handles.remove(handle)
            self._subscriptions.pop(handle, None)
        return struct.pack("<I", _ADS_OK)

    def _notification_loop(self) -> None:
        """按 Source view 周期或变化语义发送 server-initiated AMS frames。"""
        while not self._stop_event.wait(0.005):
            now = time.monotonic()
            with self._lock:
                subscriptions = tuple(self._subscriptions.values())
            for subscription in subscriptions:
                with self._lock:
                    version = self._value_versions[subscription.point_id]
                due = now - subscription.last_sent_at >= subscription.cycle_ms / 1000
                if subscription.transmission_mode == _TRANS_SERVER_ON_CHANGE:
                    due = due and version != subscription.last_version
                if due:
                    self._send_notification(subscription, now, version)

    def _send_notification(
        self,
        subscription: _Subscription,
        now: float,
        version: int,
    ) -> None:
        """发送单样本 notification；socket 失败由 client loop 负责统一回收。"""
        session = subscription.session
        definition = self._require_definition()
        with self._lock:
            # delete 返回前必须等待正在发送的样本完成，之后不允许残留推送。
            if self._subscriptions.get(subscription.handle) is not subscription:
                return
            encoded = _encode_value(
                self._points[subscription.point_id],
                self._values[subscription.point_id],
            )
            filetime = int(time.time() * 10_000_000) + 116_444_736_000_000_000
            stamp = (
                struct.pack("<QI", filetime, 1)
                + struct.pack("<II", subscription.handle, len(encoded))
                + encoded
            )
            payload = struct.pack("<II", 4 + len(stamp), 1) + stamp
            ams = (
                _AMS_HEADER.pack(
                    session.target_net_id,
                    session.target_port,
                    _net_id_bytes(str(definition.connection_params["ams_net_id"])),
                    int(definition.connection_params["ams_port"]),
                    _DEVICE_NOTIFICATION,
                    _STATE_REQUEST,
                    len(payload),
                    0,
                    0,
                )
                + payload
            )
            try:
                with session.send_lock:
                    session.sock.sendall(_TCP_HEADER.pack(0, len(ams)) + ams)
            except OSError:
                return
            subscription.last_sent_at = now
            subscription.last_version = version

    def _point_for_address(self, group: int, offset: int) -> int | None:
        """解析句柄寻址或 view 声明的直接 INDEX 寻址。"""
        with self._lock:
            if group == _IGRP_SYM_VALBYHND:
                return self._handles.get(offset)
        return self._indexes.get((group, offset))

    def _resolve_point(self, point: int | str) -> int:
        """按 point ID 或唯一 symbol 定位 Source 点。"""
        if isinstance(point, int):
            point_id = point
        else:
            point_id = self._symbols.get(point, -1)
        if point_id not in self._points:
            raise AdsOperationError(f"ADS Point 不存在: {point}")
        return point_id

    def _require_definition(self) -> ServerDefinition:
        """返回已加载定义，否则稳定失败。"""
        if self._definition is None:
            raise AdsOperationError("ADS definition 尚未加载")
        return self._definition


def _recv_exact(
    sock: socket.socket,
    length: int,
    stop_event: threading.Event,
) -> bytes | None:
    """读取固定长度；超时允许调用方继续检查 stop，EOF 返回 None。"""
    chunks = bytearray()
    while len(chunks) < length and not stop_event.is_set():
        try:
            chunk = sock.recv(length - len(chunks))
        except TimeoutError:
            if not chunks:
                raise
            continue
        if not chunk:
            return None
        chunks.extend(chunk)
    return bytes(chunks) if len(chunks) == length else None


def _net_id_bytes(value: str) -> bytes:
    """严格解析六段 AMS Net ID。"""
    try:
        parts = tuple(int(part) for part in value.split("."))
    except ValueError as exc:
        raise AdsOperationError(f"AMS Net ID 非法: {value}") from exc
    if len(parts) != 6 or any(part < 0 or part > 255 for part in parts):
        raise AdsOperationError(f"AMS Net ID 非法: {value}")
    return bytes(parts)


def _encode_value(point: PointItemDefinition, value: Any) -> bytes:
    """按 view 的 ads_data_type 编码 little-endian PLC 值。"""
    data_type = point.type_id.strip().upper()
    formats = {
        "BOOL": "<?",
        "BYTE": "<B",
        "USINT": "<B",
        "SINT": "<b",
        "WORD": "<H",
        "UINT": "<H",
        "INT": "<h",
        "DWORD": "<I",
        "UDINT": "<I",
        "DINT": "<i",
        "LWORD": "<Q",
        "ULINT": "<Q",
        "LINT": "<q",
        "REAL": "<f",
        "LREAL": "<d",
    }
    fmt = formats.get(data_type)
    if fmt is None:
        raise AdsOperationError(f"不支持的 ADS data type: {data_type}")
    try:
        return struct.pack(fmt, value)
    except (struct.error, TypeError, ValueError) as exc:
        raise AdsOperationError(
            f"ADS Point {point.point_identifier} 的值不符合 {data_type}: {value!r}"
        ) from exc


__all__ = ["AdsOperationError", "AdsTcpBackend"]
