"""structlog + stdlib logging 配置。"""
from __future__ import annotations
import logging.config
from pathlib import Path
import structlog
from .processors import add_observation_context, sanitize_event

def configure_logging(*, level: str = "INFO", log_file: str | Path | None = None, max_bytes: int = 50*1024*1024, backup_count: int = 5) -> None:
    shared = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        add_observation_context,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        sanitize_event,
    ]
    structlog.configure(
        processors=[structlog.stdlib.filter_by_level, *shared, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    handlers = {"console": {"class": "logging.StreamHandler", "formatter": "json", "level": level}}
    root_handlers = ["console"]
    if log_file is not None:
        path = Path(log_file); path.parent.mkdir(parents=True, exist_ok=True)
        handlers["file"] = {"class":"logging.handlers.RotatingFileHandler","formatter":"json","level":level,"filename":str(path),"maxBytes":max_bytes,"backupCount":backup_count,"encoding":"utf-8"}
        root_handlers.append("file")
    logging.config.dictConfig({
        "version":1,
        "disable_existing_loggers":False,
        "formatters":{"json":{"()":structlog.stdlib.ProcessorFormatter,"foreign_pre_chain":shared,"processors":[structlog.stdlib.ProcessorFormatter.remove_processors_meta,structlog.processors.JSONRenderer()]}},
        "handlers":handlers,
        "root":{"handlers":root_handlers,"level":level},
        "loggers":{"apscheduler":{"level":"WARNING"},"sqlalchemy.engine":{"level":"WARNING"}},
    })
