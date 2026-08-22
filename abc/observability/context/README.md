# Context propagation model

Execution boundaries:

HTTP
 -> OpenTelemetry Context
 -> ObservationContext
 -> Scheduler
 -> asyncio Task
 -> Worker

The context is captured at boundary creation and restored at execution.
