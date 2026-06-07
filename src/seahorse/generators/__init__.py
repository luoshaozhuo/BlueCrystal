"""seahorse 生成器层 —— 告警与控制回写生成。

本层提供告警事件与控制回写响应的生成能力，
基于信号值序列或控制命令生成对应的结果对象。
所有生成器均不访问外部系统，输出纯内存数据结构。

安全边界：
- 不得 import whale.ingest。
- 不得访问生产数据库。
"""
from __future__ import annotations

from seahorse.generators.alarm_generator import (
    ALARM_TYPE_COMMUNICATION,
    ALARM_TYPE_DEVICE_STATE,
    ALARM_TYPE_QUALITY,
    ALARM_TYPE_THRESHOLD,
    AlarmGenerator,
)
from seahorse.generators.control_result_generator import (
    CONTROL_STATUS_ACCEPTED,
    CONTROL_STATUS_DRY_RUN_ACCEPTED,
    CONTROL_STATUS_READBACK_MATCHED,
    CONTROL_STATUS_READBACK_MISMATCH,
    CONTROL_STATUS_TIMEOUT,
    CONTROL_STATUS_UNSUPPORTED,
    CONTROL_STATUS_WRITE_DISABLED,
    ControlResultGenerator,
)

__all__ = [
    "ALARM_TYPE_THRESHOLD",
    "ALARM_TYPE_DEVICE_STATE",
    "ALARM_TYPE_COMMUNICATION",
    "ALARM_TYPE_QUALITY",
    "AlarmGenerator",
    "CONTROL_STATUS_ACCEPTED",
    "CONTROL_STATUS_WRITE_DISABLED",
    "CONTROL_STATUS_DRY_RUN_ACCEPTED",
    "CONTROL_STATUS_READBACK_MATCHED",
    "CONTROL_STATUS_READBACK_MISMATCH",
    "CONTROL_STATUS_TIMEOUT",
    "CONTROL_STATUS_UNSUPPORTED",
    "ControlResultGenerator",
]
