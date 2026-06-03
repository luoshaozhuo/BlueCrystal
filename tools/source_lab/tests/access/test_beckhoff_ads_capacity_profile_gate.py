"""Beckhoff ADS capacity/profile 最小门禁测试。"""

from __future__ import annotations

import asyncio

from tools.source_lab.access.common.scheduling import build_source_specs
from tools.source_lab.access.polling.model import CapacityMode, CapacityScanConfig
from tools.source_lab.access.providers.base import SourceRuntimeSpec
from tools.source_lab.access.runners.registry import build_capacity_runner, describe_protocol_runtime_readiness
from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec  # type: ignore[import-untyped]
from tools.source_lab.protocols.registry import create_server_simulator

from tools.source_lab.tests.access.test_beckhoff_ads_simulator_contract import _build_ads_source


def _capacity_config() -> CapacityScanConfig:
    return CapacityScanConfig(
        mode=CapacityMode.FIELD,
        protocol="beckhoff_ads",
        endpoints=(),
        points=(),
        server_count_start=1,
        server_count_step=1,
        server_count_max=1,
        hz_start=1.0,
        hz_step=1.0,
        hz_max=1.0,
        process_count=1,
        progress_enabled=False,
    )


def test_beckhoff_ads_capacity_runner_reads_from_active_simulator() -> None:
    """ADS capacity runner 至少应能对活动 simulator 做一次最小 polling smoke。"""

    source = _build_ads_source()
    runtime_spec = SourceRuntimeSpec(
        endpoint=SourceEndpointSpec(
            name=source.connection.name,
            host=source.connection.host,
            port=source.connection.port,
            protocol=source.connection.protocol,
            transport=source.connection.transport,
            namespace_uri=source.connection.namespace_uri,
            ied_name=source.connection.ied_name,
            ld_name=source.connection.ld_name,
            params=dict(source.connection.params),
        ),
        points=tuple(
            SourcePointSpec(
                name=point.key,
                address=point.address or point.key,
                data_type=point.data_type,
                ln_name=point.ln_name,
                do_name=point.do_name,
                unit=point.unit,
            )
            for point in source.points
        ),
        runtime_handle=source,
    )

    facade = create_server_simulator("beckhoff_ads", source)
    runner = build_capacity_runner("beckhoff_ads")
    plans = build_source_specs((runtime_spec,), target_hz=1.0)

    async def _run() -> None:
        assert (await facade.start()).status.name == "OK"
        try:
            stats = runner.run_worker(0, plans, 1.0, _capacity_config())
            assert stats.total_reads >= 1
            assert stats.ok_reads >= 1
            assert stats.read_errors == 0
        finally:
            assert (await facade.stop()).status.name == "OK"

    asyncio.run(_run())


def test_beckhoff_ads_polling_readiness_is_degraded_python_fallback() -> None:
    """在缺少 AdsLib binary 时，polling readiness 必须显式为 degraded fallback。"""

    readiness = describe_protocol_runtime_readiness("beckhoff_ads", "polling")
    assert readiness.actual_runtime_availability in {"degraded_python_fallback", "available_native"}
    if readiness.actual_runtime_availability == "degraded_python_fallback":
        assert readiness.native_check_error is not None
