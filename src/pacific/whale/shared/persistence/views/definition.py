"""数据库 view 定义的通用数据结构。

本模块只提供 SELECT 与 DDL 文本渲染能力，不连接数据库、不持有 engine，
也不把 view 注册到 ORM metadata。
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.sql import Select


@dataclass(frozen=True)
class ViewDefinition:
    """数据库 view 的纯定义。

    Args:
        name: 数据库 view 名称。
        selectable: 用 SQLAlchemy Core 表达的 SELECT 查询。
    """

    name: str
    selectable: Select

    def select_sql(self, dialect: Dialect | None = None) -> str:
        """渲染带 literal 值的 SELECT SQL，供迁移脚本和兼容测试复用。"""

        compile_kwargs = {"literal_binds": True}
        if dialect is None:
            compiled = self.selectable.compile(compile_kwargs=compile_kwargs)
        else:
            compiled = self.selectable.compile(dialect=dialect, compile_kwargs=compile_kwargs)
        return str(compiled)

    def create_sql(self, dialect: Dialect | None = None) -> str:
        """渲染 CREATE VIEW DDL；执行时仍由 Alembic 控制事务和连接。"""

        return f"CREATE VIEW {self.name} AS\n{self.select_sql(dialect)}"

    def drop_sql(self) -> str:
        """渲染 DROP VIEW DDL；不使用 CASCADE 以兼容 SQLite 本地验证。"""

        return f"DROP VIEW IF EXISTS {self.name}"


__all__ = ["ViewDefinition"]
