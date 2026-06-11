"""Starfish OPC UA 协议 facade —— 依赖 open62541 C runner。

本模块提供 OPC UA 协议 server 模拟门面。根据环境探测 open62541
C runner 二进制 (open62541_source_simulator) 可用性，切换 real / unavailable 模式。

real 模式（binary 存在时）：
- start() 生成 TSV 配置文件并启动 open62541 C runner 子进程。
- stop() 终止子进程并清理临时配置文件。
- health() 通过 TCP connect 探测端点是否可达。

unavailable 模式（binary 缺失时）：
- 所有操作回退到 in-memory 存储，mode 报告为 "unavailable"，
  reason 说明 binary 缺失。
- 不得将 unavailable 写成真实协议 server PASS。

NOT_IMPLEMENTED（所有模式）：
- write() / subscribe() / report() 明确抛出 UnsupportedOperation。
  待后续轮次实现完整 OPC UA 客户端写入和订阅链路。

协议特征：
- 零新增第三方 Python 依赖（subprocess 为 Python 标准库）。
- native runner 需求：需 CMake 编译 open62541_source_simulator。
- runner 位置：src/starfish/native/bin/open62541_source_simulator，
  可通过 SOURCE_SIM_OPEN62541_RUNNER_PATH 环境变量覆盖。

安全边界：
- 不得 import seahorse / whale.ingest / whale.shared.source。
- 所有数据标注 synthetic。
"""

from __future__ import annotations

import os
import socket
import subprocess
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from starfish.domain import StarfishServerMemberConfig, UnsupportedOperation
from starfish.drivers.native_runtime import (
    native_runner_env,
    probe_native_binary,
    starfish_root_from,
)


# ── OPC UA 数据类型映射（Starfish value_type -> OPC UA 标量类型）───────────────────

_OPCUA_TYPE_MAP: dict[str, str] = {
    "Float": "Double",
    "Double": "Double",
    "Float64": "Double",
    "Float32": "Double",
    "Int32": "Int32",
    "Int64": "Int32",
    "Int16": "Int32",
    "Int8": "Int32",
    "UInt32": "Int32",
    "UInt16": "Int32",
    "UInt8": "Int32",
    "Boolean": "Boolean",
    "Bool": "Boolean",
    "String": "String",
}


def _map_opcua_type(value_type: str | None) -> str:
    """将 Starfish value_type 映射为 OPC UA 标量类型名。

    无法匹配时回退到 Double。

    Args:
        value_type: Starfish 点位值类型字符串。

    Returns:
        OPC UA 标量类型名（Double / Int32 / Boolean / String）。
    """
    normalized = str(value_type or "").strip().title().replace(" ", "")
    return _OPCUA_TYPE_MAP.get(normalized, "Double")


# ── open62541 runner 路径解析 ──────────────────────────────────────────────────────


def resolve_open62541_runner_path() -> Path:
    """解析 open62541 source simulator 可执行文件路径。

    优先级：
        1. 环境变量 SOURCE_SIM_OPEN62541_RUNNER_PATH。
        2. 默认路径 src/starfish/native/bin/open62541_source_simulator。

    Returns:
        open62541 runner 绝对路径（可能不存在）。
    """
    env_path = os.environ.get("SOURCE_SIM_OPEN62541_RUNNER_PATH")
    if env_path:
        return Path(env_path).expanduser().resolve()

    # 默认路径：相对于 src/starfish/native/bin/
    starfish_root = starfish_root_from(__file__)
    return starfish_root / "native" / "bin" / "open62541_source_simulator"


# ── TSV 配置生成（最小化，不 import source_lab 模型）─────────────────────────────


def _escape_tsv_field(value: str) -> str:
    """校验 TSV 字段不含控制字符。

    Args:
        value: 待校验的字段值。

    Returns:
        校验通过的原始字符串。

    Raises:
        ValueError: 包含制表符或换行符。
    """
    if "\t" in value or "\n" in value or "\r" in value:
        raise ValueError(
            f"TSV 字段包含不支持的控制字符: {value!r}"
        )
    return value


def _generate_opcua_tsv(
    host: str,
    port: int,
    plan: StarfishServerMemberConfig,
    namespace_uri: str | None = None,
) -> str:
    """根据 StarfishServerMemberConfig 生成 open62541 C runner 的最小 TSV 配置。

    输出格式（制表符分隔）：::

        endpoint\topc.tcp://host:port
        namespace_uri\turn:starfish:opcua
        update_enabled\tfalse
        node\tnode_id\tbrowse_name\tdisplay_name\tdata_type\tinitial_value
        ...

    Args:
        host: OPC UA 服务器监听地址。
        port: OPC UA 服务器监听端口。
        plan: StarfishServerMemberConfig，包含点位定义和初始值。
        namespace_uri: 可选命名空间 URI，默认为 "urn:starfish:opcua"。

    Returns:
        TSV 格式配置字符串。
    """
    uri = namespace_uri or "urn:starfish:opcua"
    lines: list[str] = [
        _escape_tsv_field("endpoint") + "\t" + _escape_tsv_field(f"opc.tcp://{host}:{port}"),
        _escape_tsv_field("namespace_uri") + "\t" + _escape_tsv_field(uri),
        _escape_tsv_field("update_enabled") + "\tfalse",
    ]

    for point in plan.points:
        # node_id 格式: IED.LD.LN.DO（open62541 C runner 要求四点层次格式）
        node_id = point.node_key or point.point_id
        # 如果 node_key 不是四点格式，使用默认层次 Starfish.SF.LN0.<point_id>
        if node_id.count(".") < 3:
            node_id = f"Starfish.SF.LN0.{point.point_id}"
        browse_name = point.point_name or point.point_id
        display_name = browse_name
        data_type = _map_opcua_type(point.value_type)
        raw_value = plan.initial_values.get(point.point_id, 0)
        # 格式化初始值
        if data_type == "Boolean":
            initial_str = "true" if raw_value else "false"
        elif data_type == "Int32":
            initial_str = str(int(float(raw_value or 0)))
        elif data_type == "String":
            initial_str = str(raw_value or "")
        else:
            initial_str = str(float(raw_value or 0.0))

        lines.append(
            "\t".join([
                _escape_tsv_field("node"),
                _escape_tsv_field(node_id),
                _escape_tsv_field(browse_name),
                _escape_tsv_field(display_name),
                _escape_tsv_field(data_type),
                _escape_tsv_field(initial_str),
            ])
        )

    return "\n".join(lines) + "\n"


# ── 依赖探测 ─────────────────────────────────────────────────────────────────────


def probe_opcua_binary() -> tuple[bool, str]:
    """探测 open62541 runner 二进制和环境依赖。

    检查项：
        1. open62541_source_simulator 可执行文件是否存在。
        2. asyncua Python 库是否可导入（subscribe 需要）。

    Returns:
        (binary_available, reason) 二元组。
    """
    runner_path = resolve_open62541_runner_path()
    available, reason = probe_native_binary(
        runner_path,
        display_name="open62541 runner",
        min_size=1024,
    )
    if not available:
        return False, (
            f"{reason}。请在 src/starfish/native/ 下执行 CMake 构建，"
            f"或通过 SOURCE_SIM_OPEN62541_RUNNER_PATH 环境变量指定路径。"
        )
    return True, reason


# ── OPC UA facade ────────────────────────────────────────────────────────────────


class OpcUaFacade:
    """OPC UA 协议 server 模拟门面。

    根据 open62541 C runner 可用性切换真实子进程或回退模式。

    真实模式（binary 可用）：
        start() 生成 TSV 配置 -> 启动 open62541_source_simulator 子进程 ->
        等待 READY 信号 -> TCP endpoint 可达。
        stop() 优雅终止子进程并清理临时文件。

    unavailable 模式（binary 缺失）：
        所有状态管理在内存中完成，mode="unavailable"。
        load_points / read / update_values 可用 in-memory 实现。
        write / subscribe / report 均为 UnsupportedOperation。

    不负责：OPC UA 协议帧编解码、完整地址空间建模、安全策略/证书。
    """

    _RUNNER_STARTUP_TIMEOUT = 10.0  # 等待 READY 的超时秒数
    _RUNNER_STOP_TIMEOUT = 5.0      # 优雅终止超时秒数
    _READY_PREFIX = "READY"

    def __init__(self, bind_host: str = "127.0.0.1", port: int = 0) -> None:
        """初始化 OPC UA facade。

        Args:
            bind_host: 绑定地址。
            port: 监听端口（0 表示自动分配）。
        """
        self._plan: StarfishServerMemberConfig | None = None
        self._started: bool = False
        self._values: dict[str, Any] = {}
        self._started_at: datetime | None = None
        self._bind_host: str = bind_host
        self._port: int = port
        self._actual_port: int = 0

        # 子进程管理
        self._process: subprocess.Popen[str] | None = None
        self._stderr_thread: threading.Thread | None = None
        self._temp_dir: tempfile.TemporaryDirectory[str] | None = None

        # 环境探测
        self._binary_available, self._binary_reason = probe_opcua_binary()

    # ── 属性 ──────────────────────────────────────────────────────────────────

    @property
    def protocol(self) -> str:
        """返回归一化协议名。"""
        return "OPC_UA"

    @property
    def mode(self) -> str:
        """返回运行模式。

        - "real": open62541 C runner 可用，真实子进程生命周期。
        - "unavailable": open62541 binary 缺失，内存回退。
        """
        return "real" if self._binary_available else "unavailable"

    @property
    def binary_available(self) -> bool:
        """返回 open62541 binary 是否可用。"""
        return self._binary_available

    @property
    def binary_reason(self) -> str:
        """返回 binary 探测原因说明。"""
        return self._binary_reason

    # ── 生命周期 ──────────────────────────────────────────────────────────────

    def start(self) -> None:
        """启动 OPC UA facade。

        真实模式：生成 TSV -> 启动 open62541 C runner -> 等待 READY。
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

        # 真实模式：启动 open62541 C runner
        runner_path = resolve_open62541_runner_path()
        if not runner_path.exists():
            raise RuntimeError(
                f"open62541 runner 不存在: {runner_path}。"
                "请先编译 open62541 C runner。"
            )

        # 确定端口
        actual_port = self._port
        if actual_port <= 0:
            actual_port = _find_free_port(self._bind_host)
        self._actual_port = actual_port

        # 生成 TSV 配置文件
        if self._plan is None:
            raise RuntimeError("OPC UA facade: load_points() 必须先于 start() 调用")
        tsv_content = _generate_opcua_tsv(self._bind_host, actual_port, self._plan)
        self._temp_dir = tempfile.TemporaryDirectory(prefix="starfish_opcua_")
        config_path = Path(self._temp_dir.name) / "server.tsv"
        config_path.write_text(tsv_content, encoding="utf-8")

        # 启动子进程
        try:
            self._process = subprocess.Popen(
                [str(runner_path), str(config_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                bufsize=1,
                env=native_runner_env(runner_path),
            )
        except OSError as exc:
            self._cleanup_temp_dir()
            raise RuntimeError(f"启动 open62541 runner 失败: {exc}") from exc

        # 启动 stderr 引流线程（避免缓冲区满导致子进程阻塞）
        assert self._process.stderr is not None
        self._stderr_thread = threading.Thread(
            target=_drain_stderr,
            args=(self._process.stderr,),
            daemon=True,
        )
        self._stderr_thread.start()

        # 等待 READY 信号
        try:
            self._wait_ready(actual_port)
        except Exception:
            # 启动失败，清理子进程
            self._terminate_process()
            self._cleanup_temp_dir()
            raise

        self._started = True
        self._started_at = datetime.now(timezone.utc)

    def stop(self) -> None:
        """停止 OPC UA facade。

        真实模式：优雅终止子进程，清理临时文件。
        unavailable 模式：重置 in-memory 状态。

        重复调用安全（幂等）。
        """
        if not self._started:
            return

        if self._binary_available and self._process is not None:
            self._terminate_process()

        self._cleanup_temp_dir()
        self._started = False

    # ── 可观测性 ──────────────────────────────────────────────────────────────

    def health(self) -> dict[str, Any]:
        """返回当前 facade 的可观测健康状态。

        真实模式：通过 TCP connect 探测端点是否可达。
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

    def load_points(self, plan: StarfishServerMemberConfig) -> None:
        """加载点位定义和初始值到内存存储。

        Args:
            plan: 已校验的 StarfishServerMemberConfig 实例。
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
            "OpcUaFacade.write 尚未实现，"
            "待后续轮次实现 OPC UA 客户端 write 链路",
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
            "OpcUaFacade.subscribe 尚未实现，"
            "待后续轮次实现 OPC UA 订阅链路",
        )

    def report(self) -> dict[str, Any]:
        """上报门面状态摘要 —— 当前未实现。

        Raises:
            UnsupportedOperation: report 操作尚未实现。
        """
        raise UnsupportedOperation(
            "report",
            "OpcUaFacade.report 尚未实现，"
            "待后续轮次实现结构化 telemetry report",
        )

    # ── 内部方法 ──────────────────────────────────────────────────────────────

    def _wait_ready(self, port: int) -> None:
        """等待 open62541 runner 就绪。

        轮询读取 stdout 上的 READY 行，然后 TCP connect 确认端点可达。

        Args:
            port: 监听端口。

        Raises:
            RuntimeError: 进程异常退出、READY 超时或端点不可达。
        """
        assert self._process is not None
        assert self._process.stdout is not None

        deadline = time.monotonic() + self._RUNNER_STARTUP_TIMEOUT

        # 阶段 1：读取 READY 行
        ready_received = False
        while time.monotonic() < deadline:
            if self._process.poll() is not None:
                raise RuntimeError(
                    f"open62541 runner 提前退出，"
                    f"exit_code={self._process.returncode}"
                )
            line = self._process.stdout.readline()
            if line == "":
                time.sleep(0.05)
                continue
            stripped = line.strip()
            if stripped == self._READY_PREFIX:
                ready_received = True
                break
            elif stripped.startswith("ERROR"):
                raise RuntimeError(
                    f"open62541 runner 报错: {stripped}"
                )
            # 其他行忽略（可能是调试输出）

        if not ready_received:
            raise RuntimeError(
                f"open62541 runner 在 {self._RUNNER_STARTUP_TIMEOUT}s 内未输出 READY"
            )

        # 阶段 2：轮询 TCP endpoint 直到可连接
        while time.monotonic() < deadline:
            if self._process.poll() is not None:
                raise RuntimeError(
                    f"open62541 runner 在输出 READY 后退出，"
                    f"exit_code={self._process.returncode}"
                )
            if _can_connect(self._bind_host, port):
                return
            time.sleep(0.05)

        raise RuntimeError(
            f"open62541 runner 输出 READY 但 TCP endpoint "
            f"{self._bind_host}:{port} 在超时时间内不可达"
        )

    def _terminate_process(self) -> None:
        """优雅终止 open62541 子进程。"""
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

    def _cleanup_temp_dir(self) -> None:
        """清理临时配置目录。"""
        if self._temp_dir is not None:
            try:
                self._temp_dir.cleanup()
            except Exception:
                pass
            self._temp_dir = None


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


__all__ = ["OpcUaFacade", "probe_opcua_binary", "resolve_open62541_runner_path"]
