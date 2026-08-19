"""Observability 自动埋点与低侵入接入机制."""

from .apscheduler import (
    APSCHEDULER_OBSERVABILITY_EVENT_MASK,
    APSchedulerListener,
    create_apscheduler_listener,
    install_apscheduler_instrumentation,
    uninstall_apscheduler_instrumentation,
)
from .composite import CompositeInstrumentationHooks
from .fastapi import (
    ActorResolver,
    default_actor_resolver,
    install_fastapi_instrumentation,
)
from .hooks import InstrumentationHooks, NullInstrumentationHooks, safe_observe
from .task_scheduler import (
    ObservedTaskScheduler,
    TaskSchedulerLike,
    instrument_task_scheduler,
)
from .task_runner import ObservedTaskRunner, TaskRunner, instrument_task_runner

__all__ = [
    "APSCHEDULER_OBSERVABILITY_EVENT_MASK",
    "APSchedulerListener",
    "ActorResolver",
    "CompositeInstrumentationHooks",
    "InstrumentationHooks",
    "NullInstrumentationHooks",
    "ObservedTaskRunner",
    "TaskRunner",
    "create_apscheduler_listener",
    "default_actor_resolver",
    "install_apscheduler_instrumentation",
    "install_fastapi_instrumentation",
    "instrument_task_runner",
    "instrument_task_scheduler",
    "ObservedTaskScheduler",
    "TaskSchedulerLike",
    "safe_observe",
    "uninstall_apscheduler_instrumentation",
]
