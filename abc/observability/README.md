# Observability integration model

Application modules should use:

1. bootstrap ObservabilityManager
2. context propagation APIs
3. instrumentation registration
4. metrics registry
5. trace manager

Boundary propagation:

HTTP
 -> OTel Context
 -> Observation Context
 -> Scheduler
 -> Async Task
 -> Worker

Modules should not directly manage exporters or lifecycle resources.
