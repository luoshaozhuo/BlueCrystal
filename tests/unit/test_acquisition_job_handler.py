"""AcquisitionJobHandler 单元测试。

测试 handler 从 job.config_json 构造 SourceAcquisitionRequest
并调用 SourceAcquisitionUseCase 的行为。

覆盖：
1. config_json 正确映射到 SourceAcquisitionRequest
2. handler 调用 use case
3. 异常向上传播
4. 缺少必要字段时抛出 ValueError
5. _build_request_from_config 格式校验
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from whale.ingest.runtime.handlers import AcquisitionJobHandler
from whale.ingest.usecases.dtos.source_acquisition_request import (
    SourceAcquisitionRequest,
)
from whale.shared.persistence.orm.ingest_runtime import IngestRuntimeJob


class _FakeAcquisitionUseCase:
    """记录最后一次调用的假 use case。"""

    def __init__(self) -> None:
        self.last_request: SourceAcquisitionRequest | None = None
        self.call_count: int = 0

    async def start(self, request: SourceAcquisitionRequest) -> object:
        self.last_request = request
        self.call_count += 1
        return None


class _RaisingUseCase:
    """总是抛出异常。"""

    async def start(self, request: SourceAcquisitionRequest) -> None:
        raise RuntimeError("simulated use case failure")


def _make_job(config: dict[str, object]) -> MagicMock:
    """构建模拟 IngestRuntimeJob。"""
    job = MagicMock(spec=IngestRuntimeJob)
    job.job_id = config.get("request_id", "job-1")
    job.job_type = "acquisition"
    job.config_json = config
    return job


def _make_minimal_config() -> dict[str, object]:
    """最小有效 config_json。"""
    return {
        "request_id": "req-001",
        "task_id": 1,
        "execution": {
            "protocol": "opcua",
            "transport": "tcp",
            "acquisition_mode": "READ",
        },
        "connections": [
            {
                "host": "127.0.0.1",
                "port": 4840,
                "ied_name": "IED1",
                "ld_name": "LD1",
            },
        ],
        "items": [
            {"key": "point1", "profile_item_id": 1, "relative_path": "s=test.value"},
        ],
    }


class TestAcquisitionJobHandler:
    """AcquisitionJobHandler 行为测试。"""

    def test_config_json_mapped_to_request(self) -> None:
        """config_json 各字段正确映射到 SourceAcquisitionRequest。"""
        fake_uc = _FakeAcquisitionUseCase()
        handler = AcquisitionJobHandler(fake_uc)
        job = _make_job(_make_minimal_config())
        handler.execute(job)

        assert fake_uc.call_count == 1
        req = fake_uc.last_request
        assert req is not None
        assert req.request_id == "req-001"
        assert req.task_id == 1
        assert req.execution.protocol == "opcua"
        assert req.execution.transport == "tcp"
        assert req.execution.acquisition_mode == "READ"
        assert len(req.connections) == 1
        assert req.connections[0].host == "127.0.0.1"
        assert req.connections[0].port == 4840
        assert len(req.items) == 1
        assert req.items[0].key == "point1"

    def test_handler_calls_use_case(self) -> None:
        """handler.execute 必须调用 use_case.start()。"""
        fake_uc = _FakeAcquisitionUseCase()
        handler = AcquisitionJobHandler(fake_uc)
        job = _make_job(_make_minimal_config())
        handler.execute(job)

        assert fake_uc.call_count == 1

    def test_handler_propagates_use_case_exception(self) -> None:
        """use case 抛出异常 → handler 向上传播。"""
        handler = AcquisitionJobHandler(_RaisingUseCase())
        job = _make_job(_make_minimal_config())
        with pytest.raises(RuntimeError, match="simulated use case failure"):
            handler.execute(job)

    def test_missing_execution_raises_value_error(self) -> None:
        """config_json 缺少 execution 字段 → ValueError。"""
        handler = AcquisitionJobHandler(_FakeAcquisitionUseCase())
        config = _make_minimal_config()
        del config["execution"]
        job = _make_job(config)
        with pytest.raises(ValueError, match="execution is required"):
            handler.execute(job)

    def test_missing_connections_raises_value_error(self) -> None:
        """config_json 缺少 connections 字段 → ValueError。"""
        handler = AcquisitionJobHandler(_FakeAcquisitionUseCase())
        config = _make_minimal_config()
        del config["connections"]
        job = _make_job(config)
        with pytest.raises(ValueError, match="connections is required"):
            handler.execute(job)

    def test_missing_items_raises_value_error(self) -> None:
        """config_json 缺少 items 字段 → ValueError。"""
        handler = AcquisitionJobHandler(_FakeAcquisitionUseCase())
        config = _make_minimal_config()
        del config["items"]
        job = _make_job(config)
        with pytest.raises(ValueError, match="items is required"):
            handler.execute(job)

    def test_invalid_execution_type_raises_value_error(self) -> None:
        """execution 不是 dict → ValueError。"""
        handler = AcquisitionJobHandler(_FakeAcquisitionUseCase())
        config = _make_minimal_config()
        config["execution"] = "not_a_dict"
        job = _make_job(config)
        with pytest.raises(ValueError, match="execution is required and must be a dict"):
            handler.execute(job)

    def test_default_values_applied(self) -> None:
        """缺少可选字段时使用默认值。"""
        fake_uc = _FakeAcquisitionUseCase()
        handler = AcquisitionJobHandler(fake_uc)
        config: dict[str, object] = {
            "request_id": "req-default",
            "task_id": 1,
            "execution": {
                "protocol": "modbus_tcp",
                "transport": "tcp",
            },
            "connections": [
                {"host": "10.0.0.1", "port": 502},
            ],
            "items": [
                {"key": "r1", "relative_path": "40001"},
            ],
        }
        job = _make_job(config)
        handler.execute(job)

        req = fake_uc.last_request
        assert req is not None
        # 默认值
        assert req.execution.acquisition_mode == "READ"
        assert req.execution.interval_ms == 5000
        assert req.execution.request_timeout_ms == 5000
        # connections 默认值
        assert req.connections[0].ied_name == "IED1"
        assert req.connections[0].ld_name == "LD1"
        # items 默认值
        assert req.items[0].profile_item_id == 1
