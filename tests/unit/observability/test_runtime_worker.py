"""验证 Runtime 生命周期、Context 作用域及 Worker wrapper。

生命周期测试使用内存 fake adapter，只证明安装/回滚顺序；Worker 测试使用真实
ContextVar 和本地 Prometheus registry，不证明外部采集链路。
"""

from __future__ import annotations

import asyncio

import pytest

from observability.config import ObservabilityConfig
from observability.context import bind_observation_context, get_observation_context
from observability.manager import ObservabilityRuntime


def _config(*, metrics: bool = True) -> ObservabilityConfig:
    """创建无网络 exporter 的 worker-only 测试配置。"""
    return ObservabilityConfig.model_validate(
        {
            "service": {"name": "worker-test"},
            "logging": {"enabled": False},
            "metrics": {"enabled": metrics},
            "tracing": {"enabled": False},
            "instrumentation": {"worker": {"enabled": True}},
        }
    )


def test_context_scope_restores_parent_after_exception() -> None:
    """嵌套作用域异常退出后必须恢复父 token 和扩展属性。"""
    before = get_observation_context()
    with pytest.raises(RuntimeError):
        with bind_observation_context(request_id="r1", attributes={"tenant": "a"}):
            assert get_observation_context().request_id == "r1"
            raise RuntimeError("stop")
    assert get_observation_context() == before


def test_worker_only_sync_return_exception_and_multi_runtime_registry() -> None:
    """无 FastAPI/scheduler 时同步 Worker 保留返回和异常，registry 相互隔离。"""
    first = ObservabilityRuntime(_config())
    second = ObservabilityRuntime(_config())
    assert first.metrics is not None
    assert second.metrics is not None
    assert first.metrics.registry is not second.metrics.registry

    observed_execution_ids: list[str | None] = []

    def runner(value: int) -> int:
        """记录同步执行上下文，并模拟成功或业务异常。"""
        observed_execution_ids.append(get_observation_context().execution_id)
        if value < 0:
            raise ValueError("negative")
        return value + 1

    wrapped = first.instrument_worker("calculate", runner)
    assert wrapped(2) == 3
    with pytest.raises(ValueError, match="negative"):
        wrapped(-1)
    assert all(observed_execution_ids)
    assert get_observation_context().execution_id is None


@pytest.mark.asyncio
async def test_async_worker_return_exception_and_cancel_semantics() -> None:
    """异步 Worker 应原样返回、传播业务异常并保留 CancelledError。"""
    runtime = ObservabilityRuntime(_config(metrics=False))

    async def runner(mode: str) -> str:
        """模拟异步成功、业务异常与可取消等待。"""
        assert get_observation_context().execution_id is not None
        if mode == "fail":
            raise LookupError("failed")
        if mode == "wait":
            await asyncio.Event().wait()
        return mode

    wrapped = runtime.instrument_worker("async.execute", runner)
    assert await wrapped("ok") == "ok"
    with pytest.raises(LookupError, match="failed"):
        await wrapped("fail")
    task = asyncio.create_task(wrapped("wait"))
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert get_observation_context().execution_id is None


class _Adapter:
    """记录安装顺序的 lifecycle fake，不模拟任何第三方框架。"""

    def __init__(
        self,
        name: str,
        events: list[str],
        *,
        fail_start: bool = False,
        fail_stop: bool = False,
        fail_uninstall: bool = False,
    ) -> None:
        self.name = name
        self._events = events
        self._fail_start = fail_start
        self._fail_stop = fail_stop
        self._fail_uninstall = fail_uninstall

    def install(self, runtime: ObservabilityRuntime) -> None:
        """记录宿主启动前的结构安装。"""
        self._events.append(f"install:{self.name}")

    def start(self) -> None:
        """先记录已获取资源，再按配置模拟 start 部分失败。"""
        self._events.append(f"resource-acquired:{self.name}")
        if self._fail_start:
            raise RuntimeError(f"start:{self.name}")

    def stop(self) -> None:
        """记录释放尝试，并可模拟资源释放本身失败。"""
        self._events.append(f"resource-release-attempted:{self.name}")
        if self._fail_stop:
            raise RuntimeError(f"stop:{self.name}")
        self._events.append(f"resource-released:{self.name}")

    def uninstall(self) -> None:
        """记录结构卸载，并可模拟卸载完成前失败。"""
        self._events.append(f"uninstall:{self.name}")
        if self._fail_uninstall:
            raise RuntimeError(f"uninstall:{self.name}")


@pytest.mark.asyncio
async def test_runtime_idempotence_reverse_shutdown_and_failure_rollback() -> None:
    """Runtime 重复启动安全，关闭与启动失败都按逆序卸载。"""
    events: list[str] = []
    runtime = ObservabilityRuntime(_config(metrics=False))
    runtime.install(_Adapter("one", events))
    runtime.install(_Adapter("two", events))
    await runtime.start()
    await runtime.start()
    await runtime.close()
    await runtime.close()
    assert events == [
        "install:one",
        "install:two",
        "resource-acquired:one",
        "resource-acquired:two",
        "resource-release-attempted:two",
        "resource-released:two",
        "resource-release-attempted:one",
        "resource-released:one",
        "uninstall:two",
        "uninstall:one",
    ]

    rollback_events: list[str] = []
    failed = ObservabilityRuntime(_config(metrics=False))
    failed.install(_Adapter("one", rollback_events))
    failed.install(_Adapter("boom", rollback_events, fail_start=True))
    with pytest.raises(RuntimeError, match="start:boom"):
        await failed.start()
    assert rollback_events == [
        "install:one",
        "install:boom",
        "resource-acquired:one",
        "resource-acquired:boom",
        "resource-release-attempted:boom",
        "resource-released:boom",
        "resource-release-attempted:one",
        "resource-released:one",
        "uninstall:boom",
        "uninstall:one",
    ]


@pytest.mark.asyncio
async def test_start_failure_preserves_primary_and_attempts_all_cleanup() -> None:
    """当前失败项 stop/uninstall 失败时仍清理此前组件并保留 start 为主异常。"""
    events: list[str] = []
    runtime = ObservabilityRuntime(_config(metrics=False))
    runtime.install(_Adapter("one", events))
    runtime.install(
        _Adapter(
            "boom",
            events,
            fail_start=True,
            fail_stop=True,
            fail_uninstall=True,
        )
    )

    with pytest.raises(RuntimeError, match="start:boom") as captured:
        await runtime.start()

    assert events == [
        "install:one",
        "install:boom",
        "resource-acquired:one",
        "resource-acquired:boom",
        "resource-release-attempted:boom",
        "resource-release-attempted:one",
        "resource-released:one",
        "uninstall:boom",
        "uninstall:one",
    ]
    notes = getattr(captured.value, "__notes__", [])
    assert any("stop failed adapter boom" in note for note in notes)
    assert any("uninstall adapter boom" in note for note in notes)


@pytest.mark.asyncio
async def test_shutdown_compound_failures_still_clean_remaining_adapters() -> None:
    """正常关闭遇到 stop/uninstall 复合失败时仍尽力清理其余组件。"""
    events: list[str] = []
    runtime = ObservabilityRuntime(_config(metrics=False))
    runtime.install(
        _Adapter("bad", events, fail_stop=True, fail_uninstall=True)
    )
    runtime.install(_Adapter("good", events))
    await runtime.start()

    with pytest.raises(RuntimeError, match="stop:bad") as captured:
        await runtime.close()

    assert "resource-released:good" in events
    assert "uninstall:good" in events
    assert "uninstall:bad" in events
    notes = getattr(captured.value, "__notes__", [])
    assert any("uninstall adapter bad" in note for note in notes)
