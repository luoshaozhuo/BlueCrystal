"""Unit tests for IEC 104 backend (stdout protocol parsing).

验证 IEC 104 lib60870 backend 的协议行解析、DTO 行为、
runner path resolution 及连接超时/错误/清理路径。
测试阶段：开发期验证 (unit/mock)（解析和 DTO 测试不依赖 native runner）；
connect/runner 相关测试在无 native runner 环境退化为开发期验证。
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

import pytest

from whale.shared.source.iec104.backends.base import (
    Iec104PreparedReadPlan,
    RawIec104ReadResult,
    RawWriteItemResult,
)
from whale.shared.source.iec104.backends.lib60870_backend import (
    Iec104Lib60870Backend,
    resolve_client_runner_path,
)
from whale.shared.source.iec104.reader import Iec104SourceReader


class TestIec104ParseSampleLine:
    """Parse SAMPLE protocol lines from native runner."""

    def test_parse_sp_sample(self) -> None:
        result = Iec104Lib60870Backend._parse_sample_line("SAMPLE\t1\t101\tSP\t1")
        assert result == (101, "SP", "1")

    def test_parse_short_sample(self) -> None:
        result = Iec104Lib60870Backend._parse_sample_line("SAMPLE\t1\t5\tSHORT\t550.000000")
        assert result == (5, "SHORT", "550.000000")

    def test_parse_sp_zero(self) -> None:
        result = Iec104Lib60870Backend._parse_sample_line("SAMPLE\t1\t102\tSP\t0")
        assert result == (102, "SP", "0")

    def test_parse_malformed_line(self) -> None:
        result = Iec104Lib60870Backend._parse_sample_line("SAMPLE")
        assert result is None

    def test_parse_empty_line(self) -> None:
        result = Iec104Lib60870Backend._parse_sample_line("")
        assert result is None

    def test_parse_non_sample(self) -> None:
        result = Iec104Lib60870Backend._parse_sample_line("READY")
        assert result is None


class TestIec104ParseWriteResult:
    """Parse WRITE_RESULT protocol lines."""

    def test_parse_ok(self) -> None:
        result = Iec104Lib60870Backend._parse_write_result_line(
            "WRITE_RESULT\treq-001\tok=1\tOK",
            expected_ioa=101,
            expected_command_type="C_SC_NA_1",
        )
        assert result.ioa == 101
        assert result.ok is True
        assert result.status_code == "OK"
        assert result.error_message is None

    def test_parse_failed(self) -> None:
        result = Iec104Lib60870Backend._parse_write_result_line(
            "WRITE_RESULT\treq-001\tok=0\texecution_failed",
            expected_ioa=101,
            expected_command_type="C_SC_NA_1",
        )
        assert result.ioa == 101
        assert result.ok is False
        assert result.status_code == "execution_failed"
        assert result.error_message is not None

    def test_parse_malformed(self) -> None:
        result = Iec104Lib60870Backend._parse_write_result_line(
            "NOISE",
            expected_ioa=101,
            expected_command_type="C_SC_NA_1",
        )
        assert result.ok is False
        assert result.status_code == "protocol_error"

    def test_parse_protocol_error_format(self) -> None:
        result = Iec104Lib60870Backend._parse_write_result_line(
            "WRITE_RESULT\treq-001",
            expected_ioa=102,
            expected_command_type="C_SC_NA_1",
        )
        assert result.ok is False
        assert result.status_code == "protocol_error"
        assert result.command_type == "C_SC_NA_1"


class TestIec104RawReadResult:
    """RawIec104ReadResult DTO behavior."""

    def test_ok_result(self) -> None:
        ts = datetime.now(tz=timezone.utc)
        result = RawIec104ReadResult(
            ok=True,
            values={101: ("SP", "1"), 102: ("SP", "0")},
            response_timestamp=ts,
        )
        assert result.ok is True
        assert result.values[101] == ("SP", "1")

    def test_failed_result(self) -> None:
        result = RawIec104ReadResult(
            ok=False,
            values={},
            error_reason="timeout",
        )
        assert result.ok is False
        assert result.error_reason == "timeout"


class TestIec104PreparedReadPlan:
    """Prepared read plan DTO."""

    def test_create_plan(self) -> None:
        plan = Iec104PreparedReadPlan(ioa_list=(101, 102, 103), common_addr=1)
        assert plan.ioa_list == (101, 102, 103)
        assert plan.common_addr == 1


class TestIec104RawWriteItemResult:
    """RawWriteItemResult DTO behavior."""

    def test_ok_result(self) -> None:
        result = RawWriteItemResult(
            ioa=101,
            ok=True,
            status_code="OK",
            error_message=None,
            command_type="C_SC_NA_1",
        )
        assert result.ok is True
        assert result.ioa == 101

    def test_failed_result(self) -> None:
        result = RawWriteItemResult(
            ioa=101,
            ok=False,
            status_code="timeout",
            error_message="connection failed",
            command_type="C_SC_NA_1",
        )
        assert result.ok is False
        assert result.error_message == "connection failed"


class TestIec104BackendConnectFailure:
    """connect 阶段 runner 不可用时的错误传播。"""

    @pytest.mark.asyncio
    async def test_connect_raises_when_runner_not_found(self) -> None:
        """当 native runner 二进制不存在时应抛出 RuntimeError。"""
        if os.name == "nt":
            pytest.skip("subprocess runner resolution differs on Windows")
        backend = Iec104Lib60870Backend("127.0.0.1", 2404)
        with mock.patch(
            "whale.shared.source.iec104.backends.lib60870_backend.resolve_client_runner_path",
            return_value=Path("/nonexistent/path/iec104_client_runner"),
        ):
            # 清除 allow_dev_fallback 环境变量，强制 runner 不可用
            with mock.patch.dict(os.environ, {}, clear=True):
                with pytest.raises(RuntimeError, match="does not exist"):
                    await backend.connect()

    @pytest.mark.asyncio
    async def test_connect_is_idempotent_when_already_connected(self) -> None:
        """已连接时再次 connect 应是空操作。"""
        backend = Iec104Lib60870Backend("127.0.0.1", 2404)
        backend._connected = True
        backend._runner = mock.AsyncMock()
        # 不应抛出异常或尝试再次连接
        await backend.connect()
        assert backend._connected is True


class TestIec104BackendDisconnectCleanup:
    """disconnect 清理路径测试。"""

    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected_is_safe(self) -> None:
        """未连接时 disconnect 应是安全的空操作。"""
        backend = Iec104Lib60870Backend("127.0.0.1", 2404)
        backend._connected = False
        backend._runner = None
        # 不应抛出异常
        await backend.disconnect()
        assert backend._connected is False

    @pytest.mark.asyncio
    async def test_disconnect_with_dead_runner_does_not_hang(self) -> None:
        """runner 已死时 disconnect 不应挂起。"""
        backend = Iec104Lib60870Backend("127.0.0.1", 2404)
        backend._connected = True
        dead_runner = mock.AsyncMock()
        dead_runner.returncode = -1  # 进程已终止
        dead_runner.stdin = None
        backend._runner = dead_runner
        # 不应挂起或抛出异常
        await backend.disconnect()
        assert backend._connected is False
        assert backend._runner is None

    @pytest.mark.asyncio
    async def test_async_context_manager_calls_disconnect(self) -> None:
        """async context manager 退出时应调用 disconnect。"""
        backend = Iec104Lib60870Backend("127.0.0.1", 2404)
        backend._connected = True
        backend._runner = mock.AsyncMock()
        backend._runner.returncode = None

        async with backend:
            assert backend._connected is True

        assert backend._connected is False


class TestIec104ResolveClientRunnerPath:
    """resolve_client_runner_path 行为测试。"""

    def test_returns_path_from_env_or_default(self) -> None:
        """应返回 Path 对象。"""
        path = resolve_client_runner_path()
        assert isinstance(path, Path)
        # 在有环境变量的情况下应该指向具体路径
        assert len(path.name) > 0

    def test_env_var_takes_priority(self) -> None:
        """环境变量应优先于默认路径。"""
        override = "/custom/path/iec104_client_runner"
        with mock.patch.dict(os.environ, {"WHALE_IEC104_CLIENT_RUNNER_PATH": override}):
            path = resolve_client_runner_path()
            assert path == Path(override)


class TestIec104SourceReaderFacade:
    """Iec104SourceReader facade 测试。"""

    def test_constructor_creates_backend(self) -> None:
        """构造时应创建 Iec104Lib60870Backend。"""
        reader = Iec104SourceReader(host="127.0.0.1", port=2404, common_addr=1)
        assert reader._host == "127.0.0.1"
        assert reader._port == 2404
        assert reader._common_addr == 1
        assert reader._backend is not None
        assert isinstance(reader._backend, Iec104Lib60870Backend)


class TestIec104BackendNotImplemented:
    """已验证路径与未实现路径的边界测试。"""

    def test_subscription_is_not_supported_by_adapter(self) -> None:
        """adapter 应明确拒绝订阅模式。"""
        from whale.ingest.adapters.source.iec104_source_acquisition_adapter import (
            Iec104SourceAcquisitionAdapter,
        )
        adapter = Iec104SourceAcquisitionAdapter()
        assert adapter.supports_subscription(
            execution=mock.Mock(), connection=mock.Mock(),
        ) is False

    def test_write_adapter_has_dry_run_path(self) -> None:
        """write adapter 应支持 dry_run 模式（不执行真实写入）。"""
        from whale.ingest.adapters.source.iec104_source_write_adapter import (
            Iec104SourceWriteAdapter,
        )
        adapter = Iec104SourceWriteAdapter()
        # dry_run 方法存在且可调用
        assert callable(adapter._dry_run_result)

    def test_write_adapter_has_error_result_path(self) -> None:
        """write adapter 应有错误结果构造路径。"""
        from whale.ingest.adapters.source.iec104_source_write_adapter import (
            Iec104SourceWriteAdapter,
        )
        adapter = Iec104SourceWriteAdapter()
        assert callable(adapter._error_result)
