"""Subscribe profile CLI 端到端诊断测试。

本测试通过 pytest 调度 simulator-backed fixture，并通过正式 CLI
``python -m tools.source_lab.field_profile --access-mode subscribe`` 执行单配置诊断。
它同时验证 profile CLI 参数解析、订阅 runner 诊断输出、runner trace，以及当前开发
环境在目标 subscribe 配置下的表现。

完整执行示例（pytest 调度）：

    env \
      SOURCE_SIM_PORT_START=45000 \
      SOURCE_SIM_PORT_END=65000 \
      SOURCE_SIM_SUB_PROCESS_COUNT=1 \
      SOURCE_SIM_FLEET_START_CONCURRENCY=4 \
      SOURCE_SIM_FLEET_START_STAGGER_MS=15 \
      SOURCE_SIM_FLEET_STARTUP_TIMEOUT_S=30 \
      SOURCE_SIM_SUB_SERVER_COUNT=10 \
      SOURCE_SIM_SUB_SAMPLE_HZ=20 \
      SOURCE_SIM_SUB_PUBLISHING_INTERVAL_MS=50 \
      SOURCE_SIM_SUB_SAMPLING_INTERVAL_MS=50 \
      SOURCE_SIM_SUB_SOURCE_UPDATE_HZ=20 \
      SOURCE_SIM_SUB_DURATION_S=6 \
      SOURCE_SIM_SUB_WARMUP_S=1 \
      SOURCE_SIM_SUB_TIMEOUT_S=5 \
      SOURCE_SIM_SUB_SOURCE_UPDATE_ENABLED=true \
      SOURCE_SIM_SUB_RUNNER_TRACE_ENABLED=true \
      SOURCE_SIM_SUB_RUNNER_TRACE_TOP_N=5 \
      SOURCE_SIM_SUB_PROFILE_MAX_LINES=80 \
      SOURCE_SIM_SUB_QUEUE_SIZE=1 \
      SOURCE_SIM_SUB_STARTUP_STAGGER_MS=0 \
      SOURCE_SIM_SUB_MONITORED_ITEM_BATCH_SIZE=100 \
      SOURCE_SIM_SUB_MONITORED_ITEM_BATCH_GAP_MS=0 \
      SOURCE_SIM_SUB_RUN_ID=subscribe_profile_smoke \
      SOURCE_SIM_SUB_DATA_PERIOD_MAX_TOLERANCE_RATIO=0.2 \
      python -m pytest tools/source_lab/tests/test_source_simulation_multi_server_subscribe_profile.py -q -s

本测试内部固定调用的 CLI 参数如下。
除 ``access-mode``、``servers``、``profile-items``、``protocol`` 外，其余参数均由
上面的 ``SOURCE_SIM_SUB_*`` 环境变量驱动：

等价 CLI 示例：

    python -m tools.source_lab.field_profile \
      --access-mode subscribe \
      --servers tools/source_lab/tests/fixtures/simulator/field_servers.tsv \
      --profile-items tools/source_lab/tests/fixtures/simulator/signal_profile_items.tsv \
      --protocol opcua \
      --process-count 1 \
      --server-count 10 \
      --sample-hz 20 \
      --publishing-interval-ms 50 \
      --sampling-interval-ms 50 \
      --source-update-hz 20 \
      --duration 6 \
      --warmup 1 \
      --timeout 5 \
      --source-update-enabled true \
      --runner-trace true \
      --runner-trace-top-n 5 \
      --profile-max-lines 80 \
      --queue-size 1 \
      --startup-stagger-ms 0 \
      --monitored-item-batch-size 100 \
      --monitored-item-batch-gap-ms 0 \
      --run-id subscribe_profile_smoke \
      --output-dir tools/source_lab/tests/tmp/subscribe_profile
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
    """Resolve the dedicated subscribe-profile output directory.

    Returns:
        Absolute output directory for this smoke test.
    """

    return _REPO_ROOT / "tools" / "source_lab" / "tests" / "tmp" / "subscribe_profile"


def _build_env() -> dict[str, str]:
    """Build the child-process environment for the subscribe profile CLI run.

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
    """Build subscribe-profile CLI args from pytest environment variables.

    Args:
        output_dir: Output directory passed to the child CLI.

    Returns:
        CLI argument vector excluding ``sys.executable -m`` prefix.
    """

    return [
        "tools.source_lab.field_profile",
        "--access-mode",
        "subscribe",
        "--servers",
        str(_fixture_path("field_servers.tsv")),
        "--profile-items",
        str(_fixture_path("signal_profile_items.tsv")),
        "--protocol",
        "opcua",
        "--process-count",
        _env_text("SOURCE_SIM_SUB_PROCESS_COUNT", "1"),
        "--server-count",
        _env_text("SOURCE_SIM_SUB_SERVER_COUNT", "10"),
        "--sample-hz",
        _env_text("SOURCE_SIM_SUB_SAMPLE_HZ", "20"),
        "--publishing-interval-ms",
        _env_text("SOURCE_SIM_SUB_PUBLISHING_INTERVAL_MS", "50"),
        "--sampling-interval-ms",
        _env_text("SOURCE_SIM_SUB_SAMPLING_INTERVAL_MS", "50"),
        "--source-update-hz",
        _env_text("SOURCE_SIM_SUB_SOURCE_UPDATE_HZ", "20"),
        "--duration",
        _env_text("SOURCE_SIM_SUB_DURATION_S", "6"),
        "--warmup",
        _env_text("SOURCE_SIM_SUB_WARMUP_S", "1"),
        "--timeout",
        _env_text("SOURCE_SIM_SUB_TIMEOUT_S", "5"),
        "--source-update-enabled",
        _env_text("SOURCE_SIM_SUB_SOURCE_UPDATE_ENABLED", "true"),
        "--runner-trace",
        _env_text("SOURCE_SIM_SUB_RUNNER_TRACE_ENABLED", "true"),
        "--runner-trace-top-n",
        _env_text("SOURCE_SIM_SUB_RUNNER_TRACE_TOP_N", "5"),
        "--profile-max-lines",
        _env_text("SOURCE_SIM_SUB_PROFILE_MAX_LINES", "80"),
        "--queue-size",
        _env_text("SOURCE_SIM_SUB_QUEUE_SIZE", "1"),
        "--startup-stagger-ms",
        _env_text("SOURCE_SIM_SUB_STARTUP_STAGGER_MS", "0"),
        "--monitored-item-batch-size",
        _env_text("SOURCE_SIM_SUB_MONITORED_ITEM_BATCH_SIZE", "100"),
        "--monitored-item-batch-gap-ms",
        _env_text("SOURCE_SIM_SUB_MONITORED_ITEM_BATCH_GAP_MS", "0"),
        "--run-id",
        _env_text("SOURCE_SIM_SUB_RUN_ID", "subscribe_profile_smoke"),
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
def test_source_simulation_multi_server_subscribe_profile() -> None:
    """Run the subscribe profile smoke path through the formal CLI."""

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

    # 设置端口范围与订阅阈值环境，驱动正式订阅 profile 链路。
    completed = _run_cli(command, env=_build_env())

    # 回显 stdout/stderr，保证 ``pytest -s`` 能直接看到 profile 诊断报告。
    _print_completed_process(completed)

    # 断言 CLI 正常退出，并保持 subscribe 诊断报告关键信息。
    assert completed.returncode == 0, completed.stderr
    assert "source_lab subscribe scan" in completed.stdout
    assert "protocol=opcua" in completed.stdout
    assert "source_update_hz=20.0" in completed.stdout or "source_update_hz=20" in completed.stdout
    assert "queue_size=1" in completed.stdout
    assert "dispatch" in completed.stdout
    assert "access_mode=subscribe" in completed.stdout
    assert "report_path=" in completed.stdout

    # 断言 profile 报告和 JSON 摘要已经落盘。
    assert any(output_dir.glob("field_profile_*.txt"))
    assert any(output_dir.glob("field_profile_*.json"))
