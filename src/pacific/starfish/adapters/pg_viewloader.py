
from sqlalchemy import create_engine
import os
import pandas as pd


from dataclasses import fields

from pacific.starfish.core.entities import EntityBase



_ENGINE = create_engine(os.environ.get("WHALE_DB_URL"))

class PGViewLoader():
    """数据库视图加载器契约。"""

    def load(
            self,
            entity: EntityBase, 
            _equ: dict[str, object]=None, 
            _in: dict[str, object]=None, 
            limit: int | None = 100000
            ) -> pd.DataFrame:
        """加载指定名称的数据库视图。
        Args:
            view_name: 数据库视图名称。
            _equ: 等值条件字典。
            _in: 范围条件字典。
            limit: 查询结果限制。

        Returns:
            pd.DataFrame: 包含视图数据的 DataFrame。
        """
        var_names = {i.name for i in fields(entity)} - {"view_name"}
        query = f"SELECT {', '.join(var_names)} FROM {entity.view_name}"
        if _equ:
            conditions = " AND ".join(f"{k} = '{v}'" for k, v in _equ.items())
            query += f" WHERE {conditions}"
        elif _in:
            conditions = " AND ".join(f"{k} IN ({', '.join(map(str, v))})" for k, v in _in.items())
            query += f" WHERE {conditions}"

        if limit is not None:
            query += f" LIMIT {limit}"

        return pd.read_sql(query, _ENGINE)

