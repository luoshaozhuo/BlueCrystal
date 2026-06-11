"""starfish CLI 入口 —— 通过高层 API 执行 ServerPlan 校验与 simulator 运行。

使用方式：

```text
python -m starfish validate-plan --input <starfish_server_plan.json>
python -m starfish describe --input <starfish_server_plan.json>
python -m starfish health --input <starfish_server_plan.json> --start
python -m starfish read --input <starfish_server_plan.json>
python -m starfish run --input <starfish_server_plan.json> --duration 30
```

模块职责：
- 暴露 5 个子命令：validate-plan / describe / health / read / run。
- 统一经 `starfish.api` 进入 application usecase，而不是直接耦合 loader/registry。
- 提供独立可单元测试的 `main(argv) -> int` 入口，封装 typer 的
  `SystemExit` 行为，错误路径以返回值表达退出码。

定位说明：
- 这是面向单份 `ServerPlan` 的 simulator/runtime CLI。
- 测试逻辑应放在 `tests/` 中，由 pytest 驱动。
- 本 CLI 不再承担 smoke/probe/profile/capacity 这类测试入口职责。

不负责：
- 替代 pytest。
- 生产数据写入、落库或生产链路编排。
- 协议 frame 编解码实现（由 `starfish.protocols` 负责）。
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Annotated, Any

import typer
import typer.main
from typer._click.exceptions import UsageError

from starfish.api import StarfishRuntime, create_default_runtime_api


_PROG_NAME = "starfish"

app = typer.Typer(
    name=_PROG_NAME,
    help="Starfish 多协议 simulator 运行 CLI",
    rich_markup_mode="rich",
)


def _runtime_api() -> Any:
    """返回默认运行时 API。"""
    return create_default_runtime_api()


def _load_plan_or_exit(input_path: Path) -> tuple[Any | None, Any]:
    """加载并校验 ServerPlan JSON。"""
    try:
        result = _runtime_api().load_plan(input_path)
    except FileNotFoundError:
        print(f"错误：文件不存在: {input_path}", file=sys.stderr)
        return None, None
    except Exception as exc:
        print(f"错误：加载失败: {exc}", file=sys.stderr)
        return None, None

    validation = result.validation
    if not validation.is_valid:
        print(f"错误：校验失败 ({len(validation.errors)} 个错误)")
        return None, validation

    plan = result.plan
    if plan is None:
        print("错误：plan 为 None")
        return None, validation
    return plan, validation


def _print_validation(validation: Any) -> None:
    """打印 validate-plan 校验明细。"""
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
        for passed in validation.passed_checks:
            print(f"  [PASS] {passed}")


def _open_runtime_or_exit(input_path: Path) -> StarfishRuntime | None:
    """加载 plan 并创建统一运行时对象。"""
    try:
        return _runtime_api().open_runtime(input_path)
    except FileNotFoundError:
        print(f"错误：文件不存在: {input_path}", file=sys.stderr)
        return None
    except ValueError as exc:
        plan, validation = _load_plan_or_exit(input_path)
        if validation is not None and getattr(validation, "errors", None):
            for err in validation.errors:
                print(f"  [ERROR] {err}")
        elif plan is not None:
            print(f"错误：{exc}", file=sys.stderr)
        return None
    except Exception as exc:
        print(f"错误：加载失败: {exc}", file=sys.stderr)
        return None


def _print_plan_summary(plan: Any) -> None:
    """打印 plan 摘要。"""
    print(f"scenario_id: {plan.scenario_id}")
    print(f"server_name: {plan.server_name}")
    print(f"endpoints:   {len(plan.endpoints)}")
    print(f"points:      {len(plan.points)}")
    print(f"synthetic:   {plan.synthetic}")
    print(f"capabilities:{plan.capabilities}")


def _print_registry_summary(plan: Any, registry: Any) -> None:
    """打印 facade 装配结果摘要。"""
    print("Facade 装配结果:")
    for entry in registry.entries:
        endpoint = entry.endpoint
        bind_host = endpoint.bind_host or endpoint.host
        bind_port = endpoint.bind_port or endpoint.port
        print(f"  endpoint:   {endpoint.endpoint_id}")
        print(f"    protocol: {endpoint.protocol}")
        print(f"    bind:     {bind_host}:{bind_port}")
        print(f"    mode:     {entry.mode}")
        print(f"    available:{entry.available}")
        if entry.reason:
            print(f"    reason:   {entry.reason}")
        if entry.driver is not None:
            health = entry.driver.health()
            print(f"    points:   {health.get('point_count', len(plan.points))}")
            print(f"    caps:     {health.get('capabilities', plan.capabilities)}")


def main(argv: list[str]) -> int:
    """Starfish CLI 统一入口。"""
    try:
        rc = typer.main.get_group(app).main(
            args=argv,
            prog_name=_PROG_NAME,
            standalone_mode=False,
        )
    except UsageError as exc:
        raise SystemExit(exc.exit_code) from None

    return 0 if rc is None else rc


@app.command("validate-plan")
def validate_plan(
    input_path: Annotated[
        Path,
        typer.Option("--input", help="starfish_server_plan.json 文件路径"),
    ],
) -> int:
    """加载并校验 Seahorse 导出的 starfish_server_plan.json 文件。"""
    plan, validation = _load_plan_or_exit(input_path)
    if plan is None:
        if validation is not None and getattr(validation, "errors", None):
            for err in validation.errors:
                print(f"  [ERROR] {err}")
        return 1

    _print_validation(validation)
    print()
    _print_plan_summary(plan)
    return 0


@app.command("describe")
def describe_plan(
    input_path: Annotated[
        Path,
        typer.Option("--input", help="starfish_server_plan.json 文件路径"),
    ],
) -> int:
    """展示 plan 摘要和 facade 装配结果。"""
    runtime = _open_runtime_or_exit(input_path)
    if runtime is None:
        return 1

    _print_plan_summary(runtime.plan)
    print()
    _print_registry_summary(runtime.plan, runtime.registry)
    return 0


@app.command("health")
def health_command(
    input_path: Annotated[
        Path,
        typer.Option("--input", help="starfish_server_plan.json 文件路径"),
    ],
    start_first: Annotated[
        bool,
        typer.Option("--start/--no-start", help="先启动 facade 再查询 health"),
    ] = False,
) -> int:
    """查看各 endpoint 当前 health。"""
    runtime = _open_runtime_or_exit(input_path)
    if runtime is None:
        return 1

    all_ok = True
    if start_first:
        try:
            runtime.start()
        except Exception as exc:
            print(f"[start] 失败: {exc}", file=sys.stderr)
            all_ok = False

    for entry in runtime.registry.entries:
        print(f"\n--- health endpoint={entry.endpoint.endpoint_id} ---")
        print(f"  protocol:  {entry.endpoint.protocol}")
        print(f"  mode:      {entry.mode}")
        print(f"  available: {entry.available}")
        if not entry.available or entry.driver is None:
            print("  status:    unavailable")
            print(f"  reason:    {entry.reason}")
            continue
        try:
            health = runtime.health(entry.endpoint.endpoint_id)
            for key, value in health.items():
                print(f"  {key}: {value}")
        except Exception as exc:
            print(f"  错误: {exc}", file=sys.stderr)
            all_ok = False

    if start_first:
        runtime.stop()
    return 0 if all_ok else 1


@app.command("read")
def read_command(
    input_path: Annotated[
        Path,
        typer.Option("--input", help="starfish_server_plan.json 文件路径"),
    ],
    point_ids: Annotated[
        list[str],
        typer.Option("--point", help="只读取指定 point_id，可重复传入"),
    ] = [],
) -> int:
    """启动 simulator，读取当前点位值并停止。"""
    runtime = _open_runtime_or_exit(input_path)
    if runtime is None:
        return 1

    try:
        runtime.start()
    except Exception as exc:
        print(f"错误：启动 simulator 失败: {exc}", file=sys.stderr)
        return 1

    available_entries = [
        entry for entry in runtime.registry.entries
        if entry.available and entry.driver is not None
    ]
    if not available_entries:
        print("错误：没有可启动的 simulator endpoint", file=sys.stderr)
        return 1

    all_ok = True
    selected_points = point_ids or None
    try:
        values_by_endpoint = runtime.read(selected_points)
    except Exception as exc:
        print(f"错误：读取失败: {exc}", file=sys.stderr)
        runtime.stop()
        return 1

    for entry in available_entries:
        print(f"\n--- read endpoint={entry.endpoint.endpoint_id} ---")
        print(f"  protocol: {entry.endpoint.protocol}")
        print(f"  mode:     {entry.mode}")
        try:
            values = values_by_endpoint.get(entry.endpoint.endpoint_id, {})
            print(f"  point_count: {len(values)}")
            for point_id, value in values.items():
                print(f"  {point_id}={value}")
        except Exception as exc:
            print(f"  错误: {exc}", file=sys.stderr)
            all_ok = False

    runtime.stop()
    return 0 if all_ok else 1


@app.command("run")
def run_command(
    input_path: Annotated[
        Path,
        typer.Option("--input", help="starfish_server_plan.json 文件路径"),
    ],
    duration: Annotated[
        float | None,
        typer.Option("--duration", help="运行秒数；不传则持续运行直到 Ctrl+C"),
    ] = None,
) -> int:
    """启动全部可用 simulator facade 并保持运行。"""
    runtime = _open_runtime_or_exit(input_path)
    if runtime is None:
        return 1

    _print_plan_summary(runtime.plan)
    print()
    _print_registry_summary(runtime.plan, runtime.registry)

    try:
        runtime.start()
    except Exception as exc:
        print(f"错误：启动 simulator 失败: {exc}", file=sys.stderr)
        return 1

    started_count = len(
        [
            entry for entry in runtime.registry.entries
            if entry.available and entry.driver is not None
        ]
    )
    print(f"\n已启动 {started_count} 个 simulator endpoint。")
    if duration is None:
        print("按 Ctrl+C 停止。")
    else:
        print(f"将运行 {duration:.2f} 秒后自动停止。")

    try:
        if duration is None:
            while True:
                time.sleep(0.5)
        else:
            deadline = time.monotonic() + max(0.0, duration)
            while time.monotonic() < deadline:
                time.sleep(min(0.5, deadline - time.monotonic()))
    except KeyboardInterrupt:
        print("\n收到中断信号，正在停止 simulator...")
    finally:
        runtime.stop()

    print("Simulator 已停止。")
    return 0


if __name__ == "__main__":
    app()
