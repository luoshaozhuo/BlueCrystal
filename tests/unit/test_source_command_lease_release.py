"""QA-2: SourceCommandUseCase 异常路径 lease release 测试。

验证 precheck 失败、write 失败、readback 不匹配三种异常路径下，
write lease 都通过 finally 正确释放。现有测试使用纯 mock 不覆盖这些路径。
"""

from __future__ import annotations

import asyncio
import os

import pytest

from whale.ingest.adapters.source.static_source_write_port_registry import (
    StaticSourceWritePortRegistry,
)
from whale.ingest.ports.runtime.write_lease_port import (
    WriteLeaseDecisionData,
    WriteLeasePort,
)
from whale.ingest.ports.source.source_write_port import SourceWritePort
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.ingest.usecases.dtos.source_write_request import (
    SourceWriteExecutionOptions,
    SourceWriteItemData,
    SourceWriteRequest,
)
from whale.ingest.usecases.dtos.source_write_result import (
    SourceWriteItemResult,
    SourceWriteResult,
)
from whale.ingest.usecases.source_command_use_case import SourceCommandUseCase


class _ReleaseTrackingLease(WriteLeasePort):
    """记录 acquire/release 调用次数的 test lease port。"""

    def __init__(self) -> None:
        self.acquire_count = 0
        self.release_count = 0
        self._allowed = True

    def acquire(
        self,
        **kwargs,
    ) -> WriteLeaseDecisionData:
        self.acquire_count += 1
        return WriteLeaseDecisionData(
            allowed=self._allowed,
            result="ALLOW",
            reason_code=None,
            fencing_token=1,
        )

    def renew(self, **kwargs) -> WriteLeaseDecisionData:
        return WriteLeaseDecisionData(
            allowed=True, result="ALLOW", reason_code=None, fencing_token=1,
        )

    def validate(self, **kwargs) -> WriteLeaseDecisionData:
        return WriteLeaseDecisionData(
            allowed=True, result="ALLOW", reason_code=None, fencing_token=1,
        )

    def release(self, **kwargs) -> None:
        self.release_count += 1


class _PrecheckFailingPort(SourceWritePort):
    """precheck 返回错误的 write port。"""

    async def write(self, execution, connection, items):
        return SourceWriteResult(
            request_id="req-1", command_id=None, dry_run=False,
            success_count=0, failure_count=1, results=[],
        )

    def precheck(self, execution, connection, items):
        return "precheck failed: device not ready"


class _WriteFailingPort(SourceWritePort):
    """write() 抛出异常的 write port。"""

    async def write(self, execution, connection, items):
        raise RuntimeError("write failed: connection timeout")


class _ReadbackMismatchPort(SourceWritePort):
    """write() 成功但 readback 不匹配的 write port。"""

    async def write(self, execution, connection, items):
        return SourceWriteResult(
            request_id="req-1", command_id="cmd-1", dry_run=False,
            success_count=1, failure_count=0,
            results=[
                SourceWriteItemResult(
                    key="k1", node_id="n1", ok=True, status_code="GOOD",
                ),
            ],
        )

    def readback(self, execution, connection, items, write_result):
        del execution, connection, items, write_result
        return {"n1": "0.0"}  # 写入时 value="1.0"，返回 "0.0"


def _request() -> SourceWriteRequest:
    return SourceWriteRequest(
        request_id="req-1",
        command_id="cmd-1",
        trace_id="trace-1",
        execution=SourceWriteExecutionOptions(
            protocol="opcua", transport="tcp", actor="tester",
            params={"require_readback": "true"},
        ),
        connections=[
            SourceConnectionData(
                host="127.0.0.1", port=4840,
                ied_name="IED1", ld_name="LD1",
                namespace_uri="",
            ),
        ],
        items=[
            SourceWriteItemData(key="k1", node_id="n1", value_type="double", value="1.0"),
        ],
    )


def test_release_called_on_precheck_failure() -> None:
    """precheck 失败后 lease.release 应被调用。"""
    os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"
    lease = _ReleaseTrackingLease()
    use_case = SourceCommandUseCase(
        write_port_registry=StaticSourceWritePortRegistry(
            {"opcua": _PrecheckFailingPort()},
        ),
        write_lease_port=lease,
    )

    with pytest.raises(RuntimeError, match="precheck failed"):
        asyncio.run(use_case.execute(_request()))

    # lease.acquire 被调用过，release 也应对等调用
    assert lease.acquire_count == 1
    assert lease.release_count == 1
    os.environ.pop("WHALE_INGEST_SOURCE_WRITE_ENABLED", None)


def test_release_called_on_write_failure() -> None:
    """write() 抛出异常后 lease.release 应被调用。"""
    os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"
    lease = _ReleaseTrackingLease()
    use_case = SourceCommandUseCase(
        write_port_registry=StaticSourceWritePortRegistry(
            {"opcua": _WriteFailingPort()},
        ),
        write_lease_port=lease,
    )

    with pytest.raises(RuntimeError, match="write failed"):
        asyncio.run(use_case.execute(_request()))

    assert lease.acquire_count == 1
    assert lease.release_count == 1
    os.environ.pop("WHALE_INGEST_SOURCE_WRITE_ENABLED", None)


def test_release_called_on_readback_mismatch() -> None:
    """readback 不匹配后 lease.release 应被调用。"""
    os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"
    lease = _ReleaseTrackingLease()
    use_case = SourceCommandUseCase(
        write_port_registry=StaticSourceWritePortRegistry(
            {"opcua": _ReadbackMismatchPort()},
        ),
        write_lease_port=lease,
    )

    with pytest.raises(RuntimeError, match="readback"):
        asyncio.run(use_case.execute(_request()))

    assert lease.acquire_count == 1
    assert lease.release_count == 1
    os.environ.pop("WHALE_INGEST_SOURCE_WRITE_ENABLED", None)


def test_success_path_releases_lease() -> None:
    """正常执行路径下 lease 也应正确释放。"""
    os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"
    lease = _ReleaseTrackingLease()

    class _OkPort(SourceWritePort):
        async def write(self, execution, connection, items):
            return SourceWriteResult(
                request_id="req-1", command_id=None, dry_run=False,
                success_count=1, failure_count=0, results=[],
            )

    use_case = SourceCommandUseCase(
        write_port_registry=StaticSourceWritePortRegistry({"opcua": _OkPort()}),
        write_lease_port=lease,
    )
    result = asyncio.run(use_case.execute(_request()))
    assert result is not None
    assert lease.acquire_count == 1
    assert lease.release_count == 1
    os.environ.pop("WHALE_INGEST_SOURCE_WRITE_ENABLED", None)


# ── 协议级 readback E2E contract 测试 (Task C) ─────────────────────────
#
# 以下测试验证 SourceCommandUseCase 的 readback 编排逻辑。
# 注意：这些测试使用模拟 SourceWritePort，不涉及真实 native runner 或真实设备。
# 当生产 adapter 实现 readback() 后，应由 Starfish facade 补充真实 E2E 验证。
#
# 已知差距（Gap）：
# 1. 当前生产 adapter（OpcUaSourceWriteAdapter / ModbusSourceWriteAdapter /
#    Iec61850MmsSourceWriteAdapter）均未实现 readback() 方法。
# 2. 真实设备 readback E2E 测试需要运行中的 IED/simulator + 完整写入再读取流程，
#    当前环境无法覆盖，需在部署环境中通过集成测试验证。
# 3. 双节点写入冲突 E2E 测试需要两套 WorkerRuntime 实例 + 共享数据库，
#    当前单元测试和 source_lab 测试均未覆盖此场景。
#    验证脚本见 tests/integration/test_ingest_prodlike_worker_failover.py。


def test_readback_confirmed_on_match() -> None:
    """write 成功且 readback 值匹配 → SUCCESS 并包含 readback=confirmed 属性。"""
    os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"

    class _ReadbackOkPort(SourceWritePort):
        """write 成功且 readback 返回值匹配的模拟 adapter。"""

        async def write(self, execution, connection, items):
            return SourceWriteResult(
                request_id="req-rb-ok", command_id="cmd-rb-ok", dry_run=False,
                success_count=1, failure_count=0,
                results=[
                    SourceWriteItemResult(
                        key="k1", node_id="n1", ok=True, status_code="GOOD",
                    ),
                ],
            )

        def readback(self, execution, connection, items, write_result):
            del execution, connection, write_result
            return {"n1": "1.0"}  # 与请求值匹配

    lease = _ReleaseTrackingLease()
    use_case = SourceCommandUseCase(
        write_port_registry=StaticSourceWritePortRegistry({"opcua": _ReadbackOkPort()}),
        write_lease_port=lease,
    )

    result = asyncio.run(use_case.execute(_request()))
    assert result is not None
    assert result.attributes.get("readback") == "confirmed"
    assert lease.release_count == 1
    os.environ.pop("WHALE_INGEST_SOURCE_WRITE_ENABLED", None)


def test_readback_not_called_when_not_required() -> None:
    """require_readback=false 时即使 port 有 readback 方法也不调用。"""
    os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"

    class _ReadbackNotCalledPort(SourceWritePort):
        async def write(self, execution, connection, items):
            return SourceWriteResult(
                request_id="req-rb-no", command_id=None, dry_run=False,
                success_count=1, failure_count=0, results=[],
            )

        def readback(self, execution, connection, items, write_result):
            raise RuntimeError("readback should NOT be called")

    def _request_no_readback() -> SourceWriteRequest:
        req = _request()
        req.execution.params = {}  # require_readback 未设置
        return req

    lease = _ReleaseTrackingLease()
    use_case = SourceCommandUseCase(
        write_port_registry=StaticSourceWritePortRegistry({"opcua": _ReadbackNotCalledPort()}),
        write_lease_port=lease,
    )

    result = asyncio.run(use_case.execute(_request_no_readback()))
    assert result is not None
    assert "readback" not in result.attributes
    assert lease.release_count == 1
    os.environ.pop("WHALE_INGEST_SOURCE_WRITE_ENABLED", None)
