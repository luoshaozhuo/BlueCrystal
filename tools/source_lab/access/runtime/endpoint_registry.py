"""Endpoint runtime registry with journaling, validation and recovery."""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass
from dataclasses import replace as dataclass_replace
from typing import Callable

from whale.shared.source.access.model import SourcePointSpec
from tools.source_lab.access.runtime.continuity_monitor import ContinuityMonitor
from tools.source_lab.access.runtime.endpoint_runtime import (
    EndpointMode,
    EndpointRuntime,
    EndpointRuntimeConfig,
    EndpointRuntimeState,
    SENSITIVE_PARAM_KEYS,
    redact_sensitive_mapping,
    utc_now_iso,
)
from tools.source_lab.access.runtime.operation_journal import OperationJournalEntry
from tools.source_lab.access.runtime.session_manager import EndpointSessionManager
from tools.source_lab.access.runtime.stagger_coordinator import StaggerCoordinator
from tools.source_lab.access.runtime.state_store import RuntimeStateStore

_SUPPORTED_PROTOCOLS_BY_MODE: dict[EndpointMode, set[str]] = {
    EndpointMode.POLLING: {"modbus_tcp", "http_rest", "opcua"},
    EndpointMode.SUBSCRIBE: {"mqtt", "opcua"},
    EndpointMode.REPORT: {"iec61850_report"},
    EndpointMode.STREAMING: {"iec61850_goose", "iec61850_sv"},
}

_PATCHABLE_FIELDS = {
    "host",
    "mode",
    "params",
    "points",
    "port",
    "protocol",
    "publishing_interval_ms",
    "read_timeout_s",
    "security_params",
    "target_hz",
}


@dataclass(frozen=True, slots=True)
class RegistryOperationResult:
    operation_id: str
    decision: str
    result: str
    endpoint_id: str
    reason_code: str
    runtime: EndpointRuntime | None = None
    recovery_errors: tuple[str, ...] = ()


DecisionHook = Callable[[str, str, dict[str, object]], tuple[bool, str]]


class EndpointRuntimeRegistry:
    def __init__(
        self,
        *,
        session_manager: EndpointSessionManager,
        continuity_monitor: ContinuityMonitor,
        stagger_coordinator: StaggerCoordinator,
        state_store: RuntimeStateStore,
        decision_hook: DecisionHook | None = None,
    ) -> None:
        self._session_manager = session_manager
        self._continuity_monitor = continuity_monitor
        self._stagger_coordinator = stagger_coordinator
        self._state_store = state_store
        self._decision_hook = decision_hook
        self._lock = threading.RLock()
        self._configs: dict[str, EndpointRuntimeConfig] = {}
        self._runtimes: dict[str, EndpointRuntime] = {}

    def add_endpoint(self, spec: EndpointRuntimeConfig) -> RegistryOperationResult:
        with self._lock:
            operation_id = self._new_operation_id()
            denied = self._check_decision(
                "ADD_ENDPOINT",
                spec.endpoint_id,
                {"protocol": spec.protocol, "mode": spec.mode.value},
                operation_id=operation_id,
            )
            if denied is not None:
                return denied

            validation_error = self._validate_config(spec)
            if validation_error is not None:
                return self._record_result(
                    operation_id=operation_id,
                    action="ADD_ENDPOINT",
                    endpoint_id=spec.endpoint_id,
                    decision="DENY",
                    result="VALIDATION_ERROR",
                    reason_code=validation_error,
                    before_config_version=None,
                    after_config_version=None,
                    changed_fields=("source",),
                    affected_endpoints=(spec.endpoint_id,),
                )

            if spec.endpoint_id in self._configs:
                existing = self._configs[spec.endpoint_id]
                return self._record_result(
                    operation_id=operation_id,
                    action="ADD_ENDPOINT",
                    endpoint_id=spec.endpoint_id,
                    decision="DENY",
                    result="CONFLICT",
                    reason_code="endpoint_exists",
                    before_config_version=existing.config_version,
                    after_config_version=existing.config_version,
                    changed_fields=(),
                    affected_endpoints=(spec.endpoint_id,),
                )

            offset_ns, offset_changed = self._stagger_coordinator.assign_offset(spec)
            runtime = EndpointRuntime(
                endpoint_id=spec.endpoint_id,
                protocol=spec.protocol,
                mode=spec.mode.value,
                config_version=spec.config_version,
                state=EndpointRuntimeState.CREATED,
                stagger_offset_ns=offset_ns,
            )
            self._configs[spec.endpoint_id] = spec
            self._runtimes[spec.endpoint_id] = runtime
            self._continuity_monitor.ensure_endpoint(
                spec.endpoint_id,
                config_version=spec.config_version,
                stagger_offset_ns=offset_ns,
                stagger_offset_changed=offset_changed,
            )
            try:
                self._session_manager.start_endpoint(runtime, spec)
            except Exception as exc:
                runtime.state = EndpointRuntimeState.FAILED
                runtime.last_error = str(exc)
                return self._record_result(
                    operation_id=operation_id,
                    action="ADD_ENDPOINT",
                    endpoint_id=spec.endpoint_id,
                    decision="ALLOW",
                    result="FAILED",
                    reason_code="session_start_failed",
                    before_config_version=None,
                    after_config_version=spec.config_version,
                    changed_fields=("source",),
                    affected_endpoints=(spec.endpoint_id,),
                )

            return self._record_result(
                operation_id=operation_id,
                action="ADD_ENDPOINT",
                endpoint_id=spec.endpoint_id,
                decision="ALLOW",
                result="SUCCESS",
                reason_code="added",
                before_config_version=None,
                after_config_version=spec.config_version,
                changed_fields=("source",),
                affected_endpoints=(spec.endpoint_id,),
            )

    def update_endpoint(
        self,
        endpoint_id: str,
        patch: dict[str, object],
        expected_version: int,
    ) -> RegistryOperationResult:
        with self._lock:
            operation_id = self._new_operation_id()
            changed_fields = self._changed_fields_from_patch(patch)
            denied = self._check_decision(
                "UPDATE_ENDPOINT",
                endpoint_id,
                {"patch": self._sanitize_patch_details(patch)},
                operation_id=operation_id,
            )
            if denied is not None:
                return denied

            config = self._configs.get(endpoint_id)
            if config is None:
                return self._record_result(
                    operation_id=operation_id,
                    action="UPDATE_ENDPOINT",
                    endpoint_id=endpoint_id,
                    decision="DENY",
                    result="NOT_FOUND",
                    reason_code="endpoint_missing",
                    before_config_version=None,
                    after_config_version=None,
                    changed_fields=changed_fields,
                    affected_endpoints=(endpoint_id,),
                )
            if config.config_version != expected_version:
                return self._record_result(
                    operation_id=operation_id,
                    action="UPDATE_ENDPOINT",
                    endpoint_id=endpoint_id,
                    decision="DENY",
                    result="CONFLICT",
                    reason_code="expected_version_mismatch",
                    before_config_version=config.config_version,
                    after_config_version=config.config_version,
                    changed_fields=changed_fields,
                    affected_endpoints=(endpoint_id,),
                )

            validation_error = self._validate_patch(config, patch)
            if validation_error is not None:
                return self._record_result(
                    operation_id=operation_id,
                    action="UPDATE_ENDPOINT",
                    endpoint_id=endpoint_id,
                    decision="DENY",
                    result="VALIDATION_ERROR",
                    reason_code=validation_error,
                    before_config_version=config.config_version,
                    after_config_version=config.config_version,
                    changed_fields=changed_fields,
                    affected_endpoints=(endpoint_id,),
                )

            updated_config = self._patched_config(config, patch)
            runtime = self._runtimes[endpoint_id]
            old_config = config
            old_runtime_snapshot = EndpointRuntime.from_dict(runtime.to_dict())

            runtime.state = EndpointRuntimeState.REPLACING
            runtime.updated_at = utc_now_iso()
            runtime.config_version = updated_config.config_version
            try:
                self._session_manager.replace_endpoint(runtime, updated_config)
            except Exception as exc:
                runtime.last_error = str(exc)
                rollback_reason = self._restore_old_session(
                    runtime=runtime,
                    config=old_config,
                    old_runtime_snapshot=old_runtime_snapshot,
                )
                if rollback_reason is None:
                    self._configs[endpoint_id] = old_config
                    self._continuity_monitor.ensure_endpoint(
                        endpoint_id,
                        config_version=old_config.config_version,
                        stagger_offset_ns=old_runtime_snapshot.stagger_offset_ns,
                        stagger_offset_changed=False,
                    )
                    return self._record_result(
                        operation_id=operation_id,
                        action="UPDATE_ENDPOINT",
                        endpoint_id=endpoint_id,
                        decision="ALLOW",
                        result="ROLLBACK",
                        reason_code="replace_failed_old_session_restored",
                        before_config_version=old_config.config_version,
                        after_config_version=old_config.config_version,
                        changed_fields=changed_fields,
                        affected_endpoints=(endpoint_id,),
                    )

                return self._record_result(
                    operation_id=operation_id,
                    action="UPDATE_ENDPOINT",
                    endpoint_id=endpoint_id,
                    decision="ALLOW",
                    result="FAILED",
                    reason_code=rollback_reason,
                    before_config_version=old_config.config_version,
                    after_config_version=updated_config.config_version,
                    changed_fields=changed_fields,
                    affected_endpoints=(endpoint_id,),
                )

            self._configs[endpoint_id] = updated_config
            runtime.protocol = updated_config.protocol
            runtime.mode = updated_config.mode.value
            runtime.config_version = updated_config.config_version
            self._continuity_monitor.ensure_endpoint(
                endpoint_id,
                config_version=updated_config.config_version,
                stagger_offset_ns=runtime.stagger_offset_ns,
                stagger_offset_changed=False,
            )
            return self._record_result(
                operation_id=operation_id,
                action="UPDATE_ENDPOINT",
                endpoint_id=endpoint_id,
                decision="ALLOW",
                result="SUCCESS",
                reason_code="updated",
                before_config_version=config.config_version,
                after_config_version=updated_config.config_version,
                changed_fields=changed_fields,
                affected_endpoints=(endpoint_id,),
            )

    def pause_endpoint(self, endpoint_id: str) -> RegistryOperationResult:
        with self._lock:
            operation_id = self._new_operation_id()
            denied = self._check_decision(
                "PAUSE_ENDPOINT",
                endpoint_id,
                {},
                operation_id=operation_id,
            )
            if denied is not None:
                return denied

            runtime = self._runtimes.get(endpoint_id)
            if runtime is None:
                return self._record_result(
                    operation_id=operation_id,
                    action="PAUSE_ENDPOINT",
                    endpoint_id=endpoint_id,
                    decision="DENY",
                    result="NOT_FOUND",
                    reason_code="endpoint_missing",
                    before_config_version=None,
                    after_config_version=None,
                    changed_fields=(),
                    affected_endpoints=(endpoint_id,),
                )
            if runtime.state == EndpointRuntimeState.PAUSED:
                return self._record_result(
                    operation_id=operation_id,
                    action="PAUSE_ENDPOINT",
                    endpoint_id=endpoint_id,
                    decision="DENY",
                    result="DENY",
                    reason_code="already_paused",
                    before_config_version=runtime.config_version,
                    after_config_version=runtime.config_version,
                    changed_fields=(),
                    affected_endpoints=(endpoint_id,),
                )
            self._session_manager.pause_endpoint(runtime)
            return self._record_result(
                operation_id=operation_id,
                action="PAUSE_ENDPOINT",
                endpoint_id=endpoint_id,
                decision="ALLOW",
                result="SUCCESS",
                reason_code="paused",
                before_config_version=runtime.config_version,
                after_config_version=runtime.config_version,
                changed_fields=(),
                affected_endpoints=(endpoint_id,),
            )

    def resume_endpoint(self, endpoint_id: str) -> RegistryOperationResult:
        with self._lock:
            operation_id = self._new_operation_id()
            denied = self._check_decision(
                "RESUME_ENDPOINT",
                endpoint_id,
                {},
                operation_id=operation_id,
            )
            if denied is not None:
                return denied

            runtime = self._runtimes.get(endpoint_id)
            if runtime is None:
                return self._record_result(
                    operation_id=operation_id,
                    action="RESUME_ENDPOINT",
                    endpoint_id=endpoint_id,
                    decision="DENY",
                    result="NOT_FOUND",
                    reason_code="endpoint_missing",
                    before_config_version=None,
                    after_config_version=None,
                    changed_fields=(),
                    affected_endpoints=(endpoint_id,),
                )
            if runtime.state != EndpointRuntimeState.PAUSED:
                return self._record_result(
                    operation_id=operation_id,
                    action="RESUME_ENDPOINT",
                    endpoint_id=endpoint_id,
                    decision="DENY",
                    result="DENY",
                    reason_code="not_paused",
                    before_config_version=runtime.config_version,
                    after_config_version=runtime.config_version,
                    changed_fields=(),
                    affected_endpoints=(endpoint_id,),
                )
            self._session_manager.resume_endpoint(runtime)
            return self._record_result(
                operation_id=operation_id,
                action="RESUME_ENDPOINT",
                endpoint_id=endpoint_id,
                decision="ALLOW",
                result="SUCCESS",
                reason_code="resumed",
                before_config_version=runtime.config_version,
                after_config_version=runtime.config_version,
                changed_fields=(),
                affected_endpoints=(endpoint_id,),
            )

    def stop_endpoint(self, endpoint_id: str) -> RegistryOperationResult:
        with self._lock:
            operation_id = self._new_operation_id()
            denied = self._check_decision(
                "STOP_ENDPOINT",
                endpoint_id,
                {},
                operation_id=operation_id,
            )
            if denied is not None:
                return denied

            runtime = self._runtimes.get(endpoint_id)
            if runtime is None:
                return self._record_result(
                    operation_id=operation_id,
                    action="STOP_ENDPOINT",
                    endpoint_id=endpoint_id,
                    decision="DENY",
                    result="NOT_FOUND",
                    reason_code="endpoint_missing",
                    before_config_version=None,
                    after_config_version=None,
                    changed_fields=(),
                    affected_endpoints=(endpoint_id,),
                )
            self._session_manager.stop_endpoint(runtime)
            return self._record_result(
                operation_id=operation_id,
                action="STOP_ENDPOINT",
                endpoint_id=endpoint_id,
                decision="ALLOW",
                result="SUCCESS",
                reason_code="stopped",
                before_config_version=runtime.config_version,
                after_config_version=runtime.config_version,
                changed_fields=(),
                affected_endpoints=(endpoint_id,),
            )

    def delete_endpoint(self, endpoint_id: str) -> RegistryOperationResult:
        with self._lock:
            operation_id = self._new_operation_id()
            denied = self._check_decision(
                "DELETE_ENDPOINT",
                endpoint_id,
                {},
                operation_id=operation_id,
            )
            if denied is not None:
                return denied

            runtime = self._runtimes.get(endpoint_id)
            config = self._configs.get(endpoint_id)
            if runtime is None or config is None:
                return self._record_result(
                    operation_id=operation_id,
                    action="DELETE_ENDPOINT",
                    endpoint_id=endpoint_id,
                    decision="DENY",
                    result="NOT_FOUND",
                    reason_code="endpoint_missing",
                    before_config_version=None,
                    after_config_version=None,
                    changed_fields=(),
                    affected_endpoints=(endpoint_id,),
                )

            self._session_manager.stop_endpoint(runtime)
            runtime.state = EndpointRuntimeState.DELETED
            runtime.updated_at = utc_now_iso()
            self._configs.pop(endpoint_id, None)
            self._stagger_coordinator.delete_offset(endpoint_id)
            return self._record_result(
                operation_id=operation_id,
                action="DELETE_ENDPOINT",
                endpoint_id=endpoint_id,
                decision="ALLOW",
                result="SUCCESS",
                reason_code="deleted",
                before_config_version=config.config_version,
                after_config_version=None,
                changed_fields=("deleted",),
                affected_endpoints=(endpoint_id,),
            )

    def replace_points(
        self,
        endpoint_id: str,
        points: tuple[SourcePointSpec, ...],
        expected_version: int,
    ) -> RegistryOperationResult:
        return self.update_endpoint(endpoint_id, {"points": points}, expected_version)

    def status(self, endpoint_id: str) -> RegistryOperationResult:
        with self._lock:
            operation_id = self._new_operation_id()
            denied = self._check_decision(
                "STATUS_ENDPOINT",
                endpoint_id,
                {},
                operation_id=operation_id,
                denied_result="STATUS_DENIED",
            )
            if denied is not None:
                return denied

            runtime = self._runtimes.get(endpoint_id)
            if runtime is None:
                return self._record_result(
                    operation_id=operation_id,
                    action="STATUS_ENDPOINT",
                    endpoint_id=endpoint_id,
                    decision="DENY",
                    result="STATUS_NOT_FOUND",
                    reason_code="endpoint_missing",
                    before_config_version=None,
                    after_config_version=None,
                    changed_fields=(),
                    affected_endpoints=(endpoint_id,),
                )
            return self._record_result(
                operation_id=operation_id,
                action="STATUS_ENDPOINT",
                endpoint_id=endpoint_id,
                decision="ALLOW",
                result="STATUS_SUCCESS",
                reason_code="status_ok",
                before_config_version=runtime.config_version,
                after_config_version=runtime.config_version,
                changed_fields=(),
                affected_endpoints=(endpoint_id,),
                runtime=runtime,
            )

    def list_status(self) -> list[EndpointRuntime]:
        with self._lock:
            return [
                EndpointRuntime.from_dict(runtime.to_dict())
                for runtime in self._runtimes.values()
            ]

    def get_config(self, endpoint_id: str) -> EndpointRuntimeConfig | None:
        with self._lock:
            return self._configs.get(endpoint_id)

    def recover(self) -> list[EndpointRuntime]:
        with self._lock:
            bundle = self._state_store.load_recovery_bundle()
            recovery_errors = list(bundle.errors.values())
            selected_backups = bundle.selected_backups

            runtime_snapshot_data: dict[str, dict[str, object]]
            continuity_snapshot_data: dict[str, dict[str, object]]
            try:
                runtime_snapshot_data = {
                    endpoint_id: dict(payload)
                    for endpoint_id, payload in dict(bundle.runtime_snapshot.payload).items()
                }
            except Exception as exc:
                runtime_snapshot_data = {}
                recovery_errors.append(f"runtime_snapshot_invalid_shape: {type(exc).__name__}: {exc}")
            try:
                continuity_snapshot_data = {
                    endpoint_id: dict(payload)
                    for endpoint_id, payload in dict(bundle.continuity_snapshot.payload).items()
                }
            except Exception as exc:
                continuity_snapshot_data = {}
                recovery_errors.append(f"continuity_snapshot_invalid_shape: {type(exc).__name__}: {exc}")

            self._stagger_coordinator.load_snapshot(
                {
                    endpoint_id: int(payload.get("stagger_offset_ns", 0))
                    for endpoint_id, payload in runtime_snapshot_data.items()
                }
            )
            self._continuity_monitor.load_snapshot(continuity_snapshot_data)

            accepted_payload = bundle.accepted_endpoints.payload
            accepted = list(accepted_payload) if isinstance(accepted_payload, list) else []
            if not isinstance(accepted_payload, list):
                recovery_errors.append("accepted_endpoints_invalid_shape")

            self._configs = {}
            self._runtimes = {}

            recovered: list[EndpointRuntime] = []
            skipped_invalid_endpoints: list[str] = []
            for payload in accepted:
                try:
                    config = EndpointRuntimeConfig.from_dict(dict(payload))
                except Exception:
                    skipped_invalid_endpoints.append(str(dict(payload).get("endpoint_id", "<unknown>")))
                    continue

                runtime_payload = runtime_snapshot_data.get(config.endpoint_id)
                if runtime_payload is None:
                    skipped_invalid_endpoints.append(config.endpoint_id)
                    continue

                runtime = EndpointRuntime.from_dict(runtime_payload)
                if runtime.state == EndpointRuntimeState.DELETED:
                    continue

                validation_error = self._validate_config(config)
                if validation_error is not None:
                    skipped_invalid_endpoints.append(f"{config.endpoint_id}:{validation_error}")
                    continue

                self._configs[config.endpoint_id] = config
                self._runtimes[config.endpoint_id] = runtime
                self._continuity_monitor.ensure_endpoint(
                    config.endpoint_id,
                    config_version=config.config_version,
                    stagger_offset_ns=runtime.stagger_offset_ns,
                    stagger_offset_changed=False,
                )
                if runtime.state == EndpointRuntimeState.PAUSED:
                    recovered.append(runtime)
                    continue

                if runtime.state in {
                    EndpointRuntimeState.RUNNING,
                    EndpointRuntimeState.STARTING,
                    EndpointRuntimeState.REPLACING,
                    EndpointRuntimeState.STOPPED,
                    EndpointRuntimeState.FAILED,
                }:
                    try:
                        self._session_manager.start_endpoint(runtime, config)
                    except Exception as exc:
                        runtime.state = EndpointRuntimeState.FAILED
                        runtime.last_error = str(exc)
                        recovery_errors.append(f"start_failed:{config.endpoint_id}:{exc}")
                recovered.append(runtime)

            if skipped_invalid_endpoints:
                recovery_errors.extend(
                    f"invalid_endpoint:{endpoint_id}" for endpoint_id in skipped_invalid_endpoints
                )

            result = "SUCCESS" if not recovery_errors else "FAILED"
            reason_code = "recovery_completed" if not recovery_errors else "partial_recovery_failure"
            self._record_result(
                operation_id=self._new_operation_id(),
                action="RECOVER",
                endpoint_id="*",
                decision="ALLOW",
                result=result,
                reason_code=reason_code,
                before_config_version=None,
                after_config_version=None,
                changed_fields=("recover",),
                affected_endpoints=tuple(runtime.endpoint_id for runtime in recovered),
                recovery_errors=tuple(recovery_errors),
                extra_payload={"selected_backups": selected_backups} if selected_backups else None,
            )
            return recovered

    def _restore_old_session(
        self,
        *,
        runtime: EndpointRuntime,
        config: EndpointRuntimeConfig,
        old_runtime_snapshot: EndpointRuntime,
    ) -> str | None:
        try:
            runtime.protocol = old_runtime_snapshot.protocol
            runtime.mode = old_runtime_snapshot.mode
            runtime.config_version = old_runtime_snapshot.config_version
            runtime.stagger_offset_ns = old_runtime_snapshot.stagger_offset_ns
            runtime.state = EndpointRuntimeState.STOPPED
            runtime.last_error = None
            self._session_manager.start_endpoint(runtime, config)
            return None
        except Exception as exc:
            runtime.state = EndpointRuntimeState.FAILED
            runtime.last_error = str(exc)
            return "replace_failed_rollback_failed"

    def _patched_config(
        self,
        config: EndpointRuntimeConfig,
        patch: dict[str, object],
    ) -> EndpointRuntimeConfig:
        source = config.source
        endpoint = source.endpoint
        if "host" in patch:
            endpoint = dataclass_replace(endpoint, host=str(patch["host"]))
        if "port" in patch:
            endpoint = dataclass_replace(endpoint, port=int(patch["port"]))
        if "protocol" in patch:
            endpoint = dataclass_replace(endpoint, protocol=str(patch["protocol"]))

        merged_params = dict(endpoint.params)
        if "params" in patch:
            merged_params.update(dict(patch["params"]))
        if "security_params" in patch:
            merged_params.update(dict(patch["security_params"]))
        if merged_params != endpoint.params:
            endpoint = dataclass_replace(endpoint, params=merged_params)

        points = tuple(patch["points"]) if "points" in patch else source.points
        source = dataclass_replace(source, endpoint=endpoint, points=points)

        mode = config.mode
        if "mode" in patch:
            mode = EndpointMode(str(patch["mode"]))
        return EndpointRuntimeConfig(
            endpoint_id=config.endpoint_id,
            protocol=str(patch.get("protocol", config.protocol)),
            mode=mode,
            source=source,
            target_hz=(
                float(patch["target_hz"])
                if patch.get("target_hz") is not None
                else config.target_hz
            ),
            publishing_interval_ms=(
                float(patch["publishing_interval_ms"])
                if patch.get("publishing_interval_ms") is not None
                else config.publishing_interval_ms
            ),
            read_timeout_s=float(patch.get("read_timeout_s", config.read_timeout_s)),
            config_version=config.config_version + 1,
        )

    def _validate_config(self, config: EndpointRuntimeConfig) -> str | None:
        if config.mode not in _SUPPORTED_PROTOCOLS_BY_MODE:
            return "unsupported_mode"
        if config.protocol not in _SUPPORTED_PROTOCOLS_BY_MODE[config.mode]:
            return "unsupported_protocol_for_mode"
        port_required = not (
            config.mode == EndpointMode.STREAMING
            and config.source.endpoint.transport == "ethernet_l2"
        )
        if port_required and config.source.endpoint.port <= 0:
            return "invalid_port"
        if not config.source.endpoint.host:
            return "invalid_host"
        if not config.source.points:
            return "empty_points"
        return None

    def _validate_patch(
        self,
        current: EndpointRuntimeConfig,
        patch: dict[str, object],
    ) -> str | None:
        unsupported_fields = sorted(set(patch.keys()) - _PATCHABLE_FIELDS)
        if unsupported_fields:
            return "unsupported_patch_fields"
        if not patch:
            return "empty_patch"

        if "mode" in patch:
            try:
                new_mode = EndpointMode(str(patch["mode"]))
            except ValueError:
                return "invalid_mode"
            if current.protocol not in _SUPPORTED_PROTOCOLS_BY_MODE.get(new_mode, set()):
                return "unsupported_mode_change"

        if "protocol" in patch:
            new_protocol = str(patch["protocol"])
            mode = EndpointMode(str(patch.get("mode", current.mode.value)))
            if new_protocol not in _SUPPORTED_PROTOCOLS_BY_MODE.get(mode, set()):
                return "unsupported_protocol_change"

        if "points" in patch and not tuple(patch["points"]):
            return "empty_points"
        if "port" in patch and int(patch["port"]) <= 0:
            return "invalid_port"
        if "host" in patch and str(patch["host"]).strip() == "":
            return "invalid_host"
        if "params" in patch and not isinstance(patch["params"], dict):
            return "invalid_params"
        if "security_params" in patch and not isinstance(patch["security_params"], dict):
            return "invalid_security_params"
        return None

    def _changed_fields_from_patch(self, patch: dict[str, object]) -> tuple[str, ...]:
        changed_fields: list[str] = []
        for field in sorted(patch.keys()):
            if field == "params":
                params = dict(patch[field])
                if any(key.lower() in SENSITIVE_PARAM_KEYS for key in params):
                    changed_fields.append("security_params")
                protocol_fields = sorted(
                    key
                    for key in params.keys()
                    if key.lower() not in SENSITIVE_PARAM_KEYS
                )
                if protocol_fields:
                    changed_fields.append("protocol_params")
                continue
            if field == "security_params":
                changed_fields.append("security_params")
                continue
            if field == "points":
                changed_fields.append("points")
                continue
            changed_fields.append(field)
        return tuple(dict.fromkeys(changed_fields))

    def _sanitize_patch_details(self, patch: dict[str, object]) -> dict[str, object]:
        sanitized: dict[str, object] = {}
        for key, value in patch.items():
            if key in {"params", "security_params"} and isinstance(value, dict):
                sanitized[key] = redact_sensitive_mapping(dict(value))
                continue
            sanitized[key] = value
        return sanitized

    def _persist(self) -> None:
        self._state_store.save_accepted_endpoints(
            [config.to_dict() for config in self._configs.values()]
        )
        self._state_store.save_registry(
            {
                endpoint_id: {
                    "config_version": config.config_version,
                    "state": self._runtimes[endpoint_id].state.value,
                }
                for endpoint_id, config in self._configs.items()
            }
        )
        self._state_store.save_runtime_snapshot(
            {
                endpoint_id: runtime.to_dict()
                for endpoint_id, runtime in self._runtimes.items()
            }
        )
        self._state_store.save_continuity_snapshot(
            {
                endpoint_id: metrics.to_dict()
                for endpoint_id, metrics in self._continuity_monitor.snapshot().items()
            }
        )

    def _check_decision(
        self,
        action: str,
        endpoint_id: str,
        context: dict[str, object],
        *,
        operation_id: str | None = None,
        denied_result: str = "DENY",
    ) -> RegistryOperationResult | None:
        if self._decision_hook is None:
            return None
        allow, reason_code = self._decision_hook(action, endpoint_id, context)
        if allow:
            return None
        operation_id = operation_id or self._new_operation_id()
        current = self._configs.get(endpoint_id)
        return self._record_result(
            operation_id=operation_id,
            action=action,
            endpoint_id=endpoint_id,
            decision="DENY",
            result=denied_result,
            reason_code=reason_code,
            before_config_version=current.config_version if current is not None else None,
            after_config_version=current.config_version if current is not None else None,
            changed_fields=(),
            affected_endpoints=(endpoint_id,),
        )

    def _record_result(
        self,
        *,
        operation_id: str,
        action: str,
        endpoint_id: str,
        decision: str,
        result: str,
        reason_code: str,
        before_config_version: int | None,
        after_config_version: int | None,
        changed_fields: tuple[str, ...],
        affected_endpoints: tuple[str, ...],
        runtime: EndpointRuntime | None = None,
        recovery_errors: tuple[str, ...] = (),
        extra_payload: dict[str, object] | None = None,
    ) -> RegistryOperationResult:
        unaffected_endpoints = tuple(
            other_id
            for other_id in self._configs.keys()
            if other_id not in affected_endpoints
        )
        self._continuity_monitor.tag_operation(
            operation_id=operation_id,
            result=result,
            affected_endpoints=affected_endpoints,
            unaffected_endpoints=unaffected_endpoints,
        )
        entry = OperationJournalEntry.create(
            operation_id=operation_id,
            action=action,
            endpoint_id=endpoint_id,
            decision=decision,
            result=result,
            reason_code=reason_code,
            before_config_version=before_config_version,
            after_config_version=after_config_version,
            changed_fields=changed_fields,
            affected_endpoints=affected_endpoints,
            unaffected_endpoints=unaffected_endpoints,
        )
        payload = entry.to_dict()
        if recovery_errors:
            payload["recovery_errors"] = list(recovery_errors)
        if extra_payload:
            payload.update(redact_sensitive_mapping(extra_payload))
        self._state_store.append_journal_entry(payload)
        self._persist()
        return RegistryOperationResult(
            operation_id=operation_id,
            decision=decision,
            result=result,
            endpoint_id=endpoint_id,
            reason_code=reason_code,
            runtime=runtime,
            recovery_errors=recovery_errors,
        )

    def _new_operation_id(self) -> str:
        return uuid.uuid4().hex
