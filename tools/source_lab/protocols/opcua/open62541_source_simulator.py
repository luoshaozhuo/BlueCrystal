"""基于 open62541 C runner 的 OPC UA 源模拟器后端。

Python 侧负责：
1. 生成 runner TSV 配置文件；
2. 启动 open62541 C runner 子进程；
3. 等待 TCP endpoint 可连接；
4. 通过 stdin 向 runner 下发写入命令；
5. stop 时 terminate / kill 子进程；
6. 清理临时配置文件目录。

不负责：OPC UA 协议栈的具体实现（由 C runner 承担）。
数据流：SimulatedSource -> build_address_space() -> render_open62541_tsv() -> TSV 文件
         -> subprocess.Popen(open62541_source_simulator) -> stdin 命令 -> 进程退出 -> 清理。
设计边界：使用 subprocess 而非绑定库调用，避免 GIL 和 C API 兼容性问题；写入命令通过 stdin 管道下发。
兼容性约束：runner 必须在运行前由 CMake 编译好；路径可被 SOURCE_SIM_OPEN62541_RUNNER_PATH 环境变量覆盖。
"""

from __future__ import annotations

import os
import socket
import subprocess
import tempfile
import time
from collections import OrderedDict
from pathlib import Path

from tools.source_lab.access.runners.protocol import (
    ProtocolDiagnostics,
    read_protocol_line,
    start_stderr_drain_thread,
)
from tools.source_lab.protocols.opcua.address_space import (
    build_address_space,
    opcua_data_type,
    render_open62541_tsv,
)
from tools.source_lab.model import SimulatedPoint, SimulatedSource


_STARTUP_TIMEOUT_SECONDS = 10.0
_READY_POLL_SECONDS = 0.05
_STOP_TIMEOUT_SECONDS = 5.0
_READY_PREFIX = "READY"
_ERROR_PREFIX = "ERROR"
_OUTPUT_TAIL_LINES = 40


class Open62541SourceSimulatorError(RuntimeError):
    """open62541 仿真器启动或关闭失败时抛出的异常。"""


class Open62541SourceSimulator:
    """由外部 open62541 C runner 实现的 OPC UA 模拟器。

    通过进程间通信管理 runner 生命周期：生成 TSV 配置 -> 启动子进程 -> 等待 READY -> stdin 写入命令 -> 终止。
    写入能力通过标准输入管道下发，C runner 解析并更新 OPC UA 服务器内部变量节点。

    关键属性：
        _source: 原始 SimulatedSource 定义。
        _startup_timeout_seconds: 启动超时秒数。
        _address_space: 构建好的 OPC UA 地址空间描述。
        _temp_dir: 临时配置文件目录实例。
        _config_path: 生成的 TSV 配置文件路径。
        _process: open62541 runner 子进程。
        _write_targets_by_key: point_key / node_id 到 (node_id, SimulatedPoint) 的写入索引。
    """

    def __init__(self, source: SimulatedSource, *, startup_timeout_seconds: float = 10.0) -> None:
        """初始化 open62541 仿真器实例。

        Args:
            source: 待仿真的源定义，协议必须为 opcua。
            startup_timeout_seconds: 启动超时秒数，可通过 connection.params 中
                open62541_startup_timeout_seconds 覆盖。

        Raises:
            Open62541SourceSimulatorError: 协议不是 opcua 时触发。
        """
        normalized_protocol = (
            source.connection.protocol.strip().lower().replace("_", "").replace("-", "")
        )
        if normalized_protocol != "opcua":
            raise Open62541SourceSimulatorError(
                "Open62541SourceSimulator only supports `opcua` sources"
            )

        timeout_from_params = source.connection.params.get("open62541_startup_timeout_seconds")
        resolved_startup_timeout = startup_timeout_seconds
        if isinstance(timeout_from_params, (int, float)) and float(timeout_from_params) > 0:
            resolved_startup_timeout = float(timeout_from_params)
        if resolved_startup_timeout <= 0:
            resolved_startup_timeout = _STARTUP_TIMEOUT_SECONDS

        self._source = source
        self._startup_timeout_seconds = resolved_startup_timeout
        self._address_space = build_address_space(source)
        self._temp_dir: tempfile.TemporaryDirectory[str] | None = None
        self._config_path: Path | None = None
        self._process: subprocess.Popen[str] | None = None
        self._write_targets_by_key: dict[str, tuple[str, SimulatedPoint]] = {}
        self._protocol_noise_count = 0
        self._protocol_noise_samples: tuple[str, ...] = ()

    @property
    def protocol_noise_count(self) -> int:
        """返回启动过程中观察到的非预期 stdout 行数。

        非预期 stdout 表示 C runner 在协议信令之外输出了无关数据，
        可能表明 runner 行为异常。
        """
        return self._protocol_noise_count

    @property
    def protocol_noise_samples(self) -> tuple[str, ...]:
        """返回启动过程中保留的非预期 stdout 样本。"""
        return self._protocol_noise_samples

    @property
    def endpoint(self) -> str:
        """返回 OPC UA 服务器端点 URL。"""
        return self._address_space.endpoint

    @property
    def name(self) -> str:
        """返回模拟器源名称。"""
        return self._source.connection.name

    def start(self) -> "Open62541SourceSimulator":
        """启动 open62541 runner 进程。

        start 是幂等的：已启动时直接返回 self。

        Returns:
            self，支持链式调用。

        Raises:
            Open62541SourceSimulatorError: runner 可执行文件缺失或启动失败。
        """
        # ---------- 阶段 1: 跳过已启动进程 ----------
        if self._process is not None:
            return self

        # ---------- 阶段 2: 检查 runner 可执行文件 ----------
        # 如果 runner 不存在，提前报错而不是启动后等待超时。
        runner_path = resolve_runner_path()
        if not runner_path.exists():
            raise Open62541SourceSimulatorError(
                "open62541 runner executable does not exist: "
                f"{runner_path}. Build it first with CMake."
            )

        # ---------- 阶段 3: 构建配置文件并启动子进程 ----------
        self._config_path = self._build_config_file()
        config_path = self._config_path

        self._process = subprocess.Popen(
            [str(runner_path), str(config_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )

        # ---------- 阶段 4: 等待 RUNNER 就绪并建立写入索引 ----------
        try:
            self._wait_until_ready()
        except Exception:
            stdout, stderr = self._terminate_and_collect_output()
            returncode = self._process.returncode if self._process is not None else None
            config_exists = config_path.exists()
            config_size = config_path.stat().st_size if config_exists else 0
            stdout_tail = _tail_output(stdout)
            stderr_tail = _tail_output(stderr)
            self._cleanup_temp_dir()
            self._process = None
            raise Open62541SourceSimulatorError(
                "Failed to start open62541 simulator runner.\n"
                f"runner_path={runner_path}\n"
                f"source={self._source.connection.name}\n"
                f"endpoint={self.endpoint}\n"
                f"endpoint_host={self._source.connection.host}\n"
                f"endpoint_port={self._source.connection.port}\n"
                f"startup_timeout_seconds={self._startup_timeout_seconds}\n"
                f"config_path={config_path}\n"
                f"config_exists={config_exists}\n"
                f"config_size_bytes={config_size}\n"
                f"returncode={returncode}\n"
                f"stdout_tail_lines={_OUTPUT_TAIL_LINES}:\n{stdout_tail}\n"
                f"stderr_tail_lines={_OUTPUT_TAIL_LINES}:\n{stderr_tail}"
            ) from None

        # 建立 point_key -> node_id 的双向索引，支持按 key 或逻辑路径写入
        self._write_targets_by_key = {}
        points_by_key = {point.key: point for point in self._source.points}
        for variable in self._address_space.variables:
            point = points_by_key.get(variable.point_key)
            if point is None:
                continue

            target = (variable.node_id, point)
            self._write_targets_by_key[variable.point_key] = target
            self._write_targets_by_key[variable.node_id] = target

        return self

    def stop(self) -> None:
        """停止 open62541 runner 进程并清理临时文件。

        优先使用 terminate（SIGTERM），超时后升级为 kill（SIGKILL）。
        幂等设计：多次调用不会报错。
        """
        if self._process is None:
            self._cleanup_temp_dir()
            return

        process = self._process
        if process.poll() is None:
            process.terminate()

            try:
                process.communicate(timeout=_STOP_TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate(timeout=_STOP_TIMEOUT_SECONDS)

        self._process = None
        self._write_targets_by_key = {}
        self._cleanup_temp_dir()

    def __enter__(self) -> "Open62541SourceSimulator":
        return self.start()

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.stop()

    def writes(self, values_by_key: dict[str, str | int | float | bool]) -> None:
        """通过 open62541 runner 的 stdin 下发点位写入命令。

        当内部循环更新已启用时，跳过 stdin 写入以避免重复更新。
        写入管道损坏时抛出 RuntimeError，不静默吞异常。

        Args:
            values_by_key: 点位 key 或完整逻辑路径到值的映射。

        Raises:
            RuntimeError: 模拟器未启动或 runner stdin 不可用时触发。
        """
        if self._process is None or self._process.poll() is not None:
            raise RuntimeError("Simulator runtime must be started before writes()")

        # 内部循环更新启用时，stdin 写入会导致值的重复更新，因此跳过。
        if self._internal_update_enabled():
            return

        if self._process.stdin is None:
            raise RuntimeError("Open62541 runner stdin is unavailable for writes()")

        commands: list[str] = []

        for key, value in values_by_key.items():
            target = self._write_targets_by_key.get(key)
            if target is None:
                continue

            node_id, point = target
            serialized = self._serialize_value(point, value)
            commands.append(
                "\t".join(
                    (
                        "write",
                        self._validate_command_field(node_id),
                        self._validate_command_field(opcua_data_type(point.data_type)),
                        serialized,
                    )
                )
                + "\n"
            )

        if not commands:
            return

        try:
            self._process.stdin.write("".join(commands))
            self._process.stdin.flush()
        except BrokenPipeError as exc:
            raise RuntimeError("Open62541 runner stdin pipe is broken") from exc
        except OSError as exc:
            raise RuntimeError("Failed to write command to open62541 runner") from exc

    def _build_config_file(self) -> Path:
        """生成 runner 使用的临时 TSV 配置文件。

        Returns:
            生成的 TSV 文件路径。
        """
        self._temp_dir = tempfile.TemporaryDirectory(prefix="open62541_source_sim_")
        config_path = Path(self._temp_dir.name) / f"{self.name}.tsv"
        config_path.write_text(
            render_open62541_tsv(
                self._address_space,
                extra_records=self._runner_config_records(),
            ),
            encoding="utf-8",
        )
        return config_path

    def _runner_config_records(self) -> dict[str, str]:
        """构建 runner TSV 配置的附加记录。

        Returns:
            包含 update_enabled / update_interval_ms / update_all 的有序字典。
        """
        update_enabled = self._internal_update_enabled()
        update_interval_ms = self._internal_update_interval_ms()
        return OrderedDict(
            (
                ("update_enabled", "true" if update_enabled else "false"),
                ("update_interval_ms", str(update_interval_ms)),
                ("update_all", "true"),
            )
        )

    def _wait_until_ready(self) -> None:
        """等待 runner 就绪：读取 stdout 上的 READY 行并轮询 TCP endpoint。

        必须先读取 READY 行再轮询 TCP，因为 runner 可能在绑定端口前就输出 READY。
        启动 stderr 引流线程避免缓冲区阻塞，finally 中确保该线程退出。

        Raises:
            Open62541SourceSimulatorError: 进程退出、READY 未收到、endpoint 不可达或 stdout 有噪声。
        """
        # ---------- 阶段 1: 校验进程状态 ----------
        if self._process is None:
            raise Open62541SourceSimulatorError("Runner process has not been started")

        # ---------- 阶段 2: 准备参数并启动 stderr 引流线程 ----------
        host = self._source.connection.host
        port = int(self._source.connection.port)
        deadline = time.monotonic() + self._startup_timeout_seconds
        assert self._process.stdout is not None
        diagnostics = ProtocolDiagnostics()
        stderr_thread = start_stderr_drain_thread(self._process.stderr, diagnostics)

        # ---------- 阶段 3: 读取 READY 行 ----------
        try:
            ready_line = read_protocol_line(
                self._process.stdout,
                allowed_prefixes=(_READY_PREFIX,),
                error_prefix=_ERROR_PREFIX,
                diagnostics=diagnostics,
                label="open62541 simulator runner",
            )
            if ready_line != _READY_PREFIX:
                raise Open62541SourceSimulatorError(
                    "READY not received from simulator runner; unexpected response: "
                    f"{ready_line!r}{diagnostics.render_context()}"
                )
            self._protocol_noise_count = diagnostics.stdout_noise_count
            self._protocol_noise_samples = tuple(diagnostics.stdout_noise_samples)
            if diagnostics.stdout_noise_count > 0:
                raise Open62541SourceSimulatorError(
                    "Simulator runner emitted unexpected stdout noise during startup"
                    f"{diagnostics.render_context()}"
                )

            # ---------- 阶段 4: 轮询 TCP endpoint 直到可连接 ----------
            while time.monotonic() < deadline:
                if self._process.poll() is not None:
                    raise Open62541SourceSimulatorError(
                        "Process exited before READY endpoint became connectable: "
                        f"exitcode={self._process.returncode}{diagnostics.render_context()}"
                    )
                if _can_connect(host, port):
                    return
                time.sleep(_READY_POLL_SECONDS)
        finally:
            stderr_thread.join(timeout=1.0)

        raise Open62541SourceSimulatorError(
            "READY received but endpoint did not become connectable before timeout: "
            f"{host}:{port}, timeout_seconds={self._startup_timeout_seconds}"
            f"{diagnostics.render_context()}"
        )

    def _terminate_and_collect_output(self) -> tuple[str, str]:
        """终止失败的 runner 进程并收集 stdout/stderr。

        Returns:
            (stdout 内容, stderr 内容)。超时未收集到时不抛出，返回空字符串。
        """
        if self._process is None:
            return "", ""

        process = self._process
        if process.poll() is None:
            process.terminate()

        try:
            stdout, stderr = process.communicate(timeout=_STOP_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate(timeout=_STOP_TIMEOUT_SECONDS)

        return stdout or "", stderr or ""

    def _cleanup_temp_dir(self) -> None:
        """清理临时配置目录，清除 TSV 配置文件。"""
        if self._temp_dir is not None:
            self._temp_dir.cleanup()
            self._temp_dir = None
            self._config_path = None

    def _serialize_value(
        self,
        point: SimulatedPoint,
        value: str | int | float | bool | None,
    ) -> str:
        """将外部值序列化为 runner 期望的标量文本格式。

        按 OPC UA 数据类型选择序列化策略：
        - Boolean 接受多种真值字符串；
        - Int32 做边界钳制；
        - String 直接转字符串；
        - 其他类型按浮点处理。

        Args:
            point: 点位定义，用于获取数据类型。
            value: 待写入的外部值。

        Returns:
            序列化后的值字符串。
        """
        opcua_type_name = opcua_data_type(point.data_type)

        if opcua_type_name == "Boolean":
            if isinstance(value, str):
                return self._validate_command_field(
                    "true" if value.strip().lower() in {"1", "true", "yes", "on"} else "false"
                )
            return self._validate_command_field("true" if bool(value) else "false")

        if opcua_type_name == "Int32":
            casted = int(float(value or 0))
            return self._validate_command_field(
                str(max(-2147483648, min(2147483647, casted)))
            )

        if opcua_type_name == "String":
            return self._validate_command_field(str(value or ""))

        return self._validate_command_field(str(float(value or 0.0)))

    def _validate_command_field(self, value: str) -> str:
        """校验 stdin 命令字段不包含制表符或换行符，防止破坏 TSV 协议。

        Args:
            value: 待校验的字段字符串。

        Returns:
            校验通过的字符串。

        Raises:
            ValueError: 字段包含制表符或换行符时抛出。
        """
        if "\t" in value or "\n" in value or "\r" in value:
            raise ValueError(
                f"Open62541 write value contains unsupported control character: {value!r}"
            )
        return value

    def _internal_update_enabled(self) -> bool:
        """解析 native runner 是否应启用内部循环更新。

        优先级：connection.params.open62541_internal_update_enabled > 环境变量 SOURCE_SIM_POLL_SOURCE_UPDATE_ENABLED。

        Returns:
            是否启用内部循环更新。
        """
        params_value = self._source.connection.params.get("open62541_internal_update_enabled")
        if isinstance(params_value, bool):
            return params_value
        if isinstance(params_value, str) and params_value.strip() != "":
            return params_value.strip().lower() in {"1", "true", "yes", "on"}
        load_update_enabled = os.environ.get("SOURCE_SIM_POLL_SOURCE_UPDATE_ENABLED", "false")
        return load_update_enabled.strip().lower() in {"1", "true", "yes", "on"}

    def _internal_update_interval_ms(self) -> int:
        """解析 native runner 内部循环更新间隔（毫秒）。

        优先级：connection.params.open62541_internal_update_interval_ms > 环境变量 SOURCE_SIM_POLL_SOURCE_UPDATE_HZ。

        Returns:
            更新间隔毫秒数，最小为 1。
        """
        params_value = self._source.connection.params.get("open62541_internal_update_interval_ms")
        if isinstance(params_value, (int, float)) and float(params_value) > 0:
            return max(1, round(float(params_value)))
        if isinstance(params_value, str) and params_value.strip() != "":
            try:
                resolved = float(params_value)
            except ValueError:
                resolved = 0.0
            if resolved > 0:
                return max(1, round(resolved))
        return _resolve_internal_update_interval_ms()


def resolve_runner_path() -> Path:
    """解析 open62541 source simulator 可执行文件路径。

    环境变量 SOURCE_SIM_OPEN62541_RUNNER_PATH 可覆盖默认路径。
    默认路径相对于 source_lab/native/build/ 目录。

    Returns:
        Runner 可执行文件绝对路径。
    """
    env_path = os.environ.get("SOURCE_SIM_OPEN62541_RUNNER_PATH")
    if env_path:
        return Path(env_path).expanduser().resolve()

    source_lab_root = Path(__file__).resolve().parents[2]
    runner_name = "open62541_source_simulator.exe" if os.name == "nt" else "open62541_source_simulator"
    return source_lab_root / "native" / "build" / runner_name


def _can_connect(host: str, port: int) -> bool:
    """检查 TCP endpoint 是否可连接。

    Args:
        host: 目标主机。
        port: 目标端口。

    Returns:
        可连接返回 True，否则 False。
    """
    try:
        with socket.create_connection((host, port), timeout=0.2):
            return True
    except OSError:
        return False


def _resolve_internal_update_interval_ms() -> int:
    """从环境变量 SOURCE_SIM_POLL_SOURCE_UPDATE_HZ 计算内部更新间隔。

    Returns:
        更新间隔毫秒数，默认 1000 / 10 = 100ms。
    """
    raw_hz = os.environ.get("SOURCE_SIM_POLL_SOURCE_UPDATE_HZ", "10")

    try:
        hz = float(raw_hz)
    except ValueError:
        hz = 10.0

    if hz <= 0:
        return 1000

    return max(1, round(1000.0 / hz))


def _tail_output(text: str) -> str:
    """截取输出文本尾部用于启动诊断。

    Args:
        text: 完整的输出文本。

    Returns:
        截取的尾部文本，保留最近 _OUTPUT_TAIL_LINES 行。
    """
    if not text:
        return ""
    lines = text.splitlines()
    if len(lines) <= _OUTPUT_TAIL_LINES:
        return "\n".join(lines)
    return "\n".join(lines[-_OUTPUT_TAIL_LINES:])
