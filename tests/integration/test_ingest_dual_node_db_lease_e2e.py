"""双节点实时数据库 lease 冲突 E2E 测试。

使用真实 SQLite 数据库（非 PostgreSQL）验证两个 WorkerRuntime 节点
对同一 resource 的 lease 获取/释放/fencing 语义。

验证场景：
1. 节点 A 获取 lease 后，节点 B 无法获取同一 resource 的 lease。
2. fencing token 不匹配时节点 B 被拒绝执行（OLD_PRIMARY_FENCED）。
3. 节点 A 释放 lease 后，节点 B 可重新获取。
4. 旧主（节点 A）释放后尝试用旧 fencing token 操作被拒绝。

测试阶段：模块集成期验证（simulator — 使用真实 DB 但单进程 SQLite，非 PostgreSQL 多进程）。
不能证明：
- 真实多进程跨节点并发行为（SQLite 不支持多写入并发）。
- 网络分区下的 lease 一致性。
- PostgreSQL 下的行锁和 MVCC 行为。

要真正验证多进程场景，需要 PostgreSQL 和多个独立进程。
"""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, datetime

import pytest
from sqlalchemy.engine import Engine

from whale.ingest.framework.persistence import (
    create_runtime_engine,
    create_runtime_session_factory,
    initialize_runtime_database,
    migrate_runtime_database,
)
from whale.ingest.runtime.fencing import FencingTokenRepository
from whale.ingest.runtime.lease import LeaseService
from whale.shared.persistence.orm.ingest_runtime import IngestFencingToken, IngestJobLease

PG_DSN_ENV = "WHALE_INGEST_TEST_PG_DSN"


def _build_lease_service(db_url: str) -> LeaseService:
    """构建一个 LeaseService 实例，模拟一个独立节点。

    Args:
        db_url: 数据库连接 URL。

    Returns:
        已初始化的 LeaseService 实例。
    """
    engine = create_runtime_engine(db_url)
    initialize_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)
    return LeaseService(session_factory, FencingTokenRepository(session_factory))


def _pg_dsn() -> str:
    dsn = os.environ.get(PG_DSN_ENV)
    if not dsn:
        pytest.skip(f"{PG_DSN_ENV} not set; PostgreSQL multi-process lease validation remains pending")
    return dsn


def _build_pg_lease_service(db_url: str) -> tuple[LeaseService, Engine]:
    engine = create_runtime_engine(db_url)
    migrate_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)
    return LeaseService(session_factory, FencingTokenRepository(session_factory)), engine


def _reset_pg_lease_tables(db_url: str) -> None:
    """清空 PG 租约表以便测试隔离。

    确保在查询前已执行 Alembic migration（防御性检查）。
    """
    engine = create_runtime_engine(db_url)
    migrate_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)
    session = session_factory()
    try:
        session.query(IngestJobLease).delete()
        session.query(IngestFencingToken).delete()
        session.commit()
    finally:
        session.close()
        engine.dispose()


def _acquire_pg_lease_once(
    db_url: str,
    lease_name: str,
    holder_key: str,
    *,
    ttl_seconds: int = 30,
) -> dict[str, object]:
    service, engine = _build_pg_lease_service(db_url)
    try:
        result = service.acquire(
            lease_name=lease_name,
            lease_scope="write",
            resource_id=lease_name,
            holder_key=holder_key,
            ttl_seconds=ttl_seconds,
        )
        return {
            "acquired": result.acquired,
            "holder_key": result.holder_key,
            "fencing_token": result.fencing_token,
            "reason": result.reason,
        }
    finally:
        engine.dispose()


def _release_pg_lease_once(db_url: str, lease_name: str, holder_key: str) -> dict[str, object]:
    service, engine = _build_pg_lease_service(db_url)
    try:
        lease = service.release(lease_name=lease_name, holder_key=holder_key)
        return {"status": lease.status, "holder_key": lease.holder_key}
    finally:
        engine.dispose()


def _validate_pg_execution_once(
    db_url: str,
    lease_name: str,
    holder_key: str,
    fencing_token: int,
) -> bool:
    service, engine = _build_pg_lease_service(db_url)
    try:
        return service.validate_execution(
            lease_name=lease_name,
            holder_key=holder_key,
            fencing_token=fencing_token,
        )
    finally:
        engine.dispose()


def _force_expire_pg_lease_once(db_url: str, lease_name: str, *, now: datetime) -> None:
    service, engine = _build_pg_lease_service(db_url)
    try:
        service.force_expire(lease_name=lease_name, now=now)
    finally:
        engine.dispose()


class TestDualNodeDbLeaseConflict:
    """双节点真实 DB lease 冲突 E2E 测试。

    使用共享 SQLite 数据库模拟两个节点对同一 lease 的并发竞争。
    两个 LeaseService 实例共享同一数据库文件，通过 DB 行锁模拟节点间冲突。
    """

    def test_node_b_cannot_acquire_same_lease(self, tmp_path) -> None:
        """节点 A 持有 lease 后，节点 B 无法获取同一 lease。

        从节点 A 的 LeaseService 获取 lease，然后用节点 B 的
        LeaseService 尝试获取同一 lease——应返回 LEASE_CONFLICT。
        """
        db_path = tmp_path / "dual-node-1.sqlite"
        db_url = f"sqlite:///{db_path}"

        node_a = _build_lease_service(db_url)
        node_b = _build_lease_service(db_url)

        # 节点 A 获取 lease
        result_a = node_a.acquire(
            lease_name="write:resource-1",
            lease_scope="write",
            resource_id="resource-1",
            holder_key="node-A-primary",
            ttl_seconds=30,
        )
        assert result_a.acquired is True, f"节点 A 应成功获取 lease: {result_a.reason}"
        token_a = result_a.fencing_token
        assert token_a > 0

        # 节点 B 尝试获取同一 lease — 应被拒绝
        result_b = node_b.acquire(
            lease_name="write:resource-1",
            lease_scope="write",
            resource_id="resource-1",
            holder_key="node-B-standby",
            ttl_seconds=30,
        )
        assert result_b.acquired is False, "节点 B 不应能获取已被节点 A 持有的 lease"
        assert result_b.reason == "LEASE_CONFLICT"

        # 清理：节点 A 释放 lease
        node_a.release(lease_name="write:resource-1", holder_key="node-A-primary")

    def test_fencing_token_mismatch_rejected(self, tmp_path) -> None:
        """fencing token 不匹配时应拒绝执行。

        节点 A 获取 lease 得到 token=1，节点 A 释放后节点 B 获取
        同一 lease 得到 token=2（FencingTokenRepository 自增）。
        节点 A 用旧 token=1 验证时应被拒绝。
        """
        db_path = tmp_path / "dual-node-2.sqlite"
        db_url = f"sqlite:///{db_path}"

        node_a = _build_lease_service(db_url)
        node_b = _build_lease_service(db_url)

        # 节点 A 获取 lease
        result_a = node_a.acquire(
            lease_name="write:resource-2",
            lease_scope="write",
            resource_id="resource-2",
            holder_key="node-A",
            ttl_seconds=30,
        )
        assert result_a.acquired is True
        token_a = result_a.fencing_token

        # 节点 A 释放 lease
        node_a.release(lease_name="write:resource-2", holder_key="node-A")

        # 节点 B 获取同一 lease（新的 fencing token）
        result_b = node_b.acquire(
            lease_name="write:resource-2",
            lease_scope="write",
            resource_id="resource-2",
            holder_key="node-B",
            ttl_seconds=30,
        )
        assert result_b.acquired is True
        token_b = result_b.fencing_token
        assert token_b != token_a, f"fencing token 应递增: old={token_a}, new={token_b}"

        # 节点 A 用旧 token 验证 — 应失败
        valid = node_a.validate_execution(
            lease_name="write:resource-2",
            holder_key="node-A",
            fencing_token=token_a,
        )
        assert valid is False, "旧 fencing token 不应通过验证"

        # 节点 B 用当前 token 验证 — 应通过
        valid_b = node_b.validate_execution(
            lease_name="write:resource-2",
            holder_key="node-B",
            fencing_token=token_b,
        )
        assert valid_b is True, "当前 fencing token 应通过验证"

        # 清理
        node_b.release(lease_name="write:resource-2", holder_key="node-B")

    def test_release_then_reacquire_by_other_node(self, tmp_path) -> None:
        """节点 A 释放 lease 后，节点 B 可重新获取。

        验证 lease 释放后的可重获性和 fencing token 正确递增。
        """
        db_path = tmp_path / "dual-node-3.sqlite"
        db_url = f"sqlite:///{db_path}"

        node_a = _build_lease_service(db_url)
        node_b = _build_lease_service(db_url)

        # 节点 A 获取并释放 lease
        result_a = node_a.acquire(
            lease_name="write:resource-3",
            lease_scope="write",
            resource_id="resource-3",
            holder_key="node-A",
            ttl_seconds=30,
        )
        assert result_a.acquired is True
        node_a.release(lease_name="write:resource-3", holder_key="node-A")

        # 释放后节点 B 可获取
        result_b = node_b.acquire(
            lease_name="write:resource-3",
            lease_scope="write",
            resource_id="resource-3",
            holder_key="node-B",
            ttl_seconds=30,
        )
        assert result_b.acquired is True, "释放后另一节点应能获取 lease"
        assert result_b.fencing_token > result_a.fencing_token, "fencing token 应递增"

        # 验证节点 B 的 lease 有效
        valid = node_b.validate_execution(
            lease_name="write:resource-3",
            holder_key="node-B",
            fencing_token=result_b.fencing_token,
        )
        assert valid is True

        # 清理
        node_b.release(lease_name="write:resource-3", holder_key="node-B")

    def test_old_primary_fenced_after_release(self, tmp_path) -> None:
        """旧主释放 lease 后尝试用旧 fencing token 操作应被拒绝。

        模拟旧主故障恢复后使用过期 fencing token 的场景。
        """
        db_path = tmp_path / "dual-node-4.sqlite"
        db_url = f"sqlite:///{db_path}"

        node_a = _build_lease_service(db_url)
        node_b = _build_lease_service(db_url)

        # 节点 A（旧主）获取 lease
        result_a = node_a.acquire(
            lease_name="write:resource-4",
            lease_scope="write",
            resource_id="resource-4",
            holder_key="node-A-old-primary",
            ttl_seconds=30,
        )
        assert result_a.acquired is True
        token_old = result_a.fencing_token

        # 节点 A 释放 lease
        node_a.release(lease_name="write:resource-4", holder_key="node-A-old-primary")

        # 节点 B（新主）获取 lease
        result_b = node_b.acquire(
            lease_name="write:resource-4",
            lease_scope="write",
            resource_id="resource-4",
            holder_key="node-B-new-primary",
            ttl_seconds=30,
        )
        assert result_b.acquired is True

        # 旧主尝试用旧 token 验证 — 应失败
        valid_old = node_a.validate_execution(
            lease_name="write:resource-4",
            holder_key="node-A-old-primary",
            fencing_token=token_old,
        )
        assert valid_old is False, "旧主用旧 fencing token 应被 fenced"

        # 新主 lease 仍然有效
        valid_new = node_b.validate_execution(
            lease_name="write:resource-4",
            holder_key="node-B-new-primary",
            fencing_token=result_b.fencing_token,
        )
        assert valid_new is True

        # 清理
        node_b.release(lease_name="write:resource-4", holder_key="node-B-new-primary")

    def test_different_resources_do_not_conflict(self, tmp_path) -> None:
        """不同 resource 的 lease 应互不冲突。

        验证 lease 隔离正确：resource-A 的 lease 不影响 resource-B。
        """
        db_path = tmp_path / "dual-node-5.sqlite"
        db_url = f"sqlite:///{db_path}"

        node_a = _build_lease_service(db_url)
        node_b = _build_lease_service(db_url)

        # 节点 A 获取 resource-A 的 lease
        result_a = node_a.acquire(
            lease_name="write:resource-A",
            lease_scope="write",
            resource_id="resource-A",
            holder_key="node-A",
            ttl_seconds=30,
        )
        assert result_a.acquired is True

        # 节点 B 获取 resource-B 的 lease — 应成功
        result_b = node_b.acquire(
            lease_name="write:resource-B",
            lease_scope="write",
            resource_id="resource-B",
            holder_key="node-B",
            ttl_seconds=30,
        )
        assert result_b.acquired is True, (
            f"不同 resource 的 lease 不应冲突: reason={result_b.reason}"
        )

        # 清理
        node_a.release(lease_name="write:resource-A", holder_key="node-A")
        node_b.release(lease_name="write:resource-B", holder_key="node-B")

    def test_expired_lease_can_be_acquired(self, tmp_path) -> None:
        """过期 lease 可由另一节点获取。

        模拟节点 A 的 lease 过期后，节点 B 可以获取同一 resource 的 lease。
        """
        db_path = tmp_path / "dual-node-6.sqlite"
        db_url = f"sqlite:///{db_path}"

        node_a = _build_lease_service(db_url)

        # 节点 A 获取短期 lease（1 秒 TTL）
        now = datetime(2026, 5, 29, 10, 0, 0, tzinfo=UTC)
        result_a = node_a.acquire(
            lease_name="write:resource-6",
            lease_scope="write",
            resource_id="resource-6",
            holder_key="node-A",
            ttl_seconds=1,
            now=now,
        )
        assert result_a.acquired is True

        # 强制过期
        expired_count = node_a.expire_due_leases(now=datetime(2026, 5, 29, 10, 0, 5, tzinfo=UTC))
        assert expired_count >= 1, f"应有至少 1 个过期 lease，实际：{expired_count}"

        # 节点 B 可以获取已过期的 lease
        result_b = node_a.acquire(
            lease_name="write:resource-6",
            lease_scope="write",
            resource_id="resource-6",
            holder_key="node-B",
            ttl_seconds=30,
            now=datetime(2026, 5, 29, 10, 0, 5, tzinfo=UTC),
        )
        assert result_b.acquired is True, "过期 lease 可由另一节点获取"

        # 验证节点 B 的 token 比节点 A 的 token 大
        assert result_b.fencing_token > result_a.fencing_token

        # 清理
        node_a.release(lease_name="write:resource-6", holder_key="node-B")

    def test_same_holder_can_reacquire_own_lease(self, tmp_path) -> None:
        """同一 holder 重新获取自己的 lease 应成功（幂等 acquire）。

        模拟节点 A 重复调用 acquire 的场景——应视为 renew 而非冲突。
        """
        db_path = tmp_path / "dual-node-7.sqlite"
        db_url = f"sqlite:///{db_path}"

        node_a = _build_lease_service(db_url)

        # 第一次获取
        result_1 = node_a.acquire(
            lease_name="write:resource-7",
            lease_scope="write",
            resource_id="resource-7",
            holder_key="node-A",
            ttl_seconds=30,
        )
        assert result_1.acquired is True
        _token_1 = result_1.fencing_token

        # 同一节点再次获取 — 应成功（renew 语义）
        result_2 = node_a.acquire(
            lease_name="write:resource-7",
            lease_scope="write",
            resource_id="resource-7",
            holder_key="node-A",
            ttl_seconds=30,
        )
        assert result_2.acquired is True, "同一 holder 应能 re-acquire 自己的 lease"

        # 清理
        node_a.release(lease_name="write:resource-7", holder_key="node-A")


@pytest.mark.integration
class TestPostgresDualProcessWriteLease:
    """PostgreSQL 双进程租约与 fencing 验证。

    测试阶段：
    - 这些用例在具备 ``WHALE_INGEST_TEST_PG_DSN`` 时提供跨模块联调期验证 风格的真实 PostgreSQL 多进程验证。
    - 若环境变量缺失则按 MISSING_ENVIRONMENT 跳过，不得视为通过。
    - 网络分区与旧主恢复全链路仍需额外 fault injection，不能仅凭本文件收口。
    """

    def setup_method(self) -> None:
        _reset_pg_lease_tables(_pg_dsn())

    def test_same_resource_concurrent_acquire_has_single_winner(self) -> None:
        """同一 resource 并发 acquire 时只能有一个进程获胜。"""
        dsn = _pg_dsn()
        lease_name = "write:pg-dual-node-1"

        with ProcessPoolExecutor(max_workers=2) as executor:
            future_a = executor.submit(_acquire_pg_lease_once, dsn, lease_name, "node-A")
            future_b = executor.submit(_acquire_pg_lease_once, dsn, lease_name, "node-B")
            result_a = future_a.result(timeout=20)
            result_b = future_b.result(timeout=20)

        acquired_count = int(bool(result_a["acquired"])) + int(bool(result_b["acquired"]))
        assert acquired_count == 1, f"expected single winner, got {result_a=} {result_b=}"
        loser = result_b if result_a["acquired"] else result_a
        winner = result_a if result_a["acquired"] else result_b
        assert loser["reason"] == "LEASE_CONFLICT", f"expected LEASE_CONFLICT, got {loser=}"
        assert int(winner["fencing_token"]) >= 1

    def test_old_primary_token_rejected_after_force_expire_and_takeover(self) -> None:
        """lease 过期并被新主接管后，旧 fencing token 必须失效。"""
        dsn = _pg_dsn()
        lease_name = "write:pg-dual-node-2"

        first = _acquire_pg_lease_once(dsn, lease_name, "node-A", ttl_seconds=1)
        assert first["acquired"] is True

        _force_expire_pg_lease_once(
            dsn,
            lease_name,
            now=datetime(2026, 5, 30, 12, 0, 5, tzinfo=UTC),
        )

        second = _acquire_pg_lease_once(dsn, lease_name, "node-B", ttl_seconds=30)
        assert second["acquired"] is True
        assert int(second["fencing_token"]) > int(first["fencing_token"])

        old_valid = _validate_pg_execution_once(
            dsn,
            lease_name,
            "node-A",
            int(first["fencing_token"]),
        )
        new_valid = _validate_pg_execution_once(
            dsn,
            lease_name,
            "node-B",
            int(second["fencing_token"]),
        )
        assert old_valid is False
        assert new_valid is True

    def test_release_allows_new_primary_takeover(self) -> None:
        """旧主持有者 release 后，新主进程应能接管。"""
        dsn = _pg_dsn()
        lease_name = "write:pg-dual-node-3"

        first = _acquire_pg_lease_once(dsn, lease_name, "node-A", ttl_seconds=30)
        assert first["acquired"] is True

        released = _release_pg_lease_once(dsn, lease_name, "node-A")
        assert released["status"] == "RELEASED"

        second = _acquire_pg_lease_once(dsn, lease_name, "node-B", ttl_seconds=30)
        assert second["acquired"] is True
        assert int(second["fencing_token"]) > int(first["fencing_token"])

    def test_db_unavailable_fails_safe_instead_of_silent_success(self) -> None:
        """数据库不可达时 acquire 必须显式失败，不能静默成功。"""
        bad_dsn = "postgresql+psycopg://whale:whale@127.0.0.1:1/nonexistent_round11"
        with pytest.raises(Exception):
            _acquire_pg_lease_once(bad_dsn, "write:pg-db-down", "node-A")
