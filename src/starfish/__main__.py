"""starfish CLI 入口 —— ServerPlan 加载、smoke、probe、profile、capacity 验证。

提供五个子命令的 argparse 入口：
    load-server-plan       从 JSON 文件加载并校验 ServerPlan 契约
    smoke-server-plan      加载 ServerPlan 并按协议创建真实/stub facade 执行 smoke
    probe-server-plan      加载 ServerPlan 并对各 endpoint 执行最小可用性探测
    profile-server-plan    对 facade read 执行 N 次采样统计
    capacity-server-plan   对 endpoint 做轻量容量扫描

使用方式：
    python -m starfish load-server-plan --input <starfish_server_plan.json>
    python -m starfish smoke-server-plan --input <starfish_server_plan.json>
    python -m starfish probe-server-plan --input <starfish_server_plan.json>
    python -m starfish profile-server-plan --input <starfish_server_plan.json> --iterations 100
    python -m starfish capacity-server-plan --input <starfish_server_plan.json> --point-count 100

安全边界：
- 不连接生产数据库。
- 不调用 whale.ingest、seahorse 或其他 Whale 运行时组件。
- CLI 仅操作本地文件系统（读），不通过网络发送数据。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _build_load_parser(subparsers: argparse._SubParsersAction) -> None:
    """注册 load-server-plan 子命令。"""
    parser = subparsers.add_parser(
        "load-server-plan",
        help="加载并校验 Seahorse 导出的 starfish_server_plan.json 文件",
        description="从 Seahorse handoff JSON 文件读取 ServerPlan 契约，"
        "执行结构校验、字段完整性检查和 payload_hash 一致性验证，"
        "并输出校验报告。",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="starfish_server_plan.json 文件路径",
    )


def _build_smoke_parser(subparsers: argparse._SubParsersAction) -> None:
    """注册 smoke-server-plan 子命令。"""
    parser = subparsers.add_parser(
        "smoke-server-plan",
        help="加载 ServerPlan 并按协议创建 facade 执行最简 smoke 验证",
        description="加载 starfish_server_plan.json 文件，根据各 endpoint "
        "协议创建对应 facade（real / mqtt-lightweight / stub），"
        "执行 load_points、start、health、read、capabilities、stop 验证。"
        "不连接生产数据库，不依赖外部协议服务。",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="starfish_server_plan.json 文件路径",
    )


def _build_probe_parser(subparsers: argparse._SubParsersAction) -> None:
    """注册 probe-server-plan 子命令。"""
    parser = subparsers.add_parser(
        "probe-server-plan",
        help="对各 endpoint facade 执行最小可用性探测",
        description="加载 ServerPlan 并逐 endpoint 创建 facade，"
        "执行最小可用性探测（start/health/load_points/read），"
        "输出每个 endpoint 的 PASS/FAIL/NOT_RUN + reason。",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="starfish_server_plan.json 文件路径",
    )


def _build_profile_parser(subparsers: argparse._SubParsersAction) -> None:
    """注册 profile-server-plan 子命令。"""
    parser = subparsers.add_parser(
        "profile-server-plan",
        help="对 facade read 执行 N 次采样统计耗时",
        description="加载 ServerPlan 并逐 endpoint 创建 facade，"
        "对每个 facade 的 read() 方法执行 N 次采样，"
        "统计 count/min/max/avg 耗时（毫秒）。",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="starfish_server_plan.json 文件路径",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=100,
        help="采样次数（默认 100）",
    )


def _build_capacity_parser(subparsers: argparse._SubParsersAction) -> None:
    """注册 capacity-server-plan 子命令。"""
    parser = subparsers.add_parser(
        "capacity-server-plan",
        help="对 endpoint 做轻量容量扫描",
        description="加载 ServerPlan 并逐 endpoint 创建 facade，"
        "对每个 facade 执行轻量容量扫描（endpoint_count / point_count / "
        "read_count），输出 PASS/FAIL/NOT_RUN + max_tested_points。",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="starfish_server_plan.json 文件路径",
    )
    parser.add_argument(
        "--point-count",
        type=int,
        default=10,
        help="read 调用次数（默认 10）",
    )


def _build_parser() -> argparse.ArgumentParser:
    """构建 Starfish CLI 顶层参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="python -m starfish",
        description="Starfish 多协议 server 模拟工具层 CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="可用子命令")
    _build_load_parser(subparsers)
    _build_smoke_parser(subparsers)
    _build_probe_parser(subparsers)
    _build_profile_parser(subparsers)
    _build_capacity_parser(subparsers)
    return parser


def _run_load(args: argparse.Namespace) -> int:
    """执行 load-server-plan 子命令。

    加载 JSON 文件，执行校验，输出详细报告。

    Args:
        args: 解析后的命令行参数。

    Returns:
        0 表示校验通过，1 表示失败。
    """
    from starfish.loader import load_server_plan

    input_path = Path(args.input)
    print(f"加载 ServerPlan: {input_path}")

    try:
        result = load_server_plan(input_path)
    except FileNotFoundError:
        print(f"错误：文件不存在: {input_path}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"错误：加载失败: {exc}", file=sys.stderr)
        return 1

    # 输出校验结果
    validation = result.validation

    if validation.errors:
        print(f"\n校验错误 ({len(validation.errors)}):")
        for err in validation.errors:
            print(f"  [ERROR] {err}")

    if validation.warnings:
        print(f"\n校验警告 ({len(validation.warnings)}):")
        for warn in validation.warnings:
            print(f"  [WARN]  {warn}")

    if validation.passed_checks:
        print(f"\n通过项 ({len(validation.passed_checks)}):")
        for p in validation.passed_checks:
            print(f"  [PASS] {p}")

    if validation.is_valid:
        plan = result.plan
        if plan:
            print(f"\n加载成功: scenario_id={plan.scenario_id}")
            print(f"  endpoints: {len(plan.endpoints)}")
            print(f"  points: {len(plan.points)}")
            print(f"  capabilities: {plan.capabilities}")
            print(f"  synthetic: {plan.synthetic}")
    else:
        print(f"\n校验失败: {len(validation.errors)} 个错误")
        return 1

    return 0


def _run_smoke(args: argparse.Namespace) -> int:
    """执行 smoke-server-plan 子命令。

    加载 JSON 文件，根据 endpoint 协议创建对应的 facade
    （real / mqtt-lightweight / stub / unavailable），执行最小能力验证：
    load_points、start、health、read、capabilities、stop。

    输出每个 endpoint 的 protocol、point_count、capabilities、mode。

    Args:
        args: 解析后的命令行参数。

    Returns:
        0 表示 smoke 通过，1 表示失败。
    """
    from starfish.loader import load_server_plan
    from starfish.registry.runtime_registry import create_facades

    input_path = Path(args.input)
    print(f"Smoke 验证 ServerPlan: {input_path}")

    # 1. 加载 ServerPlan
    try:
        result = load_server_plan(input_path)
    except FileNotFoundError:
        print(f"错误：文件不存在: {input_path}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"错误：加载失败: {exc}", file=sys.stderr)
        return 1

    if not result.validation.is_valid:
        print(f"错误：校验失败 ({len(result.validation.errors)} 个错误)")
        for err in result.validation.errors:
            print(f"  [ERROR] {err}")
        return 1

    plan = result.plan
    if plan is None:
        print("错误：plan 为 None")
        return 1

    print(f"  scenario_id: {plan.scenario_id}")
    print(f"  endpoints: {len(plan.endpoints)}")
    print(f"  points: {len(plan.points)}")
    print()

    # 2. 根据 protocol 创建对应 facade（工厂 dispatch）
    registry = create_facades(plan)

    # 3. 输出每个 endpoint 的信息
    print("Facade 工厂 dispatch 结果:")
    for entry in registry.entries:
        ep = entry.endpoint
        h = entry.facade.health() if entry.facade is not None else {}
        print(f"  endpoint: {ep.endpoint_id}")
        print(f"    protocol:      {ep.protocol}")
        print(f"    endpoint_count: {len(plan.endpoints)}")
        print(f"    point_count:   {h.get('point_count', len(plan.points))}")
        print(f"    capabilities:  {h.get('capabilities', plan.capabilities)}")
        print(f"    mode:          {entry.mode}")
        if entry.mode not in ("real",):
            print(f"    reason:        {entry.reason}")
        if entry.mode == "rtu-lightweight":
            print("    note:          不等同真实串口现场，无真实 RS-232/RS-485 电气特性")

    # 4. 对每个 facade 执行 smoke
    all_ok = True
    for entry in registry.entries:
        facade = entry.facade
        if facade is None or not entry.available:
            print(f"\n[skip] endpoint={entry.endpoint.endpoint_id}: unavailable")
            continue

        print(f"\n--- smoke {entry.endpoint.endpoint_id} (mode={entry.mode}) ---")

        # 4a. health pre-start
        h = facade.health()
        print(f"[health] status={h.get('status', '?')}, "
              f"plan_loaded={h.get('plan_loaded', False)}, "
              f"points={h.get('point_count', 0)}, "
              f"mode={h.get('mode', entry.mode)}")

        # 4b. start
        try:
            facade.start()
            h2 = facade.health()
            print(f"[start] status={h2.get('status', '?')}, "
                  f"running={h2.get('running', False)}")
        except Exception as exc:
            print(f"[start] 失败: {exc}", file=sys.stderr)
            all_ok = False
            continue

        # 4c. read
        iv = plan.initial_values or {}
        if iv:
            try:
                values = facade.read()
                print(f"[read] 初始值数量: {len(values)}")
                for i, (key, val) in enumerate(values.items()):
                    if i >= 3:
                        print(f"  ... 共 {len(values)} 个点位")
                        break
                    print(f"  {key}={val}")
            except Exception as exc:
                print(f"[read] 失败: {exc}", file=sys.stderr)
                all_ok = False
        else:
            print("[read] 无初始值")

        # 4d. capabilities
        try:
            caps = facade.capabilities()
            print(f"[capabilities] {caps}")
        except Exception as exc:
            print(f"[capabilities] 失败: {exc}", file=sys.stderr)
            all_ok = False

        # 4e. NOT_IMPLEMENTED / subscribe / report 验证（按 mode 差异化）
        if entry.mode == "stub" or entry.mode == "unavailable":
            # stub / unavailable mode: 验证 write/subscribe/report 均为 NOT_IMPLEMENTED
            from starfish.models.plan import UnsupportedOperation
            for method_name in ["write", "subscribe", "report"]:
                try:
                    if method_name == "write":
                        facade.write("test_point", 0)
                    elif method_name == "subscribe":
                        facade.subscribe(["test_point"])
                    elif method_name == "report":
                        facade.report()
                    print(f"  [NOT_IMPLEMENTED] {method_name}: 意外完成（应抛 UnsupportedOperation）")
                    all_ok = False
                except UnsupportedOperation as exc:
                    print(f"  [NOT_IMPLEMENTED] {method_name}: {exc}")
            if entry.mode == "unavailable":
                print(f"  [unavailable] binary_reason: {getattr(facade, 'binary_reason', 'unknown')}")
        elif entry.mode == "report-lightweight":
            # report-lightweight mode: report 已实现（轻量 shell），read/write/subscribe NOT_IMPLEMENTED
            from starfish.models.plan import UnsupportedOperation
            # verify report works
            try:
                # 先推送一些事件
                if iv:
                    facade.update_values(iv)
                report_result = facade.report()
                event_count = report_result.get("event_count", 0)
                print(f"  [report] 已实现（轻量: event_count={event_count}）")
            except Exception as exc:
                print(f"  [report] 失败: {exc}", file=sys.stderr)
                all_ok = False
            # verify NOT_IMPLEMENTED: write/subscribe (read 在 IEC61850_REPORT 也是 NOT_IMPLEMENTED)
            for method_name in ["read", "write", "subscribe"]:
                try:
                    if method_name == "read":
                        facade.read(["test_point"])
                    elif method_name == "write":
                        facade.write("test_point", 0)
                    elif method_name == "subscribe":
                        facade.subscribe(["test_point"])
                    print(f"  [NOT_IMPLEMENTED] {method_name}: 意外完成（应抛 UnsupportedOperation）")
                    all_ok = False
                except UnsupportedOperation as exc:
                    print(f"  [NOT_IMPLEMENTED] {method_name}: {exc}")
            print("  [report-lightweight] 不等同完整 IEC61850 Report server，"
                  "真实 runner 标记 environment-pending")
        elif entry.mode == "mqtt-lightweight":
            # mqtt-lightweight mode: subscribe 已实现，write/report 仍 NOT_IMPLEMENTED
            from starfish.models.plan import UnsupportedOperation
            # verify subscribe works
            try:
                sub_q = facade.subscribe(["test_point"])
                result = sub_q.get_nowait()
                print(f"  [subscribe] 已实现: 返回 SubscriptionQueue, "
                      f"立即轮询结果={result}")
            except Exception as exc:
                print(f"  [subscribe] 失败: {exc}", file=sys.stderr)
                all_ok = False
            # verify write/report NOT_IMPLEMENTED
            for method_name in ["write", "report"]:
                try:
                    if method_name == "write":
                        facade.write("test_point", 0)
                    elif method_name == "report":
                        facade.report()
                    print(f"  [NOT_IMPLEMENTED] {method_name}: 意外完成（应抛 UnsupportedOperation）")
                    all_ok = False
                except UnsupportedOperation as exc:
                    print(f"  [NOT_IMPLEMENTED] {method_name}: {exc}")
        elif entry.mode == "rtu-lightweight":
            # rtu-lightweight mode: write 已实现（通过内存），subscribe/report NOT_IMPLEMENTED
            # 注意：PTY 不等同真实串口现场
            from starfish.models.plan import UnsupportedOperation
            if iv:
                try:
                    first_key = next(iter(iv.keys()))
                    facade.write(first_key, 0)
                    print(f"  [write] 已实现 (FC06 via PTY, point={first_key})")
                except Exception as exc:
                    print(f"  [write] 失败: {exc}", file=sys.stderr)
                    all_ok = False
            for method_name in ["subscribe", "report"]:
                try:
                    if method_name == "subscribe":
                        facade.subscribe(["test_point"])
                    elif method_name == "report":
                        facade.report()
                    print(f"  [NOT_IMPLEMENTED] {method_name}: 意外完成（应抛 UnsupportedOperation）")
                    all_ok = False
                except UnsupportedOperation as exc:
                    print(f"  [NOT_IMPLEMENTED] {method_name}: {exc}")
            print("  [rtu-lightweight] PTY 不等同真实串口现场，"
                  "无真实 RS-232/RS-485 电气特性和时序。"
                  "仅用于本地功能验证。")
        elif entry.mode in ("codebase-pending", "environment-pending"):
            # codebase-pending / environment-pending mode: write/subscribe/report 均为 NOT_IMPLEMENTED
            from starfish.models.plan import UnsupportedOperation
            for method_name in ["write", "subscribe", "report"]:
                try:
                    if method_name == "write":
                        facade.write("test_point", 0)
                    elif method_name == "subscribe":
                        facade.subscribe(["test_point"])
                    elif method_name == "report":
                        facade.report()
                    print(f"  [NOT_IMPLEMENTED] {method_name}: 意外完成（应抛 UnsupportedOperation）")
                    all_ok = False
                except UnsupportedOperation as exc:
                    print(f"  [NOT_IMPLEMENTED] {method_name}: {exc}")
        elif entry.mode == "real":
            # 检查是否为 report-capable facade（IEC61850_REPORT）
            protocol = getattr(facade, "protocol", "")
            if protocol == "IEC61850_REPORT":
                from starfish.models.plan import UnsupportedOperation
                # report 已实现
                try:
                    if iv:
                        facade.update_values(iv)
                    report_result = facade.report()
                    event_count = report_result.get("event_count", 0)
                    print(f"  [report] 已实现（real: event_count={event_count}）")
                except Exception as exc:
                    print(f"  [report] 失败: {exc}", file=sys.stderr)
                    all_ok = False
                # read/write/subscribe NOT_IMPLEMENTED
                for method_name in ["read", "write", "subscribe"]:
                    try:
                        if method_name == "read":
                            facade.read(["test_point"])
                        elif method_name == "write":
                            facade.write("test_point", 0)
                        elif method_name == "subscribe":
                            facade.subscribe(["test_point"])
                        print(f"  [NOT_IMPLEMENTED] {method_name}: 意外完成（应抛 UnsupportedOperation）")
                        all_ok = False
                    except UnsupportedOperation as exc:
                        print(f"  [NOT_IMPLEMENTED] {method_name}: {exc}")
            else:
                # 其他 real mode 协议：write/subscribe/report 均为 NOT_IMPLEMENTED
                # 仅有 MODBUS_TCP 的 write 已实现，需特判
                from starfish.models.plan import UnsupportedOperation
                if protocol == "MODBUS_TCP":
                    # write 已实现（使用 plan 中存在的点位）
                    try:
                        if iv:
                            first_key = next(iter(iv.keys()))
                            facade.write(first_key, 0)
                            print(f"  [write] 已实现 (FC06, point={first_key})")
                    except Exception as exc:
                        print(f"  [write] 失败: {exc}", file=sys.stderr)
                        all_ok = False
                    not_impl_methods = ["subscribe", "report"]
                    for method_name in not_impl_methods:
                        try:
                            if method_name == "subscribe":
                                facade.subscribe(["test_point"])
                            elif method_name == "report":
                                facade.report()
                            print(f"  [NOT_IMPLEMENTED] {method_name}: 意外完成（应抛 UnsupportedOperation）")
                            all_ok = False
                        except UnsupportedOperation as exc:
                            print(f"  [NOT_IMPLEMENTED] {method_name}: {exc}")
                elif protocol == "IEC61850_MMS":
                    # IEC61850 MMS: write/subscribe/report NOT_IMPLEMENTED
                    for method_name in ["write", "subscribe", "report"]:
                        try:
                            if method_name == "write":
                                facade.write("test_point", 0)
                            elif method_name == "subscribe":
                                facade.subscribe(["test_point"])
                            elif method_name == "report":
                                facade.report()
                            print(f"  [NOT_IMPLEMENTED] {method_name}: 意外完成（应抛 UnsupportedOperation）")
                            all_ok = False
                        except UnsupportedOperation as exc:
                            print(f"  [NOT_IMPLEMENTED] {method_name}: {exc}")
                elif protocol in ("OPC_UA", "IEC104", "IEC_104"):
                    # OPC_UA/IEC104: write/subscribe/report NOT_IMPLEMENTED
                    for method_name in ["write", "subscribe", "report"]:
                        try:
                            if method_name == "write":
                                facade.write("test_point", 0)
                            elif method_name == "subscribe":
                                facade.subscribe(["test_point"])
                            elif method_name == "report":
                                facade.report()
                            print(f"  [NOT_IMPLEMENTED] {method_name}: 意外完成（应抛 UnsupportedOperation）")
                            all_ok = False
                        except UnsupportedOperation as exc:
                            print(f"  [NOT_IMPLEMENTED] {method_name}: {exc}")

        # 4f. stop
        try:
            facade.stop()
            h3 = facade.health()
            print(f"[stop] status={h3.get('status', '?')}")
        except Exception as exc:
            print(f"[stop] 失败: {exc}", file=sys.stderr)
            all_ok = False

    print(f"\nSmoke 完成: {'通过' if all_ok else '部分未通过'}")
    return 0 if all_ok else 1


def _run_probe(args: argparse.Namespace) -> int:
    """执行 probe-server-plan 子命令。

    加载 ServerPlan，逐 endpoint 创建 facade 并执行最小可用性探测。

    Args:
        args: 解析后的命令行参数。

    Returns:
        0 表示全部通过，1 表示有失败。
    """
    from starfish.loader import load_server_plan
    from starfish.registry.runtime_registry import create_facade_for_endpoint
    from starfish.tools.probe import probe_facade

    input_path = Path(args.input)
    print(f"Probe 探测 ServerPlan: {input_path}")

    # 加载
    try:
        load_result = load_server_plan(input_path)
    except FileNotFoundError:
        print(f"错误：文件不存在: {input_path}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"错误：加载失败: {exc}", file=sys.stderr)
        return 1

    if not load_result.validation.is_valid:
        print(f"错误：校验失败 ({len(load_result.validation.errors)} 个错误)")
        return 1

    plan = load_result.plan
    if plan is None:
        print("错误：plan 为 None")
        return 1

    all_pass = True
    for ep in plan.endpoints:
        print(f"\n--- probe endpoint={ep.endpoint_id} protocol={ep.protocol} ---")
        entry = create_facade_for_endpoint(ep, plan)
        try:
            probe_result = probe_facade(
                entry.facade,
                plan=plan,
                endpoint_id=ep.endpoint_id,
            )
            print(f"  status:   {probe_result.status}")
            print(f"  protocol: {probe_result.protocol}")
            print(f"  mode:     {probe_result.mode}")
            print(f"  reason:   {probe_result.reason}")
            if probe_result.details:
                for key, val in probe_result.details.items():
                    if key == "read" and isinstance(val, dict):
                        print(f"  read:     point_count={val.get('point_count', '?')}")
                    else:
                        print(f"  {key}: {val}")
            if probe_result.status != "PASS":
                all_pass = False
        finally:
            # 确保 facade 已停止
            try:
                entry.facade.stop()
            except Exception:
                pass

    print(f"\nProbe 完成: {'全部通过' if all_pass else '存在失败'}")
    return 0 if all_pass else 1


def _run_profile(args: argparse.Namespace) -> int:
    """执行 profile-server-plan 子命令。

    加载 ServerPlan，逐 endpoint 创建 facade 并执行 read 采样统计。

    Args:
        args: 解析后的命令行参数。

    Returns:
        0 表示全部通过，1 表示有失败。
    """
    from starfish.loader import load_server_plan
    from starfish.registry.runtime_registry import create_facade_for_endpoint
    from starfish.tools.profile import profile_facade

    input_path = Path(args.input)
    iterations = max(1, args.iterations)
    print(f"Profile 采样 ServerPlan: {input_path} (iterations={iterations})")

    try:
        load_result = load_server_plan(input_path)
    except FileNotFoundError:
        print(f"错误：文件不存在: {input_path}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"错误：加载失败: {exc}", file=sys.stderr)
        return 1

    if not load_result.validation.is_valid:
        print(f"错误：校验失败 ({len(load_result.validation.errors)} 个错误)")
        return 1

    plan = load_result.plan
    if plan is None:
        print("错误：plan 为 None")
        return 1

    all_pass = True
    for ep in plan.endpoints:
        print(f"\n--- profile endpoint={ep.endpoint_id} protocol={ep.protocol} ---")
        entry = create_facade_for_endpoint(ep, plan)
        try:
            entry.facade.start()
            profile_result = profile_facade(
                entry.facade,
                iterations=iterations,
                endpoint_id=ep.endpoint_id,
                scenario_id=plan.scenario_id,
            )
            print(f"  status:     {profile_result.status}")
            print(f"  protocol:   {profile_result.protocol}")
            print(f"  mode:       {profile_result.mode}")
            print(f"  iterations: {profile_result.iterations}")
            print(f"  duration_ms: {profile_result.duration_ms:.2f}")
            stats = profile_result.stats
            if stats:
                print(f"  count: {stats.get('count', '?')}, "
                      f"min: {stats.get('min', '?')}ms, "
                      f"max: {stats.get('max', '?')}ms, "
                      f"avg: {stats.get('avg', '?')}ms")
            print(f"  reason:     {profile_result.reason}")
            if profile_result.status != "PASS":
                all_pass = False
        finally:
            try:
                entry.facade.stop()
            except Exception:
                pass

    print(f"\nProfile 完成: {'全部通过' if all_pass else '存在失败'}")
    return 0 if all_pass else 1


def _run_capacity(args: argparse.Namespace) -> int:
    """执行 capacity-server-plan 子命令。

    加载 ServerPlan，逐 endpoint 创建 facade 并执行轻量容量扫描。

    Args:
        args: 解析后的命令行参数。

    Returns:
        0 表示全部通过，1 表示有失败。
    """
    from starfish.loader import load_server_plan
    from starfish.registry.runtime_registry import create_facade_for_endpoint
    from starfish.tools.capacity import capacity_scan

    input_path = Path(args.input)
    read_count = max(1, args.point_count)
    print(f"Capacity 扫描 ServerPlan: {input_path} (read_count={read_count})")

    try:
        load_result = load_server_plan(input_path)
    except FileNotFoundError:
        print(f"错误：文件不存在: {input_path}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"错误：加载失败: {exc}", file=sys.stderr)
        return 1

    if not load_result.validation.is_valid:
        print(f"错误：校验失败 ({len(load_result.validation.errors)} 个错误)")
        return 1

    plan = load_result.plan
    if plan is None:
        print("错误：plan 为 None")
        return 1

    all_pass = True
    for ep in plan.endpoints:
        print(f"\n--- capacity endpoint={ep.endpoint_id} protocol={ep.protocol} ---")
        entry = create_facade_for_endpoint(ep, plan)
        try:
            entry.facade.start()
            cap_result = capacity_scan(
                entry.facade,
                read_count=read_count,
                endpoint_id=ep.endpoint_id,
                scenario_id=plan.scenario_id,
            )
            print(f"  status:            {cap_result.status}")
            print(f"  protocol:          {cap_result.protocol}")
            print(f"  mode:              {cap_result.mode}")
            print(f"  endpoint_count:    {cap_result.endpoint_count}")
            print(f"  point_count:       {cap_result.point_count}")
            print(f"  max_tested_points: {cap_result.max_tested_points}")
            print(f"  read_count:        {cap_result.read_count}")
            print(f"  reason:            {cap_result.reason}")
            if cap_result.status == "FAIL":
                all_pass = False
        finally:
            try:
                entry.facade.stop()
            except Exception:
                pass

    print(f"\nCapacity 完成: {'全部通过' if all_pass else '存在失败'}")
    return 0 if all_pass else 1


def main(argv: list[str] | None = None) -> int:
    """Starfish CLI 主入口。

    解析命令行参数并分发到对应的子命令处理函数。

    Args:
        argv: 命令行参数列表，None 时使用 sys.argv[1:]。

    Returns:
        退出码，0 表示成功，非 0 表示失败。
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "load-server-plan":
        return _run_load(args)
    elif args.command == "smoke-server-plan":
        return _run_smoke(args)
    elif args.command == "probe-server-plan":
        return _run_probe(args)
    elif args.command == "profile-server-plan":
        return _run_profile(args)
    elif args.command == "capacity-server-plan":
        return _run_capacity(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())


__all__ = ["main"]
