

from enum import StrEnum, auto

import pandas as pd


class ServerStatus(StrEnum):
    CREATED = auto()       # 已创建，尚未初始化
    INITIALIZED = auto()   # 初始化完成
    STARTING = auto()      # 正在启动
    RUNNING = auto()       # 正常运行
    STOPPING = auto()      # 正在停止
    STOPPED = auto()       # 已停止
    FAILED = auto()        # 运行失败
        

class ServerDefinition:
    """服务器定义类。"""

    def __init__(
            self, 
            conn: pd.Series, 
            src_point_items_df: pd.DataFrame=None,
            sink_point_items_df: pd.DataFrame=None,
            ):
        self.conn = conn
        self.src_point_items_df = src_point_items_df
        self.sink_point_items_df = sink_point_items_df