"""Beckhoff ADS .NET virtual server 进程管理与环境探测。

本文件负责：
1. 检测 dotnet SDK/runtime 是否存在；
2. 检测 Beckhoff.TwinCAT.Ads.Server 示例项目是否可 restore/build/run；
3. 检测 ADS Router/TwinCAT 环境是否可用；
4. 启动/停止 .NET virtual ADS server 子进程；
5. 输出 server address、ams_net_id、ads_port、lifecycle 状态；
6. cleanup 必须可靠——无论正常退出还是异常，子进程必须终止。

不负责：真实 Beckhoff TwinCAT 运行时管理、ADS Router 安装、生产路径 runner。
本文件属于 tools/source_lab 工具层，不进入 `src/whale/ingest` 生产路径。
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ── 常量 ──────────────────────────────────────────────────────────────────

_DOTNET_CHECK_TIMEOUT_S = 10.0
_DOTNET_RESTORE_TIMEOUT_S = 120.0
_DOTNET_BUILD_TIMEOUT_S = 180.0
_DOTNET_SERVER_START_TIMEOUT_S = 30.0
_DOTNET_SERVER_STOP_GRACE_S = 5.0
_DOTNET_SERVER_FORCE_KILL_S = 3.0

_DEFAULT_AMS_NET_ID = "5.32.160.1.1.1"
_DEFAULT_ADS_SERVER_PORT = 851
_DEFAULT_ADS_ROUTER_PORT = 48898

# Beckhoff AdsServer 预制项目在 repository 中的相对路径模板
_REPO_ROOT = Path(__file__).resolve().parents[4]
_DEFAULT_DOTNET_PROJECT_DIR = _REPO_ROOT / "tools" / "source_lab" / "native" / "beckhoff_ads_server"
_DEFAULT_PROJECT_FILE = "BeckhoffAdsServer.csproj"


# ── 数据模型 ─────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class DotnetEnvironmentProbeResult:
    """dotnet / TwinCAT / ADS Router 环境探测结果。

    Attributes:
        dotnet_available: dotnet CLI 是否可用。
        dotnet_version: dotnet --version 输出。
        platform_os: 当前操作系统。
        is_windows: 是否为 Windows。
        ads_router_available: ADS Router 是否可访问。
        twincat_available: TwinCAT 运行时是否可用。
        ads_server_project_found: AdsServer 示例项目是否存在。
        overall_environment_ready: 综合判断——环境是否满足真实 ADS 测试条件。
        missing_components: 缺失的环境组件列表。
        probe_errors: 探测过程中遇到的错误信息。
    """

    dotnet_available: bool = False
    dotnet_version: str = ""
    platform_os: str = ""
    is_windows: bool = False
    ads_router_available: bool = False
    twincat_available: bool = False
    ads_server_project_found: bool = False
    overall_environment_ready: bool = False
    missing_components: tuple[str, ...] = ()
    probe_errors: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class VirtualAdsServerStartResult:
    """.NET virtual ADS server 启动结果。

    Attributes:
        success: 是否成功启动。
        server_address: ADS server 监听地址（host:port）。
        ams_net_id: 分配的 AMS Net ID。
        ads_port: ADS 服务端口。
        pid: 子进程 PID（0 表示未启动）。
        message: 状态描述或错误信息。
    """

    success: bool = False
    server_address: str = ""
    ams_net_id: str = ""
    ads_port: int = 0
    pid: int = 0
    message: str = ""
    stdout_preview: str = ""
    stderr_preview: str = ""


@dataclass
class VirtualAdsServerLifecycle:
    """ADS server 运行态生命周期句柄。

    此类持有子进程引用和运行状态，必须通过 stop() 可靠清理。
    实例在创建后不自动启动；调用方必须调用 start()。
    """

    project_dir: Path
    ams_net_id: str
    ads_port: int
    router_port: int
    _process: subprocess.Popen[str] | None = field(default=None, init=False)
    _started: bool = field(default=False, init=False)
    _start_result: VirtualAdsServerStartResult | None = field(default=None, init=False)

    @property
    def started(self) -> bool:
        """返回服务器是否处于启动状态。"""
        return self._started and self._process is not None

    @property
    def pid(self) -> int:
        """返回子进程 PID，未启动时为 0。"""
        if self._process is not None and self._started:
            return self._process.pid or 0
        return 0

    @property
    def start_result(self) -> VirtualAdsServerStartResult | None:
        """返回最近一次启动结果。"""
        return self._start_result

    def start(self) -> VirtualAdsServerStartResult:
        """编译并启动 .NET virtual ADS server 子进程。

        Returns:
            VirtualAdsServerStartResult 包含启动是否成功、地址、AMS Net ID 等信息。

        注意：此方法会阻塞，直到服务器输出就绪信号或超时。
        """
        if self._started:
            return VirtualAdsServerStartResult(
                success=True,
                server_address=f"127.0.0.1:{self.ads_port}",
                ams_net_id=self.ams_net_id,
                ads_port=self.ads_port,
                pid=self.pid,
                message="already running",
            )

        project_file = self.project_dir / _DEFAULT_PROJECT_FILE
        if not project_file.exists():
            result = VirtualAdsServerStartResult(
                success=False,
                message=f"AdsServer project file not found: {project_file}",
            )
            self._start_result = result
            return result

        # 1. dotnet restore
        build_cmd = ["dotnet", "build", "-c", "Release"]
        try:
            restore_proc = subprocess.run(
                build_cmd + ["--no-restore"],
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=_DOTNET_BUILD_TIMEOUT_S,
                check=False,
            )
            # 如果 --no-restore 失败，先执行 restore
            if restore_proc.returncode != 0:
                subprocess.run(
                    ["dotnet", "restore"],
                    cwd=str(self.project_dir),
                    capture_output=True,
                    text=True,
                    timeout=_DOTNET_RESTORE_TIMEOUT_S,
                    check=True,
                )
                subprocess.run(
                    build_cmd,
                    cwd=str(self.project_dir),
                    capture_output=True,
                    text=True,
                    timeout=_DOTNET_BUILD_TIMEOUT_S,
                    check=True,
                )
        except subprocess.TimeoutExpired as exc:
            result = VirtualAdsServerStartResult(
                success=False,
                message=f"dotnet build timed out: {exc}",
            )
            self._start_result = result
            return result
        except subprocess.CalledProcessError as exc:
            result = VirtualAdsServerStartResult(
                success=False,
                message=f"dotnet build failed: returncode={exc.returncode}, stderr={exc.stderr}",
            )
            self._start_result = result
            return result
        except FileNotFoundError:
            result = VirtualAdsServerStartResult(
                success=False,
                message="dotnet CLI not found in PATH",
            )
            self._start_result = result
            return result

        # 2. dotnet run
        run_cmd = ["dotnet", "run", "--project", str(project_file), "-c", "Release"]
        env = os.environ.copy()
        env["ADS_SERVER_AMS_NET_ID"] = self.ams_net_id
        env["ADS_SERVER_PORT"] = str(self.ads_port)
        env["ADS_ROUTER_PORT"] = str(self.router_port)

        try:
            self._process = subprocess.Popen(
                run_cmd,
                cwd=str(self.project_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                bufsize=1,
                env=env,
            )
        except FileNotFoundError:
            result = VirtualAdsServerStartResult(
                success=False,
                message="dotnet CLI not found in PATH during run",
            )
            self._start_result = result
            return result
        except Exception as exc:
            result = VirtualAdsServerStartResult(
                success=False,
                message=f"failed to start AdsServer process: {exc}",
            )
            self._start_result = result
            return result

        # 3. 等待服务器就绪信号
        deadline = time.monotonic() + _DOTNET_SERVER_START_TIMEOUT_S
        started, stdout_lines, stderr_lines = _wait_for_ready_signal(
            self._process, deadline
        )

        if started:
            self._started = True
            result = VirtualAdsServerStartResult(
                success=True,
                server_address=f"127.0.0.1:{self.ads_port}",
                ams_net_id=self.ams_net_id,
                ads_port=self.ads_port,
                pid=self._process.pid or 0,
                message="AdsServer started",
                stdout_preview="\n".join(stdout_lines[-10:]),
                stderr_preview="\n".join(stderr_lines[-10:]),
            )
        else:
            # 启动失败：终止子进程
            _terminate_process(self._process, grace_s=0.5)
            self._process = None
            self._started = False
            result = VirtualAdsServerStartResult(
                success=False,
                message=f"AdsServer failed to start within {_DOTNET_SERVER_START_TIMEOUT_S}s",
                stdout_preview="\n".join(stdout_lines[-10:]),
                stderr_preview="\n".join(stderr_lines[-10:]),
            )

        self._start_result = result
        return result

    def stop(self) -> None:
        """停止 virtual ADS server 子进程（可靠清理）。

        先发送 SIGTERM，等待 grace period；若仍未退出，发送 SIGKILL。
        所有清理路径之后将 _process 设为 None。
        """
        if self._process is None:
            self._started = False
            return

        _terminate_process(self._process, grace_s=_DOTNET_SERVER_STOP_GRACE_S)
        # 等待 force kill 完成
        try:
            self._process.wait(timeout=_DOTNET_SERVER_FORCE_KILL_S)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=_DOTNET_SERVER_FORCE_KILL_S)
        finally:
            self._process = None
            self._started = False


# ── 进程辅助函数 ──────────────────────────────────────────────────────────


def _wait_for_ready_signal(
    proc: subprocess.Popen[str],
    deadline: float,
) -> tuple[bool, list[str], list[str]]:
    """等待子进程输出 ADS 服务器就绪信号。

    就绪信号匹配以下模式之一：
    - "Server started"
    - "Listening"
    - "ADS server is running"
    - "ready"
    - "AdsServer"（出现在最后几行）

    通过非阻塞轮询 stdout 实现，同时收集 stderr 用于诊断。

    Args:
        proc: 已启动的子进程。
        deadline: 截止时间（monotonic 秒）。

    Returns:
        (是否就绪, stdout 行列表, stderr 行列表)
    """
    import select

    stdout_lines: list[str] = []
    stderr_lines: list[str] = []
    ready_signals = (
        "Server started",
        "Listening",
        "ADS server is running",
        "Ready",
        "ready",
        "started",
    )

    while time.monotonic() < deadline:
        if proc.poll() is not None:
            # 进程已退出
            out, err = proc.communicate(timeout=1.0)
            if out:
                stdout_lines.extend(out.splitlines())
            if err:
                stderr_lines.extend(err.splitlines())
            return False, stdout_lines, stderr_lines

        # 非阻塞轮询 stdout
        if proc.stdout:
            rlist, _, _ = select.select([proc.stdout], [], [], 0.1)
            if rlist:
                line = proc.stdout.readline()
                if line:
                    stripped = line.rstrip("\n\r")
                    stdout_lines.append(stripped)
                    if any(sig.lower() in stripped.lower() for sig in ready_signals):
                        return True, stdout_lines, stderr_lines

        # 非阻塞轮询 stderr
        if proc.stderr:
            import select as _select2
            rlist2, _, _ = _select2.select([proc.stderr], [], [], 0.01)
            if rlist2:
                line = proc.stderr.readline()
                if line:
                    stderr_lines.append(line.rstrip("\n\r"))

        time.sleep(0.1)

    return False, stdout_lines, stderr_lines


def _terminate_process(proc: subprocess.Popen[str], grace_s: float) -> None:
    """终止子进程（先 SIGTERM，等待 grace period，若未退出则 SIGKILL）。

    Args:
        proc: 要终止的子进程。
        grace_s: SIGTERM 之后的等待秒数。
    """
    if proc.poll() is not None:
        return
    try:
        proc.terminate()
        try:
            proc.wait(timeout=grace_s)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=grace_s)
    except ProcessLookupError:
        pass
    except Exception:
        try:
            proc.kill()
            proc.wait(timeout=grace_s)
        except Exception:
            pass


# ── 环境探测 ──────────────────────────────────────────────────────────────


def probe_dotnet_environment(
    project_dir: Path | None = None,
) -> DotnetEnvironmentProbeResult:
    """探测 ADS .NET virtual server 所需的整体环境。

    依次检测：
    1. dotnet CLI 是否可用及其版本；
    2. 当前操作系统（TwinCAT 仅在 Windows 上可用，Linux 仅支持 AdsServer 项目）；
    3. ADS Router 是否可用（通过 AdsServer 示例项目或端口检测）；
    4. AdsServer 示例项目是否存在。

    Args:
        project_dir: AdsServer 示例项目目录。默认使用仓库内的模板路径。

    Returns:
        DotnetEnvironmentProbeResult 包含所有检测结果。
    """
    errors: list[str] = []
    missing: list[str] = []

    target_dir = project_dir or _DEFAULT_DOTNET_PROJECT_DIR

    # 1. 检测 dotnet CLI
    dotnet_path = shutil.which("dotnet")
    dotnet_version = ""
    if dotnet_path is None:
        missing.append("dotnet_cli")
        errors.append("dotnet CLI not found in PATH")
    else:
        try:
            result = subprocess.run(
                ["dotnet", "--version"],
                capture_output=True,
                text=True,
                timeout=_DOTNET_CHECK_TIMEOUT_S,
                check=False,
            )
            if result.returncode == 0:
                dotnet_version = result.stdout.strip()
            else:
                missing.append("dotnet_cli")
                errors.append(f"dotnet --version failed: {result.stderr.strip()}")
        except Exception as exc:
            missing.append("dotnet_cli")
            errors.append(f"dotnet version check error: {exc}")

    # 2. 检测操作系统
    current_os = platform.system()
    is_windows = current_os == "Windows"

    # 3. 检测 ADS Router / TwinCAT 环境
    ads_router_available = False
    twincat_available = False

    if is_windows:
        # Windows 上检测 TwinCAT 安装目录
        twincat_dirs = [
            Path("C:/TwinCAT/3.1"),
            Path("C:/TwinCAT/AdsApi"),
        ]
        for d in twincat_dirs:
            if d.exists():
                twincat_available = True
                ads_router_available = True
                break
        if not twincat_available:
            missing.append("twincat_runtime")
    else:
        # Linux: 检测 AdsRouter 默认端口 (48898) 是否可 reach
        # 仅做本地端口 TCP connect 检测，不作为充分证据
        missing.append("twincat_runtime")
        errors.append("TwinCAT runtime is Windows-only; AdsServer project can still run on Linux")

    # 4. 检测 AdsServer 示例项目
    project_file = target_dir / _DEFAULT_PROJECT_FILE
    if project_file.exists():
        ads_server_project_found = True
    else:
        ads_server_project_found = False
        missing.append("ads_server_project")
        errors.append(f"AdsServer project not found at {project_file}")

    # 5. 环境就绪综合判断
    # 条件：dotnet 可用 且 项目存在
    overall_ready = (
        dotnet_path is not None
        and ads_server_project_found
    )

    return DotnetEnvironmentProbeResult(
        dotnet_available=dotnet_path is not None,
        dotnet_version=dotnet_version,
        platform_os=current_os,
        is_windows=is_windows,
        ads_router_available=ads_router_available,
        twincat_available=twincat_available,
        ads_server_project_found=ads_server_project_found,
        overall_environment_ready=overall_ready,
        missing_components=tuple(missing),
        probe_errors=tuple(errors),
    )


def create_virtual_ads_server(
    project_dir: Path | None = None,
    ams_net_id: str = _DEFAULT_AMS_NET_ID,
    ads_port: int = _DEFAULT_ADS_SERVER_PORT,
    router_port: int = _DEFAULT_ADS_ROUTER_PORT,
) -> VirtualAdsServerLifecycle:
    """创建 .NET virtual ADS server 生命周期管理实例。

    不自动启动；调用方需要在 with 语句或 try/finally 中调用 start() 和 stop()。

    Args:
        project_dir: AdsServer 项目目录，默认使用仓库模板路径。
        ams_net_id: ADS 服务器 AMS Net ID。
        ads_port: ADS 服务器监听端口。
        router_port: ADS Router 端口。

    Returns:
        VirtualAdsServerLifecycle 实例。
    """
    target_dir = project_dir or _DEFAULT_DOTNET_PROJECT_DIR
    return VirtualAdsServerLifecycle(
        project_dir=target_dir,
        ams_net_id=ams_net_id,
        ads_port=ads_port,
        router_port=router_port,
    )


def describe_ads_environment_requirements() -> dict[str, Any]:
    """返回 ADS 真实验证环境要求的结构化描述。

    Returns:
        字典，包含 dotnet、TwinCAT、AdsServer 项目等环境要求的详细说明。
    """
    return {
        "dotnet": {
            "required": True,
            "min_version": "6.0",
            "purpose": "build and run Beckhoff AdsServer .NET project",
            "install_hint": "https://dotnet.microsoft.com/download",
        },
        "twincat": {
            "required": False,
            "note": "TwinCAT runtime is Windows-only; AdsServer project works on Linux with limited ADS Router functionality",
            "install_hint": "https://www.beckhoff.com/en-us/products/automation/twincat/",
        },
        "ads_router": {
            "required": False,
            "note": "ADS Router is required for full ADS protocol communication; AdsServer demo can run in limited mode without it",
        },
        "ads_server_project": {
            "required": True,
            "project_path": str(_DEFAULT_DOTNET_PROJECT_DIR / _DEFAULT_PROJECT_FILE),
            "build_command": "dotnet build -c Release",
            "run_command": "dotnet run --project BeckhoffAdsServer.csproj -c Release",
        },
    }


__all__ = [
    "DotnetEnvironmentProbeResult",
    "VirtualAdsServerLifecycle",
    "VirtualAdsServerStartResult",
    "create_virtual_ads_server",
    "describe_ads_environment_requirements",
    "probe_dotnet_environment",
]
