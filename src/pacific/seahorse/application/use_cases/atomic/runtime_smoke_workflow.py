"""Seahorse 内存 runtime smoke workflow。

本 workflow 是纯内存 smoke / local / in-memory runtime 验证链路，按下列顺序
串联已有 application ports 与 atomic use cases::

    WritePlan
        -> BuildWriteBatchUseCase
        -> RuntimeExecutor.tick_and_dispatch
        -> DispatchWriteBatchUseCase
        -> InMemoryStarfishWriterBackend

workflow 仅用于本地 smoke 验证，不接真实 Starfish runtime，不调用 socket、
subprocess、native runner 或 ServerSimulatorFacade，也不启动 scheduler
executor。所有副作用仅保留在 InMemoryStarfishWriterBackend.history 和
RuntimeExecutor 的诊断字段中。

工作流运行结束后输出稳定的 :class:`RuntimeSmokeReport`，供 facade、CLI
或脚本验证整条 batch dispatch 链路最小可用性。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pacific.seahorse.application.ports.starfish_writer_port import StarfishWriterPort
from pacific.seahorse.application.use_cases.atomic.build_write_batch import BuildWriteBatchUseCase
from pacific.seahorse.application.use_cases.atomic.dispatch_write_batch import DispatchWriteBatchUseCase
from pacific.seahorse.domain.runtime_contract import WritePlan, WritePlanId

# 仅类型标注依赖：避免与 ``seahorse.application.runtime.executor`` 形成
# 模块级循环。``RuntimeExecutor`` 在模块加载时由 ``atomic.__init__`` 触发
# 的 eager re-export 会让 ``atomic`` 反向加载 ``runtime.executor``，
# 形成 executor -> atomic -> runtime_smoke_workflow -> executor 的循环。
if TYPE_CHECKING:
    from pacific.seahorse.application.runtime.executor import RuntimeExecutor


@dataclass(frozen=True, slots=True)
class RuntimeSmokeReport:
    """runtime smoke workflow 的稳定结果 DTO。

    Attributes:
        plan_id: 运行计划标识。
        runtime_id: smoke 运行时实例标识。
        tick_count: 已执行 ``tick_and_dispatch`` 调用次数。
        generated_batch_count: 累计生成 batch 数量。
        dispatch_count: 累计 dispatch 次数（与 generated_batch_count 一致
            仅用于显示；不为 0 时代表 workflow 已走到 writer 端口）。
        success_count: dispatch 中 accepted_count 累计值。
        failure_count: dispatch 中 failures 累计项数。
        last_error: 最近一次 dispatch 或 batch 生成的错误摘要；为空表示
            本轮 workflow 未发生可记录失败。
        writer_history_count: 内存 Starfish writer backend 已接收 batch
            数量；表示 backend 实际收到 writer 调用。
        dispatch_status: 最近一次 dispatch 状态诊断字段，例如
            ``"success"`` 或 ``"partial_failure"``。
    """

    plan_id: WritePlanId
    runtime_id: str
    tick_count: int
    generated_batch_count: int
    dispatch_count: int
    success_count: int
    failure_count: int
    last_error: str
    writer_history_count: int
    dispatch_status: str

    def to_diagnostic_view(self) -> dict[str, str | int]:
        """输出稳定诊断视图。

        Returns:
            仅包含标量字段的 dict，便于快照、JSON 序列化或 CLI 输出。
        """
        return {
            "plan_id": self.plan_id.value,
            "runtime_id": self.runtime_id,
            "tick_count": self.tick_count,
            "generated_batch_count": self.generated_batch_count,
            "dispatch_count": self.dispatch_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "last_error": self.last_error,
            "writer_history_count": self.writer_history_count,
            "dispatch_status": self.dispatch_status,
        }


@dataclass(slots=True)
class RuntimeSmokeWorkflow:
    """内存 runtime smoke workflow 编排。

    workflow 只持有注入的 application 端口与 atomic use case，不在内部
    重新装配具体 backend、gateway 或 data source runtime；调用方应使用
    :mod:`seahorse.container` 或测试装配提供内存实现，确保链路不接
    真实 Starfish runtime。

    Attributes:
        runtime_id: smoke 运行实例标识。
        executor: 已配置 batch_builder 与 dispatch_use_case 的内存
            :class:`RuntimeExecutor`；不允许 None，因为 workflow 必须
            串联完整 build -> tick -> dispatch 链路。
        batch_builder: WriteBatch 生成用例，由 container 注入。
        dispatch_use_case: WriteBatch 分发用例，由 container 注入。
        writer: Starfish writer 端口；用于在 workflow 完成后读取 backend
            history，避免调用方重新拆解依赖图。
    """

    runtime_id: str
    executor: RuntimeExecutor
    batch_builder: BuildWriteBatchUseCase
    dispatch_use_case: DispatchWriteBatchUseCase
    writer: StarfishWriterPort
    write_plan: WritePlan = field(repr=False)
    _success_count: int = 0
    _failure_count: int = 0

    def run(self, *, now_ns: int, ticks: int) -> RuntimeSmokeReport:
        """同步执行 smoke workflow。

        该方法按 ``ticks`` 次调用 :meth:`RuntimeExecutor.tick_and_dispatch`，
        累计 dispatch 结果并汇总 stable report。workflow 不启动线程、
        不 sleep、不查询真实 Starfish。

        Args:
            now_ns: 起始单调时钟纳秒值；workflow 按 ``now_ns + i * step_ns``
                递增推进。
            ticks: 调用 tick_and_dispatch 的次数；非正数会立即返回空报告。

        Returns:
            稳定 :class:`RuntimeSmokeReport`，包含 plan_id、tick_count、
            generated_batch_count、dispatch_count、success_count、
            failure_count、last_error、writer_history_count 等字段。
        """
        if self.executor.context.write_plan is None:
            raise ValueError("RuntimeSmokeWorkflow.executor 必须携带 WritePlan")
        self.executor.start(now_ns=now_ns)
        self._success_count = 0
        self._failure_count = 0
        last_error = ""
        last_dispatch_status = ""
        for tick_index in range(ticks):
            now = now_ns + tick_index
            try:
                result = self.executor.tick_and_dispatch(now_ns=now)
            except Exception as exc:  # noqa: BLE001 - workflow 必须继续累计
                last_error = f"workflow tick failed: {exc}"
                break
            if result is None:
                # 非 due 时不计入 dispatch，但保留 writer 状态用于快照。
                continue
            self._success_count += result.accepted_count
            self._failure_count += len(result.failures)
            last_dispatch_status = self.executor.diagnostics.last_dispatch_status
            last_error = self.executor.diagnostics.last_writer_error
        return RuntimeSmokeReport(
            plan_id=self.write_plan.plan_id,
            runtime_id=self.runtime_id,
            tick_count=self.executor.diagnostics.tick_index,
            generated_batch_count=self.executor.diagnostics.generated_batch_count,
            dispatch_count=self.executor.diagnostics.generated_batch_count,
            success_count=self._success_count,
            failure_count=self._failure_count,
            last_error=last_error,
            writer_history_count=self._resolve_writer_history(),
            dispatch_status=last_dispatch_status,
        )

    def _resolve_writer_history(self) -> int:
        """读取底层 writer backend 的 batch history 长度。

        :class:`seahorse.adapters.gateways.StarfishWriterGateway` 已暴露
        ``history`` 引用，workflow 优先读取该字段；对于未提供 ``history``
        字段的 writer 实现，返回 0 以保证 workflow 不会因为不可用的
        history 而失败。
        """
        history = getattr(self.writer, "history", None)
        return len(history) if history is not None else 0


__all__ = ["RuntimeSmokeReport", "RuntimeSmokeWorkflow"]