from __future__ import annotations

from typing import Protocol
import pandas as pd


class DBViewLoaderPort(Protocol):
    """数据库视图加载器契约。"""

    def load(self, view_name: str, _equ: dict[str, object]=None, _in: dict[str, object]=None) -> pd.DataFrame:
        """加载指定名称的数据库视图。

        Returns:
            pd.DataFrame: 包含视图数据的 DataFrame。
        """