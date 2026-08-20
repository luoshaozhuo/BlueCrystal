"""Scheduler Prometheus Metrics。"""

from prometheus_client import Counter, Gauge


SCHEDULER_RUNNING = Gauge(
    "scheduler_running",
    "Whether the scheduler is running",
    namespace="bluecrystal",
)
TASK_MISFIRES = Counter(
    "task_misfires",
    "Number of task misfires",
    namespace="bluecrystal",
)
TASK_MAX_INSTANCE_SKIPS = Counter(
    "task_max_instance_skips",
    "Number of task runs skipped by max_instances",
    namespace="bluecrystal",
)
SCHEDULER_TASK_OPERATIONS = Counter(
    "scheduler_task_operations",
    "Number of scheduler task management operations",
    ["operation"],
    namespace="bluecrystal",
)
