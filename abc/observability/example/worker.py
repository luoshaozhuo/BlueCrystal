"""仅使用 Runtime 与 Worker wrapper 的一次性进程示例。

运行 ``python -m observability.example.worker`` 后，程序直接执行同步 Worker，打印
观测摘要并退出。所有文件输出位于 ``example/output/worker/``。

Doctest 不创建 FastAPI 或 Scheduler，只检查 Worker 从 Runtime 基线继承服务上下文、
生成 execution_id，并更新 status：

>>> result = run_example()
>>> result["result"]
42
>>> result["service_name"]
'observability-example'
>>> result["service_instance_id"]
'worker-01'
>>> result["source"]
'worker'
>>> result["job_id"] is None
True
>>> result["execution_id_present"]
True
>>> result["instrumentations"]
[]
>>> result["worker_result"]
'success'
>>> result["log_under_output"] and result["audit_under_output"]
True
"""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from observability import (
    ObservabilityConfig,
    get_logger,
    get_observation_context,
    install_observability,
    load_observability_config,
)

EXAMPLE_NAME = "worker"
EXAMPLE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = EXAMPLE_DIR / "output" / EXAMPLE_NAME
CONFIG_PATH = EXAMPLE_DIR.parent / "config" / "observability.yaml"
LOG_PATH = OUTPUT_DIR / "observability.log"
AUDIT_PATH = OUTPUT_DIR / "audit.sqlite3"


@contextmanager
def _example_environment() -> Iterator[None]:
    """临时设置纯 Worker 示例的独立配置变量。"""
    values = {
        "SERVICE_INSTANCE_ID": f"{EXAMPLE_NAME}-01",
        "APP_ENV": "example",
        "OBSERVABILITY_LOG_PATH": str(LOG_PATH),
        "OBSERVABILITY_AUDIT_PATH": str(AUDIT_PATH),
        "OTLP_ENDPOINT": os.getenv("OTLP_ENDPOINT", "http://127.0.0.1:64317"),
        "OTEL_TRACE_SAMPLE_RATE": "1.0",
    }
    previous = {name: os.environ.get(name) for name in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def _load_config() -> ObservabilityConfig:
    """加载项目 YAML，并把路径环境变量解析到本示例输出目录。"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with _example_environment():
        return load_observability_config(CONFIG_PATH)


def run_example() -> dict[str, object]:
    """直接执行 Worker，并返回 Runtime 基线继承与状态观测摘要。"""
    runtime = install_observability(_load_config())
    observed: dict[str, object] = {}

    def business_worker(value: int) -> int:
        """读取纯 Worker wrapper 从 Runtime 基线派生的上下文。"""
        context = get_observation_context()
        observed.update(
            service_name=context.service_name,
            service_instance_id=context.service_instance_id,
            source=context.source,
            job_id=context.job_id,
            execution_id=context.execution_id,
        )
        get_logger(__name__).info("worker_only_example", value=value)
        return value * 2

    runner = runtime.instrument_worker("example.worker.task", business_worker)
    asyncio.run(runtime.start())
    try:
        result = runner(21)
        status = runtime.status().to_dict()
    finally:
        asyncio.run(runtime.close())

    return {
        **observed,
        "result": result,
        "execution_id_present": observed.get("execution_id") is not None,
        "instrumentations": sorted(
            item["name"] for item in status["instrumentations"]
        ),
        "worker_result": status["workers"][0]["last_result"],
        "log_under_output": LOG_PATH.is_file() and LOG_PATH.is_relative_to(OUTPUT_DIR),
        "audit_under_output": AUDIT_PATH.is_file()
        and AUDIT_PATH.is_relative_to(OUTPUT_DIR),
    }


def main() -> None:
    """运行纯 Worker 示例并输出不含敏感信息的 JSON 摘要。"""
    print(json.dumps(run_example(), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
