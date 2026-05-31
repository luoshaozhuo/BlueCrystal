"""动态运行时的测试工具函数。

为 dynamic endpoint 和 state store 测试提供共享 helper。
"""
from __future__ import annotations

import random
import socket
import time
import os
from collections.abc import Callable
from pathlib import Path

from whale.shared.source.access.model import SourceEndpointSpec, SourcePointSpec
from tools.source_lab.access.providers.base import SourceRuntimeSpec
from tools.source_lab.access.runners.http_rest_polling import HttpRestPollingRunner
from tools.source_lab.access.runners.modbus_tcp_polling import ModbusTcpPollingRunner
from tools.source_lab.access.runners.mqtt_subscription import MqttSubscriptionRunner
from tools.source_lab.access.runtime import (
    ContinuityMonitor,
    EndpointMode,
    EndpointRuntimeConfig,
    EndpointRuntimeRegistry,
    EndpointSessionManager,
    RuntimeStateStore,
    StaggerCoordinator,
)
from tools.source_lab.model import SimulatedPoint, SimulatedSource, SourceConnection
from tools.source_lab.protocols.opcua.address_space import logical_path


def choose_port(minimum: int = 56001, maximum: int = 64999) -> int:
    rng = random.SystemRandom()
    for _ in range(200):
        port = rng.randint(minimum, maximum)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("no available port")


def build_http_source(index: int, port: int) -> SimulatedSource:
    return SimulatedSource(
        connection=SourceConnection(
            name=f"http-dyn-{index}",
            host="127.0.0.1",
            port=port,
            transport="tcp",
            protocol="http_rest",
            ied_name="",
            ld_name="",
            namespace_uri=None,
        ),
        points=(
            SimulatedPoint(ln_name="WPP", do_name="TotW", unit="kW", data_type="FLOAT64"),
            SimulatedPoint(ln_name="WPP", do_name="DevSt", unit=None, data_type="BOOLEAN"),
            SimulatedPoint(ln_name="WPP", do_name="OpCnt", unit=None, data_type="INT32"),
        ),
    )


def build_modbus_source(index: int, port: int) -> SimulatedSource:
    return SimulatedSource(
        connection=SourceConnection(
            name=f"modbus-dyn-{index}",
            host="127.0.0.1",
            port=port,
            transport="tcp",
            protocol="modbus_tcp",
            ied_name="",
            ld_name="",
            namespace_uri=None,
        ),
        points=(
            SimulatedPoint(ln_name="holding", do_name="0", unit=None, data_type="INT32"),
            SimulatedPoint(ln_name="holding", do_name="1", unit=None, data_type="INT32"),
            SimulatedPoint(ln_name="holding", do_name="2", unit=None, data_type="INT32"),
        ),
    )


def build_mqtt_source(index: int, port: int) -> SimulatedSource:
    return SimulatedSource(
        connection=SourceConnection(
            name=f"mqtt-dyn-{index}",
            host="127.0.0.1",
            port=port,
            transport="tcp",
            protocol="mqtt",
            ied_name="",
            ld_name="",
            namespace_uri=None,
        ),
        points=(SimulatedPoint(ln_name="mqtt", do_name="payload", unit=None, data_type="INT32"),),
    )


def build_opcua_source(index: int, port: int) -> SimulatedSource:
    return SimulatedSource(
        connection=SourceConnection(
            name=f"opcua-dyn-{index}",
            host="127.0.0.1",
            port=port,
            transport="tcp",
            protocol="opcua",
            ied_name="OPCUAIED",
            ld_name="LD0",
            namespace_uri=f"urn:whale:dynamic:opcua:{index}",
        ),
        points=(
            SimulatedPoint(ln_name="WPPD1", do_name="TotW", unit="kW", data_type="FLOAT64"),
            SimulatedPoint(ln_name="WPPD1", do_name="DevSt", unit=None, data_type="BOOLEAN"),
            SimulatedPoint(ln_name="WPPD1", do_name="OpCnt", unit=None, data_type="INT32"),
        ),
    )


def build_iec61850_report_source(index: int, port: int) -> SimulatedSource:
    return SimulatedSource(
        connection=SourceConnection(
            name=f"report-dyn-{index}",
            host="127.0.0.1",
            port=port,
            transport="tcp",
            protocol="iec61850_report",
            ied_name="Simulator",
            ld_name="LD0",
            namespace_uri=None,
            params={"use_native_report_runner": True, "rcb_ref": "EventsRCB01"},
        ),
        points=(
            SimulatedPoint(ln_name="LLN0", do_name="Events", unit=None, data_type="BOOLEAN"),
            SimulatedPoint(ln_name="WPPD1", do_name="TotW", unit="kW", data_type="FLOAT64"),
        ),
    )


def build_goose_source(index: int, app_id: int) -> SimulatedSource:
    subscriber_interface = os.environ.get("SOURCE_LAB_L2_SUBSCRIBER_INTERFACE") or os.environ.get(
        "SOURCE_LAB_L2_INTERFACE", "lo"
    )
    publisher_interface = os.environ.get("SOURCE_LAB_L2_PUBLISHER_INTERFACE") or subscriber_interface
    return SimulatedSource(
        connection=SourceConnection(
            name=f"goose-dyn-{index}",
            host="127.0.0.1",
            port=0,
            transport="ethernet_l2",
            protocol="iec61850_goose",
            ied_name="Simulator",
            ld_name="LLN0",
            namespace_uri=None,
            params={
                "l2_interface": subscriber_interface,
                "subscriber_l2_interface": subscriber_interface,
                "publisher_l2_interface": publisher_interface,
                "app_id": app_id,
                "publish_interval_ms": 1000,
            },
        ),
        points=(SimulatedPoint(ln_name="LLN0", do_name="Events", unit=None, data_type="BOOLEAN"),),
    )


def build_sv_source(index: int, app_id: int) -> SimulatedSource:
    subscriber_interface = os.environ.get("SOURCE_LAB_L2_SUBSCRIBER_INTERFACE") or os.environ.get(
        "SOURCE_LAB_L2_INTERFACE", "lo"
    )
    publisher_interface = os.environ.get("SOURCE_LAB_L2_PUBLISHER_INTERFACE") or subscriber_interface
    return SimulatedSource(
        connection=SourceConnection(
            name=f"sv-dyn-{index}",
            host="127.0.0.1",
            port=0,
            transport="ethernet_l2",
            protocol="iec61850_sv",
            ied_name="Simulator",
            ld_name="LLN0",
            namespace_uri=None,
            params={
                "l2_interface": subscriber_interface,
                "subscriber_l2_interface": subscriber_interface,
                "publisher_l2_interface": publisher_interface,
                "app_id": app_id,
                "sample_rate_hz": 1,
            },
        ),
        points=(SimulatedPoint(ln_name="LLN0", do_name="PhVMeas", unit=None, data_type="FLOAT64"),),
    )


def runtime_spec(source: SimulatedSource, *, params: dict[str, object] | None = None) -> SourceRuntimeSpec:
    # SourceConnection.params 的类型为 dict[str, str | int | float | bool]，
    # 测试用 params 参数使用 dict[str, object] 以容纳更宽的测试值类型。
    # 在合并后传给 endpoint params 时使用 cast 适配。
    merged_params = dict(source.connection.params)
    if source.connection.protocol == "modbus_tcp":
        merged_params.setdefault("modbus_start_address", 0)
    if source.connection.protocol == "http_rest":
        merged_params.setdefault("http_path", "/points")
    if params:
        # test 用 params 放宽为 dict[str, object]，与 dict(source.connection.params)
        # 的严格类型不兼容。合并后实际值均为 str|int|float|bool，安全忽略。
        merged_params.update(params)  # type: ignore[arg-type]
    return SourceRuntimeSpec(
        endpoint=SourceEndpointSpec(
            name=source.connection.name,
            host=source.connection.host,
            port=source.connection.port,
            protocol=source.connection.protocol,
            transport=source.connection.transport,
            namespace_uri=source.connection.namespace_uri,
            ied_name=source.connection.ied_name,
            ld_name=source.connection.ld_name,
            # merged_params 值类型放宽为 object 以容纳测试用参数，
            # 实际值均为 str|int|float|bool，SourceEndpointSpec 可安全接受。
            params=merged_params,  # type: ignore[arg-type]
        ),
        points=tuple(
            SourcePointSpec(
                address=(
                    logical_path(source.connection, point)
                    if source.connection.protocol == "opcua"
                    else point.key
                ),
                name=point.key,
                data_type=point.data_type,
                ln_name=point.ln_name,
                do_name=point.do_name,
                unit=point.unit,
            )
            for point in source.points
        ),
    )


def polling_config(
    source: SimulatedSource,
    *,
    hz: float = 4.0,
    params: dict[str, object] | None = None,
) -> EndpointRuntimeConfig:
    spec = runtime_spec(source, params=params)
    return EndpointRuntimeConfig(
        endpoint_id=spec.endpoint.name,
        protocol=spec.endpoint.protocol,
        mode=EndpointMode.POLLING,
        source=spec,
        target_hz=hz,
        read_timeout_s=2.0,
    )


def subscribe_config(
    source: SimulatedSource,
    *,
    interval_ms: float = 150.0,
    params: dict[str, object] | None = None,
) -> EndpointRuntimeConfig:
    spec = runtime_spec(source, params=params)
    return EndpointRuntimeConfig(
        endpoint_id=spec.endpoint.name,
        protocol=spec.endpoint.protocol,
        mode=EndpointMode.SUBSCRIBE,
        source=spec,
        publishing_interval_ms=interval_ms,
        read_timeout_s=2.0,
    )


def report_config(
    source: SimulatedSource,
    *,
    interval_ms: float = 500.0,
    params: dict[str, object] | None = None,
) -> EndpointRuntimeConfig:
    spec = runtime_spec(source, params=params)
    return EndpointRuntimeConfig(
        endpoint_id=spec.endpoint.name,
        protocol=spec.endpoint.protocol,
        mode=EndpointMode.REPORT,
        source=spec,
        publishing_interval_ms=interval_ms,
        read_timeout_s=2.0,
    )


def streaming_config(
    source: SimulatedSource,
    *,
    interval_ms: float = 1000.0,
    params: dict[str, object] | None = None,
) -> EndpointRuntimeConfig:
    spec = runtime_spec(source, params=params)
    return EndpointRuntimeConfig(
        endpoint_id=spec.endpoint.name,
        protocol=spec.endpoint.protocol,
        mode=EndpointMode.STREAMING,
        source=spec,
        publishing_interval_ms=interval_ms,
        read_timeout_s=2.0,
    )


def build_registry(
    tmp_path: Path,
    *,
    decision_hook: Callable[[str, str, dict[str, object]], tuple[bool, str]] | None = None,
) -> tuple[EndpointRuntimeRegistry, ContinuityMonitor]:
    monitor = ContinuityMonitor()
    stagger = StaggerCoordinator()
    # 测试用简单 runner factory：仅覆盖 modbus_tcp/http_rest/mqtt。
    # runner 都是 CapacityRunner/SubscriptionRunner 子类，但 lambda 推断为具体类型，
    # 需显式标注返回类型以满足 EndpointSessionManager 的类型签名。
    from tools.source_lab.access.runners.base import CapacityRunner, SubscriptionRunner  # noqa: F811
    from tools.source_lab.access.runners.registry import RunnerInfo

    def _polling_factory(protocol: str) -> RunnerInfo | CapacityRunner:
        if protocol == "modbus_tcp":
            return ModbusTcpPollingRunner()
        if protocol == "http_rest":
            return HttpRestPollingRunner()
        raise ValueError(f"no polling runner for {protocol}")

    def _subscription_factory(protocol: str) -> SubscriptionRunner:
        if protocol == "mqtt":
            return MqttSubscriptionRunner()
        raise ValueError(f"no subscription runner for {protocol}")

    session_manager = EndpointSessionManager(
        continuity_monitor=monitor,
        stagger_coordinator=stagger,
        polling_runner_factory=_polling_factory,
        subscription_runner_factory=_subscription_factory,
    )
    registry = EndpointRuntimeRegistry(
        session_manager=session_manager,
        continuity_monitor=monitor,
        stagger_coordinator=stagger,
        state_store=RuntimeStateStore(str(tmp_path / "runtime")),
        decision_hook=decision_hook,
    )
    return registry, monitor


def build_native_registry(
    tmp_path: Path,
    *,
    decision_hook: Callable[[str, str, dict[str, object]], tuple[bool, str]] | None = None,
) -> tuple[EndpointRuntimeRegistry, ContinuityMonitor]:
    monitor = ContinuityMonitor()
    stagger = StaggerCoordinator()
    session_manager = EndpointSessionManager(
        continuity_monitor=monitor,
        stagger_coordinator=stagger,
    )
    registry = EndpointRuntimeRegistry(
        session_manager=session_manager,
        continuity_monitor=monitor,
        stagger_coordinator=stagger,
        state_store=RuntimeStateStore(str(tmp_path / "runtime")),
        decision_hook=decision_hook,
    )
    return registry, monitor


def shutdown_registry(registry: EndpointRuntimeRegistry) -> None:
    for runtime in registry.list_status():
        if runtime.state.value != "deleted":
            registry.stop_endpoint(runtime.endpoint_id)


def wait_for_metric_growth(
    monitor: ContinuityMonitor,
    endpoint_id: str,
    *,
    baseline_samples: int | None = None,
    minimum_delta: int = 1,
    timeout_s: float = 5.0,
) -> None:
    deadline = time.time() + timeout_s
    before = monitor.snapshot().get(endpoint_id)
    before_samples = baseline_samples if baseline_samples is not None else (
        before.endpoint_actual_samples if before is not None else 0
    )
    while time.time() < deadline:
        after = monitor.snapshot().get(endpoint_id)
        after_samples = after.endpoint_actual_samples if after is not None else 0
        if after_samples >= before_samples + minimum_delta:
            return
        time.sleep(0.05)
    raise AssertionError(f"metric did not grow for {endpoint_id}")
