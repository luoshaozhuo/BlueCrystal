"""IEC 61850 MMS source acquisition adapter.

Converts ingest DTOs to shared/source libiec61850 MMS calls
and converts ``RawMmsReadResult`` to ``AcquiredNodeStateBatch``.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from whale.ingest.ports.source.source_acquisition_port import (
    SourceAcquisitionPort,
    SourceBatchMismatchError,
    SourceReadError,
    SourceReadTimeoutError,
    SourceSubscriptionHandle,
    SourceSubscriptionUnsupportedError,
    SubscriptionStateHandler,
)
from whale.ingest.usecases.dtos.acquired_node_state import (
    AcquiredNodeStateBatch,
    AcquiredNodeValue,
)
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.shared.source.iec61850.backends import RawMmsReadResult
from whale.shared.source.iec61850.reader import Iec61850MmsSourceReader
from whale.shared.utils.time import ensure_utc


class Iec61850MmsSourceAcquisitionAdapter(SourceAcquisitionPort):
    """Execute IEC 61850 MMS reads via libiec61850 native runner."""

    def supports_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> bool:
        del execution, connection
        return False

    async def read(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> AcquiredNodeStateBatch:
        """Execute one IEC 61850 MMS batch read.

        Each item's ``relative_path`` is the MMS object reference.
        The functional constraint is read from ``connection.params["fc"]``
        or defaults to "NONE".

        Args:
            execution: Acquisition execution options.
            connection: Target source connection.
            items: Points to read, each with relative_path = obj_ref.

        Returns:
            A batch object for ingest state cache.

        Raises:
            SourceReadTimeoutError: When underlying read times out.
            SourceBatchMismatchError: When value count != item count.
            SourceReadError: Other read failures.
        """
        addresses = self._resolve_obj_refs(connection, items)
        fc = self._resolve_fc(connection)
        client_received_at = datetime.now(tz=UTC)

        try:
            async with self._build_reader(execution, connection) as reader:
                raw_results: list[RawMmsReadResult] = []
                for obj_ref in addresses:
                    raw = await reader.read(
                        obj_ref=obj_ref,
                        fc=fc,
                        request_id=f"{execution.protocol}_{connection.ied_name}",
                    )
                    raw_results.append(raw)
        except asyncio.TimeoutError as exc:
            raise SourceReadTimeoutError("iec61850 mms read timed out") from exc
        except FileNotFoundError as exc:
            raise SourceReadError("runner_not_available") from exc
        except RuntimeError as exc:
            message = str(exc)
            if "does not exist" in message:
                raise SourceReadError(f"runner_not_available: {message}") from exc
            raise SourceReadError(message) from exc
        except Exception as exc:
            raise SourceReadError(str(exc) or type(exc).__name__) from exc

        client_processed_at = datetime.now(tz=UTC)
        return self._to_acquired_batch_from_raw(
            connection=connection,
            items=items,
            addresses=addresses,
            raw_results=raw_results,
            client_received_at=client_received_at,
            client_processed_at=client_processed_at,
        )

    async def start_subscription(
        self,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
        *,
        state_received: SubscriptionStateHandler,
    ) -> SourceSubscriptionHandle:
        del execution, connection, items, state_received
        raise SourceSubscriptionUnsupportedError(
            "subscription acquisition is not supported by IEC 61850 MMS adapter"
        )

    @staticmethod
    def _resolve_obj_refs(
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> list[str]:
        """Convert business relative_path to MMS object references."""
        del connection
        obj_refs: list[str] = []
        for item in items:
            path = item.relative_path.strip()
            if not path:
                raise ValueError(
                    f"Empty relative_path for item key={item.key}"
                )
            obj_refs.append(path)
        if not obj_refs:
            raise ValueError("Cannot resolve MMS object references (empty items).")
        return obj_refs

    @staticmethod
    def _resolve_fc(connection: SourceConnectionData) -> str:
        """Resolve the functional constraint from connection params."""
        fc = connection.params.get("fc", "NONE")
        if isinstance(fc, str):
            return fc.strip().upper()
        return "NONE"

    @classmethod
    def _build_reader(
        cls,
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> Iec61850MmsSourceReader:
        """Construct shared/source IEC 61850 MMS reader."""
        host = connection.host.strip()
        if not host:
            raise ValueError("connection.host is required")
        if connection.port <= 0:
            raise ValueError("connection.port must be > 0")
        timeout_s = max(execution.request_timeout_ms / 1000, 2.0)
        return Iec61850MmsSourceReader(
            host=host,
            port=connection.port,
            timeout_seconds=timeout_s,
        )

    @staticmethod
    def _to_acquired_batch_from_raw(
        *,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
        addresses: list[str],
        raw_results: list[RawMmsReadResult],
        client_received_at: datetime,
        client_processed_at: datetime,
    ) -> AcquiredNodeStateBatch:
        """Convert raw MMS read results to ingest batch."""
        if len(raw_results) != len(items):
            raise SourceBatchMismatchError(
                f"raw result count {len(raw_results)} does not match item count {len(items)}"
            )

        values: list[AcquiredNodeValue] = []
        for item, obj_ref, raw in zip(items, addresses, raw_results, strict=True):
            if not raw.ok:
                reason = raw.error_reason or raw.exception or "raw_read_failed"
                raise SourceReadError(
                    f"raw read failed for {obj_ref}: {reason}"
                )

            values.append(
                Iec61850MmsSourceAcquisitionAdapter._to_acquired_value(
                    item=item,
                    obj_ref=obj_ref,
                    raw=raw,
                )
            )

        return AcquiredNodeStateBatch(
            source_id=connection.ld_name.strip() or connection.ied_name.strip() or "iec61850_mms_source",
            batch_observed_at=ensure_utc(client_received_at),
            client_received_at=ensure_utc(client_received_at),
            client_processed_at=ensure_utc(client_processed_at),
            values=values,
            availability_status="VALID",
            attributes={"acquisition_kind": "read"},
        )

    @staticmethod
    def _to_acquired_value(
        *,
        item: AcquisitionItemData,
        obj_ref: str,
        raw: RawMmsReadResult,
    ) -> AcquiredNodeValue:
        attributes: dict[str, object] = {
            "profile_item_id": item.profile_item_id,
            "relative_path": item.relative_path,
            "protocol_address": obj_ref,
        }
        if raw.value_type:
            attributes["mms_value_type"] = raw.value_type

        return AcquiredNodeValue(
            node_key=item.key,
            value=raw.value or "",
            quality="GOOD" if raw.ok else (raw.error_reason or "UNKNOWN"),
            source_timestamp=None,
            server_timestamp=None,
            client_sequence=None,
            attributes=attributes,
        )
