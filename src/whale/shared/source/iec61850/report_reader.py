"""IEC 61850 Report source reader facade.

Wraps LibIec61850ReportBackend and provides a clean API for
report subscription.
"""

from __future__ import annotations

from whale.shared.source.iec61850.backends.libiec61850_report_backend import (
    LibIec61850ReportBackend,
    resolve_report_runner_path,
)
from whale.shared.source.iec61850.backends.report_base import (
    RawReportEvent,
    RawReportEventHandler,
    ReportErrorHandler,
)


class Iec61850ReportSourceReader:
    """Thin facade over the libiec61850 report backend."""

    def __init__(self, host: str, port: int, *, timeout_seconds: float = 10.0) -> None:
        self._host = host
        self._port = port
        self._timeout_seconds = timeout_seconds
        self._backend = LibIec61850ReportBackend()

    async def subscribe(
        self,
        ied_name: str,
        rcb_ref: str,
        *,
        event_callback: RawReportEventHandler,
        error_callback: ReportErrorHandler | None = None,
        max_reconnect_attempts: int = 0,
    ) -> None:
        """Start report subscription.

        Args:
            ied_name: IED name (MMS domain).
            rcb_ref: Report Control Block reference.
            event_callback: Async callback per report event.
            error_callback: Optional async callback for errors.
            max_reconnect_attempts: Max reconnect attempts on unexpected exit.
        """
        await self._backend.subscribe(
            host=self._host,
            port=self._port,
            ied_name=ied_name,
            rcb_ref=rcb_ref,
            timeout_seconds=self._timeout_seconds,
            event_callback=event_callback,
            error_callback=error_callback,
            max_reconnect_attempts=max_reconnect_attempts,
        )

    @property
    def is_active(self) -> bool:
        """Whether subscription is currently active."""
        return self._backend.is_active

    async def close(self) -> None:
        """Stop subscription and release resources."""
        await self._backend.close()


__all__ = [
    "Iec61850ReportSourceReader",
    "RawReportEvent",
    "ReportErrorHandler",
    "resolve_report_runner_path",
]
