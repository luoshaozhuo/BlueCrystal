"""Pytest entrypoint for source_lab capacity scanner.

This test is a thin wrapper over tools.source_lab.access and keeps scanner
logic outside pytest.

Notes:
- Capacity scans use the open62541 serial polling runner adapter.

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

import pytest

from tools.source_lab.access import print_capacity_report
from tools.source_lab.access.config import from_env_for_simulator
from tools.source_lab.access.capacity import scan_source_capacity
from tools.source_lab.access.providers.simulator import SimulatorSourceProvider
from tools.source_lab.access.runners.open62541_serial_polling import OpcUaOpen62541CapacityRunner


@pytest.mark.load
def test_source_simulation_multi_server_capacity() -> None:
    config = from_env_for_simulator()
    provider = SimulatorSourceProvider.from_env()
    runner = OpcUaOpen62541CapacityRunner()

    result = scan_source_capacity(config, provider=provider, runner=runner)
    print_capacity_report(result)

    assert result.levels
    assert result.has_accepted_level
