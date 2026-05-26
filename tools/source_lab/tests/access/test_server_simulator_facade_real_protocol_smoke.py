"""ServerSimulatorFacade 真实协议 Smoke 测试。

验证每个协议的 simulator facade 能正常启动、TCP 端口可达、
update_values 注入数据后可通过健康检查验证。

跳过条件：需要可用 TCP 端口；不依赖 C 子进程编译结果。
"""

from __future__ import annotations

import asyncio
import random
import socket
from dataclasses import replace

import pytest

from tools.source_lab.model import SimulatedPoint, SimulatedSource, SourceConnection
from tools.source_lab.protocols.registry import create_server_simulator


def _choose_available_port(
    *,
    host: str = "127.0.0.1",
    minimum_port: int = 41001,
    maximum_port: int = 42999,
) -> int:
    rng = random.SystemRandom()
    tried: set[int] = set()
    for _ in range(100):
        candidate = rng.randint(minimum_port, maximum_port)
        if candidate in tried:
            continue
        tried.add(candidate)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, candidate))
            except OSError:
                continue
            return candidate
    raise RuntimeError("No available TCP ports found")


# ── 构建各协议的 SimulatedSource ──────────────────────────────────────────

_SMOKE_POINTS = (
    SimulatedPoint(ln_name="WPPD1", do_name="TotW", unit="kW", data_type="FLOAT64", initial_value=12.5),
    SimulatedPoint(ln_name="WPPD1", do_name="DevSt", unit=None, data_type="BOOLEAN", initial_value=True),
    SimulatedPoint(ln_name="WPPD1", do_name="OpCnt", unit=None, data_type="INT32", initial_value=7),
)


def _build_source(protocol: str, port: int) -> SimulatedSource:
    base_kwargs = dict(
        name=f"{protocol}_smoke",
        host="127.0.0.1",
        port=port,
        transport="tcp",
        protocol=protocol,
    )
    # 协议特定参数
    if protocol == "opcua":
        base_kwargs["namespace_uri"] = "urn:whale:smoke:opcua"
        base_kwargs["ied_name"] = "OPCUAIED"
        base_kwargs["ld_name"] = "LD0"
    elif protocol in ("modbus_tcp", "modbus_rtu"):
        base_kwargs["namespace_uri"] = None
        base_kwargs["ied_name"] = ""
        base_kwargs["ld_name"] = ""
    elif protocol == "iec104":
        base_kwargs["namespace_uri"] = None
        base_kwargs["ied_name"] = ""
        base_kwargs["ld_name"] = ""
    elif protocol in ("iec61850_mms", "iec61850_report"):
        base_kwargs["namespace_uri"] = None
        base_kwargs["ied_name"] = "IED61850"
        base_kwargs["ld_name"] = "LD0"
    elif protocol == "iec61850_goose":
        base_kwargs["namespace_uri"] = None
        base_kwargs["ied_name"] = "Simulator"
        base_kwargs["ld_name"] = "LLN0"
        base_kwargs["transport"] = "ethernet_l2"
        base_kwargs["params"] = {
            "l2_interface": "lo",
            "app_id": 1000,
            "publish_interval_ms": 1000,
            "probe_duration_s": 3,
        }
    elif protocol == "iec61850_sv":
        base_kwargs["namespace_uri"] = None
        base_kwargs["ied_name"] = "Simulator"
        base_kwargs["ld_name"] = "LLN0"
        base_kwargs["transport"] = "ethernet_l2"
        base_kwargs["params"] = {
            "l2_interface": "lo",
            "app_id": 4000,
            "sample_rate_hz": 1,
            "probe_duration_s": 3,
        }
    else:
        base_kwargs["namespace_uri"] = None
        base_kwargs["ied_name"] = ""
        base_kwargs["ld_name"] = ""

    return SimulatedSource(
        connection=SourceConnection(**base_kwargs),
        points=_SMOKE_POINTS,
    )


# ── 需要跳过 real_native_runner 协议的标记 ────────────────────────────────
# OPC UA 需要 open62541 可执行文件，未编译时跳过
_requires_native_runner = pytest.mark.skipif(
    True,  # 默认跳过依赖 C 编译的协议；CI 环境可通过覆盖此变量启用
    reason="native runner not compiled in this environment",
)


def _tcp_port_reachable(host: str, port: int, timeout: float = 3.0) -> bool:
    """检查 TCP 端口是否可达。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        try:
            sock.connect((host, port))
            return True
        except OSError:
            return False


def _skip_if_l2_unavailable(protocol: str) -> None:
    import os
    from pathlib import Path

    names = {
        "iec61850_goose": (
            "iec61850_goose_publisher_simulator",
            "iec61850_goose_subscriber_runner",
        ),
        "iec61850_sv": (
            "iec61850_sv_publisher_simulator",
            "iec61850_sv_subscriber_runner",
        ),
    }[protocol]
    build_dir = Path(__file__).resolve().parents[2] / "native" / "build"
    missing = [name for name in names if not (build_dir / name).exists()]
    if missing:
        pytest.skip(
            "dependency_missing: "
            + ",".join(missing)
            + " not compiled. CI: cmake -S tools/source_lab/native "
            "-B tools/source_lab/native/build && cmake --build tools/source_lab/native/build"
        )
    if os.geteuid() != 0:
        pytest.skip(
            f"raw_socket_permission_missing: {protocol} requires CAP_NET_RAW/root and "
            "a usable L2 interface. CI: pytest -k 'goose or sv' tools/source_lab/tests/access -q"
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "protocol,requires_native",
    [
        ("opcua", True),
        ("modbus_tcp", False),
        ("iec104", False),
        ("iec61850_mms", False),
        ("iec61850_report", False),
    ],
)
async def test_facade_lifecycle_and_tcp_health(protocol: str, requires_native: bool) -> None:
    """验证 facade 生命周期：start → TCP 可达 → health OK → stop → TCP 不可达。"""
    if requires_native:
        pytest.skip("native runner required but not available")

    port = _choose_available_port()
    source = _build_source(protocol, port)
    facade = create_server_simulator(protocol, source)

    # 启动
    result = await facade.start()
    assert result.status.name == "OK", f"{protocol} start failed: {result.message}"
    await asyncio.sleep(0.2)  # 等待 TCP 服务器就绪

    # TCP 端口可达
    assert _tcp_port_reachable("127.0.0.1", port), f"{protocol} TCP port {port} unreachable after start"

    # 健康检查 OK
    health = await facade.health()
    assert health.status.name == "OK", f"{protocol} health failed: {health.message}"
    assert health.running is True

    # 停止
    stop_result = await facade.stop()
    assert stop_result.status.name == "OK", f"{protocol} stop failed: {stop_result.message}"

    # TCP 端口不可达
    await asyncio.sleep(0.2)
    assert not _tcp_port_reachable("127.0.0.1", port), f"{protocol} TCP port {port} still reachable after stop"


@pytest.mark.asyncio
async def test_opcua_facade_with_native_simulator() -> None:
    """OPC UA facade 在 open62541 可执行文件可用时验证完整生命周期。"""
    try:
        from tools.source_lab.protocols.opcua.open62541_source_simulator import resolve_runner_path
        runner = resolve_runner_path()
        if not runner.exists():
            pytest.skip(f"open62541 runner not compiled: {runner}")
    except (RuntimeError, FileNotFoundError):
        pytest.skip("open62541 runner not compiled")

    port = _choose_available_port()
    source = _build_source("opcua", port)
    facade = create_server_simulator("opcua", source)

    result = await facade.start()
    assert result.status.name == "OK", f"OPC UA start failed: {result.message}"
    await asyncio.sleep(0.5)

    try:
        # TCP 端口可达
        assert _tcp_port_reachable("127.0.0.1", port)

        # 健康检查 OK
        health = await facade.health()
        assert health.status.name == "OK"
        assert health.running is True

        # update_values 注入（通过 stdin 协议写入模拟器）
        uv = await facade.update_values({"WPPD1_TotW": 42.0})
        assert uv.status.name == "OK", f"update_values failed: {uv.message}"
    finally:
        await facade.stop()


@pytest.mark.asyncio
async def test_modbus_tcp_facade_lifecycle() -> None:
    """Modbus TCP facade 生命周期。"""
    port = _choose_available_port()
    source = _build_source("modbus_tcp", port)
    facade = create_server_simulator("modbus_tcp", source)

    result = await facade.start()
    assert result.status.name == "OK"
    await asyncio.sleep(0.2)

    try:
        assert _tcp_port_reachable("127.0.0.1", port)

        health = await facade.health()
        assert health.status.name == "OK"
        assert health.running is True

        # update_values（注入内部值，真实 Modbus 客户端可读取）
        uv = await facade.update_values({"WPPD1_TotW": 42.0})
        assert uv.status.name == "OK"
    finally:
        await facade.stop()

    assert not _tcp_port_reachable("127.0.0.1", port)


@pytest.mark.asyncio
async def test_iec104_facade_lifecycle() -> None:
    """IEC104 facade 生命周期。"""
    port = _choose_available_port()
    source = _build_source("iec104", port)
    facade = create_server_simulator("iec104", source)

    result = await facade.start()
    assert result.status.name == "OK"
    await asyncio.sleep(0.2)

    try:
        assert _tcp_port_reachable("127.0.0.1", port)

        health = await facade.health()
        assert health.status.name == "OK"
        assert health.running is True

        uv = await facade.update_values({"WPPD1_TotW": 42.0})
        assert uv.status.name == "OK"
    finally:
        await facade.stop()

    assert not _tcp_port_reachable("127.0.0.1", port)


@pytest.mark.asyncio
async def test_iec61850_mms_facade_lifecycle() -> None:
    """IEC61850 MMS facade 生命周期。"""
    port = _choose_available_port()
    source = _build_source("iec61850_mms", port)
    facade = create_server_simulator("iec61850_mms", source)

    result = await facade.start()
    assert result.status.name == "OK"
    await asyncio.sleep(0.2)

    try:
        assert _tcp_port_reachable("127.0.0.1", port)

        health = await facade.health()
        assert health.status.name == "OK"
        assert health.running is True

        uv = await facade.update_values({"WPPD1_TotW": 42.0})
        assert uv.status.name == "OK"
    finally:
        await facade.stop()

    assert not _tcp_port_reachable("127.0.0.1", port)


# ── IEC61850 MMS 真实读写 Smoke ──────────────────────────────────────────

_MMS_SMOKE_POINTS = (
    SimulatedPoint(ln_name="GGIO1", do_name="Ind1.stVal", unit=None, data_type="BOOLEAN", initial_value=False),
    SimulatedPoint(ln_name="GGIO1", do_name="AnIn1.mag", unit=None, data_type="INT32", initial_value=0),
    SimulatedPoint(ln_name="GGIO1", do_name="SPCtrl1.setVal", unit=None, data_type="BOOLEAN", initial_value=False),
)


def _build_mms_source(port: int) -> SimulatedSource:
    return SimulatedSource(
        connection=SourceConnection(
            name="mms_smoke",
            host="127.0.0.1",
            port=port,
            transport="tcp",
            protocol="iec61850_mms",
            namespace_uri=None,
            ied_name="Simulator",
            ld_name="Simulator",
        ),
        points=_MMS_SMOKE_POINTS,
    )


@pytest.mark.asyncio
async def test_iec61850_mms_facade_read_write() -> None:
    """MMS facade 真实读写测试：start → read → write → readback → stop。"""
    port = _choose_available_port()
    source = _build_mms_source(port)
    facade = create_server_simulator("iec61850_mms", source)

    result = await facade.start()
    assert result.status.name == "OK", f"MMS start failed: {result.message}"
    await asyncio.sleep(0.5)  # wait for both simulator and client runner

    try:
        # 1. Read Ind1.stVal (BOOLEAN ST) — server toggles it every 1s
        read_result = await facade.read(["GGIO1.Ind1.stVal"])
        assert read_result.status.name in ("OK", "PARTIAL_SUCCESS"), (
            f"MMS read failed: {read_result.message}"
        )
        val = read_result.values.get("GGIO1.Ind1.stVal")
        assert val is not None, f"MMS read returned no value for Ind1: {read_result.values}"
        assert isinstance(val, bool), f"Ind1 should be bool, got {type(val)}"

        # 2. Write true to SPCtrl1.setVal (BOOLEAN SP)
        write_result = await facade.write({"GGIO1.SPCtrl1.setVal": True})
        assert write_result.status.name == "OK", (
            f"MMS write failed: {write_result.message}"
        )

        # 3. Readback SPCtrl1.setVal
        readback = await facade.read(["GGIO1.SPCtrl1.setVal"])
        assert readback.status.name in ("OK", "PARTIAL_SUCCESS"), (
            f"MMS readback failed: {readback.message}"
        )
        rb_val = readback.values.get("GGIO1.SPCtrl1.setVal")
        assert rb_val is True, (
            f"MMS write-then-readback expected True, got {rb_val!r}"
        )
    finally:
        await facade.stop()

    assert not _tcp_port_reachable("127.0.0.1", port)


# ── Modbus TCP 真实读写 Smoke ────────────────────────────────────────────

import struct


def _modbus_read_registers(
    host: str, port: int, reg_addr: int, count: int = 1, unit_id: int = 1,
) -> list[int]:
    """Read Modbus holding registers via FC03 over raw TCP (real protocol)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(3.0)
        sock.connect((host, port))
        req_len = 6  # unit_id(1) + fc(1) + addr(2) + count(2)
        mbap = struct.pack(">HHHB", 1, 0, req_len, unit_id)
        pdu = struct.pack(">BHH", 0x03, reg_addr, count)
        sock.sendall(mbap + pdu)
        resp = sock.recv(1024)
        if len(resp) < 9:
            raise ValueError(f"Short FC03 response: {len(resp)} bytes")
        fc = resp[7]
        if fc == 0x83:
            raise ValueError(f"FC03 exception: code={resp[8]}")
        if fc != 0x03:
            raise ValueError(f"Unexpected FC: 0x{fc:02x}")
        byte_count = resp[8]
        vals: list[int] = []
        for i in range(count):
            off = 9 + i * 2
            if off + 2 > len(resp):
                break
            vals.append(struct.unpack(">H", resp[off:off+2])[0])
        if len(vals) < byte_count // 2:
            raise ValueError(f"Truncated FC03 data: got {len(vals)} of {byte_count // 2}")
        return vals


_MODBUS_WRITE_POINTS = (
    SimulatedPoint(ln_name="holding", do_name="0", unit=None, data_type="INT32", initial_value=0),
    SimulatedPoint(ln_name="holding", do_name="1", unit=None, data_type="BOOLEAN", initial_value=False),
    SimulatedPoint(ln_name="holding", do_name="2", unit=None, data_type="INT32", initial_value=0),
)


def _build_modbus_write_source(port: int) -> SimulatedSource:
    return SimulatedSource(
        connection=SourceConnection(
            name="modbus_write_smoke",
            host="127.0.0.1",
            port=port,
            transport="tcp",
            protocol="modbus_tcp",
            namespace_uri=None,
            ied_name="",
            ld_name="",
        ),
        points=_MODBUS_WRITE_POINTS,
    )


@pytest.mark.asyncio
async def test_modbus_tcp_facade_write_readback() -> None:
    """Modbus TCP facade 真实写入+读取：
    start -> write(FC06) -> readback(FC03) -> stop."""
    port = _choose_available_port()
    source = _build_modbus_write_source(port)
    facade = create_server_simulator("modbus_tcp", source)

    result = await facade.start()
    assert result.status.name == "OK", f"Modbus start failed: {result.message}"
    await asyncio.sleep(0.2)

    try:
        # Write INT32 value 42 to register 0 via FC06 (native runner)
        wr = await facade.write({"holding.0": 42})
        assert wr.status.name == "OK", f"Modbus write failed: {wr.message}"

        # Readback register 0 via FC03 real protocol
        rb = _modbus_read_registers("127.0.0.1", port, 0, 1)
        assert len(rb) == 1, f"expected 1 register, got {len(rb)}"
        assert rb[0] == 42, f"readback expected 42, got {rb[0]}"

        # Write boolean True to register 1
        wr2 = await facade.write({"holding.1": True})
        assert wr2.status.name == "OK"
        rb2 = _modbus_read_registers("127.0.0.1", port, 1, 1)
        assert rb2[0] == 1, f"readback bool expected 1, got {rb2[0]}"

        # Write 255 to register 2
        wr3 = await facade.write({"holding.2": 255})
        assert wr3.status.name == "OK"
        rb3 = _modbus_read_registers("127.0.0.1", port, 2, 1)
        assert rb3[0] == 255, f"readback expected 255, got {rb3[0]}"
    finally:
        await facade.stop()

    assert not _tcp_port_reachable("127.0.0.1", port)


# ── IEC61850 Report 订阅 Smoke ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_iec61850_report_facade_subscribe_report() -> None:
    """Report facade 真实订阅测试：
    start -> subscribe -> wait events -> report -> stop."""
    port = _choose_available_port()
    source = _build_mms_source(port)
    facade = create_server_simulator("iec61850_report", source)

    result = await facade.start()
    assert result.status.name == "OK", f"Report start failed: {result.message}"
    await asyncio.sleep(0.5)

    try:
        # Subscribe to report runner (connects to C simulator's RCB)
        sr = await facade.subscribe([])
        assert sr.status.name == "OK", f"subscribe failed: {sr.message}"

        # Wait for periodic data changes (Ind1 toggles every 1s -> report events)
        await asyncio.sleep(2.5)

        # Drain collected report events
        rr = await facade.report([])
        assert rr.status.name == "OK", f"report failed: {rr.message}"
        assert "REPORT" in (rr.message or ""), (
            f"expected REPORT events after 2.5s, got: {rr.message}"
        )
    finally:
        await facade.stop()

    assert not _tcp_port_reachable("127.0.0.1", port)


@pytest.mark.asyncio
async def test_goose_facade_real_subscribe_event() -> None:
    """GOOSE facade starts a real publisher and subscriber receives an event."""
    _skip_if_l2_unavailable("iec61850_goose")
    source = _build_source("iec61850_goose", 0)
    facade = create_server_simulator("iec61850_goose", source)

    result = await facade.start()
    assert result.status.name == "OK", f"GOOSE start failed: {result.message}"
    try:
        health = await facade.health()
        assert health.status.name == "OK"
        sub = await facade.subscribe(["LLN0.Events.stVal"])
        assert sub.status.name == "OK", f"GOOSE subscribe failed: {sub.message}"
        assert "count=" in sub.message
    finally:
        await facade.stop()


@pytest.mark.asyncio
async def test_sv_facade_real_subscribe_sample() -> None:
    """SV facade starts a real publisher and subscriber receives a sample."""
    _skip_if_l2_unavailable("iec61850_sv")
    source = _build_source("iec61850_sv", 0)
    facade = create_server_simulator("iec61850_sv", source)

    result = await facade.start()
    assert result.status.name == "OK", f"SV start failed: {result.message}"
    try:
        health = await facade.health()
        assert health.status.name == "OK"
        sub = await facade.subscribe(["LLN0.PhVMeas.mag"])
        assert sub.status.name == "OK", f"SV subscribe failed: {sub.message}"
        assert "count=" in sub.message
    finally:
        await facade.stop()


# ── OPC UA 真实写入 Smoke ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_opcua_facade_real_write() -> None:
    """OPC UA facade 真实写入（write 通过 open62541 原生 runner）。"""
    try:
        from tools.source_lab.protocols.opcua.open62541_source_simulator import resolve_runner_path
        runner = resolve_runner_path()
        if not runner.exists():
            pytest.skip(f"open62541 runner not compiled: {runner}")
    except (RuntimeError, FileNotFoundError):
        pytest.skip("open62541 runner not compiled")

    port = _choose_available_port()
    source = _build_source("opcua", port)
    facade = create_server_simulator("opcua", source)

    result = await facade.start()
    assert result.status.name == "OK", f"OPC UA start failed: {result.message}"
    await asyncio.sleep(0.5)

    try:
        # write() via open62541 native runner (real OPC UA write)
        wr = await facade.write({"WPPD1.TotW": 42.0})
        assert wr.status.name == "OK", f"OPC UA write failed: {wr.message}"

        # Multiple writes
        wr2 = await facade.write({"WPPD1.DevSt": False})
        assert wr2.status.name == "OK"
    finally:
        await facade.stop()
