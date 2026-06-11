"""Starfish HTTP REST 协议真实 server facade。

本模块提供 HTTP REST 协议的真实 server 生命周期实现。
使用 Python 标准库 `http.server.ThreadingHTTPServer` 启动真实 HTTP 服务端，
支持 GET /points 读取当前点位值，供外部 HTTP 客户端连接和读取。

当前实现状态：
- 已实现: start() / stop() / health() / load_points() / read() /
  update_values() / capabilities()
- NOT_IMPLEMENTED: write() / subscribe() / report()
  （HTTP REST server 仅支持 GET 读取，暂时不支持写入和对端推送）

协议 server 特征：
- 零外部二进制依赖（纯 Python 标准库）。
- 可在单元测试中通过 localhost 动态端口稳定运行。
- 线程模式：daemon 线程运行 serve_forever，不阻塞调用方。

安全边界：
- 不得 import seahorse / whale.ingest / whale.shared.source。
- 不连接生产数据库。
- 所有数据标注 synthetic。
"""

from __future__ import annotations

import json
import socket
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from starfish.domain import StarfishServerPlan, UnsupportedOperation


class _PointsHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器 —— 仅处理 GET /points。

    其他路径返回 404。不记录访问日志以保持测试环境清洁。
    """

    # 类变量，由 HttpRestFacade 在 start 时注入
    facade_ref: HttpRestFacade | None = None

    def do_GET(self) -> None:  # noqa: N802
        """处理 GET 请求。

        仅响应 /points 路径，返回当前内存点位值的 JSON 数组。
        """
        if not self.path.startswith("/points"):
            self.send_response(404)
            self.end_headers()
            return

        facade = _PointsHandler.facade_ref
        values_dict: dict[str, Any] = {}
        if facade is not None:
            values_dict = facade.read()

        payload = {
            "values": [
                {"point": key, "value": value}
                for key, value in values_dict.items()
            ]
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        """抑制 HTTP 访问日志，保持测试输出清洁。"""
        del format, args


class HttpRestFacade:
    """HTTP REST 协议真实 server facade。

    启动 Python 标准库 HTTPServer 提供 /points GET 端点，
    支持内存值存储和实时读取。所有操作在调用线程中同步执行，
    网络 I/O 在独立 daemon 线程中处理。

    不负责：TLS/HTTPS、认证授权、POST/PUT/PATCH 写入端点。

    Attributes:
        _plan: 已加载的 StarfishServerPlan。
        _started: 是否已调用 start()。
        _values: 内存点位值存储 (point_id -> value)。
        _started_at: start() 调用时间。
        _server: ThreadingHTTPServer 实例。
        _thread: server 线程。
        _port: 期望监听端口（0 表示 OS 自动分配）。
        _actual_port: 实际监听端口（由 OS 分配后回填）。
    """

    def __init__(self, bind_host: str = "127.0.0.1", port: int = 0) -> None:
        self._plan: StarfishServerPlan | None = None
        self._started: bool = False
        self._values: dict[str, Any] = {}
        self._started_at: datetime | None = None
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._bind_host: str = bind_host
        self._port: int = port
        self._actual_port: int = 0

    # ── 生命周期 ──────────────────────────────────────────────────────────────

    def start(self) -> None:
        """启动 HTTP REST 真实 server。

        创建 ThreadingHTTPServer 并在 daemon 线程中运行 serve_forever。
        重复调用安全（幂等）。

        Raises:
            OSError: 端口已被占用。
        """
        if self._started:
            return

        _PointsHandler.facade_ref = self
        server = HTTPServer((self._bind_host, self._port), _PointsHandler)
        self._server = server
        self._actual_port = server.server_port

        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.2}, daemon=True)
        thread.start()
        self._thread = thread
        self._started = True
        self._started_at = datetime.now(timezone.utc)

    def stop(self) -> None:
        """停止 HTTP REST server。

        调用 server.shutdown() 并等待线程结束。
        不删除已加载的 plan 和 values，以便停止后仍可查询。
        重复调用安全（幂等）。
        """
        if not self._started:
            return

        if self._server is not None:
            try:
                self._server.shutdown()
                self._server.server_close()
            except Exception:
                pass
            self._server = None

        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

        self._started = False

    # ── 可观测性 ──────────────────────────────────────────────────────────────

    def health(self) -> dict[str, Any]:
        """返回当前 facade 的可观测健康状态。

        通过 TCP connect 探测 server 是否可达，
        并返回点位数量、capabilities 等元信息。

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
            "protocol": "HTTP_REST",
            "mode": "real",
            "port": port,
            "running": running,
        }

    # ── 数据操作 ──────────────────────────────────────────────────────────────

    def load_points(self, plan: StarfishServerPlan) -> None:
        """从 StarfishServerPlan 加载点位定义和初始值。

        Args:
            plan: 已加载并校验的 StarfishServerPlan。
        """
        self._plan = plan
        self._values = dict(plan.initial_values)

    def read(self, point_ids: list[str] | None = None) -> dict[str, Any]:
        """读取当前内存中的点位值。

        Args:
            point_ids: 要读取的点位 ID 列表，None 表示全部。

        Returns:
            point_id -> 当前值 的 dict。不存在的点位置为 None。
        """
        if point_ids is None:
            return dict(self._values)
        return {pid: self._values.get(pid) for pid in point_ids}

    def update_values(self, values: dict[str, Any]) -> None:
        """批量更新点位值到内存存储。

        更新后客户端通过 GET /points 可立即读取新值。

        Args:
            values: point_id -> 新值 的 dict。
        """
        self._values.update(values)

    def capabilities(self) -> list[str]:
        """返回当前已加载 plan 的能力声明列表。

        Returns:
            能力声明字符串列表，未加载时返回空列表。
        """
        if self._plan is None:
            return []
        return list(self._plan.capabilities)

    # ── NOT_IMPLEMENTED 操作 ──────────────────────────────────────────────────

    def write(self, point_id: str, value: Any) -> None:
        """写入单个点位值 —— 当前未实现。

        HTTP REST server 仅支持 GET /points 读取，不支持写入端点。

        Args:
            point_id: 目标点位 ID。
            value: 要写入的值。

        Raises:
            UnsupportedOperation: 写入操作尚未实现。
        """
        raise UnsupportedOperation(
            "write",
            "HttpRestFacade.write 尚未实现，HTTP REST server 当前仅支持 GET /points，"
            "待后续轮次实现 POST/PUT 写入端点",
        )

    def subscribe(self, point_ids: list[str]) -> None:
        """订阅点位数据变更通知 —— 当前未实现。

        HTTP REST server 不支持服务端推送（Server-Sent Events 待后续轮次）。

        Args:
            point_ids: 要订阅的点位 ID 列表。

        Raises:
            UnsupportedOperation: 订阅操作尚未实现。
        """
        raise UnsupportedOperation(
            "subscribe",
            "HttpRestFacade.subscribe 尚未实现，"
            "待后续轮次实现 SSE 或 WebSocket 推送",
        )

    def report(self) -> dict[str, Any]:
        """上报当前门面状态摘要 —— 当前未实现。

        Raises:
            UnsupportedOperation: report 操作尚未实现。
        """
        raise UnsupportedOperation(
            "report",
            "HttpRestFacade.report 尚未实现，"
            "待后续轮次实现结构化 telemetry report",
        )

    @property
    def protocol(self) -> str:
        """返回归一化协议名。"""
        return "HTTP_REST"

    @property
    def mode(self) -> str:
        """返回运行模式：real（真实 server）、stub（内存替身）或 unavailable（不可用）。"""
        return "real"


__all__ = ["HttpRestFacade"]
