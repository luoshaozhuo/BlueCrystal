"""Starfish Native Runner 管理框架测试（Round 10 新增）。

验证 native runner 探查、规格定义和子进程生命周期管理：
1. NativeRunnerSpec dataclass 构造与默认值。
2. probe_native_runner 存在/不存在/太小/不可读场景。
3. NativeProcessHandle start_subprocess / wait_for_ready / stop_subprocess。

测试阶段：开发期验证 (P1)。
使用的替身：Python 临时脚本模拟 binary（echo 输出后 sleep），
  外部依赖：subprocess 标准库（无外部二进制）。
  不能证明：真实 C runner 行为、协议 server 启动、网络连通性。
  NOT_RUN 条件：无。
"""

from __future__ import annotations

import tempfile
import time
from pathlib import Path

import pytest

from starfish.native.runner_spec import NativeRunnerSpec
from starfish.native.runner_probe import probe_native_runner
from starfish.native.process_handle import NativeProcessHandle


# ── NativeRunnerSpec 测试 ──────────────────────────────────────────────────────


class TestNativeRunnerSpec:
    """NativeRunnerSpec dataclass 构造与默认值测试。"""

    def test_default_values(self) -> None:
        """默认值应正确。"""
        spec = NativeRunnerSpec()
        assert spec.protocol == ""
        assert spec.binary_name == ""
        assert spec.default_source_path == Path(".")
        assert spec.ready_signal == ""
        assert spec.health_port == 0
        assert spec.min_binary_size == 1024

    def test_construction_with_values(self) -> None:
        """传入参数应正确保存。"""
        spec = NativeRunnerSpec(
            protocol="OPC_UA",
            binary_name="opcua_server",
            default_source_path=Path("/tmp/build"),
            ready_signal="server started",
            health_port=4840,
            min_binary_size=2048,
        )
        assert spec.protocol == "OPC_UA"
        assert spec.binary_name == "opcua_server"
        assert spec.default_source_path == Path("/tmp/build")
        assert spec.ready_signal == "server started"
        assert spec.health_port == 4840
        assert spec.min_binary_size == 2048


# ── probe_native_runner 测试 ───────────────────────────────────────────────────


class TestProbeNativeRunner:
    """probe_native_runner 探查测试。"""

    def test_probe_existing_file_sufficient_size(self) -> None:
        """存在的足够大且可读文件应返回 True。"""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            binary = tmp_path / "test_runner"
            binary.write_bytes(b"x" * 2000)
            binary.chmod(0o755)

            spec = NativeRunnerSpec(
                binary_name="test_runner",
                default_source_path=tmp_path,
                min_binary_size=1024,
            )
            ok, reason = probe_native_runner(spec)
            assert ok is True
            assert "可用" in reason

    def test_probe_directory_not_exist(self) -> None:
        """目录不存在应返回 (False, reason)。"""
        spec = NativeRunnerSpec(
            binary_name="nonexistent",
            default_source_path=Path("/tmp/nonexistent_dir_xyz"),
            min_binary_size=1024,
        )
        ok, reason = probe_native_runner(spec)
        assert ok is False
        assert "不存在" in reason

    def test_probe_file_not_exist(self) -> None:
        """文件不存在应返回 (False, reason)。"""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            spec = NativeRunnerSpec(
                binary_name="nonexistent_file",
                default_source_path=tmp_path,
                min_binary_size=1024,
            )
            ok, reason = probe_native_runner(spec)
            assert ok is False
            assert "不存在" in reason

    def test_probe_path_not_directory(self) -> None:
        """default_source_path 指向文件而非目录应返回失败。"""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            not_a_dir = tmp_path / "not_a_dir"
            not_a_dir.write_text("hello")
            spec = NativeRunnerSpec(
                binary_name="any",
                default_source_path=not_a_dir,
                min_binary_size=1024,
            )
            ok, reason = probe_native_runner(spec)
            assert ok is False
            assert "不是目录" in reason

    def test_probe_file_too_small(self) -> None:
        """文件小于 min_binary_size 应返回 (False, reason)。"""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            binary = tmp_path / "small_runner"
            binary.write_bytes(b"x" * 100)
            binary.chmod(0o755)

            spec = NativeRunnerSpec(
                binary_name="small_runner",
                default_source_path=tmp_path,
                min_binary_size=1024,
            )
            ok, reason = probe_native_runner(spec)
            assert ok is False
            assert "过小" in reason

    def test_probe_file_exactly_min_size(self) -> None:
        """文件大小等于 min_binary_size 应视为可接受。"""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            binary = tmp_path / "exact_runner"
            binary.write_bytes(b"x" * 1024)
            binary.chmod(0o755)

            spec = NativeRunnerSpec(
                binary_name="exact_runner",
                default_source_path=tmp_path,
                min_binary_size=1024,
            )
            ok, reason = probe_native_runner(spec)
            assert ok is True

    def test_probe_file_not_readable(self) -> None:
        """文件不可读应返回 (False, reason)。"""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            binary = tmp_path / "unreadable_runner"
            binary.write_bytes(b"x" * 2000)
            binary.chmod(0o000)

            spec = NativeRunnerSpec(
                binary_name="unreadable_runner",
                default_source_path=tmp_path,
                min_binary_size=1024,
            )
            ok, reason = probe_native_runner(spec)
            assert ok is False
            assert "不可读" in reason

            # cleanup: restore permission so tempdir can be cleaned
            binary.chmod(0o644)


# ── NativeProcessHandle 测试 ───────────────────────────────────────────────────


class TestNativeProcessHandleStartStop:
    """NativeProcessHandle 子进程启动与停止测试。"""

    def test_start_subprocess(self) -> None:
        """使用 Python 脚本作为 mock binary，验证子进程启动成功。"""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            script = tmp_path / "mock_runner.py"
            script.write_text("""\
#!/usr/bin/env python3
import sys, time
print("ready", flush=True)
sys.stdout.flush()
time.sleep(30)
""")
            script.chmod(0o755)

            spec = NativeRunnerSpec(
                binary_name="mock_runner.py",
                default_source_path=tmp_path,
                min_binary_size=10,
            )

            handle = NativeProcessHandle()
            proc = handle.start_subprocess(spec, port=0)
            assert proc is not None
            assert proc.poll() is None

            handle.stop_subprocess(timeout=1.0)
            assert handle._process is None

    def test_start_subprocess_with_port(self) -> None:
        """传入 port > 0 时应作为参数传给子进程。"""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            script = tmp_path / "echo_args.py"
            script.write_text("""\
#!/usr/bin/env python3
import sys
print(" ".join(sys.argv[1:]), flush=True)
""")
            script.chmod(0o755)

            spec = NativeRunnerSpec(
                binary_name="echo_args.py",
                default_source_path=tmp_path,
                min_binary_size=10,
            )

            handle = NativeProcessHandle()
            proc = handle.start_subprocess(spec, port=2404)

            # 等待进程退出并读取输出
            deadline = time.monotonic() + 3.0
            stdout_data = b""
            while time.monotonic() < deadline:
                if proc.poll() is not None:
                    stdout_data = proc.stdout.read() if proc.stdout else b""
                    break
                time.sleep(0.1)
            else:
                handle.stop_subprocess(timeout=0.5)
                stdout_data = proc.stdout.read() if proc.stdout else b""

            output = stdout_data.decode("utf-8", errors="replace").strip()
            assert "2404" in output, f"端口未传递: output={output!r}"

            handle.stop_subprocess(timeout=0.5)

    def test_start_subprocess_file_not_found(self) -> None:
        """二进制不存在时应抛出 FileNotFoundError。"""
        spec = NativeRunnerSpec(
            binary_name="definitely_not_exist_xyz",
            default_source_path=Path("/tmp"),
            min_binary_size=1024,
        )
        handle = NativeProcessHandle()
        with pytest.raises(FileNotFoundError):
            handle.start_subprocess(spec)

    def test_wait_for_ready_with_signal(self) -> None:
        """ready_signal 出现时 wait_for_ready 应返回 True。"""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            script = tmp_path / "ready_runner.py"
            script.write_text("""\
#!/usr/bin/env python3
import sys, time
print("initializing...", flush=True)
time.sleep(0.3)
print("SERVER_READY", flush=True)
time.sleep(10)
""")
            script.chmod(0o755)

            spec = NativeRunnerSpec(
                binary_name="ready_runner.py",
                default_source_path=tmp_path,
                ready_signal="SERVER_READY",
                min_binary_size=10,
            )

            handle = NativeProcessHandle()
            handle.start_subprocess(spec)

            ready = handle.wait_for_ready("SERVER_READY", timeout=5.0)
            assert ready is True

            handle.stop_subprocess(timeout=0.5)

    def test_wait_for_ready_timeout(self) -> None:
        """ready_signal 始终不出现时 wait_for_ready 应返回 False。"""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            script = tmp_path / "slow_runner.py"
            script.write_text("""\
#!/usr/bin/env python3
import time
time.sleep(20)
""")
            script.chmod(0o755)

            spec = NativeRunnerSpec(
                binary_name="slow_runner.py",
                default_source_path=tmp_path,
                ready_signal="NEVER_APPEARS",
                min_binary_size=10,
            )

            handle = NativeProcessHandle()
            handle.start_subprocess(spec)

            ready = handle.wait_for_ready("NEVER_APPEARS", timeout=1.0)
            assert ready is False

            handle.stop_subprocess(timeout=0.5)

    def test_wait_for_ready_empty_signal(self) -> None:
        """空 ready_signal 时 wait_for_ready 应直接返回 True。"""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            script = tmp_path / "no_signal_runner.py"
            script.write_text("""\
#!/usr/bin/env python3
import time
time.sleep(5)
""")
            script.chmod(0o755)

            spec = NativeRunnerSpec(
                binary_name="no_signal_runner.py",
                default_source_path=tmp_path,
                min_binary_size=10,
            )

            handle = NativeProcessHandle()
            handle.start_subprocess(spec)
            ready = handle.wait_for_ready("", timeout=1.0)
            assert ready is True

            handle.stop_subprocess(timeout=0.5)

    def test_wait_for_ready_no_process(self) -> None:
        """未启动子进程时 wait_for_ready 应返回 False。"""
        handle = NativeProcessHandle()
        ready = handle.wait_for_ready("any", timeout=0.5)
        assert ready is False

    def test_stop_subprocess_idempotent(self) -> None:
        """重复 stop_subprocess 应为幂等。"""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            script = tmp_path / "long_runner.py"
            script.write_text("""\
#!/usr/bin/env python3
import time
print("started", flush=True)
time.sleep(60)
""")
            script.chmod(0o755)

            spec = NativeRunnerSpec(
                binary_name="long_runner.py",
                default_source_path=tmp_path,
                min_binary_size=10,
            )

            handle = NativeProcessHandle()
            handle.start_subprocess(spec)
            handle.stop_subprocess(timeout=0.5)
            handle.stop_subprocess(timeout=0.5)

    def test_stop_subprocess_when_already_exited(self) -> None:
        """进程已退出时 stop_subprocess 应安全处理。"""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            script = tmp_path / "quick_runner.py"
            script.write_text("""\
#!/usr/bin/env python3
print("done", flush=True)
""")
            script.chmod(0o755)

            spec = NativeRunnerSpec(
                binary_name="quick_runner.py",
                default_source_path=tmp_path,
                min_binary_size=10,
            )

            handle = NativeProcessHandle()
            handle.start_subprocess(spec)
            time.sleep(0.5)
            handle.stop_subprocess(timeout=1.0)


# ── 集成测试 ──────────────────────────────────────────────────────────────────


class TestNativeRunnerIntegration:
    """Native runner 框架组合使用测试。"""

    def test_probe_then_start_then_stop(self) -> None:
        """probe 通过后启动子进程并正确停止。"""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            script = tmp_path / "integ_runner.py"
            script.write_text("""\
#!/usr/bin/env python3
import sys, time
print("INTEG_READY", flush=True)
sys.stdout.flush()
time.sleep(30)
""")
            script.chmod(0o755)

            spec = NativeRunnerSpec(
                binary_name="integ_runner.py",
                default_source_path=tmp_path,
                ready_signal="INTEG_READY",
                min_binary_size=10,
            )

            # 1. probe
            ok, reason = probe_native_runner(spec)
            assert ok is True, f"probe 失败: {reason}"

            # 2. start
            handle = NativeProcessHandle()
            proc = handle.start_subprocess(spec)
            assert proc.poll() is None

            # 3. wait_for_ready
            ready = handle.wait_for_ready("INTEG_READY", timeout=5.0)
            assert ready is True

            # 4. stop
            handle.stop_subprocess(timeout=1.0)
            assert handle._process is None
