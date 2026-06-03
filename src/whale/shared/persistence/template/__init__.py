"""共享持久化层模板导出边界.

这里导出协议参数模板、协议视图定义和样例数据入口，供初始化脚本、单测和
本地演示使用；不负责 ingest 生产路径装配。
"""

from whale.shared.persistence.template.protocol_param_data import ENDPOINT_PARAM_DEFS, SIGNAL_PARAM_DEFS
from whale.shared.persistence.template.protocol_view_defs import _PROTOCOL_VIEW_DEFS, ensure_protocol_views
from whale.shared.persistence.template.sample_data import PROTOCOL_SAMPLE_SPECS, generate_all_sample_data

__all__ = [
    "ENDPOINT_PARAM_DEFS",
    "SIGNAL_PARAM_DEFS",
    "_PROTOCOL_VIEW_DEFS",
    "ensure_protocol_views",
    "PROTOCOL_SAMPLE_SPECS",
    "generate_all_sample_data",
]
