"""Public observability installation API."""

from __future__ import annotations

from fastapi import FastAPI

from ..config import ObservabilityConfig
from ..manager import ObservabilityManager


def install_observability(
    app: FastAPI,
    config: ObservabilityConfig | None = None,
) -> ObservabilityManager:
    """Install observability manager into application."""
    manager = ObservabilityManager(
        config or ObservabilityConfig()
    )
    app.state.observability = manager
    return manager
