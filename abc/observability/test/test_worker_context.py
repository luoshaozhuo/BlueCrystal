"""验证跨线程 Worker 仍携带 Runtime 服务级关联上下文。"""

from __future__ import annotations

from threading import Thread

from observability.config import ObservabilityConfig
from observability.context import bind_observation_context, get_observation_context
from observability.runtime import ObservabilityRuntime


def test_worker_in_new_thread_inherits_runtime_service_context() -> None:
    """后台线程中的 Worker 日志上下文必须包含 Runtime 的服务和实例标识。"""
    config = ObservabilityConfig.model_validate(
        {
            "service": {"name": "worker-context-test", "instance_id": "node-1"},
            "logging": {"enabled": False},
            "metrics": {"enabled": False},
            "tracing": {"enabled": False},
            "instrumentation": {"worker": {"enabled": True}},
        }
    )
    runtime = ObservabilityRuntime(config)
    observed: list[tuple[str | None, str | None, str | None]] = []

    def runner() -> None:
        """读取封装器绑定后的当前上下文。"""
        context = get_observation_context()
        observed.append(
            (context.service_name, context.service_instance_id, context.execution_id)
        )

    thread = Thread(target=runtime.instrument_worker("threaded-worker", runner))
    thread.start()
    thread.join()

    assert len(observed) == 1
    service_name, instance_id, execution_id = observed[0]
    assert (service_name, instance_id) == ("worker-context-test", "node-1")
    assert execution_id is not None


def test_worker_ignores_context_from_another_runtime() -> None:
    """独立 Worker 不得错误继承当前线程中另一 Runtime 的服务上下文。"""
    runtime = ObservabilityRuntime(
        ObservabilityConfig.model_validate(
            {
                "service": {"name": "expected-service", "instance_id": "expected-node"},
                "logging": {"enabled": False},
                "metrics": {"enabled": False},
                "tracing": {"enabled": False},
                "instrumentation": {"worker": {"enabled": True}},
            }
        )
    )
    observed = []
    wrapped = runtime.instrument_worker(
        "isolated-worker", lambda: observed.append(get_observation_context())
    )

    with bind_observation_context(
        service_name="other-service",
        service_instance_id="other-node",
        request_id="foreign-request",
    ):
        wrapped()

    assert observed[0].service_name == "expected-service"
    assert observed[0].service_instance_id == "expected-node"
    assert observed[0].request_id is None
