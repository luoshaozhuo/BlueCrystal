"""File-backed runtime state store with lock, checksum, retention and repair."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import shutil
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

from tools.source_lab.access.runtime.endpoint_runtime import redact_sensitive_mapping

_SENSITIVE_MARKER = "***REDACTED***"
_SNAPSHOT_FILES = (
    "accepted_endpoints",
    "registry",
    "runtime_snapshot",
    "continuity_snapshot",
)


def _utc_now_compact() -> str:
    return datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%S%fZ")


def _redact_object(payload: object) -> object:
    if isinstance(payload, dict):
        redacted = redact_sensitive_mapping(payload)
        return {key: _redact_object(value) for key, value in redacted.items()}
    if isinstance(payload, list):
        return [_redact_object(item) for item in payload]
    return payload


@dataclass(frozen=True, slots=True)
class SnapshotLoadResult:
    payload: object
    error: str | None = None
    used_backup: bool = False
    selected_backup: str | None = None


@dataclass(frozen=True, slots=True)
class RecoveryLoadBundle:
    accepted_endpoints: SnapshotLoadResult
    registry: SnapshotLoadResult
    runtime_snapshot: SnapshotLoadResult
    continuity_snapshot: SnapshotLoadResult

    @property
    def errors(self) -> dict[str, str]:
        result: dict[str, str] = {}
        if self.accepted_endpoints.error is not None:
            result["accepted_endpoints"] = self.accepted_endpoints.error
        if self.registry.error is not None:
            result["registry"] = self.registry.error
        if self.runtime_snapshot.error is not None:
            result["runtime_snapshot"] = self.runtime_snapshot.error
        if self.continuity_snapshot.error is not None:
            result["continuity_snapshot"] = self.continuity_snapshot.error
        return result

    @property
    def selected_backups(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for name in _SNAPSHOT_FILES:
            item = getattr(self, name)
            if item.selected_backup is not None:
                result[name] = item.selected_backup
        return result


class RuntimeStateStore:
    def __init__(self, base_dir: str | None = None) -> None:
        resolved_dir = (
            base_dir
            or os.environ.get("SOURCE_LAB_RUNTIME_STATE_DIR")
            or ".source_lab_runtime"
        )
        self.base_dir = Path(resolved_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.accepted_endpoints_path = self.base_dir / "accepted_endpoints.json"
        self.registry_path = self.base_dir / "endpoint_registry.json"
        self.runtime_snapshot_path = self.base_dir / "endpoint_runtime_snapshot.json"
        self.journal_path = self.base_dir / "operation_journal.jsonl"
        self.continuity_path = self.base_dir / "continuity_snapshot.json"
        self.lock_path = self.base_dir / ".runtime_state.lock"
        self.snapshot_retention = max(
            1,
            int(os.environ.get("SOURCE_LAB_RUNTIME_SNAPSHOT_RETENTION", "5")),
        )
        self._snapshot_paths = {
            "accepted_endpoints": self.accepted_endpoints_path,
            "registry": self.registry_path,
            "runtime_snapshot": self.runtime_snapshot_path,
            "continuity_snapshot": self.continuity_path,
        }

    @contextmanager
    def locked(self) -> Iterator[None]:
        self.lock_path.touch(exist_ok=True)
        with self.lock_path.open("r+", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _backup_path(self, path: Path) -> Path:
        return path.with_suffix(path.suffix + ".bak")

    def _versioned_backup_path(self, path: Path, stamp: str) -> Path:
        return path.with_name(f"{path.name}.{stamp}.bak")

    def _list_versioned_backups(self, path: Path) -> list[Path]:
        return sorted(
            path.parent.glob(f"{path.name}.*.bak"),
            key=lambda candidate: candidate.name,
            reverse=True,
        )

    def _prune_versioned_backups(self, path: Path) -> None:
        backups = self._list_versioned_backups(path)
        for candidate in backups[self.snapshot_retention :]:
            candidate.unlink(missing_ok=True)

    def _checksum(self, serialized_payload: str) -> str:
        return hashlib.sha256(serialized_payload.encode("utf-8")).hexdigest()

    def _envelope(self, payload: object) -> dict[str, object]:
        serialized_payload = json.dumps(payload, ensure_ascii=True, sort_keys=True)
        return {
            "checksum": self._checksum(serialized_payload),
            "payload": payload,
        }

    def _accepted_bundle_checksum(self, payload: dict[str, object]) -> str:
        canonical = {
            "schema_version": payload["schema_version"],
            "bundle_version": payload["bundle_version"],
            "redacted": payload["redacted"],
            "endpoints": payload["endpoints"],
        }
        serialized = json.dumps(canonical, ensure_ascii=True, sort_keys=True)
        return self._checksum(serialized)

    def _read_json_with_lock(self, path: Path, *, default: object) -> object:
        with self.locked():
            return self._read_json(path, default=default)

    def _write_json(self, path: Path, payload: object) -> None:
        envelope = self._envelope(payload)
        serialized = json.dumps(envelope, ensure_ascii=True, indent=2, sort_keys=True)
        backup_path = self._backup_path(path)
        with self.locked():
            stamp = _utc_now_compact()
            if path.exists():
                shutil.copy2(path, backup_path)
                shutil.copy2(path, self._versioned_backup_path(path, stamp))
                self._prune_versioned_backups(path)
            with tempfile.NamedTemporaryFile(
                "w",
                dir=path.parent,
                prefix=f".{path.name}.",
                suffix=".tmp",
                encoding="utf-8",
                delete=False,
            ) as handle:
                handle.write(serialized)
                handle.flush()
                os.fsync(handle.fileno())
                temp_path = Path(handle.name)
            os.replace(temp_path, path)

    def _unwrap_envelope(self, path: Path, raw: object) -> object:
        if not isinstance(raw, dict):
            raise ValueError(f"{path.name}: invalid envelope")
        if "payload" not in raw or "checksum" not in raw:
            raise ValueError(f"{path.name}: missing payload/checksum")
        payload = raw["payload"]
        checksum = str(raw["checksum"])
        serialized_payload = json.dumps(payload, ensure_ascii=True, sort_keys=True)
        if checksum != self._checksum(serialized_payload):
            raise ValueError(f"{path.name}: checksum_mismatch")
        return payload

    def _read_json(self, path: Path, *, default: object) -> object:
        if not path.exists():
            return default
        raw = json.loads(path.read_text(encoding="utf-8"))
        return self._unwrap_envelope(path, raw)

    def _sanitize_error(self, path: Path, exc: Exception) -> str:
        text = f"{path.name}: {type(exc).__name__}: {exc}"
        return (
            text.replace("password", _SENSITIVE_MARKER)
            .replace("token", _SENSITIVE_MARKER)
            .replace("username", _SENSITIVE_MARKER)
            .replace("private_key", _SENSITIVE_MARKER)
        )

    def _read_candidate(self, path: Path) -> object:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return self._unwrap_envelope(path, raw)

    def _read_json_resilient(self, path: Path, *, default: object) -> SnapshotLoadResult:
        if not path.exists():
            return SnapshotLoadResult(payload=default)
        with self.locked():
            try:
                return SnapshotLoadResult(payload=self._read_candidate(path))
            except Exception as exc:
                primary_error = self._sanitize_error(path, exc)
                candidates = [self._backup_path(path), *self._list_versioned_backups(path)]
                for candidate in candidates:
                    if not candidate.exists():
                        continue
                    try:
                        return SnapshotLoadResult(
                            payload=self._read_candidate(candidate),
                            error=(
                                f"{primary_error}; recovered_from_backup={candidate.name}"
                            ),
                            used_backup=True,
                            selected_backup=candidate.name,
                        )
                    except Exception:
                        continue
                backup_errors: list[str] = []
                for candidate in candidates:
                    if candidate.exists():
                        try:
                            self._read_candidate(candidate)
                        except Exception as backup_exc:
                            backup_errors.append(self._sanitize_error(candidate, backup_exc))
                suffix = (
                    "; backup_failed=" + " | ".join(backup_errors)
                    if backup_errors
                    else ""
                )
                return SnapshotLoadResult(payload=default, error=primary_error + suffix)

    def _accepted_state_bundle(self, *, redacted: bool) -> dict[str, object]:
        endpoints = self.load_accepted_endpoints()
        registry = self.load_registry()
        bundle_endpoints: list[dict[str, object]] = []
        for endpoint in endpoints:
            item = json.loads(json.dumps(endpoint))
            endpoint_id = str(item.get("endpoint_id", ""))
            state = str(registry.get(endpoint_id, {}).get("state", "running"))
            item["state"] = state
            bundle_endpoints.append(item if not redacted else _redact_object(item))
        bundle = {
            "schema_version": "1.0",
            "bundle_version": _utc_now_compact(),
            "redacted": redacted,
            "endpoints": bundle_endpoints,
        }
        bundle["checksum"] = self._accepted_bundle_checksum(bundle)
        return bundle

    def _validate_accepted_bundle_checksum(self, payload: dict[str, object]) -> bool:
        checksum = payload.get("checksum")
        if not isinstance(checksum, str):
            return False
        return checksum == self._accepted_bundle_checksum(payload)

    def save_accepted_endpoints(self, payload: list[dict[str, object]]) -> None:
        self._write_json(self.accepted_endpoints_path, payload)

    def load_accepted_endpoints(self) -> list[dict[str, object]]:
        return list(self._read_json(self.accepted_endpoints_path, default=[]))

    def save_registry(self, payload: dict[str, dict[str, object]]) -> None:
        self._write_json(self.registry_path, payload)

    def load_registry(self) -> dict[str, dict[str, object]]:
        return dict(self._read_json(self.registry_path, default={}))

    def save_runtime_snapshot(self, payload: dict[str, dict[str, object]]) -> None:
        self._write_json(self.runtime_snapshot_path, payload)

    def load_runtime_snapshot(self) -> dict[str, dict[str, object]]:
        return dict(self._read_json(self.runtime_snapshot_path, default={}))

    def save_continuity_snapshot(self, payload: dict[str, dict[str, object]]) -> None:
        self._write_json(self.continuity_path, payload)

    def load_continuity_snapshot(self) -> dict[str, dict[str, object]]:
        return dict(self._read_json(self.continuity_path, default={}))

    def load_recovery_bundle(self) -> RecoveryLoadBundle:
        return RecoveryLoadBundle(
            accepted_endpoints=self._read_json_resilient(
                self.accepted_endpoints_path,
                default=[],
            ),
            registry=self._read_json_resilient(self.registry_path, default={}),
            runtime_snapshot=self._read_json_resilient(
                self.runtime_snapshot_path,
                default={},
            ),
            continuity_snapshot=self._read_json_resilient(
                self.continuity_path,
                default={},
            ),
        )

    def export_accepted_state(self, *, redacted: bool = True) -> dict[str, object]:
        return self._accepted_state_bundle(redacted=redacted)

    def import_accepted_state(self, payload: dict[str, object]) -> None:
        endpoints = payload.get("endpoints", [])
        if not isinstance(endpoints, list):
            raise ValueError("accepted_state_endpoints_invalid")
        raw_endpoints = []
        for item in endpoints:
            if not isinstance(item, dict):
                raise ValueError("accepted_state_item_invalid")
            raw_item = dict(item)
            raw_item.pop("state", None)
            raw_endpoints.append(raw_item)
        self.save_accepted_endpoints(raw_endpoints)

    def dump_continuity(self) -> dict[str, dict[str, object]]:
        return self.load_continuity_snapshot()

    def dump_registry(self) -> dict[str, dict[str, object]]:
        return self.load_registry()

    def inspect_state_store(self) -> dict[str, dict[str, object]]:
        summary: dict[str, dict[str, object]] = {}
        with self.locked():
            for name, path in self._snapshot_paths.items():
                latest_backup = self._backup_path(path)
                versioned = self._list_versioned_backups(path)
                primary_status = "missing"
                corruption = False
                latest_version = versioned[0].name if versioned else None
                if path.exists():
                    try:
                        self._read_candidate(path)
                        primary_status = "ok"
                    except Exception as exc:
                        primary_status = self._sanitize_error(path, exc)
                        corruption = True
                summary[name] = {
                    "path": str(path),
                    "exists": path.exists(),
                    "checksum_status": primary_status,
                    "backup_count": int(latest_backup.exists()) + len(versioned),
                    "latest_version": latest_version,
                    "retention": self.snapshot_retention,
                    "corruption": corruption,
                    "latest_backup": latest_backup.name if latest_backup.exists() else None,
                    "versioned_backups": [candidate.name for candidate in versioned],
                }
        return summary

    def repair_state_store(self) -> dict[str, dict[str, object]]:
        results: dict[str, dict[str, object]] = {}
        with self.locked():
            for name, path in self._snapshot_paths.items():
                selected: str | None = None
                status = "NOT_NEEDED"
                reason = "primary_ok"
                try:
                    if path.exists():
                        self._read_candidate(path)
                        results[name] = {
                            "status": status,
                            "reason": reason,
                            "selected_backup": None,
                        }
                        continue
                except Exception:
                    status = "FAILED"
                    reason = "checksum_failure"

                for candidate in [self._backup_path(path), *self._list_versioned_backups(path)]:
                    if not candidate.exists():
                        continue
                    try:
                        self._read_candidate(candidate)
                    except Exception:
                        continue
                    shutil.copy2(candidate, path)
                    selected = candidate.name
                    status = "SUCCESS"
                    reason = "restored_from_backup"
                    break

                results[name] = {
                    "status": status,
                    "reason": reason,
                    "selected_backup": selected,
                }
        return results

    def append_journal_entry(self, payload: dict[str, object]) -> None:
        redacted = _redact_object(payload)
        with self.locked():
            with self.journal_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(redacted, ensure_ascii=True) + "\n")

    def load_journal_entries(self) -> list[dict[str, object]]:
        if not self.journal_path.exists():
            return []
        return [
            json.loads(line)
            for line in self.journal_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def validate_accepted_state_bundle(self, payload: object) -> list[str]:
        if not isinstance(payload, dict):
            if isinstance(payload, list):
                return ["legacy_bundle_format_unsupported"]
            return ["accepted_state_not_object"]
        errors: list[str] = []
        schema_version = payload.get("schema_version")
        bundle_version = payload.get("bundle_version")
        endpoints = payload.get("endpoints")
        if not isinstance(schema_version, str) or not schema_version:
            errors.append("missing:schema_version")
        if not isinstance(bundle_version, str) or not bundle_version:
            errors.append("missing:bundle_version")
        if not isinstance(endpoints, list):
            errors.append("missing:endpoints")
            return errors
        if not self._validate_accepted_bundle_checksum(payload):
            errors.append("invalid:checksum")
        return errors
