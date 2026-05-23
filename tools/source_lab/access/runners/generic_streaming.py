"""通用 streaming runner 基类，供订阅类协议复用。"""

from __future__ import annotations

from dataclasses import dataclass
import time

from tools.source_lab.access.common.access_model import AccessBatch, AccessMode
from tools.source_lab.access.runners.base import SubscriptionRunner
from tools.source_lab.access.common.scheduling import RunnerEndpointPlan
from tools.source_lab.access.subscribe.model import SubscribeScanConfig, SubscribeWorkerRawStats


@dataclass(frozen=True, slots=True)
class StreamingSample:
    """单次 streaming 采样结果。"""

    value_count: int
    bad_count: int = 0
    missing_ts_count: int = 0
    data_age_ms: float | None = None


class GenericStreamingSubscriptionRunner(SubscriptionRunner):
    """通用 streaming runner。

    子类只需实现 ``read_stream_sample``，其余统计由基类统一构建。
    """

    name: str = "generic_streaming_runner"

    def read_stream_sample(
        self,
        spec: RunnerEndpointPlan,
        *,
        config: SubscribeScanConfig,
    ) -> StreamingSample:
        """读取一个订阅样本。"""

        raise NotImplementedError

    def run_worker(
        self,
        worker_index: int,
        specs: tuple[RunnerEndpointPlan, ...],
        config: SubscribeScanConfig,
    ) -> SubscribeWorkerRawStats:
        """执行一个订阅 worker 分片。"""

        if not specs:
            return SubscribeWorkerRawStats(
                worker_index=worker_index,
                endpoint_count=0,
                expected_monitored_items=0,
                monitored_created=0,
                monitored_failed=0,
                batches=(),
                notification_count=0,
                value_count=0,
                bad_count=0,
                missing_ts_count=0,
                reserved_sequence_gap_count=0,
                reserved_queue_overflow_count=0,
                keepalive_count=0,
                publish_timeout_count=0,
                reconnect_count=0,
            )

        total_batches = max(1, int(round(config.duration_s / max(0.001, config.publishing_interval_ms / 1000.0))))
        now_ns = time.time_ns()
        batches: list[AccessBatch] = []
        value_count = 0
        bad_count = 0
        missing_ts_count = 0

        for batch_index in range(total_batches):
            for local_index, spec in enumerate(specs):
                sample = self.read_stream_sample(spec, config=config)
                value_count += sample.value_count
                bad_count += sample.bad_count
                missing_ts_count += sample.missing_ts_count
                batches.append(
                    AccessBatch(
                        endpoint_id=spec.source.endpoint.name,
                        profile_id=str(spec.source.endpoint.params.get("profile_id", "")),
                        protocol=str(spec.source.endpoint.protocol),
                        access_mode=AccessMode.SUBSCRIBE,
                        worker_index=worker_index,
                        local_index=local_index,
                        global_index=spec.global_index,
                        batch_index=batch_index,
                        sequence=batch_index,
                        scheduled_ns=None,
                        started_ns=None,
                        received_ns=now_ns + batch_index,
                        source_timestamp_s=time.time(),
                        server_timestamp_s=time.time(),
                        value_count=sample.value_count,
                        expected_count=len(spec.source.points),
                        bad_count=sample.bad_count,
                        missing_timestamp_count=sample.missing_ts_count,
                        error_code=None,
                        data_age_ms=sample.data_age_ms,
                        period_ms=config.publishing_interval_ms,
                        notify_timestamp_ns=now_ns + batch_index,
                        flush_timestamp_ns=now_ns + batch_index + 1,
                    )
                )

        expected_monitored_items = sum(len(spec.source.points) for spec in specs)
        return SubscribeWorkerRawStats(
            worker_index=worker_index,
            endpoint_count=len(specs),
            expected_monitored_items=expected_monitored_items,
            monitored_created=expected_monitored_items,
            monitored_failed=0,
            batches=tuple(batches),
            notification_count=len(batches),
            value_count=value_count,
            bad_count=bad_count,
            missing_ts_count=missing_ts_count,
            reserved_sequence_gap_count=0,
            reserved_queue_overflow_count=0,
            keepalive_count=0,
            publish_timeout_count=0,
            reconnect_count=0,
        )
