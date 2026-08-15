"""seahorse — 样例场站生成器。

seahorse 是 BlueCrystal 平台的模拟场景生成组件，负责根据场景配置生成确定性
的种子计划（seed plan）、信号值序列、告警事件与控制回写结果。

架构分层（Clean Architecture application_profile）：

- ``seahorse.domain`` —— 场景、计划、生成结果、bundle 等纯领域模型。
- ``seahorse.application`` —— 用例编排、端口契约、运行时状态骨架。
- ``seahorse.adapters`` —— CLI 入口、JSON / JSONL 序列化、handoff gateway。
- ``seahorse.infrastructure`` —— 时钟、调度器、driver backend、Whale 元数据仓储。
- ``seahorse.api`` —— 对外稳定 facade（``SeahorseFacade``）。

安全边界：

- seahorse 不进入 whale.ingest 生产运行路径。
- seahorse 不得 import whale.ingest。
- seahorse 不得 import starfish。
- ``seahorse.domain`` 与 ``seahorse.application`` 只依赖端口，不依赖
  adapters / infrastructure / api / starfish / whale.shared.persistence。
"""

from __future__ import annotations