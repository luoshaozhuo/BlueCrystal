"""Stable JSON CLI for dynamic endpoint runtime operations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec
from tools.source_lab.access.providers.base import SourceRuntimeSpec
from tools.source_lab.access.runtime.continuity_monitor import ContinuityMonitor
from tools.source_lab.access.runtime.endpoint_registry import EndpointRuntimeRegistry
from tools.source_lab.access.runtime.endpoint_runtime import (
    EndpointMode,
    EndpointRuntimeConfig,
    redact_sensitive_mapping,
    utc_now_iso,
)
from tools.source_lab.access.runtime.session_manager import EndpointSessionManager
from tools.source_lab.access.runtime.stagger_coordinator import StaggerCoordinator
from tools.source_lab.access.runtime.state_store import RuntimeStateStore

_SUPPORTED_PROTOCOLS_BY_MODE: dict[str, set[str]] = {
    "polling": {"modbus_tcp", "http_rest", "opcua"},
    "subscribe": {"mqtt", "opcua"},
    "report": {"iec61850_report"},
    "streaming": {"iec61850_goose", "iec61850_sv"},
}


def build_registry(state_dir: str | None = None) -> EndpointRuntimeRegistry:
    monitor = ContinuityMonitor()
    stagger = StaggerCoordinator()
    session_manager = EndpointSessionManager(
        continuity_monitor=monitor,
        stagger_coordinator=stagger,
    )
    return EndpointRuntimeRegistry(
        session_manager=session_manager,
        continuity_monitor=monitor,
        stagger_coordinator=stagger,
        state_store=RuntimeStateStore(state_dir),
    )


def _config_from_payload(payload: dict[str, object]) -> EndpointRuntimeConfig:
    """将 JSON payload 字典转换为 EndpointRuntimeConfig。

    JSON 反序列化边界处需要 isinstance 收窄，避免将 object 直接传给
    dict/int/float 构造器。
    """
    source_raw = payload.get("source")
    if not isinstance(source_raw, dict):
        raise ValueError(f"source must be a dict, got {type(source_raw)}")
    source_data: dict[str, object] = source_raw

    endpoint_raw = source_data.get("endpoint")
    if not isinstance(endpoint_raw, dict):
        raise ValueError("source.endpoint must be a dict")
    endpoint_data: dict[str, object] = endpoint_raw

    points_raw = source_data.get("points")
    if not isinstance(points_raw, list):
        raise ValueError("source.points must be a list")
    points_data: list[object] = points_raw

    params_raw = endpoint_data.get("params", {})
    if not isinstance(params_raw, dict):
        params_raw = {}

    # 从 endpoint_data dict 提取字段时显式转换为目标类型，
    # 避免 object -> int/str/Optional 的 mypy 类型不匹配
    endpoint_port_raw = endpoint_data.get("port", 0)
    endpoint_port: int = int(endpoint_port_raw)  # type: ignore[call-overload]  # JSON 反序列化边界，dict.get 返回 object

    ns_uri_raw = endpoint_data.get("namespace_uri")
    namespace_uri: str | None = str(ns_uri_raw) if ns_uri_raw is not None else None

    source = SourceRuntimeSpec(
        endpoint=SourceEndpointSpec(
            name=str(endpoint_data["name"]),
            host=str(endpoint_data["host"]),
            port=endpoint_port,
            protocol=str(endpoint_data["protocol"]),
            transport=str(endpoint_data.get("transport", "tcp")),
            namespace_uri=namespace_uri,
            ied_name=str(endpoint_data.get("ied_name", "")),
            ld_name=str(endpoint_data.get("ld_name", "")),
            params=params_raw,
        ),
        points=tuple(
            SourcePointSpec(
                address=str(point["address"]) if isinstance(point, dict) else "",
                name=point.get("name") if isinstance(point, dict) else None,
                data_type=point.get("data_type") if isinstance(point, dict) else None,
                ln_name=point.get("ln_name") if isinstance(point, dict) else None,
                do_name=point.get("do_name") if isinstance(point, dict) else None,
                unit=point.get("unit") if isinstance(point, dict) else None,
            )
            for point in points_data
            if isinstance(point, dict)
        ),
    )

    target_hz_raw = payload.get("target_hz")
    target_hz: float | None = None
    if target_hz_raw is not None:
        target_hz = float(target_hz_raw)  # type: ignore[arg-type]  # JSON 反序列化边界，object 原语经 isinstance 已在 get 之后由运行时保证

    publishing_interval_raw = payload.get("publishing_interval_ms")
    publishing_interval_ms: float | None = None
    if publishing_interval_raw is not None:
        publishing_interval_ms = float(publishing_interval_raw)  # type: ignore[arg-type]

    read_timeout_raw = payload.get("read_timeout_s", 5.0)
    read_timeout_s: float = float(read_timeout_raw) if read_timeout_raw is not None else 5.0  # type: ignore[arg-type]

    config_version_raw = payload.get("config_version", 1)
    if config_version_raw is not None:
        config_version: int = int(config_version_raw)  # type: ignore[call-overload]  # JSON 反序列化边界
    else:
        config_version = 1

    return EndpointRuntimeConfig(
        endpoint_id=str(payload["endpoint_id"]),
        protocol=str(payload["protocol"]),
        mode=EndpointMode(str(payload["mode"])),
        source=source,
        target_hz=target_hz,
        publishing_interval_ms=publishing_interval_ms,
        read_timeout_s=read_timeout_s,
        config_version=config_version,
    )


def _runtime_payload(runtime: object) -> dict[str, object]:
    if hasattr(runtime, "to_dict"):
        raw: object = _redact_payload(dict(runtime.to_dict()))
        if isinstance(raw, dict):
            return raw
        return {"runtime": str(runtime)}
    return {"runtime": str(runtime)}


def _redact_payload(payload: object) -> object:
    if isinstance(payload, dict):
        redacted = redact_sensitive_mapping(payload)
        return {key: _redact_payload(value) for key, value in redacted.items()}
    if isinstance(payload, list):
        return [_redact_payload(item) for item in payload]
    return payload


def _schemas() -> dict[str, dict[str, object]]:
    # 使用显式类型标注避免 mypy 推断 inner dict 为 Collection[str] 导致类型不匹配
    endpoint_schema: dict[str, object] = {
        "type": "object",
        "required": ["endpoint_id", "protocol", "mode", "source", "config_version"],
        "properties": {
            "endpoint_id": {"type": "string"},
            "protocol": {"type": "string"},
            "mode": {"enum": ["polling", "subscribe", "report", "streaming"]},
            "target_hz": {"type": ["number", "null"]},
            "publishing_interval_ms": {"type": ["number", "null"]},
            "read_timeout_s": {"type": "number"},
            "config_version": {"type": "integer"},
            "state": {"type": "string"},
            "source": {"type": "object"},
        },
    }
    return {
        "endpoint": endpoint_schema,
        "operation": {
            "type": "object",
            "required": ["operation_id", "decision", "result", "reason_code"],
            "properties": {
                "operation_id": {"type": "string"},
                "decision": {"type": "string"},
                "result": {"type": "string"},
                "reason_code": {"type": "string"},
            },
        },
        "continuity": {
            "type": "object",
            "required": ["endpoint_actual_samples", "endpoint_config_version"],
            "properties": {
                "endpoint_actual_samples": {"type": "integer"},
                "endpoint_event_count": {"type": "integer"},
                "endpoint_callback_gap_count": {"type": "integer"},
                "endpoint_runtime_backend": {"type": ["string", "null"]},
            },
        },
        "accepted-state": {
            "type": "object",
            "required": [
                "schema_version",
                "bundle_version",
                "redacted",
                "endpoints",
                "checksum",
            ],
            "properties": {
                "schema_version": {"type": "string"},
                "bundle_version": {"type": "string"},
                "redacted": {"type": "boolean"},
                "checksum": {"type": "string"},
                "endpoints": {
                    "type": "array",
                    "items": endpoint_schema,
                },
            },
        },
    }


def _validate_endpoint_payload(payload: dict[str, object]) -> list[str]:
    errors: list[str] = []
    for field in ("endpoint_id", "protocol", "mode", "source", "config_version"):
        if field not in payload:
            errors.append(f"missing:{field}")
    source = payload.get("source")
    if not isinstance(source, dict):
        errors.append("invalid:source")
        return errors
    endpoint = source.get("endpoint")
    points = source.get("points")
    if not isinstance(endpoint, dict):
        errors.append("invalid:source.endpoint")
    else:
        for field in ("name", "host", "port", "protocol"):
            if field not in endpoint:
                errors.append(f"missing:source.endpoint.{field}")
        if str(endpoint.get("host", "")).strip() == "":
            errors.append("invalid:source.endpoint.host")
        try:
            endpoint_port_raw = endpoint.get("port", 0)
            if int(endpoint_port_raw) <= 0:  # type: ignore[call-overload]  # JSON 反序列化边界
                errors.append("invalid:source.endpoint.port")
        except (TypeError, ValueError):
            errors.append("invalid:source.endpoint.port")
    if not isinstance(points, list) or not points:
        errors.append("invalid:source.points")
    mode = str(payload.get("mode", ""))
    protocol = str(payload.get("protocol", ""))
    if mode not in _SUPPORTED_PROTOCOLS_BY_MODE:
        errors.append("invalid:mode")
    elif protocol not in _SUPPORTED_PROTOCOLS_BY_MODE[mode]:
        errors.append("invalid:protocol_for_mode")
    try:
        config_ver_raw = payload.get("config_version", 0)
        if int(config_ver_raw) <= 0:  # type: ignore[call-overload]  # JSON 反序列化边界
            errors.append("invalid:config_version")
    except (TypeError, ValueError):
        errors.append("invalid:config_version")
    if str(payload.get("state", "")).lower() == "deleted":
        errors.append("invalid:deleted_endpoint_in_active_restore_set")
    return errors


def validate_accepted_state_payload(payload: object) -> list[str]:
    store = RuntimeStateStore()
    bundle_errors = store.validate_accepted_state_bundle(payload)
    if not isinstance(payload, dict):
        return bundle_errors
    assert isinstance(payload, dict)
    endpoints = payload.get("endpoints", [])
    errors: list[str] = list(bundle_errors)
    if not isinstance(endpoints, list):
        return errors
    seen_ids: set[str] = set()
    for index, item in enumerate(endpoints):
        if not isinstance(item, dict):
            errors.append(f"invalid_item:{index}")
            continue
        endpoint_id = str(item.get("endpoint_id", ""))
        if endpoint_id in seen_ids:
            errors.append(f"{index}:duplicate:endpoint_id")
        seen_ids.add(endpoint_id)
        item_errors = _validate_endpoint_payload(item)
        errors.extend(f"{index}:{error}" for error in item_errors)
    return errors


def _emit(payload: dict[str, object]) -> int:
    """将 payload 序列化为 JSON 写入 stdout 并返回退出码。

    退出码从 payload 中读取，通过 isinstance 收窄类型后转为 int。
    """
    sys.stdout.write(json.dumps(_redact_payload(payload), ensure_ascii=True, indent=2) + "\n")
    exit_code_raw = payload.get("exit_code", 0)
    if isinstance(exit_code_raw, (int, float)):
        return int(exit_code_raw)
    try:
        return int(str(exit_code_raw))
    except (ValueError, TypeError):
        return 0


def _write_json_file(path: str, payload: object) -> None:
    Path(path).write_text(
        json.dumps(_redact_payload(payload), ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


def _write_jsonl_file(path: str, payload: list[dict[str, object]]) -> None:
    with Path(path).open("w", encoding="utf-8") as handle:
        for item in payload:
            handle.write(json.dumps(_redact_payload(item), ensure_ascii=True) + "\n")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="source-lab-dynamic-cli")
    parser.add_argument("--state-dir", default=None)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-status")
    status = subparsers.add_parser("status")
    status.add_argument("endpoint_id")

    for name in ("pause", "resume", "stop", "delete"):
        action = subparsers.add_parser(name)
        action.add_argument("endpoint_id")

    recover = subparsers.add_parser("recover")
    recover.add_argument("--print-runtime", action="store_true")

    replace_points = subparsers.add_parser("replace-points")
    replace_points.add_argument("endpoint_id")
    replace_points.add_argument("expected_version", type=int)
    replace_points.add_argument("points_json")

    update = subparsers.add_parser("update")
    update.add_argument("endpoint_id")
    update.add_argument("expected_version", type=int)
    update.add_argument("patch_json")

    add = subparsers.add_parser("add")
    add.add_argument("config_json")

    export_state = subparsers.add_parser("export-accepted-state")
    export_state.add_argument("--output", required=True)
    export_state.add_argument("--raw", action="store_true")
    export_state.add_argument("--redacted", action="store_true")

    import_state = subparsers.add_parser("import-accepted-state")
    import_state.add_argument("--file", required=True)

    validate_state = subparsers.add_parser("validate-accepted-state")
    validate_state.add_argument("--file", required=True)

    dump_continuity = subparsers.add_parser("dump-continuity")
    dump_continuity.add_argument("--output", required=True)

    dump_journal = subparsers.add_parser("dump-journal")
    dump_journal.add_argument("--output", required=True)

    inspect_state = subparsers.add_parser("inspect-state-store")
    inspect_state.add_argument("--output", required=False)

    repair_state = subparsers.add_parser("repair-state-store")
    repair_state.add_argument("--from-backup", action="store_true")

    schema = subparsers.add_parser("schema")
    schema.add_argument(
        "--type",
        required=True,
        choices=("endpoint", "operation", "continuity", "accepted-state"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    registry = build_registry(args.state_dir)
    state_store = getattr(registry, "_state_store", RuntimeStateStore(args.state_dir))

    if args.command == "list-status":
        runtimes = [_runtime_payload(runtime) for runtime in registry.list_status()]
        return _emit({"command": "list-status", "runtimes": runtimes, "exit_code": 0})

    if args.command == "status":
        result = registry.status(args.endpoint_id)
        return _emit(
            {
                "command": "status",
                "operation_id": result.operation_id,
                "decision": result.decision,
                "result": result.result,
                "reason_code": result.reason_code,
                "runtime": _runtime_payload(result.runtime) if result.runtime is not None else None,
                "exit_code": 0 if result.result == "STATUS_SUCCESS" else 1,
            }
        )

    if args.command == "recover":
        recovered = registry.recover()
        return _emit(
            {
                "command": "recover",
                "recovered_count": len(recovered),
                "runtimes": [_runtime_payload(runtime) for runtime in recovered] if args.print_runtime else [],
                "exit_code": 0,
            }
        )

    if args.command == "replace-points":
        points_payload = json.loads(args.points_json)
        points = tuple(
            SourcePointSpec(
                address=str(point["address"]),
                name=point.get("name"),
                data_type=point.get("data_type"),
                ln_name=point.get("ln_name"),
                do_name=point.get("do_name"),
                unit=point.get("unit"),
            )
            for point in points_payload
        )
        result = registry.replace_points(args.endpoint_id, points, args.expected_version)
        return _emit(
            {
                "command": "replace-points",
                "operation_id": result.operation_id,
                "decision": result.decision,
                "result": result.result,
                "reason_code": result.reason_code,
                "exit_code": 0 if result.result == "SUCCESS" else 1,
            }
        )

    if args.command == "update":
        patch = json.loads(args.patch_json)
        result = registry.update_endpoint(args.endpoint_id, patch, args.expected_version)
        return _emit(
            {
                "command": "update",
                "operation_id": result.operation_id,
                "decision": result.decision,
                "result": result.result,
                "reason_code": result.reason_code,
                "exit_code": 0 if result.result == "SUCCESS" else 1,
            }
        )

    if args.command == "add":
        config = _config_from_payload(json.loads(args.config_json))
        result = registry.add_endpoint(config)
        return _emit(
            {
                "command": "add",
                "operation_id": result.operation_id,
                "decision": result.decision,
                "result": result.result,
                "reason_code": result.reason_code,
                "exit_code": 0 if result.result == "SUCCESS" else 1,
            }
        )

    if args.command == "export-accepted-state":
        redacted = not args.raw or args.redacted
        payload = state_store.export_accepted_state(redacted=redacted)
        _write_json_file(args.output, payload)
        endpoints_list = payload.get("endpoints", [])
        if not isinstance(endpoints_list, list):
            endpoints_list = []
        return _emit(
            {
                "command": args.command,
                "output": args.output,
                "count": len(endpoints_list),
                "redacted": payload["redacted"],
                "exit_code": 0,
            }
        )

    if args.command == "validate-accepted-state":
        payload = json.loads(Path(args.file).read_text(encoding="utf-8"))
        errors = validate_accepted_state_payload(payload)
        return _emit(
            {
                "command": args.command,
                "file": args.file,
                "valid": not errors,
                "errors": errors,
                "exit_code": 0 if not errors else 1,
            }
        )

    if args.command == "import-accepted-state":
        raw_payload = json.loads(Path(args.file).read_text(encoding="utf-8"))
        errors = validate_accepted_state_payload(raw_payload)
        if isinstance(raw_payload, dict) and bool(raw_payload.get("redacted")):
            errors = [*errors, "redacted_bundle_not_importable"]
        if errors:
            state_store.append_journal_entry(
                {
                    "operation_id": f"cli-import-{utc_now_iso()}",
                    "action": "IMPORT_ACCEPTED_STATE",
                    "endpoint_id": "*",
                    "decision": "DENY",
                    "result": "VALIDATION_ERROR",
                    "reason_code": "accepted_state_schema_invalid",
                    "errors": errors,
                    "timestamp": utc_now_iso(),
                }
            )
            return _emit(
                {
                    "command": args.command,
                    "file": args.file,
                    "valid": False,
                    "errors": errors,
                    "exit_code": 1,
                }
            )
        # validate_accepted_state_payload 收窄后 raw_payload 必为 dict
        assert isinstance(raw_payload, dict)
        state_store.import_accepted_state(raw_payload)
        endpoint_count: int = len(raw_payload.get("endpoints", [])) if isinstance(raw_payload.get("endpoints"), list) else 0
        state_store.append_journal_entry(
            {
                "operation_id": f"cli-import-{utc_now_iso()}",
                "action": "IMPORT_ACCEPTED_STATE",
                "endpoint_id": "*",
                "decision": "ALLOW",
                "result": "SUCCESS",
                "reason_code": "accepted_state_imported",
                "count": endpoint_count,
                "timestamp": utc_now_iso(),
            }
        )
        return _emit(
            {
                "command": args.command,
                "file": args.file,
                "valid": True,
                "count": endpoint_count,
                "exit_code": 0,
            }
        )

    if args.command == "dump-continuity":
        payload = state_store.dump_continuity()
        _write_json_file(args.output, payload)
        return _emit({"command": args.command, "output": args.output, "exit_code": 0})

    if args.command == "dump-journal":
        payload = state_store.load_journal_entries()
        _write_jsonl_file(args.output, payload)
        return _emit({"command": args.command, "output": args.output, "count": len(payload), "exit_code": 0})

    if args.command == "inspect-state-store":
        payload = state_store.inspect_state_store()
        if args.output:
            _write_json_file(args.output, payload)
        return _emit(
            {
                "command": args.command,
                "output": args.output,
                "snapshots": payload,
                "exit_code": 0,
            }
        )

    if args.command == "repair-state-store":
        if not args.from_backup:
            return _emit(
                {
                    "command": args.command,
                    "result": "DENY",
                    "reason_code": "from_backup_flag_required",
                    "exit_code": 1,
                }
            )
        payload = state_store.repair_state_store()
        success = all(item["status"] in {"SUCCESS", "NOT_NEEDED"} for item in payload.values())
        state_store.append_journal_entry(
            {
                "operation_id": f"cli-repair-{utc_now_iso()}",
                "action": "REPAIR_STATE_STORE",
                "endpoint_id": "*",
                "decision": "ALLOW",
                "result": "SUCCESS" if success else "FAILED",
                "reason_code": "repair_completed" if success else "repair_partial_failure",
                "repair_results": payload,
                "timestamp": utc_now_iso(),
            }
        )
        return _emit(
            {
                "command": args.command,
                "result": "SUCCESS" if success else "FAILED",
                "repair_results": payload,
                "exit_code": 0 if success else 1,
            }
        )

    if args.command == "schema":
        return _emit({"command": args.command, "type": args.type, "schema": _schemas()[args.type], "exit_code": 0})

    method_name = f"{args.command}_endpoint"
    result = getattr(registry, method_name)(args.endpoint_id)
    return _emit(
        {
            "command": args.command,
            "operation_id": result.operation_id,
            "decision": result.decision,
            "result": result.result,
            "reason_code": result.reason_code,
            "exit_code": 0 if result.result == "SUCCESS" else 1,
        }
    )


if __name__ == "__main__":
    raise SystemExit(main())
