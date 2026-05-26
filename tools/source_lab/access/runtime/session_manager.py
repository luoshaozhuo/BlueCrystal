"""Endpoint session manager using endpoint-scoped replacement threads."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Callable

from tools.source_lab.access.common.scheduling import RunnerEndpointPlan
from tools.source_lab.access.polling.model import CapacityMode, CapacityScanConfig
from tools.source_lab.access.runners.base import CapacityRunner, SubscriptionRunner
from tools.source_lab.access.runners.generic_polling import GenericPollingCapacityRunner
from tools.source_lab.access.runners.generic_streaming import GenericStreamingSubscriptionRunner
from tools.source_lab.access.runners.iec61850_l2_streaming import (
    Iec61850GooseStreamingRunner,
    Iec61850SvStreamingRunner,
)
from tools.source_lab.access.runners.iec61850_report import Iec61850ReportRunner
from tools.source_lab.access.runners.open62541_serial_polling import (
    OpcUaOpen62541CapacityRunner,
)
from tools.source_lab.access.runners.open62541_subscription import (
    OpcUaOpen62541SubscribeRunner,
)
from tools.source_lab.access.runners.registry import (
    build_capacity_runner,
    build_subscription_runner,
)
from tools.source_lab.access.runtime.continuity_monitor import ContinuityMonitor
from tools.source_lab.access.runtime.endpoint_runtime import (
    EndpointMode,
    EndpointRuntime,
    EndpointRuntimeConfig,
    EndpointRuntimeState,
    utc_now_iso,
)
from tools.source_lab.access.runtime.stagger_coordinator import StaggerCoordinator
from tools.source_lab.access.subscribe.model import SubscribeScanConfig


@dataclass
class NativeSessionHandle:
    runner_name: str
    endpoint_id: str
    cycle_count: int = 0
    last_cycle_started_at: str | None = None
    last_cycle_finished_at: str | None = None
    last_error: str | None = None
    runner_object: object | None = None


@dataclass
class _SessionControl:
    thread: threading.Thread
    stop_event: threading.Event
    pause_event: threading.Event
    handle: NativeSessionHandle = field(default_factory=lambda: NativeSessionHandle("", ""))


class EndpointSessionManager:
    def __init__(
        self,
        *,
        continuity_monitor: ContinuityMonitor,
        stagger_coordinator: StaggerCoordinator,
        polling_runner_factory: Callable[[str], CapacityRunner] | None = None,
        subscription_runner_factory: Callable[[str], SubscriptionRunner] | None = None,
    ) -> None:
        self._continuity_monitor = continuity_monitor
        self._stagger_coordinator = stagger_coordinator
        self._polling_runner_factory = polling_runner_factory or build_capacity_runner
        self._subscription_runner_factory = (
            subscription_runner_factory or build_subscription_runner
        )
        self._lock = threading.RLock()
        self._controls: dict[str, _SessionControl] = {}

    def start_endpoint(self, runtime: EndpointRuntime, config: EndpointRuntimeConfig) -> None:
        with self._lock:
            if runtime.endpoint_id in self._controls:
                raise RuntimeError(f"endpoint already started: {runtime.endpoint_id}")

            stop_event = threading.Event()
            pause_event = threading.Event()
            handle = NativeSessionHandle(
                runner_name=config.protocol,
                endpoint_id=runtime.endpoint_id,
            )
            thread = threading.Thread(
                target=self._run_endpoint_loop,
                name=f"source-lab-endpoint-{runtime.endpoint_id}",
                args=(runtime, config, stop_event, pause_event, handle),
                daemon=True,
            )
            runtime.state = EndpointRuntimeState.STARTING
            runtime.last_error = None
            runtime.last_started_at = utc_now_iso()
            runtime.updated_at = utc_now_iso()
            runtime.runner_handle = handle
            control = _SessionControl(
                thread=thread,
                stop_event=stop_event,
                pause_event=pause_event,
                handle=handle,
            )
            self._controls[runtime.endpoint_id] = control
            thread.start()

    def pause_endpoint(self, runtime: EndpointRuntime) -> None:
        with self._lock:
            control = self._controls.get(runtime.endpoint_id)
            if control is None:
                raise KeyError(runtime.endpoint_id)
            control.pause_event.set()
            runtime.state = EndpointRuntimeState.PAUSED
            runtime.updated_at = utc_now_iso()
            self._continuity_monitor.record_pause(runtime.endpoint_id)

    def resume_endpoint(self, runtime: EndpointRuntime) -> None:
        with self._lock:
            control = self._controls.get(runtime.endpoint_id)
            if control is None:
                raise KeyError(runtime.endpoint_id)
            control.pause_event.clear()
            runtime.state = EndpointRuntimeState.RUNNING
            runtime.updated_at = utc_now_iso()

    def stop_endpoint(self, runtime: EndpointRuntime) -> None:
        with self._lock:
            control = self._controls.pop(runtime.endpoint_id, None)
        if control is None:
            return

        runtime.state = EndpointRuntimeState.STOPPING
        runtime.updated_at = utc_now_iso()
        control.stop_event.set()
        control.thread.join(timeout=10.0)
        runtime.state = EndpointRuntimeState.STOPPED
        runtime.last_stopped_at = utc_now_iso()
        runtime.updated_at = utc_now_iso()
        self._continuity_monitor.record_stop(runtime.endpoint_id)

    def replace_endpoint(
        self,
        runtime: EndpointRuntime,
        config: EndpointRuntimeConfig,
    ) -> None:
        self.stop_endpoint(runtime)
        self.start_endpoint(runtime, config)

    def _run_endpoint_loop(
        self,
        runtime: EndpointRuntime,
        config: EndpointRuntimeConfig,
        stop_event: threading.Event,
        pause_event: threading.Event,
        handle: NativeSessionHandle,
    ) -> None:
        try:
            offset_seconds = runtime.stagger_offset_ns / 1_000_000_000.0
            if offset_seconds > 0:
                stop_event.wait(offset_seconds)

            if config.mode == EndpointMode.POLLING:
                self._run_polling_loop(runtime, config, stop_event, pause_event, handle)
            elif config.mode in {EndpointMode.SUBSCRIBE, EndpointMode.REPORT, EndpointMode.STREAMING}:
                self._run_subscription_loop(runtime, config, stop_event, pause_event, handle)
            else:
                raise RuntimeError(f"mode not supported in round3: {config.mode.value}")
        except Exception as exc:
            runtime.state = EndpointRuntimeState.FAILED
            runtime.last_error = str(exc)
            runtime.updated_at = utc_now_iso()
            handle.last_error = str(exc)

    def _run_polling_loop(
        self,
        runtime: EndpointRuntime,
        config: EndpointRuntimeConfig,
        stop_event: threading.Event,
        pause_event: threading.Event,
        handle: NativeSessionHandle,
    ) -> None:
        runner = self._polling_runner_factory(config.protocol)
        plan = RunnerEndpointPlan(
            global_index=0,
            source=config.source,
            offset_ns=runtime.stagger_offset_ns,
        )
        runtime.state = EndpointRuntimeState.RUNNING
        handle.runner_name = getattr(runner, "name", type(runner).__name__)
        handle.runner_object = runner
        self._continuity_monitor.bind_runtime(
            runtime.endpoint_id,
            runtime_backend=handle.runner_name,
            runner_handle_id=f"{runtime.endpoint_id}:{id(handle)}",
            permission_status="available",
        )
        self._continuity_monitor.record_start(
            runtime.endpoint_id,
            config_version=config.config_version,
            stagger_offset_ns=runtime.stagger_offset_ns,
        )

        if isinstance(runner, GenericPollingCapacityRunner):
            self._run_generic_polling_loop(
                runtime, config, stop_event, pause_event, handle, runner, plan
            )
            return
        if isinstance(runner, OpcUaOpen62541CapacityRunner):
            self._run_native_polling_loop(
                runtime, config, stop_event, pause_event, handle, runner, plan
            )
            return
        raise RuntimeError(
            f"polling runner does not support endpoint runtime: {type(runner).__name__}"
        )

    def _run_generic_polling_loop(
        self,
        runtime: EndpointRuntime,
        config: EndpointRuntimeConfig,
        stop_event: threading.Event,
        pause_event: threading.Event,
        handle: NativeSessionHandle,
        runner: GenericPollingCapacityRunner,
        plan: RunnerEndpointPlan,
    ) -> None:
        period_s = max(0.01, config.expected_period_ms() / 1000.0)
        cfg = CapacityScanConfig(
            mode=CapacityMode.SIMULATOR,
            protocol=config.protocol,
            endpoints=(config.source.endpoint,),
            points=config.source.points,
            server_count_start=1,
            server_count_step=1,
            server_count_max=1,
            hz_start=config.target_hz or 1.0,
            hz_step=config.target_hz or 1.0,
            hz_max=config.target_hz or 1.0,
            process_count=1,
            level_duration_s=period_s,
            read_timeout_s=config.read_timeout_s,
        )
        next_run = time.monotonic()
        while not stop_event.is_set():
            if pause_event.is_set():
                stop_event.wait(0.02)
                continue
            now = time.monotonic()
            if now < next_run:
                stop_event.wait(next_run - now)
                continue

            handle.cycle_count += 1
            handle.last_cycle_started_at = utc_now_iso()
            self._continuity_monitor.record_expected_tick(runtime.endpoint_id)
            sample = runner.read_once(
                plan,
                target_hz=config.target_hz or 1.0,
                config=cfg,
            )
            self._continuity_monitor.record_sample(
                runtime.endpoint_id,
                timestamp_ms=time.time() * 1000.0,
                expected_period_ms=config.expected_period_ms(),
                successful=sample.ok,
            )
            handle.last_cycle_finished_at = utc_now_iso()
            next_run += period_s

    def _run_native_polling_loop(
        self,
        runtime: EndpointRuntime,
        config: EndpointRuntimeConfig,
        stop_event: threading.Event,
        pause_event: threading.Event,
        handle: NativeSessionHandle,
        runner: OpcUaOpen62541CapacityRunner,
        plan: RunnerEndpointPlan,
    ) -> None:
        period_s = max(0.2, config.expected_period_ms() / 1000.0)
        cfg = CapacityScanConfig(
            mode=CapacityMode.SIMULATOR,
            protocol=config.protocol,
            endpoints=(config.source.endpoint,),
            points=config.source.points,
            server_count_start=1,
            server_count_step=1,
            server_count_max=1,
            hz_start=config.target_hz or 1.0,
            hz_step=config.target_hz or 1.0,
            hz_max=config.target_hz or 1.0,
            process_count=1,
            warmup_s=0.0,
            level_duration_s=period_s,
            read_timeout_s=config.read_timeout_s,
            min_expected_point_count=1,
            max_expected_point_count=max(1, len(config.source.points)),
        )
        while not stop_event.is_set():
            if pause_event.is_set():
                stop_event.wait(0.02)
                continue

            handle.cycle_count += 1
            handle.last_cycle_started_at = utc_now_iso()
            self._continuity_monitor.record_expected_tick(runtime.endpoint_id)
            stats = runner.run_worker(
                0,
                (plan,),
                config.target_hz or 1.0,
                cfg,
            )
            successful = stats.ok_reads > 0 and stats.read_errors == 0
            timestamp_ms = time.time() * 1000.0
            for _ in range(max(1, stats.ok_reads or stats.total_reads or 1)):
                self._continuity_monitor.record_sample(
                    runtime.endpoint_id,
                    timestamp_ms=timestamp_ms,
                    expected_period_ms=config.expected_period_ms(),
                    successful=successful,
                )
            handle.last_cycle_finished_at = utc_now_iso()
            stop_event.wait(period_s)

    def _run_subscription_loop(
        self,
        runtime: EndpointRuntime,
        config: EndpointRuntimeConfig,
        stop_event: threading.Event,
        pause_event: threading.Event,
        handle: NativeSessionHandle,
    ) -> None:
        runner = self._subscription_runner_factory(config.protocol)
        plan = RunnerEndpointPlan(
            global_index=0,
            source=config.source,
            offset_ns=runtime.stagger_offset_ns,
        )
        runtime.state = EndpointRuntimeState.RUNNING
        handle.runner_name = getattr(runner, "name", type(runner).__name__)
        handle.runner_object = runner
        self._continuity_monitor.bind_runtime(
            runtime.endpoint_id,
            runtime_backend=handle.runner_name,
            runner_handle_id=f"{runtime.endpoint_id}:{id(handle)}",
            permission_status="available",
        )
        self._continuity_monitor.record_start(
            runtime.endpoint_id,
            config_version=config.config_version,
            stagger_offset_ns=runtime.stagger_offset_ns,
        )

        if isinstance(runner, (GenericStreamingSubscriptionRunner, Iec61850ReportRunner)):
            self._run_generic_subscription_loop(
                runtime, config, stop_event, pause_event, handle, runner, plan
            )
            return
        if isinstance(runner, OpcUaOpen62541SubscribeRunner):
            self._run_native_subscription_loop(
                runtime, config, stop_event, pause_event, handle, runner, plan
            )
            return
        if isinstance(runner, (Iec61850GooseStreamingRunner, Iec61850SvStreamingRunner)):
            self._run_worker_subscription_loop(
                runtime,
                config,
                stop_event,
                pause_event,
                handle,
                runner,
                plan,
            )
            return
        raise RuntimeError(
            f"subscription runner does not support endpoint runtime: {type(runner).__name__}"
        )

    def _run_generic_subscription_loop(
        self,
        runtime: EndpointRuntime,
        config: EndpointRuntimeConfig,
        stop_event: threading.Event,
        pause_event: threading.Event,
        handle: NativeSessionHandle,
        runner: GenericStreamingSubscriptionRunner,
        plan: RunnerEndpointPlan,
    ) -> None:
        period_s = max(0.05, config.expected_period_ms() / 1000.0)
        cfg = SubscribeScanConfig(
            mode=CapacityMode.SIMULATOR,
            protocol=config.protocol,
            server_count_start=1,
            server_count_step=1,
            server_count_max=1,
            process_count=1,
            publishing_interval_ms=config.publishing_interval_ms or 1000.0,
            sampling_interval_ms=config.publishing_interval_ms or 1000.0,
            queue_size=1,
            duration_s=period_s,
            read_timeout_s=config.read_timeout_s,
            source_update_enabled=False,
        )
        next_run = time.monotonic()
        while not stop_event.is_set():
            if pause_event.is_set():
                stop_event.wait(0.02)
                continue
            now = time.monotonic()
            if now < next_run:
                stop_event.wait(next_run - now)
                continue

            handle.cycle_count += 1
            handle.last_cycle_started_at = utc_now_iso()
            self._continuity_monitor.record_expected_tick(runtime.endpoint_id)
            sample = runner.read_stream_sample(plan, config=cfg)
            effective_expected_period_ms = max(config.expected_period_ms(), 1500.0)
            self._continuity_monitor.record_event(
                runtime.endpoint_id,
                timestamp_ms=time.time() * 1000.0,
                expected_period_ms=effective_expected_period_ms,
                successful=sample.value_count > 0 and sample.bad_count == 0,
            )
            handle.last_cycle_finished_at = utc_now_iso()
            next_run += period_s

    def _run_native_subscription_loop(
        self,
        runtime: EndpointRuntime,
        config: EndpointRuntimeConfig,
        stop_event: threading.Event,
        pause_event: threading.Event,
        handle: NativeSessionHandle,
        runner: OpcUaOpen62541SubscribeRunner,
        plan: RunnerEndpointPlan,
    ) -> None:
        period_s = max(0.3, config.expected_period_ms() / 1000.0)
        cfg = SubscribeScanConfig(
            mode=CapacityMode.SIMULATOR,
            protocol=config.protocol,
            server_count_start=1,
            server_count_step=1,
            server_count_max=1,
            process_count=1,
            publishing_interval_ms=config.publishing_interval_ms or 500.0,
            sampling_interval_ms=config.publishing_interval_ms or 500.0,
            queue_size=4,
            duration_s=period_s,
            read_timeout_s=config.read_timeout_s,
            source_update_enabled=True,
            source_update_hz=4.0,
            min_expected_point_count=1,
            max_expected_point_count=max(1, len(config.source.points)),
        )
        while not stop_event.is_set():
            if pause_event.is_set():
                stop_event.wait(0.02)
                continue

            handle.cycle_count += 1
            handle.last_cycle_started_at = utc_now_iso()
            self._continuity_monitor.record_expected_tick(runtime.endpoint_id)
            stats = runner.run_worker(0, (plan,), cfg)
            successful = stats.notification_count > 0 and stats.bad_count == 0
            timestamp_ms = time.time() * 1000.0
            effective_expected_period_ms = max(config.expected_period_ms(), 1500.0)
            for _ in range(max(1, stats.notification_count or 1)):
                self._continuity_monitor.record_event(
                    runtime.endpoint_id,
                    timestamp_ms=timestamp_ms,
                    expected_period_ms=effective_expected_period_ms,
                    successful=successful,
                )
            handle.last_cycle_finished_at = utc_now_iso()
            stop_event.wait(period_s)

    def _run_worker_subscription_loop(
        self,
        runtime: EndpointRuntime,
        config: EndpointRuntimeConfig,
        stop_event: threading.Event,
        pause_event: threading.Event,
        handle: NativeSessionHandle,
        runner: SubscriptionRunner,
        plan: RunnerEndpointPlan,
    ) -> None:
        period_s = max(1.0, config.expected_period_ms() / 1000.0)
        cfg = SubscribeScanConfig(
            mode=CapacityMode.SIMULATOR,
            protocol=config.protocol,
            server_count_start=1,
            server_count_step=1,
            server_count_max=1,
            process_count=1,
            publishing_interval_ms=config.publishing_interval_ms or 1000.0,
            sampling_interval_ms=config.publishing_interval_ms or 1000.0,
            queue_size=4,
            duration_s=period_s,
            read_timeout_s=config.read_timeout_s,
            source_update_enabled=True,
            source_update_hz=4.0,
            min_expected_point_count=1,
            max_expected_point_count=max(1, len(config.source.points)),
        )
        while not stop_event.is_set():
            if pause_event.is_set():
                stop_event.wait(0.02)
                continue

            handle.cycle_count += 1
            handle.last_cycle_started_at = utc_now_iso()
            self._continuity_monitor.record_expected_tick(runtime.endpoint_id)
            try:
                stats = runner.run_worker(0, (plan,), cfg)
                self._continuity_monitor.bind_runtime(
                    runtime.endpoint_id,
                    runtime_backend=handle.runner_name,
                    runner_handle_id=f"{runtime.endpoint_id}:{id(handle)}",
                    permission_status="available",
                )
            except RuntimeError as exc:
                message = str(exc)
                permission_status = (
                    "raw_socket_permission_missing"
                    if "CAP_NET_RAW" in message or "raw socket" in message
                    else "dependency_missing"
                    if "dependency_missing" in message
                    else "failed"
                )
                self._continuity_monitor.bind_runtime(
                    runtime.endpoint_id,
                    runtime_backend=handle.runner_name,
                    runner_handle_id=f"{runtime.endpoint_id}:{id(handle)}",
                    permission_status=permission_status,
                )
                self._continuity_monitor.record_stream_drop(runtime.endpoint_id)
                raise

            successful = stats.notification_count > 0 and stats.bad_count == 0
            timestamp_ms = time.time() * 1000.0
            for _ in range(max(1, stats.notification_count or 1)):
                self._continuity_monitor.record_event(
                    runtime.endpoint_id,
                    timestamp_ms=timestamp_ms,
                    expected_period_ms=max(config.expected_period_ms(), period_s * 1000.0),
                    successful=successful,
                )
            handle.last_cycle_finished_at = utc_now_iso()
            stop_event.wait(period_s)
