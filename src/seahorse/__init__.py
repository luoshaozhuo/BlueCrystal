"""seahorse — 样例场站生成器。

seahorse 是 Whale 平台的模拟场景生成组件，负责根据场景配置生成确定性
的种子计划（seed plan）、信号值序列、告警事件与控制回写结果。

架构分层：
- reference_data: 协议参数模板、样例数据与视图定义，供 Navicat、单测和演示使用。
- models: 场景配置、元数据、种子计划、端点规划等核心数据结构。
- ports: 生成策略、导出器等抽象接口，定义后续扩展边界。
- orchestration: 场景生成编排器，串联配置解析、策略调用与计划装配。
- exporters: 导出能力预留（本轮不实现具体导出逻辑）。

安全边界：
- seahorse 不进入 whale.ingest 生产运行路径。
- seahorse 不得 import whale.ingest。
- seahorse/reference_data 不得依赖 whale ingest runtime。
"""

from __future__ import annotations
