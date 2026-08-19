"""Task Prometheus Metrics。"""
from prometheus_client import Counter, Gauge, Histogram
TASK_EXECUTIONS = Counter("task_executions", "Number of task executions", ["result"], namespace="bluecrystal")
TASK_EXECUTIONS_IN_FLIGHT = Gauge("task_executions_in_flight", "Current running task executions", namespace="bluecrystal")
TASK_EXECUTION_DURATION = Histogram("task_execution_duration_seconds", "Task execution duration", ["result"], namespace="bluecrystal")
