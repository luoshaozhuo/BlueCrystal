"""structlog 的显式配置和业务 Logger 工厂。"""

from __future__ import annotations

import logging
from typing import Any, cast

import structlog

from ..config import LoggingConfig
from .processors import add_observation_context, sanitize_event


def configure_logging(config: LoggingConfig) -> None:
    """显式配置 structlog；仅在 Runtime 创建时产生全局配置副作用。"""
    controlled = {"processors", "wrapper_class", "logger_factory"}
    conflict = controlled.intersection(config.options)
    if conflict:
        raise ValueError(
            "logging.options conflicts with runtime-controlled keys: "
            + ", ".join(sorted(conflict))
        )
    if config.renderer == "json":
        renderer: Any = structlog.processors.JSONRenderer()
    elif config.renderer == "console":
        renderer = structlog.dev.ConsoleRenderer()
    else:
        raise ValueError(f"logging.renderer: unsupported renderer {config.renderer!r}")
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            add_observation_context,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            sanitize_event,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, config.level.upper(), logging.INFO)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        **config.options,
    )
    if config.configure_stdlib:
        logging.basicConfig(level=config.level.upper())


def get_logger(name: str | None = None) -> structlog.typing.FilteringBoundLogger:
    """返回自动注入当前关联上下文的业务 Logger。"""
    return cast(structlog.typing.FilteringBoundLogger, structlog.get_logger(name))
