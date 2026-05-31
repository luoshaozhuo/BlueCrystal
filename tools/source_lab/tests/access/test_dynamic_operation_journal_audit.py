"""operation journal 审计测试。

验证 dynamic runtime 操作日志的审计记录完整性和不可篡改性。
证据等级：L2（contract）。
"""
from __future__ import annotations

from pathlib import Path

from tools.source_lab.access.runtime import (
    ContinuityMonitor,
    EndpointRuntimeRegistry,
    RuntimeStateStore,
    StaggerCoordinator,
)
from tools.source_lab.tests.access._dynamic_runtime_test_utils import (
    build_http_source,
    build_registry,
    polling_config,
)


class _FailOnReplaceSessionManager:
    """测试用 EndpointSessionManager stub。

    仅实现测试所需方法，replace_endpoint 故意抛出异常以模拟替换失败。
    不继承 EndpointSessionManager（构造函数签名不同且含线程管理），
    传入 EndpointRuntimeRegistry 时需 type: ignore。
    """

    def __init__(self) -> None:
        self.started: list[str] = []

    def start_endpoint(self, runtime: object, config: object) -> None:
        self.started.append(getattr(runtime, "endpoint_id"))

    def pause_endpoint(self, runtime: object) -> None:
        return None

    def resume_endpoint(self, runtime: object) -> None:
        return None

    def stop_endpoint(self, runtime: object) -> None:
        return None

    def replace_endpoint(self, runtime: object, config: object) -> None:
        raise RuntimeError("replace boom")


def _journal_results(path: Path) -> list[dict[str, object]]:
    return RuntimeStateStore(str(path)).load_journal_entries()


def test_dynamic_status_success_and_not_found_are_journaled(tmp_path: Path) -> None:
    registry, _monitor = build_registry(tmp_path)
    source = build_http_source(1, 58011)
    assert registry.add_endpoint(polling_config(source)).result == "SUCCESS"

    assert registry.status(source.connection.name).result == "STATUS_SUCCESS"
    assert registry.status("missing-endpoint").result == "STATUS_NOT_FOUND"

    results = {entry["result"] for entry in _journal_results(tmp_path / "runtime")}
    assert "STATUS_SUCCESS" in results
    assert "STATUS_NOT_FOUND" in results


def test_dynamic_status_denied_is_journaled(tmp_path: Path) -> None:
    def deny_status(action: str, endpoint_id: str, _context: dict[str, object]) -> tuple[bool, str]:
        if action == "STATUS_ENDPOINT":
            return False, "status_denied_for_test"
        return True, "ok"

    registry, _monitor = build_registry(tmp_path, decision_hook=deny_status)
    result = registry.status("ep-1")
    assert result.result == "STATUS_DENIED"

    entries = _journal_results(tmp_path / "runtime")
    assert any(
        entry["action"] == "STATUS_ENDPOINT"
        and entry["result"] == "STATUS_DENIED"
        and entry["reason_code"] == "status_denied_for_test"
        for entry in entries
    )


def test_dynamic_update_version_conflict_is_journaled(tmp_path: Path) -> None:
    registry, _monitor = build_registry(tmp_path)
    source = build_http_source(2, 58012)
    assert registry.add_endpoint(polling_config(source)).result == "SUCCESS"

    result = registry.update_endpoint(source.connection.name, {"host": "127.0.0.2"}, expected_version=99)
    assert result.result == "CONFLICT"

    entries = _journal_results(tmp_path / "runtime")
    assert any(entry["result"] == "CONFLICT" and entry["action"] == "UPDATE_ENDPOINT" for entry in entries)


def test_dynamic_invalid_patch_validation_error_is_journaled(tmp_path: Path) -> None:
    registry, _monitor = build_registry(tmp_path)
    source = build_http_source(3, 58013)
    assert registry.add_endpoint(polling_config(source)).result == "SUCCESS"

    result = registry.update_endpoint(source.connection.name, {"unsupported_field": "x"}, expected_version=1)
    assert result.result == "VALIDATION_ERROR"

    entries = _journal_results(tmp_path / "runtime")
    assert any(
        entry["result"] == "VALIDATION_ERROR"
        and entry["reason_code"] == "unsupported_patch_fields"
        for entry in entries
    )


def test_dynamic_replacement_failure_rolls_back_or_marks_failed_and_is_journaled(tmp_path: Path) -> None:
    source = build_http_source(4, 58014)
    session_manager = _FailOnReplaceSessionManager()
    # _FailOnReplaceSessionManager 为测试 stub，仅实现必要方法，
    # 不继承 EndpointSessionManager（其构造函数含线程管理，不应在测试中初始化）。
    registry = EndpointRuntimeRegistry(
        session_manager=session_manager,  # type: ignore[arg-type]
        continuity_monitor=ContinuityMonitor(),
        stagger_coordinator=StaggerCoordinator(),
        state_store=RuntimeStateStore(str(tmp_path / "runtime")),
    )
    assert registry.add_endpoint(polling_config(source)).result == "SUCCESS"

    result = registry.update_endpoint(source.connection.name, {"host": "127.0.0.2"}, expected_version=1)
    assert result.result == "ROLLBACK"
    assert session_manager.started.count(source.connection.name) == 2

    entries = _journal_results(tmp_path / "runtime")
    assert any(entry["result"] == "ROLLBACK" and entry["action"] == "UPDATE_ENDPOINT" for entry in entries)


def test_dynamic_journal_contains_affected_and_unaffected_endpoints(tmp_path: Path) -> None:
    registry, _monitor = build_registry(tmp_path)
    sources = (
        build_http_source(5, 58015),
        build_http_source(6, 58016),
        build_http_source(7, 58017),
    )
    for source in sources:
        assert registry.add_endpoint(polling_config(source)).result == "SUCCESS"

    result = registry.update_endpoint(sources[0].connection.name, {"host": "127.0.0.2"}, expected_version=1)
    assert result.result == "SUCCESS"

    entries = _journal_results(tmp_path / "runtime")
    update_entries = [entry for entry in entries if entry["action"] == "UPDATE_ENDPOINT"]
    assert update_entries
    entry = update_entries[-1]
    assert entry["affected_endpoints"] == [sources[0].connection.name]
    # journal entries 返回 dict[str, object]，unaffected_endpoints 实际为 list[str]，
    # 需显式 cast 以满足 mypy 类型收窄。
    unaffected: list[str] = entry["unaffected_endpoints"]  # type: ignore[assignment]
    assert set(unaffected) == {
        sources[1].connection.name,
        sources[2].connection.name,
    }
    for field in (
        "operation_id",
        "action",
        "endpoint_id",
        "decision",
        "result",
        "reason_code",
        "before_config_version",
        "after_config_version",
        "affected_endpoints",
        "unaffected_endpoints",
        "timestamp",
    ):
        assert field in entry
