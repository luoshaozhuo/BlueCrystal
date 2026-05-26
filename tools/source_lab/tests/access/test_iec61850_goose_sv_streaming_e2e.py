"""IEC 61850 GOOSE/SV streaming facade and E2E tests.

GOOSE/SV use Linux L2 raw sockets. In developer environments without
CAP_NET_RAW/root or a suitable interface these tests skip with CI commands
instead of reporting a fake pass.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from tools.source_lab.tests.access.test_server_simulator_facade_capacity_profile_e2e import (
    _FacadeE2EProvider,
    _build_e2e_source,
    _build_subscription_runner,
    _smoke_subscribe_config,
)
from tools.source_lab.access.polling.model import CapacityStatus
from tools.source_lab.access.subscribe.model import SubscribeScanResult
from tools.source_lab.access.subscribe.profile import run_subscribe_profile
from tools.source_lab.access.subscribe.scan import scan_source_subscriptions
from tools.source_lab.protocols.registry import create_server_simulator
from tools.source_lab.sources import PortAllocator


def _skip_if_l2_unavailable(protocol: str) -> None:
    names = {
        "iec61850_goose": (
            "iec61850_goose_publisher_simulator",
            "iec61850_goose_subscriber_runner",
        ),
        "iec61850_sv": (
            "iec61850_sv_publisher_simulator",
            "iec61850_sv_subscriber_runner",
        ),
    }[protocol]
    build_dir = Path(__file__).resolve().parents[2] / "native" / "build"
    missing = [name for name in names if not (build_dir / name).exists()]
    interface = os.environ.get("SOURCE_LAB_L2_INTERFACE", "lo")
    if missing:
        pytest.skip(
            "dependency_missing: "
            + ",".join(missing)
            + " not compiled. CI: cmake -S tools/source_lab/native "
            "-B tools/source_lab/native/build && cmake --build tools/source_lab/native/build"
        )
    if not _has_cap_net_raw():
        pytest.skip(
            f"raw_socket_permission_missing: {protocol} requires CAP_NET_RAW/root "
            f"and a usable L2 interface. interface={interface} "
            f"target={','.join(names)}. CI: sudo -E env SOURCE_LAB_L2_INTERFACE={interface} "
            "pytest -k 'goose or sv' tools/source_lab/tests/access -q"
        )


def _has_cap_net_raw() -> bool:
    if os.geteuid() == 0:
        return True
    try:
        for line in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
            if line.startswith("CapEff:"):
                value = int(line.split(":", 1)[1].strip(), 16)
                return bool(value & (1 << 13))
    except OSError:
        return False
    return False


async def _assert_facade_subscribe(protocol: str, point_key: str) -> None:
    _skip_if_l2_unavailable(protocol)
    source = _build_e2e_source(protocol, 0)
    facade = create_server_simulator(protocol, source)

    result = await facade.start()
    assert result.status.name == "OK", result.message
    try:
        subscription = await facade.subscribe([point_key])
        assert subscription.status.name == "OK", subscription.message
        assert "count=" in subscription.message
    finally:
        await facade.stop()


@pytest.mark.asyncio
async def test_goose_facade_real_subscribe_event() -> None:
    await _assert_facade_subscribe("iec61850_goose", "LLN0.Events.stVal")


@pytest.mark.asyncio
async def test_sv_facade_real_subscribe_sample() -> None:
    await _assert_facade_subscribe("iec61850_sv", "LLN0.PhVMeas.mag")


def _run_streaming_capacity(protocol: str) -> SubscribeScanResult:
    _skip_if_l2_unavailable(protocol)
    allocator = PortAllocator.from_range(start=41601, end=42000)
    source = _build_e2e_source(protocol, allocator.allocate_many(1)[0])
    provider = _FacadeE2EProvider(source, port_allocator=allocator)
    config = _smoke_subscribe_config(protocol)
    runner = _build_subscription_runner(protocol)
    return scan_source_subscriptions(config, provider=provider, runner=runner)


def test_goose_streaming_capacity_e2e_via_facade() -> None:
    result = _run_streaming_capacity("iec61850_goose")
    top = result.levels[0]
    assert top.final_status in (CapacityStatus.PASS, CapacityStatus.FLAKY)
    assert top.final_metrics.value_count > 0


def test_sv_streaming_capacity_e2e_via_facade() -> None:
    result = _run_streaming_capacity("iec61850_sv")
    top = result.levels[0]
    assert top.final_status in (CapacityStatus.PASS, CapacityStatus.FLAKY)
    assert top.final_metrics.value_count > 0


def _run_streaming_profile(protocol: str):
    _skip_if_l2_unavailable(protocol)
    allocator = PortAllocator.from_range(start=41701, end=42000)
    source = _build_e2e_source(protocol, allocator.allocate_many(1)[0])
    provider = _FacadeE2EProvider(source, port_allocator=allocator)
    config = _smoke_subscribe_config(protocol)
    runner = _build_subscription_runner(protocol)
    return run_subscribe_profile(config, provider=provider, runner=runner)


def test_goose_streaming_profile_e2e_via_facade() -> None:
    result = _run_streaming_profile("iec61850_goose")
    top = result.result.levels[0]
    assert top.final_status in (CapacityStatus.PASS, CapacityStatus.FLAKY)
    assert top.final_metrics.value_count > 0


def test_sv_streaming_profile_e2e_via_facade() -> None:
    result = _run_streaming_profile("iec61850_sv")
    top = result.result.levels[0]
    assert top.final_status in (CapacityStatus.PASS, CapacityStatus.FLAKY)
    assert top.final_metrics.value_count > 0
