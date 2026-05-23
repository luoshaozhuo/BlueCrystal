"""通用 polling runner 基类，供多协议实现复用。"""

from __future__ import annotations

from dataclasses import dataclass
import time

from tools.source_lab.access.polling.metrics import ReaderStats, WorkerRawStats, record_tick
from tools.source_lab.access.polling.model import CapacityScanConfig, TickResult
from tools.source_lab.access.runners.base import CapacityRunner
from tools.source_lab.access.common.scheduling import RunnerEndpointPlan


@dataclass(frozen=True, slots=True)
class PollingReadSample:
    """单次轮询读取样本。"""

    ok: bool
    value_count: int
    response_timestamp_s: float | None
    error_code: str | None = None


class GenericPollingCapacityRunner(CapacityRunner):
    """通用 polling runner。

    子类只需实现 ``read_once`` 即可复用 worker 级统计逻辑。
    """

    name: str = "generic_polling_runner"

    def read_once(
        self,
        spec: RunnerEndpointPlan,
        *,
        target_hz: float,
        config: CapacityScanConfig,
    ) -> PollingReadSample:
        """执行一次协议读取。

        Args:
            spec: 目标 endpoint 计划。
            target_hz: 当前目标采样频率。
            config: 轮询扫描配置。

        Returns:
            一次读取结果。
        """

        raise NotImplementedError

    def run_worker(
        self,
        worker_index: int,
        specs: tuple[RunnerEndpointPlan, ...],
        target_hz: float,
        config: CapacityScanConfig,
    ) -> WorkerRawStats:
        """执行一个 worker 分片。"""

        if not specs:
            return WorkerRawStats(
                worker_index=worker_index,
                reader_count=0,
                batch_mismatches=0,
                read_errors=0,
                missing_response_timestamps=0,
                response_timestamps_by_reader=(),
                max_observed_concurrent_reads=0,
            )

        total_ticks = max(1, int(round(config.level_duration_s * target_hz)))
        responses: list[tuple[float, ...]] = []
        read_errors = 0
        batch_mismatches = 0
        missing_response_timestamps = 0
        total_reads = 0
        ok_reads = 0
        value_count = 0

        for spec in specs:
            stats = ReaderStats()
            expected = len(spec.source.points)
            for _ in range(total_ticks):
                started = time.perf_counter_ns()
                sample = self.read_once(spec, target_hz=target_hz, config=config)
                elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000.0
                tick = TickResult(
                    ok=sample.ok,
                    error=sample.error_code,
                    elapsed_ms=elapsed_ms,
                    value_count=sample.value_count,
                    response_timestamp_s=sample.response_timestamp_s,
                )
                record_tick(stats, tick)
                if sample.ok and sample.value_count != expected:
                    batch_mismatches += 1
                if sample.ok and sample.response_timestamp_s is None:
                    missing_response_timestamps += 1
            read_errors += stats.read_errors
            total_reads += stats.total_reads
            ok_reads += stats.ok_reads
            value_count += stats.value_count
            responses.append(tuple(stats.response_timestamps))

        return WorkerRawStats(
            worker_index=worker_index,
            reader_count=len(specs),
            batch_mismatches=batch_mismatches,
            read_errors=read_errors,
            missing_response_timestamps=missing_response_timestamps,
            response_timestamps_by_reader=tuple(responses),
            max_observed_concurrent_reads=1,
            total_reads=total_reads,
            ok_reads=ok_reads,
            value_count=value_count,
        )
