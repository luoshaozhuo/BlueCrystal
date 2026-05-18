# mypy: disable-error-code=import-untyped
"""File loaders that validate field server/profile inputs and build runtime sources."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec

from tools.source_lab.access.providers.base import SourceRuntimeSpec
from tools.source_lab.access.utils import normalize_protocol

_SERVER_REQUIRED_FIELDS = (
    "endpoint_id",
    "profile_id",
    "application_protocol",
    "transport",
    "host",
    "port",
)
_ITEM_REQUIRED_FIELDS = ("profile_id", "address", "data_type")


@dataclass(frozen=True, slots=True)
class FieldEndpointMetadata:
    """Stable field metadata attached to one runtime source."""

    endpoint_id: str
    profile_id: str
    protocol: str


@dataclass(frozen=True, slots=True)
class FieldServerRow:
    """Validated row from ``field_servers`` input."""

    endpoint_id: str
    profile_id: str
    application_protocol: str
    transport: str
    host: str
    port: int
    namespace_uri: str | None
    ied_name: str
    ld_name: str
    params: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class SignalProfileItemRow:
    """Validated row from ``signal_profile_items`` input."""

    profile_id: str
    address: str
    data_type: str
    point_name: str | None
    protocol: str | None
    ln_name: str | None
    do_name: str | None
    unit: str | None


def _detect_dialect(path: Path) -> csv.Dialect:
    """Detect the CSV dialect from filename suffix."""

    class _TsvDialect(csv.excel_tab):
        pass

    if path.suffix.lower() == ".tsv":
        return _TsvDialect()
    return csv.excel()


def _required_value(row: dict[str, str], field: str, *, path: Path, row_number: int) -> str:
    """Return one required field or raise a descriptive validation error."""

    value = row.get(field, "").strip()
    if value == "":
        raise ValueError(f"{path}:{row_number} missing required field '{field}'")
    return value


def _optional_value(row: dict[str, str], field: str) -> str | None:
    """Return one optional field as stripped text or ``None``."""

    value = row.get(field)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _parse_enabled(value: str | None) -> bool:
    """Parse optional enabled flags with permissive truthy defaults."""

    if value is None or value.strip() == "":
        return True
    return value.strip().lower() not in {"0", "false", "no", "off", "disabled"}


def _load_rows(path: Path) -> list[dict[str, str]]:
    """Load raw rows from CSV or TSV input."""

    dialect = _detect_dialect(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, dialect=dialect)
        if reader.fieldnames is None:
            raise ValueError(f"{path}: missing header row")
        return [dict(row) for row in reader]


def load_field_servers(path: Path) -> tuple[FieldServerRow, ...]:
    """Load and validate ``field_servers`` rows.

    Args:
        path: CSV or TSV file path.

    Returns:
        Validated enabled server rows.
    """

    rows = _load_rows(path)
    servers: list[FieldServerRow] = []
    for row_number, row in enumerate(rows, start=2):
        if not _parse_enabled(row.get("enabled")):
            continue
        for field in _SERVER_REQUIRED_FIELDS:
            _required_value(row, field, path=path, row_number=row_number)
        port_text = _required_value(row, "port", path=path, row_number=row_number)
        try:
            port = int(port_text)
        except ValueError as exc:
            raise ValueError(f"{path}:{row_number} invalid integer field 'port': {port_text!r}") from exc
        protocol = normalize_protocol(
            _required_value(row, "application_protocol", path=path, row_number=row_number)
        )
        params = tuple(
            (key, value)
            for key in (
                "security_policy",
                "security_mode",
                "auth_type",
                "username",
                "password",
            )
            if (value := _optional_value(row, key)) is not None
        )
        servers.append(
            FieldServerRow(
                endpoint_id=_required_value(row, "endpoint_id", path=path, row_number=row_number),
                profile_id=_required_value(row, "profile_id", path=path, row_number=row_number),
                application_protocol=protocol,
                transport=_required_value(row, "transport", path=path, row_number=row_number),
                host=_required_value(row, "host", path=path, row_number=row_number),
                port=port,
                namespace_uri=_optional_value(row, "namespace_uri"),
                ied_name=_optional_value(row, "ied_name") or "",
                ld_name=_optional_value(row, "ld_instance_id")
                or _optional_value(row, "ld_name")
                or "",
                params=params,
            )
        )
    return tuple(servers)


def load_signal_profile_items(path: Path) -> tuple[SignalProfileItemRow, ...]:
    """Load and validate ``signal_profile_items`` rows.

    Args:
        path: CSV or TSV file path.

    Returns:
        Validated enabled profile item rows.
    """

    rows = _load_rows(path)
    items: list[SignalProfileItemRow] = []
    for row_number, row in enumerate(rows, start=2):
        if not _parse_enabled(row.get("enabled")):
            continue
        for field in _ITEM_REQUIRED_FIELDS:
            _required_value(row, field, path=path, row_number=row_number)
        protocol = _optional_value(row, "protocol")
        items.append(
            SignalProfileItemRow(
                profile_id=_required_value(row, "profile_id", path=path, row_number=row_number),
                address=_required_value(row, "address", path=path, row_number=row_number),
                data_type=_required_value(row, "data_type", path=path, row_number=row_number),
                point_name=_optional_value(row, "point_name") or _optional_value(row, "item_id"),
                protocol=normalize_protocol(protocol) if protocol is not None else None,
                ln_name=_optional_value(row, "ln_name"),
                do_name=_optional_value(row, "do_name"),
                unit=_optional_value(row, "unit"),
            )
        )
    return tuple(items)


def _group_profile_items(
    items: tuple[SignalProfileItemRow, ...],
) -> dict[str, tuple[SignalProfileItemRow, ...]]:
    """Group validated items by ``profile_id``."""

    grouped: dict[str, list[SignalProfileItemRow]] = {}
    for item in items:
        grouped.setdefault(item.profile_id, []).append(item)
    return {key: tuple(value) for key, value in grouped.items()}


def _known_profile_ids(path: Path) -> set[str]:
    """Return all profile identifiers declared in the raw profile items file."""

    known_ids: set[str] = set()
    for row_number, row in enumerate(_load_rows(path), start=2):
        profile_id = row.get("profile_id", "").strip()
        if profile_id == "":
            raise ValueError(f"{path}:{row_number} missing required field 'profile_id'")
        known_ids.add(profile_id)
    return known_ids


def build_field_runtime_sources(
    servers_path: Path,
    profile_items_path: Path,
    *,
    protocol: str | None = None,
) -> tuple[SourceRuntimeSpec, ...]:
    """Build runtime sources from field TSV/CSV inputs.

    Args:
        servers_path: ``field_servers`` CSV/TSV path.
        profile_items_path: ``signal_profile_items`` CSV/TSV path.
        protocol: Optional normalized protocol filter.

    Returns:
        Runtime sources bound by ``profile_id``.

    Raises:
        ValueError: If any required field is missing or server/profile bindings are invalid.
    """

    servers = load_field_servers(servers_path)
    grouped_items = _group_profile_items(load_signal_profile_items(profile_items_path))
    known_profile_ids = _known_profile_ids(profile_items_path)
    requested_protocol = normalize_protocol(protocol) if protocol is not None else None

    sources: list[SourceRuntimeSpec] = []
    for server in servers:
        if requested_protocol is not None and server.application_protocol != requested_protocol:
            continue
        profile_items = grouped_items.get(server.profile_id)
        if profile_items is None:
            if server.profile_id in known_profile_ids:
                raise ValueError(
                    f"{profile_items_path}: profile_id={server.profile_id!r} has no enabled items for "
                    f"endpoint_id={server.endpoint_id!r}"
                )
            raise ValueError(
                f"{servers_path}: endpoint_id={server.endpoint_id!r} references missing profile_id={server.profile_id!r}"
            )

        points: list[SourcePointSpec] = []
        for item in profile_items:
            if item.protocol is not None and item.protocol != server.application_protocol:
                raise ValueError(
                    "protocol mismatch for "
                    f"endpoint_id={server.endpoint_id!r}, profile_id={server.profile_id!r}: "
                    f"server={server.application_protocol!r}, item={item.protocol!r}"
                )
            points.append(
                SourcePointSpec(
                    address=item.address,
                    name=item.point_name,
                    data_type=item.data_type,
                    ln_name=item.ln_name,
                    do_name=item.do_name,
                    unit=item.unit,
                )
            )

        if not points:
            raise ValueError(
                f"{profile_items_path}: profile_id={server.profile_id!r} has no enabled items for endpoint_id={server.endpoint_id!r}"
            )

        endpoint = SourceEndpointSpec(
            name=server.endpoint_id,
            host=server.host,
            port=server.port,
            protocol=server.application_protocol,
            transport=server.transport,
            namespace_uri=server.namespace_uri,
            ied_name=server.ied_name,
            ld_name=server.ld_name,
            params=dict(server.params),
        )
        metadata = FieldEndpointMetadata(
            endpoint_id=server.endpoint_id,
            profile_id=server.profile_id,
            protocol=server.application_protocol,
        )
        sources.append(
            SourceRuntimeSpec(
                endpoint=endpoint,
                points=tuple(points),
                runtime_handle=metadata,
            )
        )

    return tuple(sources)
