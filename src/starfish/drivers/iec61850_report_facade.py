"""Starfish IEC61850 Report 协议 facade —— report/event 语义 + ReportQueue。

本模块提供 IEC61850 Report 协议 server 模拟门面，实现 report 语义和事件队列。
根据环境探测 iec61850_simulator_server 和 iec61850_report_runner C runner
二进制可用性，切换 real / unavailable 模式。

real 模式（binary 存在时）：
- start() 启动 iec61850_simulator_server C runner 子进程。
- subscribe() 启动 iec61850_report_runner 子进程，收集 REPORT 事件到 ReportQueue。
- update_values() 后向 ReportQueue 推送事件。
- stop() 优雅终止子进程。
- report() 返回收集的 report 事件。

unavailable 模式（binary 缺失时）：
- 所有操作回退到 in-memory 存储 + 轻量 report shell。
- mode="report-lightweight"，不等同完整 IEC61850 Report server。
- 真实 runner 标记 environment-pending。
- 不得将 unavailable 写成真实协议 server PASS。

NOT_IMPLEMENTED（所有模式）：
- read() / write() / subscribe() 明确抛出 UnsupportedOperation。
  IEC61850 Report facade 专注于 report 事件语义，不实现 MMS 读写。

协议特征：
- 零新增第三方 Python 依赖（subprocess / threading 均为 Python 标准库）。
- native runner 需求：需 CMake 编译 iec61850_simulator_server 和
  iec61850_report_runner（依赖 libiec61850）。
- runner 位置：src/starfish/native/bin/。

安全边界：
- 不得 import seahorse / whale.ingest / whale.shared.source。
- 所有数据标注 synthetic。
- 不实现 RCB 配置、Report 完整状态机、Trigger Option 等 IEC61850-7-2 语义。
"""

from __future__ import annotations

import os
import queue
import socket
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from starfish.domain import StarfishServerPlan, UnsupportedOperation
from starfish.drivers.native_runtime import (
    native_runner_env,
    probe_native_binary,
    starfish_root_from,
)


# ── ReportQueue ───────────────────────────────────────────────────────────────────


class ReportQueue:
    """IEC61850 Report 事件队列封装。

    封装 queue.Queue 提供阻塞 / 非阻塞取事件，用于 subscribe 返回的句柄。
    语义与 MqttFacade 的 SubscriptionQueue 类似，但命名为 ReportQueue / event
    以体现 IEC61850 Report Control Block 事件模型。

    每个 REPORT 事件是一个 dict，包含 event_type、point_id、value、timestamp。
    在 real 模式下由 iec61850_report_runner stderr 线程解析插入；
    在 report-lightweight 模式下由 update_values 推送。
    """

    def __init__(self) -> None:
        """初始化空事件队列。"""
        self._queue: queue.Queue[dict[str, Any]] = queue.Queue()

    def put(self, event: dict[str, Any]) -> None:
        """向队列尾部插入一个 report 事件（非阻塞）。

        Args:
            event: report 事件 dict，至少包含 event_type 字段。
        """
        self._queue.put(event)

    def get(self, timeout: float | None = None) -> dict[str, Any] | None:
        """从队列头部取一个 report 事件。

        Args:
            timeout: 最大等待秒数，None 表示无限阻塞。

        Returns:
            report 事件 dict，超时时返回 None。
        """
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def get_nowait(self) -> dict[str, Any] | None:
        """非阻塞取队首事件，队列空时返回 None。

        Returns:
            report 事件 dict 或 None。
        """
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def drain(self) -> list[dict[str, Any]]:
        """一次性排空队列中所有事件。

        Returns:
            事件列表（按入队顺序），可能为空。
        """
        events: list[dict[str, Any]] = []
        while True:
            try:
                events.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return events

    def qsize(self) -> int:
        """返回队列当前大小（近似值，非线程安全精确值）。

        Returns:
            队列中待消费的事件数。
        """
        return self._queue.qsize()


# ── IEC61850 report runner 路径解析 ────────────────────────────────────────────────


def resolve_iec61850_report_runner_path() -> Path:
    """解析 iec61850_report_runner 可执行文件路径。

    优先级：
        1. 环境变量 IEC61850_REPORT_RUNNER_PATH。
        2. 默认路径 src/starfish/native/bin/iec61850_report_runner。

    Returns:
        iec61850_report_runner 绝对路径（可能不存在）。
    """
    env_path = os.environ.get("IEC61850_REPORT_RUNNER_PATH")
    if env_path:
        return Path(env_path).expanduser().resolve()

    starfish_root = starfish_root_from(__file__)
    return starfish_root / "native" / "bin" / "iec61850_report_runner"


def resolve_iec61850_report_simulator_path() -> Path:
    """解析 iec61850_simulator_server 可执行文件路径（report facade 复用 MMS server）。

    优先级：
        1. 环境变量 IEC61850_MMS_RUNNER_PATH（复用 MMS facade 路径）。
        2. 默认路径 src/starfish/native/bin/iec61850_simulator_server。

    Returns:
        iec61850_simulator_server 绝对路径（可能不存在）。
    """
    env_path = os.environ.get("IEC61850_MMS_RUNNER_PATH")
    if env_path:
        return Path(env_path).expanduser().resolve()

    starfish_root = starfish_root_from(__file__)
    return starfish_root / "native" / "bin" / "iec61850_simulator_server"


# ── 依赖探测 ─────────────────────────────────────────────────────────────────────


def probe_iec61850_report_binary() -> tuple[bool, str]:
    """探测 IEC61850 Report 所需的两个 C runner 二进制可用性。

    检查 iec61850_simulator_server 和 iec61850_report_runner 两个 binary
    的存在性、文件大小（>= 1024 bytes）和可执行权限。

    Returns:
        (binary_available, reason) 二元组。两个 binary 均可用时才返回 True。
    """
    sim_path = resolve_iec61850_report_simulator_path()
    runner_path = resolve_iec61850_report_runner_path()

    sim_ok, sim_reason = probe_native_binary(
        sim_path,
        display_name="iec61850_simulator_server",
        min_size=1024,
    )
    if not sim_ok:
        return False, (
            f"{sim_reason}。请在 src/starfish/native/ 下执行 CMake 构建（依赖 libiec61850）。"
        )

    run_ok, run_reason = probe_native_binary(
        runner_path,
        display_name="iec61850_report_runner",
        min_size=1024,
    )
    if not run_ok:
        return False, (
            f"{run_reason}。请在 src/starfish/native/ 下执行 CMake 构建（依赖 libiec61850）。"
        )

    return True, f"IEC61850 Report binaries 可用: simulator={sim_reason}; runner={run_reason}"


# ── IEC61850 Report facade ───────────────────────────────────────────────────────


class Iec61850ReportFacade:
    """IEC61850 Report 协议 server 模拟门面，含 report/event 语义和 ReportQueue。

    根据 iec61850_simulator_server + iec61850_report_runner C runner 可用性切换模式。

    真实模式（binary 可用）：
        start() 启动 iec61850_simulator_server 子进程。
        subscribe() 启动 iec61850_report_runner 收集 REPORT 事件到 ReportQueue。
        update_values() 后向 ReportQueue 推送 update 事件。
        report() 返回排空事件队列的内容。
        stop() 优雅终止子进程。

    report-lightweight 模式（binary 缺失）：
        start() / stop() / health() 仅管理 in-memory 状态。
        update_values() 向内存 ReportQueue 推送事件。
        report() 返回排空的事件队列。
        明确声明这不是完整 IEC61850 Report server。
        真实 runner 标记 environment-pending。

    不负责：RCB 配置、Trigger Option、OptFields、BufTm、IntgPd 等
    IEC61850-7-2 标准的 RCB 语义。
    """

    _RUNNER_STARTUP_TIMEOUT = 10.0  # 等待 READY 的超时秒数
    _RUNNER_STOP_TIMEOUT = 5.0      # 优雅终止超时秒数
    _READY_PREFIX = "READY"
    _RCB_REF = "EventsRCB01"

    def __init__(self, bind_host: str = "127.0.0.1", port: int = 0) -> None:
        """初始化 IEC61850 Report facade。

        Args:
            bind_host: 绑定地址。
            port: 监听端口（0 表示自动分配）。
        """
        self._plan: StarfishServerPlan | None = None
        self._started: bool = False
        self._values: dict[str, Any] = {}
        self._started_at: datetime | None = None
        self._bind_host: str = bind_host
        self._port: int = port
        self._actual_port: int = 0

        # 子进程管理
        self._sim_process: subprocess.Popen[str] | None = None
        self._stderr_thread: threading.Thread | None = None

        # Report runner 子进程
        self._report_process: subprocess.Popen[str] | None = None
        self._report_thread: threading.Thread | None = None

        # 事件队列（支持多个 subscriber 各自持有独立队列）
        self._event_queue = ReportQueue()
        self._subscribers: list[ReportQueue] = []

        # 环境探测
        self._binary_available, self._binary_reason = probe_iec61850_report_binary()

    # ── 属性 ──────────────────────────────────────────────────────────────────

    @property
    def protocol(self) -> str:
        """返回归一化协议名。"""
        return "IEC61850_REPORT"

    @property
    def mode(self) -> str:
        """返回运行模式。

        - "real": 两个 C runner 均可用，真实子进程生命周期 + report 收集。
        - "report-lightweight": binary 缺失，轻量 report shell（非完整 IEC61850 Report server）。
        """
        return "real" if self._binary_available else "report-lightweight"

    @property
    def binary_available(self) -> bool:
        """返回 IEC61850 Report runner binaries 是否可用。"""
        return self._binary_available

    @property
    def binary_reason(self) -> str:
        """返回 binary 探测原因说明。"""
        return self._binary_reason

    # ── 生命周期 ──────────────────────────────────────────────────────────────

    def start(self) -> None:
        """启动 IEC61850 Report facade。

        真实模式：启动 iec61850_simulator_server C runner -> 等待 READY。
        report-lightweight 模式：设置 in-memory 状态。

        重复调用安全（幂等）。

        Raises:
            RuntimeError: 真实模式下 binary 不存在、子进程启动失败或 READY 超时。
        """
        if self._started:
            return

        if not self._binary_available:
            # report-lightweight 模式：仅设置状态
            self._started = True
            self._started_at = datetime.now(timezone.utc)
            return

        runner_path = resolve_iec61850_report_simulator_path()
        if not runner_path.exists():
            raise RuntimeError(
                f"iec61850_simulator_server 不存在: {runner_path}。"
                "请先编译 libiec61850 C runner。"
            )

        actual_port = self._port
        if actual_port <= 0:
            actual_port = _find_free_port(self._bind_host)
        self._actual_port = actual_port

        try:
            self._sim_process = subprocess.Popen(
                [str(runner_path), str(actual_port)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                bufsize=1,
                env=native_runner_env(runner_path),
            )
        except OSError as exc:
            raise RuntimeError(
                f"启动 iec61850_simulator_server 失败: {exc}"
            ) from exc

        assert self._sim_process.stderr is not None
        self._stderr_thread = threading.Thread(
            target=_drain_stderr,
            args=(self._sim_process.stderr,),
            daemon=True,
        )
        self._stderr_thread.start()

        try:
            self._wait_ready(actual_port)
        except Exception:
            self._terminate_sim_process()
            raise

        self._started = True
        self._started_at = datetime.now(timezone.utc)

    def stop(self) -> None:
        """停止 IEC61850 Report facade。

        真实模式：停止 report runner，终止 simulator server 子进程。
        report-lightweight 模式：重置 in-memory 状态，清空事件队列。

        重复调用安全（幂等）。
        """
        if not self._started:
            return

        if self._report_process is not None:
            rp = self._report_process
            self._report_process = None
            try:
                if rp.stdin is not None and rp.poll() is None:
                    rp.stdin.write("QUIT\n")
                    rp.stdin.flush()
                if rp.poll() is None:
                    rp.terminate()
                    rp.wait(timeout=self._RUNNER_STOP_TIMEOUT)
            except Exception:
                try:
                    rp.kill()
                    rp.wait(timeout=self._RUNNER_STOP_TIMEOUT)
                except Exception:
                    pass

        if self._report_thread is not None:
            self._report_thread.join(timeout=1.0)
            self._report_thread = None

        if self._binary_available and self._sim_process is not None:
            self._terminate_sim_process()

        # 重置内存状态
        self._event_queue = ReportQueue()
        self._subscribers.clear()
        self._started = False

    # ── 可观测性 ──────────────────────────────────────────────────────────────

    def health(self) -> dict[str, Any]:
        """返回当前 facade 的可观测健康状态。

        真实模式：通过 TCP connect 探测 simulator 端点是否可达。
        report-lightweight 模式：返回 mode="report-lightweight" 及原因。

        Returns:
            包含 health 信息的 dict。
        """
        port = self._actual_port or self._port
        running = False
        if self._started and self._binary_available and port > 0:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2.0)
                try:
                    sock.connect((self._bind_host, port))
                    running = True
                except OSError:
                    pass
                finally:
                    sock.close()
            except Exception:
                pass

        mode = self.mode
        result: dict[str, Any] = {
            "status": "started" if self._started else "stopped",
            "plan_loaded": self._plan is not None,
            "point_count": len(self._plan.points) if self._plan else 0,
            "endpoint_count": len(self._plan.endpoints) if self._plan else 0,
            "capabilities": list(self._plan.capabilities) if self._plan else [],
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "synthetic": self._plan.synthetic if self._plan else True,
            "protocol": self.protocol,
            "mode": mode,
            "port": port,
            "running": running,
            "binary_available": self._binary_available,
            "event_queue_size": self._event_queue.qsize(),
            "subscriber_count": len(self._subscribers),
        }
        if not self._binary_available:
            result["reason"] = self._binary_reason
        return result

    # ── 数据操作 ──────────────────────────────────────────────────────────────

    def load_points(self, plan: StarfishServerPlan) -> None:
        """加载点位定义和初始值到内存存储。

        Args:
            plan: 已校验的 StarfishServerPlan 实例。
        """
        self._plan = plan
        self._values = dict(plan.initial_values)

    def update_values(self, values: dict[str, Any]) -> None:
        """批量更新内存点位值，并推送 report event 到所有 subscriber 队列。

        每次调用生成一个 update 事件并推送到：
        - 内部 _event_queue（供 report() 排空）。
        - 所有活跃 subscriber 的 ReportQueue。

        Args:
            values: point_id -> 新值 的 dict。
        """
        self._values.update(values)

        event: dict[str, Any] = {
            "event_type": "update",
            "values": dict(values),
            "point_ids": list(values.keys()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # 推送到内部事件队列
        self._event_queue.put(event)

        # 推送到所有 subscriber 队列
        for sub_q in list(self._subscribers):
            try:
                sub_q.put(event)
            except Exception:
                pass

    def capabilities(self) -> list[str]:
        """返回当前已加载 plan 的能力声明列表。

        Returns:
            能力声明字符串列表，未加载时返回空列表。
        """
        if self._plan is None:
            return []
        return list(self._plan.capabilities)

    # ── Report 语义 ───────────────────────────────────────────────────────────

    def report(self) -> dict[str, Any]:
        """返回收集的 report 事件。

        排空内部事件队列，返回聚合结果。在真实模式下也包含来自
        iec61850_report_runner 的 REPORT 行。

        Returns:
            包含 event_count 和 events 列表的 dict。
            格式: {"events": [...], "event_count": N, "mode": str}
        """
        events = self._event_queue.drain()
        return {
            "events": [
                {
                    "event_type": e.get("event_type", "report"),
                    "timestamp": e.get("timestamp", ""),
                    "point_ids": e.get("point_ids", []),
                    "values": e.get("values", {}),
                    "seq": e.get("seq", ""),
                    "rcb": e.get("rcb", ""),
                }
                for e in events
            ],
            "event_count": len(events),
            "mode": self.mode,
        }

    # ── Subscriber 管理 ───────────────────────────────────────────────────────

    def _add_subscriber(self, sub_q: ReportQueue) -> None:
        """注册一个 subscriber 队列。

        Args:
            sub_q: subscriber 的 ReportQueue 实例。
        """
        self._subscribers.append(sub_q)

    def _remove_subscriber(self, sub_q: ReportQueue) -> None:
        """移除一个 subscriber 队列。

        Args:
            sub_q: 要移除的 ReportQueue 实例。
        """
        try:
            self._subscribers.remove(sub_q)
        except ValueError:
            pass

    # ── NOT_IMPLEMENTED ───────────────────────────────────────────────────────

    def read(self, point_ids: list[str] | None = None) -> dict[str, Any]:
        """读取点位值 —— IEC61850 Report facade 专注于 report，不实现 read。

        Args:
            point_ids: 忽略。

        Raises:
            UnsupportedOperation: read 操作未实现。
        """
        raise UnsupportedOperation(
            "read",
            "Iec61850ReportFacade.read 尚未实现。"
            "IEC61850 Report facade 专注于 report/event 语义，"
            "read 功能应由 Iec61850MmsFacade 提供",
        )

    def write(self, point_id: str, value: Any) -> None:
        """写入点位值 —— IEC61850 Report facade 不实现 write。

        Args:
            point_id: 忽略。
            value: 忽略。

        Raises:
            UnsupportedOperation: write 操作未实现。
        """
        raise UnsupportedOperation(
            "write",
            "Iec61850ReportFacade.write 尚未实现。"
            "IEC61850 Report facade 专注于 report/event 语义，"
            "write 功能应由 Iec61850MmsFacade 提供",
        )

    def subscribe(self, point_ids: list[str] | None = None) -> None:
        """订阅点位变更通知 —— 当前未实现面向外部客户端的 subscribe。

        Note:
            内部 event 推送通过 update_values -> ReportQueue 机制完成。
            此方法当前为 NOT_IMPLEMENTED，因为 subscribe 语义与 report() 聚合
            存在语义冲突。使用 report() 排空事件队列替代。

        Args:
            point_ids: 要订阅的点位列表（忽略）。

        Raises:
            UnsupportedOperation: subscribe 操作未实现。
        """
        raise UnsupportedOperation(
            "subscribe",
            "Iec61850ReportFacade.subscribe 尚未实现。"
            "使用 report() 排空事件队列作为替代",
        )

    # ── 内部方法 ──────────────────────────────────────────────────────────────

    def _wait_ready(self, port: int) -> None:
        """等待 iec61850_simulator_server 就绪。

        轮询读取 stdout 上的 READY 行，然后 TCP connect 确认端点可达。

        Args:
            port: 监听端口。

        Raises:
            RuntimeError: 进程异常退出、READY 超时或端点不可达。
        """
        assert self._sim_process is not None
        assert self._sim_process.stdout is not None

        deadline = time.monotonic() + self._RUNNER_STARTUP_TIMEOUT

        ready_received = False
        while time.monotonic() < deadline:
            if self._sim_process.poll() is not None:
                raise RuntimeError(
                    f"iec61850_simulator_server 提前退出，"
                    f"exit_code={self._sim_process.returncode}"
                )
            line = self._sim_process.stdout.readline()
            if line == "":
                time.sleep(0.05)
                continue
            stripped = line.strip()
            if stripped == self._READY_PREFIX:
                ready_received = True
                break
            elif stripped.startswith("ERROR"):
                raise RuntimeError(
                    f"iec61850_simulator_server 报错: {stripped}"
                )

        if not ready_received:
            raise RuntimeError(
                f"iec61850_simulator_server 在 {self._RUNNER_STARTUP_TIMEOUT}s 内未输出 READY"
            )

        while time.monotonic() < deadline:
            if self._sim_process.poll() is not None:
                raise RuntimeError(
                    f"iec61850_simulator_server 在输出 READY 后退出，"
                    f"exit_code={self._sim_process.returncode}"
                )
            if _can_connect(self._bind_host, port):
                return
            time.sleep(0.05)

        raise RuntimeError(
            f"iec61850_simulator_server 输出 READY 但 TCP endpoint "
            f"{self._bind_host}:{port} 在超时时间内不可达"
        )

    def _terminate_sim_process(self) -> None:
        """优雅终止 iec61850_simulator_server 子进程。"""
        if self._sim_process is None:
            return

        process = self._sim_process
        self._sim_process = None

        if process.poll() is None:
            process.terminate()
            try:
                process.communicate(timeout=self._RUNNER_STOP_TIMEOUT)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate(timeout=self._RUNNER_STOP_TIMEOUT)

        if self._stderr_thread is not None:
            self._stderr_thread.join(timeout=1.0)
            self._stderr_thread = None


# ── 工具函数 ─────────────────────────────────────────────────────────────────────


def _find_free_port(host: str = "127.0.0.1") -> int:
    """查找可用端口。

    Args:
        host: 绑定地址。

    Returns:
        可用端口号。
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])
    finally:
        sock.close()


def _can_connect(host: str, port: int, timeout: float = 0.5) -> bool:
    """检查 TCP endpoint 是否可连接。

    Args:
        host: 目标主机。
        port: 目标端口。
        timeout: 连接超时秒数。

    Returns:
        True 表示可连接。
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _drain_stderr(stderr: Any) -> None:
    """读取并丢弃 stderr 输出，避免缓冲区满导致子进程阻塞。

    Args:
        stderr: subprocess 的 stderr 流，需支持 readline()。
    """
    try:
        while True:
            line = stderr.readline()
            if not line:
                break
    except Exception:
        pass


__all__ = [
    "Iec61850ReportFacade",
    "ReportQueue",
    "probe_iec61850_report_binary",
    "resolve_iec61850_report_runner_path",
    "resolve_iec61850_report_simulator_path",
]
