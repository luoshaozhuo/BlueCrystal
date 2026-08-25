"""BackgroundScheduler 与 Worker 的一次性进程示例。

运行 ``python -m observability.example.scheduler_worker`` 后，程序调度一个 DateTrigger
任务，等待执行完成，打印观测摘要并退出。所有文件输出位于
``example/output/scheduler_worker/``。

Doctest 执行真实 BackgroundScheduler 线程池任务，并检查 Scheduler context、Worker
状态、日志及审计文件：

>>> result = run_example()
>>> result["service_name"]
'observability-example'
>>> result["source"]
'worker'
>>> result["job_id"]
'scheduler-example-job'
>>> result["execution_id_present"]
True
>>> result["instrumentations"]
['apscheduler']
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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Event

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_REMOVED

from observability import (
    ObservabilityConfig,
    get_logger,
    get_observation_context,
    install_observability,
    load_observability_config,
)
from observability.instrumentation import observe_scheduler_action

EXAMPLE_NAME = "scheduler_worker"
EXAMPLE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = EXAMPLE_DIR / "output" / EXAMPLE_NAME
CONFIG_PATH = EXAMPLE_DIR.parent / "config" / "observability.yaml"
LOG_PATH = OUTPUT_DIR / "observability.log"
AUDIT_PATH = OUTPUT_DIR / "audit.sqlite3"


@contextmanager
def _example_environment() -> Iterator[None]:
    """临时设置 Scheduler 示例的独立配置变量。"""
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
    """执行一次 Scheduler → Worker 链路并返回稳定观测摘要。"""
    scheduler = BackgroundScheduler(timezone=timezone.utc, daemon=False)
    runtime = install_observability(_load_config(), scheduler=scheduler)
    completed = Event()
    removed = Event()
    observed: dict[str, object] = {}

    def business_worker() -> str:
        """记录 Executor 恢复后、Worker wrapper 内部可见的上下文。"""
        context = get_observation_context()
        observed.update(
            service_name=context.service_name,
            source=context.source,
            job_id=context.job_id,
            execution_id=context.execution_id,
        )
        get_logger(__name__).info("scheduler_worker_example")
        return "done"

    runner = runtime.instrument_worker("example.scheduler.task", business_worker)

    def record_job_event(event: object) -> None:
        """在 Worker 状态落定及一次性 Job 清理后通知主线程。"""
        if getattr(event, "job_id", None) != "scheduler-example-job":
            return
        code = getattr(event, "code", None)
        if code == EVENT_JOB_EXECUTED:
            completed.set()
        elif code == EVENT_JOB_REMOVED:
            removed.set()

    scheduler.add_listener(
        record_job_event,
        EVENT_JOB_EXECUTED | EVENT_JOB_REMOVED,
    )
    asyncio.run(runtime.start())
    scheduler.start()
    try:
        observe_scheduler_action(
            runtime,
            operation="schedule.create",
            target_type="job",
            target_id="scheduler-example-job",
            detail={"shape": "scheduler+worker"},
            action=lambda: scheduler.add_job(
                runner,
                trigger="date",
                run_date=datetime.now(timezone.utc) + timedelta(milliseconds=50),
                id="scheduler-example-job",
            ),
        )()
        if not completed.wait(2):
            raise TimeoutError("scheduler example worker did not finish")
        if not removed.wait(2):
            raise TimeoutError("scheduler example job was not removed")
        status = runtime.status().to_dict()
    finally:
        scheduler.shutdown(wait=True)
        asyncio.run(runtime.close())

    return {
        **observed,
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
    """运行示例并把不含敏感信息的结果写到标准输出。"""
    print(json.dumps(run_example(), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
