"""Starfish IEC 60870-5-104 协议 facade —— 依赖 lib60870 C runner。

本模块提供 IEC104 协议 server 模拟门面。根据环境探测
iec104_simulator_server C runner 二进制可用性，切换 real / unavailable 模式。

real 模式（binary 存在时）：
- start() 启动 iec104_simulator_server 子进程，传入端口号。
- stop() 终止子进程。
- health() 通过 TCP connect 探测端点是否可达。

unavailable 模式（binary 缺失时）：
- 所有操作回退到 in-memory 存储，mode 报告为 "unavailable"，
  reason 说明 binary 缺失。
- 不得将 unavailable 写成真实协议 server PASS。

NOT_IMPLEMENTED（所有模式）：
- write() / subscribe() / report() 明确抛出 UnsupportedOperation。
  待后续轮次实现完整 IEC104 客户端写入和事件订阅链路。

协议特征：
- 零新增第三方 Python 依赖（subprocess 为 Python 标准库）。
- native runner 需求：需 CMake 编译 iec104_simulator_server。
- runner 位置：src/starfish/native/bin/iec104_simulator_server，
  可通过 WHALE_NATIVE_RUNNER_DIR 环境变量覆盖。

安全边界：
- 不得 import seahorse / whale.ingest / whale.shared.source。
- 所有数据标注 synthetic。
"""

from __future__ import annotations

import os
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


# ── iec104 runner 路径解析 ────────────────────────────────────────────────────────


def resolve_iec104_runner_path() -> Path:
    """解析 iec104_simulator_server 可执行文件路径。

    优先级：
        1. 环境变量 WHALE_NATIVE_RUNNER_DIR（需指向包含该二进制的目录）。
        2. 默认路径 src/starfish/native/bin/iec104_simulator_server。

    Returns:
        iec104 runner 绝对路径（可能不存在）。
    """
    env_dir = os.environ.get("WHALE_NATIVE_RUNNER_DIR")
    if env_dir:
        base = Path(env_dir).expanduser().resolve()
    else:
        starfish_root = starfish_root_from(__file__)
        base = starfish_root / "native" / "bin"
    return base / "iec104_simulator_server"


# ── 依赖探测 ─────────────────────────────────────────────────────────────────────


def probe_iec104_binary() -> tuple[bool, str]:
    """探测 iec104_simulator_server 二进制和环境依赖。

    检查项：
        1. iec104_simulator_server 可执行文件是否存在。
        2. 是否具有执行权限。

    Returns:
        (binary_available, reason) 二元组。
    """
    runner_path = resolve_iec104_runner_path()
    available, reason = probe_native_binary(
        runner_path,
        display_name="iec104 simulator server",
        min_size=1024,
    )
    if not available:
        return False, (
            f"{reason}。请在 src/starfish/native/ 下执行 CMake 构建，"
            f"或通过 WHALE_NATIVE_RUNNER_DIR 环境变量指定目录。"
        )
    return True, reason


# ── IEC104 facade ────────────────────────────────────────────────────────────────


class Iec104Facade:
    """IEC 60870-5-104 协议 server 模拟门面。

    根据 iec104_simulator_server C runner 可用性切换真实子进程或回退模式。

    真实模式（binary 可用）：
        start() 启动 iec104_simulator_server 子进程 -> 等待 READY 信号。
        stop() 优雅终止子进程。
        health() 通过 TCP connect 探测端点可达性。

    unavailable 模式（binary 缺失）：
        所有状态管理在内存中完成，mode="unavailable"。
        load_points / read / update_values 可用 in-memory 实现。
        write / subscribe / report 均为 UnsupportedOperation。

    IEC104 协议特征：
        iec104_simulator_server 启动后在指定端口监听 IEC104 TCP 连接，
        响应 interrogation 命令和时钟同步帧。IEC104 帧编解码由 C runner 承担，
        Python 侧不处理 IEC104 协议细节。

    不负责：ASDU 编解码、IOA 地址映射、时标处理、冗余链路。
    """

    _RUNNER_STARTUP_TIMEOUT = 10.0  # 等待 READY 的超时秒数
    _RUNNER_STOP_TIMEOUT = 5.0      # 优雅终止超时秒数
    _READY_LINE = "READY"          # runner 就绪信号

    def __init__(self, bind_host: str = "127.0.0.1", port: int = 0) -> None:
        """初始化 IEC104 facade。

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
        self._process: subprocess.Popen[str] | None = None
        self._stderr_thread: threading.Thread | None = None

        # 环境探测
        self._binary_available, self._binary_reason = probe_iec104_binary()

    # ── 属性 ──────────────────────────────────────────────────────────────────

    @property
    def protocol(self) -> str:
        """返回归一化协议名。"""
        return "IEC104"

    @property
    def mode(self) -> str:
        """返回运行模式。

        - "real": iec104_simulator_server C runner 可用，真实子进程生命周期。
        - "unavailable": iec104 binary 缺失，内存回退。
        """
        return "real" if self._binary_available else "unavailable"

    @property
    def binary_available(self) -> bool:
        """返回 iec104_simulator_server binary 是否可用。"""
        return self._binary_available

    @property
    def binary_reason(self) -> str:
        """返回 binary 探测原因说明。"""
        return self._binary_reason

    # ── 生命周期 ──────────────────────────────────────────────────────────────

    def start(self) -> None:
        """启动 IEC104 facade。

        真实模式：启动 iec104_simulator_server 子进程 -> 等待 READY。
        unavailable 模式：设置 in-memory 状态。

        重复调用安全（幂等）。

        Raises:
            RuntimeError: 真实模式下二进制不存在、子进程启动失败或 READY 超时。
        """
        if self._started:
            return

        if not self._binary_available:
            # unavailable 模式：仅设置状态
            self._started = True
            self._started_at = datetime.now(timezone.utc)
            return

        # 真实模式：启动 iec104_simulator_server C runner
        runner_path = resolve_iec104_runner_path()
        if not runner_path.exists():
            raise RuntimeError(
                f"iec104 simulator server 不存在: {runner_path}。"
                "请先编译 iec104_simulator_server。"
            )

        # 确定端口
        actual_port = self._port
        if actual_port <= 0:
            actual_port = _find_free_port(self._bind_host)
        self._actual_port = actual_port

        # 启动子进程：iec104_simulator_server <port>
        try:
            self._process = subprocess.Popen(
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
            raise RuntimeError(f"启动 iec104 simulator server 失败: {exc}") from exc

        # 启动 stderr 引流线程
        assert self._process.stderr is not None
        self._stderr_thread = threading.Thread(
            target=_drain_stderr,
            args=(self._process.stderr,),
            daemon=True,
        )
        self._stderr_thread.start()

        # 等待 READY 信号
        assert self._process.stdout is not None
        deadline = time.monotonic() + self._RUNNER_STARTUP_TIMEOUT
        ready_received = False
        while time.monotonic() < deadline:
            if self._process.poll() is not None:
                raise RuntimeError(
                    f"iec104 simulator server 提前退出，"
                    f"exit_code={self._process.returncode}"
                )
            line = self._process.stdout.readline()
            if line == "":
                time.sleep(0.05)
                continue
            stripped = line.strip()
            if stripped == self._READY_LINE:
                ready_received = True
                break
            # 其他行忽略

        if not ready_received:
            self._terminate_process()
            raise RuntimeError(
                f"iec104 simulator server 在 "
                f"{self._RUNNER_STARTUP_TIMEOUT}s 内未输出 READY"
            )

        self._started = True
        self._started_at = datetime.now(timezone.utc)

    def stop(self) -> None:
        """停止 IEC104 facade。

        真实模式：优雅终止子进程。
        unavailable 模式：重置 in-memory 状态。

        重复调用安全（幂等）。
        """
        if not self._started:
            return

        if self._binary_available and self._process is not None:
            self._terminate_process()

        self._started = False

    # ── 可观测性 ──────────────────────────────────────────────────────────────

    def health(self) -> dict[str, Any]:
        """返回当前 facade 的可观测健康状态。

        真实模式：通过 TCP connect 探测端口是否可达。
        unavailable 模式：返回 mode="unavailable" 及原因。

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

    def read(self, point_ids: list[str] | None = None) -> dict[str, Any]:
        """从内存读取当前点位值。

        Args:
            point_ids: 要读取的点位 ID 列表，None 表示全部。

        Returns:
            point_id -> 当前值 的 dict。不存在的点位置为 None。
        """
        if point_ids is None:
            return dict(self._values)
        return {pid: self._values.get(pid) for pid in point_ids}

    def update_values(self, values: dict[str, Any]) -> None:
        """批量更新内存中的点位值。

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

    # ── NOT_IMPLEMENTED ───────────────────────────────────────────────────────

    def write(self, point_id: str, value: Any) -> None:
        """写入单个点位值 —— 当前未实现。

        Args:
            point_id: 目标点位 ID。
            value: 要写入的值。

        Raises:
            UnsupportedOperation: 写入操作尚未实现。
        """
        raise UnsupportedOperation(
            "write",
            "Iec104Facade.write 尚未实现，"
            "待后续轮次实现 IEC104 ASDU 写链路",
        )

    def subscribe(self, point_ids: list[str]) -> None:
        """订阅点位数据变更通知 —— 当前未实现。

        Args:
            point_ids: 要订阅的点位 ID 列表。

        Raises:
            UnsupportedOperation: 订阅操作尚未实现。
        """
        raise UnsupportedOperation(
            "subscribe",
            "Iec104Facade.subscribe 尚未实现，"
            "待后续轮次实现 IEC104 事件订阅链路",
        )

    def report(self) -> dict[str, Any]:
        """上报门面状态摘要 —— 当前未实现。

        Raises:
            UnsupportedOperation: report 操作尚未实现。
        """
        raise UnsupportedOperation(
            "report",
            "Iec104Facade.report 尚未实现，"
            "待后续轮次实现结构化 telemetry report",
        )

    # ── 内部方法 ──────────────────────────────────────────────────────────────

    def _terminate_process(self) -> None:
        """优雅终止 iec104_simulator_server 子进程。"""
        if self._process is None:
            return

        process = self._process
        self._process = None

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


__all__ = ["Iec104Facade", "probe_iec104_binary", "resolve_iec104_runner_path"]
