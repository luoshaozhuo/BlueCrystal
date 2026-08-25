"""将 Runtime 状态快照作为可选 FastAPI 路由暴露。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI

if TYPE_CHECKING:
    from ..runtime import ObservabilityRuntime


def install_status_route(app: object, runtime: ObservabilityRuntime) -> None:
    """在启用 status 的 FastAPI 宿主上幂等注册 ``GET /status``。"""
    if not isinstance(app, FastAPI):
        raise TypeError("status route target must be FastAPI")
    if getattr(app.state, "_observability_status_route_installed", False):
        return

    @app.get("/status", include_in_schema=False)
    def status() -> dict[str, object]:
        """返回当前挂载 Runtime 的只读状态，支持同一 app 重新装配。"""
        current_runtime = getattr(app.state, "observability", runtime)
        return current_runtime.status().to_dict()

    app.state._observability_status_route_installed = True
