"""Beckhoff ADS polling runner。

当前为 source_lab 工具层 Python lightweight 实现，通过进程内 ADS simulator
注册表读取点值；同时保留 AdsLib native runner 的预检/降级路径。
"""

from __future__ import annotations

import time

from tools.source_lab.access.common.scheduling import RunnerEndpointPlan
from tools.source_lab.access.polling.model import CapacityScanConfig
from tools.source_lab.access.runners.generic_polling import GenericPollingCapacityRunner, PollingReadSample
from tools.source_lab.model import SimulatedSource
from tools.source_lab.protocols.beckhoff_ads.runtime import ADS_SIMULATOR_REGISTRY, AdsRuntimeUnavailableError


class BeckhoffAdsPollingRunner(GenericPollingCapacityRunner):
    """基于 source_lab ADS simulator 注册表的 polling runner。"""

    name = "beckhoff_ads_polling_runner"

    def read_once(
        self,
        spec: RunnerEndpointPlan,
        *,
        target_hz: float,
        config: CapacityScanConfig,
    ) -> PollingReadSample:
        runtime_handle = getattr(spec.source, "runtime_handle", None)
        if not isinstance(runtime_handle, SimulatedSource):
            return PollingReadSample(
                ok=False,
                value_count=0,
                response_timestamp_s=None,
                error_code="missing_runtime_handle",
            )
        try:
            point_names = [str(point.name) for point in spec.source.points if point.name]
            values = ADS_SIMULATOR_REGISTRY.read(
                runtime_handle,
                point_names,
            )
            return PollingReadSample(
                ok=bool(values),
                value_count=len(values),
                response_timestamp_s=time.time(),
                error_code=None if values else "ads_no_values",
            )
        except AdsRuntimeUnavailableError:
            return PollingReadSample(
                ok=False,
                value_count=0,
                response_timestamp_s=None,
                error_code="ads_runtime_unavailable",
            )
