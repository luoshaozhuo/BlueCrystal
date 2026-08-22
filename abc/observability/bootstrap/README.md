# Observability bootstrap

Unified startup flow:

Config
 |
ObservabilityManager
 |
 +-- Logging
 +-- Metrics
 +-- Trace
 +-- Audit
 +-- Instrumentation
 +-- PropagationManager

Application modules should only depend on bootstrap entry points.
