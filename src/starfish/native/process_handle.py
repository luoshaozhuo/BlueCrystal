"""Native 子进程句柄 —— NativeProcessHandle。

提供 native runner 子进程的启动、就绪等待和安全停止生命周期管理。
子进程的创建、信号发送和资源释放均在本模块内闭环。

安全边界：
- 不得 import seahorse / whale.ingest / whale.shared.source。
- 所有操作基于 subprocess 标准库，不引入外部 runner 客户端。
"""

from __future__ import annotations

import os
import signal
import subprocess
import time

from starfish.native.runner_spec import NativeRunnerSpec


# 子进程号不存在的典型信号（跨平台兼容，不存在时用 SIGTERM）
_SECONDARY_KILL_SIGNAL: int = getattr(signal, "SIGKILL", signal.SIGTERM)


class NativeProcessHandle:
    """Native runner 子进程生命周期管理器。

    负责启动 native 二进制子进程、等待就绪信号（从 stdout/stderr 扫描）
    和优雅终止（terminate -> communicate -> kill 降级链）。

    不负责：端口分配、协议连接、二进制编译、健康探测（TCP connect 等由 facade 自行处理）。

    Attributes:
        _process: 当前活跃的子进程 Popen 对象，未启动或已停止时为 None。
    """

    def __init__(self) -> None:
        self._process: subprocess.Popen[bytes] | None = None

    def start_subprocess(
        self,
        spec: NativeRunnerSpec,
        port: int = 0,
        env: dict[str, str] | None = None,
    ) -> subprocess.Popen[bytes]:
        """启动 native runner 子进程。

        使用 spec 中定义的 binary_name 在 default_source_path 下启动子进程。
        如果 port > 0，将其作为第一个命令行参数传入（大部分 C runner 以此指定监听端口）。

        Args:
            spec: NativeRunnerSpec 实例，定义二进制路径和元信息。
            port: 监听端口号，> 0 时传给子进程作为参数。
            env: 额外环境变量 dict，会与当前 os.environ 合并。

        Returns:
            已启动的 subprocess.Popen 对象。

        Raises:
            FileNotFoundError: 二进制文件不存在。
            OSError: 启动子进程失败。
        """
        binary_path = spec.default_source_path / spec.binary_name
        if not binary_path.is_file():
            raise FileNotFoundError(f"Native runner 二进制不存在: {binary_path}")

        cmd: list[str] = [str(binary_path)]
        if port > 0:
            cmd.append(str(port))

        # 合并环境变量，调用方传入的环境变量优先级高于当前进程环境
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)

        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=merged_env,
        )
        return self._process

    def wait_for_ready(
        self,
        ready_signal: str,
        timeout: float = 10.0,
    ) -> bool:
        """等待子进程输出中就绪信号出现。

        非阻塞扫描子进程的 stdout 和 stderr，查找 ready_signal 字符串。
        在 timeout 秒内轮询，每次轮询间隔 0.1 秒。

        如果 ready_signal 为空字符串，直接返回 True（不需要等待就绪信号）。

        Args:
            ready_signal: 就绪信号字符串（如 "server started"），
                          空字符串表示不需要等待。
            timeout: 最大等待时间（秒）。默认 10 秒。

        Returns:
            True 如果在 timeout 内检测到就绪信号；
            False 如果超时、进程已退出或无就绪信号配置。
        """
        if not ready_signal:
            return True

        if self._process is None:
            return False

        deadline = time.monotonic() + timeout
        stdout_buf: list[str] = []
        stderr_buf: list[str] = []

        while time.monotonic() < deadline:
            # 检查进程是否已退出
            poll_code = self._process.poll()
            if poll_code is not None:
                # 收集最后输出再判断
                self._collect_output(stdout_buf, stderr_buf)
                combined = "".join(stdout_buf) + "".join(stderr_buf)
                if ready_signal in combined:
                    return True
                return False

            # 收集可用输出
            self._collect_output(stdout_buf, stderr_buf)
            combined = "".join(stdout_buf) + "".join(stderr_buf)
            if ready_signal in combined:
                return True

            time.sleep(0.1)

        return False

    def stop_subprocess(
        self,
        timeout: float = 5.0,
    ) -> None:
        """停止 native runner 子进程。

        使用三级降级链：
            1. terminate()（发送 SIGTERM）。
            2. communicate(timeout) 等待进程退出并收集残留输出。
            3. 如仍未退出，kill()（发送 SIGKILL）。

        所有步骤均捕获异常，确保不向调用方泄漏进程异常。
        重复调用安全（幂等）。

        Args:
            timeout: communicate 等待超时时间（秒）。默认 5 秒。
        """
        if self._process is None:
            return

        proc: subprocess.Popen[bytes] = self._process  # type narrowing

        try:
            poll_code = proc.poll()
            if poll_code is not None:
                # 进程已退出
                self._process = None
                return
        except Exception:
            pass

        # 1. terminate
        try:
            proc.terminate()
        except Exception:
            pass

        # 2. communicate 等待退出
        try:
            proc.communicate(timeout=timeout)
        except Exception:
            pass

        # 3. 仍未退出，强制 kill
        try:
            poll_code = proc.poll()
            if poll_code is None:
                proc.kill()
                proc.communicate(timeout=timeout)
        except Exception:
            pass

        self._process = None

    def _collect_output(
        self,
        stdout_buf: list[str],
        stderr_buf: list[str],
    ) -> None:
        """非阻塞收集子进程 stdout 和 stderr 中当前可读的数据。

        Args:
            stdout_buf: stdout 输出累积缓冲区（原地追加）。
            stderr_buf: stderr 输出累积缓冲区（原地追加）。
        """
        if self._process is None:
            return

        for stream, buf in [
            (self._process.stdout, stdout_buf),
            (self._process.stderr, stderr_buf),
        ]:
            if stream is None:
                continue
            try:
                # 非阻塞读取
                import os as _os_module
                fd = stream.fileno()
                _os_module.set_blocking(fd, False)
                try:
                    data = stream.read(4096)
                    if data:
                        buf.append(data.decode("utf-8", errors="replace"))
                except Exception:
                    pass
                finally:
                    _os_module.set_blocking(fd, True)
            except Exception:
                pass


__all__ = ["NativeProcessHandle"]
