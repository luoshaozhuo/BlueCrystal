"""SourceAcquisitionUseCase 单元测试。

这些测试覆盖请求校验、模式分发和订阅 fail-fast 语义。
"""

from __future__ import annotations

import asyncio
from typing import cast

import pytest

from whale.ingest.ports.source.source_acquisition_port import (
    SourceReadOnceFailedError,
)
from whale.ingest.usecases import SourceAcquisitionUseCase
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
    SourceAcquisitionRequest,
)
from whale.ingest.usecases.dtos.source_acquisition_start_result import (
    SourceAcquisitionStartResult,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.ingest.usecases.roles.polling_acquisition_role import PollingAcquisitionRole
from whale.ingest.usecases.roles.polling_acquisition_role import PollingAcquisitionSession
from whale.ingest.usecases.roles.subscription_acquisition_role import (
    SubscriptionAcquisitionRole,
)


class FakePollingRole:
    """记录 polling start 调用的假角色。"""

    def __init__(self, *, error: Exception | None = None) -> None:
        self.calls: list[SourceAcquisitionRequest] = []
        self.error = error

    def start(self, request: SourceAcquisitionRequest) -> SourceAcquisitionStartResult:
        """记录调用并返回固定结果。"""

        self.calls.append(request)
        loop = asyncio.get_running_loop()

        async def _run() -> None:
            if self.error is not None:
                raise self.error

        task = loop.create_task(_run())
        return SourceAcquisitionStartResult(
            request_id=request.request_id,
            task_id=request.task_id,
            mode=request.execution.acquisition_mode.upper(),
            sessions=[
                PollingAcquisitionSession(
                    task=task,
                    stop_event=asyncio.Event(),
                )
            ],
        )


class FakeSubscriptionRole:
    """记录 subscription start 调用的假角色。"""

    def __init__(self) -> None:
        self.calls: list[SourceAcquisitionRequest] = []

    async def start(self, request: SourceAcquisitionRequest) -> SourceAcquisitionStartResult:
        """记录调用并返回固定结果。"""

        self.calls.append(request)
        return SourceAcquisitionStartResult(
            request_id=request.request_id,
            task_id=request.task_id,
            mode=request.execution.acquisition_mode.upper(),
            sessions=[],
        )


def _build_request(acquisition_mode: str) -> SourceAcquisitionRequest:
    return SourceAcquisitionRequest(
        request_id="request-1",
        task_id=101,
        execution=AcquisitionExecutionOptions(
            protocol="opcua",
            transport="tcp",
            acquisition_mode=acquisition_mode,
            interval_ms=100,
            max_iteration=1 if acquisition_mode != "POLLING" else None,
            request_timeout_ms=500,
            freshness_timeout_ms=30_000,
            alive_timeout_ms=60_000,
        ),
        connections=[
            SourceConnectionData(
                host="127.0.0.1",
                port=4840,
                ied_name="IED_01",
                ld_name="LD_01",
                namespace_uri="urn:test",
            )
        ],
        items=[
            AcquisitionItemData(
                key="TotW",
                profile_item_id=1,
                relative_path="WTG_001/MMXU1.TotW.mag.f",
            )
        ],
    )


def _build_use_case() -> tuple[SourceAcquisitionUseCase, FakePollingRole, FakeSubscriptionRole]:
    polling_role = FakePollingRole()
    subscription_role = FakeSubscriptionRole()
    return (
        SourceAcquisitionUseCase(
            polling_role=cast(PollingAcquisitionRole, polling_role),
            subscription_role=cast(SubscriptionAcquisitionRole, subscription_role),
        ),
        polling_role,
        subscription_role,
    )


def test_read_once_routes_to_polling_role() -> None:
    use_case, polling_role, subscription_role = _build_use_case()

    result = asyncio.run(use_case.start(_build_request("READ_ONCE")))

    assert result.mode == "READ_ONCE"
    assert len(polling_role.calls) == 1
    assert subscription_role.calls == []


def test_polling_routes_to_polling_role() -> None:
    use_case, polling_role, subscription_role = _build_use_case()

    result = asyncio.run(use_case.start(_build_request("POLLING")))

    assert result.mode == "POLLING"
    assert len(polling_role.calls) == 1
    assert subscription_role.calls == []


def test_subscribe_fails_fast_when_current_reader_does_not_support_subscription() -> None:
    use_case, polling_role, subscription_role = _build_use_case()

    result = asyncio.run(use_case.start(_build_request("SUBSCRIBE")))

    assert polling_role.calls == []
    assert result.mode == "SUBSCRIBE"
    assert len(subscription_role.calls) == 1


def test_read_once_propagates_one_shot_failure() -> None:
    polling_role = FakePollingRole(error=SourceReadOnceFailedError("all connections failed"))
    subscription_role = FakeSubscriptionRole()
    use_case = SourceAcquisitionUseCase(
        polling_role=cast(PollingAcquisitionRole, polling_role),
        subscription_role=cast(SubscriptionAcquisitionRole, subscription_role),
    )

    with pytest.raises(SourceReadOnceFailedError, match="all connections failed"):
        asyncio.run(use_case.start(_build_request("READ_ONCE")))


def test_read_requires_max_iteration_equal_to_one() -> None:
    use_case, polling_role, subscription_role = _build_use_case()
    request = _build_request("READ")
    request.execution.max_iteration = None

    with pytest.raises(ValueError, match="read_once modes require max_iteration == 1"):
        asyncio.run(use_case.start(request))

    assert polling_role.calls == []
    assert subscription_role.calls == []


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (lambda request: setattr(request, "request_id", ""), "request_id is required"),
        (lambda request: setattr(request, "task_id", 0), "task_id must be greater than 0"),
        (lambda request: setattr(request, "connections", []), "connections cannot be empty"),
        (lambda request: setattr(request, "items", []), "items cannot be empty"),
        (
            lambda request: setattr(request.connections[0], "host", ""),
            "connection.host is required",
        ),
        (
            lambda request: setattr(request.connections[0], "port", 0),
            "connection.port must be greater than 0",
        ),
        (
            lambda request: setattr(request.items[0], "relative_path", ""),
            "item.relative_path is required",
        ),
    ],
)
def test_request_validation_errors(
    mutator: object,
    message: str,
) -> None:
    use_case, _, _ = _build_use_case()
    request = _build_request("READ")
    assert callable(mutator)
    mutator(request)

    with pytest.raises(ValueError, match=message):
        asyncio.run(use_case.start(request))
