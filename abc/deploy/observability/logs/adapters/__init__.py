"""Logs 本地输出 Adapter."""

from .console import ConsoleLogSink
from .rolling_file import RollingFileLogSink

__all__ = [
    "ConsoleLogSink",
    "RollingFileLogSink",
]
