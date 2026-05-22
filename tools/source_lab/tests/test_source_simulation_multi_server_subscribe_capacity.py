"""Subscribe capacity CLI 端到端探查测试。

本测试通过正式 CLI
``python -m tools.source_lab.field_capacity --access-mode subscribe`` 执行订阅容量扫描。
它同时验证 CLI 参数、source_update_hz / sample_hz 矩阵、warmup 生效、
open62541 subscription runner，以及当前开发环境订阅模式承载能力。

完整执行示例（pytest 调度）：

    env \
      SOURCE_SIM_PORT_START=45000 \
      SOURCE_SIM_PORT_END=65000 \
      SOURCE_SIM_FLEET_START_CONCURRENCY=4 \
      SOURCE_SIM_FLEET_START_STAGGER_MS=15 \
      SOURCE_SIM_FLEET_STARTUP_TIMEOUT_S=30 \
      SOURCE_SIM_SUB_PROCESS_COUNT_START=1 \
      SOURCE_SIM_SUB_PROCESS_COUNT_STEP=1 \
      SOURCE_SIM_SUB_PROCESS_COUNT_MAX=1 \
      SOURCE_SIM_SUB_SERVER_COUNT_START=10 \
      SOURCE_SIM_SUB_SERVER_COUNT_STEP=10 \
      SOURCE_SIM_SUB_SERVER_COUNT_MAX=20 \
      SOURCE_SIM_SUB_SAMPLE_HZ_START=20 \
      SOURCE_SIM_SUB_SAMPLE_HZ_STEP=20 \
      SOURCE_SIM_SUB_SAMPLE_HZ_MAX=40 \
      SOURCE_SIM_SUB_SOURCE_UPDATE_HZ_START=10 \
      SOURCE_SIM_SUB_SOURCE_UPDATE_HZ_STEP=20 \
      SOURCE_SIM_SUB_SOURCE_UPDATE_HZ_MAX=30 \
      SOURCE_SIM_SUB_DURATION_S=6 \
      SOURCE_SIM_SUB_WARMUP_S=1 \
      SOURCE_SIM_SUB_TIMEOUT_S=5 \
      SOURCE_SIM_SUB_SOURCE_UPDATE_ENABLED=true \
      SOURCE_SIM_SUB_QUEUE_SIZE=1 \
      SOURCE_SIM_SUB_STARTUP_STAGGER_MS=0 \
      SOURCE_SIM_SUB_MONITORED_ITEM_BATCH_SIZE=100 \
      SOURCE_SIM_SUB_MONITORED_ITEM_BATCH_GAP_MS=0 \
      SOURCE_SIM_SUB_RUN_ID=subscribe_capacity_smoke \
      SOURCE_SIM_SUB_DATA_PERIOD_MAX_TOLERANCE_RATIO=0.2 \
      python -m pytest tools/source_lab/tests/test_source_simulation_multi_server_subscribe_capacity.py -q -s

本测试内部固定调用的 CLI 参数如下。
除 ``access-mode``、``servers``、``profile-items``、``protocol`` 外，其余参数均由
上面的 ``SOURCE_SIM_SUB_*`` 环境变量驱动：

等价 CLI 示例：

    python -m tools.source_lab.field_capacity \
      --access-mode subscribe \
      --servers tools/source_lab/tests/fixtures/simulator/field_servers.tsv \
      --profile-items tools/source_lab/tests/fixtures/simulator/signal_profile_items.tsv \
      --protocol opcua \
      --process-count-start 1 \
      --process-count-step 1 \
      --process-count-max 1 \
      --server-count-start 10 \
      --server-count-step 10 \
      --server-count-max 20 \
      --sample-hz-start 20 \
      --sample-hz-step 20 \
      --sample-hz-max 40 \
      --source-update-hz-start 10 \
      --source-update-hz-step 20 \
      --source-update-hz-max 30 \
      --duration 6 \
      --warmup 1 \
      --timeout 5 \
      --source-update-enabled true \
      --queue-size 1 \
      --startup-stagger-ms 0 \
      --monitored-item-batch-size 100 \
      --monitored-item-batch-gap-ms 0 \
      --run-id subscribe_capacity_smoke \
      --output-dir tools/source_lab/tests/tmp/subscribe_capacity
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "simulator"


def _env_text(name: str, default: str) -> str:
    """Read one CLI-driving environment variable as text.

    Args:
        name: Environment variable name.
        default: Fallback string when the variable is unset.

    Returns:
        Explicit environment value or the provided default.
    """

    return os.environ.get(name, default).strip() or default


def _fixture_path(name: str) -> Path:
    """Resolve one simulator fixture path.

    Args:
        name: Fixture filename under the simulator fixture directory.

    Returns:
        Absolute fixture path.
    """

    return _FIXTURE_DIR / name


def _output_dir() -> Path:
    """Resolve the dedicated subscribe-capacity output directory.

    Returns:
        Absolute output directory for this smoke test.
    """

    return _REPO_ROOT / "tools" / "source_lab" / "tests" / "tmp" / "subscribe_capacity"


def _build_env() -> dict[str, str]:
    """Build the child-process environment for the subscribe CLI run.

    Returns:
        Environment variables used by the CLI subprocess.
    """

    env = os.environ.copy()
    env.setdefault("SOURCE_SIM_PORT_START", "45000")
    env.setdefault("SOURCE_SIM_PORT_END", "65000")
    env.setdefault("SOURCE_SIM_FLEET_START_CONCURRENCY", "4")
    env.setdefault("SOURCE_SIM_FLEET_START_STAGGER_MS", "15")
    env.setdefault("SOURCE_SIM_FLEET_STARTUP_TIMEOUT_S", "30")
    env.setdefault("SOURCE_SIM_SUB_DATA_PERIOD_MAX_TOLERANCE_RATIO", "0.2")
    return env


def _command_args(output_dir: Path) -> list[str]:
    """Build subscribe-capacity CLI args from pytest environment variables.

    Args:
        output_dir: Output directory passed to the child CLI.

    Returns:
        CLI argument vector excluding ``sys.executable -m`` prefix.
    """

    return [
        "tools.source_lab.field_capacity",
        "--access-mode",
        "subscribe",
        "--servers",
        str(_fixture_path("field_servers.tsv")),
        "--profile-items",
        str(_fixture_path("signal_profile_items.tsv")),
        "--protocol",
        "opcua",
        "--process-count-start",
        _env_text("SOURCE_SIM_SUB_PROCESS_COUNT_START", "1"),
        "--process-count-step",
        _env_text("SOURCE_SIM_SUB_PROCESS_COUNT_STEP", "1"),
        "--process-count-max",
        _env_text("SOURCE_SIM_SUB_PROCESS_COUNT_MAX", "1"),
        "--server-count-start",
        _env_text("SOURCE_SIM_SUB_SERVER_COUNT_START", "10"),
        "--server-count-step",
        _env_text("SOURCE_SIM_SUB_SERVER_COUNT_STEP", "10"),
        "--server-count-max",
        _env_text("SOURCE_SIM_SUB_SERVER_COUNT_MAX", "20"),
        "--sample-hz-start",
        _env_text("SOURCE_SIM_SUB_SAMPLE_HZ_START", "20"),
        "--sample-hz-step",
        _env_text("SOURCE_SIM_SUB_SAMPLE_HZ_STEP", "20"),
        "--sample-hz-max",
        _env_text("SOURCE_SIM_SUB_SAMPLE_HZ_MAX", "40"),
        "--source-update-hz-start",
        _env_text("SOURCE_SIM_SUB_SOURCE_UPDATE_HZ_START", "10"),
        "--source-update-hz-step",
        _env_text("SOURCE_SIM_SUB_SOURCE_UPDATE_HZ_STEP", "20"),
        "--source-update-hz-max",
        _env_text("SOURCE_SIM_SUB_SOURCE_UPDATE_HZ_MAX", "30"),
        "--duration",
        _env_text("SOURCE_SIM_SUB_DURATION_S", "6"),
        "--warmup",
        _env_text("SOURCE_SIM_SUB_WARMUP_S", "1"),
        "--timeout",
        _env_text("SOURCE_SIM_SUB_TIMEOUT_S", "5"),
        "--source-update-enabled",
        _env_text("SOURCE_SIM_SUB_SOURCE_UPDATE_ENABLED", "true"),
        "--queue-size",
        _env_text("SOURCE_SIM_SUB_QUEUE_SIZE", "1"),
        "--startup-stagger-ms",
        _env_text("SOURCE_SIM_SUB_STARTUP_STAGGER_MS", "0"),
        "--monitored-item-batch-size",
        _env_text("SOURCE_SIM_SUB_MONITORED_ITEM_BATCH_SIZE", "100"),
        "--monitored-item-batch-gap-ms",
        _env_text("SOURCE_SIM_SUB_MONITORED_ITEM_BATCH_GAP_MS", "0"),
        "--run-id",
        _env_text("SOURCE_SIM_SUB_RUN_ID", "subscribe_capacity_smoke"),
        "--output-dir",
        str(output_dir),
    ]


def _run_cli(command: list[str], *, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Run one source_lab CLI command and return the completed process.

    Args:
        command: Command vector passed to ``subprocess.run``.
        env: Environment variables used by the child process.

    Returns:
        Completed process with captured text stdout and stderr.
    """

    return subprocess.run(
        command,
        cwd=_REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=2400,
        check=False,
    )


def _print_completed_process(completed: subprocess.CompletedProcess[str]) -> None:
    """Replay captured CLI stdout/stderr for ``pytest -s`` visibility.

    Args:
        completed: Completed subprocess result to echo back to the test console.
    """

    print(completed.stdout, end="")
    print(completed.stderr, end="", file=sys.stderr)


@pytest.mark.load
def test_source_simulation_multi_server_subscribe_capacity() -> None:
    """Run the subscribe capacity smoke path through the formal CLI."""

    # 定位 simulator fixture，并准备独立输出目录。
    output_dir = _output_dir()
    shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 组装正式 CLI 参数；除固定输入文件外，其余关键参数全部允许由 pytest 环境覆盖。
    command = [
        sys.executable,
        "-m",
        *_command_args(output_dir),
    ]

    # 设置端口范围与订阅阈值环境，确保正式订阅容量链路可运行。
    completed = _run_cli(command, env=_build_env())

    # 回显 stdout/stderr，保证 ``pytest -s`` 能直接看到订阅容量表。
    _print_completed_process(completed)

    # 断言 CLI 正常退出，并保留当前 subscribe capacity 表头风格。
    assert completed.returncode == 0, completed.stderr
    assert "proc" in completed.stdout
    assert "srv" in completed.stdout
    assert "sub_hz" in completed.stdout
    assert "src_hz" in completed.stdout
    assert "sub_ms" in completed.stdout
    assert "src_ms" in completed.stdout
    assert "value_ratio" in completed.stdout
    assert "status" in completed.stdout
    assert "reason" in completed.stdout

    # 断言容量报告产物已经落盘。
    assert any(output_dir.glob("field_capacity_*.csv"))
    assert any(output_dir.glob("field_capacity_*.jsonl"))
