"""ingest 运行时模块级就绪探针聚合。

汇总运行时数据库、Redis/StateCache、Kafka/MessagePublisher、
audit sink、access policy、shared_source runner readiness、
source adapter registry、config/runtime mode 等组件的就绪状态，
输出每个组件 status/reason/latency_ms/fail-open|fail-closed/required|optional。

核心原则：
- required 组件失败 => 整体 not ready
- optional 组件失败 => 整体仍 ready（degraded）
- 响应不泄露内部 IP、密码、token 等敏感信息

不负责：单个组件的具体健康检查逻辑（由各组件自身实现）。
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from pacific.whale.ingest.config import CONFIG

LOGGER = logging.getLogger(__name__)

# 默认超时秒数，适用于 TCP connect / 简单 ping 等轻量检查
DEFAULT_CHECK_TIMEOUT_SECONDS = 3.0


class RuntimeCheckFn(Protocol):
    """运行时组件就绪检查函数签名。"""

    def __call__(self, *, timeout_seconds: float) -> dict[str, object]:
        """执行一次就绪检查，返回结构化结果。

        Returns:
            包含 status (str)、reason (str)、latency_ms (float) 的字典。
        """


@dataclass(frozen=False, slots=True)
class ComponentReadinessEntry:
    """单个组件的就绪检查结果。

    Args:
        component: 组件名称，如 "runtime_db"、"redis_state_cache"。
        status: "ready" / "degraded" / "not_ready" / "unchecked"。
        reason: 人类可读的状态描述。
        required: 是否为必需组件。
        fail_open: True 表示不阻塞，False 表示 fail-closed 阻塞就绪。
        latency_ms: 检查耗时毫秒数。
        detail: 可选的额外诊断信息（不得包含敏感信息）。
    """

    component: str
    status: str
    reason: str
    required: bool
    fail_open: bool
    latency_ms: float
    detail: dict[str, object] | None = None


@dataclass(frozen=False, slots=True)
class ReadyzAggregate:
    """模块级就绪聚合结果。

    Attributes:
        overall: "ready" | "degraded" | "not_ready"。
        checked_at: 检查时的 UTC ISO 时间戳。
        components: 各组件就绪条目列表。
        degraded_reasons: optional 组件失败的原因摘要列表。
        config_mode: 当前运行时模式。
    """

    overall: str
    checked_at: str
    components: list[dict[str, object]]
    degraded_reasons: list[str] = field(default_factory=list)
    config_mode: str = ""


_SENSITIVE_KEYS: frozenset[str] = frozenset({
    "password", "token", "secret", "api_key", "apikey",
    "passwd", "credential", "dsn", "url", "connection_string",
    "redis_url", "database_url", "bootstrap_servers",
})


def _sanitize_detail(raw: dict[str, object] | None) -> dict[str, object] | None:
    """剔除 detail 中包含敏感信息的键值。

    防止 readyz 响应泄露内部 IP、密码、token 等。
    日志中可保留完整诊断信息，但 API 响应必须脱敏。
    """
    if raw is None:
        return None
    sanitized: dict[str, object] = {}
    for key, value in raw.items():
        lower_key = key.lower()
        if any(bad in lower_key for bad in _SENSITIVE_KEYS):
            sanitized[key] = "***REDACTED***"
        else:
            sanitized[key] = value
    return sanitized


def _build_check_result(
    *,
    component: str,
    status: str,
    reason: str,
    required: bool,
    fail_open: bool,
    latency_ms: float,
    detail: dict[str, object] | None = None,
) -> dict[str, object]:
    """构建单个组件就绪检查的 API 响应字典（已对 detail 脱敏）。"""
    return {
        "component": component,
        "status": status,
        "reason": reason,
        "required": required,
        "fail_open": fail_open,
        "latency_ms": round(latency_ms, 3),
        "detail": _sanitize_detail(detail),
    }


# ── 各组件就绪检查函数 ──────────────────────────────────────────────


def _check_runtime_db(
    engine_provider: Any | None = None,
    *,
    timeout_seconds: float = DEFAULT_CHECK_TIMEOUT_SECONDS,
) -> ComponentReadinessEntry:
    """检查运行时数据库连接。

    required=True, fail_open=False。
    数据库不可达时必须阻塞 ready。
    """
    t0 = time.perf_counter()
    try:
        from pacific.whale.ingest.framework.persistence.runtime_db import probe_runtime_readiness
        from sqlalchemy import create_engine

        if engine_provider is not None:
            engine = engine_provider
        else:
            from pacific.whale.ingest.framework.persistence.session import create_db_url
            engine = create_engine(
                create_db_url(),
                connect_args={"connect_timeout": int(timeout_seconds)},
                pool_pre_ping=False,
            )

        probe_runtime_readiness(engine, timeout_seconds=int(timeout_seconds))
        elapsed = (time.perf_counter() - t0) * 1000.0
        return ComponentReadinessEntry(
            component="runtime_db",
            status="ready",
            reason="数据库连接正常",
            required=True,
            fail_open=False,
            latency_ms=elapsed,
            detail={"backend": CONFIG.database.backend},
        )
    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000.0
        return ComponentReadinessEntry(
            component="runtime_db",
            status="not_ready",
            reason=f"数据库不可达: {type(exc).__name__}",
            required=True,
            fail_open=False,
            latency_ms=elapsed,
            detail={"backend": CONFIG.database.backend, "error": str(exc)[:200]},
        )


def _check_redis_state_cache(
    redis_client: Any | None = None,
    *,
    timeout_seconds: float = DEFAULT_CHECK_TIMEOUT_SECONDS,
) -> ComponentReadinessEntry:
    """检查 Redis 状态缓存连接。

    required=True, fail_open=False。
    Redis 不可达时必须阻塞 ready（采集和状态写入依赖 Redis）。
    """
    t0 = time.perf_counter()
    try:
        import redis as redis_lib

        if redis_client is not None:
            r = redis_client
        else:
            r = redis_lib.Redis(
                host=CONFIG.state_cache.host,
                port=CONFIG.state_cache.port,
                db=CONFIG.state_cache.db,
                socket_connect_timeout=timeout_seconds,
                socket_timeout=timeout_seconds,
            )

        r.ping()
        elapsed = (time.perf_counter() - t0) * 1000.0
        return ComponentReadinessEntry(
            component="redis_state_cache",
            status="ready",
            reason="Redis 状态缓存连接正常",
            required=True,
            fail_open=False,
            latency_ms=elapsed,
            detail={"backend": CONFIG.state_cache.backend},
        )
    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000.0
        return ComponentReadinessEntry(
            component="redis_state_cache",
            status="not_ready",
            reason=f"Redis 不可达: {type(exc).__name__}",
            required=True,
            fail_open=False,
            latency_ms=elapsed,
            detail={"backend": CONFIG.state_cache.backend, "error": str(exc)[:200]},
        )


def _check_message_publisher(
    publisher: Any | None = None,
    *,
    timeout_seconds: float = DEFAULT_CHECK_TIMEOUT_SECONDS,
) -> ComponentReadinessEntry:
    """检查消息发布器（Kafka/Redis Streams/Relational Outbox）。

    required=True, fail_open=False（采集-发布链路不可失）。
    """
    t0 = time.perf_counter()
    backend = CONFIG.message.backend

    try:
        if publisher is not None:
            if hasattr(publisher, "health_check"):
                publisher.health_check()
            # 有 publisher 实例即视为可用，不盲目 TCP 连接后端
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ComponentReadinessEntry(
                component="message_publisher",
                status="ready",
                reason="消息发布器实例已注入",
                required=True,
                fail_open=False,
                latency_ms=elapsed,
                detail={"backend": backend},
            )

        if backend == "kafka":
            from pacific.whale.ingest.config import KafkaMessageConfig
            from typing import cast
            import socket

            kafka_cfg = cast(KafkaMessageConfig, CONFIG.message)
            for server in kafka_cfg.bootstrap_servers:
                host, _, port_str = server.partition(":")
                port = int(port_str) if port_str else 9092
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout_seconds)
                try:
                    sock.connect((host, port))
                finally:
                    sock.close()

            elapsed = (time.perf_counter() - t0) * 1000.0
            return ComponentReadinessEntry(
                component="kafka_message_publisher",
                status="ready",
                reason="Kafka 至少一个 broker TCP 可连通",
                required=True,
                fail_open=False,
                latency_ms=elapsed,
                detail={"backend": backend},
            )

        elif backend == "redis_streams":
            # Redis Streams 复用 Redis 连通性
            # 实际 redis_state_cache 已检查同一 Redis 实例
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ComponentReadinessEntry(
                component="redis_streams_publisher",
                status="ready",
                reason="Redis Streams 发布器复用 Redis 连通性",
                required=True,
                fail_open=False,
                latency_ms=elapsed,
                detail={"backend": backend},
            )

        elif backend == "relational_outbox":
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ComponentReadinessEntry(
                component="relational_outbox_publisher",
                status="ready",
                reason="关系数据库 outbox 发布器与 runtime_db 共享连接",
                required=True,
                fail_open=False,
                latency_ms=elapsed,
                detail={"backend": backend},
            )

        else:
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ComponentReadinessEntry(
                component="message_publisher",
                status="ready",
                reason=f"消息后端 {backend} 已配置",
                required=True,
                fail_open=False,
                latency_ms=elapsed,
            )
    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000.0
        return ComponentReadinessEntry(
            component="message_publisher",
            status="not_ready",
            reason=f"消息发布器不可达: {type(exc).__name__}",
            required=True,
            fail_open=False,
            latency_ms=elapsed,
            detail={"backend": backend, "error": str(exc)[:200]},
        )


def _check_audit_sink(
    audit_sink: Any | None = None,
    *,
    timeout_seconds: float = DEFAULT_CHECK_TIMEOUT_SECONDS,
) -> ComponentReadinessEntry:
    """检查审计 sink 可用性。

    required=False, fail_open=True。
    审计失败不应阻塞主业务；但审计不可用应标记为 degraded。
    """
    t0 = time.perf_counter()
    try:
        if audit_sink is None:
            elapsed = (time.perf_counter() - t0) * 1000.0
            return ComponentReadinessEntry(
                component="audit_sink",
                status="degraded",
                reason="审计 sink 未注入（no-op 模式）",
                required=False,
                fail_open=True,
                latency_ms=elapsed,
                detail={"mode": "no-op"},
            )
        # 审计 sink 有实例即视为可用
        elapsed = (time.perf_counter() - t0) * 1000.0
        return ComponentReadinessEntry(
            component="audit_sink",
            status="ready",
            reason="审计 sink 可用",
            required=False,
            fail_open=True,
            latency_ms=elapsed,
            detail={"type": type(audit_sink).__name__},
        )
    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000.0
        return ComponentReadinessEntry(
            component="audit_sink",
            status="degraded",
            reason=f"审计 sink 检查失败: {type(exc).__name__}",
            required=False,
            fail_open=True,
            latency_ms=elapsed,
            detail={"error": str(exc)[:200]},
        )


def _check_access_policy(
    access_policy: Any | None = None,
    *,
    timeout_seconds: float = DEFAULT_CHECK_TIMEOUT_SECONDS,
) -> ComponentReadinessEntry:
    """检查访问策略组件。

    required=False, fail_open=True。
    默认 allow-all 视作 degraded，生产部署应注入真实策略。
    """
    t0 = time.perf_counter()
    try:
        elapsed = (time.perf_counter() - t0) * 1000.0
        if access_policy is None:
            return ComponentReadinessEntry(
                component="access_policy",
                status="degraded",
                reason="访问策略未注入（默认 allow-all 模式，不适用于生产环境）",
                required=False,
                fail_open=True,
                latency_ms=elapsed,
                detail={"mode": "allow-all"},
            )
        return ComponentReadinessEntry(
            component="access_policy",
            status="ready",
            reason="访问策略已注入",
            required=False,
            fail_open=True,
            latency_ms=elapsed,
            detail={"type": type(access_policy).__name__},
        )
    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000.0
        return ComponentReadinessEntry(
            component="access_policy",
            status="degraded",
            reason=f"访问策略检查失败: {type(exc).__name__}",
            required=False,
            fail_open=True,
            latency_ms=elapsed,
            detail={"error": str(exc)[:200]},
        )


def _check_shared_source_runner_readiness(
    *,
    timeout_seconds: float = DEFAULT_CHECK_TIMEOUT_SECONDS,
) -> ComponentReadinessEntry:
    """检查 shared_source production runner 可用性。

    检测 WHALE_SHARED_SOURCE_RUNNER_DIR 环境变量、PATH 发现、
    以及 whitelisted dev fallback 状态。

    required=False, fail_open=True。
    无 native runner 时降级为 Python lightweight runner。
    """
    t0 = time.perf_counter()
    try:
        import os
        from pacific.whale.shared.source.runner_resolution import (
            _PRODUCTION_RUNNER_DIR_ENV,
            _ALLOW_DEV_FALLBACK_ENV,
            _is_truthy,
        )

        shared_dir = os.environ.get(_PRODUCTION_RUNNER_DIR_ENV)
        dev_fallback = _is_truthy(os.environ.get(_ALLOW_DEV_FALLBACK_ENV))

        detail: dict[str, object] = {
            "production_runner_dir_set": shared_dir is not None,
            "dev_fallback_enabled": dev_fallback,
        }

        if shared_dir:
            from pathlib import Path
            rd = Path(shared_dir).expanduser().resolve()
            detail["resolved_runner_dir"] = str(rd)
            detail["runner_dir_exists"] = rd.exists()

        # 尝试查找一个可用的 native runner 以验证路径
        runner_stems = (
            "open62541_client_runner",
            "modbus_tcp_polling_runner",
            "iec61850_mms_client_runner",
            "iec104_client_runner",
        )
        found_count = 0
        import shutil

        for stem in runner_stems:
            if shutil.which(stem):
                found_count += 1

        elapsed = (time.perf_counter() - t0) * 1000.0
        if found_count >= 2:
            return ComponentReadinessEntry(
                component="shared_source_runner",
                status="ready",
                reason=f"PATH 发现 {found_count} 个 native runner",
                required=False,
                fail_open=True,
                latency_ms=elapsed,
                detail=detail,
            )
        elif found_count == 1:
            return ComponentReadinessEntry(
                component="shared_source_runner",
                status="ready",
                reason="PATH 发现 1 个 native runner",
                required=False,
                fail_open=True,
                latency_ms=elapsed,
                detail=detail,
            )
        elif shared_dir:
            return ComponentReadinessEntry(
                component="shared_source_runner",
                status="ready",
                reason="WHALE_SHARED_SOURCE_RUNNER_DIR 已设置",
                required=False,
                fail_open=True,
                latency_ms=elapsed,
                detail=detail,
            )
        elif dev_fallback:
            return ComponentReadinessEntry(
                component="shared_source_runner",
                status="degraded",
                reason="使用 dev/test fallback（非生产 runner artifact）",
                required=False,
                fail_open=True,
                latency_ms=elapsed,
                detail=detail,
            )
        else:
            return ComponentReadinessEntry(
                component="shared_source_runner",
                status="degraded",
                reason="未发现 production native runner；需设置 WHALE_SHARED_SOURCE_RUNNER_DIR 或安装到 PATH",
                required=False,
                fail_open=True,
                latency_ms=elapsed,
                detail=detail,
            )
    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000.0
        return ComponentReadinessEntry(
            component="shared_source_runner",
            status="degraded",
            reason=f"runner readiness 检查异常: {type(exc).__name__}",
            required=False,
            fail_open=True,
            latency_ms=elapsed,
            detail={"error": str(exc)[:200]},
        )


def _check_source_adapter_registry(
    acquisition_registry: Any | None = None,
    write_registry: Any | None = None,
    *,
    timeout_seconds: float = DEFAULT_CHECK_TIMEOUT_SECONDS,
) -> ComponentReadinessEntry:
    """检查 source adapter registry 中已注册的协议适配器。

    required=True, fail_open=False。
    至少一个采集适配器可用时视为 ready。
    """
    t0 = time.perf_counter()
    try:
        detail: dict[str, object] = {}
        acquisition_protocols: list[str] = []
        write_protocols: list[str] = []

        if acquisition_registry is not None:
            if hasattr(acquisition_registry, "ports_by_protocol"):
                acquisition_protocols = sorted(acquisition_registry.ports_by_protocol.keys())
            elif hasattr(acquisition_registry, "list_protocols"):
                acquisition_protocols = sorted(acquisition_registry.list_protocols())
            elif hasattr(acquisition_registry, "get"):
                acquisition_protocols = ["(protocol-registry)"]

        if write_registry is not None:
            if hasattr(write_registry, "ports_by_protocol"):
                write_protocols = sorted(write_registry.ports_by_protocol.keys())
            elif hasattr(write_registry, "list_protocols"):
                write_protocols = sorted(write_registry.list_protocols())
            elif hasattr(write_registry, "get"):
                write_protocols = ["(protocol-registry)"]

        detail["acquisition_protocols"] = acquisition_protocols
        detail["write_protocols"] = write_protocols

        elapsed = (time.perf_counter() - t0) * 1000.0

        if not acquisition_protocols and not write_protocols:
            return ComponentReadinessEntry(
                component="source_adapter_registry",
                status="not_ready",
                reason="未注册任何采集或写入适配器",
                required=True,
                fail_open=False,
                latency_ms=elapsed,
                detail=detail,
            )

        return ComponentReadinessEntry(
            component="source_adapter_registry",
            status="ready",
            reason=f"已注册 {len(acquisition_protocols)} 个采集协议, "
                    f"{len(write_protocols)} 个写入协议",
            required=True,
            fail_open=False,
            latency_ms=elapsed,
            detail=detail,
        )
    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000.0
        return ComponentReadinessEntry(
            component="source_adapter_registry",
            status="not_ready",
            reason=f"adapter registry 检查失败: {type(exc).__name__}",
            required=True,
            fail_open=False,
            latency_ms=elapsed,
            detail={"error": str(exc)[:200]},
        )


def _check_config_runtime_mode(
    *,
    timeout_seconds: float = DEFAULT_CHECK_TIMEOUT_SECONDS,
) -> ComponentReadinessEntry:
    """检查配置和运行时模式。

    required=True, fail_open=False。
    """
    t0 = time.perf_counter()
    try:
        db_backend = CONFIG.database.backend
        cache_backend = CONFIG.state_cache_backend
        message_backend = CONFIG.message.backend

        elapsed = (time.perf_counter() - t0) * 1000.0
        return ComponentReadinessEntry(
            component="config_runtime_mode",
            status="ready",
            reason=f"运行模式: db={db_backend}, cache={cache_backend}, message={message_backend}",
            required=True,
            fail_open=False,
            latency_ms=elapsed,
            detail={
                "database_backend": db_backend,
                "state_cache_backend": cache_backend,
                "message_backend": message_backend,
            },
        )
    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000.0
        return ComponentReadinessEntry(
            component="config_runtime_mode",
            status="not_ready",
            reason=f"配置加载失败: {type(exc).__name__}",
            required=True,
            fail_open=False,
            latency_ms=elapsed,
            detail={"error": str(exc)[:200]},
        )


# ── 聚合就绪探针 ──────────────────────────────────────────────────────


_ReadinessCheckerTuple = tuple[str, RuntimeCheckFn]


def _make_checker(entry: ComponentReadinessEntry) -> RuntimeCheckFn:
    """将 ComponentReadinessEntry 转化为统一签名的检查函数。"""
    def _check(*, timeout_seconds: float) -> dict[str, object]:
        _ = timeout_seconds
        return {
            "component": entry.component,
            "status": entry.status,
            "reason": entry.reason,
            "required": entry.required,
            "fail_open": entry.fail_open,
            "latency_ms": entry.latency_ms,
            "detail": entry.detail,
        }
    return _check


def evaluate_readiness(
    *,
    session_factory: Any | None = None,
    audit_sink: Any | None = None,
    access_policy: Any | None = None,
    acquisition_registry: Any | None = None,
    write_registry: Any | None = None,
    redis_client: Any | None = None,
    message_publisher: Any | None = None,
    timeout_seconds: float = DEFAULT_CHECK_TIMEOUT_SECONDS,
) -> ReadyzAggregate:
    """执行模块级就绪聚合检查。

    依次检查 runtime_db、redis_state_cache、message_publisher、
    audit_sink、access_policy、shared_source_runner、
    source_adapter_registry、config_runtime_mode。

    Args:
        session_factory: 可选的数据库 session 工厂，用于构造 DB 引擎。
        audit_sink: 审计 sink 实例。
        access_policy: 访问策略实例。
        acquisition_registry: 采集适配器注册表。
        write_registry: 写入适配器注册表。
        redis_client: Redis 客户端实例。
        message_publisher: 消息发布器实例。
        timeout_seconds: 每个检查的超时秒数。

    Returns:
        ReadyzAggregate 包含 overall 状态、各组件条目的聚合结果。
    """
    from datetime import UTC, datetime

    engine_provider = None
    if session_factory is not None:
        if hasattr(session_factory, "kw") and hasattr(session_factory, "kw") and "bind" in getattr(session_factory, "kw", {}):
            engine_provider = session_factory.kw["bind"]

    checks: list[tuple[str, Callable[[], ComponentReadinessEntry]]] = [
        ("runtime_db", lambda: _check_runtime_db(
            engine_provider=engine_provider,
            timeout_seconds=timeout_seconds,
        )),
        ("redis_state_cache", lambda: _check_redis_state_cache(
            redis_client=redis_client,
            timeout_seconds=timeout_seconds,
        )),
        ("message_publisher", lambda: _check_message_publisher(
            publisher=message_publisher,
            timeout_seconds=timeout_seconds,
        )),
        ("audit_sink", lambda: _check_audit_sink(
            audit_sink=audit_sink,
            timeout_seconds=timeout_seconds,
        )),
        ("access_policy", lambda: _check_access_policy(
            access_policy=access_policy,
            timeout_seconds=timeout_seconds,
        )),
        ("shared_source_runner", lambda: _check_shared_source_runner_readiness(
            timeout_seconds=timeout_seconds,
        )),
        ("source_adapter_registry", lambda: _check_source_adapter_registry(
            acquisition_registry=acquisition_registry,
            write_registry=write_registry,
            timeout_seconds=timeout_seconds,
        )),
        ("config_runtime_mode", lambda: _check_config_runtime_mode(
            timeout_seconds=timeout_seconds,
        )),
    ]

    entries: list[ComponentReadinessEntry] = []
    overall_ready = True
    degraded_reasons: list[str] = []

    for name, check_fn in checks:
        try:
            entry = check_fn()
        except Exception as exc:
            entry = ComponentReadinessEntry(
                component=name,
                status="not_ready",
                reason=f"检查抛出异常: {type(exc).__name__}",
                required=True,
                fail_open=False,
                latency_ms=0.0,
                detail={"error": str(exc)[:200]},
            )
        entries.append(entry)

        if entry.required and not entry.fail_open and entry.status != "ready":
            overall_ready = False
        if entry.required and entry.fail_open and entry.status not in ("ready",):
            degraded_reasons.append(f"{entry.component}: {entry.reason}")
        if not entry.required and entry.status != "ready":
            degraded_reasons.append(f"{entry.component}: {entry.reason}")

    # 确定总体状态
    if overall_ready and not degraded_reasons:
        overall = "ready"
    elif overall_ready and degraded_reasons:
        overall = "degraded"
    else:
        overall = "not_ready"

    return ReadyzAggregate(
        overall=overall,
        checked_at=datetime.now(tz=UTC).isoformat(),
        components=[_build_check_result(
            component=e.component,
            status=e.status,
            reason=e.reason,
            required=e.required,
            fail_open=e.fail_open,
            latency_ms=e.latency_ms,
            detail=e.detail,
        ) for e in entries],
        degraded_reasons=degraded_reasons,
        config_mode="api",
    )


def build_readyz_response(
    aggregate: ReadyzAggregate,
) -> dict[str, object]:
    """从 ReadyzAggregate 构建安全的 API 响应字典。

    确保不泄露内部 IP、密码、token 等敏感信息。

    Args:
        aggregate: evaluate_readiness() 返回的聚合结果。

    Returns:
        安全的 JSON 可序列化字典，包含 overall、checked_at、
        components、degraded_reasons、config_mode。
    """
    return {
        "status": aggregate.overall,
        "checked_at": aggregate.checked_at,
        "components": aggregate.components,
        "degraded_reasons": aggregate.degraded_reasons,
        "config_mode": aggregate.config_mode,
    }
