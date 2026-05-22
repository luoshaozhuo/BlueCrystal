"""Polling capacity CLI 端到端探查测试。

本测试通过 pytest 调度 simulator-backed fixture，并通过正式 CLI
``python -m tools.source_lab.field_capacity --access-mode polling`` 执行容量扫描。
它同时验证 field_capacity CLI 参数解析、capacity 服务链路、open62541 polling
runner，以及当前开发环境在多 server / 多频率组合下的承载能力。

完整执行示例（pytest 调度）：

    env \
      SOURCE_SIM_PORT_START=45000 \
      SOURCE_SIM_PORT_END=65000 \
      SOURCE_SIM_FLEET_START_CONCURRENCY=4 \
      SOURCE_SIM_FLEET_START_STAGGER_MS=15 \
      SOURCE_SIM_FLEET_STARTUP_TIMEOUT_S=30 \
      SOURCE_SIM_POLL_PROCESS_COUNT_START=1 \
      SOURCE_SIM_POLL_PROCESS_COUNT_STEP=1 \
      SOURCE_SIM_POLL_PROCESS_COUNT_MAX=1 \
      SOURCE_SIM_POLL_SERVER_COUNT_START=10 \
      SOURCE_SIM_POLL_SERVER_COUNT_STEP=20 \
      SOURCE_SIM_POLL_SERVER_COUNT_MAX=30 \
      SOURCE_SIM_POLL_HZ_START=10 \
      SOURCE_SIM_POLL_HZ_STEP=20 \
      SOURCE_SIM_POLL_HZ_MAX=30 \
      SOURCE_SIM_POLL_DURATION_S=6 \
      SOURCE_SIM_POLL_WARMUP_S=1 \
      SOURCE_SIM_POLL_TIMEOUT_S=5 \
      SOURCE_SIM_POLL_SOURCE_UPDATE_ENABLED=true \
      SOURCE_SIM_POLL_RUN_ID=polling_capacity_smoke \
      SOURCE_SIM_POLL_PERIOD_MAX_TOLERANCE_RATIO=0.2 \
      SOURCE_SIM_POLL_PERIOD_MEAN_ERROR_RATIO=0.05 \
      python -m pytest tools/source_lab/tests/test_source_simulation_multi_server_polling_capacity.py -q -s

本测试内部固定调用的 CLI 参数如下。
除 ``access-mode``、``servers``、``profile-items``、``protocol`` 外，其余参数均由
上面的 ``SOURCE_SIM_POLL_*`` 环境变量驱动：

等价 CLI 示例：

    python -m tools.source_lab.field_capacity \
      --access-mode polling \
      --servers tools/source_lab/tests/fixtures/simulator/field_servers.tsv \
      --profile-items tools/source_lab/tests/fixtures/simulator/signal_profile_items.tsv \
      --protocol opcua \
      --process-count-start 1 \
      --process-count-step 1 \
      --process-count-max 1 \
      --server-count-start 10 \
      --server-count-step 20 \
      --server-count-max 30 \
      --hz-start 10 \
      --hz-step 20 \
      --hz-max 30 \
      --duration 6 \
      --warmup 1 \
      --timeout 5 \
      --source-update-enabled true \
      --run-id polling_capacity_smoke \
      --output-dir tools/source_lab/tests/tmp/polling_capacity
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
    """Resolve the dedicated polling-capacity output directory.

    Returns:
        Absolute output directory for this smoke test.
    """

    return _REPO_ROOT / "tools" / "source_lab" / "tests" / "tmp" / "polling_capacity"


def _build_env() -> dict[str, str]:
    """Build the child-process environment for the polling CLI run.

    Returns:
        Environment variables used by the CLI subprocess.
    """

    env = os.environ.copy()
    env.setdefault("SOURCE_SIM_PORT_START", "45000")
    env.setdefault("SOURCE_SIM_PORT_END", "65000")
    env.setdefault("SOURCE_SIM_FLEET_START_CONCURRENCY", "4")
    env.setdefault("SOURCE_SIM_FLEET_START_STAGGER_MS", "15")
    env.setdefault("SOURCE_SIM_FLEET_STARTUP_TIMEOUT_S", "30")
    env.setdefault("SOURCE_SIM_POLL_PERIOD_MAX_TOLERANCE_RATIO", "0.2")
    env.setdefault("SOURCE_SIM_POLL_PERIOD_MEAN_ERROR_RATIO", "0.05")
    return env


def _command_args(output_dir: Path) -> list[str]:
    """Build polling-capacity CLI args from pytest environment variables.

    Args:
        output_dir: Output directory passed to the child CLI.

    Returns:
        CLI argument vector excluding ``sys.executable -m`` prefix.
    """

    return [
        "tools.source_lab.field_capacity",
        "--access-mode",
        "polling",
        "--servers",
        str(_fixture_path("field_servers.tsv")),
        "--profile-items",
        str(_fixture_path("signal_profile_items.tsv")),
        "--protocol",
        "opcua",
        "--process-count-start",
        _env_text("SOURCE_SIM_POLL_PROCESS_COUNT_START", "1"),
        "--process-count-step",
        _env_text("SOURCE_SIM_POLL_PROCESS_COUNT_STEP", "1"),
        "--process-count-max",
        _env_text("SOURCE_SIM_POLL_PROCESS_COUNT_MAX", "1"),
        "--server-count-start",
        _env_text("SOURCE_SIM_POLL_SERVER_COUNT_START", "10"),
        "--server-count-step",
        _env_text("SOURCE_SIM_POLL_SERVER_COUNT_STEP", "20"),
        "--server-count-max",
        _env_text("SOURCE_SIM_POLL_SERVER_COUNT_MAX", "30"),
        "--hz-start",
        _env_text("SOURCE_SIM_POLL_HZ_START", "10"),
        "--hz-step",
        _env_text("SOURCE_SIM_POLL_HZ_STEP", "20"),
        "--hz-max",
        _env_text("SOURCE_SIM_POLL_HZ_MAX", "30"),
        "--duration",
        _env_text("SOURCE_SIM_POLL_DURATION_S", "6"),
        "--warmup",
        _env_text("SOURCE_SIM_POLL_WARMUP_S", "1"),
        "--timeout",
        _env_text("SOURCE_SIM_POLL_TIMEOUT_S", "5"),
        "--source-update-enabled",
        _env_text("SOURCE_SIM_POLL_SOURCE_UPDATE_ENABLED", "true"),
        "--run-id",
        _env_text("SOURCE_SIM_POLL_RUN_ID", "polling_capacity_smoke"),
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
        timeout=1800,
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
def test_source_simulation_multi_server_polling_capacity() -> None:
    """Run the polling capacity smoke path through the formal CLI."""

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

    # 设置端口范围与阈值环境，确保 simulator provider 在当前开发环境可运行。
    completed = _run_cli(command, env=_build_env())

    # 回显 stdout/stderr，保证 ``pytest -s`` 可直接观察容量表。
    _print_completed_process(completed)

    # 断言 CLI 正常退出并保留当前容量表头风格。
    assert completed.returncode == 0, completed.stderr
    assert "proc" in completed.stdout
    assert "srv" in completed.stdout
    assert "hz" in completed.stdout
    assert "period_ms" in completed.stdout
    assert "value_ratio" in completed.stdout
    assert "status" in completed.stdout
    assert "reason" in completed.stdout

    # 断言 capacity 报告产物已经落盘。
    assert any(output_dir.glob("field_capacity_*.csv"))
    assert any(output_dir.glob("field_capacity_*.jsonl"))
