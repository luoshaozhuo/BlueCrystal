"""Starfish MQTT 轻量级协议 backend。

本模块提供 MQTT-like 协议的轻量级 TCP server 生命周期实现。
使用 Python 标准库 socket 启动真实 TCP server，采用 JSON 行协议
与客户端交互，内部管理 topic -> payload 映射和 subscribe 轮询队列。

能力边界明确声明：
- 已实现: start() / stop() / health() / load_points() / read() /
  update_values() / capabilities() / subscribe()
  （subscribe 返回 SubscriptionQueue 轮询队列，支持 Starfish 工具层语义）
- NOT_IMPLEMENTED: write() / report()
- 不得标记为完整 MQTT broker：未实现 MQTT v3.1.1 CONNECT/CONNACK/
  SUBSCRIBE/SUBACK/PUBLISH 完整握手，未实现 QoS 1/2、遗嘱消息、
  keep-alive、clean session 等 MQTT 规范特性。

协议 server 特征：
- 零外部二进制依赖（纯 Python 标准库）。
- 可在单元测试中通过 localhost 动态端口稳定运行。
- 线程模式：daemon 线程运行 accept 循环，每个客户端连接独立线程处理。
- TCP 线上协议：JSON 行（一行一个 JSON 对象，以 \\n 分隔），
  简单可调试，不绑定特定 MQTT 版本。

topic -> payload 内部模型：
- load_points 时将 point_id 映射为 topic "starfish/<point_id>"。
- update_values 时根据变更的点位通知订阅者。
- subscribe 返回 SubscriptionQueue，供调用方轮询获取变更通知。

安全边界：
- 不得 import seahorse / whale.ingest / whale.shared.source。
- 不连接生产数据库。
- 所有数据标注 synthetic。
"""

from __future__ import annotations

import json
import queue
import socket
import threading
from datetime import datetime, timezone
from typing import Any

from starfish.domain import StarfishServerMemberConfig, UnsupportedOperation


class SubscriptionQueue:
    """订阅轮询队列 —— 用于接收点位值变更通知。

    每个 subscribe 调用返回一个新的 SubscriptionQueue 实例。
    当 update_values 或 TCP publish 更新被订阅点位时，
    新值以 (point_id, new_value) 元组推入队列。

    调用方通过 get() 阻塞等待或 get_nowait() 非阻塞轮询。

    不负责：自动重连、QoS 保证、离线消息缓存。
    """

    def __init__(self) -> None:
        self._q: queue.Queue[tuple[str, Any]] = queue.Queue()

    def get(self, timeout: float | None = None) -> tuple[str, Any]:
        """获取下一个变更通知。

        Args:
            timeout: 超时秒数，None 表示无限等待。

        Returns:
            (point_id, new_value) 元组。

        Raises:
            queue.Empty: 超时后队列仍为空。
        """
        return self._q.get(timeout=timeout)

    def get_nowait(self) -> tuple[str, Any] | None:
        """非阻塞获取下一个变更通知。

        Returns:
            (point_id, new_value) 元组，队列为空时返回 None。
        """
        try:
            return self._q.get_nowait()
        except queue.Empty:
            return None

    def _put(self, point_id: str, value: Any) -> None:
        """内部方法：将变更通知推入队列。

        Args:
            point_id: 发生变更的点位 ID。
            value: 变更后的新值。
        """
        self._q.put((point_id, value))


class MqttServerBackend:
    """MQTT 轻量级协议 backend。

    启动 TCP socket server，监听指定端口，提供基于 JSON 行协议的
    轻量级 MQTT-like 端点。内部管理 topic -> payload 映射和
    subscribe 轮询队列。

    线上协议（JSON 行，每行一个完整 JSON 对象，以 \\n 结尾）：
        客户端 -> 服务端:
            {"action": "read", "point_ids": ["p1", "p2"]}
            {"action": "read_all"}
            {"action": "publish", "point_id": "p1", "value": 42}
        服务端 -> 客户端:
            {"values": {"p1": 42, "p2": 100}}
            {"error": "unsupported action: ..."}

    不负责：完整 MQTT v3.1.1/v5.0 协议握手、QoS 1/2、
    遗嘱消息、keep-alive、clean session、TLS 加密。

    Attributes:
        _plan: 已加载的 StarfishServerMemberConfig。
        _started: 是否已调用 start()。
        _values: 内存点位值存储 (point_id -> value)。
        _started_at: start() 调用时间。
        _subscriptions: topic (point_id) -> 订阅队列列表。
        _lock: 线程安全锁（_values 和 _subscriptions 读写保护）。
    """

    # 线上协议支持的 action 集合
    _SUPPORTED_ACTIONS: frozenset[str] = frozenset({"read", "read_all", "publish"})

    def __init__(self, bind_host: str = "127.0.0.1", port: int = 0) -> None:
        self._plan: StarfishServerMemberConfig | None = None
        self._started: bool = False
        self._values: dict[str, Any] = {}
        self._started_at: datetime | None = None
        self._bind_host: str = bind_host
        self._port: int = port
        self._actual_port: int = 0

        # 订阅管理：point_id -> list[SubscriptionQueue]
        self._subscriptions: dict[str, list[SubscriptionQueue]] = {}

        # socket / 线程
        self._server_socket: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        # 线程安全锁（_values 和 _subscriptions 读写保护）
        self._lock = threading.Lock()

    # ── 生命周期 ──────────────────────────────────────────────────────────────

    def connect(self) -> None:
        """完成 DriverPort 预连接；当前 backend 保持 start() 负责实际启动。"""
        return None

    def start(self) -> None:
        """启动 MQTT 轻量级 TCP server。

        绑定 socket 到 bind_host:port，在 daemon 线程中运行 accept 循环。
        每个客户端连接在独立 daemon 线程中处理。

        重复调用安全（幂等）。

        Raises:
            OSError: 端口已被占用。
        """
        if self._started:
            return

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self._bind_host, self._port))
        server.listen(64)
        server.settimeout(0.5)  # accept 超时以响应 stop_event

        self._server_socket = server
        self._actual_port = server.getsockname()[1]
        self._stop_event.clear()

        thread = threading.Thread(target=self._serve_loop, daemon=True)
        thread.start()
        self._thread = thread
        self._started = True
        self._started_at = datetime.now(timezone.utc)

    def stop(self) -> None:
        """停止 MQTT 轻量级 TCP server。

        设置停止信号，关闭监听 socket，等待 accept 线程结束。
        不删除已加载的 plan、values 和 subscriptions，
        以便停止后仍可查询。
        重复调用安全（幂等）。
        """
        if not self._started:
            return

        self._stop_event.set()
        if self._server_socket is not None:
            try:
                self._server_socket.close()
            except OSError:
                pass
            self._server_socket = None

        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

        self._started = False

    # ── 可观测性 ──────────────────────────────────────────────────────────────

    def health(self) -> dict[str, Any]:
        """返回当前 backend 的可观测健康状态。

        通过 TCP connect 探测 server socket 是否可连接。

        Returns:
            包含 health 信息的 dict。
        """
        port = self._actual_port or self._port
        running = False
        if self._started and port > 0:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1.0)
                try:
                    sock.connect((self._bind_host, port))
                    running = True
                except OSError:
                    pass
                finally:
                    sock.close()
            except Exception:
                pass

        return {
            "status": "started" if self._started else "stopped",
            "plan_loaded": self._plan is not None,
            "point_count": len(self._plan.points) if self._plan else 0,
            "endpoint_count": len(self._plan.endpoints) if self._plan else 0,
            "capabilities": list(self._plan.capabilities) if self._plan else [],
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "synthetic": self._plan.synthetic if self._plan else True,
            "protocol": "MQTT",
            "mode": "mqtt-lightweight",
            "port": port,
            "running": running,
            "subscription_count": sum(
                len(qs) for qs in self._subscriptions.values()
            ),
        }

    # ── 数据操作 ──────────────────────────────────────────────────────────────

    def load_points(self, plan: StarfishServerMemberConfig) -> None:
        """从 StarfishServerMemberConfig 加载点位定义和初始值。

        同时清空已有订阅队列（重新加载时旧订阅失效）。

        Args:
            plan: 已加载并校验的 StarfishServerMemberConfig。
        """
        self._plan = plan
        with self._lock:
            self._values = dict(plan.initial_values)
            # 重新加载时清空旧订阅
            self._subscriptions.clear()

    def read(self, point_ids: list[str] | None = None) -> dict[str, Any]:
        """读取当前内存中的点位值。

        线程安全：使用内部锁保护 _values dict。

        Args:
            point_ids: 要读取的点位 ID 列表，None 表示全部。

        Returns:
            point_id -> 当前值 的 dict。不存在的点位置为 None。
        """
        with self._lock:
            if point_ids is None:
                return dict(self._values)
            return {pid: self._values.get(pid) for pid in point_ids}

    def update_values(self, values: dict[str, Any]) -> None:
        """批量更新点位值到内存存储。

        更新后通知所有订阅了对应 point_id 的订阅队列。
        线程安全。

        Args:
            values: point_id -> 新值 的 dict。
        """
        with self._lock:
            self._values.update(values)
            # 通知订阅者
            for point_id, new_value in values.items():
                subs = self._subscriptions.get(point_id, [])
                for sub_q in subs:
                    sub_q._put(point_id, new_value)

    def capabilities(self) -> list[str]:
        """返回当前已加载 plan 的能力声明列表。

        Returns:
            能力声明字符串列表，未加载时返回空列表。
        """
        if self._plan is None:
            return []
        return list(self._plan.capabilities)

    # ── subscribe（已实现）────────────────────────────────────────────────────

    def subscribe(self, point_ids: list[str]) -> SubscriptionQueue:
        """订阅点位数据变更通知 —— 返回轮询队列。

        为每个 point_id 注册订阅。当 update_values() 或 TCP publish
        更新匹配点位时，新值推入返回的 SubscriptionQueue。

        本方法实现了 Starfish 工具层 subscribe 语义，
        不同于其他 backend 的 NOT_IMPLEMENTED。

        Args:
            point_ids: 要订阅的点位 ID 列表。

        Returns:
            SubscriptionQueue 实例，可通过 get()/get_nowait() 轮询变更。
        """
        sub_q = SubscriptionQueue()
        with self._lock:
            for pid in point_ids:
                if pid not in self._subscriptions:
                    self._subscriptions[pid] = []
                self._subscriptions[pid].append(sub_q)
        return sub_q

    # ── NOT_IMPLEMENTED 操作 ──────────────────────────────────────────────────

    def write(self, point_id: str, value: Any) -> None:
        """写入单个点位值 —— 当前未实现。

        MQTT 轻量级 backend 暂不支持单点写入 API。
        可通过 update_values 批量更新。

        Args:
            point_id: 目标点位 ID。
            value: 要写入的值。

        Raises:
            UnsupportedOperation: 写入操作尚未实现。
        """
        raise UnsupportedOperation(
            "write",
            "MqttServerBackend.write 尚未实现，请使用 update_values 批量更新点位值",
        )

    def report(self) -> dict[str, Any]:
        """上报当前门面状态摘要 —— 当前未实现。

        Raises:
            UnsupportedOperation: report 操作尚未实现。
        """
        raise UnsupportedOperation(
            "report",
            "MqttServerBackend.report 尚未实现，"
            "待后续轮次实现结构化 telemetry report",
        )

    # ── 协议属性 ──────────────────────────────────────────────────────────────

    @property
    def protocol(self) -> str:
        """返回归一化协议名。"""
        return "MQTT"

    @property
    def mode(self) -> str:
        """返回运行模式：mqtt-lightweight（轻量级 MQTT-like，非完整 MQTT broker）。"""
        return "mqtt-lightweight"

    # ── TCP server 内部实现 ───────────────────────────────────────────────────

    def _serve_loop(self) -> None:
        """主 accept 循环。

        在 daemon 线程中运行，等待客户端连接。
        每个连接在独立 daemon 线程中处理。
        """
        assert self._server_socket is not None
        while not self._stop_event.is_set():
            try:
                client, _addr = self._server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                if self._stop_event.is_set():
                    return
                continue
            threading.Thread(
                target=self._handle_client, args=(client,), daemon=True,
            ).start()

    def _handle_client(self, client: socket.socket) -> None:
        """处理单个 TCP 客户端连接。

        循环接收数据，按行解析 JSON 消息，分发到对应 action 处理器。

        Args:
            client: 已接受的客户端 socket。
        """
        buf = b""
        with client:
            client.settimeout(0.5)
            while not self._stop_event.is_set():
                try:
                    data = client.recv(4096)
                except socket.timeout:
                    continue
                except OSError:
                    return
                if not data:
                    return

                buf += data
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    try:
                        response = self._handle_line(line)
                    except Exception:
                        response = json.dumps({"error": "internal error"}).encode("utf-8") + b"\n"
                    if response:
                        try:
                            client.sendall(response)
                        except OSError:
                            return

    def _handle_line(self, line: bytes) -> bytes:
        """解析并处理一行 JSON 消息。

        支持的 action：
            read:      读取指定点位值
            read_all:  读取全部点位值
            publish:   发布（更新）单个点位值并通知订阅者

        Args:
            line: 一行 JSON 消息的字节串（不含换行符）。

        Returns:
            响应 JSON 行（含换行符），或空 bytes 表示不响应。
        """
        line_str = line.decode("utf-8").strip()
        if not line_str:
            return b""

        try:
            msg = json.loads(line_str)
        except json.JSONDecodeError:
            return json.dumps({"error": "invalid JSON"}).encode("utf-8") + b"\n"

        if not isinstance(msg, dict):
            return json.dumps({"error": "message must be a JSON object"}).encode("utf-8") + b"\n"

        action = msg.get("action", "")
        if action not in self._SUPPORTED_ACTIONS:
            return (
                json.dumps({"error": f"unsupported action: {action}"}).encode("utf-8")
                + b"\n"
            )

        if action == "read":
            return self._handle_read_action(msg)
        elif action == "read_all":
            return self._handle_read_all_action()
        elif action == "publish":
            return self._handle_publish_action(msg)

        return b""

    def _handle_read_action(self, msg: dict[str, Any]) -> bytes:
        """处理 read action：返回指定点位值。

        Args:
            msg: 解析后的 JSON 消息 dict，应含 "point_ids" 列表字段。

        Returns:
            JSON 行响应。
        """
        point_ids = msg.get("point_ids", [])
        if not isinstance(point_ids, list):
            return json.dumps({"error": "point_ids must be a list"}).encode("utf-8") + b"\n"

        values = self.read(point_ids)
        return json.dumps({"values": values}, ensure_ascii=False).encode("utf-8") + b"\n"

    def _handle_read_all_action(self) -> bytes:
        """处理 read_all action：返回全部点位值。

        Returns:
            JSON 行响应。
        """
        values = self.read()
        return json.dumps({"values": values}, ensure_ascii=False).encode("utf-8") + b"\n"

    def _handle_publish_action(self, msg: dict[str, Any]) -> bytes:
        """处理 publish action：更新单个点位值并通知订阅者。

        等同于 update_values({point_id: value})，但通过 TCP 线上协议触发。

        Args:
            msg: 解析后的 JSON 消息 dict，应含 "point_id" 和 "value" 字段。

        Returns:
            JSON 行响应。
        """
        point_id = msg.get("point_id")
        value = msg.get("value")
        if point_id is None:
            return json.dumps({"error": "missing point_id"}).encode("utf-8") + b"\n"

        self.update_values({str(point_id): value})
        return json.dumps({"published": True, "point_id": point_id}).encode("utf-8") + b"\n"


__all__ = ["MqttServerBackend", "SubscriptionQueue"]
