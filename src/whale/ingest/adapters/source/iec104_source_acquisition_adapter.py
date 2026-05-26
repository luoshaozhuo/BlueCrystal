"""IEC 104 source acquisition adapter.

Converts ingest DTOs to shared/source IEC 104 native runner calls
and converts ``RawIec104ReadResult`` to ``AcquiredNodeStateBatch``.
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
from whale.shared.source.iec104.backends import RawIec104ReadResult
from whale.shared.source.iec104.reader import Iec104SourceReader
from whale.shared.utils.time import ensure_utc


class Iec104SourceAcquisitionAdapter(SourceAcquisitionPort):
    """Execute IEC 104 reads via native runner (interrogation)."""

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
        """Execute one IEC 104 batch read (interrogation).

        Args:
            execution: Acquisition execution options.
            connection: Target source connection.
            items: Points to read, each with ``relative_path`` as IOA string.

        Returns:
            A batch object for ingest state cache.

        Raises:
            SourceReadTimeoutError: When underlying read times out.
            SourceBatchMismatchError: When value count != item count.
            SourceReadError: Other read failures.
        """
        ioa_list = self._resolve_ioa_list(connection, items)
        client_received_at = datetime.now(tz=UTC)

        try:
            async with self._build_reader(execution, connection) as reader:
                raw = await reader.read(ioa_list)
        except asyncio.TimeoutError as exc:
            raise SourceReadTimeoutError("iec104 read timed out") from exc
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
            ioa_list=ioa_list,
            raw=raw,
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
            "subscription acquisition is not supported by IEC 104 adapter"
        )

    @staticmethod
    def _resolve_ioa_list(
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
    ) -> list[int]:
        """Convert business ``relative_path`` to integer IOA values."""
        del connection
        ioa_list: list[int] = []
        for item in items:
            path = item.relative_path.strip()
            if path.isdigit() or (path.startswith("-") and path[1:].isdigit()):
                ioa_list.append(int(path))
            else:
                raise ValueError(
                    f"Cannot resolve IEC 104 IOA from relative_path={path!r} "
                    f"for item key={item.key}"
                )
        if not ioa_list:
            raise ValueError("Cannot resolve IEC 104 IOA list (empty items).")
        return ioa_list

    @staticmethod
    def _build_reader(
        execution: AcquisitionExecutionOptions,
        connection: SourceConnectionData,
    ) -> Iec104SourceReader:
        """Construct shared/source IEC 104 reader."""
        host = connection.host.strip()
        if not host:
            raise ValueError("connection.host is required")
        if connection.port <= 0:
            raise ValueError("connection.port must be > 0")
        common_addr = int(connection.params.get("common_address", 1))
        return Iec104SourceReader(host=host, port=connection.port, common_addr=common_addr)

    @staticmethod
    def _to_acquired_batch_from_raw(
        *,
        connection: SourceConnectionData,
        items: list[AcquisitionItemData],
        ioa_list: list[int],
        raw: RawIec104ReadResult,
        client_received_at: datetime,
        client_processed_at: datetime,
    ) -> AcquiredNodeStateBatch:
        if not raw.ok:
            reason = raw.error_reason or raw.exception or "raw_read_failed"
            raise SourceReadError(f"raw read failed: {reason}")

        # Build value list by matching items to IOA
        values: list[AcquiredNodeValue] = []
        for item, ioa in zip(items, ioa_list, strict=True):
            raw_entry = raw.values.get(ioa)
            if raw_entry is None:
                values.append(
                    AcquiredNodeValue(
                        node_key=item.key,
                        value="",
                        quality="UNKNOWN",
                        source_timestamp=None,
                        server_timestamp=ensure_utc(raw.response_timestamp) if raw.response_timestamp else None,
                        client_sequence=None,
                        attributes={
                            "profile_item_id": item.profile_item_id,
                            "relative_path": item.relative_path,
                            "protocol_address": str(ioa),
                            "warning": "ioa_not_found_in_response",
                        },
                    )
                )
            else:
                type_tag, value_str = raw_entry
                values.append(
                    AcquiredNodeValue(
                        node_key=item.key,
                        value=value_str,
                        quality="GOOD",
                        source_timestamp=None,
                        server_timestamp=ensure_utc(raw.response_timestamp) if raw.response_timestamp else None,
                        client_sequence=None,
                        attributes={
                            "profile_item_id": item.profile_item_id,
                            "relative_path": item.relative_path,
                            "protocol_address": str(ioa),
                            "iec104_type": type_tag,
                        },
                    )
                )

        return AcquiredNodeStateBatch(
            source_id=connection.ld_name.strip() or connection.ied_name.strip() or "iec104_source",
            batch_observed_at=ensure_utc(raw.response_timestamp or client_received_at),
            client_received_at=ensure_utc(client_received_at),
            client_processed_at=ensure_utc(client_processed_at),
            values=values,
            availability_status="VALID",
            attributes={"acquisition_kind": "read"},
        )
