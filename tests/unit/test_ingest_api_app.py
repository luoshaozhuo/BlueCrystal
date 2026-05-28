"""FastAPI app factory tests."""

from __future__ import annotations

from whale.ingest.api import create_app
from whale.ingest.framework.persistence import (
    create_runtime_engine,
    create_runtime_session_factory,
    initialize_runtime_database,
)


def test_api_app_contains_expected_routes(tmp_path) -> None:
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'api.sqlite'}")
    initialize_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)

    app = create_app(
        session_factory=session_factory,
        readiness_probe=lambda: True,
    )

    route_paths = {route.path for route in app.routes}
    assert "/healthz" in route_paths
    assert "/readyz" in route_paths
    assert "/api/v1/acquisition-tasks" in route_paths
    assert "/api/v1/acquisition-tasks/{task_id}" in route_paths
