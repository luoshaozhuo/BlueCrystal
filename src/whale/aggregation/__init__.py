"""数据聚合层（aggregation）—— 当前为骨架模块。

本包提供 ADS 聚合、周期性聚合和实时聚合逻辑。
当前状态：骨架（skeleton）。导入自 whale.models 的模型类尚未实现，
因此本模块无法独立导入运行。该能力属于远期 roadmap，不属于当前
ingest/message_pipeline/speed_layer/storage 生产链路。

不负责：
- 消息管道（由 message_pipeline 负责）
- 速度层消费调度（由 speed_layer 负责）
- 存储层写入（由 storage 负责）
"""

from whale.aggregation.ads import (
    aggregate_availability,
    aggregate_power_curve_deviation,
    load_power_curve,
)
from whale.aggregation.periodic import aggregate_periodic
from whale.aggregation.realtime import aggregate_realtime

__all__ = [
    "aggregate_availability",
    "aggregate_periodic",
    "aggregate_power_curve_deviation",
    "aggregate_realtime",
    "load_power_curve",
]
