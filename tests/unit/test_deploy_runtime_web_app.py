"""运行时部署 Web app factory 的开发期契约测试.

测试使用真实 FastAPI 路由装配和内存中的 APScheduler 实例，不启动 HTTP
监听或任务调度循环，因此不能证明网络服务、并发调度或外部依赖可用性。
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from deploy.bootstrap.runtime import execute_task
from deploy.runtime.scheduler import TaskScheduler
from deploy.runtime.web.app import create_api


def test_create_api_registers_health_and_task_routes() -> None:
    """app factory 应能构造应用并注册带绝对前缀的运行时路由."""
    app = create_api(TaskScheduler(execute_task))
    client = TestClient(app)

    health_response = client.get("/health/")
    tasks_response = client.get("/task/tasks")

    assert health_response.status_code == 200
    assert health_response.json() == {
        "scheduler_running": False,
        "scheduled_task_count": 0,
    }
    assert tasks_response.status_code == 200
    assert tasks_response.json() == []
