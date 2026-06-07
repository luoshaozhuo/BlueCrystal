"""seahorse CLI 入口 —— 场景生成、导出与校验。

提供四个子命令的 argparse 入口：
    generate-scenario     根据参数生成场景并保存 bundle JSON 和可选 JSONL 时序文件
    export-bundle         加载已有 bundle JSON 并重新导出
    validate-bundle       校验已有 bundle JSON 的完整性和一致性
    export-server-plan    从 bundle JSON 或直接生成 ServerPlan 的 Starfish handoff JSON

安全边界：
- 不连接生产数据库。
- 不调用 whale.ingest、starfish 或其他 Whale 运行时组件。
- CLI 仅操作本地文件系统，不通过网络发送数据。

使用方式：
    python -m seahorse generate-scenario --scenario-id demo --output-dir ./out
    python -m seahorse export-bundle --input ./out/demo_bundle.json --output-dir ./exported
    python -m seahorse validate-bundle --input ./out/demo_bundle.json
    python -m seahorse export-server-plan --input ./out/demo_bundle.json --output-dir ./out
    python -m seahorse export-server-plan --scenario-id demo --seed 42 --output-dir ./out
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from datetime import datetime, timezone


def _build_generate_parser(subparsers: argparse._SubParsersAction) -> None:
    """注册 generate-scenario 子命令。"""
    parser = subparsers.add_parser(
        "generate-scenario",
        help="根据参数生成场景并保存 bundle JSON 文件",
        description="启动 Seahorse 生成器，依据场景配置生成完整的种子计划、"
        "信号值序列、告警事件和控制回写结果，并打包为 ScenarioBundle JSON 文件。",
    )
    parser.add_argument(
        "--scenario-id",
        required=True,
        help="场景唯一标识（必填）",
    )
    parser.add_argument(
        "--name",
        default="",
        help="场景可读名称",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="确定性随机种子（默认 42）",
    )
    parser.add_argument(
        "--asset-count",
        type=int,
        default=1,
        help="要生成的资产数量（默认 1）",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=3600.0,
        help="模拟总时长，单位秒（默认 3600.0）",
    )
    parser.add_argument(
        "--sample-interval",
        type=int,
        default=100,
        help="信号采样间隔，单位毫秒（默认 100）",
    )
    parser.add_argument(
        "--protocol-targets",
        nargs="+",
        default=["OPC_UA"],
        help="目标协议列表（默认 OPC_UA）",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="输出目录路径（默认当前目录）",
    )
    parser.add_argument(
        "--no-jsonl",
        action="store_true",
        help="禁用 JSONL 时序导出",
    )
    parser.add_argument(
        "--start-time",
        default=None,
        help="模拟起始时间，ISO 8601 格式（如 2024-01-01T00:00:00+00:00），"
        "默认使用当前 UTC 时间。注意：使用默认值会导致校验和不可重现。",
    )


def _build_export_parser(subparsers: argparse._SubParsersAction) -> None:
    """注册 export-bundle 子命令。"""
    parser = subparsers.add_parser(
        "export-bundle",
        help="加载已有 bundle JSON 并重新导出",
        description="读取已保存的 ScenarioBundle JSON 文件，重新验证并导出。",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="输入的 bundle JSON 文件路径",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="输出目录路径（默认当前目录）",
    )


def _build_validate_parser(subparsers: argparse._SubParsersAction) -> None:
    """注册 validate-bundle 子命令。"""
    parser = subparsers.add_parser(
        "validate-bundle",
        help="校验 bundle JSON 文件的完整性和一致性",
        description="读取 ScenarioBundle JSON 文件，执行结构完整性、"
        "数据一致性和校验和验证。",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="输入的 bundle JSON 文件路径",
    )


def _build_server_plan_export_parser(subparsers: argparse._SubParsersAction) -> None:
    """注册 export-server-plan 子命令。

    支持两种模式：
    1. 从已有 bundle JSON 文件提取 ServerPlan 并导出。
    2. 直接根据参数生成 ServerPlan 并导出（无需完整 bundle）。
    """
    parser = subparsers.add_parser(
        "export-server-plan",
        help="导出 ServerPlan 为 Starfish handoff JSON 文件",
        description="从已有 ScenarioBundle JSON 中提取 ServerPlan，"
        "或直接根据参数生成 ServerPlan，并导出为 Starfish runtime "
        "可解析的 starfish_server_plan.json 文件。",
    )
    parser.add_argument(
        "--input",
        default=None,
        help="输入的 bundle JSON 文件路径（从已有 bundle 提取模式）",
    )
    parser.add_argument(
        "--scenario-id",
        default=None,
        help="场景唯一标识（直接生成模式，必填）",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="确定性随机种子（直接生成模式，默认 42）",
    )
    parser.add_argument(
        "--asset-count",
        type=int,
        default=1,
        help="资产数量（直接生成模式，默认 1）",
    )
    parser.add_argument(
        "--protocol-targets",
        nargs="+",
        default=["OPC_UA"],
        help="目标协议列表（直接生成模式，默认 OPC_UA）",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="输出目录路径（默认当前目录）",
    )


def _build_parser() -> argparse.ArgumentParser:
    """构建 Seahorse CLI 顶层参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="python -m seahorse",
        description="Seahorse 样例场站生成器 CLI —— 场景生成、导出与校验",
    )
    subparsers = parser.add_subparsers(dest="command", help="可用子命令")
    _build_generate_parser(subparsers)
    _build_export_parser(subparsers)
    _build_validate_parser(subparsers)
    _build_server_plan_export_parser(subparsers)
    return parser


def _run_generate(args: argparse.Namespace) -> int:
    """执行 generate-scenario 子命令。

    Args:
        args: 解析后的命令行参数。

    Returns:
        0 表示成功，1 表示失败。
    """
    from seahorse.models.scenario import ScenarioConfig
    from seahorse.models.bundle import ScenarioBundle
    from seahorse.orchestration import SeahorseGenerator
    from seahorse.exporters.serialization import compute_bundle_checksum
    from seahorse.exporters.bundle_exporter import save_bundle
    from seahorse.exporters.timeseries_exporter import save_timeseries

    # 解析 start_time
    start_time = None
    if args.start_time:
        try:
            start_time = datetime.fromisoformat(args.start_time)
        except ValueError as exc:
            print(f"错误：start_time 格式无效: {exc}", file=sys.stderr)
            return 1

    # 构建场景配置
    if start_time is not None:
        config = ScenarioConfig(
            scenario_id=args.scenario_id,
            name=args.name,
            deterministic_seed=args.seed,
            start_time=start_time,
            duration_seconds=args.duration,
            sample_interval_ms=args.sample_interval,
            asset_count=args.asset_count,
            protocol_targets=args.protocol_targets,
        )
    else:
        config = ScenarioConfig(
            scenario_id=args.scenario_id,
            name=args.name,
            deterministic_seed=args.seed,
            duration_seconds=args.duration,
            sample_interval_ms=args.sample_interval,
            asset_count=args.asset_count,
            protocol_targets=args.protocol_targets,
        )

    # 生成场景
    generator = SeahorseGenerator(config)
    seed_plan, server_plan, signals, alarms, controls = generator.generate()

    # 构建并填充 bundle
    bundle = ScenarioBundle(
        schema_version="1.0.0",
        scenario_version="1.0.0",
        generator_version="0.2.0",
        created_at=datetime.now(timezone.utc),
        scenario_id=config.scenario_id,
        name=config.name,
        deterministic_seed=config.deterministic_seed,
        synthetic=True,
        scenario_config=config,
        scenario_metadata=generator.metadata,
        seed_plan=seed_plan,
        server_plan=server_plan,
        generated_timeseries_sample=signals,
        alarm_events=alarms,
        control_results=controls,
    )
    bundle.checksum = compute_bundle_checksum(bundle)

    # 保存 bundle JSON
    output_dir = Path(args.output_dir)
    bundle_path = save_bundle(bundle, output_dir)
    print(f"bundle JSON 已保存: {bundle_path}")

    # 保存 JSONL 时序（可选）
    if not args.no_jsonl:
        ts_path = save_timeseries(signals, output_dir, scenario_id=args.scenario_id)
        print(f"JSONL 时序已保存: {ts_path}")

    # 打印摘要
    stats = generator.metadata.stats
    print(f"生成摘要: {stats}")
    print(f"校验和: {bundle.checksum[:16]}...")

    if start_time is None:
        print("注意：未指定 --start-time，校验和在下一次运行时可能不同。", file=sys.stderr)

    return 0


def _run_export(args: argparse.Namespace) -> int:
    """执行 export-bundle 子命令。

    Args:
        args: 解析后的命令行参数。

    Returns:
        0 表示成功，1 表示失败。
    """
    import json
    from seahorse.exporters.bundle_validator import validate_bundle_from_dict

    input_path = Path(args.input)
    if not input_path.is_file():
        print(f"错误：输入文件不存在: {input_path}", file=sys.stderr)
        return 1

    try:
        raw = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"错误：JSON 解析失败: {exc}", file=sys.stderr)
        return 1

    # 执行校验
    result = validate_bundle_from_dict(raw)
    if not result.is_valid:
        print("校验失败:")
        for err in result.errors:
            print(f"  [ERROR] {err}")
        for warn in result.warnings:
            print(f"  [WARN]  {warn}")
        return 1

    print("校验通过")
    for p in result.passed_checks:
        print(f"  [PASS] {p}")

    # 重新导出到输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    scenario_id = raw.get("scenario_id", "exported")
    output_path = output_dir / f"{scenario_id}_bundle.json"
    output_path.write_text(
        json.dumps(raw, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"bundle 已重新导出: {output_path}")

    return 0


def _run_validate(args: argparse.Namespace) -> int:
    """执行 validate-bundle 子命令。

    Args:
        args: 解析后的命令行参数。

    Returns:
        0 表示校验通过，1 表示校验失败。
    """
    import json
    from seahorse.exporters.bundle_validator import validate_bundle_from_dict

    input_path = Path(args.input)
    if not input_path.is_file():
        print(f"错误：输入文件不存在: {input_path}", file=sys.stderr)
        return 1

    try:
        raw = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"错误：JSON 解析失败: {exc}", file=sys.stderr)
        return 1

    result = validate_bundle_from_dict(raw)

    if result.errors:
        print("校验错误:")
        for err in result.errors:
            print(f"  [ERROR] {err}")

    if result.warnings:
        print("校验警告:")
        for warn in result.warnings:
            print(f"  [WARN]  {warn}")

    if result.passed_checks:
        print("通过项:")
        for p in result.passed_checks:
            print(f"  [PASS] {p}")

    if result.is_valid:
        print("\n校验结果: 通过")
        return 0
    else:
        print(f"\n校验结果: 失败（{len(result.errors)} 个错误）")
        return 1


def _run_server_plan_export(args: argparse.Namespace) -> int:
    """执行 export-server-plan 子命令。

    支持两种模式：
    1. 指定 --input 时，从已有 bundle JSON 提取 ServerPlan 并导出。
    2. 指定 --scenario-id 时，直接生成最小 ServerPlan 并导出。

    Args:
        args: 解析后的命令行参数。

    Returns:
        0 表示成功，1 表示失败。
    """
    import json
    from pathlib import Path

    from seahorse.exporters.server_plan_exporter import save_server_plan
    from seahorse.exporters.server_plan_validator import validate_server_plan
    from seahorse.models.plan import ServerPlan

    output_dir = Path(args.output_dir)

    if args.input:
        # 模式 1：从已有 bundle JSON 提取 ServerPlan
        input_path = Path(args.input)
        if not input_path.is_file():
            print(f"错误：输入文件不存在: {input_path}", file=sys.stderr)
            return 1

        try:
            raw = json.loads(input_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"错误：JSON 解析失败: {exc}", file=sys.stderr)
            return 1

        server_plan_raw = raw.get("server_plan")
        if not server_plan_raw:
            print("错误：输入 bundle JSON 中缺少 server_plan 字段", file=sys.stderr)
            return 1

        # 从 dict 重建 ServerPlan
        from seahorse.models.plan import ServerEndpointPlan, ServerPointPlan

        server_plan = ServerPlan(
            server_id=server_plan_raw.get("server_id", ""),
            scenario_id=server_plan_raw.get("scenario_id", ""),
            server_name=server_plan_raw.get("server_name", ""),
            endpoints=[
                ServerEndpointPlan(
                    endpoint_name=ep.get("endpoint_name", ""),
                    endpoint_id=ep.get("endpoint_id", ep.get("endpoint_name", "")),
                    protocol=ep.get("protocol", ""),
                    bind_host=ep.get("bind_host", "0.0.0.0"),
                    bind_port=ep.get("bind_port", 0),
                    host=ep.get("host", ep.get("bind_host", "")),
                    port=ep.get("port", ep.get("bind_port", 0)),
                )
                for ep in server_plan_raw.get("endpoints", [])
            ],
            points=[
                ServerPointPlan(
                    point_id=pt.get("point_id", ""),
                    point_name=pt.get("point_name", ""),
                    data_type=pt.get("data_type", "FLOAT64"),
                    access_mode=pt.get("access_mode", "RO"),
                    associated_signal_id=pt.get("associated_signal_id", ""),
                    node_key=pt.get("node_key", ""),
                    variable_key=pt.get("variable_key", ""),
                    value_type=pt.get("value_type", ""),
                )
                for pt in server_plan_raw.get("points", [])
            ],
            synthetic=server_plan_raw.get("synthetic", True),
            strategy_id=server_plan_raw.get("strategy_id", ""),
            capabilities=server_plan_raw.get("capabilities", []),
            update_policy=server_plan_raw.get("update_policy", {}),
            initial_values=server_plan_raw.get("initial_values", {}),
        )
    elif args.scenario_id:
        # 模式 2：直接生成最小 ServerPlan
        from seahorse.models.scenario import ScenarioConfig
        from seahorse.orchestration import SeahorseGenerator

        config = ScenarioConfig(
            scenario_id=args.scenario_id,
            deterministic_seed=args.seed,
            asset_count=args.asset_count,
            protocol_targets=args.protocol_targets,
        )
        generator = SeahorseGenerator(config)
        _, server_plan = generator.generate_minimal()
    else:
        print(
            "错误：必须指定 --input（从 bundle 提取）或 --scenario-id（直接生成）",
            file=sys.stderr,
        )
        return 1

    # 校验 ServerPlan
    result = validate_server_plan(server_plan)
    if result.errors:
        print("ServerPlan 校验错误:")
        for err in result.errors:
            print(f"  [ERROR] {err}")
    if result.warnings:
        print("ServerPlan 校验警告:")
        for warn in result.warnings:
            print(f"  [WARN]  {warn}")

    # 校验失败时仍尝试导出（部分场景可能是有意的不完整）
    saved_path = save_server_plan(server_plan, output_dir)
    print(f"ServerPlan handoff JSON 已保存: {saved_path}")

    if result.is_valid:
        print("ServerPlan 校验通过")
        return 0
    else:
        print(f"ServerPlan 校验未通过（{len(result.errors)} 个错误），但文件已导出")
        return 1


def main(argv: list[str] | None = None) -> int:
    """Seahorse CLI 主入口。

    解析命令行参数并分发到对应的子命令处理函数。

    Args:
        argv: 命令行参数列表，None 时使用 sys.argv[1:]。

    Returns:
        退出码，0 表示成功，非 0 表示失败。
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate-scenario":
        return _run_generate(args)
    elif args.command == "export-bundle":
        return _run_export(args)
    elif args.command == "validate-bundle":
        return _run_validate(args)
    elif args.command == "export-server-plan":
        return _run_server_plan_export(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())


__all__ = ["main"]
