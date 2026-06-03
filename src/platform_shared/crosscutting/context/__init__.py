"""Tracing 和 correlation context 基础模型（骨架）。

提供跨组件的 trace_id、span_id、correlation_id 和 causation_id 等上下文传播基础。
当前为最小骨架，后续按 PS-FR-001 补充 context propagation 辅助工具。

不负责：具体 tracing backend（如 OpenTelemetry）、采样策略、审计上下文。
"""
