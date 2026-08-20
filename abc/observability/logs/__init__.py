"""结构化日志公共接口。"""

from .config import configure_logging
from .processors import add_observation_context, sanitize_event

__all__ = [
    "configure_logging",
    "add_observation_context",
    "sanitize_event",
]
