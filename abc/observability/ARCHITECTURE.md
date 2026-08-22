# Observability Architecture

## Responsibilities

context
- ObservationContext
- propagation
- baggage boundary

trace
- span creation
- sampling
- error tracing

metrics
- metric definition
- registry management

logs
- structured logging

audit
- business audit records

status
- runtime current state

instrumentation
- third-party framework adapters only

lifecycle
- resource startup and shutdown

bootstrap
- unified assembly entry point


## Runtime lifecycle

Application
    |
    v
ObservabilityBootstrap
    |
    v
ObservabilityManager
    |
    +-- Context
    +-- Trace
    +-- Metrics
    +-- Logs
    +-- Audit
    +-- Instrumentation


## Propagation model

HTTP
 |
OpenTelemetry Context
 |
Baggage
 |
ObservationContext
 |
Scheduler
 |
Async Task
 |
Worker
