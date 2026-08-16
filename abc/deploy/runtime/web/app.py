"""构造了运行时部署模式的web api接口"""

from __future__ import annotations

import fastapi

from deploy.runtime.web.routers.task import create_task_router
from deploy.runtime.web.routers.health import create_health_router


from deploy.runtime.scheduler import TaskScheduler


def create_web_api(scheduler: TaskScheduler) -> fastapi.FastAPI:
    """创建运行时部署模式的 Web API."""

    app = fastapi.FastAPI(
        title="BlueCrystal",
        version="0.1.0",
    )

    app.include_router(create_health_router(scheduler))
    app.include_router(create_task_router(scheduler))

    return app