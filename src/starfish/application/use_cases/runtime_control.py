"""Starfish runtime 控制用例。

本模块承接 ServerRegistry 纯化后移出的运行时执行职责。它可以编排
DriverPort 的 start/stop/read/write/health 调用、同步 DriverInstance 状态
并发出 runtime event；不创建 driver、不解析配置文件，也不触碰 native 或
协议 codec。
"""

from __future__ import annotations

from typing import Any, cast

from starfish.application.runtime import DriverInstance, DriverState, ServerRegistry
from starfish.domain import DriverEntry


def _mark_entry_running(registry: ServerRegistry, entry: DriverEntry) -> None:
    """将 entry 对应实例标记为 RUNNING。"""
    instance = registry.resolve_instance_for_entry(entry)
    if instance.state != DriverState.RUNNING:
        instance.mark_running()


def _mark_entry_stopped(registry: ServerRegistry, entry: DriverEntry) -> None:
    """将 entry 对应实例标记为 STOPPED。"""
    instance = registry.resolve_instance_for_entry(entry)
    if instance.state in {DriverState.RUNNING, DriverState.DEGRADED}:
        instance.mark_stopped()


def _emit_entry_event(
    registry: ServerRegistry,
    entry: DriverEntry,
    event_type: str,
    *,
    payload: dict[str, Any] | None = None,
) -> None:
    """按 entry 对应 DriverInstance 发出非侵入 runtime event。"""
    node, binding = registry.resolve_node_binding_for_entry(entry)
    binding.driver_instance.emit_runtime_event(
        event_type,
        node_id=node.node_id,
        payload=payload,
    )


def _record_entry_error(
    registry: ServerRegistry,
    entry: DriverEntry | None,
    message: str,
    *,
    payload: dict[str, Any] | None = None,
) -> None:
    """记录 entry 对应实例错误；找不到 entry 时不影响原主流程。"""
    if entry is None:
        return
    try:
        node, binding = registry.resolve_node_binding_for_entry(entry)
        binding.driver_instance.record_error(
            message,
            node_id=node.node_id,
            payload=payload,
        )
    except Exception:
        # 可观测记录失败不能改变 runtime 原有异常传播或停止清理语义。
        pass


class StartSystemUseCase:
    """启动全部可用 endpoint 的 runtime 控制用例。"""

    def execute(self, registry: ServerRegistry) -> list[DriverEntry]:
        """启动 registry 中所有可用 driver。

        Args:
            registry: 已构建 RuntimeGraph 的 registry 视图。

        Returns:
            已成功启动的 entry 列表，用于后续 stop 清理。

        Raises:
            RuntimeError: 任一 endpoint 启动失败时，停止已启动 entry 后抛出稳定错误。
        """
        started_entries: list[DriverEntry] = []
        current_entry: DriverEntry | None = None
        try:
            for current_entry in registry.entries:
                if not current_entry.available or current_entry.driver is None:
                    continue
                current_entry.driver.start()
                _mark_entry_running(registry, current_entry)
                _emit_entry_event(registry, current_entry, "START")
                started_entries.append(current_entry)
        except Exception as exc:
            _record_entry_error(
                registry,
                current_entry,
                str(exc),
                payload={"operation": "START"},
            )
            StopSystemUseCase().execute(registry, started_entries)
            endpoint_id = (
                current_entry.endpoint.endpoint_id if current_entry is not None else "unknown"
            )
            raise RuntimeError(f"启动 endpoint={endpoint_id} 失败: {exc}") from exc
        return started_entries


class StopSystemUseCase:
    """停止 endpoint 的 runtime 控制用例。"""

    def execute(
        self,
        registry: ServerRegistry,
        entries: list[DriverEntry] | None = None,
    ) -> None:
        """按反向顺序停止 entry，保持旧 manager 的清理语义。

        Args:
            registry: 已构建 RuntimeGraph 的 registry 视图。
            entries: 指定要停止的 entry；为 None 时停止全部已可用 entry。
        """
        target_entries = entries if entries is not None else registry.available_entries()
        for entry in reversed(target_entries):
            try:
                entry.driver.stop()
                _mark_entry_stopped(registry, entry)
                _emit_entry_event(registry, entry, "STOP")
            except Exception:
                _record_entry_error(
                    registry,
                    entry,
                    "stop failed",
                    payload={"operation": "STOP"},
                )
                continue


class HealthSystemUseCase:
    """聚合 endpoint 健康状态的 runtime 控制用例。"""

    def execute(
        self,
        registry: ServerRegistry,
        *,
        endpoint_id: str | None = None,
    ) -> dict[str, Any]:
        """返回 endpoint 健康信息。

        Args:
            registry: 已构建 RuntimeGraph 的 registry 视图。
            endpoint_id: 指定 endpoint 时仅查询该 driver；为 None 时返回聚合映射。

        Returns:
            单 endpoint 健康信息或 endpoint_id 到健康信息的映射。
        """
        if endpoint_id is not None:
            return cast("dict[str, Any]", registry.resolve_entry(endpoint_id).driver.health())

        result: dict[str, Any] = {}
        for entry in registry.entries:
            ep_id = entry.endpoint.endpoint_id or entry.endpoint.endpoint_name or "unknown"
            if entry.driver is not None and entry.available:
                result[ep_id] = entry.driver.health()
            else:
                result[ep_id] = {
                    "status": "unavailable",
                    "reason": entry.reason or "NOT_IMPLEMENTED",
                }
        return result


class ReadSystemUseCase:
    """读取 endpoint 点位值的 runtime 控制用例。"""

    def execute(
        self,
        registry: ServerRegistry,
        point_ids: list[str] | None = None,
        *,
        endpoint_id: str | None = None,
    ) -> dict[str, Any]:
        """执行 read 并记录 READ/ERROR event。"""
        if endpoint_id is not None:
            entry = registry.resolve_entry(endpoint_id)
            try:
                result = cast("dict[str, Any]", entry.driver.read(point_ids))
                _emit_entry_event(
                    registry,
                    entry,
                    "READ",
                    payload={"point_ids": point_ids},
                )
                return result
            except Exception as exc:
                _record_entry_error(
                    registry,
                    entry,
                    str(exc),
                    payload={"operation": "READ", "point_ids": point_ids},
                )
                raise

        result: dict[str, Any] = {}
        for entry in registry.available_entries():
            try:
                result[entry.endpoint.endpoint_id] = entry.driver.read(point_ids)
                _emit_entry_event(
                    registry,
                    entry,
                    "READ",
                    payload={"point_ids": point_ids},
                )
            except Exception as exc:
                _record_entry_error(
                    registry,
                    entry,
                    str(exc),
                    payload={"operation": "READ", "point_ids": point_ids},
                )
                raise
        return result


class WriteSystemUseCase:
    """写入 endpoint 点位值的 runtime 控制用例。"""

    def execute(
        self,
        registry: ServerRegistry,
        point_id: str,
        value: Any,
        *,
        endpoint_id: str | None = None,
    ) -> None:
        """执行 write 并记录 WRITE/ERROR event。"""
        entry = registry.resolve_entry(endpoint_id)
        try:
            entry.driver.write(point_id, value)
            _emit_entry_event(
                registry,
                entry,
                "WRITE",
                payload={"point_id": point_id},
            )
        except Exception as exc:
            _record_entry_error(
                registry,
                entry,
                str(exc),
                payload={"operation": "WRITE", "point_id": point_id},
            )
            raise


class HotSwapDriverInstanceUseCase:
    """执行 instance-level hot swap 的 runtime 控制用例。"""

    def execute(
        self,
        registry: ServerRegistry,
        binding_id: str,
        new_entry: DriverEntry,
        *,
        version: str = "v2",
    ) -> DriverInstance:
        """重新绑定 DriverInstance 并停止旧运行实例。

        Args:
            registry: 已构建 RuntimeGraph 的 registry 视图。
            binding_id: 要替换的 binding。
            new_entry: adapter factory 已创建好的新 driver entry。
            version: 新实例版本标识。

        Returns:
            新绑定的 DriverInstance。
        """
        new_instance = registry.create_driver_instance(
            new_entry,
            binding_id=binding_id,
            version=version,
        )
        node_id = ""
        for node in registry.runtime_graph.nodes:
            if any(binding.binding_id == binding_id for binding in node.bindings):
                node_id = node.node_id
                break

        old_instance = registry.runtime_graph.bind_driver_instance(binding_id, new_instance)
        if old_instance.driver is not None and old_instance.state in {
            DriverState.RUNNING,
            DriverState.DEGRADED,
        }:
            try:
                old_instance.driver.stop()
            except Exception as exc:
                old_instance.record_error(
                    str(exc),
                    node_id=node_id,
                    payload={"operation": "SWAP_STOP_OLD", "binding_id": binding_id},
                )
                raise
            old_instance.mark_stopped()
        if old_instance.state == DriverState.INITIALIZED:
            old_instance.transition_to(DriverState.STOPPED)
        old_instance.mark_retired()
        new_instance.emit_runtime_event(
            "SWAP",
            node_id=node_id,
            payload={"binding_id": binding_id, "old_instance_id": old_instance.id},
        )
        registry.refresh_entries()
        return new_instance


__all__ = [
    "HealthSystemUseCase",
    "HotSwapDriverInstanceUseCase",
    "ReadSystemUseCase",
    "StartSystemUseCase",
    "StopSystemUseCase",
    "WriteSystemUseCase",
]
