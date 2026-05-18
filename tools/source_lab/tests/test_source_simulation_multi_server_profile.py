"""Profile one simulator-backed capacity level through the formal access path.

cd ~/Whale

SOURCE_SIM_LOAD_PROCESS_COUNT=5 \
SOURCE_SIM_LOAD_SERVER_COUNT=50 \
SOURCE_SIM_LOAD_TARGET_HZ=50 \
SOURCE_SIM_LOAD_LEVEL_DURATION_S=120 \
SOURCE_SIM_LOAD_WARMUP_S=10 \
SOURCE_SIM_LOAD_SOURCE_UPDATE_ENABLED=false \
SOURCE_SIM_LOAD_PERIOD_MAX_TOLERANCE_RATIO=0.2 \
SOURCE_SIM_LOAD_PERIOD_MEAN_ERROR_RATIO=0.05 \
SOURCE_SIM_LOAD_FAIL_CONFIRM_RUNS=1 \
SOURCE_SIM_LOAD_ACCEPT_FLAKY_AS_PASS=false \
SOURCE_SIM_LOAD_STOP_HZ_RAMP_ON_FIRST_FAIL=true \
SOURCE_SIM_LOAD_TOP_GAP_COUNT=30 \
SOURCE_SIM_LOAD_PROGRESS_ENABLED=true \
SOURCE_SIM_LOAD_PROGRESS_INTERVAL_S=5 \
SOURCE_SIM_LOAD_RUNNER_TRACE_ENABLED=true \
SOURCE_SIM_LOAD_RUNNER_TRACE_TOP_N=30 \
SOURCE_SIM_FLEET_STARTUP_TIMEOUT_S=60 \
SOURCE_SIM_FLEET_STOP_GRACE_S=0.2 \
SOURCE_SIM_PORT_START=52000 \
SOURCE_SIM_PORT_END=65000 \
SOURCE_SIM_LOAD_MIN_POINTS=300 \
SOURCE_SIM_LOAD_MAX_POINTS=500 \
SOURCE_SIM_LOAD_VERBOSE_ERRORS=true \
python -m pytest tools/source_lab/tests/test_source_simulation_multi_server_profile.py -s -v
"""

from __future__ import annotations

import os
from dataclasses import replace
from typing import Protocol, cast

import pytest

from tools.source_lab.access import print_capacity_report
from tools.source_lab.access.capacity import scan_source_capacity
from tools.source_lab.access.config import from_env_for_simulator
from tools.source_lab.access.model import CapacityScanConfig
from tools.source_lab.access.providers.simulator import SimulatorSourceProvider
from tools.source_lab.access.runners.open62541_serial_polling import OpcUaOpen62541CapacityRunner


class _ProfilerLike(Protocol):
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def output_text(self, *, unicode: bool, color: bool, show_all: bool) -> str: ...


def _env_flag(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _env_first_int(names: tuple[str, ...], default: int) -> int:
    for name in names:
        value = os.environ.get(name)
        if value is not None and value.strip() != "":
            return int(value)
    return default


def _env_first_float(names: tuple[str, ...], default: float) -> float:
    for name in names:
        value = os.environ.get(name)
        if value is not None and value.strip() != "":
            return float(value)
    return default


def _trim_text_lines(text: str, *, max_lines: int) -> str:
    if max_lines <= 0:
        return text
    lines = text.splitlines()
    return text if len(lines) <= max_lines else "\n".join(lines[:max_lines])


def _new_profiler() -> _ProfilerLike | None:
    try:
        from pyinstrument import Profiler  # type: ignore[import-not-found, import-untyped]
    except ImportError:
        return None
    return cast(_ProfilerLike, Profiler(async_mode="enabled"))


def _print_profiler_report(profiler: _ProfilerLike | None) -> None:
    if profiler is None:
        print("pyinstrument not installed; profiler output skipped")
        return
    report = profiler.output_text(
        unicode=True,
        color=True,
        show_all=_env_flag("SOURCE_SIM_PROFILE_SHOW_ALL", False),
    )
    print()
    print(_trim_text_lines(report, max_lines=_env_first_int(("SOURCE_SIM_PROFILE_MAX_LINES",), 80)))


def _maybe_install_uvloop() -> None:
    if not _env_flag("SOURCE_SIM_PROFILE_USE_UVLOOP", False):
        return
    try:
        import uvloop  # type: ignore[import-not-found, import-untyped]
    except ImportError:
        pytest.skip("SOURCE_SIM_PROFILE_USE_UVLOOP=true but uvloop is not installed")
    uvloop.install()


def _single_level_config() -> CapacityScanConfig:
    config = from_env_for_simulator()
    server_count = _env_first_int(
        ("SOURCE_SIM_LOAD_SERVER_COUNT", "SOURCE_SIM_LOAD_SERVER_COUNT_START"),
        config.server_count_start,
    )
    target_hz = _env_first_float(
        ("SOURCE_SIM_LOAD_TARGET_HZ", "SOURCE_SIM_LOAD_HZ_START"),
        config.hz_start,
    )
    return replace(
        config,
        server_count_start=server_count,
        server_count_step=1,
        server_count_max=server_count,
        hz_start=target_hz,
        hz_step=target_hz,
        hz_max=target_hz,
    )


@pytest.mark.load
def test_source_simulation_multi_server_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _maybe_install_uvloop()
    monkeypatch.setenv("SOURCE_SIM_LOAD_RUNNER_TRACE_ENABLED", "true")
    monkeypatch.setenv("SOURCE_SIM_LOAD_RUNNER_TRACE_TOP_N", "5")
    observed_progress: list[str] = []
    reporter_module = __import__("tools.source_lab.access.reporter", fromlist=["_emit_progress_line"])
    original_emit = reporter_module._emit_progress_line

    def _record_progress(message: str) -> None:
        observed_progress.append(message)
        original_emit(message)

    monkeypatch.setattr(reporter_module, "_emit_progress_line", _record_progress)

    config = _single_level_config()
    provider = SimulatorSourceProvider.from_env()
    runner = OpcUaOpen62541CapacityRunner()
    profiler = _new_profiler()

    if profiler is not None:
        profiler.start()
        try:
            result = scan_source_capacity(config, provider=provider, runner=runner)
        finally:
            profiler.stop()
    else:
        result = scan_source_capacity(config, provider=provider, runner=runner)

    print_capacity_report(result)
    _print_profiler_report(profiler)

    assert len(result.levels) == 1
    assert result.levels[0].primary.server_count == config.server_count_start
    joined = "\n".join(observed_progress)
    assert "runner summaries" in joined
    assert "top runner lag" in joined
    assert "top runner read" in joined
