"""structlog 的显式配置和业务 Logger 工厂。"""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path
from typing import cast

import structlog

from ..config import LoggingConfig
from .processors import add_observation_context, sanitize_event


def configure_logging(config: LoggingConfig) -> None:
    """显式配置 structlog；仅在 Runtime 创建时产生全局配置副作用。"""
    controlled = {
        "processors",
        "wrapper_class",
        "logger_factory",
        "cache_logger_on_first_use",
    }

    conflict = controlled.intersection(config.options)
    if conflict:
        raise ValueError(
            "logging.options conflicts with runtime-controlled keys: "
            + ", ".join(sorted(conflict))
        )

    log_level = getattr(
        logging,
        config.level.upper(),
        logging.INFO,
    )

    if config.file is not None:
        log_path = Path(config.file.path)

        if not log_path.name:
            raise ValueError(
                "logging.file.path must include the target log filename"
            )

        log_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    if config.file is not None:
        if config.file.rotation not in {"daily", "size"}:
            raise ValueError(
                "logging.file.rotation must be one of: 'daily', 'size'"
            )

        if config.file.rotation == "daily":
            handler = logging.handlers.TimedRotatingFileHandler(
                config.file.path,
                when="midnight",
                interval=1,
                backupCount=config.file.backup_count,
                encoding="utf-8",
            )
        else:
            handler = logging.handlers.RotatingFileHandler(
                config.file.path,
                maxBytes=config.file.max_bytes,
                backupCount=config.file.backup_count,
                encoding="utf-8",
            )
    else:
        handler = logging.StreamHandler()

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
    )

    handler.setFormatter(formatter)
    handler.setLevel(log_level)

    handler.name = config.handler_name

    root_logger = logging.getLogger()

    # 避免重复初始化导致日志重复输出
    for old_handler in root_logger.handlers[:]:
        if old_handler.name == config.handler_name:
            root_logger.removeHandler(old_handler)

    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            add_observation_context,
            structlog.processors.TimeStamper(
                fmt="iso",
                utc=True,
            ),
            sanitize_event,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            log_level
        ),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
        **config.options,
    )


def get_logger(
    name: str | None = None,
) -> structlog.typing.FilteringBoundLogger:
    """返回自动注入当前关联上下文的业务 Logger。"""
    return cast(
        structlog.typing.FilteringBoundLogger,
        structlog.get_logger(name),
    )