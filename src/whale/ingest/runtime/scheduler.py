# mypy: disable-error-code=import-untyped
"""Runtime scheduler for ingest."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from collections.abc import Callable
from threading import Event

from apscheduler.events import (  # type: ignore[import-untyped]
    EVENT_JOB_ERROR,
    EVENT_JOB_EXECUTED,
    JobExecutionEvent,
)
from apscheduler.schedulers.base import BaseScheduler  # type: ignore[import-untyped]

from whale.ingest.ports.runtime.source_runtime_config_port import (
    SourceRuntimeConfigData,
    SourceRuntimeConfigPort,
)
from whale.ingest.runtime.acquisition_mode import AcquisitionMode
from whale.ingest.runtime.job_status import JobStatus
from whale.ingest.runtime.scheduler_job import (
    AcquisitionStatus,
    ScheduledSourceJob,
)
from whale.ingest.runtime.scheduler_factory import build_scheduler
from whale.ingest.runtime.scheduler_settings import SchedulerSettings
from whale.ingest.usecases.build_runtime_plan_usecase import RuntimePlanBuildUseCase
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    SourceAcquisitionRequest,
)
from whale.ingest.usecases.polling_acquisition_usecase import (
    PollingAcquisitionUseCase,
)
from whale.ingest.usecases.subscribe_acquisition_usecase import (
    SubscribeAcquisitionUseCase,
)

PollingAcquisitionUseCaseFactory = Callable[[], PollingAcquisitionUseCase]
SubscribeAcquisitionUseCaseFactory = Callable[[], SubscribeAcquisitionUseCase]


class SourceScheduler:
    """Drive ingest use cases from runtime configurations."""

    def __init__(
        self,
        runtime_config_port: SourceRuntimeConfigPort,
        plan_build_usecase: RuntimePlanBuildUseCase,
        polling_acquisition_usecase_factory: PollingAcquisitionUseCaseFactory,
        subscribe_acquisition_usecase_factory: SubscribeAcquisitionUseCaseFactory,
        settings: SchedulerSettings | None = None,
    ) -> None:
        """Initialize the scheduler with required dependencies."""
        self._runtime_config_port = runtime_config_port
        self._plan_build_usecase = plan_build_usecase
        self._polling_usecase_factory = polling_acquisition_usecase_factory
        self._subscribe_usecase_factory = subscribe_acquisition_usecase_factory
        self._settings = settings or SchedulerSettings()
        self._scheduler: BaseScheduler = build_scheduler(self._settings)
        self._jobs: dict[str, ScheduledSourceJob] = {}

        self._scheduler.add_listener(
            self._on_job_executed_or_failed,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR,
        )

    def run(self) -> None:
        """Load enabled execution plans and start the scheduler."""
        self.reload()
        self._scheduler.start()

    def wait_until_terminal(self, timeout_seconds: float) -> bool:
        """Wait until all registered jobs reach terminal states."""
        deadline = time.monotonic() + timeout_seconds
        terminal_statuses = {JobStatus.FINISHED, JobStatus.FAILED, JobStatus.STOPPED}

        while time.monotonic() < deadline:
            if all(job.status in terminal_statuses for job in self._jobs.values()):
                return True
            time.sleep(0.05)

        return all(job.status in terminal_statuses for job in self._jobs.values())

    def has_failures(self) -> bool:
        """Return whether any registered job failed."""
        return any(
            job.status is JobStatus.FAILED
            or (job.last_result is not None and job.last_result.status is AcquisitionStatus.FAILED)
            for job in self._jobs.values()
        )

    def stop(self, wait: bool = True) -> None:
        """Request runtime jobs to stop and shutdown the scheduler."""
        for runtime_job in self._jobs.values():
            if runtime_job.stop_event is not None:
                runtime_job.stop_event.set()

        if self._scheduler.running:
            self._scheduler.shutdown(wait=wait)

        for runtime_job in self._jobs.values():
            if runtime_job.status in {JobStatus.SCHEDULED, JobStatus.RUNNING}:
                runtime_job.status = JobStatus.STOPPED

    def reload(self) -> None:
        """Reload enabled execution plans and register jobs again."""
        self._clear_registered_jobs()
        self._register_jobs()

    def get_runtime_jobs(self) -> list[ScheduledSourceJob]:
        """Return in-memory runtime jobs."""
        return list(self._jobs.values())

    def _register_jobs(self) -> None:
        """Register jobs from enabled runtime configs."""
        runtime_configs = self._runtime_config_port.list_enabled()
        polling_groups: dict[str, list[SourceRuntimeConfigData]] = defaultdict(list)
        subscription_groups: dict[str, list[SourceRuntimeConfigData]] = defaultdict(list)

        for runtime_config in runtime_configs:
            mode = self._get_acquisition_mode(runtime_config)
            protocol = runtime_config.protocol

            if mode is AcquisitionMode.ONCE:
                self._register_once_job(runtime_config)
            elif mode is AcquisitionMode.POLLING:
                polling_groups[protocol].append(runtime_config)
            elif mode is AcquisitionMode.SUBSCRIPTION:
                subscription_groups[protocol].append(runtime_config)
            else:
                raise ValueError(f"Unsupported acquisition mode: {mode}")

        for protocol, group in polling_groups.items():
            self._register_polling_job(
                protocol=protocol,
                runtime_configs=tuple(group),
            )

        for protocol, group in subscription_groups.items():
            self._register_subscription_job(
                protocol=protocol,
                runtime_configs=tuple(group),
            )

    def _register_once_job(self, runtime_config: SourceRuntimeConfigData) -> None:
        """Register one immediate ONCE job."""
        runtime_config_id = runtime_config.runtime_config_id
        job_id = self._build_once_job_id(runtime_config_id)

        if job_id in self._jobs:
            return

        self._scheduler.add_job(
            self._run_once_job,
            id=job_id,
            replace_existing=False,
            args=[runtime_config],
        )

        self._jobs[job_id] = ScheduledSourceJob(
            aps_job_id=job_id,
            status=JobStatus.SCHEDULED,
            runtime_configs=(runtime_config,),
        )

    def _register_polling_job(
        self,
        *,
        protocol: str,
        runtime_configs: tuple[SourceRuntimeConfigData, ...],
    ) -> None:
        """Register one long-running polling job for one protocol."""
        job_id = self._build_polling_job_id(protocol)
        if job_id in self._jobs:
            return

        stop_event = Event()
        self._scheduler.add_job(
            self._run_polling_job,
            id=job_id,
            replace_existing=False,
            args=[runtime_configs, stop_event],
        )

        self._jobs[job_id] = ScheduledSourceJob(
            runtime_configs=runtime_configs,
            aps_job_id=job_id,
            status=JobStatus.SCHEDULED,
            stop_event=stop_event,
        )

    def _register_subscription_job(
        self,
        *,
        protocol: str,
        runtime_configs: tuple[SourceRuntimeConfigData, ...],
    ) -> None:
        """Register one merged long-running subscription job."""
        job_id = self._build_subscription_job_id(protocol)
        if job_id in self._jobs:
            return

        stop_event = Event()
        self._scheduler.add_job(
            self._run_subscription_job,
            id=job_id,
            replace_existing=False,
            args=[runtime_configs, stop_event],
        )

        self._jobs[job_id] = ScheduledSourceJob(
            runtime_configs=runtime_configs,
            aps_job_id=job_id,
            status=JobStatus.SCHEDULED,
            stop_event=stop_event,
        )

    def _run_once_job(self, runtime_config: SourceRuntimeConfigData) -> None:
        """Execute one ONCE job."""
        runtime_config_id = runtime_config.runtime_config_id
        job_id = self._build_once_job_id(runtime_config_id)
        runtime_job = self._jobs.get(job_id)

        if runtime_job is not None:
            runtime_job.status = JobStatus.RUNNING

        requests = [
            SourceAcquisitionRequest(
                request_id=request.request_id,
                task_id=request.task_id,
                execution=AcquisitionExecutionOptions(
                    protocol=request.execution.protocol,
                    transport=request.execution.transport,
                    acquisition_mode=request.execution.acquisition_mode,
                    interval_ms=request.execution.interval_ms,
                    max_iteration=1,
                    request_timeout_ms=request.execution.request_timeout_ms,
                    freshness_timeout_ms=request.execution.freshness_timeout_ms,
                    alive_timeout_ms=request.execution.alive_timeout_ms,
                ),
                connections=list(request.connections),
                items=list(request.items),
            )
            for request in self._plan_build_usecase.build_requests([runtime_config])
        ]
        results = asyncio.run(self._polling_usecase_factory().execute_once(requests[0]))
        if runtime_job is not None:
            runtime_job.last_result = results[0] if results else None

    def _run_polling_job(
        self,
        runtime_configs: tuple[SourceRuntimeConfigData, ...],
        stop_event: Event,
    ) -> None:
        """Start one merged long-running polling job."""
        first_config = runtime_configs[0]
        job_id = self._build_polling_job_id(first_config.protocol)
        runtime_job = self._jobs.get(job_id)

        if runtime_job is not None:
            runtime_job.status = JobStatus.RUNNING

        requests = self._plan_build_usecase.build_requests(list(runtime_configs))
        asyncio.run(self._run_polling_requests(requests, stop_event))
        if runtime_job is not None:
            runtime_job.status = JobStatus.STOPPED if stop_event.is_set() else JobStatus.FINISHED

    def _run_subscription_job(
        self,
        runtime_configs: tuple[SourceRuntimeConfigData, ...],
        stop_event: Event,
    ) -> None:
        """Start one merged long-running subscription job."""
        job_id = self._build_subscription_job_id(runtime_configs[0].protocol)
        runtime_job = self._jobs.get(job_id)

        if runtime_job is not None:
            runtime_job.status = JobStatus.RUNNING

        requests = self._plan_build_usecase.build_requests(list(runtime_configs))
        asyncio.run(self._run_subscription_requests(requests, stop_event))
        if runtime_job is not None:
            runtime_job.status = JobStatus.STOPPED if stop_event.is_set() else JobStatus.FINISHED

    async def _run_polling_requests(
        self,
        requests: list[SourceAcquisitionRequest],
        stop_event: Event,
    ) -> None:
        """并发启动多个 polling 聚合请求。"""

        async with asyncio.TaskGroup() as task_group:
            for request in requests:
                task_group.create_task(
                    self._polling_usecase_factory().execute(
                        request=request,
                        stop_event=stop_event,
                    )
                )

    async def _run_subscription_requests(
        self,
        requests: list[SourceAcquisitionRequest],
        stop_event: Event,
    ) -> None:
        """并发启动多个 subscription 聚合请求。"""

        async with asyncio.TaskGroup() as task_group:
            for request in requests:
                task_group.create_task(
                    self._subscribe_usecase_factory().execute(
                        request=request,
                        stop_event=stop_event,
                    )
                )

    def _on_job_executed_or_failed(self, event: JobExecutionEvent) -> None:
        """Handle APScheduler job completion events."""
        runtime_job = self._jobs.get(event.job_id)
        if runtime_job is None:
            return

        if runtime_job.status is JobStatus.STOPPED:
            return

        if event.exception is None and (
            runtime_job.last_result is None
            or runtime_job.last_result.status is not AcquisitionStatus.FAILED
        ):
            runtime_job.status = JobStatus.FINISHED
        else:
            runtime_job.status = JobStatus.FAILED

    def _clear_registered_jobs(self) -> None:
        """Remove all APScheduler jobs and clear runtime registry."""
        for runtime_job in self._jobs.values():
            if runtime_job.stop_event is not None:
                runtime_job.stop_event.set()

        for aps_job in self._scheduler.get_jobs():
            aps_job.remove()
        self._jobs.clear()

    @staticmethod
    def _build_once_job_id(runtime_config_id: int) -> str:
        """Build one stable job identifier for ONCE mode."""
        return f"once:{runtime_config_id}"

    @staticmethod
    def _build_polling_job_id(protocol: str) -> str:
        """Build one stable job identifier for a protocol-level polling job."""
        return f"polling:{protocol}"

    @staticmethod
    def _build_subscription_job_id(protocol: str) -> str:
        """Build one stable job identifier for a merged subscription protocol."""
        return f"subscription:{protocol}"

    @staticmethod
    def _get_acquisition_mode(runtime_config: SourceRuntimeConfigData) -> AcquisitionMode:
        """Extract acquisition mode from one runtime config."""
        try:
            return AcquisitionMode(runtime_config.acquisition_mode.upper())
        except ValueError as exc:
            raise ValueError(
                f"Unsupported acquisition mode: {runtime_config.acquisition_mode}"
            ) from exc
