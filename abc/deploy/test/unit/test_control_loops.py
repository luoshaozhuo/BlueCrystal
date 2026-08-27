"""第一阶段两个后台控制循环的单元测试。

测试仅使用进程内 asyncio Event 与回调替身，验证单轮普通异常不会终止循环以及 stop 的取消
语义；不验证协调后端、Lease 或任何分布式故障处理能力。测试需在安装 pytest-asyncio 的本地
开发环境执行。
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

import pytest

from deploy.core.coordination_maintenance import CoordinationMaintenance
from deploy.core.reconciliation import ReconciliationControl


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "controller_factory",
    [
        pytest.param(
            lambda callback: CoordinationMaintenance(callback, interval_seconds=3600),
            id="coordination-maintenance",
        ),
        pytest.param(
            lambda callback: ReconciliationControl(callback, interval_seconds=3600),
            id="reconciliation",
        ),
    ],
)
async def test_control_loop_records_single_round_error_and_continues(
    controller_factory: Callable[[Callable[[], Awaitable[None]]], CoordinationMaintenance | ReconciliationControl],
) -> None:
    """保护单轮异常只记录且下一次主动唤醒仍可执行的控制循环契约。"""
    first_attempt = asyncio.Event()
    second_attempt = asyncio.Event()
    attempts = 0

    async def callback() -> None:
        """第一次模拟可恢复错误，第二次通知测试回调已继续执行。"""
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            first_attempt.set()
            raise RuntimeError("expected")
        second_attempt.set()

    controller = controller_factory(callback)
    await controller.start()
    assert controller.is_running is True

    await asyncio.wait_for(first_attempt.wait(), timeout=1)
    controller.trigger()
    await asyncio.wait_for(second_attempt.wait(), timeout=1)

    assert isinstance(controller.last_error, RuntimeError)
    assert controller.is_running is True

    await controller.stop()
    assert controller.is_running is False
    await controller.stop()
