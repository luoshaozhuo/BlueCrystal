"""双节点写入冲突与 lease/fencing 并发语义测试。

使用 mock lease repository 验证两个 WorkerRuntime 节点
对同一 job 执行写入时的 lease 冲突行为。

验证场景：
1. 节点 A 获取 lease 后，节点 B 无法获取同一 lease
2. fencing token 不匹配时拒绝执行
3. lease 释放后另一节点可获取
4. 并发 lease 获取的原子性

证据等级：L2 (contract/stub)。
真实双 WorkerRuntime + DB lease E2E 需要多个进程和 PostgreSQL，
当前标记为 PENDING。
"""

from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest

from whale.ingest.runtime.worker_runtime import WorkerRuntime, WorkerRuntimeMetrics
from whale.ingest.runtime.modes import RuntimeMode
from whale.ingest.runtime.scheduler_settings import SchedulerSettings


class _StubLeaseService:
    """模拟 LeaseService，用于并发冲突测试。"""

    def __init__(self) -> None:
        self._leases: dict[str, dict[str, object]] = {}
        self._lock = threading.Lock()

    def acquire(
        self,
        *,
        lease_name: str,
        holder_key: str,
        ttl_seconds: int,
        now: object = None,
    ) -> bool:
        with self._lock:
            if lease_name in self._leases:
                existing = self._leases[lease_name]
                if existing["holder_key"] != holder_key:
                    return False
            self._leases[lease_name] = {
                "holder_key": holder_key,
                "ttl_seconds": ttl_seconds,
            }
            return True

    def renew(
        self,
        *,
        lease_name: str,
        holder_key: str,
        ttl_seconds: int,
        now: object = None,
    ) -> None:
        with self._lock:
            if lease_name not in self._leases:
                raise ValueError(f"lease {lease_name} not found")
            existing = self._leases[lease_name]
            if existing["holder_key"] != holder_key:
                raise ValueError(f"lease {lease_name} not owned by {holder_key}")
            existing["ttl_seconds"] = ttl_seconds

    def release(self, *, lease_name: str, holder_key: str) -> None:
        with self._lock:
            if lease_name in self._leases:
                existing = self._leases[lease_name]
                if existing["holder_key"] == holder_key:
                    del self._leases[lease_name]


class _StubFencingTokenRepository:
    """模拟 FencingTokenRepository。"""

    def __init__(self) -> None:
        self._tokens: dict[str, int] = {}
        self._counter = 0

    def generate(self, job_id: str) -> int:
        self._counter += 1
        self._tokens[job_id] = self._counter
        return self._counter

    def get(self, job_id: str) -> int:
        return self._tokens.get(job_id, 0)

    def validate(self, job_id: str, token: int) -> bool:
        current = self._tokens.get(job_id, 0)
        return current == token


class _TestMetrics(WorkerRuntimeMetrics):
    """暴露指标以便测试断言。"""

    def get(self, name: str) -> int:
        return self._counters.get(name, 0)


def _build_test_settings(node_key: str) -> SchedulerSettings:
    return SchedulerSettings(
        timezone="UTC",
        runtime_mode=RuntimeMode.STANDALONE,
        node_key=node_key,
        heartbeat_interval_seconds=3600,
        lease_ttl_seconds=30,
        pull_max_in_flight=1,
    )


def _build_test_worker(node_key: str, lease_service, metrics=None) -> WorkerRuntime:
    settings = _build_test_settings(node_key)
    return WorkerRuntime(
        settings=settings,
        node_repository=MagicMock(),
        job_repository=MagicMock(),
        assignment_repository=MagicMock(),
        lease_service=lease_service,
        fencing_token_repository=MagicMock(),
        metrics=metrics or _TestMetrics(),
        handlers={},
    )


class TestDualNodeWriteLeaseConflict:
    """双节点 lease 冲突语义测试。"""

    def test_second_node_cannot_acquire_same_lease(self) -> None:
        """节点 A 持有 lease 后，节点 B 应被拒绝。"""
        lease_svc = _StubLeaseService()
        # 节点 A 获取 lease
        assert lease_svc.acquire(lease_name="job:test-1", holder_key="node-A", ttl_seconds=30) is True
        # 节点 B 试图获取同一 lease — 应被拒绝
        assert lease_svc.acquire(lease_name="job:test-1", holder_key="node-B", ttl_seconds=30) is False

    def test_lease_release_allows_other_node(self) -> None:
        """释放 lease 后另一节点可以获取。"""
        lease_svc = _StubLeaseService()
        lease_svc.acquire(lease_name="job:test-2", holder_key="node-A", ttl_seconds=30)
        lease_svc.release(lease_name="job:test-2", holder_key="node-A")
        # 释放后节点 B 可以获取
        assert lease_svc.acquire(lease_name="job:test-2", holder_key="node-B", ttl_seconds=30) is True

    def test_fencing_token_prevents_stale_execution(self) -> None:
        """fencing token 不匹配时应拒绝执行。"""
        repo = _StubFencingTokenRepository()
        token_a = repo.generate("job-test-3")
        # 生成新 token 使旧 token 失效
        token_b = repo.generate("job-test-3")
        # 旧 token 不应通过验证
        assert repo.validate("job-test-3", token_a) is False
        # 新 token 应通过
        assert repo.validate("job-test-3", token_b) is True

    def test_lease_not_owned_cannot_renew(self) -> None:
        """不拥有 lease 时 renew 应抛出 ValueError。"""
        lease_svc = _StubLeaseService()
        lease_svc.acquire(lease_name="job:test-4", holder_key="node-A", ttl_seconds=30)
        with pytest.raises(ValueError):
            lease_svc.renew(lease_name="job:test-4", holder_key="node-B", ttl_seconds=30)

    def test_lease_not_found_cannot_renew(self) -> None:
        """lease 不存在时 renew 应抛出 ValueError。"""
        lease_svc = _StubLeaseService()
        with pytest.raises(ValueError):
            lease_svc.renew(lease_name="job:nonexistent", holder_key="node-A", ttl_seconds=30)

    def test_worker_skips_job_without_lease(self) -> None:
        """lease 不匹配时 _execute_one 应记录 JOB_SKIPPED_NO_LEASE。"""
        metrics = _TestMetrics()
        lease_svc = _StubLeaseService()
        worker = _build_test_worker("node-X", lease_svc, metrics)

        # 模拟 scheduler.validate_execution 返回 DENY
        mock_decision = MagicMock()
        mock_decision.allowed = False
        mock_decision.reason_code = "LEASE_NOT_OWNED"
        worker._scheduler.validate_execution = MagicMock(return_value=mock_decision)

        worker._execute_one(job_id="job-conflict", fencing_token=1, now=MagicMock())

        assert metrics.get("job_skipped_no_lease") >= 1

    def test_concurrent_lease_acquisition_atomic(self) -> None:
        """并发获取 lease 时只有一个赢家。"""
        lease_svc = _StubLeaseService()
        results: list[bool] = []

        def try_acquire(node: str) -> None:
            ok = lease_svc.acquire(lease_name="job:atomic", holder_key=node, ttl_seconds=30)
            results.append(ok)

        threads = [
            threading.Thread(target=try_acquire, args=("node-A",)),
            threading.Thread(target=try_acquire, args=("node-B",)),
            threading.Thread(target=try_acquire, args=("node-C",)),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 只有一个节点应成功获取 lease
        success_count = sum(1 for r in results if r)
        assert success_count == 1, (
            f"Dual-node write conflict: expected exactly 1 lease winner, "
            f"got {success_count}"
        )
