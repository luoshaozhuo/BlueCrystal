"""Turtle 审计治理基础能力。

提供全局审计治理模型、策略和端口，与各模块特定审计适配器协作。
ingest 保有自己的 audit adapter（db_audit_sink、http_audit_sink 等），
Turtle 的 audit 子包提供可复用的审计治理 Schema 和策略基础。
"""

__all__: list[str] = []

