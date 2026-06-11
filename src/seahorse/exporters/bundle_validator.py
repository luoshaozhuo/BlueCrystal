"""seahorse 场景包校验器。

本模块提供场景包的结构和完整性校验能力，验证包中关键字段
的存在性、一致性和数据完整性。校验结果以结构化形式返回，
便于集成到 CI/CD 或自动验收流程。

校验项：
    1. schema_version 字段存在且非空
    2. scenario_id 在各子计划间一致
    3. seed_plan 和 server_config 存在且非空
    4. generated_timeseries_sample 中所有条目的 synthetic=True
    5. checksum 可复算且与存储值一致
    6. server_config 中 server members / endpoints / points 基本结构存在

安全边界：
- 不得 import whale.ingest。
- 校验仅操作内存数据，无外部副作用。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from seahorse.models.bundle import ScenarioBundle
from seahorse.exporters.serialization import compute_bundle_checksum


@dataclass
class ValidationResult:
    """校验结果 —— 记录单次 bundle 校验的通过/失败明细。

    Attributes:
        is_valid: 全部校验是否通过。
        errors: 错误消息列表（致命问题）。
        warnings: 警告消息列表（非致命但需关注）。
        passed_checks: 已通过的校验项描述列表。
    """

    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    passed_checks: list[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        """记录一条校验错误，同时将 is_valid 置为 False。"""
        self.errors.append(msg)
        self.is_valid = False

    def add_warning(self, msg: str) -> None:
        """记录一条校验警告，不影响 is_valid。"""
        self.warnings.append(msg)

    def add_pass(self, msg: str) -> None:
        """记录一条通过的校验项。"""
        self.passed_checks.append(msg)


def validate_bundle(bundle: ScenarioBundle) -> ValidationResult:
    """对场景包执行完整性校验。

    按顺序执行以下检查，任何错误都不影响后续检查的执行：
    1. schema_version 存在性
    2. scenario_id 一致性（config、seed_plan、server_config）
    3. seed_plan/server_config 存在性
    4. generated_timeseries_sample 中所有信号值的 synthetic 标记
    5. checksum 可复算（与存储值比较）
    6. server_config 的基本结构

    Args:
        bundle: 已填充的场景包（可以是 JSON 反序列化后重建的）。

    Returns:
        包含所有检查结果的 ValidationResult 实例。
    """
    result = ValidationResult()

    # 1. schema_version 存在性
    if not bundle.schema_version:
        result.add_error("schema_version 缺失或为空")
    else:
        result.add_pass(f"schema_version 存在: {bundle.schema_version}")

    # 2. scenario_id 一致性
    config_id = bundle.scenario_config.scenario_id if bundle.scenario_config else ""
    seed_id = bundle.seed_plan.scenario_id if bundle.seed_plan else ""
    server_id = bundle.server_config.scenario_id if bundle.server_config else ""
    bundle_id = bundle.scenario_id

    ids_to_check: dict[str, str] = {
        "bundle.scenario_id": bundle_id,
    }
    if bundle.scenario_config:
        ids_to_check["scenario_config.scenario_id"] = config_id
    if bundle.seed_plan:
        ids_to_check["seed_plan.scenario_id"] = seed_id
    if bundle.server_config:
        ids_to_check["server_config.scenario_id"] = server_id

    unique_ids = set(ids_to_check.values())
    if len(unique_ids) > 1:
        result.add_error(f"scenario_id 不一致: {ids_to_check}")
    elif len(unique_ids) == 0:
        result.add_error("无法获取 scenario_id（所有子计划均为 None）")
    else:
        result.add_pass(f"scenario_id 一致: {next(iter(unique_ids))}")

    # 3. seed_plan / server_config 存在性
    if bundle.seed_plan is None:
        result.add_error("seed_plan 缺失")
    elif not bundle.seed_plan.entities:
        result.add_warning("seed_plan.entities 为空（可能为最小场景）")
    else:
        result.add_pass(f"seed_plan 存在，包含 {len(bundle.seed_plan.entities)} 个实体")

    if bundle.server_config is None:
        result.add_error("server_config 缺失")
    else:
        server_count = len(bundle.server_config.servers) if bundle.server_config.servers else 0
        ep_count = sum(len(server.endpoints) for server in bundle.server_config.servers)
        pt_count = sum(len(server.points) for server in bundle.server_config.servers)
        if server_count == 0:
            result.add_warning("server_config 的 servers 为空")
        else:
            result.add_pass(
                f"server_config 存在，含 {server_count} 个 server members、{ep_count} 个端点、{pt_count} 个点位"
            )

    # 4. generated_timeseries_sample 中 synthetic 一致性
    if not bundle.generated_timeseries_sample:
        result.add_warning("generated_timeseries_sample 为空（无信号值）")
    else:
        non_synthetic = [
            sv.signal_id
            for sv in bundle.generated_timeseries_sample
            if not sv.synthetic
        ]
        if non_synthetic:
            result.add_error(
                f"generated_timeseries_sample 中 {len(non_synthetic)} 条 signal 的 "
                f"synthetic=False（期望全为 True），首条: {non_synthetic[:5]}"
            )
        else:
            result.add_pass(
                f"generated_timeseries_sample ({len(bundle.generated_timeseries_sample)} 条) "
                "全部 synthetic=True"
            )

    # 5. checksum 可复算
    if not bundle.checksum:
        result.add_error("checksum 缺失或为空")
    else:
        try:
            recomputed = compute_bundle_checksum(bundle)
            if recomputed == bundle.checksum:
                result.add_pass(f"checksum 可复算且一致: {bundle.checksum[:16]}...")
            else:
                result.add_error(
                    f"checksum 不匹配: 存储值={bundle.checksum[:16]}..., "
                    f"复算值={recomputed[:16]}..."
                )
        except Exception as exc:
            result.add_error(f"checksum 复算异常: {exc}")

    # 6. server_config 基本结构
    if bundle.server_config is not None:
        for server_index, server in enumerate(bundle.server_config.servers):
            for ep_index, ep in enumerate(server.endpoints):
                if not getattr(ep, "endpoint_name", ""):
                    result.add_warning(f"server_config.servers[{server_index}].endpoints[{ep_index}] 缺少 endpoint_name")
                if not getattr(ep, "protocol", ""):
                    result.add_warning(f"server_config.servers[{server_index}].endpoints[{ep_index}] 缺少 protocol")
            for pt_index, pt in enumerate(server.points):
                if not getattr(pt, "point_id", ""):
                    result.add_warning(f"server_config.servers[{server_index}].points[{pt_index}] 缺少 point_id")
        result.add_pass("server_config 结构检查完成")

    return result


def validate_bundle_from_dict(data: dict[str, Any]) -> ValidationResult:
    """从 JSON 反序列化的 dict 构建 ScenarioBundle 并校验。

    适用于已有 JSON bundle 文件后加载的场景。从 dict 重建
    ScenarioBundle 时需要处理 dataclass 类型还原。

    Args:
        data: 从 JSON 文件加载后得到的字典，包含 bundle 的全部字段。

    Returns:
        ValidationResult 实例。

    Raises:
        TypeError: 如果 dict 结构无法正确映射到 ScenarioBundle 字段。
    """
    from datetime import datetime
    from seahorse.models.scenario import ScenarioConfig, ScenarioMetadata
    from seahorse.models.plan import (
        AcquisitionTaskPlan,
        EndpointPlan,
        SeedEntity,
        SeedPlan,
        ServerConfig,
        ServerEndpointConfig,
        ServerMemberConfig,
        ServerPointConfig,
        SignalProfileItemPlan,
        SignalProfilePlan,
    )
    from seahorse.models.generation import (
        GeneratedAlarmEvent,
        GeneratedControlResult,
        GeneratedSignalValue,
    )

    def _parse_datetime(val: Any) -> Any:
        """将 ISO 格式时间字符串还原为 datetime 对象，失败时原样返回。"""
        if isinstance(val, str):
            try:
                return datetime.fromisoformat(val)
            except (ValueError, TypeError):
                return val
        return val

    # 重建 scenario_config
    scenario_config = None
    if data.get("scenario_config"):
        sc_raw = data["scenario_config"]
        scenario_config = ScenarioConfig(
            scenario_id=sc_raw.get("scenario_id", ""),
            name=sc_raw.get("name", ""),
            deterministic_seed=sc_raw.get("deterministic_seed", 0),
            start_time=_parse_datetime(sc_raw.get("start_time")),
            duration_seconds=sc_raw.get("duration_seconds", 3600.0),
            sample_interval_ms=sc_raw.get("sample_interval_ms", 100),
            asset_count=sc_raw.get("asset_count", 1),
            protocol_targets=sc_raw.get("protocol_targets", []),
        )

    # 重建 seed_plan
    seed_plan = None
    if data.get("seed_plan"):
        sp_raw = data["seed_plan"]
        entities = [
            SeedEntity(
                entity_id=e.get("entity_id", ""),
                entity_type=e.get("entity_type", "WTG"),
                display_name=e.get("display_name", ""),
                parent_entity_id=e.get("parent_entity_id"),
            )
            for e in sp_raw.get("entities", [])
        ]
        signal_profiles = [
            SignalProfilePlan(
                profile_id=p.get("profile_id", ""),
                profile_name=p.get("profile_name", ""),
                standard_family=p.get("standard_family", ""),
                items=[
                    SignalProfileItemPlan(
                        signal_id=item.get("signal_id", ""),
                        signal_name=item.get("signal_name", ""),
                        unit=item.get("unit", ""),
                        data_type=item.get("data_type", "FLOAT64"),
                        ln_class=item.get("ln_class", ""),
                        cdc=item.get("cdc", "MV"),
                        sample_interval_ms=item.get("sample_interval_ms", 100),
                        generation_hint=item.get("generation_hint", "RANDOM"),
                    )
                    for item in p.get("items", [])
                ],
            )
            for p in sp_raw.get("signal_profiles", [])
        ]
        endpoints = [
            EndpointPlan(
                endpoint_id=e.get("endpoint_id", ""),
                application_protocol=e.get("application_protocol", ""),
                service_type=e.get("service_type", ""),
                transport=e.get("transport", "TCP"),
                host=e.get("host"),
                port=e.get("port"),
                endpoint_params=e.get("endpoint_params", {}),
            )
            for e in sp_raw.get("endpoints", [])
        ]
        acquisition_tasks = [
            AcquisitionTaskPlan(
                task_id=t.get("task_id", ""),
                acquisition_mode=t.get("acquisition_mode", "POLLING"),
                poll_interval_ms=t.get("poll_interval_ms", 100),
                request_timeout_ms=t.get("request_timeout_ms", 500),
                associated_endpoint_id=t.get("associated_endpoint_id", ""),
                associated_profile_id=t.get("associated_profile_id", ""),
            )
            for t in sp_raw.get("acquisition_tasks", [])
        ]
        seed_plan = SeedPlan(
            plan_id=sp_raw.get("plan_id", ""),
            scenario_id=sp_raw.get("scenario_id", ""),
            entities=entities,
            signal_profiles=signal_profiles,
            endpoints=endpoints,
            acquisition_tasks=acquisition_tasks,
        )

    # 重建 server_config
    server_config = None
    if data.get("server_config"):
        sv_raw = data["server_config"]
        server_config = ServerConfig(
            config_id=sv_raw.get("config_id", ""),
            scenario_id=sv_raw.get("scenario_id", ""),
            config_name=sv_raw.get("config_name", ""),
            servers=[
                ServerMemberConfig(
                    server_id=server.get("server_id", ""),
                    server_name=server.get("server_name", ""),
                    source_name=server.get("source_name", ""),
                    logical_device_name=server.get("logical_device_name", ""),
                    endpoints=[
                        ServerEndpointConfig(
                            endpoint_name=e.get("endpoint_name", ""),
                            endpoint_id=e.get("endpoint_id", e.get("endpoint_name", "")),
                            protocol=e.get("protocol", ""),
                            bind_host=e.get("bind_host", "0.0.0.0"),
                            bind_port=e.get("bind_port", 0),
                            host=e.get("host", e.get("bind_host", "")),
                            port=e.get("port", e.get("bind_port", 0)),
                        )
                        for e in server.get("endpoints", [])
                    ],
                    points=[
                        ServerPointConfig(
                            point_id=p.get("point_id", ""),
                            point_name=p.get("point_name", ""),
                            data_type=p.get("data_type", "FLOAT64"),
                            access_mode=p.get("access_mode", "RO"),
                            associated_signal_id=p.get("associated_signal_id", ""),
                            node_key=p.get("node_key", ""),
                            variable_key=p.get("variable_key", ""),
                            value_type=p.get("value_type", ""),
                        )
                        for p in server.get("points", [])
                    ],
                    capabilities=server.get("capabilities", []),
                    update_policy=server.get("update_policy", {}),
                    initial_values=server.get("initial_values", {}),
                )
                for server in sv_raw.get("servers", [])
            ],
            synthetic=sv_raw.get("synthetic", True),
            strategy_id=sv_raw.get("strategy_id", ""),
        )

    # 重建 timeseries, alarms, controls
    ts_sample = [
        GeneratedSignalValue(
            signal_id=sv.get("signal_id", ""),
            scenario_id=sv.get("scenario_id", ""),
            source_id=sv.get("source_id", ""),
            device_id=sv.get("device_id", ""),
            profile_item_id=sv.get("profile_item_id", ""),
            node_key=sv.get("node_key", ""),
            variable_key=sv.get("variable_key", ""),
            timestamp=_parse_datetime(sv.get("timestamp")),
            value=float(sv.get("value", 0.0)),
            quality=int(sv.get("quality", 0)),
            unit=sv.get("unit", ""),
            strategy_id=sv.get("strategy_id", ""),
            synthetic=bool(sv.get("synthetic", True)),
        )
        for sv in data.get("generated_timeseries_sample", [])
    ]

    alarm_events = [
        GeneratedAlarmEvent(
            alarm_id=a.get("alarm_id", ""),
            entity_id=a.get("entity_id", ""),
            alarm_type=a.get("alarm_type", ""),
            severity=a.get("severity", "WARNING"),
            timestamp=_parse_datetime(a.get("timestamp")),
            cleared_at=_parse_datetime(a.get("cleared_at")),
            message=a.get("message", ""),
        )
        for a in data.get("alarm_events", [])
    ]

    control_results = [
        GeneratedControlResult(
            control_id=c.get("control_id", ""),
            entity_id=c.get("entity_id", ""),
            control_type=c.get("control_type", ""),
            target_value=float(c.get("target_value", 0.0)),
            result_value=float(c.get("result_value", 0.0)),
            status=c.get("status", "SUCCESS"),
            timestamp=_parse_datetime(c.get("timestamp")),
            message=c.get("message", ""),
        )
        for c in data.get("control_results", [])
    ]

    # 重建 scenario_metadata
    scenario_metadata = None
    if data.get("scenario_metadata"):
        sm = data["scenario_metadata"]
        scenario_metadata = ScenarioMetadata(
            scenario_id=sm.get("scenario_id", ""),
            generated_at=_parse_datetime(sm.get("generated_at")),
            seahorse_version=sm.get("seahorse_version", "0.1.0"),
            config_snapshot=sm.get("config_snapshot", {}),
            stats=sm.get("stats", {}),
        )

    bundle = ScenarioBundle(
        schema_version=data.get("schema_version", ""),
        scenario_version=data.get("scenario_version", ""),
        generator_version=data.get("generator_version", ""),
        created_at=_parse_datetime(data.get("created_at")),
        scenario_id=data.get("scenario_id", ""),
        name=data.get("name", ""),
        deterministic_seed=data.get("deterministic_seed", 0),
        synthetic=data.get("synthetic", True),
        scenario_config=scenario_config,
        scenario_metadata=scenario_metadata,
        seed_plan=seed_plan,
        server_config=server_config,
        generated_timeseries_sample=ts_sample,
        alarm_events=alarm_events,
        control_results=control_results,
        checksum=data.get("checksum", ""),
        replay_metadata=data.get("replay_metadata"),
    )

    return validate_bundle(bundle)


__all__ = ["ValidationResult", "validate_bundle", "validate_bundle_from_dict"]
