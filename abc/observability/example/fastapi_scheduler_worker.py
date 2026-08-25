"""FastAPI、BackgroundScheduler 与 Worker 的完整单进程示例。

运行命令：

``python -m observability.example.fastapi_scheduler_worker``

服务提供 ``/status``、``/metrics``、直接 Worker 和一次性调度任务入口。所有文件
输出位于 ``example/output/fastapi_scheduler_worker/``；内嵌 Scheduler 要求 Uvicorn
保持单进程。

Doctest 会通过真实 TestClient 启动 lifespan，执行 HTTP Worker 与 DateTrigger Worker，
并检查自动安装的 status、metrics、日志和审计输出：

>>> result = run_doctest_scenario()
>>> result["direct_task"]
1
>>> result["request_id"]
'fastapi-request-1'
>>> result["job_id"]
'example-job'
>>> result["execution_id_present"]
True
>>> result["instrumentations"]
['apscheduler', 'fastapi']
>>> result["worker_metric_present"]
True
>>> result["log_under_output"] and result["audit_under_output"]
True
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator, Iterator
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Event, Lock

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_REMOVED
from fastapi import FastAPI, Query

from observability import (
    ObservabilityConfig,
    ObservabilityRuntime,
    get_logger,
    get_observation_context,
    install_observability,
    load_observability_config,
)
from observability.instrumentation import observe_scheduler_action

EXAMPLE_NAME = "fastapi_scheduler_worker"
EXAMPLE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = EXAMPLE_DIR / "output" / EXAMPLE_NAME
CONFIG_PATH = EXAMPLE_DIR.parent / "config" / "observability.yaml"
LOG_PATH = OUTPUT_DIR / "observability.log"
AUDIT_PATH = OUTPUT_DIR / "audit.sqlite3"
SERVER_LOG_PATH = OUTPUT_DIR / "server.log"


@contextmanager
def _example_environment() -> Iterator[None]:
    """临时设置本示例配置变量，加载完成后恢复宿主进程环境。"""
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
    """从项目 YAML 加载已绑定到本示例输出目录的配置。"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with _example_environment():
        return load_observability_config(CONFIG_PATH)


def create_app() -> FastAPI:
    """创建资源由 FastAPI lifespan 管理的完整示例应用。"""
    scheduler = BackgroundScheduler(
        timezone=timezone.utc,
        daemon=False,
        job_defaults={
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": 60,
        },
    )
    completed = Event()
    job_removed = Event()
    observations: dict[int, dict[str, object]] = {}
    observations_lock = Lock()
    runtime: ObservabilityRuntime

    def business_worker(task_id: int, *, fail: bool = False) -> int:
        """记录业务执行点可见的完整上下文，并模拟成功或失败。"""
        context = get_observation_context()
        with observations_lock:
            observations[task_id] = {
                "request_id": context.request_id,
                "correlation_id": context.correlation_id,
                "source": context.source,
                "job_id": context.job_id,
                "execution_id": context.execution_id,
            }
        get_logger(__name__).info("example_worker", task_id=task_id, fail=fail)
        completed.set()
        if fail:
            raise ValueError("requested example failure")
        return task_id

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
        """依次启动 Runtime 与 Scheduler，并在退出时逆序关闭。"""
        scheduler_started = False
        await runtime.start()
        try:
            scheduler.start()
            scheduler_started = True
            yield
        finally:
            try:
                if scheduler_started:
                    await asyncio.to_thread(scheduler.shutdown, wait=True)
            finally:
                await runtime.close()

    app = FastAPI(
        title="FastAPI + Scheduler + Worker Observability Example",
        lifespan=lifespan,
    )
    runtime = install_observability(_load_config(), app=app, scheduler=scheduler)
    runner = runtime.instrument_worker("example.fastapi.task", business_worker)

    def record_removed_job(event: object) -> None:
        """通知 doctest 一次性 Job 已完成 JobStore 清理。"""
        if getattr(event, "job_id", None) == "example-job":
            job_removed.set()

    scheduler.add_listener(record_removed_job, EVENT_JOB_REMOVED)

    # doctest 只通过 app.state 读取测试结果，不额外创建观测辅助路由。
    app.state.example_completed = completed
    app.state.example_job_removed = job_removed
    app.state.example_observations = observations
    app.state.example_runtime = runtime

    @app.get("/")
    def describe() -> dict[str, object]:
        """返回本示例形态和自动安装的观测入口。"""
        return {
            "shape": "fastapi+scheduler+worker",
            "status": "/status",
            "metrics": "/metrics",
            "output_dir": str(OUTPUT_DIR),
        }

    @app.post("/tasks/{task_id}/run")
    def run_task(task_id: int, fail: bool = False) -> dict[str, int]:
        """在当前 HTTP 请求上下文中直接运行 Worker。"""
        return {"task_id": runner(task_id, fail=fail)}

    @app.post("/schedules/{job_id}")
    def schedule_task(
        job_id: str,
        task_id: int,
        delay_seconds: float = Query(default=1.0, gt=0, le=86_400),
    ) -> dict[str, object]:
        """创建一次性 Job，并审计该 Scheduler 管理操作。"""
        run_date = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
        job = observe_scheduler_action(
            runtime,
            operation="schedule.create",
            target_type="job",
            target_id=job_id,
            detail={"task_id": task_id, "delay_seconds": delay_seconds},
            action=lambda: scheduler.add_job(
                runner,
                trigger="date",
                run_date=run_date,
                id=job_id,
                args=(task_id,),
            ),
        )()
        return {"job_id": job.id, "next_run_time": job.next_run_time.isoformat()}

    return app


def run_doctest_scenario() -> dict[str, object]:
    """通过真实 TestClient、Scheduler 和 Worker 返回稳定的观测断言摘要。"""
    from fastapi.testclient import TestClient

    app = create_app()
    headers = {
        "x-request-id": "fastapi-request-1",
        "x-correlation-id": "fastapi-correlation-1",
        "x-actor": "example-user",
    }
    with TestClient(app) as client:
        direct = client.post("/tasks/1/run", headers=headers)
        direct.raise_for_status()
        app.state.example_completed.clear()
        scheduled = client.post(
            "/schedules/example-job",
            params={"task_id": 2, "delay_seconds": 0.05},
            headers=headers,
        )
        scheduled.raise_for_status()
        if not app.state.example_completed.wait(2):
            raise TimeoutError("scheduled example worker did not finish")
        if not app.state.example_job_removed.wait(2):
            raise TimeoutError("scheduled example job was not removed")
        status = client.get("/status").json()
        metrics = client.get("/metrics").text
        scheduled_context = app.state.example_observations[2]
        return {
            "direct_task": direct.json()["task_id"],
            "request_id": scheduled_context["request_id"],
            "job_id": scheduled_context["job_id"],
            "execution_id_present": scheduled_context["execution_id"] is not None,
            "instrumentations": sorted(
                item["name"] for item in status["instrumentations"]
            ),
            "worker_metric_present": "worker_executions_total" in metrics,
            "log_under_output": LOG_PATH.is_file() and LOG_PATH.is_relative_to(OUTPUT_DIR),
            "audit_under_output": AUDIT_PATH.is_file()
            and AUDIT_PATH.is_relative_to(OUTPUT_DIR),
        }


def _uvicorn_log_config() -> dict[str, object]:
    """把 Uvicorn 服务日志和访问日志限制到本示例输出目录。"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
        },
        "handlers": {
            "server": {
                "class": "logging.FileHandler",
                "filename": str(SERVER_LOG_PATH),
                "formatter": "default",
                "encoding": "utf-8",
            }
        },
        "loggers": {
            "uvicorn": {"handlers": ["server"], "level": "INFO", "propagate": False},
            "uvicorn.error": {"handlers": ["server"], "level": "INFO", "propagate": False},
            "uvicorn.access": {"handlers": ["server"], "level": "INFO", "propagate": False},
        },
    }


def main() -> None:
    """以单进程 Uvicorn 启动完整示例。"""
    import uvicorn

    uvicorn.run(
        create_app(),
        host=os.getenv("OBSERVABILITY_FASTAPI_EXAMPLE_HOST", "127.0.0.1"),
        port=int(os.getenv("OBSERVABILITY_FASTAPI_EXAMPLE_PORT", "8000")),
        workers=1,
        log_config=_uvicorn_log_config(),
    )


if __name__ == "__main__":
    main()
