"""Configuration loader for observability."""

from pathlib import Path
from typing import Any

import yaml

from . import (
    LoggingConfig,
    MetricsConfig,
    ObservabilityConfig,
    TraceConfig,
)


def load_observability_config(path: str | Path) -> ObservabilityConfig:
    """Load observability configuration from yaml file."""
    data: dict[str, Any] = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    section = data.get("observability", {})

    return ObservabilityConfig(
        logging=LoggingConfig(
            level=section.get("logging", {}).get("level", "INFO"),
        ),
        metrics=MetricsConfig(
            namespace=section.get("metrics", {}).get(
                "namespace", "bluecrystal"
            ),
            subsystem=section.get("metrics", {}).get("subsystem"),
        ),
        trace=TraceConfig(
            enabled=section.get("trace", {}).get("enabled", True),
            service_name=section.get("trace", {}).get(
                "service_name", "bluecrystal"
            ),
            normal_sample_rate=section.get("trace", {}).get(
                "normal_sample_rate", 0.001
            ),
        ),
    )
