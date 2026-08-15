"""Fencing token 辅助模块。提供防脑裂的 fencing token 生成和验证能力。

并发安全性：next_value 使用 INSERT ... ON CONFLICT DO UPDATE ... RETURNING 实现原子递增，
避免双节点同时获取 fencing token 时的 IntegrityError 竞态条件。
PostgreSQL 9.5+ 和 SQLite 3.35+ 均支持该语句。
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Callable

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from pacific.whale.shared.persistence.orm import IngestFencingToken


@dataclass(frozen=True, slots=True)
class FencingToken:
    """一个单调增长的 fencing token 快照。持有 token 名称和当前递增值。

    Attributes:
        token_name: 令牌名称，对应被保护的资源标识（如 write:resource-1）。
        value: 当前递增后的 token 值，供调用方用于后续验证和防脑裂判断。
    """

    token_name: str
    value: int


class FencingTokenRepository:
    """将单调递增的 fencing token 持久化到运行时数据库。

    使用原子 INSERT ... ON CONFLICT DO UPDATE ... RETURNING 保证并发安全，
    无论行是否存在，均在单次原子语句中完成递增并返回新值。
    不再依赖先 UPDATE 再 INSERT 的两步流程，避免 TOCTOU 和 IntegrityError 竞态条件。

    关键操作：
    - next_value(token_name): 原子递增并返回新值。首次调用时自动创建行并设 current_value=1。
    - current_value(token_name): 只读当前值，不修改。行不存在时返回 value=0。

    Args:
        session_factory: 可调用对象，返回 SQLAlchemy Session，由调用方管理连接生命周期。
    """

    def __init__(self, session_factory: sessionmaker[Session] | Callable[[], Session]) -> None:
        """初始化 fencing token 仓库。

        Args:
            session_factory: 数据库会话工厂，每次调用返回独立 Session。
        """
        self._session_factory = session_factory

    def next_value(self, token_name: str) -> FencingToken:
        """原子递增 fencing token 并返回新值。

        使用单条 INSERT ... ON CONFLICT DO UPDATE ... RETURNING 实现原子递增，
        彻底消除双节点并发获取同一 token_name 时的 INSERT IntegrityError 竞态条件。

        并发行为：
        - 行不存在：INSERT current_value=1，RETURNING 返回 (token_name, 1)。
        - 行已存在：ON CONFLICT 触发 DO UPDATE SET current_value = current_value + 1，
          RETURNING 返回递增后的值。
        - 两个并发调用在 PostgreSQL 下由行锁串行化；在 SQLite WAL 模式下也保证串行写入。

        该语句仅依赖标准 SQL 的 ON CONFLICT 和 RETURNING 子句，不要求额外 schema 或迁移。

        Args:
            token_name: 要递增的 fencing token 名称。

        Returns:
            包含 token_name 和递增后 value 的 FencingToken 快照。

        Raises:
            AssertionError: 如果 RETURNING 未返回行，通常表示 schema 不一致或数据库不支持。
        """
        session = self._session_factory()
        try:
            result = session.execute(
                text(
                    "INSERT INTO ingest_fencing_token (token_name, current_value) "
                    "VALUES (:name, 1) "
                    "ON CONFLICT (token_name) DO UPDATE "
                    "SET current_value = ingest_fencing_token.current_value + 1 "
                    "RETURNING token_name, current_value"
                ),
                {"name": token_name},
            )
            row = result.fetchone()
            assert row is not None, (
                f"UPSERT fence token {token_name}: RETURNING 未返回行，"
                f"可能为 schema 不一致或数据库不支持 ON CONFLICT / RETURNING"
            )
            session.commit()
            return FencingToken(token_name=row[0], value=row[1])
        finally:
            session.close()

    def current_value(self, token_name: str) -> FencingToken:
        """读取指定名称的 fencing token 当前值，不执行递增。

        纯只读操作，不修改数据库行。行不存在时返回 value=0。

        Args:
            token_name: 要查询的 fencing token 名称。

        Returns:
            FencingToken 快照。若行不存在则 value=0。
        """
        session = self._session_factory()
        try:
            row = session.get(IngestFencingToken, token_name)
            if row is None:
                return FencingToken(token_name=token_name, value=0)
            return FencingToken(token_name=row.token_name, value=row.current_value)
        finally:
            session.close()


def redact_fencing_token(token: int | None) -> str | None:
    """返回 fencing token 的稳定脱敏摘要字符串，用于审计输出。"""

    if token is None:
        return None
    return sha256(str(token).encode("utf-8")).hexdigest()[:16]
