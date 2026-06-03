"""数据处理层（processing）—— 当前为骨架模块。

本包提供数据清洗（cleaner）和数据标准化（normalizer）逻辑。
当前状态：骨架（skeleton）。导入自 whale.models 的模型类尚未实现，
因此本模块无法独立导入运行。该能力属于远期 roadmap，不属于当前
ingest/message_pipeline/speed_layer/storage 生产链路。

不负责：
- 消息管道（由 message_pipeline 负责）
- 存储层写入（由 storage 负责）
- 速度层消费调度（由 speed_layer 负责）
"""

from whale.processing.cleaner import PointCleaner
from whale.processing.normalizer import NormalizationError, normalize_batch

__all__ = ["NormalizationError", "PointCleaner", "normalize_batch"]
