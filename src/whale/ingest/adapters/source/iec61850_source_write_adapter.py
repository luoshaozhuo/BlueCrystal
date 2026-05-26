"""IEC 61850 MMS source write adapter.

Converts ingest DTOs to shared/source libiec61850 MMS write calls
and converts ``RawWriteItemResult`` to ``SourceWriteResult``.

Design conventions:
- Implements SourceWritePort, does not depend on source_lab.
- Uses Iec61850MmsSourceReader for MMS direct write.
- Each write creates a short-lived reader connection.
- Supports only mms_direct_write (writes to SP/CF FC data attributes).
"""

from __future__ import annotations

from datetime import UTC, datetime

from whale.ingest.ports.source.source_write_port import SourceWritePort
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.ingest.usecases.dtos.source_write_request import (
    SourceWriteExecutionOptions,
    SourceWriteItemData,
)
from whale.ingest.usecases.dtos.source_write_result import SourceWriteItemResult, SourceWriteResult
from whale.shared.source.iec61850.backends import RawWriteItemResult
from whale.shared.source.iec61850.reader import Iec61850MmsSourceReader


class Iec61850MmsSourceWriteAdapter(SourceWritePort):
    """Execute IEC 61850 MMS direct write via libiec61850 native runner."""

    async def write(
        self,
        execution: SourceWriteExecutionOptions,
        connection: SourceConnectionData,
        items: list[SourceWriteItemData],
    ) -> SourceWriteResult:
        """Execute one IEC 61850 MMS direct write batch.

        Each item's ``node_id`` is the MMS object reference,
        ``value_type`` is the MMS type (BOOLEAN, INT32, UINT32,
        FLOAT32, FLOAT64, VISIBLE_STRING).

        The functional constraint is read from
        ``execution.params["fc"]`` or defaults to "SP".

        Args:
            execution: Write execution options.
            connection: Target source connection.
            items: Items to write.

        Returns:
            Structured write result.
        """
        client_requested_at = datetime.now(tz=UTC)
        if execution.dry_run:
            return self._dry_run_result(execution, connection, items, client_requested_at)

        fc = self._resolve_fc(execution)
        host = connection.host.strip()
        if not host or connection.port <= 0:
            return self._error_result(
                execution, items, "connection_invalid",
                "Host or port is invalid.",
                client_requested_at,
            )

        timeout_s = max(execution.request_timeout_ms / 1000, 2.0)
        item_results: list[SourceWriteItemResult] = []
        raw_results: list[RawWriteItemResult] = []

        async with Iec61850MmsSourceReader(host, connection.port, timeout_seconds=timeout_s) as reader:
            for item in items:
                try:
                    raw = await reader.write(
                        obj_ref=item.node_id,
                        fc=fc,
                        value_type=item.value_type,
                        value=item.value,
                        request_id=f"{execution.protocol}_{item.key}",
                    )
                except Exception as exc:
                    raw = RawWriteItemResult(
                        obj_ref=item.node_id,
                        ok=False,
                        status_code="adapter_error",
                        error_message=str(exc) or type(exc).__name__,
                        value_type=item.value_type,
                    )

                raw_results.append(raw)
                item_results.append(
                    SourceWriteItemResult(
                        key=item.key,
                        node_id=raw.obj_ref,
                        ok=raw.ok,
                        status_code=raw.status_code,
                        error_message=raw.error_message,
                        value_type=raw.value_type or item.value_type,
                    )
                )

        success_count = sum(1 for r in raw_results if r.ok)
        failure_count = len(raw_results) - success_count

        return SourceWriteResult(
            request_id=f"iec61850_mms_write_{datetime.now(tz=UTC).timestamp()}",
            dry_run=False,
            success_count=success_count,
            failure_count=failure_count,
            results=item_results,
            client_requested_at=client_requested_at,
            client_completed_at=datetime.now(tz=UTC),
            attributes={"protocol": "iec61850_mms"},
        )

    @staticmethod
    def _resolve_fc(execution: SourceWriteExecutionOptions) -> str:
        """Resolve functional constraint from execution params."""
        fc = execution.params.get("fc", "SP")
        if isinstance(fc, str):
            return fc.strip().upper()
        return "SP"

    @staticmethod
    def _dry_run_result(
        execution: SourceWriteExecutionOptions,
        connection: SourceConnectionData,
        items: list[SourceWriteItemData],
        client_requested_at: datetime,
    ) -> SourceWriteResult:
        _ = connection
        item_results = [
            SourceWriteItemResult(
                key=item.key,
                node_id=item.node_id,
                ok=False,
                status_code="DRY_RUN",
                error_message="would_write (dry_run mode in adapter)",
                value_type=item.value_type,
            )
            for item in items
        ]
        return SourceWriteResult(
            request_id=f"dry_run_{execution.protocol}",
            dry_run=True,
            success_count=0,
            failure_count=len(item_results),
            results=item_results,
            client_requested_at=client_requested_at,
            client_completed_at=datetime.now(tz=UTC),
            attributes={"protocol": execution.protocol, "mode": "dry_run"},
        )

    @staticmethod
    def _error_result(
        execution: SourceWriteExecutionOptions,
        items: list[SourceWriteItemData],
        error_code: str,
        error_message: str,
        client_requested_at: datetime,
    ) -> SourceWriteResult:
        item_results = [
            SourceWriteItemResult(
                key=item.key,
                node_id=item.node_id,
                ok=False,
                status_code=error_code,
                error_message=error_message,
                value_type=item.value_type,
            )
            for item in items
        ]
        return SourceWriteResult(
            request_id=f"error_{execution.protocol}",
            dry_run=False,
            success_count=0,
            failure_count=len(item_results),
            results=item_results,
            client_requested_at=client_requested_at,
            client_completed_at=datetime.now(tz=UTC),
            attributes={"protocol": execution.protocol, "error": error_code},
        )
