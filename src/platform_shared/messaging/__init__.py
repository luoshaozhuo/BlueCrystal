"""跨组件消息基础模型（骨架）。

提供 message envelope、correlation、schema_version 等跨组件消息抽象。
当前为最小骨架，后续按 PS-FR-005 补充具体模型定义。

不负责：Kafka/Pulsar 具体 adapter、消息路由、消息持久化。
具体 broker 适配仍归 whale.message_pipeline。
"""
