

from enum import StrEnum, auto
import pandas as pd
from dataclasses import dataclass


class ServerStatus(StrEnum):
    NOT_CREATED = auto()       # 未创建
    CREATED = auto()       # 已创建，尚未初始化
    INITIALIZED = auto()   # 初始化完成
    STARTING = auto()      # 正在启动
    RUNNING = auto()       # 正常运行
    STOPPING = auto()      # 正在停止
    STOPPED = auto()       # 已停止
    FAILED = auto()        # 运行失败
        

@dataclass(slots=True, kw_only=True, eq=False)
class ServerDefinition:
    """所有协议 Server 的公共定义。"""

    conn: pd.Series
    src_point_items_df: pd.DataFrame
    sink_point_items_df: pd.DataFrame

    def __post_init__(self) -> None:
        if self.src_point_items_df.empty and self.sink_point_items_df.empty:
            raise ValueError(
                f"connection_id={self.conn['connection_id']} 未定义任何点位"
            )
