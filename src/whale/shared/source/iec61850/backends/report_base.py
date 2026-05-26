"""IEC 61850 Report backend base types.

Report 是 IEC 61850 的订阅/事件能力，与 MMS polling read/write 不同。
Report 通过 RCB (ReportControlBlock) 配置，由 server 主动推送数据变化。
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class RawReportEvent:
    """Raw IEC 61850 Report event.

    One REPORT line from the IEC 61850 report runner stdout.
    """

    rcb_ref: str
    """Report Control Block object reference."""

    timestamp_ms: int
    """Event timestamp in milliseconds since epoch."""

    seq_num: int
    """Report sequence number (monotonically increasing per RCB)."""

    values: tuple[str, ...] = field(default_factory=tuple)
    """Data set values in order, as string-encoded MMS values."""

    ok: bool = True
    """Whether this event was successfully parsed."""

    error_reason: str | None = None
    """Error description if ok=False."""


RawReportEventHandler = Callable[[RawReportEvent], Awaitable[None]]
"""Async callback invoked on each report event."""

ReportErrorHandler = Callable[[str], Awaitable[None]]
"""Async callback invoked on protocol-level error or unexpected exit."""


@runtime_checkable
class Iec61850ReportClientBackend(Protocol):
    """Protocol for IEC 61850 Report client backend."""

    async def subscribe(
        self,
        host: str,
        port: int,
        ied_name: str,
        rcb_ref: str,
        *,
        timeout_seconds: float = 10.0,
        event_callback: RawReportEventHandler,
        error_callback: ReportErrorHandler | None = None,
        max_reconnect_attempts: int = 0,
    ) -> None:
        """Start report subscription.

        Connects to the IEC 61850 server, locates the RCB, reserves and
        enables the report.  Incoming report events are delivered to
        ``event_callback``.

        Args:
            host: Server hostname or IP.
            port: Server port.
            ied_name: IED name (MMS domain).
            rcb_ref: Report Control Block reference (short name or full ref).
            timeout_seconds: Overall subscription timeout.
            event_callback: Async callback for each report event.
            error_callback: Optional async callback for protocol errors.
            max_reconnect_attempts: Max reconnect attempts on unexpected exit.
                Default 0 = disabled.
        """

    async def close(self) -> None:
        """Stop the subscription and release resources."""
