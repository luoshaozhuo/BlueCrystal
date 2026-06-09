"""starfish CLI 入口 —— ServerPlan 加载、smoke、probe、profile、capacity 验证。

使用方式：

```text
python -m starfish load-server-plan --input <starfish_server_plan.json>
python -m starfish smoke-server-plan --input <starfish_server_plan.json>
python -m starfish probe-server-plan --input <starfish_server_plan.json>
python -m starfish profile-server-plan --input <starfish_server_plan.json> --iterations 100
python -m starfish capacity-server-plan --input <starfish_server_plan.json> --point-count 100
```

模块职责：
- 暴露 5 个子命令：load-server-plan / smoke-server-plan / probe-server-plan
  / profile-server-plan / capacity-server-plan。
- 复用 `starfish.loader` / `starfish.registry.runtime_registry` /
  `starfish.tools.{probe,profile,capacity}`，不重复实现协议解析或 facade 工厂。
- 提供独立可单元测试的 `main(argv) -> int` 入口，封装 typer 的
  `SystemExit` 行为，错误路径以返回值表达退出码。

不负责：
- 真实协议 server 启动（由 facade 负责）。
- 数据落库或生产链路写入。
- 协议 frame 编解码（由 `starfish.protocols` 负责）。

安全边界：
- 不连接生产数据库。
- 不调用 whale.ingest / seahorse 或其他 Whale 运行时组件。
- CLI 仅操作本地 file 系统（只读），不通过网络发送数据。
- 所有 ServerPlan JSON 的 `synthetic=True`，本 CLI 不视作真实现场验证。

退出码约定（与既有契约一致）：
- 0: 成功。
- 1: 业务错误（文件不存在、加载异常、校验失败、plan 为 None、smoke
  任一 endpoint 失败、probe 任一 endpoint 非 PASS、profile 任一 endpoint
  非 PASS、capacity 任一 endpoint FAIL、顶层无子命令）。
- 2: typer/argparse 参数错误（缺必填参数、未知子命令等），由 typer 抛
  `SystemExit` 抛出而非被 `main` 拦截。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Any, Callable

import typer
import typer.main
from typer._click.exceptions import UsageError

# 初始化 Typer 应用。
# `app` 同时是 `python -m starfish` 的入口对象和测试用
# `typer.main.get_group(app)` 的子命令注册载体。测试通过
# `main(argv)` 调用，不直接 import `app`。
app = typer.Typer(
    name="starfish",
    help="Starfish 多协议 server 模拟工具层 CLI",
    rich_markup_mode="rich",
)

# 程序名：在 `main` 中通过 `prog_name=` 显式传入，避免 click 默认行为
# 把 argv[0] 当作 program name 而导致子命令被识别为 extra args。
_PROG_NAME = "starfish"


# ── 私有 helper：ServerPlan 加载 + 校验 + 取 plan ──────────────────────────────


def _load_plan_or_exit(input_path: Path) -> tuple[Any | None, Any]:
    """加载并校验 ServerPlan JSON。

    职责：统一 5 个子命令的「`load_server_plan` + 错误码转换 + 校验
    提示 + 取 plan」模板，调用方只需根据返回值决定退出码。

    Args:
        input_path: ServerPlan JSON 文件路径（来自 CLI `--input`）。

    Returns:
        `(plan, validation)` 二元组：
        - `(plan, validation)`：加载成功且校验通过，`plan` 非 None。
        - `(None, validation_or_None)`：加载失败或校验失败，调用方
          应当返回非 0 退出码。校验失败时 `validation` 仍可能非 None
          （来自 loader 返回），用于子命令继续打印 errors 列表。

    side effect:
        - FileNotFoundError → stderr 写 `错误：文件不存在: ...`。
        - 其它 Exception → stderr 写 `错误：加载失败: ...`。
        - 校验失败 → stdout 写 `错误：校验失败 (N 个错误)`。

    何时记失败：仅在出现预期异常类型时记 1，调用方拿到 `plan is None`
    时直接 `return 1`，避免在 helper 内调用 `typer.Exit` 制造
    `SystemExit`，与本模块 `main()` 入口「错误路径以返回值表达」
    的契约一致。
    """
    from starfish.loader import load_server_plan as _load_plan

    try:
        result = _load_plan(input_path)
    except FileNotFoundError:
        # FileNotFoundError 由 loader 显式 raise，转为 stderr 提示。
        print(f"错误：文件不存在: {input_path}", file=sys.stderr)
        return None, None
    except Exception as exc:
        # JSON 解析错误、ValueError、其它 loader 异常统一兜底。
        # 不区分具体类型，由调用方选择是否继续打印 validation 详情。
        print(f"错误：加载失败: {exc}", file=sys.stderr)
        return None, None

    validation = result.validation
    if not validation.is_valid:
        # 校验失败：保留 validation 返回以便调用方补充错误打印。
        print(f"错误：校验失败 ({len(validation.errors)} 个错误)")
        return None, validation

    plan = result.plan
    if plan is None:
        # 校验通过但 plan 仍为 None（loader 在边缘情况下不构造 plan）。
        print("错误：plan 为 None")
        return None, validation
    return plan, validation


def _print_validation(validation: Any) -> None:
    """打印 `load-server-plan` 的三段校验明细。

    Args:
        validation: `ValidationResult` 实例，必须含
            `errors` / `warnings` / `passed_checks` 三个 list 字段。
    """
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


# ── 私有 helper：smoke 中「期望抛 UnsupportedOperation」模板 ─────────────────────


def _expect_unsupported(facade: Any, method_name: str, *args: Any) -> bool:
    """调用 facade 方法，期望抛 `UnsupportedOperation`。

    用于 smoke 验证中「该 facade 不应实现某方法」的契约检查。
    `UnsupportedOperation` 是契约异常（见 `starfish.models.plan`），
    表示方法故意抛错而非崩溃；调用方在 smoke 整体聚合中按行记通过。

    Args:
        facade: 已加载 plan 的 facade 实例。
        method_name: 要调用的方法名（如 "write" / "subscribe" /
            "report" / "read"）。
        *args: 透传给该方法的参数。

    Returns:
        True  当方法按契约抛出 `UnsupportedOperation`（期望路径）。
        False 当方法意外完成（违反契约，smoke 视为失败）。

    side effect:
        stdout 始终写一行 `[NOT_IMPLEMENTED] {method_name}: ...`，
        无论结果是期望抛错还是意外完成。
    """
    from starfish.models.plan import UnsupportedOperation

    try:
        getattr(facade, method_name)(*args)
    except UnsupportedOperation as exc:
        print(f"  [NOT_IMPLEMENTED] {method_name}: {exc}")
        return True
    # 方法意外完成：违反 NOT_IMPLEMENTED 契约，记 smoke 失败。
    print(f"  [NOT_IMPLEMENTED] {method_name}: 意外完成（应抛 UnsupportedOperation）")
    return False


# ── 私有 helper：smoke mode dispatch ─────────────────────────────────────────


def _smoke_stub(facade: Any, _plan: Any, _iv: dict[str, Any]) -> bool:
    """stub / unavailable 模式：write/subscribe/report 必须抛
    UnsupportedOperation。

    unavailable 模式下 binary 缺失，但 smoke 仍验证「未实现」契约；
    二进制 reason 在 smoke_server_plan 主体中单独打印。

    Args:
        facade: 已加载 plan 的 facade。
        _plan: 保留以与 dispatch 表签名一致；stub 模式不需要 plan 内容。
        _iv: 保留以与 dispatch 表签名一致；stub 模式不依赖 initial_values。
    """
    ok = True
    ok &= _expect_unsupported(facade, "write", "test_point", 0)
    ok &= _expect_unsupported(facade, "subscribe", ["test_point"])
    ok &= _expect_unsupported(facade, "report")
    return ok


def _smoke_report_lightweight(facade: Any, plan: Any, iv: dict[str, Any]) -> bool:
    """report-lightweight 模式：report 是真实能力；
    read/write/subscribe 抛 UnsupportedOperation。"""
    ok = True
    try:
        if iv:
            facade.update_values(iv)
        report_result = facade.report()
        event_count = report_result.get("event_count", 0)
        print(f"  [report] 已实现（轻量: event_count={event_count}）")
    except Exception as exc:
        # 真实能力失败：smoke 视作该 mode 失败。
        print(f"  [report] 失败: {exc}", file=sys.stderr)
        ok = False
    ok &= _expect_unsupported(facade, "read", ["test_point"])
    ok &= _expect_unsupported(facade, "write", "test_point", 0)
    ok &= _expect_unsupported(facade, "subscribe", ["test_point"])
    print(
        "  [report-lightweight] 不等同完整 IEC61850 Report server，"
        "真实 runner 标记 environment-pending"
    )
    return ok


def _smoke_mqtt_lightweight(facade: Any, plan: Any, iv: dict[str, Any]) -> bool:
    """mqtt-lightweight 模式：subscribe 是真实能力（返回队列）；
    write/report 抛 UnsupportedOperation。"""
    ok = True
    try:
        sub_q = facade.subscribe(["test_point"])
        result = sub_q.get_nowait()
        print(f"  [subscribe] 已实现: 返回 SubscriptionQueue, 立即轮询结果={result}")
    except Exception as exc:
        print(f"  [subscribe] 失败: {exc}", file=sys.stderr)
        ok = False
    ok &= _expect_unsupported(facade, "write", "test_point", 0)
    ok &= _expect_unsupported(facade, "report")
    return ok


def _smoke_rtu_lightweight(facade: Any, plan: Any, iv: dict[str, Any]) -> bool:
    """rtu-lightweight 模式：write 是真实能力（FC06 via PTY）；
    subscribe/report 抛 UnsupportedOperation。"""
    ok = True
    if iv:
        try:
            first_key = next(iter(iv.keys()))
            facade.write(first_key, 0)
            print(f"  [write] 已实现 (FC06 via PTY, point={first_key})")
        except Exception as exc:
            print(f"  [write] 失败: {exc}", file=sys.stderr)
            ok = False
    ok &= _expect_unsupported(facade, "subscribe", ["test_point"])
    ok &= _expect_unsupported(facade, "report")
    print(
        "  [rtu-lightweight] PTY 不等同真实串口现场，"
        "无真实 RS-232/RS-485 电气特性和时序。仅用于本地功能验证。"
    )
    return ok


def _smoke_pending(facade: Any, plan: Any, iv: dict[str, Any]) -> bool:
    """codebase-pending / environment-pending 模式：
    write/subscribe/report 必须抛 UnsupportedOperation。"""
    ok = True
    ok &= _expect_unsupported(facade, "write", "test_point", 0)
    ok &= _expect_unsupported(facade, "subscribe", ["test_point"])
    ok &= _expect_unsupported(facade, "report")
    return ok


def _smoke_real_iec61850_report(facade: Any, plan: Any, iv: dict[str, Any]) -> bool:
    """real 模式 IEC61850_REPORT：report 是真实能力；
    read/write/subscribe 抛 UnsupportedOperation。"""
    ok = True
    try:
        if iv:
            facade.update_values(iv)
        report_result = facade.report()
        event_count = report_result.get("event_count", 0)
        print(f"  [report] 已实现（real: event_count={event_count}）")
    except Exception as exc:
        print(f"  [report] 失败: {exc}", file=sys.stderr)
        ok = False
    ok &= _expect_unsupported(facade, "read", ["test_point"])
    ok &= _expect_unsupported(facade, "write", "test_point", 0)
    ok &= _expect_unsupported(facade, "subscribe", ["test_point"])
    return ok


def _smoke_real_modbus_tcp(facade: Any, plan: Any, iv: dict[str, Any]) -> bool:
    """real 模式 MODBUS_TCP：write 是真实能力（FC06）；
    subscribe/report 抛 UnsupportedOperation。"""
    ok = True
    if iv:
        try:
            first_key = next(iter(iv.keys()))
            facade.write(first_key, 0)
            print(f"  [write] 已实现 (FC06, point={first_key})")
        except Exception as exc:
            print(f"  [write] 失败: {exc}", file=sys.stderr)
            ok = False
    ok &= _expect_unsupported(facade, "subscribe", ["test_point"])
    ok &= _expect_unsupported(facade, "report")
    return ok


def _smoke_real_iec61850_mms(facade: Any, plan: Any, iv: dict[str, Any]) -> bool:
    """real 模式 IEC61850_MMS：
    write/subscribe/report 必须抛 UnsupportedOperation。"""
    ok = True
    ok &= _expect_unsupported(facade, "write", "test_point", 0)
    ok &= _expect_unsupported(facade, "subscribe", ["test_point"])
    ok &= _expect_unsupported(facade, "report")
    return ok


def _smoke_real_pending_3method(facade: Any, plan: Any, iv: dict[str, Any]) -> bool:
    """real 模式下 OPC_UA / IEC104 / IEC_104 派发：
    当前实现中 write/subscribe/report 仍抛 UnsupportedOperation。
    """
    ok = True
    ok &= _expect_unsupported(facade, "write", "test_point", 0)
    ok &= _expect_unsupported(facade, "subscribe", ["test_point"])
    ok &= _expect_unsupported(facade, "report")
    return ok


def _smoke_real_dispatch(facade: Any, plan: Any, iv: dict[str, Any]) -> bool:
    """real 模式按 `facade.protocol` 二级派发。

    HTTP_REST 等当前未列出的 real 协议（未在 dispatch 表中）：
    不执行 mode-specific 步骤，与既有实现一致。
    """
    protocol = getattr(facade, "protocol", "")
    real_dispatch: dict[str, Callable[[Any, Any, dict[str, Any]], bool]] = {
        "IEC61850_REPORT": _smoke_real_iec61850_report,
        "MODBUS_TCP": _smoke_real_modbus_tcp,
        "IEC61850_MMS": _smoke_real_iec61850_mms,
        "OPC_UA": _smoke_real_pending_3method,
        "IEC104": _smoke_real_pending_3method,
        "IEC_104": _smoke_real_pending_3method,
    }
    handler = real_dispatch.get(protocol)
    if handler is None:
        # HTTP_REST 等：mode 维度无契约要验证，视为通过。
        return True
    return handler(facade, plan, iv)


# 非 real 模式的一级 dispatch 表。
# 各 handler 签名：(facade, plan, iv) -> bool，True 表示本段无失败。
_SMOKE_MODE_DISPATCH: dict[str, Callable[[Any, Any, dict[str, Any]], bool]] = {
    "stub": _smoke_stub,
    "unavailable": _smoke_stub,
    "report-lightweight": _smoke_report_lightweight,
    "mqtt-lightweight": _smoke_mqtt_lightweight,
    "rtu-lightweight": _smoke_rtu_lightweight,
    "codebase-pending": _smoke_pending,
    "environment-pending": _smoke_pending,
}


# ── 公共入口 ──────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    """Starfish CLI 统一入口。

    包装 `typer.main.get_group(app)` 的 `standalone_mode=False` 调用，
    把 typer 的「`--help` 显示+退出 0」「MissingParameter / 未知子命令
    → 退出 2」等元行为重新抛回为 `SystemExit`，但把业务错误统一转为
    整数返回（0 成功 / 1 失败）。

    Args:
        argv: 参数列表（不含程序名）。None 时使用 `sys.argv[1:]`。

    Returns:
        整数退出码：0 成功，1 业务错误，2 由 typer 抛 SystemExit 处理。

    Raises:
        SystemExit: 当 argv 含 `--help`/`-h`、缺必填参数、未知子命令
            等元行为触发时抛出，code 由 typer 决定（0 或 2）。
    """
    if argv is None:
        argv = sys.argv[1:]

    # 顶层无命令：约定返回非 0，不抛 SystemExit（与 typer 默认
    # `no_args_is_help=True` 行为不同——本 CLI 要求「无命令」本身
    # 即视为错误）。
    if not argv:
        try:
            typer.main.get_group(app).main(
                args=["--help"],
                prog_name=_PROG_NAME,
                standalone_mode=False,
            )
        except SystemExit:
            # --help 自然 SystemExit(0)，但本路径只关心「无命令」错误。
            pass
        return 1

    # --help 必须抛 SystemExit（与既有契约一致），其它情况才返回 int。
    has_help = "--help" in argv or "-h" in argv

    try:
        rc = typer.main.get_group(app).main(
            args=argv,
            prog_name=_PROG_NAME,
            standalone_mode=False,
        )
    except UsageError as e:
        # MissingParameter / NoSuchOption / 未知子命令 等：抛 SystemExit。
        raise SystemExit(e.exit_code) from None

    if has_help:
        # typer 在 standalone_mode=False 下 --help 返回 0，不抛 SystemExit。
        # 测试契约要求此时以 SystemExit(0) 抛出，向上兼容原 behavior。
        raise SystemExit(0 if rc is None else rc)

    # 业务回调返回 int：透传；返回 None：视为成功。
    return 0 if rc is None else rc


# ── 子命令：load-server-plan ──────────────────────────────────────────────────


@app.command("load-server-plan")
def load_server_plan(
    input_path: Annotated[
        Path,
        typer.Option("--input", help="starfish_server_plan.json 文件路径"),
    ],
) -> int:
    """加载并校验 Seahorse 导出的 starfish_server_plan.json 文件。

    职责：
        从 Seahorse handoff JSON 文件读取 ServerPlan 契约，执行结构
        校验、字段完整性检查和 payload_hash 一致性验证，并输出
        校验报告。

    Args:
        input_path: ServerPlan JSON 文件路径。

    Returns:
        退出码：0 校验通过；1 业务错误（文件不存在 / 加载异常 /
        校验失败 / plan 为 None）。

    side effect:
        读取本地 JSON 文件；向 stdout 打印校验明细（errors /
        warnings / passed_checks），向 stderr 打印业务错误文案。
    """
    plan, validation = _load_plan_or_exit(input_path)
    if plan is None:
        # 校验失败时 validation 可能非 None，继续打印明细后退出。
        if validation is not None and getattr(validation, "errors", None):
            for err in validation.errors:
                print(f"  [ERROR] {err}")
        return 1

    _print_validation(validation)
    print(f"\n加载成功: scenario_id={plan.scenario_id}")
    print(f"  endpoints: {len(plan.endpoints)}")
    print(f"  points: {len(plan.points)}")
    print(f"  capabilities: {plan.capabilities}")
    print(f"  synthetic: {plan.synthetic}")
    return 0


# ── 子命令：smoke-server-plan ─────────────────────────────────────────────────


@app.command("smoke-server-plan")
def smoke_server_plan(
    input_path: Annotated[
        Path,
        typer.Option("--input", help="starfish_server_plan.json 文件路径"),
    ],
) -> int:
    """加载 ServerPlan 并按协议创建 facade 执行最简 smoke 验证。

    职责：
        根据各 endpoint 协议创建对应 facade（real / mqtt-lightweight /
        stub / unavailable / report-lightweight / rtu-lightweight /
        codebase-pending / environment-pending），执行
        health → start → read initial_values → capabilities →
        mode-specific 验证 → stop 序列，任一 endpoint 失败记
        `all_ok = False`。

    不负责：连接生产数据库、依赖外部协议服务。

    Args:
        input_path: ServerPlan JSON 文件路径。

    Returns:
        退出码：0 全部 endpoint 通过；1 任一 endpoint 失败。

    side effect:
        读取本地 JSON 文件；为每个 endpoint 启动并停止 facade；
        向 stdout 打印 smoke 详细输出（含 mode 区分），向 stderr
        打印失败步骤。
    """
    from starfish.registry.runtime_registry import create_facades

    print(f"Smoke 验证 ServerPlan: {input_path}")

    plan, _ = _load_plan_or_exit(input_path)
    if plan is None:
        return 1

    print(f"  scenario_id: {plan.scenario_id}")
    print(f"  endpoints: {len(plan.endpoints)}")
    print(f"  points: {len(plan.points)}")
    print()

    registry = create_facades(plan)

    # Facade 工厂 dispatch 结果输出：保留 endpoint_count/point_count/
    # capabilities 等字段名以维持既有 stdout 文案契约。
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

    all_ok = True
    for entry in registry.entries:
        facade = entry.facade
        # unavailable / facade 为 None 的 endpoint：仅打印 skip 跳过
        # 后续 health/start/... 序列，与既有契约一致。
        if facade is None or not entry.available:
            print(f"\n[skip] endpoint={entry.endpoint.endpoint_id}: unavailable")
            continue

        print(f"\n--- smoke {entry.endpoint.endpoint_id} (mode={entry.mode}) ---")

        # step 1: health（启动前健康探针，输出 status/plan_loaded 等）。
        h = facade.health()
        print(
            f"[health] status={h.get('status', '?')}, "
            f"plan_loaded={h.get('plan_loaded', False)}, "
            f"points={h.get('point_count', 0)}, "
            f"mode={h.get('mode', entry.mode)}"
        )

        # step 2: start。start 失败时跳过该 endpoint 后续步骤（与既有
        # 行为一致），避免在未启动的 facade 上调 read/capabilities。
        try:
            facade.start()
            h2 = facade.health()
            print(
                f"[start] status={h2.get('status', '?')}, "
                f"running={h2.get('running', False)}"
            )
        except Exception as exc:
            print(f"[start] 失败: {exc}", file=sys.stderr)
            all_ok = False
            continue

        # step 3: read initial_values。空 initial_values 仅打印「无初始值」。
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

        # step 4: capabilities。
        try:
            caps = facade.capabilities()
            print(f"[capabilities] {caps}")
        except Exception as exc:
            print(f"[capabilities] 失败: {exc}", file=sys.stderr)
            all_ok = False

        # step 5: mode-specific dispatch。
        # 入口表格 + real 协议二级派发表使各 mode 的实现职责清晰可读。
        if entry.mode == "real":
            ok = _smoke_real_dispatch(facade, plan, iv)
        else:
            handler = _SMOKE_MODE_DISPATCH.get(entry.mode)
            ok = handler(facade, plan, iv) if handler is not None else True
        # unavailable 在 stub 模板之外多打印一行 binary_reason，便于排错。
        if entry.mode == "unavailable":
            print(
                f"  [unavailable] binary_reason: "
                f"{getattr(facade, 'binary_reason', 'unknown')}"
            )
        if not ok:
            all_ok = False

        # step 6: stop。start 已成功但 stop 失败时只标 all_ok，
        # 不中断后续 endpoint（与既有契约一致）。
        try:
            facade.stop()
            h3 = facade.health()
            print(f"[stop] status={h3.get('status', '?')}")
        except Exception as exc:
            print(f"[stop] 失败: {exc}", file=sys.stderr)
            all_ok = False

    print(f"\nSmoke 完成: {'通过' if all_ok else '部分未通过'}")
    return 0 if all_ok else 1


# ── 子命令：probe-server-plan ─────────────────────────────────────────────────


@app.command("probe-server-plan")
def probe_server_plan(
    input_path: Annotated[
        Path,
        typer.Option("--input", help="starfish_server_plan.json 文件路径"),
    ],
) -> int:
    """对各 endpoint facade 执行最小可用性探测。

    职责：加载 ServerPlan 并逐 endpoint 创建 facade，执行最小可用性
    探测（start/health/load_points/read），输出每个 endpoint 的
    PASS/FAIL/NOT_RUN + reason。

    Args:
        input_path: ServerPlan JSON 文件路径。

    Returns:
        退出码：0 全部 PASS；1 任一 endpoint 非 PASS。

    side effect:
        读取本地 JSON 文件；为每个 endpoint 创建并清理 facade；向
        stdout 打印探测结果，向 stderr 打印 `start/stop` 失败兜底。
    """
    from starfish.registry.runtime_registry import create_facade_for_endpoint
    from starfish.tools.probe import probe_facade

    print(f"Probe 探测 ServerPlan: {input_path}")

    plan, _ = _load_plan_or_exit(input_path)
    if plan is None:
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
            # stop 失败不影响 probe 自身结论（probe 已在返回前聚合）；
            # 也不应掩盖原始异常——仅在 stop 抛错时静默吞掉以避免
            # 测试期资源残留干扰。
            try:
                entry.facade.stop()
            except Exception:
                pass

    print(f"\nProbe 完成: {'全部通过' if all_pass else '存在失败'}")
    return 0 if all_pass else 1


# ── 子命令：profile-server-plan ───────────────────────────────────────────────


@app.command("profile-server-plan")
def profile_server_plan(
    input_path: Annotated[
        Path,
        typer.Option("--input", help="starfish_server_plan.json 文件路径"),
    ],
    iterations: Annotated[
        int,
        typer.Option("--iterations", help="采样次数"),
    ] = 100,
) -> int:
    """对 facade read 执行 N 次采样统计耗时。

    职责：加载 ServerPlan 并逐 endpoint 创建 facade，对每个 facade 的
    `read()` 方法执行 N 次采样，统计 count/min/max/avg 耗时（毫秒）。

    Args:
        input_path: ServerPlan JSON 文件路径。
        iterations: 采样次数（默认 100，最小归一化为 1）。

    Returns:
        退出码：0 全部 PASS；1 任一 endpoint 非 PASS。

    side effect:
        读取本地 JSON 文件；为每个 endpoint 启动并停止 facade；向
        stdout 打印采样统计。
    """
    from starfish.registry.runtime_registry import create_facade_for_endpoint
    from starfish.tools.profile import profile_facade

    actual_iterations = max(1, iterations)
    print(f"Profile 采样 ServerPlan: {input_path} (iterations={actual_iterations})")

    plan, _ = _load_plan_or_exit(input_path)
    if plan is None:
        return 1

    all_pass = True
    for ep in plan.endpoints:
        print(f"\n--- profile endpoint={ep.endpoint_id} protocol={ep.protocol} ---")
        entry = create_facade_for_endpoint(ep, plan)
        try:
            entry.facade.start()
            profile_result = profile_facade(
                entry.facade,
                iterations=actual_iterations,
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
                print(
                    f"  count: {stats.get('count', '?')}, "
                    f"min: {stats.get('min', '?')}ms, "
                    f"max: {stats.get('max', '?')}ms, "
                    f"avg: {stats.get('avg', '?')}ms"
                )
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


# ── 子命令：capacity-server-plan ──────────────────────────────────────────────


@app.command("capacity-server-plan")
def capacity_server_plan(
    input_path: Annotated[
        Path,
        typer.Option("--input", help="starfish_server_plan.json 文件路径"),
    ],
    point_count: Annotated[
        int,
        typer.Option("--point-count", help="read 调用次数"),
    ] = 10,
) -> int:
    """对 endpoint 做轻量容量扫描。

    职责：加载 ServerPlan 并逐 endpoint 创建 facade，对每个 facade
    执行轻量容量扫描（endpoint_count / point_count / read_count），
    输出 PASS/FAIL/NOT_RUN + max_tested_points。

    Args:
        input_path: ServerPlan JSON 文件路径。
        point_count: read 调用次数（默认 10，最小归一化为 1）。

    Returns:
        退出码：0 全部非 FAIL；1 任一 endpoint FAIL（NOT_RUN 不计入）。

    side effect:
        读取本地 JSON 文件；为每个 endpoint 启动并停止 facade；向
        stdout 打印容量统计。
    """
    from starfish.registry.runtime_registry import create_facade_for_endpoint
    from starfish.tools.capacity import capacity_scan

    read_count = max(1, point_count)
    print(f"Capacity 扫描 ServerPlan: {input_path} (read_count={read_count})")

    plan, _ = _load_plan_or_exit(input_path)
    if plan is None:
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


if __name__ == "__main__":
    # `python -m starfish` 直接调用 typer：保留原有「命令名打错时
    # 由 typer 抛 SystemExit」的 shell 行为。
    app()
